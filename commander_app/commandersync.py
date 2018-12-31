# Author: RObert H Cudmore
# Date: 20181222

"""
Purpose: Copy files from any number of PiE servers to local.

Important:
	- Will remove from remote PiE server as follows
	    if self.deleteRemoteFiles
	    and if we copy the file
	    and the file we copied has same size as file on PiE server
	- All files are copied into a folder 'mydata' that is always in the same folder as this script/code
	    Should be able to mount a server into /mydata (e.g. LindenNas)
"""

import os, time, math, stat, sys, logging
import threading, queue
import socket, paramiko

import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed #ProcessPoolExecutor

logger = logging.getLogger('commander')

class UserCancelSync(Exception):
	pass

class CommanderSync(threading.Thread):

	def __init__(self, inQueue, myConfig):
		threading.Thread.__init__(self)
		
		###
		###
		if getattr(sys, 'freeze', False):
			# running as bundle (aka frozen)
			logger.info('running frozen')
			self.bundle_dir = sys._MEIPASS
		else:
			# running live
			logger.info('running live')
			self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
		logger.info('bundle_dir is ' + self.bundle_dir)
		###
		###

		# userPath will be /Users/<user> on macOS and /home/<user> on Debian/Raspbian
		userPath = os.path.expanduser('~')
		self.localFolder = os.path.join(userPath, 'commander_data') # all local files with be in this folder
		logger.info('saving to ' + self.localFolder)
		
		#self._localFolder = os.path.abspath(self.localFolder)
		#print('Commander sync will save into:', self._localFolder)
		
		# to log in to remote servers
		self.username = 'pi'
		self.password = 'poetry7d'
		
		# this code will not work if remote PiE server does not have /home/pi/video
		self.remoteFolder = 'video' # all files on remote PiE servers are in /home/pi/video
				
		# delete files on remote (i) when copied and (ii) when local size is same as remote size
		self.deleteRemoteFiles = False
		
		self.copyTheseExtensions = ['.mp4', '.txt']


		self.inQueue = inQueue # commands are ('fetchfiles', 'sync', 'cancel')
		
		self.cancel = False
		self.fetchIsBusy = False
		self.syncIsBusy = False
		
		self.sshTimeout = 5 # seconds, timeout when trying to establish ssh connection
		
		# load ip list (same as commander) and assign (self.serverList, self.ipDict)
		self.setConfig(myConfig)

		self.numFilesToCopy = 0 # total number across all ip in ipList
		self.myFileList = []
		
		self.mySyncList = [] # what we actually synchronized
		
		self.pool = None
		self.myFutures = None
		
		self.syncStartedSeconds = None
		self.syncStartStr = ''
		self.syncElapsedSeconds = None
		self.syncElapsedStr = ''
		#self.syncNumToCopy = 0 # number remaining
		self.syncNumCopied = 0 # number actually copied
		self.syncNumTotalToCopy = 0 # total number to copy
		self.syncTotalBytesToCopy = 0
		self.syncBytesCopied = 0
		self.syncEstimatedTimeArrival = None # estimated time remaining
		
		#self.known_hosts = os.path.join(os.path.dirname(__file__), 'known_hosts')
		
	def setDeleteRemoteFiles(self, onoff):
		self.deleteRemoteFiles = onoff
		print('commandersync.py setDeleteRemoteFiles() set self.deleteRemoteFiles:', self.deleteRemoteFiles)
	
	# 20181229, was this
	#def loadConfig(self):
	def setConfig(self, serverList):
		"""
		Sharing config file with main commander
		This is an extremely simple list of IP, it is NOT json
		When user changes/saves ip list in main commander page, this needs to be reloaded
		
		Parameters:
			serverList: List of dict {ip, username, password}
		Assigns:
			self.serverList
			self.ipDict
		"""
		
		
		"""
		#thisFile = 'config/config_commander.txt'
		thisFile = os.path.join(self.bundle_dir, 'config', 'config_commander.txt')
		if not os.path.isfile(thisFile):
			#logger.info('defaulting to config/config_commander_factory.txt')
			#thisFile = 'config/config_commander_factory.txt'
			thisFile = os.path.join(self.bundle_dir, 'config', 'config_commander_factory.txt')
		logger.info('Loading config file ' + thisFile)
		with open(thisFile, 'r') as f:
			configfile = f.readlines()
		# remove whitespace characters like ',' and `\n` from each line
		returnConfigFile = [x.strip(',\n') for x in configfile] 

		#
		# assign
		self.ipList = returnConfigFile
		"""
		
		print('commandersync.serverList serverList:', serverList)
		
		self.serverList = serverList
		
		self.ipDict = {}
		for server in self.serverList:
			self.ipDict[server['ip']] = {
				'ip': server['ip'],
				'hostname': '',
				'madeConnection': False,
				'numFiles': 0,
				'numFilesToCopy': 0,
			}

		#return returnConfigFile
		
	############################################################################
	def run(self):
		"""
		Continuosly monitor and respond to incoming commands in self.inQueue Queue
		"""
		while True:
			#try:
			if 1:
				#
				# STOP TRYING TO USE THIS DURING SYNC AND SYNC CANCEL ... IT DOES NOT GET EXECUTED
				#
				"""
				if self.syncStartedSeconds is not None:
					print('setting xxx yyy zzz')
					self.syncElapsedSeconds = time.time() - self.syncStartedSeconds
					self.syncElapsedStr = _humanReadableTime(self.syncElapsedSeconds)
				"""
				
				# each time through the loop, determine if we have any more running futures
				# if not then sync is no longer busy
				allDone = True
				if self.myFutures is not None:
					for future in self.myFutures:
						try:
							if not future.done():
								allDone = False
								break
						except (UserCancelSync) as e:
							print('run() received UserCancelSync:', e, 'future:', future)
						except (OSError) as e:
							print('run() received OSError exception:', e)
						except (Exception) as e:
							print('run() received unknown exception:', e)
					if allDone:
						if self.syncIsBusy:
							print('run() determined all future(s) are done()')
							# added 122818
							print('run() setting self.myFutures = None')
							
							# ???
							self.myFutures = None
							
							# ???
							self.cancel = False

							"""
							self.syncStartedSeconds = None
							self.syncStartStr = ''
							self.syncElapsedSeconds = ''
							"""
							
						self.syncIsBusy = False
					"""
					else:
						# we never get here
						print('not all threads are done')
					"""
					
					"""
					else:
						print('setting xxx yyy zzz')
						self.syncElapsedSeconds = time.time() - self.syncStartedSeconds
						self.syncElapsedStr = _humanReadableTime(self.syncElapsedSeconds)
					"""
				if self.syncIsBusy:
					self.syncBytesCopied = 0
					self.syncEstimatedTimeArrival = 0
					tmpFileCount = 0
					for idx, file in enumerate(self.myFileList):
						self.syncBytesCopied += file['bytesCopied']
						if file['etaSeconds'] is not None:
							self.syncEstimatedTimeArrival += file['etaSeconds']
							tmpFileCount += 1
					if tmpFileCount > 0:
						self.syncEstimatedTimeArrival /= tmpFileCount
					else:
						self.syncEstimatedTimeArrival = None
					#print('self.syncEstimatedTimeArrival:', self.syncEstimatedTimeArrival)
					
				try:
					inDict = self.inQueue.get(block=False, timeout=0)
				except (queue.Empty) as e:
					# there was nothing in the queue
					pass
				else:
					# there was something in the queue
					#print('commandersync.run() inDict:', inDict)

					if inDict == 'fetchfiles':
						self.fetchFileList()
					if inDict == 'sync':
						# need to spawn sync as new thread so we can cancel!!!

						self.syncStartedSeconds = time.time()
						self.syncStartStr = time.strftime('%Y%m%d %H:%M:%S', time.localtime(math.floor(self.syncStartedSeconds))) 
						self.syncElapsedSeconds = 0

						try:
							self.sync()
						except (Exception) as e:
							print('commandersync.run() received exception:', str(e))
						
					if inDict == 'cancel': # cancel a sync
						print('\n    **** commandersync.run() inDict == cancel')
						if self.syncIsBusy:
							print('commandersync setting self.cancel = True')
							self.cancel = True
							"""
							try:
								raise UserCancelSync
							except (UserCancelSync) as e:
								pass
							"""
				# make sure not to remove this
				time.sleep(0.1)
			"""
			except (Exception) as e:
				print('commandersync.run() 2 unknown exception:', e)
			"""
								
	############################################################################
	############################################################################
	def fetchFileList(self):
		"""
		Fetch all files to be copied from each ip in self.serverList
		
		Detalails:
			Will only add files with extensions self.copyTheseExtensions
		"""
		
		def _fetchFileList(ip, path, depth):
			"""
			recursively build list of files starting at path 'path'
			"""
			#print(depth, '=== fetchFileList() path:', path)

			# ftp.listdir_attr will fail if remote does not have folder self.remoteFolder
			
			# actualPath will be used on remote linux system, do not use os.path.join
			actualPath = self.remoteFolder + '/' + path # we are always looking in self.remoteFolder = /home/pi/video
			
			for attr in ftp.listdir_attr(path=actualPath): # returns SFTPAttributes

				# todo: remove this, paramiko will never return ('.', '..')
				if attr.filename.startswith('.'):
					continue

				if stat.S_ISDIR(attr.st_mode):
					# attr is a folder/dir -->> recursively traverse into it
					# newPath will be used on remote linux system, do not use os.path.join
					if path:
						newPath = path + '/' + attr.filename
					else:
						newPath = attr.filename
						
					_fetchFileList(ip, newPath, depth + '    ')
				else:
					# assuming attr is a file -->> append to self.myFileList

					remoteFile = attr.filename
					sizeInBytes = attr.st_size
					
					tmpFileName, tmpExtension = os.path.splitext(remoteFile)
					if not (tmpExtension in self.copyTheseExtensions):
						continue
					
					#
					# check if local file already exists
					fullLocalPath = os.path.join(self.localFolder, hostname, path, remoteFile)
					#print('fullLocalPath:', fullLocalPath)
					localExists = os.path.isfile(fullLocalPath)

					if not localExists:
						self.numFilesToCopy += 1 # across all ip in self.serverList
						
					myFile = {
						'ip': ip,
						'hostname': hostname,
						'remotePath': path,
						'remoteFile': remoteFile,
						'progress': '', # set in self.myCallback()
						'size': sizeInBytes,
						'bytesCopied': 0,
						'localExists': localExists,
						'humanSize': self._humanReadableSize(sizeInBytes),
						'humanProgress': '', # initialized as string but assigned to int/float in myCallback
						'startSeconds': 0, # leave this initialized to 0 (not str)
						'elapsedTime': '', # initialized as string but assigned to int/float in myCallback
						'percent': '', # initialized as string but assigned to int/float in myCallback
						'lastCallbackSeconds': None,
						'lastCallbackBytes': None,
						'etaSeconds': None,
					}
					self.myFileList.append(myFile)
					self.ipDict[ip]['numFiles'] += 1 # for one ip
					if not localExists:
						self.ipDict[ip]['numFilesToCopy'] += 1 # for one ip
					
		# fetch ip from file, may have configured in main interface
		#self.ipList = self.loadConfig()
		#self.loadConfig() # now called self.setConfig
		
		print('commandersync.fetchfilelist self.serverList:', self.serverList)
		
		self.fetchIsBusy = True
		self.numFilesToCopy = 0
		self.myFileList = []
		for server in self.serverList:
			
			print('fetchFileList server:', server)
			current_ip = server['ip']
			
			# initialize internal dictionary
			self.ipDict[current_ip]['ip'] = current_ip
			self.ipDict[current_ip]['hostname'] = '' # assigned below
			self.ipDict[current_ip]['numFiles'] = 0
			self.ipDict[current_ip]['numFilesToCopy'] = 0
			self.ipDict[current_ip]['madeConnection'] = False
			
			# connect with ssh
			ssh = paramiko.SSHClient()
			#ssh.load_host_keys(self.known_hosts)
			#ssh.load_system_host_keys()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			
			try:
				logger.info('opening ssh connection to ip: ' + current_ip)
				ssh.connect(current_ip, port=22, username=self.username, password=self.password, timeout=self.sshTimeout)
			except (paramiko.ssh_exception.BadHostKeyException) as e:
				print('fetchFileList() ssh.connect exception 1:', str(e))
			except(paramiko.ssh_exception.AuthenticationException) as e:
				print('fetchFileList() ssh.connect exception 2:', str(e))
			except (paramiko.ssh_exception.SSHException) as e:
				print('fetchFileList() ssh.connect exception 3:', str(e))
			except (paramiko.ssh_exception.NoValidConnectionsError) as e:
				print('fetchFileList() ssh.connect exception 4:', str(e))
			except (socket.timeout) as e:
				print('*** fetchFileList() ssh.connect exception 5:', str(e))
			else: # else is only executed if no exceptions !!!
				print('fetchFileList() in else')

				self.ipDict[server['ip']]['madeConnection'] = True
				
				# todo: add error checking here
				
				# get remote hostname, we will make a local folder 'hostname'
				stdin, stdout, stderror = ssh.exec_command('hostname')
				hostname = stdout.read().strip().decode("utf-8")
			
				self.ipDict[current_ip]['hostname'] = hostname
				
				ftp = ssh.open_sftp()
					
				_fetchFileList(current_ip, '', depth='')
					
				ftp.close()

			ssh.close()

		print('fetchFileList() found', self.numFilesToCopy, 'files to copy from', len(self.myFileList), 'files across', len(self.serverList), 'PiE servers')

		self.fetchIsBusy = False
		
	############################################################################
	def myCallback(self, bytesDone, bytesTotal, file, idx, lock):
		"""
		Track the progress of a network file copy
		
		Parameters:
			file:
			idx: index into self.myFileList
			lock: a global lock shared across all copyThread threads
		"""

		try:
			#print('self.cancel:', self.cancel)
			if self.cancel:
				#
				print('!!! myCallback() raise UserCancelSync idx:', idx, 'file:', file)
				raise UserCancelSync
				#
			
			self.myFileList[idx]['progress'] = bytesDone
			self.myFileList[idx]['humanProgress'] = self._humanReadableSize(bytesDone)
		
			elapsedTime = time.time() - self.myFileList[idx]['startSeconds']
			elapsedTimeStr = self._humanReadableTime(elapsedTime)
			self.myFileList[idx]['elapsedTime'] = elapsedTimeStr
			self.myFileList[idx]['percent'] = round(bytesDone/bytesTotal*100,1)
		
			self.myFileList[idx]['bytesCopied'] = bytesDone
			
			#
			# calculate eta seconds
			if self.myFileList[idx]['lastCallbackSeconds'] is not None:
				
				#totalBytesRemaining = self.syncTotalBytesToCopy - self.syncBytesCopied
				totalBytesRemaining = bytesTotal - bytesDone
				
				secondsElapsed = time.time() - self.myFileList[idx]['lastCallbackSeconds']
				elapsedBytes = bytesDone - self.myFileList[idx]['lastCallbackBytes'] # since last callback
				etaSeconds = secondsElapsed * totalBytesRemaining / elapsedBytes
				self.myFileList[idx]['etaSeconds'] = etaSeconds
				
				# when we are done, there is no more ETA
				if bytesDone == bytesTotal:
					self.myFileList[idx]['etaSeconds'] = None
					
			self.myFileList[idx]['lastCallbackSeconds'] = time.time()
			self.myFileList[idx]['lastCallbackBytes'] = bytesDone
				
			
			with lock:
				self.syncElapsedSeconds = time.time() - self.syncStartedSeconds
				self.syncElapsedStr = self._humanReadableTime(self.syncElapsedSeconds)
		
		except (UserCancelSync) as e:
			#print('!!! myCallback() RE RAISE UserCancelSync idx:', idx, 'file:', file)
			raise
		except (Exception) as e:
			print('!!! myCallback() Exception:', e, 'idx:', idx, 'file:', file)
		
	def copyThread(self, idx, ip, hostname, remoteFilePath, localFilePath, lock):
		"""
		Copy a single file from remote to local
		Don't copy if .lock file exists
		
		Parameters:
			idx: index into self.myFileList
		"""

		startTime = time.time()
		
		# don't start work if there is a pending cancel
		try:
			inDict = self.inQueue.get(block=False, timeout=0)
		except (queue.Empty) as e:
			# there was nothing in the queue
			pass
		else:
			if inDict == 'cancel': # cancel a sync
				if self.syncIsBusy:
					self.cancel = True

		ftp_get_cancel = False # ftp.get was started but then cancelles
		cancelledBefore_get = False # cancelled before ftp.get was started
		
		if self.cancel:
			print('copyThread() is self.cancel idx:', idx, 'remoteFilePath:', remoteFilePath)
			cancelledBefore_get = True
			pass
		else:
			logger.info('starting sftp copy of remote file: ' + remoteFilePath)
			
			# self.mySyncList
			syncDict = {
				'ip': ip,
				'hostname': hostname,
				'remoteFile': remoteFilePath,
				'localFile': localFilePath,
				'lockFile': False,
				'madeCopy': False,
			}
		
			ssh = paramiko.SSHClient()
			#ssh.load_host_keys(self.known_hosts)
			#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		
			try:
				ssh.connect(ip, port=22, username=self.username, password=self.password, timeout=self.sshTimeout)
			except (paramiko.ssh_exception.BadHostKeyException) as e:
				print('\n*** exception copyThread() 1:', str(e), 'remoteFilePath:', remoteFilePath)
			except(paramiko.ssh_exception.AuthenticationException) as e:
				print('\n *** exception copyThread() 2:', str(e), 'remoteFilePath:', remoteFilePath)
			except (paramiko.ssh_exception.SSHException) as e:
				print('\n *** exception copyThread() 3 paramiko.ssh_exception.SSHException:')
				print('   ', str(e))
				print('   remoteFilePath:', remoteFilePath)
				print('   ip:', ip)
				print('   hostname:', hostname)
				
				# see: https://stackoverflow.com/questions/25609153/paramiko-error-reading-ssh-protocol-banner
				# need to take action here !!!
				# getting exception e:
				# Error reading SSH protocol banner[Errno 54] Connection reset by peer
				#
				# this exception is pretty random.
				# one idea is to just force web interface to NOT allow sync twice in a row!!! Require user to 'fetch' again
				# with this it seems to be fixed
				self.myFileList[idx]['percent'] = 'Busy Error'

				with lock:
					self.syncNumTotalToCopy -= 1
				
			except (paramiko.ssh_exception.NoValidConnectionsError) as e:
				print('\n *** exception copyThread() 4:', str(e), 'remoteFilePath:', remoteFilePath)
			except (socket.timeout) as e:
				print('\n *** exception copyThread() 5:', str(e), 'remoteFilePath:', remoteFilePath)
			else: # else is only executed if no exceptions !!!
				
				ftp = ssh.open_sftp()

				#
				# if the remote has a .lock then DO NOT get()
				lockFileExists = False
				lockFile = remoteFilePath + '.lock'
				#print('copyThread() looking for lock file:', lockFile)
				try:
					attr = ftp.stat(lockFile)
					lockFileExists = True
					print('    !!! found lock file:', lockFile)
				except (IOError) as e:
					# no .lock file
					#print('    !!! no lock file:', lockFile)
					#sprint('xxx IOError')
					pass
					
				if lockFileExists:
					"""
					print('    copyThread()')
					print('    ip:', ip, 'hostname:', hostname, 'remoteFilePath:', remoteFilePath)
					print('    FOUND LOCK FILE ON REMOTE -->> did not copy')
					"""
					syncDict['lockFile'] = True
				else:
					#
					# copy the file from remote to local
					"""
					print('    copyThread()')
					print('    ip:', ip, 'hostname:', hostname, 'remoteFilePath:', remoteFilePath)
					print('    local file:', localFilePath)
					"""
					
					"""
					with lock:
						self.syncNumToCopy += 1
					"""
					
					try:
						self.myFileList[idx]['startSeconds'] = time.time()
						
						try:
							###
							# ftp.get
							###
							lambdaFunction = lambda a, b, file=remoteFilePath, idx=idx, lock=lock: self.myCallback(a, b, file, idx, lock)
							ftp.get(remoteFilePath, localFilePath, callback=lambdaFunction)
						except (UserCancelSync) as e:
							print('    *** copyThread() got UserCancelSync exception idx:', idx, 'remoteFilePath:', remoteFilePath)
							# CLEANUP PARTIAL FILE
							ftp_get_cancel = True
						except (Exception) as e:
							print('unknown exception in ftp.get():', e, 'remoteFilePath:', remoteFilePath)
						else: # else is only executed if no exceptions !!!
							try:
								pass
								#ftp.close()
							except:
								print('ftp.close() exception', 'remoteFilePath:', remoteFilePath)
							
					except (IOError) as e:
						print('MY EXCEPTION: IOError exception in ftp.get() e:', str(e), ', remoteFilePath:', remoteFilePath)
					except:
						print('MY EXCEPTION: unknown exception in ftp.get(), remoteFilePath:', remoteFilePath)
						# should try and remove fullLocalPath
					else: # else is only executed if no exceptions !!!
						#
						# once file is copied to local and we are 100% sure this is true, remove from remote
	
						if ftp_get_cancel:
							print('        ****    ftp_get_cancel, remove file idx:', idx, 'file:', localFilePath)
							os.remove(localFilePath)
							self.myFileList[idx]['percent'] = 'Cancelled'
						else:
							print('    done copying from remote:', remoteFilePath)
							with lock:
								#self.syncNumToCopy -= 1
								self.syncNumCopied += 1
								
							syncDict['madeCopy'] = True
					
							# before we delete from remote, check the size of local is same as size of remote?
							attr_remote = ftp.lstat(path=remoteFilePath)
							remoteSize = attr_remote.st_size
	
							attr_local = os.stat(localFilePath)
							localSize = attr_local.st_size # 1 Byte = 10**-6 MB
	
							#print('    remoteSize:', remoteSize, 'localSize:', localSize)
	
							if remoteSize == localSize:
								if self.deleteRemoteFiles:
									print('    removing remote file:', remoteFilePath)
									ftp.remove(remoteFilePath)
								
									#
									# delete parent (date) dir if neccessary (empty)
									# construct parentDirPath (e.g. date folder) and remove if empty
									"""
									parentDirPath = ???
									attrList in ftp.listdir_attr(path=parentDirPath): # returns SFTPAttributes
									if attrList is Empty:
										delete parentDirPath
									"""
								else:
									print('    not removing from remote server, self.deleteRemoteFiles == False')
							else:
								print('    ERROR: sizes did not match -->> did not remove from remote server')
		
				#print('1')
				ftp.close()

			#print('2')
			try:
				ssh.close()
			except:
				print('ssh.close() exception')
				
			self.mySyncList.append(syncDict)
		
		stopTime = time.time()
		elapsedSeconds = round(stopTime-startTime,2)
		if ftp_get_cancel or cancelledBefore_get:
			pass
		else:
			print('    copyThread() took', elapsedSeconds, 'remoteFilePath:', remoteFilePath)
		
		try:
			pass
		except (Exception) as e:
			print('copyThread() unknown exception:', e)
	
	def sync(self):
		"""
		Copy all files in self.myFileList
		Do not copy files that already exist locally
		"""
		
		print('\n    *** commandersync.sync()')
		
		self.syncIsBusy = True
		
		self.mySyncList = [] # keep track of what we actually sync

		self.syncNumTotalToCopy = 0
		#self.syncNumToCopy = 0
		self.syncNumCopied = 0 # number actually copied
		
		#
		# create a pool of workers
		max_workers= None # when None = cpu cores * 5
		thread_name_prefix= 'myThreadPoolExecutor'
		self.pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=thread_name_prefix) #max_workers
		
		self.myFutures = []

		"""
		self.syncStartedSeconds = time.time()
		self.syncStartStr = time.strftime('%Y%m%d %H:%M:%S', time.localtime(math.floor(self.syncStartedSeconds))) 
		self.syncElapsedSeconds = 0
		"""
		
		# copy_thread needs to use a lock to set any self.xxx member variables
		self.myManager = multiprocessing.Manager()
		self.myLock = self.myManager.Lock()
		
		#
		# insert all files into self.pool using self.pool.submit
		startTime = time.time()
		numCopied = 0
		for idx, file in enumerate(self.myFileList):

			ip = file['ip']
			hostname = file['hostname']
			remotePath = file['remotePath']
			remoteFile = file['remoteFile']
			localExists = file['localExists'] # todo: use this
			
			print('self.localFolder:', self.localFolder)
			print('hostname:', hostname)
			print('remotePath:', remotePath)
			localFolder = os.path.join(self.localFolder, hostname, remotePath)
			print('localFolder:', localFolder)
			
			#
			# check if local file already exists
			# todo: use localExists
			fullLocalPath = os.path.join(localFolder, remoteFile)
			if os.path.isfile(fullLocalPath):
				#print('local already exists:', fullLocalPath)
				continue
		
			#
			# todo: put all 3 of these mkdir into copyThread()
			#
			
			# 1) make local directory for all files (e.g. 'video')
			if not os.path.isdir(self.localFolder):
				print('mkdir self.localFolder:', self.localFolder)
				os.mkdir(self.localFolder) # 

			# 2) make local directory for 'hostname'
			hostNameFolder = os.path.join(self.localFolder, hostname)
			if not os.path.isdir(hostNameFolder):
				print('mkdir hostNameFolder:', hostNameFolder)
				os.mkdir(hostNameFolder) # 

			#
			# 3) make local directory (usually date folder 'yyyymmdd')
			if not os.path.isdir(localFolder):
				print('mkdir localFolder:', localFolder)
				os.mkdir(localFolder) # assumes we are only going one dir deep, e.g. /home/pi/video/20181220

			# all our remote files are always in /home/pi/video
			# can't use join, this is always a linux path and needs to be linux path even on window
			# todo: make sure this works when remotePath == ''
			if remotePath:
				fullRemoteFile = self.remoteFolder + '/' + remotePath + '/' + remoteFile
			else:
				fullRemoteFile = self.remoteFolder + '/' + remoteFile
				
			##
			# self.pool.submit
			##
			try:
				future = self.pool.submit(self.copyThread, idx, ip, hostname, fullRemoteFile, fullLocalPath, self.myLock)
				self.myFutures.append(future)
			except:
				# this never happens
				print('self.pool.submit() exception')
				
			# in main run(), go through this list of future(s)
			# check is ALL are done()
			# once all are done() then self.syncIsBusy = False
			
			with self.myLock:
				self.syncNumTotalToCopy += 1
				#self.syncNumToCopy += 1 # decremented when done in copyThread
				self.syncTotalBytesToCopy += file['size']
			numCopied += 1

		"""
		# this blocks
		print('*** sync() starting for future in as_completed(self.myFutures)')
		for future in as_completed(self.myFutures):
			# future.state
			# future.returned
			print('   yyy', future)
		print('*** sync() finished for future in as_completed(self.myFutures)')
		"""
		
		# wait for background threads to stop
		#print('sync() self.pool.shutdown(wait=True)')
		#self.pool.shutdown(wait=True)
		
		# this will return immediately but we still need to wait for running tasks !!!!
		try:
			print('self.pool.shutdown(wait=False)')
			self.pool.shutdown(wait=False)
		except (UserCancelSync) as e:
			print('sync() received exception UserCancelSync:', e)
		except (OSError) as e:
			print('sync() received exception OSError:', e)
		except (Exception) as e:
			print('sync() received unknown exception:', e)
			
		#
		# i need to change the logic here
		# self.syncIsBusy needs to be updated to reflect that threads in pool are still running???
		self.syncIsBusy = True
		
		#print('sync() is exiting')


	################################################################################
	# Utilities
	################################################################################
	def _humanReadableSize(self, bytes):
		"""
		Return a human readable string with unit ('bytes', 'KB', 'MB')
		"""
		theStr = str(bytes)
		if bytes < 1000:
			# bytes
			theStr = str(bytes) + ' bytes'
		elif bytes < 1000000:
			# KB, divide -> round -> int -> str
			theStr = str(int(round(bytes/1000,0))) + ' KB'
		elif bytes < 1000000000:
			# MB
			theStr = str(round(bytes/1000000,1)) + ' MB'
		else:
			# MB
			theStr = str(round(bytes/1000000000,2)) + ' GB'
		return theStr

	################################################################################
	def _humanReadableTime(self, seconds):
		"""
		Given seconds, return string with hours and minutes
		"""
		retStr = ''
		if seconds is not None:
			theSeconds = round(seconds % 60,1)
			if theSeconds > 1:
				theSeconds = math.floor(theSeconds)
			theMinutes = math.floor(seconds/60)
			#print('seconds:', seconds, 'theMinutes:', theMinutes, 'theSeconds:', theSeconds)
			if theMinutes > 0:
				retStr += str(theMinutes) + ' min'
			if theSeconds > 0 or ((not theMinutes>0) and theSeconds>=0):
				retStr += ' ' + str(theSeconds) + ' sec'
		return retStr

		
if __name__ == '__main__':
	inQueue = queue.Queue()
	cs = CommanderSync(inQueue)
	
	print(cs._humanReadableTime(59))
	
	"""
	cs.daemon = True
	cs.start()
	
	print('putting fetchfiles on inQueue')
	inQueue.put('fetchfiles')
	#fileList = cs.fetchFileList()
	
	print('waiting for results')
	while cs.isBusy:
		pass
	
	for k,v in cs.ipDict.items():
		print(k,v)
		
	#cs.sync()
	
	#for file in cs.myFileList:
	#	print(file)
	"""