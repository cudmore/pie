#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603

# asssuming $homecage_path has been set-up in install-homecage.sh

myip=`hostname -I | xargs`

echo "Starting PiE server in $homecage_path"

cd $treadmill_path

# activate python pie_env if it exists
if [ ! -f ../pie_env/bin/activate ]; then
	echo "Did not find python environment pie_env/bin/activate"
else
	echo "Activating Python environment with 'source pie_env/bin/activate'"
	source ../pie_env/bin/activate
fi

echo "Calling 'python treadmill_app.py'"
python treadmill_app.py 

echo "Browse to the server at http://"$myip":5010"

exit 0