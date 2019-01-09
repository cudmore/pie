# Author: Robert H Cudmore
# Date: 20190107
#
# increment version numbers in version.py

import time #json, subprocess

import version

if __name__ == '__main__':
	
	# increment to current date
	now = time.time()
	newVersion = time.strftime('%Y%m%d', time.localtime(now))
	# increment minor version
	newVersionMinor = version.__version_minor__ + 1
	
	# resave version.py
	with open('version.py', 'w') as outfile:
		outfile.write('__version__ = ' + newVersion + '\n')
		outfile.write('__version_minor__ = ' + str(newVersionMinor) + '\n')
	
	# leave this here, used to grab output in bash
	print(newVersion, newVersionMinor)