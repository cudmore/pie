# Robert Cudmore
# 20170817

import os, sys, time, subprocess

from flask import Flask, render_template, send_file, jsonify, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import logging

from datetime import datetime # added to report start of PiE server restart (see restartpieserver)

from treadmill import treadmill

#########################################################################
app = Flask('treadmill_app')
#app = Flask(__name__)
CORS(app)

# socketio is for server side push during armed recording
# if we do not use this, REST calls to interface will cause errors in GPIO timing
# socketio needs to use 'async_mode = 'threading'
# otherwise server side emit does not arrive at web client ????
async_mode = 'threading' #choose from: None, 'eventlet', 'threading'
socketio = SocketIO(app, async_mode=async_mode)

# instantiate a treadmill object
# treadmill needs socketio to emit to client on external GPIO triggerIn
treadmill = treadmill(socketio)

pieLogger = logging.getLogger('pie')
pieHandler = pieLogger.handlers[0]

app.logger = pieLogger

# turn off werkzeug logging
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.setLevel(logging.ERROR)

#########################################################################
@app.after_request
def myAfterRequest(response):
	"""
	ignore some specific endpoints to reduce log clutter
	we could put 'lastimage' in this list but are intentionally leaving it out
	to remind user that opening the 'lastimage' tab actually hits the server
	and can cause problems with gpio timing
	"""
	if request.endpoint is None or request.endpoint in ['status', 'static', 'log', 'lastimage']:
		# ignore
		pass
	else:
		#request.endpoint is name of my function (not web address)
		#print(request.url)
		app.logger.info('myAfterRequest: ' + request.path)
	return response

#########################################################################
# socketio
#########################################################################
@socketio.on('client_connected', namespace='')
def handle_client_connect_event(json):
	app.logger.info('client_connected on ' + json['clientUrl'])

	'''
	# this is an example of an emit()
	socketio.emit('my_response',
				{'data': 'Server generated event', 'status': treadmill.getStatus()},
				namespace='')
	'''
	
#########################################################################
# REST routes
#########################################################################
@app.route('/')
def hello_world():
	#return render_template('index.html', async_mode=socketio.async_mode)
	return send_file('templates/index.html')

@app.route('/templates/partials/<path:htmlfile>')
def templates(htmlfile):
	#print('htmlfile:', htmlfile)
	return send_file('templates/partials/' + htmlfile)

@app.route('/systeminfo')
def systeminfo():
	return jsonify(treadmill.systemInfo)

@app.route('/log')
def log():
	# stream pie.log text file
	with open('pie.log', 'r') as f:
		return Response(f.read(), mimetype='text/plain')

@app.route('/environment')
def environment():
	return send_file('templates/environment.html')

@app.route('/environmentlog')
def environmentlog():
	logFilePath = treadmill.trial.getConfig('trial', 'savePath') # '/home/pi/video/logs/environment.log'
	logFilePath = os.path.join(logFilePath, 'logs/environment.log')
	if os.path.isfile(logFilePath):
		with open(logFilePath, 'r') as f:
			return Response(f.read(), mimetype='text/plain')
	else:
		return 'No ' + logFilePath + ' found. <BR><BR>' + str(dict(treadmill.trial.config['hardware']['dhtsensor'])) + "<BR>"
		
@app.route('/status')
def status():
	return jsonify(treadmill.getStatus())

@app.route('/api/refreshsysteminfo')
def refreshsysteminfo():
	treadmill.trial.refreshSystemInfo()
	return jsonify(treadmill.getStatus())

@app.route('/api/lastimage')
def lastimage():
	myImage = 'static/still.jpg'
	if os.path.isfile(myImage):
		return send_file(myImage)
	else:
		return ''

#########################################################################
# set the animalID and conditionID
#########################################################################
@app.route('/api/set/animalid/<string:animalID>')
def setAnimalID(animalID):
	treadmill.trial.setAnimalID(animalID)
	return jsonify(treadmill.getStatus())
	
