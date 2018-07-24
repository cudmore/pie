#!/bin/bash

# Robert Cudmore
# 20180708
#

ip=`hostname -I | xargs`
timestamp="[$HOSTNAME] "$(date '+%Y-%m-%d %H:%M:%S')" : "


systemctl is-active --quiet treadmill.service
if [ $? -eq 0 ]
then
	# is running
	echo "$timestamp Restarting PiE server http://$ip:5010"
	sudo systemctl restart treadmill.service

	# check if running
	systemctl is-active --quiet treadmill.service
	if [ $? -eq 0 ]
	then
		# is running
		echo "$timestamp PiE server is running at http://$ip:5010"
	else
		# is not running
		echo "$timestamp ERROR failed to start Pie server"
	fi
else
	# is not running
	echo "$timestamp pie server service is not running"
fi

exit 0