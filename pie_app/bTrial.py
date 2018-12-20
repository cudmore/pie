"""
Author: Robert H Cudmore
Date: 20180525

Purpose: Catch all class to manage a trial. A trial roughly corresponds
to one video recording. See bTrial() for more information.
"""

import os, sys, time, json, threading, queue, subprocess
from collections import OrderedDict
from datetime import datetime, timedelta
import pprint
#import serial

# for dht sensor
import RPi.GPIO as GPIO

import logging

from logging import FileHandler #RotatingFileHandler
from logging.config import dictConfig

# set up logging
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

logFileHandler = FileHandler('pie.log', mode='w')
logFileHandler.setLevel(logging.DEBUG)
logFileHandler.setFormatter(myFormatter)

logger = logging.getLogger('pie')
logger.addHandler(logFileHandler)

logger.setLevel(logging.DEBUG)
logger.debug('initialized pie.log')

# load dht temperature/humidity sensor library
try:
	import Adafruit_DHT 
	logger.info('Loaded Adafruit_DHT')
except:
	Adafruit_DHT = None
	logger.warning('Did not load Adafruit_DHT')

import bUtil
from bCamera import bCamera
from bPins import PinThread
from bSerial import mySerialThread
from version import __version__


#########################################################################
class bTrial():
	"""
	Enapsulates a trial. Reads config json file, keeps self.runtime up to date,
	will start trial with user input and/or external GPIO trigger, catches input GPIO
	and logs to file, controls raspberry pi camera (bCamera).
	
	Threads: lights, temperature/humidity, serial
	"""

	def __init__(self):

		self.systemInfo = bUtil.getSystemInfo()

		self.config = None
		self.loadConfigFile(initGPIO=False) # load config_default.json
		
		if self.config['video']['useCamera']:
			self.cameraErrorQueue = queue.Queue()
			self.camera = bCamera(trial=self, cameraErrorQueue=self.cameraErrorQueue)
		else:
			self.cameraErrorQueue = None
			self.camera = None
		self.cameraResponseStr = []
				
		# the time the server (this code) was started, use to get server uptime
		self.startTimeSeconds = time.time() 
		
		#
		# runtime
		self.runtime = OrderedDict()

		self.runtime['trialNum'] = 0
		self.runtime['isRunning'] = False
		self.runtime['startTimeSeconds'] = None
		self.runtime['numFrames'] = 0
		self.runtime['startDateStr'] = ''
		self.runtime['startTimeStr'] = ''

		self.runtime['currentEpoch'] = None
		self.runtime['lastEpochSeconds'] = None # start time of epoch

		# see newEvent()
		self.runtime['eventTypes'] = []
		self.runtime['eventValues'] = []
		self.runtime['eventStrings'] = []
		self.runtime['eventTimes'] = [] # relative to self.runtime['startTimeSeconds']
		self.runtime['eventTicks'] = []
		'''
		self.runtime['perf_counter'] = []
		self.runtime['lastFrameInterval'] = []
		'''
		
		#self.runtime['lastFrameTime'] = None
		
		self.runtime['currentFile'] = ''
		self.runtime['lastStillTime'] = None

		self.runtime['lastResponse'] = 'None'

		self.runtime['scopeFilename'] = '' # set by self.setScopeFilename()
		
		# index into list self.config['hardware']['eventOut']
		# will be assigned in initGPIO_()
		'''
		self.triggerOutIndex = 0
		self.whiteLEDIndex = 1
		self.irLEDIndex = 2
		'''
		
		#
		# GPIO
		#self.initGPIO_()

		"""
		testing frame thread to improve detection and precision
		"""
		self.myPinThread = PinThread(self)
		self.myPinThread.init(self.config, initFirstTime=True)
		# PinThread does nothing in its run() function
		#self.myPinThread.daemon = True
		#self.myPinThread.start()

		#
		# lights thread
		self.lightsThread = None
		self.lightsThread = threading.Thread(target = self.myLightsThread)
		self.lightsThread.daemon = True
		self.lightsThread.start()
		
		#
		# serial thread
		self.serialResponseStr = []
		self.inSerialQueue = queue.Queue() # queue is infinite length
		self.outSerialQueue = queue.Queue()
		self.errorSerialQueue = queue.Queue()
		port = self.config['hardware']['serial']['port']
		baud = self.config['hardware']['serial']['baud']
		self.mySerialThread = None
		# start serial thread
		self.mySerialThread = mySerialThread(self.inSerialQueue, self.outSerialQueue, self.errorSerialQueue, port, baud)
		self.mySerialThread.daemon = True
		self.mySerialThread.start()
		
		#
		# temperature thread
		if Adafruit_DHT is not None:
			sensorPin = self.config['hardware']['dhtsensor']['pin']
			# pigpio
			# todo: fix this
			if self.myPinThread.pigpiod:
				logger.debug('did not start temperature thread with pigpiod')
			else:
				#logger.debug('starting temperature thread')
				GPIO.setup(sensorPin, GPIO.IN) # pins 2/3 have 1K8 pull up resistors
				myThread = threading.Thread(target = self.tempThread)
				myThread.daemon = True
				myThread.start()
		else:
			logger.warning('Adafruit_DHT is not loaded')

		# done initializing
		now = datetime.now()
		tmpStartTime = 'on ' + now.strftime('%Y-%m-%d') + ' at ' + now.strftime('%H:%M:%S')
		self.runtime['lastResponse'] = 'PiE server started ' + tmpStartTime
		
	def serialInAppend(self, type, str):
		"""
		type : (str) can be either 'command' or 'dump'
				if type is 'command' then 'str' is command
				if type is 'dump' then str is full path to file
		"""
		if self.mySerialThread:
			serialDict = {}
			serialDict['type'] = type
			serialDict['str'] = str
			
			#print('serialInAppend() serialDict:', serialDict)
			self.inSerialQueue.put(serialDict)
		else:
			logger.error('serial thread self.mySerialThread not defined')
			pass
			
	#########################################################################
	# property
	#########################################################################
	@property
	def lastResponse(self):
		return '' if self.runtime is None else self.runtime['lastResponse']
	
	@lastResponse.setter
	def lastResponse(self, str):
		try:
			self.runtime['lastResponse'] = str
		except (AttributeError) as e:
			pass
			
	@property
	def isRunning(self):
		return self.runtime['isRunning']

	@property
	def timeElapsed(self):
		""" Time elapsed since startTimeSeconds """
		if self.isRunning:
			return round(time.time() - self.runtime['startTimeSeconds'], 2)
		else:
			return None
	
	@property
	def epochTimeElapsed(self):
		if self.isRunning:
			return round(time.time() - self.runtime['lastEpochSeconds'], 1)
		else:
			return None
			
	@property
	def numFrames(self):
		return self.runtime['numFrames']
		
	@property
	def currentEpoch(self):
		return self.runtime['currentEpoch']

	@property
	def currentTrial(self):
		return self.runtime['trialNum']

		
	#########################################################################
	# Set from REST interface. Use these to have other machines tell us stuff
	#########################################################################
	def setAnimalID(self, animalID):
		"""
		Rest interface used by Igor to set animal id
		"""
		self.config['trial']['animalID'] = animalID
		self.lastResponse = 'Animal ID is now "' + animalID + '"'
		
	def setConditionID(self, conditionID):
		"""
		Rest interface used by Igor to set condition id
		"""
		self.config['trial']['conditionID'] = conditionID
		self.lastResponse = 'Condition ID is now "' + conditionID + '"'

	def setScopeFilename(self, scopeFilename):
		"""
		Used by PrairieView to set the name of the file acquired.
		Will be saved in trial file.
		Need to set this before stopTrial(), make sure trial is longer than image acquisition
		"""
		if self.isRunning:
			self.runtime['scopeFilename'] = scopeFilename
			self.lastResponse = 'Scope filename is now:' + scopeFilename
		else:
			self.lastResponse = 'Can not set scope filename when trial is not running'

	#########################################################################
	# status
	#########################################################################
	def getStatus(self):
		status = OrderedDict()
		status['config'] = self.config
		status['runtime'] = self.runtime

		now = datetime.now()
		status['runtime']['currentDate'] = now.strftime('%Y-%m-%d')
		status['runtime']['currentTime'] = now.strftime('%H:%M:%S')

		status['runtime']['currentFile'] = self.camera.currentFile
		status['runtime']['secondsElapsedStr'] = self.camera.secondsElapsedStr
		status['runtime']['cameraState'] = self.camera.state
		
		# added this because 'armed' checkbox cannot bind to a primitive (e.g. $scope.isArmed)
		# it needs to bind to an object property
		# this seems to be a bug in angularjs and took 3+ days to figure out
		if self.camera.state in ['armed', 'armedrecording']:
			status['runtime']['cameraIsArmed'] = True
		else:
			status['runtime']['cameraIsArmed'] = False
			
		if self.camera.lastStillTime > 0:
			status['runtime']['lastStillTime'] = time.strftime('%Y%m%d %H:%M:%S', time.localtime(self.camera.lastStillTime)) 
		else:
			status['runtime']['lastStillTime'] = 'None'
		
		status['runtime']['numFrames'] = self.runtime['numFrames'] #self.numFrames

		status['systemInfo'] = self.systemInfo # remember to update occasionally
		status['systemInfo']['version'] = __version__
		status['systemInfo']['uptime'] = str(timedelta(seconds = time.time() - self.startTimeSeconds)).split('.')[0]

		while not self.cameraErrorQueue.empty():
			cameraItem = self.cameraErrorQueue.get(block=False)
			#print('   ****** trial.getStatus() cameraErrorQueue cameraItem:', cameraItem)
			self.cameraResponseStr.append(cameraItem)
			
			# any camera error puts server state into idle
			'''
			print('   ***** trial.getStatus() setting camera state to idle')
			self.camera.state = 'idle'
			status['runtime']['cameraState'] = 'idle'
			status['runtime']['cameraIsArmed'] = False
			print("status['runtime']['cameraState']=", status['runtime']['cameraState'])
			'''
			
		if self.cameraResponseStr:	
			status['runtime']['cameraQueue'] = self.cameraResponseStr
		else:
			status['runtime']['cameraQueue'] = ['None']

		#
		# append both outSerialQueue and errorSerialQueue to serialResponseStr
		while not self.outSerialQueue.empty():
			serialItem = self.outSerialQueue.get(block=False)
			self.serialResponseStr.append(serialItem)

		while not self.errorSerialQueue.empty():
			serialItem = self.errorSerialQueue.get(block=False)
			#print('   errorSerialQueue serialItem:', serialItem)
			self.serialResponseStr.append(serialItem)

		if self.serialResponseStr:	
			status['runtime']['serialQueue'] = self.serialResponseStr
		else:
			status['runtime']['serialQueue'] = ['None']
				
		return status
	
	#########################################################################
	# refresh system info (hard drive space remaining)
	#########################################################################
	def refreshSystemInfo(self):
		self.systemInfo = bUtil.getSystemInfo()	
		
	#########################################################################
	# update config, led, animal
	#########################################################################
	def updateConfig(self, configDict):
		"""
		Update self.config (['trial'], ['lights'], ['video'])
		Only update the subset that can be changed by user in javascript configFormController
		Remember, ['motor'] is saved in a different controller, arduinoFormController
		"""

		self.runtime['trialNum'] = configDict['trial']['trialNum']
		
		self.config['trial'] = configDict['trial']
		self.config['lights'] = configDict['lights']
		self.config['video'] = configDict['video']
		
		self.config['hardware']['allowArming'] = configDict['hardware']['allowArming']
		self.config['hardware']['serial']['useSerial'] = configDict['hardware']['serial']['useSerial']

		self.config['hardware'] = configDict['hardware']
		
		self.lastResponse = 'Updated configure'
		
	def updatePins(self, configDict):
		#print('=== bTrial.updatePins()')
		self.config['hardware']['eventIn'] = configDict['hardware']['eventIn']
		self.config['hardware']['eventOut'] = configDict['hardware']['eventOut']
		self.config['hardware']['dhtsensor'] = configDict['hardware']['dhtsensor']
		self.initGPIO_()

		self.lastResponse = 'Updated pins'
		
	# 20181024, while working on processing
	# this needs to be made more bullet proof, assuming ledIdx is in (1,2)
	def updateLED2(self, ledIdx, newValue):
		self.config['hardware']['eventOut'][ledIdx]['state'] = newValue
		# set actual pins
		self.myPinThread.eventOut('whiteLED', newValue)
		
	def updateLED(self, configDict, allowAuto=True):
		
		now = time.time()
		
		# todo: fix this logic
		# get the indices into config dictionary
		whiteLEDIndex = None
		for idx, eventOut in enumerate(configDict['hardware']['eventOut']):
			if eventOut['name'] == 'whiteLED':
				whiteLEDIndex = idx
				break
				
		irLEDIndex = None
		for idx, eventOut in enumerate(configDict['hardware']['eventOut']):
			if eventOut['name'] == 'irLED':
				irLEDIndex = idx
				break
				
		# grab what we just received
		newWhite = configDict['hardware']['eventOut'][whiteLEDIndex]['state']
		newIR = configDict['hardware']['eventOut'][irLEDIndex]['state']
		newAuto = configDict['lights']['auto']

		wasWhite = self.config['hardware']['eventOut'][whiteLEDIndex]['state']
		wasIR = self.config['hardware']['eventOut'][irLEDIndex]['state']
		wasAuto = self.config['lights']['auto']

		if not allowAuto and self.config['lights']['auto']:
			self.lastResponse = 'Can not set lights when in auto mode'
			pass
		else:
			self.config['hardware']['eventOut'][whiteLEDIndex]['state'] = newWhite
			self.config['hardware']['eventOut'][irLEDIndex]['state'] = newIR

			# set actual pins
			self.myPinThread.eventOut('whiteLED', newWhite)
			self.myPinThread.eventOut('irLED', newIR)
				
			# only log when we make a change
			if newWhite != wasWhite:
				#print('white status change')
				self.newEvent('whiteLED', newWhite, now=now)
			if newIR != wasIR:
				#print('ir status change')
				self.newEvent('irLED', newIR, now=now)

			# if we made any changes
			if newWhite != wasWhite or newIR != wasIR:
				# respond with what we just did
				newWhiteStr = 'On' if newWhite else 'Off'
				newIRStr = 'On' if newIR else 'Off'
				newAutoStr = 'On' if newAuto else 'Off'
				self.lastResponse = 'Updated lights, white:' + newWhiteStr + ' ir:' + newIRStr + ' auto:' + newAutoStr 

		self.config['lights']['auto'] = newAuto

		
	def updateAnimal(self, configDict):
		self.config['trial']['animalID'] = configDict['trial']['animalID']
		self.config['trial']['conditionID'] = configDict['trial']['conditionID']
		
		self.lastResponse = 'Updated ID:"' + self.config['trial']['animalID'] + '" Condition:"' + self.config['trial']['conditionID'] + '"'

	#########################################################################
	# load and save config file
	#########################################################################
	def loadConfigFile(self, thisFile='config_default.json', initGPIO=True):
		"""
		Load a json config file, setting self.config. Optionally initialize GPIO
		
		config_default.json is not included in git repository
		"""
		
		#print('=== bTrial.loadConfigFile()')
		
		logger.info('loading config file: ' + thisFile)

		mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
		configpath = os.path.join(mypath, 'config') # *this/config
		configpath = os.path.join(configpath, thisFile) # *this/config/<thisFile>
		
		if not os.path.isfile(configpath):
			logger.info('Config file not found: ' + configpath)
			# switch to config_factory_defaults.json
			thisFile = 'config_factory_defaults.json'
			configpath = os.path.join(mypath, 'config') # *this/config
			configpath = os.path.join(configpath, thisFile) # *this/config/<thisFile>
			logger.info('Defaulting to ' + configpath)
			
		with open(configpath) as configFile:
			try:
				config = json.load(configFile, object_pairs_hook=OrderedDict)
			except ValueError as e:
				logger.error('config.json ValueError: ' + str(e))
				# if there is an error in loading config file (json is wrong) we REALLY want to exit
				sys.exit(1)
			#201812, why was thin in else clause? does else cluase get executed when 'try' suceeds?
			#else:
			#logger.debug('loaded config file: ' + thisFile)
			#logger.debug('calling initGPIO_() to re-initialize the Raspberry GPIO')
			self.config = config
			if initGPIO:
				self.initGPIO_()
			self.lastResponse = 'Loaded configuration file ' + thisFile
			return config

	def saveConfig(self):
		""" Save self.config to a file """

		mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
		configpath = os.path.join(mypath, 'config') # *this/config
		configpath = os.path.join(configpath, 'config_default.json') # *this/config/config_default.json

		with open(configpath, 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved configuration config_default.json'

		logger.debug('saveConfig saved: ' + configpath)
	
	def getConfig(self, key1, key2):
		""" Get a single config parameter """
		if not key1 in self.config:
			#error
			raise
		else:
			if not key2 in self.config[key1]:
				# error
				raise
			else:
				return self.config[key1][key2]
	
	#########################################################################
	# GPIO
	#########################################################################
	def initGPIO_(self):
		"""
		Init gpio pins with data in self.config dict (loaded from json file)
		"""
		#print('=== bTrial.initGPIO_()')
		self.myPinThread.init(self.config)
					
	#########################################################################
	# start/stop a trial
	#########################################################################
	def startTrial(self, startArmVideo=False, now=None):
		"""
		pass startArmVideo = True when calling from WITHIN startArmVideo loop
		"""
		if now is None:
			now = time.time()
			
		if self.isRunning:
			logger.warning('start trial aborted, already running')
			return False

		logger.debug('startTrial')

		if self.camera is not None:
			if startArmVideo:
				# *this function startTrial() is being called from within the startarmvideo loop
				pass
			else:
				# 20180815, before we start the thread, make sure we can get the camera
				if self.camera.initCamera_() is None:
					# error
					#print('   ### ### bCamera.arm was not able to access camera')
					return False
				else:
					self.camera.releaseCamera()

		self.runtime['trialNum'] = self.runtime['trialNum'] + 1
		
		self.runtime['startArmVideo'] = startArmVideo
		
		self.runtime['isRunning'] = True
		
		self.runtime['startTimeSeconds'] = now
		self.runtime['startDateStr'] = time.strftime('%Y%m%d', time.localtime(now))
		self.runtime['startTimeStr'] = time.strftime('%H:%M:%S', time.localtime(now))
		
		self.runtime['numFrames'] = 0

		self.runtime['currentEpoch'] = 0
		self.runtime['lastEpochSeconds'] = now
		
		# keep track of events, these are appended to in newEvent() and saved in saveTrial()
		self.runtime['eventTypes'] = []
		self.runtime['eventValues'] = []
		self.runtime['eventStrings'] = []
		self.runtime['eventTimes'] = [] # relative to self.runtime['startTimeSeconds']
		self.runtime['eventTicks'] = []
		
		self.runtime['currentFile'] = 'n/a' # video
		self.runtime['lastStillTime'] = None
		
		self.runtime['scopeFilename'] = '' # set by self.setScopeFilename()
				
		self.newEvent('startTrial', self.runtime['trialNum'], now=now)
		
		if self.camera is not None:
			if startArmVideo:
				# *this function startTrial() is being called from within the startarmvideo loop
				# watermark video with trial start
				if self.camera is not None:
					self.camera.annotate(newAnnotation='S')
				#pass
			else:
				self.camera.record(True, startNewTrial=False)

		"""
		todo: I need to fix this, it is sending out when we get externally triggered
		"""
		#
		# triggerOut
		#
		#201812, I really need to fix this, i need to know the feault state (True) and send opposite
		# was this
		#self.myPinThread.eventOut('triggerOut', True)
		self.myPinThread.eventOut('triggerOut', False)

		'''
		if self.triggerOutIndex is not None:
			triggerOutDict = self.config['hardware']['eventOut'][self.triggerOutIndex]
			enabled = triggerOutDict['enabled']
			if enabled:
				# trigger out pin will remain (! defaultValue) during entire trial
				pin = triggerOutDict['pin']
				defaultValue = triggerOutDict['defaultValue']
				thisValue = not defaultValue
				#logger.info('triggerOut pin:' + str(pin) + ' value:' + str(thisValue))
				
				# pigpio
				GPIO.output(pin, thisValue)
			else:
				logger.info('triggerOut not enabled')
		'''
		
		#
		# report that we started a trial
		nowStr = time.strftime('%H:%M:%S', time.localtime(now))
		if self.runtime['startArmVideo']:
			startArmStr = 'ARMED'
		else:
			startArmStr = ''
		self.lastResponse = 'Start ' + startArmStr + ' trial ' + str(self.currentTrial) + ' repeat ' + str(self.currentEpoch) + ' at ' + nowStr
		
	def stopTrial(self):
		"""
		stop a trial and save file
		"""
		now = time.time()

		if not self.isRunning:
			logger.warning('stopTrial but trial is not running')
			return 0
			
		logger.debug('stopTrial')
		self.newEvent('stopTrial', self.runtime['trialNum'], now=now)
		self.runtime['isRunning'] = False
		self.saveTrial()

		if self.runtime['startArmVideo']:
			if self.camera is not None:
				# *this function startTrial() is being called from with the startarmvideo loop
				pass
		else:
			if self.camera is not None:
				self.camera.record(False)

		# clear annotations on video
		if self.camera is not None:
			self.camera.annotate(newAnnotation='')

		# tell arduino to stop
		# this is not symetric, NOT sending serial on start
		# but sending serial here in case user hits stop
		# maybe make this use other teensy pin for 'emergency stop
		self.serialInAppend('command', 'stop')

		# triggerOut
		#201812, this need to be paired with startTRial
		# was this
		#self.myPinThread.eventOut('triggerOut', False)
		self.myPinThread.eventOut('triggerOut', True)
		
		'''
		if self.triggerOutIndex is not None:
			triggerOutDict = self.config['hardware']['eventOut'][self.triggerOutIndex]
			enabled = triggerOutDict['enabled']
			if enabled:
				pin = triggerOutDict['pin']
				defaultValue = triggerOutDict['defaultValue']
				logger.debug('stopTrial pin:' + str(pin) + ' value:' + str(defaultValue))
				
				# pigpio
				GPIO.output(pin, defaultValue)
		'''
				
		#
		# report that we stopped a trial
		nowStr = time.strftime('%H:%M:%S', time.localtime(now))
		if self.runtime['startArmVideo']:
			startArmStr = 'ARMED'
		else:
			startArmStr = ''
		self.lastResponse = 'Stopped ' + startArmStr + ' trial ' + str(self.currentTrial) + ' repeat ' + str(self.currentEpoch) + ' at ' + nowStr

	#def newEvent(self, type, val, str='', now=None, tick=None, perf_counter=None, lastFrameInterval=None):
	def newEvent(self, type, val, str='', now=None, tick=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.runtime['eventTypes'].append(type)
			self.runtime['eventValues'].append(val)
			self.runtime['eventStrings'].append(str)
			self.runtime['eventTimes'].append(now) # when saving, derive (*this - self.runtime['startTimeSeconds'])
			self.runtime['eventTicks'].append(tick)
			#self.runtime['perf_counter'].append(perf_counter)
			#self.runtime['lastFrameInterval'].append(lastFrameInterval)

	def newEpoch(self, now=None):
		"""
		epoch is repeat in user interface
		"""
		if now is None:
			now = time.time()
		if self.isRunning:
			self.runtime['currentEpoch'] += 1
			self.runtime['lastEpochSeconds'] = now
			self.newEvent('newRepeat', self.currentEpoch, now=now)
	
			nowStr = time.strftime('%H:%M:%S', time.localtime(now))

			if self.runtime['startArmVideo']:
				startArmStr = 'armed'
			else:
				startArmStr = ''
			self.lastResponse = 'Start ' + startArmStr + ' trial ' + str(self.currentTrial) + ' repeat ' + str(self.currentEpoch) + ' at ' + nowStr
		
	def getFilename(self, useStartTime=False, withRepeat=False):
		"""
		Get a base filename from trial
		Caller is responsible for appending proper filetype extension
		"""
		hostnameID_str = ''
		if self.config['trial']['includeHostname']:
			hostnameID_str = '_' + self.systemInfo['hostname'] # we always have a host name
		animalID_str = ''
		if self.config['trial']['animalID']:
			animalID_str = '_' + self.config['trial']['animalID']
		conditionID_str = ''
		if self.config['trial']['conditionID']:
			conditionID_str = '_' + self.config['trial']['conditionID']
		if useStartTime:
			# time the trial was started
			useThisTime = time.localtime(self.runtime['startTimeSeconds'])
		else:
			# time the epoch was started
			useThisTime = time.localtime(self.runtime['lastEpochSeconds'])
		timeStr = time.strftime('%Y%m%d_%H%M%S', useThisTime) 
		
		# file names have (hostname, animal, condition, trial)
		filename = timeStr + hostnameID_str + animalID_str + conditionID_str + '_t' + str(self.runtime['trialNum'])
		if withRepeat:
			filename += '_r' + str(self.currentEpoch)
		return filename
		
	def saveTrial(self):
		delim = ','
		eol = '\n'
		saveFile = self.getFilename(useStartTime=True) + '.txt'
		savePath = os.path.join('/home/pi/video', self.runtime['startDateStr'])
		saveFilePath = os.path.join(savePath, saveFile)
		if not os.path.exists(savePath):
			os.makedirs(savePath)
		with open(saveFilePath, 'w') as file:
			# one line header
			# todo: clean up numRepeats = ['currentEpoch']
			headerLine = 'date=' + self.runtime['startDateStr'] + ';' \
							'time=' + self.runtime['startTimeStr'] + ';' \
							'startTimeSeconds=' + str(self.runtime['startTimeSeconds']) + ';' \
							'hostname=' + '"' + self.systemInfo['hostname'] + '"' + ';' \
							'id=' + '"' + self.config['trial']['animalID'] + '"' + ';' \
							'condition=' + '"' + self.config['trial']['conditionID'] + '"' + ';' \
							'trialNum=' + str(self.runtime['trialNum']) + ';' \
							'numRepeats=' + str(self.runtime['currentEpoch']) + ';' \
							'repeatDuration=' + str(self.config['trial']['repeatDuration']) + ';' \
							'numRepeatsRecorded=' + str(self.config['trial']['numberOfRepeats']) + ';' \
							'repeatInfinity=' + '"' + str(self.config['trial']['repeatInfinity']) + '"' + ';' \
							'scopeFilename'  + '"' + self.runtime['scopeFilename'] + '"' + ';'

			if self.camera is not None:
				cameraHeader = 'video_fps=' + str(self.config['video']['fps']) + ';' \
							'video_resolution=' + '"' + self.config['video']['resolution'] + '"' + ';'
				headerLine += cameraHeader
			
			headerLine += eol						
			file.write(headerLine)
			# column header for event data is (date, time, sconds, event, value, str
			''' pigpio
							#'ticks' + delim + \
							#'perf_counter' + delim + \
							#'lastFrameInterval' + delim + \
			'''
			columnHeader = 'date' + delim + 'time' + delim + \
							'linuxSeconds' + delim + 'secondsSinceStart' + delim + \
							'event' + delim + \
							'value' + delim + \
							'str' + delim + \
							'tick' + eol
			file.write(columnHeader)
			# one line per event
			for idx, eventTime in enumerate(self.runtime['eventTimes']):
				# convert epoch seconds to date/time str 
				dateStr = time.strftime('%Y%m%d', time.localtime(eventTime))
				timeStr = time.strftime('%H:%M:%S', time.localtime(eventTime))
				# need the plus at end of each line here
				#secondsSinceStart = round(eventTime - self.runtime['startTimeSeconds'],4)
				secondsSinceStart = eventTime - self.runtime['startTimeSeconds']
				'''
				eventTicks is only used for pigpio frame
				'''
				frameLine = dateStr + delim + \
							timeStr + delim + \
							str(eventTime) + delim + \
							str(secondsSinceStart) + delim + \
							self.runtime['eventTypes'][idx] + delim + \
							str(self.runtime['eventValues'][idx]) + delim + \
							self.runtime['eventStrings'][idx] + delim + \
							str(self.runtime['eventTicks'][idx])
				frameLine += eol
				file.write(frameLine)

		logger.info('saved: ' + saveFilePath)
		
		#
		# grab from arduino/teensy and save
		teensySavePath = os.path.join('/home/pi/video', self.runtime['startDateStr'])
		teensyFile = self.getFilename(useStartTime=True) + '_a.txt' # a is for arduino
		saveFilePath = os.path.join(savePath, teensyFile)
		self.serialInAppend('dump', saveFilePath)

	#########################################################################
	# NOT WORKING !!!
	#########################################################################
	def loadTrialFile(Self, path):
		"""
		load a .txt trial file
		"""
		ret = OrderedDict()
		ret['recordVideo'] = []
		if not os.path.isfile(path):
			return ret
		with open(path) as f:
			# parse one line header
			header = f.readline().strip()
			print('header 0:', header)
			if header.endswith(';'):
				# print('stripping ; from header', str(len(header)))
				header = header[0:len(header)-1] # python string index uses ':' and not ','
			print('header 1:', header)
			header = header.split(';') # header is a list of k=v
			# print('loadTrialFile() header:', header)
			for item in header:
				lhs,rhs = item.split('=')
				ret[lhs] = rhs
				
			# one line column names
			# todo: parse column names so we don't need to use [idx] below
			columnNames = f.readline().rstrip()
			# list of events, one per line
			event = f.readline().rstrip()
			while event:
				# print('   event:', event)
				event = event.split(',') # event is a list
				for item in event:
					# something like: 20180611,09:03:16,1528722196.370188,recordVideo,/home/pi/video/20180611/20180611_090316_hc1_animal_condition_t1_r2.h264
					itemType = item[3]
					if itemType == 'recordVideo':
						recordVideo = {}
						recordVideo['repeat'] = item[4]
						recordVideo['videoFile'] = item[5]
						ret['recordVideo'].append(recordVideo)
				event = f.readline().rstrip()
		return ret
		
	#############################################################
	# Background threads
	#############################################################
	def myLightsThread(self):
		logger.debug('starting myLightsThread')
		while True:
			if self.config['lights']['auto']:
				now = datetime.now()

				# todo: get rid of this garbage
				whiteLEDIndex = None
				for idx, eventOut in enumerate(self.config['hardware']['eventOut']):
					if eventOut['name'] == 'whiteLED':
						whiteLEDIndex = idx
						break
				
				irLEDIndex = None
				for idx, eventOut in enumerate(self.config['hardware']['eventOut']):
					if eventOut['name'] == 'irLED':
						irLEDIndex = idx
						break
				
				# grab what we just received
				tmpConfig = self.config

				isDaytime = now.hour >= float(self.config['lights']['sunrise']) and now.hour < float(self.config['lights']['sunset'])
				if isDaytime:
					# was this
					#self.myPinThread.eventOut('whiteLED', True)
					#self.myPinThread.eventOut('irLED', False)
					# now this
					tmpConfig['hardware']['eventOut'][whiteLEDIndex]['state'] = True
					tmpConfig['hardware']['eventOut'][irLEDIndex]['state'] = False
					self.updateLED(tmpConfig, allowAuto=True)
				else:
					# was this
					#self.myPinThread.eventOut('whiteLED', False)
					#self.myPinThread.eventOut('irLED', True)				
					tmpConfig['hardware']['eventOut'][whiteLEDIndex]['state'] = False
					tmpConfig['hardware']['eventOut'][irLEDIndex]['state'] = True
					self.updateLED(tmpConfig, allowAuto=True)
			time.sleep(1)
		logger.debug('stopping myLightsThread')

	def tempThread(self):
		"""
		Thread to run temperature/humidity in background
		Adafruit DHT sensor code is blocking
		"""
		lastTemperatureTime = 0
		
		#print('Adafruit_DHT.DHT11:', Adafruit_DHT.DHT11)
		dhtSensorDict_ = { 'DHT11': Adafruit_DHT.DHT11, 'DHT22': Adafruit_DHT.DHT22, 'AM2302': Adafruit_DHT.AM2302}
		sensorTypeStr = self.config['hardware']['dhtsensor']['sensorType']
		sensorType = dhtSensorDict_[sensorTypeStr]
		
		pin = self.config['hardware']['dhtsensor']['pin']

		logger.info('starting temperature thread')
		logger.info('sensorTypeStr:' + sensorTypeStr + ' sensorType:' + str(sensorType) + ' pin:' + str(pin))

		while True:
			now = time.time()

			readtemperature = self.config['hardware']['dhtsensor']['readtemperature']
			temperatureInterval = self.config['hardware']['dhtsensor']['temperatureInterval'] # seconds
			continuouslyLog = self.config['hardware']['dhtsensor']['continuouslyLog']

			if readtemperature and (now > lastTemperatureTime + temperatureInterval):
				try:
					humidity, temperature = Adafruit_DHT.read_retry(sensorType, pin)
					if humidity is not None and temperature is not None:
						lastTemperature = round(temperature, 2)
						lastHumidity = round(humidity, 2)
						# log this to a file
						self.newEvent('temperature', lastTemperature)
						self.newEvent('humidity', lastHumidity)
						if continuouslyLog:
							# 1) save in main /home/pi/video folder
							logPath = self.getConfig('trial', 'savePath')
							logPath = os.path.join(logPath,'logs')							
							# 2) save a second copy based on server start time
							logPath2 = self.getConfig('trial', 'savePath')
							logPath2 = os.path.join(logPath2,'logs')							
							tmpDateStr = time.strftime('%Y%m%d', time.localtime(self.startTimeSeconds))
							tmpTimeStr = time.strftime('%H%M%S', time.localtime(self.startTimeSeconds))
							
							if not os.path.isdir(logPath):
								os.makedirs(logPath)
							
							# all log files will start with a header
							headerLine = "Host,DateTime,Seconds,Temperature,Humidity,whiteLight,irLight" + '\n'
							
							# 1
							logFile = os.path.join(logPath, 'environment.log')
							if not os.path.isfile(logFile):
								with open(logFile, 'a') as f:
									f.write(headerLine)
							# 2
							tmpLogFileName = tmpDateStr + '_' + tmpTimeStr + '.log'
							logFile2 = os.path.join(logPath2, tmpLogFileName)
							if not os.path.isfile(logFile2):
								with open(logFile2, 'a') as f:
									f.write(headerLine)
							
							dateTimeStr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
							secondsStr = str(now)
							lineStr = self.systemInfo['hostname'] + ',' \
								+ dateTimeStr + ',' \
								+ secondsStr + ',' \
								+ str(lastTemperature) + ',' \
								+ str(lastHumidity) + ',' \
								+ '' + ',' \
								+ '' \
								+ '\n' 
							with open(logFile, 'a') as f: # 1
								f.write(lineStr)
							with open(logFile2, 'a') as f: # 2
								f.write(lineStr)
					else:
						logger.warning('temperature/humidity error, sensorType:' + sensorTypeStr + ' ' + str(sensorType) + ' pin:' + str(pin) + ' temperatureInterval:' + str(temperatureInterval))
					# set even on fail, this way we do not immediately hit it again
					lastTemperatureTime = time.time()
				except:
					logger.error('exception reading temp/hum')
					#raise
			# 
			time.sleep(temperatureInterval/2)

		logger.info('tempThread() stop')
	
if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

		
