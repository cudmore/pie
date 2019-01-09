"""
Author: Robert H Cudmore
Date: 20181220

General purpose version check for the PiE server. If any of these fail, the PiE server will not run properly.

Usage:

	# activate virtual environment (Assuming it exists)
	source ~/pie/pie_env/bin/activate
	
	# run version check
	python ~/pie/pie_app/version_check.py
	
	# deactivate virtual environment
	deactivate
"""

import version # has __version__ and __version_minor__

def getVersion():
	
	import sys, subprocess

	import platform
	print('=== linux:\n    ', platform.linux_distribution())
	
	cmd = ['uname', '-a']
	out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	print('    ', out.decode('utf-8').strip())

	#
	# python
	print('=== python:', sys.version.split('\n')[0], sys.version.split('\n')[1])

	#
	# PiE
	print('=== PiE:', version.__version__, version.__version_minor__)

	#
	# picamera
	from pkg_resources import require, DistributionNotFound
	try:
		print('=== picamera:', require('picamera'))
	except (DistributionNotFound) as e:
		print('=== picamera: not found')

	#
	# RPi.GPIO
	try:
		import RPi.GPIO as GPIO  
		print('=== RPi.GPIO:', GPIO.VERSION)
	except (ImportError) as e:
		print('=== RPi.GPIO:', e)

	"""
	import pigpio
	print('=== pigpio:\n    ', pigpio.get_pigpio_version())
	"""
	
	#
	# serial
	try:
		import serial
		print('=== serial:', serial.VERSION)
	except (ImportError) as e:
		print('=== serial:', e)

	#
	# flask
	try:
		import flask
		print('=== flask:', flask.__version__)
	except (ImportError) as e:
		print('=== flask:', e)

	#
	# flask_cors
	try:
		import flask_cors
		print('=== flask_cors:', flask_cors.__version__)
	except (ImportError) as e:
		print('=== flask_cors:', e)
	
	#
	# flask_socketio
	try:
		import flask_socketio
		print('=== flask_socketio:', flask_socketio.__version__)
	except (ImportError) as e:
		print('=== flask_socketio:', e)

	#
	# avconv
	cmd = ['avconv', '-version']
	try:
		process = subprocess.Popen(cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT)
	except (FileNotFoundError) as e:
		print('=== avconv raised FileNotFoundError exception, avconv is not installed? exception:', e)
	else:
		#returncode = process.wait()
		#print('avconv returned {0}'.format(returncode))
		print('=== avconv:\n', process.stdout.read().decode('utf-8'))
	
	#
	# uv4l
	cmd = ['uv4l', '-i']
	try:
		out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	except (FileNotFoundError) as e:
		print('=== uv4l raised FileNotFoundError exception, uv4l is not installed? exception:', e)
	else:
		print('=== uv4l\n', out.decode('utf-8'))
	
if __name__ == '__main__':
	getVersion()