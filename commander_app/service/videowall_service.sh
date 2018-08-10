#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603

# asssuming $videowall_path has been set-up in install-commander.sh

myip=`hostname -I | xargs`

echo "Starting videowall server in $videowall_path"

cd $videowall_path

# activate python env if it exists
if [ ! -f commander_env/bin/activate ]; then
	echo "Did not find python environment commander_env/bin/activate"
else
	echo "Activating Python environment with 'source commander_env/bin/activate'"
	source commander_env/bin/activate
fi

echo "calling 'python commander.py'"
#python homecage_app.py $1 > homecage_app.log 2>&1
python commander.py 

echo "   Browse the server at http://"$myip":8000"

exit 0