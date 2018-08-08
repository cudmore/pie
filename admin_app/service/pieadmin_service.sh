#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603

# asssuming $pieadmin_path has been set-up in pieadmin.service

myip=`hostname -I | xargs`

echo "Starting PieAdmin server in $pieadmin_path"

cd $pieadmin_path

# activate python env if it exists
if [ ! -f ../env/bin/activate ]; then
	echo "Did not find python environment env/bin/activate"
else
	echo "Activating Python environment with 'source env/bin/activate'"
	source ../env/bin/activate
fi

# python -V

echo "calling 'python admin.py'"
python admin.py 

echo "   Browse to the server at http://"$myip":5011"

exit 0