# Robert Cudmore
# 20180101

from __future__ import print_function    # (at top of module)

import os, sys, subprocess
import json, queue

from flask import Flask, render_template, send_file, jsonify, abort, request#, redirect, make_response
from flask_cors import CORS
from subprocess import check_output


import logging

from logging import FileHandler #RotatingFileHandler
from logging.config import dictConfig

###
###
if getattr(sys, 'freeze', False):
	# running as bundle (aka frozen)
	#logger.info('running frozen')
	bundle_dir = sys._MEIPASS
	#bundle_dir = '/Users/cudmore/Sites/pie/commander_app/dist/commander'
else:
	# running live
	#logger.info('running live')
	bundle_dir = os.path.dirname(os.path.abspath(__file__))
#logger.info('bundle_dir is ' + bundle_dir)
#bundle_dir = '/Users/cudmore/Sites/pie/commander_app/dist/commander'
###
###

#
# save config.json and commander.log here
userPath = os.path.expanduser('~')
globalCommanderConfigPath = os.path.join(userPath, 'commander_config') # all local files with be in this folder
if not os.path.isdir(globalCommanderConfigPath):
	os.mkdir(globalCommanderConfigPath)

def _saveConfig(myConfig):
	thisFile = os.path.join(globalCommanderConfigPath, 'config_commander.json')
	
	logger.info('saveconfig() configfile: ' + thisFile)
	with open(thisFile, 'w') as outfile:
		json.dump(myConfig, outfile, indent=4)
		"""
		for line in iplist.split(','):
			#print('line:', line)
			outfile.write(line + ',' + '\n')
		"""

def _loadConfig():
	#thisFile = os.path.join(bundle_dir, 'config', 'config_commander.json')
	thisFile = os.path.join(globalCommanderConfigPath, 'config_commander.json')
	saveFirstTime = False
	if not os.path.isfile(thisFile):
		thisFile = os.path.join(bundle_dir, 'config', 'config_commander_factory.json')
		saveFirstTime = True
		logger.info('defaulting to config file: ' + thisFile)
	logger.info('Loading config file ' + thisFile)
	
	serverList = []
	with open(thisFile) as f:
		try:
			myConfig = json.load(f)
			#serverList = my_json['serverList']
		except ValueError as e:
			logger.error('_loadConfig ValueError: ' + str(e))
			# if there is an error in loading config file (json is wrong) we REALLY want to exit
			print('please fix config file:', thisFile)
			sys.exit(1)
	
	if saveFirstTime:
		_saveConfig(myConfig)
		
	#logger.info('Config file contains: ' + str(myConfig))
	return myConfig
	

logFormat = "[%(asctime)s] {%(filename)s %(funcName)s:%(lineno)d} %(levelname)s - %(message)s"
dictConfig({
	'version': 1,
	'formatters': {'default': {
		'format': logFormat,
	}},
	'handlers': {'wsgi': {
		'class': 'logging.StreamHandler',
		'stream': 'ext://flask.logging.wsgi_errors_stream',
		'formatter': 'default'
	}},
	'root': {
		'level': 'INFO',
		'handlers': ['wsgi']
	}
})

myFormatter = logging.Formatter(logFormat)

logger = logging.getLogger('commander')

#logFileHandler = FileHandler('commander.log', mode='w')
myLoggerPath = os.path.join(globalCommanderConfigPath, 'commander.log')
logFileHandler = FileHandler(myLoggerPath, mode='w')
logFileHandler.setLevel(logging.DEBUG)
logFileHandler.setFormatter(myFormatter)

logger = logging.getLogger('commander')
logger.addHandler(logFileHandler)
logger.setLevel(logging.DEBUG)
logger.info('logging to: ' + myLoggerPath)

import commandersync # this has to come after logger is initialized

# load config file
myConfig = _loadConfig()

# check that 'localFolder' is valid
if myConfig['localFolder']:
	if not os.path.isdir(myConfig['localFolder']):
		# error
		logger.error('config localFolder does not exist: "' + myConfig['localFolder'] + '"')
		print('please make sure folder specified in commander_config.json "localFolder" exists')
		sys.exit(1)
else:
	myConfig['localFolder'] = os.path.join(userPath, 'commander_data')
logger.info('Will save download/sync data to: ' + myConfig['localFolder'])


###
app = Flask(__name__)
#app = Flask(__name__, static_url_path=bundle_dir, template_folder=bundle_dir)
# was this before implementing pyinstaller/frozen
#app = Flask(__name__)

CORS(app)

# added 20181223
app.logger = logger

# turn off werkzeug logging
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.setLevel(logging.ERROR)
###


@app.route('/')
@app.route('/commander')
def hello_world():
	indexPath = os.path.join(bundle_dir, 'templates', 'index.html')
	return send_file(indexPath)
	#return send_file('templates/index.html')

