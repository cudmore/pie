"""
Author: Robert Cudmore
Date: 20170817

Purpose: A class that is a wrapper around a bTrial object.

Details: Derives treadmillTrial from bTrial to provide bidirectional communication
with a web server (usually Flask) using socketio. This was needed as REST web requests,
at least in Flask, were disrupting Raspberry GPIO timing. To fix this, the web javascript
timer that requests REST status is turned off during a trial.
"""

import os, sys, time
from collections import OrderedDict
from datetime import timedelta
from pprint import pprint

import logging

#import RPi.GPIO as GPIO

import bUtil
import bTrial
import bCamera

logger = logging.getLogger('pie')

#########################################################################
class treadmillTrial(bTrial.bTrial):
	def __init__(self, treadmill):
		bTrial.bTrial.__init__(self)
		self.treadmill = treadmill
		
	def startTrial(self, startArmVideo=False, now=None):
		bTrial.bTrial.startTrial(self, startArmVideo, now)
		
		#print('\nsend startTrial socketio')
		myDict = {'data': 'Server generated event', 'status': self.treadmill.getStatus()}		
		self.treadmill.socketio.emit('socket_startTrial',
				myDict,
				namespace='')
						
	def stopTrial(self):
		bTrial.bTrial.stopTrial(self)
		
		#print('\nsend stopTrial socketio')
		myDict = {'data': 'Server generated event', 'status': self.treadmill.getStatus()}
		self.treadmill.socketio.emit('socket_stopTrial',
				myDict,
				namespace='')

