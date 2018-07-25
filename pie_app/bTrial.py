# Robert H Cudmore
# 20180525

import os, sys, time, json, threading, queue, subprocess
from collections import OrderedDict
from datetime import datetime, timedelta
import pprint
import serial
import RPi.GPIO as GPIO

import logging

from logging import FileHandler #RotatingFileHandler
from logging.config import dictConfig

#
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
logger.debug('bTrial initialized pie.log')
logger.debug('RPi.GPIO VERSION:' + str(GPIO.VERSION))

#
# load dht temperature/humidity sensor library
try:
	import Adafruit_DHT 
	logger.debug('Loaded Adafruit_DHT')
except:
	Adafruit_DHT = None
	logger.warning('Did not load Adafruit_DHT')

import bUtil
from bCamera import bCamera
from version import __version__

#########################################################################
class mySerialThread(threading.Thread):
	"""
	background thread which monitors inSerialQueue and sends commands out serial.
	"""
	def __init__(self, inSerialQueue, outSerialQueue, errorSerialQueue, port, baud):
		threading.Thread.__init__(self)
		self.inSerialQueue = inSerialQueue
		self.outSerialQueue = outSerialQueue
		self.errorSerialQueue = errorSerialQueue
		self.port = port #'/dev/ttyACM0'
		self.baud = baud #115200
		logger.debug('mySerialThread initializing, port:' + str(port) + ' baud:' + str(baud))
		
		self.mySerial = None
		try:
			# there is no corresponding self.mySerial.close() ???
			self.mySerial = serial.Serial(port, baud, timeout=0.25)
		except (serial.SerialException) as e:
			logger.error(str(e))
			errorSerialQueue.put(str(e))
		except:
			logger.error('other exception in mySerialThread init')
			raise
		#else:
		#	errorSerialQueue.put('None')

	def run(self):
		logger.debug('mySerialThread.run() starting')
		while True:
			try:
				# serialDict is {'type': command/dump, 'str': command/filePath}
				serialDict = self.inSerialQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				# there was nothing in the queue
				pass
			else:
				# there was something in the queue
				#logger.info('serialThread inSerialQueue: "' + str(serialCommand) + '"')
				
				serialType = serialDict['type']
				serialCommand = serialDict['str']
				try:
					if self.mySerial is not None:
						if serialType == 'dump':
							# dump a teensy/arduino trial to a file
							fullSavePath = serialCommand
							self.mySerial.write('d\n'.encode()) # write 'd\n'

							#time.sleep(0.01)

							resp = self.mySerial.readline().decode().strip()
							with open(fullSavePath, 'w') as file:
								while resp:
									file.write(resp + '\n')
									resp = self.mySerial.readline().decode().strip()
						elif serialType == 'command':
							# send a command to teensy and get one line response
							if not serialCommand.endswith('\n'):
								serialCommand += '\n'
							self.mySerial.write(serialCommand.encode())

							#time.sleep(0.01)
						
							resp = self.mySerial.readline().decode().strip()
							self.outSerialQueue.put(resp)
							logger.info('serialThread outSerialQueue: "' + str(resp) + '"')
						else:
							logger.error('bad serial command type' + str(serialDict))
				except (serial.SerialException) as e:
					logger.error(str(e))
				except:
					logger.error('other exception in mySerialThread run')
					raise

			# make sure not to remove this
			time.sleep(0.005)

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
		self.runtime['startDateStr'] = ''
		self.runtime['startTimeStr'] = ''

		self.runtime['currentEpoch'] = None
		self.runtime['lastEpochSeconds'] = None # start time of epoch

		self.runtime['eventTypes'] = []
		self.runtime['eventValues'] = []
		self.runtime['eventStrings'] = []
		self.runtime['eventTimes'] = [] # relative to self.runtime['startTimeSeconds']

		self.runtime['currentFile'] = ''
		self.runtime['lastStillTime'] = None

		self.runtime['lastResponse'] = 'None'

		self.runtime['scopeFilename'] = '' # set by self.setScopeFilename()
		
		# index into list self.config['hardware']['eventOut']
		# will be assigned in initGPIO_()
		self.triggerOutIndex = None
		self.whiteLEDIndex = None
		self.irLEDIndex = None
		
		#
		# GPIO
		self.initGPIO_()

		#
		# lights thread
		self.lightsThread = threading.Thread(target = self.lightsThread)
		self.lightsThread.daemon = True
		self.lightsThread.start()

		#
		# temperature thread
		if Adafruit_DHT is not None:
			logger.debug('Initialized DHT temperature sensor')
			sensorPin = self.config['hardware']['dhtsensor']['pin']
			GPIO.setup(sensorPin, GPIO.IN) # pins 2/3 have 1K8 pull up resistors
			myThread = threading.Thread(target = self.tempThread)
			myThread.daemon = True
			myThread.start()
		else:
			#logger.debug('Did not load DHT temperature sensor')
			pass

		#
		# serial thread
		self.serialResponseStr = []
		self.inSerialQueue = queue.Queue() # queue is infinite length
		self.outSerialQueue = queue.Queue()
		self.errorSerialQueue = queue.Queue()
		# create, deamonize and start the serial thread
		port = self.config['hardware']['serial']['port']
		baud = self.config['hardware']['serial']['baud']
		self.mySerialThread = mySerialThread(self.inSerialQueue, self.outSerialQueue, self.errorSerialQueue, port, baud)
		self.mySerialThread.daemon = True
		self.mySerialThread.start()
		
		self.runtime['lastResponse'] = 'PiE server started'
		
	def serialInAppend(self, type, str):
		"""
		type : (str) can be either 'command' or 'dump'
				if type is 'command' then 'str' is command
				if type is 'dump' then str is full path to file
		"""
		if self.mySerialThread.mySerial:
			serialDict = {}
			serialDict['type'] = type
			serialDict['str'] = str
			self.inSerialQueue.put(serialDict)
		else:
			#logger.warning('serial port ' + self.mySerialThread.port + ' not defined: ' + str)
			pass
			
	#########################################################################
	# property
	#########################################################################
	@property
	def lastResponse(self):
		# this is a ternary operator and look complex
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
		return self.runtime['eventTypes'].count('frame')

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
		
		if self.camera.lastStillTime > 0:
			status['runtime']['lastStillTime'] = time.strftime('%Y%m%d %H:%M:%S', time.localtime(self.camera.lastStillTime)) 
		else:
			status['runtime']['lastStillTime'] = 'None'
		
		status['runtime']['numFrames'] = self.numFrames

		status['systemInfo'] = self.systemInfo # remember to update occasionally
		status['systemInfo']['version'] = __version__
		status['systemInfo']['uptime'] = str(timedelta(seconds = time.time() - self.startTimeSeconds)).split('.')[0]

		while not self.cameraErrorQueue.empty():
			cameraItem = self.cameraErrorQueue.get()
			print('   cameraErrorQueue cameraItem:', cameraItem)
			self.cameraResponseStr.append(cameraItem)
		if self.serialResponseStr:	
			status['runtime']['cameraQueue'] = self.cameraResponseStr
		else:
			status['runtime']['cameraQueue'] = ['None']

		#
		# append both outSerialQueue and errorSerialQueue to serialResponseStr
		while not self.outSerialQueue.empty():
			serialItem = self.outSerialQueue.get()
			self.serialResponseStr.append(serialItem)

		while not self.errorSerialQueue.empty():
			serialItem = self.errorSerialQueue.get()
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
		
		# was this
		self.config['hardware']['allowArming'] = configDict['hardware']['allowArming']
		self.config['hardware']['serial']['useSerial'] = configDict['hardware']['serial']['useSerial']

		self.config['hardware'] = configDict['hardware']
		
		self.lastResponse = 'Updated configure'
		
	def updatePins(self, configDict):
		self.config['hardware']['eventIn'] = configDict['hardware']['eventIn']
		self.config['hardware']['eventOut'] = configDict['hardware']['eventOut']
		self.config['hardware']['dhtsensor'] = configDict['hardware']['dhtsensor']
		self.initGPIO_()

		self.lastResponse = 'Updated pins'
		
	def updateLED(self, configDict):
		# grab what we just received
		newWhite = configDict['hardware']['eventOut'][self.whiteLEDIndex]['state']
		newIR = configDict['hardware']['eventOut'][self.irLEDIndex]['state']
		newAuto = configDict['lights']['auto']

		if self.config['lights']['auto']:
			self.lastResponse = 'Can not set lights when in auto mode'
			pass
		else:
			self.config['hardware']['eventOut'][self.whiteLEDIndex]['state'] = newWhite
			self.config['hardware']['eventOut'][self.irLEDIndex]['state'] = newIR
				
			# set actual pins
			self.eventOut('whiteLED', newWhite)
			self.eventOut('irLED', newIR)

		self.config['lights']['auto'] = newAuto

		newWhiteStr = 'On' if newWhite else 'Off'
		newIRStr = 'On' if newIR else 'Off'
		newAutoStr = 'On' if newAuto else 'Off'
		self.lastResponse = 'Updated lights, white:' + newWhiteStr + ' ir:' + newIRStr + ' auto:' + newAutoStr 
		
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
		logger.debug('loadConfigFile() loading file: ' + thisFile)

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
			else:
				#logger.debug('loaded config file: ' + thisFile)
				#logger.debug('calling initGPIO_() to re-initialize the Raspberry GPIO')
				self.config = config
				if initGPIO:
					self.initGPIO_()
				self.lastResponse = 'Loaded configuration file ' + thisFile
				return config

	def saveConfig(self):
		""" Save self.config to a file """
		logger.debug('saveConfig')

		mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
		configpath = os.path.join(mypath, 'config') # *this/config
		configpath = os.path.join(configpath, 'config_default.json') # *this/config/config_default.json

		with open(configpath, 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved configuration config_default.json'
	
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

		polarityDict_ = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
		pullUpDownDict = { 'up': GPIO.PUD_UP, 'down': GPIO.PUD_DOWN}

		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		self.triggerOutIndex = None # assigned below when we find 'triggerOut'
		self.whiteLEDIndex = None
		self.irLEDIndex = None
		
		#
		# events in (e.g. frame)
		for idx,eventIn in enumerate(self.config['hardware']['eventIn']):
			# as long as each event has different pin, polarity can be different
			name = eventIn['name']
			pin = eventIn['pin']

			polarityStr = eventIn['polarity'] #rising, falling, both
			polarity = polarityDict_[polarityStr]

			pull_up_downStr = eventIn['pull_up_down'] # up or down
			pull_up_down = pullUpDownDict[pull_up_downStr]

			
			bouncetime = eventIn['bouncetime']
			enabled = eventIn['enabled'] # is it enabled to receive events

			self.config['hardware']['eventIn'][idx]['idx'] = idx # for reverse lookup

			if enabled:
				GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)

				# pin is always passed as first argument, this is why we have undefined 'x' here
				cb = lambda x, name=name: self.eventIn_Callback(x,name)

				try:
					GPIO.remove_event_detect(pin)
				except (RuntimeError) as e:
					print('error in eventIn remove_event_detect, enabled: ' + str(e))

				try:
					GPIO.add_event_detect(pin, polarity, callback=cb, bouncetime=bouncetime) # ms
					#GPIO.add_event_detect(pin, polarity, callback=self.eventIn_Callback, bouncetime=200) # ms
				except (RuntimeError) as e:
					logger.warning('eventIn add_event_detect: ' + str(e))
					pass
					
				logger.info('ENABLED eventIn name:' + name + ' pin:' + str(pin) + ' polarity:' + polarityStr + ' pull_up_down:' + pull_up_downStr + ' bouncetime:' + str(bouncetime))
				#logger.info('ENABLED eventIn: ' +  str(eventIn))
			else:
				try:
					#print('pin:', pin, 'is not enabled, calling remove_event_detect(pin)')
					GPIO.remove_event_detect(pin)
					logger.info('DISABLED eventIn name:' + name + ' pin:' + str(pin))
				except (RuntimeError) as e:
					print('error in eventIn remove_event_detect, not enabled: ' + str(e))
			
		#
		# events out (e.g. led, motor, or lick port)
		for idx,eventOut in enumerate(self.config['hardware']['eventOut']):
			enabled = eventOut['enabled'] # is it enabled to receive events
			name = eventOut['name']
			pin = eventOut['pin']
			defaultValue = eventOut['defaultValue']

			# set the status in the config struct
			self.config['hardware']['eventOut'][idx]['state'] = defaultValue # so javascript can read state
			self.config['hardware']['eventOut'][idx]['idx'] = idx # for reverse lookup

			if enabled:
				GPIO.setup(pin, GPIO.OUT)
				GPIO.output(pin, defaultValue)
				logger.info('ENABLED eventOut name:' + name + ' pin:' + str(pin) + ' defaultValue:' + str(defaultValue))
			else:
				pass
				
			# assign index for reverse lookup
			if name == 'triggerOut':
				self.triggerOutIndex = idx
			if name == 'whiteLED':
				self.whiteLEDIndex = idx
			if name == 'irLED':
				self.irLEDIndex = idx

			"""
			# testing pulse-width-modulation (PWM) on piins (18, 19)
			if name == 'whiteLED':
				tmpPin = pin #19
				tmpFreq = 50 # Hz
				tmpDutyCycle = 0
				self.pwm0 = GPIO.PWM(tmpPin, tmpFreq)
				self.pwm0.start(tmpDutyCycle) # # where dc is the duty cycle (0.0 <= dc <= 100.0)
				try:
					while True:
						for dc in range(0, 101, 5):
							self.pwm0.ChangeDutyCycle(dc)
							time.sleep(0.1)
						for dc in range(100, -1, -5):
							self.pwm0.ChangeDutyCycle(dc)
							time.sleep(0.1)
				except KeyboardInterrupt:
					pass
			"""
				
	##########################################
	# Input pin callbacks
	##########################################
	#cb = lambda x, name=name: self.eventIn_Callback(x,name)
	def eventIn_Callback(self, pin, name=None):
		"""
		Can call manually with just name
		REMEMBER: DO NOT RUN VLASK SERVER IN DEBUG MODE (WE GET HIT TWICE)
		"""
		
		now = time.time()
		
		#if self.isRunning:
		if True:
			enabled = False
			dictList = self.config['hardware']['eventIn']
			if pin is None and name is not None:
				# called by user, look up event in list by ['name']
				thisItem = next(item for item in dictList if item["name"] == name)
				if thisItem is None:
					print('ERROR: did not find pin by name:', name)
					pass
				else:
					enabled = thisItem['enabled']
					pin = thisItem['pin']
			elif pin is not None:
				# we received a callback with pin specified
				# look up by pin number
				thisItem = next(item for item in dictList if item["pin"] == pin)
				if thisItem is None:
					#error
					print('ERROR: did not find pin by pin number:', pin)
				else:
					enabled = thisItem['enabled']
					name = thisItem['name']

			# value of pinIsUp will not work if receiving a fast pulse and detecting 'both'
			pinIsUp = GPIO.input(pin) == 1
			#print('=== RECEIVED eventIn_Callback', now, 'pin:', pin, 'name:', name, 'enabled:', enabled, 'pinIsUp:', pinIsUp)
			
			if enabled:
				#print('eventIn_Callback() enabled:' + str(enabled) + ' pin:' + str(pin) + ' name:' + name)
			
				if name == 'triggerIn':
					#logger.debug('\ntriggerIn_Callback pin:' + str(pin))
					if self.camera is not None:
						if self.camera.isState('armed'):
				
							# I can't fucking remember which one
							#self.startTrial(startArmVideo=False)
				
							self.camera.startArmVideo(now=now)
							#self.lastResponse = self.camera.lastResponse
						else:
							print('!!! received triggerIn when camera is NOT armed')
					else:
						print('!!! received triggerIn but camera is None')
				elif name == 'frame':
					if self.isRunning:
						#self.numFrames += 1 # can't do this, no setter
						self.newEvent('frame', self.numFrames, now=now)
						if self.camera is not None:
							self.camera.annotate(self.numFrames)
						logger.debug('eventIn_Callback() frame ' + str(self.numFrames))
					else:
						print('!!! received frame when not running')
				else:
					if self.isRunning:
						# just log the name and state
						self.newEvent(name, pinIsUp, now=now)
						if name == 'arduinoMotor':
							if self.camera is not None:
								if pinIsUp:
									self.camera.annotate('m')
								else:
									self.camera.annotate('')
						logger.debug('eventIn_Callback() pin: ' + str(pin) + ' name: ' + name + ' value: ' + str(pinIsUp))
					else:
						print('!!! received', name, ' when not running')

			else:
				logger.warning('eventIn_Callback() pin is not enabled, pin: ' + str(pin) + ' name: ' + name + ' value: ' + str(pinIsUp))
		
		#else:
		#	print('!!! Trial not running eventIn_Callback()', now, 'pin:', pin, 'name:', name, self.isRunning)
		#	pass
						
	##########################################
	# Output pins on/off
	##########################################
	def eventOut(self, name, onoff):
		""" Turn output pins on/off """
		dictList = self.config['hardware']['eventOut'] # list of event out(s)
		try:
			thisItem = next(item for item in dictList if item["name"] == name)
		except StopIteration:
			thisItem = None
		if thisItem is None:
			err = 'eventOut() got bad name: ' + name
			logger.error(err)
			self.lastResponse = err
		else:
			wasThis = self.config['hardware']['eventOut'][thisItem['idx']]['state']
			pin = thisItem['pin']
			#print('1', thisItem, wasThis, onoff)
			#if wasThis != onoff:
			#	print('eventOut() setting pin:', str(pin), 'to', str(onoff), thisItem)
			GPIO.output(pin, onoff)
			# set the state of the out pin we just set
			if wasThis != onoff:
				self.config['hardware']['eventOut'][thisItem['idx']]['state'] = onoff
				self.newEvent(name, onoff, now=time.time())
				logger.debug('eventOut ' + name + ' '+ str(onoff))

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
			logger.warning('startTrial but trial is running')
			return 0

		self.runtime['trialNum'] = self.runtime['trialNum'] + 1
		
		self.runtime['startArmVideo'] = startArmVideo
		
		self.runtime['isRunning'] = True
		
		self.runtime['startTimeSeconds'] = now
		self.runtime['startDateStr'] = time.strftime('%Y%m%d', time.localtime(now))
		self.runtime['startTimeStr'] = time.strftime('%H:%M:%S', time.localtime(now))
		
		self.runtime['currentEpoch'] = 0
		self.runtime['lastEpochSeconds'] = now
		
		self.runtime['eventTypes'] = []
		self.runtime['eventValues'] = []
		self.runtime['eventStrings'] = []
		self.runtime['eventTimes'] = [] # relative to self.runtime['startTimeSeconds']
		
		self.runtime['currentFile'] = 'n/a' # video
		self.runtime['lastStillTime'] = None
		
		self.runtime['scopeFilename'] = '' # set by self.setScopeFilename()
		
		logger.debug('startTrial startArmVideo=' + str(startArmVideo))
		
		self.newEvent('startTrial', self.runtime['trialNum'], now=now)
		
		if self.camera is not None:
			if startArmVideo:
				# *this function startTrial() is being called from within the startarmvideo loop
				pass
			else:
				self.camera.record(True, startNewTrial=False)

		#
		# triggerOut
		if self.triggerOutIndex is not None:
			triggerOutDict = self.config['hardware']['eventOut'][self.triggerOutIndex]
			enabled = triggerOutDict['enabled']
			if enabled:
				# trigger out pin will remain (! defaultValue) during entire trial
				pin = triggerOutDict['pin']
				defaultValue = triggerOutDict['defaultValue']
				thisValue = not defaultValue
				logger.info('triggerOut pin:' + str(pin) + ' value:' + str(thisValue))
				GPIO.output(pin, thisValue)
			else:
				logger.info('triggerOut not enabled')
	
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
			self.camera.annotate('')

		# tell arduino to stop
		# this is not symetric, NOT sending serial on start
		# but sending serial here in case user hits stop
		# maybe make this use other teensy pin for 'emergency stop
		self.serialInAppend('command', 'stop')

		# triggerOut
		if self.triggerOutIndex is not None:
			triggerOutDict = self.config['hardware']['eventOut'][self.triggerOutIndex]
			enabled = triggerOutDict['enabled']
			if enabled:
				pin = triggerOutDict['pin']
				defaultValue = triggerOutDict['defaultValue']
				logger.debug('stopTrial pin:' + str(pin) + ' value:' + str(defaultValue))
				GPIO.output(pin, defaultValue)
		
		#
		# report that we stopped a trial
		nowStr = time.strftime('%H:%M:%S', time.localtime(now))
		if self.runtime['startArmVideo']:
			startArmStr = 'ARMED'
		else:
			startArmStr = ''
		self.lastResponse = 'Stopped ' + startArmStr + ' trial ' + str(self.currentTrial) + ' repeat ' + str(self.currentEpoch) + ' at ' + nowStr

	def newEvent(self, type, val, str='', now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.runtime['eventTypes'].append(type)
			self.runtime['eventValues'].append(val)
			self.runtime['eventStrings'].append(str)
			self.runtime['eventTimes'].append(now) # when saving, derive (*this - self.runtime['startTimeSeconds'])
		
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
			columnHeader = 'date' + delim + 'time' + delim + 'linuxSeconds' + delim + 'secondsSinceStart' + delim + 'event' + delim + 'value' + delim + 'str' + eol
			file.write(columnHeader)
			# one line per event
			for idx, eventTime in enumerate(self.runtime['eventTimes']):
				# convert epoch seconds to date/time str 
				dateStr = time.strftime('%Y%m%d', time.localtime(eventTime))
				timeStr = time.strftime('%H:%M:%S', time.localtime(eventTime))
				# need the plus at end of each line here
				secondsSinceStart = round(eventTime - self.runtime['startTimeSeconds'],4)
				frameLine = dateStr + delim + \
							timeStr + delim + \
							str(eventTime) + delim + \
							str(secondsSinceStart) + delim + \
							self.runtime['eventTypes'][idx] + delim + \
							str(self.runtime['eventValues'][idx]) + delim + \
							self.runtime['eventStrings'][idx]
				frameLine += eol
				file.write(frameLine)

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
	def lightsThread(self):
		logger.debug('lightsThread start')
		while True:
			if self.config['lights']['auto']:
				now = datetime.now()
				#print(now.hour, self.config['lights']['sunrise'], self.config['lights']['sunset'])
				isDaytime = now.hour >= float(self.config['lights']['sunrise']) and now.hour < float(self.config['lights']['sunset'])
				if isDaytime:
					#print('isDaytime')
					self.eventOut('whiteLED', True)
					#self.config['hardware']['eventOut'][self.whiteLEDIndex]['state'] = True
					
					self.eventOut('irLED', False)
					#self.config['hardware']['eventOut'][self.irLEDIndex]['state'] = False
				else:
					#print('not isDaytime')
					self.eventOut('whiteLED', False)
					#self.config['hardware']['eventOut'][self.whiteLEDIndex]['state'] = False

					self.eventOut('irLED', True)
					#self.config['hardware']['eventOut'][self.irLEDIndex]['state'] = True

				#print(self.config['hardware']['eventOut'][0]['state'], self.config['hardware']['eventOut'][1]['state'])
				
			time.sleep(.5)
		logger.debug('lightsThread stop')

	def tempThread(self):
		"""
		Thread to run temperature/humidity in background
		Adafruit DHT sensor code is blocking
		"""
		logger.info('tempThread() start')
		lastTemperatureTime = 0
		
		#print('Adafruit_DHT.DHT11:', Adafruit_DHT.DHT11)
		dhtSensorDict_ = { 'DHT11': Adafruit_DHT.DHT11, 'DHT22': Adafruit_DHT.DHT22, 'AM2302': Adafruit_DHT.AM2302}
		sensorTypeStr = self.config['hardware']['dhtsensor']['sensorType']
		sensorType = dhtSensorDict_[sensorTypeStr]
		
		pin = self.config['hardware']['dhtsensor']['pin']
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
						#logger.debug('temperature/humidity ' + str(lastTemperature) + '/' + str(lastHumidity))
						if continuouslyLog:
							# make log file if neccessary
							script_path = os.path.dirname(os.path.abspath( __file__ ))
							logPath = os.path.join(script_path,'logs')
							if not os.path.isdir(logPath):
								os.makedirs(logPath)
							logFile = os.path.join(logPath, 'environment.log')
							if not os.path.isfile(logFile):
								headerLine = "Host,DateTime,Seconds,Temperature,Humidity,whiteLight,irLight" + '\n'
								with open(logFile, 'a') as f:
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
							with open(logFile, 'a') as f:
								f.write(lineStr)
					else:
						logger.warning('temperature/humidity error, sensorType:' + sensorTypeStr + ' ' + str(sensorType) + ' pin:' + str(pin) + ' temperatureInterval:' + str(temperatureInterval))
					# set even on fail, this way we do not immediately hit it again
					lastTemperatureTime = time.time()
				except:
					logger.error('exception reading temp/hum')
					#raise
			# 
			time.sleep(0.5)

		logger.info('tempThread() stop')
	
if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

		
