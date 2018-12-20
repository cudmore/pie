"""
Author: Robert H Cudmore
Date: 20180808
"""

import time, threading, serial, queue

import logging
logger = logging.getLogger('flask.app')

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
		logger.debug('starting mySerialThread')
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
			time.sleep(0.1)
