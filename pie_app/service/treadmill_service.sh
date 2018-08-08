#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603

# asssuming $homecage_path has been set-up in install-homecage.sh

myip=`hostname -I | xargs`

echo "Starting homecage server in $homecage_path"

cd $treadmill_path

# activate python env if it exists
if [ ! -f ../env/bin/activate ]; then
	echo "Did not find python environment env/bin/activate"
else
	echo "Activating Python environment with 'source env/bin/activate'"
	source ../env/bin/activate
fi

# python -V

echo "calling 'python treadmill_app.py'"
python treadmill_app.py 

echo "   Browse to the server at http://"$myip":5000"

exit 0