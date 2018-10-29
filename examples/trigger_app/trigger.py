# Robert Cudmore
# 20180726

import time
import RPi.GPIO as GPIO

triggerInPin = 24
frameInPin = 23

GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)

# runtime dict
rt = {}
rt['trialIsRunning'] = False
rt['trialNumber'] = 0
rt['trialDurationSeconds'] = 4
rt['startTrialSeconds'] = 0
rt['frameTimeSeconds'] = []

######################################################################
def startTrial(now):
	if rt['trialIsRunning']:
		# trial already running
		pass
	else:
		rt['trialNumber'] += 1
		rt['startTrialSeconds'] = now
		rt['frameTimeSeconds'] = []
		rt['trialIsRunning'] = True
		print('trial', rt['trialNumber'], 'started', now)
			
######################################################################
def updateTrial(now):
	"""
	Return True to continue, return False to stop
	"""
	if rt['trialIsRunning']:
		timeSinceStart = time.time() - rt['startTrialSeconds']
		if timeSinceStart > rt['trialDurationSeconds']:
			stopTrial()
			return False
	else:
		return True

######################################################################
def stopTrial():
	if rt['trialIsRunning']:
		rt['trialIsRunning'] = False
		
		# output frames
		frameNumber = 0
		for frameSeconds in rt['frameTimeSeconds']:
			if frameNumber == 0:
				# no lastInterval
				pass			
			else:
				lastInterval = rt['frameTimeSeconds'][frameNumber] - rt['frameTimeSeconds'][frameNumber-1]
				print(str(frameNumber), lastInterval)
			frameNumber += 1
	else:
		# trial not running
		pass

######################################################################
def newFrame(now):
	rt['frameTimeSeconds'].append(now)
	numFrames = len(rt['frameTimeSeconds'])
	print('new frame', numFrames, now)
	
######################################################################
def triggeIn_Callback(pin):
	now = time.time()
	startTrial(now)
	
######################################################################
def frameIn_Callback(pin):
	now = time.time()
	newFrame(now)
	
def initGPIO():
	#
	# trigger in
	pullUpDown = GPIO.PUD_DOWN # (GPIO.PUD_DOWN, GPIO.PUD_UP)
	GPIO.setup(triggerInPin, GPIO.IN, pull_up_down=pullUpDown)

	polarity = GPIO.RISING # (GPIO.RISING, GPIO.FALIING, GPIO.BOTH)
	bouncetime = 20 # ms
	GPIO.add_event_detect(triggerInPin, polarity, callback=triggeIn_Callback, bouncetime=bouncetime)

	#
	# frame in
	pullUpDown = GPIO.PUD_DOWN # (GPIO.PUD_DOWN, GPIO.PUD_UP)
	GPIO.setup(frameInPin, GPIO.IN, pull_up_down=pullUpDown)

	polarity = GPIO.RISING # (GPIO.RISING, GPIO.FALIING, GPIO.BOTH)
	bouncetime = 20 # ms
	GPIO.add_event_detect(frameInPin, polarity, callback=frameIn_Callback, bouncetime=bouncetime)

	print('gpio initialized')
	
if __name__ == '__main__':
	initGPIO()
	
	print('waiting for trigger in, press ctrl+c to terminate')
	while True:
		now = time.time()
		try:
			keepGoing = updateTrial(now)
			if not keepGoing:
				pass
				#break
		except (KeyboardInterrupt) as e:
			break
		except:
			break
		time.sleep(0.01)
		