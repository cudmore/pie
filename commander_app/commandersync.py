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

import os, time, math, stat
import threading, queue
import socket, paramiko

class CommanderSync(threading.Thread):

	def __init__(self, inQueue):
		threading.Thread.__init__(self)
		
		self.localFolder = '../../mydata' # all local files with be in this folder
		
		self._localFolder = os.path.abspath(self.localFolder)
		print('Commander sync will save into:', self._localFolder)
		
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
		
		# load ip list (same as commander) and assign (self.ipList, self.ipDict)
		self.loadConfig()

		self.numFilesToCopy = 0 # total number across all ip in ipList
		self.myFileList = []
		
		self.mySyncList = [] # what we actually synchronized
		
		#self.known_hosts = os.path.join(os.path.dirname(__file__), 'known_hosts')
		
	def setDeleteRemoteFiles(self, onoff):
		self.deleteRemoteFiles = onoff
		print('commandersync.py setDeleteRemoteFiles() set self.deleteRemoteFiles:', self.deleteRemoteFiles)
	
	def loadConfig(self):
		"""
		Sharing config file with main commander
		This is an extremely simple list of IP, it is NOT json
		When user changes/saves ip list in main commander page, this needs to be reloaded
		
		Assigns:
			self.ipList
			self.ipDict
		"""
		
		thisFile = 'config/config_commander.txt'
		if not os.path.isfile(thisFile):
			#logger.info('defaulting to config/config_commander_factory.txt')
			thisFile = 'config/config_commander_factory.txt'
		#logger.info('Loading config file ' + thisFile)
		with open(thisFile, 'r') as f:
			configfile = f.readlines()
		# remove whitespace characters like ',' and `\n` from each line
		returnConfigFile = [x.strip(',\n') for x in configfile] 

		#
		# assign
		self.ipList = returnConfigFile
		
		self.ipDict = {}
		for ip in self.ipList:
			self.ipDict[ip] = {
				'ip': ip,
				'hostname': '',
				'madeConnection': False,
				'numFiles': 0,
				'numFilesToCopy': 0,
			}

		return returnConfigFile
		
	############################################################################
	def run(self):
		"""
		Continuosly process icoming commands in self.inQueue Queue
		"""
		while True:
			try:
				inDict = self.inQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				# there was nothing in the queue
				pass
			else:
				# there was something in the queue
				print('commandersync.run() inDict:', inDict)

				if inDict == 'fetchfiles':
					self.fetchFileList()
				if inDict == 'sync':
					# need to spawn sync as new thread so we can cancel!!!
					self.sync()
				if inDict == 'cancel': # cancel a sync
					print('commandersync.run() inDict == cancel')
					if self.syncIsBusy:
						print('commandersync setting self.cancel = True')
						self.cancel = True
					
			# make sure not to remove this
			time.sleep(0.1)
				
	############################################################################
	def _humanReadableSize(self, bytes):
		"""
		Return a human readable string with unit ('bytes', 'KB', 'MB')
		"""
		
		# todo: add GB

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

	############################################################################
	def fetchFileList(self):
		"""
		fetch all files to be copied from each ip in self.ipList
		"""
		
		def _fetchFileList(ip, path, depth):
			#print(depth, '=== fetchFileList() path:', path)

			# ftp.listdir_attr will fail if remote does not have folder self.remoteFolder
			actualPath = os.path.join(self.remoteFolder, path) # we are always looking in remote /home/pi/video
			
			for attr in ftp.listdir_attr(path=actualPath): # returns SFTPAttributes

				if attr.filename.startswith('.'):
					continue

				if stat.S_ISDIR(attr.st_mode):
					# if attr is a folder/dir -->> recursively traverse into it
					newPath = os.path.join(path, attr.filename)
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
						self.numFilesToCopy += 1 # across all ip in self.ipList
						
					myFile = {
						'ip': ip,
						'hostname': hostname,
						'remotePath': path,
						'remoteFile': remoteFile,
						'progress': 0, # set in self.myCallback()
						'size': sizeInBytes,
						'localExists': localExists,
						'humanSize': self._humanReadableSize(sizeInBytes),
						'humanProgress': '0', # set in self.myCallback(),
						'startSeconds': 0,
						'elapsedTime': 0
					}
					self.myFileList.append(myFile)
					self.ipDict[ip]['numFiles'] += 1 # for one ip
					if not localExists:
						self.ipDict[ip]['numFilesToCopy'] += 1 # for one ip
					
		# fetch ip from file, may have configured in main interface
		#self.ipList = self.loadConfig()
		self.loadConfig()
		
		self.fetchIsBusy = True
		self.numFilesToCopy = 0
		self.myFileList = []
		for ip in self.ipList:
			
			# initialize internal dictionary
			self.ipDict[ip]['ip'] = ip
			self.ipDict[ip]['hostname'] = '' # assigned below
			self.ipDict[ip]['numFiles'] = 0
			self.ipDict[ip]['numFilesToCopy'] = 0
			self.ipDict[ip]['madeConnection'] = False
			
			# connect with ssh
			ssh = paramiko.SSHClient()
			#ssh.load_host_keys(self.known_hosts)

			#ssh.load_system_host_keys()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			
			try:
				print('fetchFileList() opening connection to ip:', ip)
				ssh.connect(ip, port=22, username=self.username, password=self.password, timeout=self.sshTimeout)
			except (paramiko.ssh_exception.BadHostKeyException) as e:
				print('exception 1:', str(e))
			except(paramiko.ssh_exception.AuthenticationException) as e:
				print('exception 2:', str(e))
			except (paramiko.ssh_exception.SSHException) as e:
				print('exception 3:', str(e))
			except (paramiko.ssh_exception.NoValidConnectionsError) as e:
				print('exception 4:', str(e))
			except (socket.timeout) as e:
				print('exception 5:', str(e))
			else: # else is only executed if no exceptions !!!
				self.ipDict[ip]['madeConnection'] = True
				
				# todo: add error checking here
				
				# get remote hostname, we will make a local folder 'hostname'
				stdin, stdout, stderror = ssh.exec_command('hostname')
				hostname = stdout.read().strip().decode("utf-8")
				#print('hostname:', hostname, type(hostname))
			
				self.ipDict[ip]['hostname'] = hostname
				
				ftp = ssh.open_sftp()
					
				_fetchFileList(ip, '', depth='')
					
				ftp.close()

			ssh.close()

		print('fetchFileList() found', self.numFilesToCopy, 'files to copy from', len(self.myFileList), 'files across', len(self.ipList), 'PiE servers')
		for k, v in self.ipDict.items():
			print('    ', k, v)
			
		self.fetchIsBusy = False
	############################################################################
	def myCallback(self, bytesDone, bytesTotal, file, idx):
		"""
		Track the progress of a network file copy
		
		Parameters:
			idx: index into self.myFileList
		"""
		self.myFileList[idx]['progress'] = bytesDone
		self.myFileList[idx]['humanProgress'] = self._humanReadableSize(bytesDone)
		
		self.myFileList[idx]['elapsedTime'] = time.time() - self.myFileList[idx]['startSeconds']
		
		if bytesDone == bytesTotal:
			#print('        done:', file, bytesDone, 'of', bytesTotal, ',', bytesTotal*(10**-6), 'MB')
			pass
		else:
			#print('        progress:', file, bytesDone, 'of', bytesTotal)
			pass
		#pass
	
	def copyThread(self, idx, ip, hostname, remoteFilePath, localFilePath):
		"""
		Copy a single file from remote to local
		Don't copy if .lock file exists
		
		Parameters:
			idx: index into self.myFileList
		"""

		startTime = time.time()
		
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
			print('exception copyThread() 1:', str(e))
		except(paramiko.ssh_exception.AuthenticationException) as e:
			print('exception copyThread() 2:', str(e))
		except (paramiko.ssh_exception.SSHException) as e:
			print('exception copyThread() 3:', str(e))
		except (paramiko.ssh_exception.NoValidConnectionsError) as e:
			print('exception copyThread() 4:', str(e))
		except (socket.timeout) as e:
			print('exception copyThread() 5:', str(e))
		else:
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
				pass
	
			if lockFileExists:
				"""
				print('    copyThread()')
				print('    ip:', ip, 'hostname:', hostname)
				print('    remote file:', remoteFilePath)
				print('    FOUND LOCK FILE ON REMOTE -->> did not copy')
				"""
				syncDict['lockFile'] = True
			else:
				#
				# copy the file from remote to local
				"""
				print('    copyThread()')
				print('    ip:', ip, 'hostname:', hostname)
				print('    remote file:', remoteFilePath)
				print('    local file:', localFilePath)
				"""
				try:
					self.myFileList[idx]['startSeconds'] = time.time()
					lambdaFunction = lambda a, b, file=remoteFilePath, idx=idx: self.myCallback(a, b, file, idx)
					ftp.get(remoteFilePath, localFilePath, callback=lambdaFunction)
				except (IOError) as e:
					print('MY EXCEPTION: IOError exception in ftp.get() e:', str(e), ', file:', remoteFilePath)
				except:
					print('MY EXCEPTION: unknown exception in ftp.get(), file:', remoteFilePath)
					# should try and remove fullLocalPath
				else: # else is only executed if no exceptions !!!
					#
					# once file is copied to local and we are 100% sure this is true, remove from remote
	
					print('    done copying from remote:', remoteFilePath)
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
						else:
							print('    not removing from remote server, self.deleteRemoteFiles == False')
					else:
						print('    ERROR: sizes did not match -->> did not remove from remote server')
		
			ftp.close()

		ssh.close()

		self.mySyncList.append(syncDict)
		
		stopTime = time.time()
		elapsedSeconds = round(stopTime-startTime,2)
		print('    took', elapsedSeconds)
		
	def sync(self):
		"""
		Copy all files in self.myFileList
		Do not copy files that already exist locally
		"""
		
		print('=== commandersync.sync()')
		
		self.syncIsBusy = True
		
		self.mySyncList = [] # keep track of what we actually sync
		
		startTime = time.time()
		numCopied = 0
		for idx, file in enumerate(self.myFileList):

			# check if we were cancelled
			try:
				inDict = self.inQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				# there was nothing in the queue
				pass
			else:
				if inDict == 'cancel': # cancel a sync
					if self.syncIsBusy:
						self.cancel = True
					

			# respond to cancel
			if self.cancel:
				print('commandersync.sync() is cancelling')
				self.cancel = False
				break
			
			#print(file)
			ip = file['ip']
			hostname = file['hostname']
			remotePath = file['remotePath']
			remoteFile = file['remoteFile']
			# todo: use this
			localExists = file['localExists']
			
			localFolder = os.path.join(self.localFolder, hostname, remotePath)

			#
			# check if local file already exists
			# todo: use localExists
			fullLocalPath = os.path.join(localFolder, remoteFile)
			if os.path.isfile(fullLocalPath):
				#print('local already exists:', fullLocalPath)
				continue
		
			# make local directory for all files (e.g. 'video')
			if not os.path.isdir(self.localFolder):
				os.mkdir(self.localFolder) # will make in same dir as *this file

			# make local directory for 'hostname'
			hostNameFolder = os.path.join(self.localFolder, hostname)
			if not os.path.isdir(hostNameFolder):
				os.mkdir(hostNameFolder) # will make in same dir as *this file

			#
			# make local directory (usually date folder 'yyyymmdd')
			if not os.path.isdir(localFolder):
				os.mkdir(localFolder) # assumes we are only going one dir deep, e.g. /home/pi/video/20181220

			# all our remote files are always in /home/pi/video
			# todo: fix this
			fullRemoteFile = os.path.join(self.remoteFolder, remotePath, remoteFile)
	
			#
			# todo: get this into a thread
			#
			print('copying file', numCopied+1, 'of', self.numFilesToCopy, 'idx:', idx, 'of', len(self.myFileList))
			self.copyThread(idx, ip, hostname, fullRemoteFile, fullLocalPath)

			numCopied += 1
		
		stopTime = time.time()
		elapsedSeconds = round(stopTime - startTime,2)
		print('finished, copied', numCopied, 'files in', elapsedSeconds, 'seconds, ', round(elapsedSeconds/60,2), 'minutes')
		
		self.syncIsBusy = False
		
if __name__ == '__main__':
	inQueue = queue.Queue()
	cs = CommanderSync(inQueue)
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
		