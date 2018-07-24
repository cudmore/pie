# Robert Cudmore
# 20180101

from __future__ import print_function    # (at top of module)

import os, sys, subprocess
import json, queue

from flask import Flask, render_template, send_file, jsonify, abort#, redirect, make_response
from flask_cors import CORS
from subprocess import check_output

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

"""
def getStatus():
	# Get struct of status from the backend
	status = home.getStatus()
	return status
"""
	
@app.route('/')
def hello_world():
	return send_file('templates/index.html')

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
	ips = check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
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

