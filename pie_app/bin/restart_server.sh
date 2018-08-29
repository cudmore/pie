#!/bin/bash

# Robert Cudmore
# 20180708
#

ip=`hostname -I | xargs`
timestamp="[$HOSTNAME] "$(date '+%Y-%m-%d %H:%M:%S')" : "

echo "$timestamp restart_server.sh pwd: $PWD"

# shutdown streaming
function streamStop(){
	# check that uv4l is available
	type uv4l >/dev/null 2>&1 || { >&2 echo "uv4l not installed"; }

	uv4lPID=`pgrep -f uv4l`
	if [ -n "$uv4lPID" ]; then
		echo "$timestamp Stopping video stream ..."
		sudo kill -- -$uv4lPID
		#sudo service uv4l_raspicam stop
		#sudo pkill uv4l
		echo "$timestamp killed stream with 'kill --'"
	else
		echo "$timestamp Video stream is not running, use 'stream start' to start."
		#exit 1
	fi
}

streamStop

systemctl is-active --quiet treadmill.service
if [ $? -eq 0 ]
then
	# is running
	echo "$timestamp Restarting PiE server http://$ip:5010 in 3 seconds"
	sleep 3
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