#########################################################################
class treadmill():

	#def __init__(self):		
	def __init__(self, socketio):		
		self.systemInfo = bUtil.getSystemInfo()
		
		self.socketio = socketio
		
		self.trial = treadmillTrial(self)
		#self.trial = bTrial.bTrial()

						
	#########################################################################
	# status
	#########################################################################
	def getStatus(self):
		status = OrderedDict()
		status['trial'] = self.trial.getStatus()
		
		#print("status['trial']['runtime']['cameraState']=", status['trial']['runtime']['cameraState'])
		
		return status
		
	#########################################################################
	# Start/Stop
	#########################################################################
	def startRecord(self):
		self.trial.startTrial() # starts the video
		
	def stopRecord(self):
		self.trial.stopTrial() # stops the video

	def startStream(self):
		if self.trial.camera:
			self.trial.camera.stream(True)
		
	def stopStream(self):
		if self.trial.camera:
			self.trial.camera.stream(False)

	def startArm(self):
		# turn off repeat infinity, set num repeats = 1
		self.trial.config['trial']['repeatInfinity'] = False
		self.trial.config['trial']['numberOfRepeats'] = 1
		
		if self.trial.camera:
			self.trial.camera.arm(True)
		
		# arm teensy
		self.serialUpdateArm(True)
		
	def stopArm(self):
		if self.trial.camera:
			self.trial.camera.arm(False)

		# un-arm teensy
		self.serialUpdateArm(False)
		
	def startArmVideo(self):
		''' MASTER '''
		logger.debug('startArmVideo')
		#self.trial.startTrial(startArmVideo=True) # starts the video
		if self.trial.camera is not None:
			self.trial.camera.startArmVideo()
					
	def stopArmVideo(self):
		logger.debug('stopArmVideo')
		''' MASTER '''
		#self.trial.stopTrial() # stops the video
		if self.trial.camera is not None:
			self.trial.camera.stopArmVideo()

		
	#########################################################################
	# update config
	#########################################################################
	def saveConfig(self):
		self.trial.saveConfig()
		
	def updateConfig(self, configDict):
		self.trial.updateConfig(configDict)
		
	def updatePins(self, configDict):
		self.trial.updatePins(configDict)
		
	def updateAnimal(self, configDict):
		self.trial.updateAnimal(configDict)
		
	def updateLED(self, configDict):
		self.trial.updateLED(configDict)
	
	def updateFan(self, configDict):
		self.trial.updateFan(configDict)
	
	def loadConfig(self, loadThis):
		"""
		Load a config file from disk
		"""
		# lhs config is not used
		if loadThis == 'factorydefaults':
			config = self.trial.loadConfigFile(thisFile='config_factory_defaults.json')
			#if config is not None:
			#	self.trial.config = config
		elif loadThis == 'default':
			config = self.trial.loadConfigFile(thisFile='config_default.json')
			#if config is not None:
			#	self.trial.config = config
		elif loadThis == 'homecage':
			config = self.trial.loadConfigFile(thisFile='config_homecage.json')
			#if config is not None:
			#	self.trial.config = config
		elif loadThis == 'scope':
			config = self.trial.loadConfigFile(thisFile='config_scope.json')
			#if config is not None:
			#	self.trial.config = config
		elif loadThis == 'treadmill':
			config = self.trial.loadConfigFile(thisFile='config_treadmill.json')
			#if config is not None:
			#	self.trial.config = config
		elif loadThis == 'userconfig':
			config = self.trial.loadConfigFile(thisFile='config_user.json')
				
	#########################################################################
	# Serial communication with teensy/arduino
	#########################################################################
	def serialUpdateMotor(self, motorDict):
		""" todo: put this in bTrial """

		#print('serialUpdateMotor()')
		#print('motorDict:', motorDict)
		
		for key, value in motorDict.items():
			#convert python based variable to arduino
			if key == 'motorNumEpochs':
				key = 'numEpoch'
			if key == 'motorRepeatDuration':
				key = 'epochDur'
			if key == 'motorSpeed':
				if motorDict['motorDirection'] == 'Forward':
					value *= +1
				elif motorDict['motorDirection'] == 'Reverse':
					value *= -1
			"""
			if key == 'motorRepeatDuration':
				key = 'epochDur'
			if key == 'motorRepeatDuration':
				key = 'epochDur'
			"""

			serialCommand = 'settrial,' + key + ',' + str(value)
			self.trial.serialInAppend('command', serialCommand)
		
		"""
		key = 'preDur'
		value = 0
		serialCommand = 'settrial,' + key + ',' + str(value)
		self.trial.serialInAppend('command', serialCommand)
		key = 'postDur'
		value = 0
		serialCommand = 'settrial,' + key + ',' + str(value)
		self.trial.serialInAppend('command', serialCommand)
		
		#self.inSerialQueue.put('p')
		"""
		
		newFileDuration = motorDict['motorNumEpochs'] * motorDict['motorRepeatDuration']		
		# motorRepeatDuration (ms) -->> fileDuration (sec)
		newFileDuration /= 1000
		
		self.trial.config['trial']['repeatInfinity'] = False
		self.trial.config['trial']['numberOfRepeats'] = 1
		self.trial.config['trial']['repeatDuration'] = newFileDuration

		self.trial.config['motor'] = motorDict
		# convert ['updateMotor'] to (-1, +1)	

		self.trial.lastResponse = 'Finished updating motor'
		
	#########################################################################
	def serialUpdateArm(self, onoff):
		key = 'arm'
		value = onoff
		serialCommand = 'settrial,' + key + ',' + str(value)
		self.trial.serialInAppend('command', serialCommand)
		
#########################################################################
if __name__ == '__main__':
	# debugging
	t = treadmill()
	
	# debug serieal
	r = t.sendtoserial('p')
	print('params:', r)
	r = t.sendtoserial('v')
	print('version:', r)
	r = t.sendtoserial('d')
	print('trial:', r)
	
	'''
	These are the parameter names used by version 20160918 of teensy code
	
	[b'trialNumber=0',
		b'trialDur=1700', # DON'T set this one, it is calculated
		b'motorNumEpochs=3',
		b'epochDur=500',
		b'preDur=100',
		b'postDur=100',
		b'useMotor=0',
		b'motorDel=100',
		b'motorDur=300',
		b'motorSpeed=0',
		b'motorMaxSpeed=1000',
		b'versionStr=20160918']
	'''
	trialDict = {'epochDur': 1000, 'motorNumEpochs': 1, 'badkey': 'badvalue'}
	t.serial_settrial2(trialDict)
	
	