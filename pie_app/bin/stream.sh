#!/bin/bash

function usage(){
    echo "stream - Illegal parameters"
    echo "Usage:"
    echo "   stream start"
    echo "   stream start width height"
    echo "   stream stop"
}

function streamStart(){
	videoPID=`pgrep -f video.py`
	if [ -n "$videoPID" ]; then
		echo "video is recording, use 'record stop' to stop."
		exit 1
	fi

	uv4lPID=`pgrep -f uv4l`
	if [ -n "$uv4lPID" ]; then
		echo "stream is already running, use 'stream stop' to stop."
		exit 1
	fi

	# check that uv4l is available
	type uv4l >/dev/null 2>&1 || { >&2 echo "uv4l not installed"; exit 1; }

	uv4l --driver raspicam --auto-video_nr --encoding h264 --width $streamWidth --height $streamHeight --enable-server on
	#uv4l --verbosity=-1 --driver raspicam --auto-video_nr --encoding h264 --width 1280 --height 720 --enable-server on
	
	ip=`ifconfig eth0 | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'`
	
	echo View the stream at:
	echo "   "http://$ip:8080/stream

}

function streamStop(){
	# check that uv4l is available
	type uv4l >/dev/null 2>&1 || { >&2 echo "uv4l not installed"; exit 1; }

	uv4lPID=`pgrep -f uv4l`
	if [ -n "$uv4lPID" ]; then
		echo "stopping video stream ..."
		sudo kill -- -$uv4lPID
		#sudo service uv4l_raspicam stop
		#sudo pkill uv4l
		echo "done"
	else
		echo "video stream is not running, use 'stream start' to start."
		exit 1
	fi
}

if (( $# != 1 || $# != 3)); then
	echo
else
    usage
    exit 1
fi

if [ "$#" -ne 3 ]; then
	streamWidth=640
	streamHeight=480
else
	streamWidth=$2
	streamHeight=$3
fi


case "$1" in
	start) streamStart
		;;
	stop) streamStop
		;;
	*) usage
		;;
esac

exit 0

