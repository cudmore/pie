# Robert Cudmore
# 20180807

import time, threading

import RPi.GPIO as GPIO
import pigpio

import logging

logger = logging.getLogger('pie')

#########################################################################
class PinThread(threading.Thread):
	# need 'isRunning'
	def __init__(self, trial):
		"""
		trial: bTrial object
		"""
		threading.Thread.__init__(self)
		self.trial = trial
		self.pigpiod = None

		"""
		A dictionary of pin numbers (index with integer)
		Value is input or output pin dictionary from config json file
		"""
		self.pinNumberDict_ = {}
		
	def gpio_InputPinCallback(self, pin):
		""" Input pin callback for GPIO """
		now = time.time()
		self.inputCallback(pin, now)
		
	def pigpio_InputCallback(self, pin, level, tick):
		""" Input pin callback for pigpio """
		now = time.time()
		tick = tick * 1000 # us to ms
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
						self.trial.newEvent('triggerIn', True, now=now)
					elif self.trial.camera.isState('armedrecording'):
						# received start trigger while running
						self.trial.camera.stopArmVideo()
						self.trial.newEvent('triggerIn', False, now=now)
					else:
						logger.warning('PinThread received triggerIn when camera is NOT armed')
				else:
					print('!!! PinThread received triggerIn but camera is None')
			elif name == 'frame':
				if self.trial.isRunning:
					now = time.time()
					self.trial.runtime['numFrames'] += 1
			
					lastFrameInterval = 0
					if self.trial.runtime['numFrames'] > 1:
						#lastFrameInterval = pigpio.tickDiff(self.trial.runtime['lastFrameTime'], tick)
						lastFrameInterval = now - self.trial.runtime['lastFrameTime']
					self.trial.runtime['lastFrameTime'] = now
			
					# log the frame
					self.trial.newEvent('frame', self.trial.numFrames, now=now)
					# watermark video
					if self.trial.camera is not None:
						self.trial.camera.annotate(self.trial.numFrames)
				else:
					#print('!!! PinThread received frame when not running')
					pass
			else:
				# just log all other events
				self.trial.newEvent(name, True, now=now)
				
	# todo: not used?
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
				pass
			else:
				GPIO.output(pin, onoff)
			# set the state of the out pin we just set
			#self.pinNumberDict_[pin]['state'] = onoff

	def configPin(self, inout, configDict):

		# dictionaries to map config json to GPIO and pigpio packages
		gpioPolarityDict = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
		gpioPullUpDownDict = { 'up': GPIO.PUD_UP, 'down': GPIO.PUD_DOWN}
		
		pigPolarityDict = { 'rising': pigpio.RISING_EDGE, 'falling': pigpio.FALLING_EDGE, 'both': pigpio.EITHER_EDGE}
		pigPullUpDownDict = { 'up': pigpio.PUD_UP, 'down': pigpio.PUD_DOWN}
		
		pin = configDict['pin']
		name = configDict['name']
		enabled = configDict['enabled']
		
		self.pinNumberDict_[pin] = configDict
		
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
					GPIO.remove_event_detect(pin)
			except (RuntimeError) as e:
				print('error in eventIn remove_event_detect, enabled: ' + str(e))

			if enabled:
				if self.pigpiod:
					self.pigpiod.set_mode(pin, pigpio.INPUT)
					self.pigpiod.set_pull_up_down(pin, pullUpDown) # (pigpio.PUD_OFF, pigpio.PUD_UP, pigpio.PUD_DOWN)
				else:
					GPIO.setup(pin, GPIO.IN, pull_up_down=pullUpDown)

				try:
					if self.pigpiod:
						self.pigpiod.callback(pin, polarity, self.pigpio_InputCallback)
					else:
						GPIO.add_event_detect(pin, polarity, callback=self.gpio_InputPinCallback, bouncetime=bouncetime)
				except (RuntimeError) as e:
					logger.warning('eventIn add_event_detect: ' + str(e))
					pass
					
				logger.info('ENABLED eventIn name:' + name + ' pin:' + str(pin) + ' polarity:' + str(polarity) + ' pull_up_down:' + str(pullUpDown) + ' bouncetime:' + str(bouncetime))

		elif inout == 'output':
			defaultValue = configDict['defaultValue']

			# set the status in the config struct
			#self.config['hardware']['eventOut'][idx]['state'] = defaultValue # so javascript can read state
			#self.config['hardware']['eventOut'][idx]['idx'] = idx # for reverse lookup

			if enabled:
				if self.pigpiod:
					# todo: fix this
					pass
				else:
					GPIO.setup(pin, GPIO.OUT)
					GPIO.output(pin, defaultValue)
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
			
	def init(self, config):

		self.pigpiod = pigpio.pi()
		if not self.pigpiod.connected:
			self.pigpiod = None

		if self.pigpiod:
			logger.info('Initialized pigpio')
			pass
		else:
			logger.info('Initialized GPIO')
			GPIO.setmode(GPIO.BCM)
			GPIO.setwarnings(True)	
	
		'''
		#
		# trigger in
		pin = 24
		pull_up_down = GPIO.PUD_DOWN
		polarity = GPIO.RISING
		bouncetime = 20
	
		if self.pigpiod:
			self.pigpiod.set_mode(pin, pigpio.INPUT)
			self.pigpiod.set_pull_up_down(pin, pigpio.PUD_DOWN) # (pigpio.PUD_OFF, pigpio.PUD_UP, pigpio.PUD_DOWN)
			self.pigpiod.callback(pin, pigpio.RISING_EDGE, self.triggerIn_Callback)
			mode = self.pigpiod.get_mode(pin) # 0:input, 1:output
			print('pigpio triggerIn pin', pin, 'mode', mode)
		else:
			GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
			GPIO.add_event_detect(pin, polarity, callback=self.triggerIn_Callback, bouncetime=bouncetime)
		'''
		
		'''
		#
		#frame
		pin = 23
		pull_up_down = GPIO.PUD_DOWN
		polarity = GPIO.RISING
		bouncetime = 10
	
		if self.pigpiod:
			self.pigpiod.set_mode(pin, pigpio.INPUT)
			self.pigpiod.set_pull_up_down(pin, pigpio.PUD_DOWN) # (pigpio.PUD_OFF, pigpio.PUD_UP, pigpio.PUD_DOWN)
			self.pigpiod.callback(pin, pigpio.RISING_EDGE, self.frameIn_Callback)
			mode = self.pigpiod.get_mode(pin) # 0:input, 1:output
			print('pigpio frameIn pin', pin, 'mode', mode)
		else:
			GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
			GPIO.add_event_detect(pin, polarity, callback=self.frameIn_Callback, bouncetime=bouncetime)
		'''
		
		'''
		self.triggerOutIndex = None # assigned below when we find 'triggerOut'
		self.whiteLEDIndex = None
		self.irLEDIndex = None
		'''
		
		self.pinNumberDict_ = {} # assigned in self.configPin

		# input (e.g. triggerIn, frame)
		for idx,eventIn in enumerate(config['hardware']['eventIn']):
			self.configPin('input', eventIn)
			#self.config['hardware']['eventIn'][idx]['idx'] = idx # for reverse lookup

		# output (e.g. led, motor, or lick port)
		for idx,eventOut in enumerate(config['hardware']['eventOut']):
			self.configPin('output', eventOut)
			# set the status in the config struct
			#self.config['hardware']['eventOut'][idx]['state'] = defaultValue # so javascript can read state
			#self.config['hardware']['eventOut'][idx]['idx'] = idx # for reverse lookup
			
	def run(self):

		#self.init()
		
		while True:
			#time.sleep(0.01)
			time.sleep(1)
			
