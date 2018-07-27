# Robert H Cudmore
# 20180525

import os, io, time, math, json
from datetime import datetime
from collections import OrderedDict
import threading, subprocess, queue

import picamera

import bTrial

import logging
logger = logging.getLogger('flask.app')

class bCamera:
	def __init__(self, trial=None, cameraErrorQueue=None):
	
		self.cameraErrorQueue = cameraErrorQueue
		
		self.camera = None

		self.state = 'idle'
		
		if trial is None:
			self.trial = bTrial()
		else:
			self.trial = trial # a bTrial class
		
		self.currentFile = '' # actually part of trial
		self.secondsElapsedStr = ''
		
		# still image during recording
		self.lastStillTime = 0
		self.stillPath = os.path.join(os.path.dirname(__file__), 'static/still.jpg')
		
		#
		# a background thread to convert .h264 to .mp4
		self.convertFileQueue = queue.Queue()
		self.convertErrorQueue = queue.Queue() # queue is infinite length
		thread = threading.Thread(target=self.convertVideoThread, args=(self.convertFileQueue,self.convertErrorQueue,))
		thread.daemon = True							# Daemonize thread
		thread.start()									# Start the execution
		
	def isState(self, thisState):
		return self.state == thisState
	
	#########################################################################
	# properties
	#########################################################################
	@property
	def lastResponse(self):
		self.trial.lastResponse
	
	@lastResponse.setter
	def lastResponse(self, str):
		self.trial.lastResponse = str
			
	def initCamera_(self, cameraErrorQueue=None):
		"""
		Internal function that retuns the current configuration of the camera.
		Used by record and are video thread
		"""
		ret = OrderedDict()
		
		try:
			self.camera = picamera.PiCamera()
		except (picamera.exc.PiCameraMMALError) as e:
			logger.error('picamera PiCameraMMALError: ' + str(e))
			if cameraErrorQueue is not None:
				cameraErrorQueue.put(str(e))
			self.lastResponse = str(e)
			self.state = 'idle'
			raise
		except (picamera.exc.PiCameraError) as e:
			logger.error('picamera PiCameraError: ' + str(e))
			self.lastResponse = str(e)
			self.state = 'idle'
			raise

		ret['led'] = self.trial.getConfig('video', 'led')
		#print("ret['led']:", ret['led'])
		self.camera.led = ret['led']

		resolution = self.trial.getConfig('video', 'resolution')
		width = int(resolution.split(',')[0])
		height = int(resolution.split(',')[1])
		self.camera.resolution = (width, height)
		
		ret['fps'] = self.trial.getConfig('video', 'fps')
		self.camera.framerate = ret['fps']
		
		# package trial config into a struct
		ret['repeatDuration'] = self.trial.getConfig('trial', 'repeatDuration') # different key names
		ret['repeatInfinity'] = self.trial.getConfig('trial', 'repeatInfinity')
		ret['numberOfRepeats'] = self.trial.getConfig('trial', 'numberOfRepeats')
		ret['savePath'] = self.trial.getConfig('trial', 'savePath')
		
		ret['captureStill'] = self.trial.getConfig('video', 'captureStill')
		ret['stillInterval'] = self.trial.getConfig('video', 'stillInterval')
		ret['converttomp4'] = self.trial.getConfig('video', 'converttomp4')
		ret['bufferSeconds'] = self.trial.getConfig('video', 'bufferSeconds')

		return ret
		
	#########################################################################
	# Record a number of video files
	#########################################################################
	def record(self, onoff, startNewTrial=True):
		okGo = self.state in ['idle'] if onoff else self.state in ['recording']
		logger.debug('record onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if okGo:
			self.state = 'recording' if onoff else 'idle'
			if onoff:
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=(startNewTrial,self.cameraErrorQueue,))
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				#self.trial.stopTrial()
				# thread will fall out of loop on self.state=='idle'
				pass
			return onoff
		else:
			return False
				
	def recordVideoThread(self, startNewTrial=True, cameraErrorQueue=None):
		"""
		Record individual video files in background thread
		"""
		
		logging.info('recordVideoThread start')
		
		#
		# grab configuration from trial
		thisCamera = self.initCamera_(cameraErrorQueue=cameraErrorQueue)
		repeatDuration = thisCamera['repeatDuration']
		repeatInfinity = thisCamera['repeatInfinity']
		numberOfRepeats = thisCamera['numberOfRepeats']
		fps = thisCamera['fps']
		captureStill = thisCamera['captureStill']
		stillInterval = thisCamera['stillInterval']
		converttomp4 = thisCamera['converttomp4']
		savePath = thisCamera['savePath']
		# tweek numberOfRepeats
		numberOfRepeats = float('Inf') if repeatInfinity else float(numberOfRepeats)
		
		#
		self.camera.start_preview()

		now = time.time()

		if startNewTrial:
			self.trial.startTrial()
		
		startDateStr = time.strftime('%Y%m%d', time.localtime(now)) 
		saveVideoPath = os.path.join(savePath, startDateStr)
		if not os.path.isdir(saveVideoPath):
			os.makedirs(saveVideoPath)

		self.lastStillTime = 0 # seconds
		currentRepeat = 1
		while self.isState('recording') and (currentRepeat <= numberOfRepeats):
			
			self.trial.newEpoch()
			
			#the file we are about to record/save
			# time stamp is based on trial.newEpoch()
			self.currentFile = self.trial.getFilename(withRepeat=True) + '.h264'
			self.secondsElapsedStr = '0'
			videoFilePath = os.path.join(saveVideoPath, self.currentFile)

			logger.debug('Start video file:' + self.currentFile + ' dur:' + str(repeatDuration) + ' fps:' + str(fps))

			self.trial.newEvent('recordVideo', currentRepeat, str=videoFilePath)	

			try:
				self.camera.start_recording(videoFilePath)
			except (IOError) as e:
				logger.error('start recording:' + str(e))
				self.camera.close()
				self.lastResponse = str(e)
				self.state = 'idle'
				raise

			startRecordSeconds = time.time()
				
			# record until duration or we are no longer 'recording'
			while self.isState('recording') and (time.time() <= (startRecordSeconds + float(repeatDuration))):
				self.camera.wait_recording()
				if captureStill and time.time() > (self.lastStillTime + float(stillInterval)):
					self.camera.capture(self.stillPath, use_video_port=True)
					self.lastStillTime = time.time()
					'''
					self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
					'''
				self.secondsElapsedStr = str(round(time.time() - startRecordSeconds, 1))
					
			self.camera.stop_recording()

			tmpFolderpath, tmpFilename = os.path.split(videoFilePath)
			logger.debug('Stop video file: ' + tmpFilename)
			
			self.trial.newEvent('stopVideo', currentRepeat, str=videoFilePath) # paired with startVideo			
			
			currentRepeat += 1

			if converttomp4:
				self.convertVideo(videoFilePath, fps)
			
		self.state = 'idle'
		self.currentFile = ''
		self.secondsElapsedStr = 'n/a'
		
		self.trial.stopTrial()
		self.camera.close()
		
		logging.debug('recordVideoThread end')

	#########################################################################
	# Stream to browser
	#########################################################################
	def stream(self,onoff):
		''' start and stop video stream '''
		okGo = self.state in ['idle'] if onoff else self.state in ['streaming']
		logger.debug('stream onoff:' + str(onoff) + ' okGo:' + str(okGo))

		if okGo:
			self.state = 'streaming' if onoff else 'idle'
			if onoff:
				streamResolution = self.trial.getConfig('video', 'streamResolution')
				streamWidth = streamResolution.split(',')[0] #str is ok here
				streamHeight = streamResolution.split(',')[1]

				script_path = os.path.dirname(os.path.abspath( __file__ ))
				cmd = [script_path + "/bin/stream.sh", "start", str(streamWidth), str(streamHeight)]

				logger.info(cmd)
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is on'
				except subprocess.CalledProcessError as e:
					error = e.output.decode('utf-8')
					logger.error('stream on exception: ' + error)
					self.lastResponse = error
					#self.stream(False)
					self.state = 'idle'
					raise
			else:
				script_path = os.path.dirname(os.path.abspath( __file__ ))
				cmd = [script_path + "/bin/stream.sh", "stop"]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is off'
				except subprocess.CalledProcessError as e:
					error = e.output.decode('utf-8')
					logger.error('stream off exception: ' + error)
					self.lastResponse = error
					raise
			
	#########################################################################
	# Arm video (wait for trigger) by creating a video loop
	#########################################################################
	def arm(self, onoff):
		''' start and stop arm '''
		okGo = self.state in ['idle'] if onoff else self.state in ['armed']
		logger.debug('arm onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if okGo:
			self.state = 'armed' if onoff else 'idle'
			if onoff:
				# spawn background task with video loop
				#try:
				if 1:

					# save into date folder
					savePath = self.trial.getConfig('trial', 'savePath')
					startTime = datetime.now()
					startTimeStr = startTime.strftime('%Y%m%d')
					saveVideoPath = os.path.join(savePath, startTimeStr)
					if not os.path.isdir(saveVideoPath):
						os.makedirs(saveVideoPath)

					thread = threading.Thread(target=self.armVideoThread, args=([saveVideoPath, self.cameraErrorQueue]))
					thread.daemon = True							# Daemonize thread
					thread.start()									# Start the execution

					self.lastResponse = 'Armed and waiting for trigger'
			else:
				if self.camera:
					# stop background task with video loop
					try:
						self.camera.stop_recording()	
						self.camera.close()
					except picamera.exc.PiCameraNotRecording:
						logger.error('PiCameraNotRecording')
					self.lastResponse = 'Arming is off'
						
	def startArmVideo(self, now=None):
		if now is None:
			now = time.time()
		if self.isState('armed'):
			#logger.debug('startArmVideo()')
			self.state = 'armedrecording' # will trigger armVideoThread()
			
	def stopArmVideo(self):
		if self.isState('armedrecording'):
			now=time.time()
			logger.debug('stopArmVideo()')
			self.state = 'armed' # will force armVideoThread() out of while loop

	def armVideoThread(self, saveVideoPath, cameraErrorQueue):
		"""
		Arm the camera by starting a circular stream
		
		Start recording from circular stream in response to trigger.
		This will record until (i) repeatDuration or (ii) stop trigger
		"""
		if 1: #self.camera:
			self.lastStillTime = 0
			
			#
			thisCamera = self.initCamera_(cameraErrorQueue=cameraErrorQueue)
			repeatDuration = thisCamera['repeatDuration']
			repeatInfinity = thisCamera['repeatInfinity']
			numberOfRepeats = thisCamera['numberOfRepeats']
			fps = thisCamera['fps']
			captureStill = thisCamera['captureStill']
			stillInterval = thisCamera['stillInterval']
			converttomp4 = thisCamera['converttomp4']
			savePath = thisCamera['savePath']
			bufferSeconds = thisCamera['bufferSeconds'] # for video loop
			# tweek numberOfRepeats
			#numberOfRepeats = float('Inf') if repeatInfinity else float(numberOfRepeats)
			
			self.camera.start_preview()

			logger.debug('Starting circular stream, bufferSeconds:' + str(bufferSeconds))
			circulario = picamera.PiCameraCircularIO(self.camera, seconds=bufferSeconds)
			self.camera.start_recording(circulario, format='h264')

			while self.isState('armed') or self.isState('armedrecording'):
				self.camera.wait_recording()
				#if self.isState('armedrecording') and (currentRepeat <= numberOfRepeats):
				if self.isState('armedrecording'):
					currentRepeat = 1 #important: for now we will just do one repeat
					
					# when we receive trigger, we need to start a startArmVideo trial
					self.trial.startTrial(startArmVideo=True)

					self.trial.newEpoch()

					# get base file name from trial
					filePrefix = self.trial.getFilename(withRepeat=True) # uses ['lastEpochSeconds']
					beforefilename = filePrefix + '_before.h264'
					afterfilename = filePrefix + '_after.h264'					
					beforefilepath = os.path.join(saveVideoPath, beforefilename) # saveVideoPath is param to *this function
					afterfilepath = os.path.join(saveVideoPath, afterfilename)

					self.trial.newEvent('beforefilepath', currentRepeat, str=beforefilepath)
					self.trial.newEvent('afterfilepath', currentRepeat, str=afterfilepath)

					# we were in a video loop, save the pre-trigger video and start recording
					# video for *this trial
					self.camera.split_recording(afterfilepath)					
					# Write the bufferSeconds seconds "before" motion to disk
					circulario.copy_to(beforefilepath, seconds=bufferSeconds)
					circulario.clear()
			
					startRecordSeconds = time.time()
					self.secondsElapsedStr = '0'
			
					#logger.debug('Start video file: ' + afterfilename)
					self.currentFile = afterfilename
				
					# Record ONE video file per start trigger (this is a limitation)
					stopOnTrigger = False #todo: make this global and set on pin
					while self.isState('armedrecording') and not stopOnTrigger and (time.time()<(startRecordSeconds + float(repeatDuration))):
						self.camera.wait_recording() # seconds

						self.secondsElapsedStr = str(round(time.time() - startRecordSeconds, 1))

						if captureStill and time.time() > (self.lastStillTime + float(stillInterval)):
							self.camera.capture(self.stillPath, use_video_port=True)
							self.lastStillTime = time.time()
						
						# DO NOT REMOVE THIS !!!
						time.sleep(0.1)
						
					self.secondsElapsedStr = 'n/a'

					self.camera.split_recording(circulario)
			
					self.currentFile = ''
					self.trial.stopTrial()

					self.state = 'armed'
					
					#
					# convert to mp4
					if converttomp4:
						self.convertVideo(beforefilepath, fps)
						self.convertVideo(afterfilepath, fps)
				
				# DO NOT REMOVE THIS
				time.sleep(0.1)

	#########################################################################
	# Add an annotation/watermark on top of video
	#########################################################################
	def annotate(self, text):
		"""
		Add watermark to video
		"""
		if self.camera:
			try:
				self.camera.annotate_background = picamera.Color('black')
				self.camera.annotate_text = str(text)
			except picamera.exc.PiCameraClosed as e:
				logger.error('watermark ' + str(e))

	#########################################################################
	# Thread to convert video from .h264 to .mp4
	#########################################################################
	def convertVideoThread(self, fileQueue, errorQueue):
		"""
		A thread that will monitor fileQueue
		and call ./bin/convert_video.sh to convert .h264 to .mp4
		"""
		
		logger.info('initializing convertVideoThread')
		while True:
			try:
				file = fileQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				pass
			else:
				#print('queue not empty')
				tmpFolderpath, tmpFilename = os.path.split(file['path'])
				logger.info('starting convertVideoThread:' + tmpFilename + ' fps:' + str(file['fps']))
				
				script_path = os.path.dirname(os.path.abspath( __file__ ))
				#print('script_path:', script_path)
				
				cmd = [script_path + "/bin/convert_video.sh", file['path'], str(file['fps']), "delete"]
				
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					#self.lastResponse = 'Converted video to mp4'
				except (subprocess.CalledProcessError, OSError) as e:
					logger.error('convertVideoThread ./bin/convert_video exception: ' + str(e))
					pass
				except:
					raise	
				logger.info('finished convertVideoThread:' + tmpFilename + ' fps:' + str(file['fps']))
				
			time.sleep(0.1)
	
	def convertVideo(self, videoFilePath, fps):
		"""
		Add a file/fps to the convertFileQueue. convertVideoThread() will process it
		"""
		theDict = {}
		theDict['path'] = videoFilePath
		theDict['fps'] = fps
		self.convertFileQueue.put(theDict)
					
if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

	from bTrial import bTrial
	t = bTrial()
	
	c = bCamera(trial=t)

	'''
	# test recording
	c.state = 'recording'
	c.recordVideoThread()
	'''
	
	'''
	# test streaming
	c.state = 'idle'
	c.stream(1)
	time.sleep(20)
	c.stream(0)
	'''
	
	# armed recording
	c.arm(True)
	c.startArmVideo()
	time.sleep(20)
	c.stopArmVideo()
	