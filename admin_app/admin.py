# Robert H Cudmore
# 20180713

"""
	Headless Flask server with REST interface (5011)
	Use this to control a PiE server on same machine (5010)
"""

import os, sys, time, subprocess
import threading, queue

from flask import Flask, render_template, send_file, jsonify, request, Response
from flask_cors import CORS

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

logger = logging.getLogger('pie_admin')

logFileHandler = FileHandler('admin.log', mode='w')
logFileHandler.setLevel(logging.DEBUG)
logFileHandler.setFormatter(myFormatter)

logger = logging.getLogger('pie')
logger.addHandler(logFileHandler)
logger.setLevel(logging.DEBUG)
logger.debug('admin initialized admin.log')

class pieadmin():
	def __init__(self):
		self.outBashQueue = queue.Queue()
		self.bashResponseStr = []
		
		self.lastResponse = ''
		
	def getStatus(self):
		status = {}
		status['runtime'] = {}
		
		#
		# outBashQueue
		while not self.outBashQueue.empty():
			bashItem = self.outBashQueue.get()
			self.bashResponseStr.append(bashItem)

		if self.bashResponseStr:	
			status['runtime']['bashQueue'] = self.bashResponseStr
		else:
			status['runtime']['bashQueue'] = ['None']
		
		return status
		
	#########################################################################
	# restart server in a background thread that has 'sleep 10; sudo systemctl restart treadmill.service;'
	#########################################################################
	def restartServerThread_(self):
		script_path = os.path.dirname(os.path.abspath( __file__ ))
		cmd = [script_path + "/bin/restart_server.sh"]
		try:
			logger.info(cmd)
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			out = out.decode()
			out = out.split('\n')
			for line in out:
				#print('line: ', line)
				self.outBashQueue.put(line)
		except (subprocess.CalledProcessError, OSError) as e:
			#error = e.output.decode('utf-8')
			logger.error('restartServerThread_ exception: ' + str(e))
			self.lastResponse = str(e)
			#raise
		
	def restartServer(self):

		logger.info('restartServer starting restartServerThread_')

		restartThread = threading.Thread(target=self.restartServerThread_, args=())
		restartThread.daemon = True				# Daemonize thread
		restartThread.start()					# Start the execution

		logger.info('RETURNED restartServer')
		
		self.lastResponse = 'Restarting treadmill server'

	#########################################################################
	# reboot machine
	#########################################################################
	def rebootMachineThread_(self):
		script_path = os.path.dirname(os.path.abspath( __file__ ))
		cmd = [script_path + "/bin/reboot_machine.sh"]
		try:
			logger.info(cmd)
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			out = out.decode()
			out = out.split('\n')
			for line in out:
				#print('line: ', line)
				self.outBashQueue.put(line)
		except (subprocess.CalledProcessError, OSError) as e:
			#error = e.output.decode('utf-8')
			logger.error('rebootMachineThread_ exception: ' + str(e))
			self.lastResponse = str(e)
			#raise
		
	def rebootMachine(self):

		logger.info('rebootMachine starting rebootMachineThread_')

		restartThread = threading.Thread(target=self.rebootMachineThread_, args=())
		restartThread.daemon = True				# Daemonize thread
		restartThread.start()					# Start the execution

		logger.info('RETURNED rebootMachine')
		
		self.lastResponse = 'Rebooting machine'

	#########################################################################
	# Update Software
	#########################################################################
	def updateSoftwareThread_(self):
		script_path = os.path.dirname(os.path.abspath( __file__ ))
		cmd = [script_path + "/bin/update_software.sh"]
		try:
			logger.info(cmd)
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			out = out.decode()
			out = out.split('\n')
			for line in out:
				print('line: ', line)
				self.outBashQueue.put(line)
		except (subprocess.CalledProcessError, OSError) as e:
			#error = e.output.decode('utf-8')
			logger.error('updateSoftwareThread_ exception: ' + str(e))
			self.lastResponse = str(e)
			#raise
		
	def updateSoftware(self):

		logger.info('updateSoftware starting updateSoftwareThread_')

		restartThread = threading.Thread(target=self.updateSoftwareThread_, args=())
		restartThread.daemon = True				# Daemonize thread
		restartThread.start()					# Start the execution

		logger.info('RETURNED updateSoftware')
		
		self.lastResponse = 'Updating software'

	#########################################################################
	# Revert To Stable
	#########################################################################
	def reverttostableThread_(self):
		script_path = os.path.dirname(os.path.abspath( __file__ ))
		cmd = [script_path + "/bin/revert_to_stable.sh"]
		try:
			logger.info(cmd)
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			out = out.decode()
			out = out.split('\n')
			for line in out:
				print('line: ', line)
				self.outBashQueue.put(line)
		except (subprocess.CalledProcessError, OSError) as e:
			#error = e.output.decode('utf-8')
			logger.error('reverttostableThread_ exception: ' + str(e))
			self.lastResponse = str(e)
			#raise
		
	def revertToStable(self):

		logger.info('reverttostable starting reverttostableThread_')

		restartThread = threading.Thread(target=self.reverttostableThread_, args=())
		restartThread.daemon = True				# Daemonize thread
		restartThread.start()					# Start the execution

		logger.info('RETURNED reverttostable')
		
		self.lastResponse = 'Reverting to stable'


#########################################################################
myAdmin = pieadmin()

app = Flask(__name__)
CORS(app)

# turn off werkzeug logging
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.setLevel(logging.ERROR)

#########################################################################
@app.route('/')
def hello_world():
	#return send_file('templates/admin.html')
	return 'PiE admin server, please use commander interface'
	
@app.route('/status')
def status():
	return jsonify(myAdmin.getStatus())

#########################################################################
@app.route('/api/restartserver')
def restartserver():
	myAdmin.restartServer()
	return jsonify(myAdmin.getStatus())

@app.route('/api/rebootmachine')
def rebootmachine():
	myAdmin.rebootMachine()
	return jsonify(myAdmin.getStatus())

@app.route('/api/updatesoftware')
def updatesoftware():
	myAdmin.updateSoftware()
	return jsonify(myAdmin.getStatus())

@app.route('/api/reverttostable')
def reverttostable():
	myAdmin.revertToStable()
	return jsonify(myAdmin.getStatus())

@app.route('/api/clearbashqueue')
def clearbashqueue():
	myAdmin.bashResponseStr = []
	return jsonify(myAdmin.getStatus())

#########################################################################
def whatismyip():
	ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

if __name__ == '__main__':	
	myip = whatismyip()
	
	responseStr = 'Flask server is running at: ' + 'http://' + str(myip) + ':5011'
	app.logger.debug(responseStr)
	
	# 0.0.0.0 will run on external ip	
	app.run(host='0.0.0.0', port=5011, debug=True, threaded=True)
