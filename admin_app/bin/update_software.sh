#!/bin/bash

# Robert Cudmore
# 20180712

#update_software.sh

ip=`hostname -I | xargs`

timestamp="[$HOSTNAME] "$(date '+%Y-%m-%d %H:%M:%S')" : "

echo "$timestamp === Admin server is at http://$ip:5011"

systemctl is-active --quiet treadmill.service
if [ $? -eq 0 ]
then
	# is running
	echo ''
else
	# is not running
	echo "$timestamp Pie server systemctl is not running -->> No action taken"
	exit 0
fi

echo "$timestamp updating PiE server"

echo "$timestamp In folder: $PWD" # called from commander, we get /home/pi/pie/admin_app
cd ..

#if [[ `git status --porcelain` ]]; then
#  # Changes
#	echo "$timestamp there are changes in git repo"
#	#git fetch --all
#	#git reset --hard origin/master
#else
#  # No changes
#	echo "$timestamp git up to date"
#fi

# shutdown PiE server
echo "$timestamp stopping PiE server at http://$ip:5010"
sudo systemctl stop treadmill.service

git remote update

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    echo "$timestamp Git is up-to-date"
elif [ $LOCAL = $BASE ]; then

    echo "$timestamp Git needs to pull"
	
	if [ ! -f ./pie_app/config/config_default.json ]; then
	    #echo "File not found!"
	    echo ''
	else
		echo "$timestamp Removing saved config file, will be recreated on next server run"
		echo "$timestamp rm ./pie_app/config/config_default.json"
		rm ./pie_app/config/config_default.json
	fi
	
	##
	##
	git pull
	##
	##
	echo "$timestamp Done pulling, software should be up to date"
	
elif [ $REMOTE = $BASE ]; then
    echo "$timestamp Git needs to push"
else
    echo "$timestamp WARNING, git has diverged"
fi

version=`cat ./pie_app/version.py`
echo "$timestamp PiE server version is: $version"

# start PiE server
echo "$timestamp starting PiE server at http://$ip:5010"
sudo systemctl start treadmill.service
