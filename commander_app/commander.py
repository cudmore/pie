# Robert Cudmore
# 20180101

from __future__ import print_function    # (at top of module)

import os, sys, subprocess
import json, queue

from flask import Flask, render_template, send_file, jsonify, abort, request#, redirect, make_response
from flask_cors import CORS
from subprocess import check_output

import commandersync

import logging

from logging import FileHandler #RotatingFileHandler
from logging.config import dictConfig

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

logFileHandler = FileHandler('commander.log', mode='w')
logFileHandler.setLevel(logging.DEBUG)
logFileHandler.setFormatter(myFormatter)

logger = logging.getLogger('commander')
logger.addHandler(logFileHandler)
logger.setLevel(logging.DEBUG)
logger.debug('commander initialized commander.log')


app = Flask(__name__)
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
	return send_file('templates/index.html')

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
# commandersync
# 20181223
##################################################################
# this has to be instantiated as a threaded commandersync and live in background
# insert commands into a queue ['fetchfilelist', 'runsync']
inQueue = queue.Queue()
cs = commandersync.CommanderSync(inQueue)
cs.daemon = True
cs.start()

@app.route('/sync')
def sync():
	return send_file('templates/commander_sync.html')

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
	global inQueue
	inQueue.put('cancel')
	return jsonify(cs.mySyncList)

@app.route('/sync/status')
def sync_status():
	global cs
	status = {
		'fetchIsBusy': cs.fetchIsBusy,
		'syncIsBusy': cs.syncIsBusy,
		'ipDict': cs.ipDict,
		'myFileList': cs.myFileList,
		'mySyncList': cs.mySyncList
	}
	return jsonify(status)

##################################################################
# Config
#	Config file is in 'config_commander.txt'
#	It is a comma seperated list of IP addresses
##################################################################
@app.route('/loadconfig')
def loadconfig():
	thisFile = 'config/config_commander.txt'
	if not os.path.isfile(thisFile):
		logger.info('defaulting to config/config_commander_factory.txt')
		thisFile = 'config/config_commander_factory.txt'
	logger.info('Loading config file ' + thisFile)
	with open(thisFile, 'r') as f:
		configfile = f.readlines()
	# remove whitespace characters like ',' and `\n` from each line
	returnConfigFile = [x.strip(',\n') for x in configfile] 
	logger.info('Config file contains: ' + str(returnConfigFile))
	return jsonify(returnConfigFile)

@app.route('/saveconfig/<iplist>')
def saveconfig(iplist):
	"""
	iplist is string list of ip numbers
	"""
	thisFile = 'config/config_commander.txt'
	logger.info('saveconfig() configfile: ' + thisFile)
	with open(thisFile, 'w') as outfile:
		for line in iplist.split(','):
			#print('line:', line)
			outfile.write(line + ',' + '\n')
	return 'saved'
	
##################################################################
def whatismyip():
	try:
		ips = check_output(['hostname', '--all-ip-addresses'])
		ips = ips.decode('utf-8').strip()
	except:
		ips = '[IP]'
	return ips

##################################################################
if __name__ == '__main__':
	myip = whatismyip()
	
	debug = False
	if len(sys.argv) == 2:
		if sys.argv[1] == 'debug':
			debug = True
	app.logger.debug('Running flask server with debug = ' + str(debug))
		
	responseStr = 'Flask server is running at: ' + 'http://' + str(myip) + ':8000'
	print(responseStr)
	app.logger.debug(responseStr)
	
	# 0.0.0.0 will run on external ip and needed to start at boot with systemctl
	# before we get a valid ip from whatismyip()
	
	app.run(host='0.0.0.0', port=8000, debug=debug, threaded=True)

