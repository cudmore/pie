#!/usr/bin/python3

"""
Author: Robert Cudmore
Date: 20181013
Purpose: Send an email with IP and MAC address of a Raspberry Pi
Usage:
	python3 startupmailer.py 'this is my message'
"""

import subprocess
import smtplib
import socket
import os
from email.mime.text import MIMEText
import datetime
import sys
from time import strftime
import platform # to get host name
from uuid import getnode as get_mac
from datetime import datetime

message = ''
if len( sys.argv ) > 1:
    message = sys.argv[1]

from my_config import gmail_user
from my_config import gmail_password
from my_config import gmail_to

smtpserver = smtplib.SMTP('smtp.gmail.com', 587)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.ehlo
smtpserver.login(gmail_user, gmail_password)

ip = subprocess.check_output(['hostname', '--all-ip-addresses'])
ip = ip.decode('utf-8').strip()

hostname = platform.node()

mac = get_mac()
mac = hex(mac)

now = datetime.now()
thedate = now.strftime('%Y%m%d')
thetime = now.strftime('%H:%M:%S')

mail_body = ''
mail_body += 'date: ' + thedate + '\n'
mail_body += 'time: ' + thetime + '\n'
mail_body += 'hostname: ' + hostname + '\n'
mail_body += 'ip: %s\n' % ip
mail_body += 'mac: ' + mac + '\n'
mail_body += 'message: ' + message + '\n'

timeStr = strftime('%b %d %Y, %H:%M:%S')

mail_subject = hostname + ' pi@' + ip + ' on %s' % timeStr

msg = MIMEText(mail_body)
msg['Subject'] = mail_subject
msg['From'] = gmail_user
smtpserver.sendmail(gmail_user, gmail_to, msg.as_string())
smtpserver.quit()

print('sent email:')
print('   gmail_user:', gmail_user)
print('   gmail_to:', gmail_to)
print('   contents:', msg.as_string())