@app.route('/api/set/conditionid/<string:conditionID>')
def setConditionID(conditionID):
	treadmill.trial.setConditionID(conditionID)
	return jsonify(treadmill.getStatus())
	
#########################################################################
# set the scope file name
# this is used by prairie scope at end of scan
#########################################################################
@app.route('/api/set/scopefilename/<string:scopeFilename>')
def setScopeFilename(scopeFilename):
	treadmill.trial.setScopeFilename(scopeFilename)
	return jsonify(treadmill.getStatus())
	
#########################################################################
# respond to actions like start and stop
#########################################################################
@app.route('/api/action/<string:thisAction>')
def action(thisAction):

	#print('*** /api/action/' + thisAction)
	
	if thisAction == 'startRecord':
		treadmill.startRecord()
	if thisAction == 'stopRecord':
		treadmill.stopRecord()

	if thisAction == 'startStream':
		treadmill.startStream()
	if thisAction == 'stopStream':
		treadmill.stopStream()

	if thisAction == 'startArm':
		treadmill.startArm()
	if thisAction == 'stopArm':
		treadmill.stopArm()

	if thisAction == 'startArmVideo':
		treadmill.startArmVideo()
	if thisAction == 'stopArmVideo':
		treadmill.stopArmVideo()

	return jsonify(treadmill.getStatus())

#########################################################################
# handle submission of forms
#########################################################################
@app.route('/api/submit/<string:submitThis>', methods=['GET', 'POST'])
def submit(submitThis):
	post = request.get_json()

	if submitThis == 'saveconfig': # GET
		treadmill.saveConfig()

	if submitThis == 'configparams':
		treadmill.updateConfig(post)
	if submitThis == 'pinparams':
		treadmill.updatePins(post)
	if submitThis == 'animalparams':
		treadmill.updateAnimal(post)
	if submitThis == 'ledparams':
		treadmill.updateLED(post)
	if submitThis == 'motorparams':
		treadmill.serialUpdateMotor(post)

	return jsonify(treadmill.getStatus())

# 20181024, writing processsing examples
@app.route('/api/v2/set/led/<int:ledIdx>/<int:newValue>')
def set_led(ledIdx, newValue):
	print("ledIdx:", ledIdx, "newValue:", newValue)
	treadmill.trial.updateLED2(ledIdx, True if newValue else False)
	return jsonify(treadmill.getStatus())
	
#########################################################################
#  Load default config files from /config
#########################################################################
@app.route('/api/submit/loadconfig/<string:loadThis>')
def loadconfig(loadThis):
	treadmill.loadConfig(loadThis)
	return jsonify(treadmill.getStatus())

#########################################################################
#  not used -->> remove
#########################################################################
#########################################################################
#  restart server
#########################################################################
@app.route('/api/restartpieserver')
def restartpieserver():
	print('restartpieserver()')
	
	# stop streaming 
	
	#
	script_path = os.path.dirname(os.path.abspath( __file__ ))
	cmd = [script_path + "/bin/restart_server.sh"]

	app.logger.info(cmd)

	#20181012, want to inform user that request has been issued
	# the server will respond when restarted
	# remember, this does not function during ./pie run
	now = datetime.now()
	tmpStartTime = 'on ' + now.strftime('%Y-%m-%d') + ' at ' + now.strftime('%H:%M:%S')
	treadmill.trial.runtime['lastResponse'] = 'Please wait ... PiE server restart requested ' + tmpStartTime

	try:
		out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		#self.lastResponse = 'Streaming is on'
	except subprocess.CalledProcessError as e:
		error = e.output.decode('utf-8')
		app.logger.error('restartpieserver error: ' + error)
		#self.lastResponse = error
		raise
	return jsonify(treadmill.getStatus())

