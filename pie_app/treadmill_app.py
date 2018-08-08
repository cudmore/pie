# 20170817
# Robert Cudmore

'''
import eventlet
eventlet.monkey_patch()
'''

import os, sys, time, subprocess

from flask import Flask, render_template, send_file, jsonify, request, Response
from flask_cors import CORS
# socketio
import threading
from flask_socketio import SocketIO, emit

import logging

from treadmill import treadmill

# was here before socketio
#treadmill = treadmill()

#########################################################################
app = Flask('treadmill_app')
#app.config['SECRET_KEY'] = 'secret!'
#app = Flask(__name__)
CORS(app)

# socketio, i need to use 'threading'
async_mode = 'threading' #choose: None, 'eventlet', 'threading'
socketio = SocketIO(app, async_mode=async_mode)
"""
thread = None
#thread_lock = threading.Lock()
"""

treadmill = treadmill(socketio)
#treadmill = treadmill()

pieLogger = logging.getLogger('pie')
pieHandler = pieLogger.handlers[0]

app.logger = pieLogger

# turn off werkzeug logging
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.setLevel(logging.ERROR)

#########################################################################
"""
class myPushThread(threading.Thread):
	# need 'isRunning'
	def __init__(self, treadmill, socketio):
		threading.Thread.__init__(self)
		self.treadmill = treadmill
		self.socketio = socketio
		
	def run(self):
		while True:
			status = self.treadmill.getStatus()
			#print('\n\n\nmyPushThread run()', str(status))
			self.socketio.emit('my_response',
					{'data': 'Server generated event', 'status': status},
					namespace='')
			time.sleep(1.0)
"""			

"""
class ssePushThread(threading.Thread):
	# need 'isRunning'
	def __init__(self, treadmill):
		threading.Thread.__init__(self)
		self.treadmill = treadmill
		
	def run(self):
		while True:
			status = self.treadmill.getStatus()
			#print('\n\n\nmyPushThread run()', str(status))
			yield 'NEW DATA'
			time.sleep(1.0)
"""

#########################################################################
@app.after_request
def myAfterRequest(response):
	#if request.endpoint is None or request.endpoint in ["status", "log", "static", "lastimage"]:
	if request.endpoint is None or request.endpoint in ['status', 'static']:
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
'''
def background_thread():
	"""Example of how to send server generated events to clients."""
	count = 0
	while True:
		socketio.sleep(0.5)
		count += 1
		#print('background_thread emit')
		socketio.emit('my_response',
					  {'data': 'Server generated event', 'count': count, 'status': treadmill.getStatus()},
					  namespace='')
'''

@socketio.on('client_connected', namespace='')
def handle_client_connect_event(json):
	print('client_connected -->> handle_client_connect_event()') # data:', json['date'])

	socketio.emit('my_response',
				{'data': 'Server generated event', 'status': treadmill.getStatus()},
				namespace='')

	
'''
@socketio.on('client_connected')
def handle_client_connect_event(json):
	emit('my_response', {'data': 'Connected', 'count': 0})

	print('handle_client_connect_event received json: {0}'.format(str(json)))
	#
	if thread is None:
		print('handle_client_connect_event() is starting thread myPushThread')
		thread = ssePushThread(treadmill)
		thread.daemon = True
		thread.start()
	"""
	global thread
	if thread is None:
		thread = socketio.start_background_task(target=background_thread)
	"""
	"""
	with thread_lock:
		if thread is None:
			print('handle_client_connect_event() is starting thread myPushThread')
			thread = myPushThread(treadmill, socketio)
			thread.daemon = True
			thread.start()
	"""
	"""
	if thread is None:
		print('handle_client_connect_event() is starting thread myPushThread')
		thread = myPushThread(treadmill, socketio)
		thread.daemon = True
		thread.start()
	"""
'''

# sse
"""
@app.route('/subscribeToStatus')
def subscribeToStatus():
	def eventStream():
		while True:
			time.sleep(0.5)
			# Poll data from the database
			# and see if there's a new message
			#print('yield')
			yield 'data: xxxYYY'
			 #treadmill.getStatus()
	
	return Response(eventStream(), mimetype="text/event-stream")
"""
	
#########################################################################
# routes
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
	with open('pie.log', 'r') as f:
		return Response(f.read(), mimetype='text/plain')

@app.route('/environment')
def environment():
	return send_file('templates/environment.html')

@app.route('/environmentlog')
def environmentlog():
	logFilePath = 'logs/environment.log'
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
@app.route('/api/set/animalid/<string:animalID>')
def setAnimalID(animalID):
	treadmill.trial.setAnimalID(animalID)
	return jsonify(treadmill.getStatus())
	
@app.route('/api/set/conditionid/<string:conditionID>')
def setConditionID(conditionID):
	treadmill.trial.setConditionID(conditionID)
	return jsonify(treadmill.getStatus())
	
@app.route('/api/set/scopefilename/<string:scopeFilename>')
def setScopeFilename(scopeFilename):
	treadmill.trial.setScopeFilename(scopeFilename)
	return jsonify(treadmill.getStatus())
	
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

#########################################################################
@app.route('/api/submit/loadconfig/<string:loadThis>')
def loadconfig(loadThis):
	treadmill.loadConfig(loadThis)
	return jsonify(treadmill.getStatus())

#########################################################################
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

#########################################################################
@app.route('/videolist')
@app.route('/videolist/<path:req_path>')
def videolist(req_path=''):
	"""
	Serve a list of video files
	"""
	
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
		
		isTrialFile = f.endswith('.txt') # big assumption, should parse '_r%d.txt'
		'''
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
def whatismyip():
	ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

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
