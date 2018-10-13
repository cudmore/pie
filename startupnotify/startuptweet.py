#!/usr/bin/python3

"""
Author: Robert Cudmore
Date: 20181013
Purpose: Send a Tweet with IP and MAC address of a Raspberry Pi
Install:
	pip3 install tweepy
Usage:
	python3 startuptweet.py 'this is my tweet'
"""

import tweepy
import sys
import socket
import subprocess
from uuid import getnode as get_mac
from datetime import datetime

# Create variables for each key, secret, token
from my_config import hash_tag
from my_config import consumer_key
from my_config import consumer_secret
from my_config import access_token
from my_config import access_token_secret

message = ''
if len( sys.argv ) > 1:
    message = sys.argv[1]


# Set up OAuth and integrate with API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#

thetime = datetime.now().strftime('%Y%m%d %H:%M:%S')

ip = subprocess.check_output(['hostname', '--all-ip-addresses'])
ip = ip.decode('utf-8').strip()

hostname = socket.gethostname()

mac = get_mac()
mac = hex(mac)

tweet = thetime + ' ' + hostname + ' ' + ip + ' ' + mac + ' ' + message + ' ' + hash_tag
print('tweeting:', tweet)
api.update_status(status=tweet)