#########################################################################
#  not used -->> remove
#########################################################################
"""
@app.route('/api/eventout/<name>/<int:onoff>')
def eventOut(name, onoff):
	''' turn named output pin on/off '''
	treadmill.trial.myPinThread.eventOut(name, True if onoff else False)
	return jsonify(treadmill.getStatus())

@app.route('/api/simulate/starttrigger')
def simulate_starttrigger():
	# todo: remove pin from triggerIn_Callback
	tmpPin = None
	treadmill.trial.triggerIn_Callback(tmpPin)
	return jsonify(treadmill.getStatus())
"""

#########################################################################
#  display list of files in video/
#########################################################################
@app.route('/videolist')
@app.route('/videolist/<path:req_path>')
def videolist(req_path=''):
	# we need to append '/' so os.path.join works???
	savePath = treadmill.trial.config['trial']['savePath'] + '/'
	
	tmpStr = savePath[1:]
	req_path2 = req_path.replace(tmpStr, '')
	#req_path2 = req_path2.replace('/', '') # why do i need this?
	
	abs_path = os.path.join(savePath, req_path2)

	# Return 404 if path doesn't exist
	if not os.path.exists(abs_path):
		app.logger.error('videolist() aborting with 404, abs_path: ' + abs_path)
		return "" #abort(404)
	
	# Check if path is a file and serve
	if os.path.isfile(abs_path):

		# serve log files by streaming text, serve video by sending file
		# this is a very simple interface and requires ENTIRE video file to be 'downloaded'
		# video files are NOT streaming
		if abs_path.endswith('.log'):
			with open(abs_path, 'r') as f:
				return Response(f.read(), mimetype='text/plain')
		else:
			app.logger.debug(('videolist() is serving file:', abs_path))
			return send_file(abs_path)

	# Show directory contents
	files = []
	for f in os.listdir(abs_path):
		if f.startswith('.') or f in ['Network Trash Folder', 'Temporary Items']:
			continue
		f2 = f
		f = os.path.join(abs_path, f)
		
		fileDict = {}
		
		'''
		isTrialFile = f.endswith('.txt') # big assumption, should parse '_r%d.txt'
		isLogFile = f.endswith('.log')
		if isTrialFile:
			fileDict = home.trial.loadTrialFile(f)
		'''
		
		# get file size in either MB or KB (if <1 MB)
		unitStr = 'MB'
		size = os.path.getsize(f)
		sizeMB = size/(1024*1024.0) # mb
		if sizeMB < 0.1:
			unitStr = 'bytes'
			sizeMB = size
		sizeStr = "%0.1f %s" % (sizeMB, unitStr)
		
		#fd = {'path':f, 'file':f2, 'isfile':True, 'size':sizeStr}
		fileDict['path'] = f
		fileDict['file'] = f2
		fileDict['isFile'] = True
		fileDict['size'] = sizeStr
		fileDict['cTime'] = time.strftime('%Y%m%d %H%M%S', time.localtime(os.path.getctime(f)))
		fileDict['mTime'] = time.strftime('%Y%m%d %H%M%S', time.localtime(os.path.getmtime(f)))
		files.append(fileDict)
		
	# sort the list
	files = sorted(files, key=lambda k: k['file']) 

	return render_template('videolist.html', files=files, abs_path=abs_path, systemInfo=treadmill.systemInfo)

#########################################################################
#  utility
#########################################################################
def whatismyip():
	ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

#########################################################################
#  main
#########################################################################
if __name__ == '__main__':	
	myip = whatismyip()
	
	debug = False
	if len(sys.argv) == 2:
		if sys.argv[1] == 'debug':
			debug = True
	app.logger.debug('Running flask server with debug = ' + str(debug))
		
	responseStr = 'Flask server is running at: ' + 'http://' + str(myip) + ':5010'
	app.logger.debug(responseStr)
	
	# 0.0.0.0 will run on external ip	
	#app.run(host='0.0.0.0', port=5010, debug=debug, threaded=True)
	socketio.run(app, host='0.0.0.0', port=5010, debug=debug)

	treadmill.trial.myPinThread.exiting()
	print('treadmill_app.__main__ is exiting')