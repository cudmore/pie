import version

def getVersion():
	
	import sys, subprocess

	import platform
	print('=== linux:\n    ', platform.linux_distribution())
	
	cmd = ['uname', '-a']
	out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	print('    ', out.decode('utf-8').strip())

	print('=== python:', sys.version.split('\n')[0], sys.version.split('\n')[1])

	print('=== PiE:', __version__)

	#import picamera
	from pkg_resources import require
	print('=== picamera:', require('picamera'))
	
	import RPi.GPIO as GPIO  
	print('=== RPi.GPIO:', GPIO.VERSION)
	
	"""
	import pigpio
	print('=== pigpio:\n    ', pigpio.get_pigpio_version())
	"""
	
	import serial
	print('=== serial:', serial.VERSION)

	import flask
	print('=== flask:', flask.__version__)

	import flask_cors
	print('=== flask_cors:', flask_cors.__version__)
	
	import flask_socketio
	print('=== flask_socketio:', flask_socketio.__version__)

	cmd = ['avconv', '-version']
	process = subprocess.Popen(cmd,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT)
	#returncode = process.wait()
	#print('avconv returned {0}'.format(returncode))
	print('=== avconv:\n', process.stdout.read().decode('utf-8'))
	
	cmd = ['uv4l', '-i']
	out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	print('=== uv4l\n', out.decode('utf-8'))
	
if __name__ == '__main__':
	getVersion()