#########################################################################
@app.after_request
def myAfterRequest(response):
	"""
	ignore some specific endpoints to reduce log clutter
	we could put 'lastimage' in this list but are intentionally leaving it out
	to remind user that opening the 'lastimage' tab actually hits the server
	and can cause problems with gpio timing
	"""
	if request.endpoint is None or request.endpoint in ['sync_status', 'static', 'log', 'lastimage']:
		# ignore
		pass
	else:
		#request.endpoint is name of my function (not web address)
		#print(request.url)
		app.logger.info('myAfterRequest: ' + request.path)
	return response

##################################################################
# Config
#	Config file is in 'config_commander.txt'
#	It is a comma seperated list of IP addresses
##################################################################
@app.route('/loadconfig')
def loadconfig():
	myConfig = _loadConfig()
	return jsonify(myConfig)

@app.route('/saveconfig/<myConfig>')
def saveconfig(myConfig):
	"""
	serverList is a list of dict {ip, username, password}
	"""
	
	# convert string to json
	myConfig = json.loads(myConfig)
	print('saveconfig() myConfig:', myConfig)
	
	_saveConfig(myConfig)
			
	# tell commandersync to reload new ip list
	#cs.loadConfig()
	cs.setConfig(myConfig)
	
	return 'saved'
	

##################################################################
# CommanderSync
##################################################################
# this has to be instantiated as a threaded commandersync and live in background
# insert commands into a queue ['fetchfilelist', 'runsync']
inQueue = queue.Queue()
cs = commandersync.CommanderSync(inQueue, myConfig)
cs.daemon = True
cs.start()

@app.route('/sync')
def sync():
	return send_file('templates/commander_sync.html')

@app.route('/sync/deleteaftercopy/<int:onoff>')
def delete_after_copy(onoff):
	print('delete_after_copy:', onoff)
	cs.setDeleteRemoteFiles(onoff)
	return jsonify(cs.ipDict)

@app.route('/sync/fetchfiles')
def sync_fetchfiles():
	global inQueue
	inQueue.put('fetchfiles')
	return jsonify(cs.ipDict)

@app.route('/sync/run')
def sync_run():
	global inQueue
	inQueue.put('sync')
	return jsonify(cs.mySyncList)

@app.route('/sync/cancel')
def sync_cancel():
	# queue is not working because thread is busy during sync
	global inQueue
	inQueue.put('cancel')
	
	cs.cancel = True
	
	return jsonify(cs.mySyncList)

@app.route('/sync/status')
def sync_status():
	global cs
	status = {
		'fetchIsBusy': cs.fetchIsBusy,
		'syncIsBusy': cs.syncIsBusy,
		'ipDict': cs.ipDict,
		'myFileList': cs.myFileList,
		'mySyncList': cs.mySyncList,
		'localFolder': cs.localFolder,
		'cancel': cs.cancel, # if True then cancel is pending
		'syncStartStr': cs.syncStartStr,
		'syncElapsedStr': cs.syncElapsedStr,
		'syncNumCopied': cs.syncNumCopied,
		'syncNumTotalToCopy': cs.syncNumTotalToCopy,
		'syncBytesCopied': cs._humanReadableSize(cs.syncBytesCopied),
		'syncTotalBytesToCopy': cs._humanReadableSize(cs.syncTotalBytesToCopy),
		'syncEstimatedTimeArrival': cs._humanReadableTime(cs.syncEstimatedTimeArrival)
	}
	return jsonify(status)

##################################################################
def whatismyip():
	platform = sys.platform
	app.logger.info('platform is ' + platform)
	if platform.startswith('linux'):
		ip = check_output(['hostname', '--all-ip-addresses'])
		ip = ip.decode('utf-8').strip()
	elif platform == 'darwin':
		whatismyip_cmd = os.path.join(bundle_dir,'bin', 'whatismyip')
		ip = subprocess.check_output(whatismyip_cmd)
		ip = ip.decode('utf-8').strip()
	else:
		print('commander whatismyip() unknown platform:', platform)
		ip = ''
	return ip


##################################################################
if __name__ == '__main__':

	myip = whatismyip()
	
	debug = False
	if len(sys.argv) == 2:
		if sys.argv[1] == 'debug':
			debug = True
	#app.logger.info('Running flask server with debug = ' + str(debug))
		
	responseStr = 'Starting Flask web server at: ' + 'http://' + str(myip) + ':8000'
	#print(responseStr)
	app.logger.info(responseStr)
	
	# 0.0.0.0 will run on external ip and needed to start at boot with systemctl
	# before we get a valid ip from whatismyip()
	
	try:
		app.run(host='0.0.0.0', port=8000, debug=debug, threaded=True)
	except (OSError) as e:
		logger.error('OSError: ' + str(e) + ' ' + myip)
		logger.error('Is the commander already running on this machine?')
