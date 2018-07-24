# Robert H Cudmore
# 20180525

from __future__ import print_function	# (at top of module)

import os, subprocess
import platform, socket
from collections import OrderedDict
from datetime import datetime, timedelta

def getSystemInfo(path='/home/pi/video'):
	ret = OrderedDict()
	
	now = datetime.now()
	ret['date'] = now.strftime('%Y-%m-%d')
	ret['time'] = now.strftime('%H:%M:%S')

	ret['ip'] = whatismyip_safe()
	ret['hostname'] = hostname()
	
	ret['cpuTemperature'] = cpuTemperature()
	
	ret['gbRemaining'], ret['gbSize'] = drivespaceremaining(path)
	
	ret['raspberryModel'] = raspberrymodel()
	ret['debianVersion'] = debianversion()
	ret['pythonVersion'] = pythonversion()
	ret['systemUptime'] = systemUptime()
	
	return ret
	
def whatismyip():
	ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

def whatismyip_safe():
	'''
	Goal here was to get ip address at boot using 'systemctl enable homecage.service'
	This does not work? I make sure I call getSystemInfo() when loading homepage '/'
	'''
	arg='hostname -I'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	ip = data[0].decode('utf-8').strip()
	return ip
	
def hostname():
	return socket.gethostname()
	
def cpuTemperature():
	#cpu temperature
	res = os.popen('vcgencmd measure_temp').readline()
	cpuTemperature = res.replace("temp=","").replace("'C\n","")
	return cpuTemperature
	
def drivespaceremaining(path):
	#see: http://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python
	if os.path.exists(path):
		statvfs = os.statvfs(path)
	
		#http://www.stealthcopter.com/blog/2009/09/python-diskspace/
		capacity = statvfs.f_bsize * statvfs.f_blocks
		available = statvfs.f_bsize * statvfs.f_bavail
		used = statvfs.f_bsize * (statvfs.f_blocks - statvfs.f_bavail) 
		#print 'drivespaceremaining()', used/1.073741824e9, available/1.073741824e9, capacity/1.073741824e9
		gbRemaining = available/1.073741824e9
		gbSize = capacity/1.073741824e9
	
		#round to 2 decimal places
		gbRemaining = "{0:.2f}".format(gbRemaining)
		gbSize = "{0:.2f}".format(gbSize)
	else:
		gbRemaining = 'n/a'
		gbSize = 'n/a'
	return gbRemaining, gbSize
	
def raspberrymodel():
	# get the raspberry pi version, we can run on version 2/3, on model B streaming does not work
	cmd = 'cat /proc/device-tree/model'
	child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	out, err = child.communicate() # out is something like 'Raspberry Pi 2 Model B Rev 1.1'
	out = out.decode('utf-8')
	return out

def debianversion():
	# get the version of Raspian, we want to be running on Jessie or Stretch
	dist = platform.dist() # 8 is jessie, 9 is stretch
	ret = ''
	if len(dist)==3:
		ret = dist[0] + ' ' + dist[1]
		'''
		if float(dist[1]) >= 8:
			#logger.info('Running on Jessie, Stretch or newer')
		else:
			#logger.warning('Not designed to work on Raspbian before Jessie')
		'''
	else:
		pass
	return ret
	
def pythonversion():
	return platform.python_version()
	
def systemUptime():
	uptime_string = ''
	with open('/proc/uptime', 'r') as f:
	    uptime_seconds = float(f.readline().split('.')[0])
	    uptime_string = str(timedelta(seconds = uptime_seconds))
	return uptime_string
		