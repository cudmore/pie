"""
Author: Robert Cudmore
Date: 20180807

Purpose: A thread class to control GPIO pins

Details: Interact with bTrial on triggerIn and frame

ToDo: For this to actually be a thread, need to implement in/out queue

"""

import time, threading

import RPi.GPIO as GPIO
import pigpio

import logging

logger = logging.getLogger('pie')

#########################################################################
#class PinThread(threading.Thread):
class PinThread(threading.Thread):
	# need 'isRunning'
	def __init__(self, trial):
		"""
		trial: bTrial object
		"""
		#threading.Thread.__init__(self)
		self.trial = trial
		self.pigpiod = None

		"""
		A dictionary of pin numbers (index with integer)
		Value is input or output pin dictionary from config json file
		"""
		self.pinNumberDict_ = {}
		
		# not working
		# 3, 8, 24 (sometimes 25)
		# working
		# 4, 7, 25
		if 0:
			GPIO.setmode(GPIO.BCM)
			GPIO.setwarnings(True)	
			tmpPin = 25
			GPIO.setup(tmpPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.add_event_detect(tmpPin, GPIO.RISING, callback=self.gpio_InputPinCallback, bouncetime=20)
		
	#########################################################################
	# Initialize from config json
	#########################################################################
	def init(self, config, initFirstTime=False):

		print('=== bPins.init() config')
		if initFirstTime:
			#self.pigpiod = pigpio.pi()
			if self.pigpiod is None or not self.pigpiod.connected:
				self.pigpiod = None
	
			if self.pigpiod:
				logger.info('Initialized pigpio')
				pass
			else:
				logger.info('Initialized GPIO with GPIO.setmode(GPIO.BCM)')
				#GPIO.cleanup() # can't cleanup before we setup
				GPIO.setmode(GPIO.BCM)
				GPIO.setwarnings(True)	
	
		self.pinNumberDict_ = {} # assigned in self.configPin()

		#
		# input (e.g. triggerIn, frame)
		for idx,eventIn in enumerate(config['hardware']['eventIn']):
			self.configPin('input', eventIn)
			#self.config['hardware']['eventIn'][idx]['idx'] = idx # for reverse lookup

		#
		# output (e.g. led, motor, or lick port)
		for idx,eventOut in enumerate(config['hardware']['eventOut']):
			self.configPin('output', eventOut)
			# set the status in the config struct
			#self.config['hardware']['eventOut'][idx]['state'] = defaultValue # so javascript can read state
			#self.config['hardware']['eventOut'][idx]['idx'] = idx # for reverse lookup
	
	def exiting(self):
		GPIO.cleanup()
		
	#########################################################################
	# Input pin callbacks
	#########################################################################
	# todo: merge gpio_InputPinCallback and pigpio_InputCallback by using level=None, tick=None
	#	then check for level/tick and we are in pigpio
	def gpio_InputPinCallback(self, pin):
		""" Input pin callback for GPIO """
		print('=== bPins.gpio_InputPinCallback() pin:', pin)
		now = time.time()
		self.inputCallback(pin, now)
		
	def pigpio_InputCallback(self, pin, level, tick):
		""" Input pin callback for pigpio """
		now = time.time()
		tick = tick / 1000 # us to ms
		self.inputCallback(pin, now, tick=tick)
	
	def inputCallback(self, pin, now, tick=None):
		# look up pin name from number
		if pin not in self.pinNumberDict_:
			print('error: PinThread.inputCallback received bad pin', pin)
		else:
			pinDict = self.pinNumberDict_[pin]
			name = pinDict['name']
			if name == 'triggerIn':
				if self.trial.camera is not None:
					if self.trial.camera.isState('armed'):
						# received start trigger while armed
						self.trial.camera.startArmVideo(now=now)
						self.trial.newEvent('triggerIn', True, now=now, tick=tick)
					elif self.trial.camera.isState('armedrecording'):
						# received start trigger while running
						self.trial.camera.stopArmVideo()
						self.trial.newEvent('triggerIn', False, now=now, tick=tick)
					else:
						logger.warning('PinThread received triggerIn when camera is NOT armed')
				else:
					print('!!! PinThread received triggerIn but camera is None')
			elif name == 'frame':
				if self.trial.isRunning:
					self.trial.runtime['numFrames'] += 1
			
					'''
					lastFrameInterval = 0
					if self.trial.runtime['numFrames'] > 1:
						lastFrameInterval = now - self.trial.runtime['lastFrameTime']
					self.trial.runtime['lastFrameTime'] = now
					'''
					# log the frame, if using pigpio(d) we will also get a tick
					# pigpio tick is orders of magnitude more precise that time.time()
					# I think this is because background processes in a while loop call time.sleep()
					# which throw off system wide time.time()
					
					videoTimestamp = 'NaN'
					if self.trial.camera is not None:
						# annotate/watermark video with frame number
						self.trial.camera.annotate(newAnnotation = str(self.trial.numFrames))

						# try and get frame.timestamp from camera video recording
						frame = self.trial.camera.camera.frame
						if frame is None:
							pass
						else:
							if frame.timestamp is None:
								pass
							else:
								#self.trial.newEvent('frameTimeStamp', frame.timestamp, str=str(self.trial.numFrames), now=now)
								videoTimestamp = str(frame.timestamp)

					# log the frame
					self.trial.newEvent('frame', self.trial.numFrames, now=now, str=videoTimestamp, tick=tick)

				else:
					#print('!!! PinThread received frame when not running')
					pass
			else:
				# just log all other events
				
				videoTimestamp = 'NaN'
				if self.trial.camera is not None:
					# try and get frame.timestamp from camera video recording
					frame = self.trial.camera.camera.frame
					if frame is None:
						pass
					else:
						if frame.timestamp is None:
							pass
						else:
							#self.trial.newEvent('frameTimeStamp', frame.timestamp, str=str(self.trial.numFrames), now=now)
							videoTimestamp = str(frame.timestamp)
				
				# log the event
				self.trial.newEvent(name, True, now=now, str=videoTimestamp, tick=tick)
				
	##########################################
	# Output pins on/off
	##########################################
	def eventOut(self, name, onoff):
		""" Turn output pins on/off """
		now = time.time()
		pin = self.pinFromName(name)
		if pin is None:
			err = 'eventOut() got bad output pin name: ' + name
			logger.error(err)
			self.trial.lastResponse = err
		else:

			if self.pigpiod:
				# todo: fix this
				self.pigpiod.write(pin, onoff)
			else:
				try:
					logger.info(name + ' ' + str(onoff))
					GPIO.output(pin, onoff)
				except (RuntimeError) as e:
					# we will always get here with start/stop trial when out trigger is off
					logger.error(str(e) + ' pin:' + str(pin))
					#raise
					
			# set the state of the out pin we just set
			#self.pinNumberDict_[pin]['state'] = onoff

	#########################################################################
	# Configure a pin as 'input' or 'output' using config json
	#########################################################################
	def configPin(self, inout, configDict):

		#print('\nbPins.configPin() inout:', inout, 'configDict:', configDict)
		
		# dictionaries to map config json to GPIO and pigpio packages
		gpioPolarityDict = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
		gpioPullUpDownDict = { 'up': GPIO.PUD_UP, 'down': GPIO.PUD_DOWN}
		
		pigPolarityDict = { 'rising': pigpio.RISING_EDGE, 'falling': pigpio.FALLING_EDGE, 'both': pigpio.EITHER_EDGE}
		pigPullUpDownDict = { 'up': pigpio.PUD_UP, 'down': pigpio.PUD_DOWN}
		
		pin = configDict['pin']
		name = configDict['name']
		enabled = configDict['enabled']
		
		self.pinNumberDict_[pin] = configDict
		
		print('=== configPin() name:', name, 'pin:', pin, 'enabled:', enabled, 'inout:', inout)
		
		# input
		if inout == 'input':
			polarity = configDict['polarity']
			pullUpDown = configDict['pull_up_down']
			bouncetime = configDict['bouncetime']
			
			if self.pigpiod:
				polarity = pigPolarityDict[polarity]
			else:
				polarity = gpioPolarityDict[polarity]

			if self.pigpiod:
				pullUpDown = pigPullUpDownDict[pullUpDown]
			else:
				pullUpDown = gpioPullUpDownDict[pullUpDown]

			# always try to remove existing input pin callback
			try:
				if self.pigpiod:
					# to cancel, we need pointer to return of pi.callback()
					#self.pigpiod.callback(pin, pigpio.RISING_EDGE, self.frameIn_Callback)
					pass
				else:
					#print('GPIO.remove_event_detect() pin:', pin)
					GPIO.remove_event_detect(pin)
					logger.info('GPIO.remove_event_detect() name:'+ name + ' pin:' + str(pin))
			except (RuntimeError) as e:
				logger.error('error in eventIn remove_event_detect, enabled: ' + str(e) + ', name:' + name + ' pin:' + str(pin))
			except (RuntimeWarning) as e:
				print('xxx yyy')
			except:
				print('xxx bPins.configPin() unexpected exception')
				
			if enabled:
				if self.pigpiod:
					self.pigpiod.set_mode(pin, pigpio.INPUT)
					self.pigpiod.set_pull_up_down(pin, pullUpDown) # (pigpio.PUD_OFF, pigpio.PUD_UP, pigpio.PUD_DOWN)
				else:
					#print('GPIO.setup() pin:', pin, GPIO.IN, pullUpDown)
					#print('1')
					#print('calling GPIO.setup() GPIO.IN pin:', pin)
					GPIO.setup(pin, GPIO.IN, pull_up_down=pullUpDown)
					logger.info('GPIO.setup() GPIO.IN name:'+ name + ' pin:' + str(pin) + ' pull_up_down:' + str(pullUpDown))
					#print('2')
				try:
					if self.pigpiod:
						print('=== self.pigpiod.callback')
						self.pigpiod.callback(pin, polarity, self.pigpio_InputCallback)
					else:
						GPIO.add_event_detect(pin, polarity, callback=self.gpio_InputPinCallback, bouncetime=bouncetime)
						logger.info('GPIO.add_event_detect() name:'+ name + ' pin:' + str(pin) + ' polarity:' + str(polarity) + ' bouncetime:' + str(bouncetime))
				except (RuntimeError) as e:
					logger.error('eventIn add_event_detect: ' + str(e) + ', name:' + name + ' pin:' + str(pin) + ' polarity:' + str(polarity) + ' bouncetime:' + str(bouncetime))
					pass
				except:
					print('xxx bPins.configPin() unexpected exception --- add_event_detect()')
					
				#logger.info('ENABLED eventIn name:' + name + ' pin:' + str(pin) + ' polarity:' + str(polarity) + ' pull_up_down:' + str(pullUpDown) + ' bouncetime:' + str(bouncetime))

		elif inout == 'output':
			defaultValue = configDict['defaultValue']

			# set the status in the config struct
			#self.config['hardware']['eventOut'][idx]['state'] = defaultValue # so javascript can read state
			#self.config['hardware']['eventOut'][idx]['idx'] = idx # for reverse lookup

			if enabled:
				if self.pigpiod:
					# todo: fix this
					self.pigpiod.set_mode(pin, pigpio.OUTPUT)
					self.pigpiod.write(pin, defaultValue)
				else:
					try:
						print('3')
						print('calling GPIO.setup() GPIO.OUT pin:', pin)
						GPIO.setup(pin, GPIO.OUT)
						print('4')
						self.eventOut(name, defaultValue)
						#GPIO.output(pin, defaultValue)
						print('5')
					except (RuntimeError) as e:
						print('xxx runtime error e:', str(e))
					except:
						print('yyy runtime error e:', str(e))
				logger.info('ENABLED eventOut name:' + name + ' pin:' + str(pin) + ' defaultValue:' + str(defaultValue))
			else:
				pass
			
			# assign index for reverse lookup
			'''
			if name == 'triggerOut':
				self.triggerOutIndex = idx
			if name == 'whiteLED':
				self.whiteLEDIndex = idx
			if name == 'irLED':
				self.irLEDIndex = idx
			'''
			
			"""
			# testing pulse-width-modulation (PWM) on pins (18, 19)
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
			
	#########################################################################
	# utility
	#########################################################################
	def pinFromName(self, name):
		""" Given a pin name, return its pin number """
		ret = None
		for i, (k,v) in enumerate(self.pinNumberDict_.items()):
			#print('pinDict:', v)
			if v['name'] == name:
				ret = k
				break
		if ret is None:
			print('error: pinFromName() did not find pin named "', name, '"')
		return ret
			
	#########################################################################
	# run
	#########################################################################
	def run(self):
		while True:
			#time.sleep(0.01)
			time.sleep(1)
			
