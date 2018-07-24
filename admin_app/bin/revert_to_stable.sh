#!/bin/bash

# Robert Cudmore
# 20180712

#revert_to_stable.sh

ip=`hostname -I | xargs`

timestamp="[$HOSTNAME] "$(date '+%Y-%m-%d %H:%M:%S')" : "

echo "$timestamp === Admin server is at http://$ip:5011"

echo "$timestamp === Reverting PiE software to stable"

echo "$timestamp === Revert is not implemented"

