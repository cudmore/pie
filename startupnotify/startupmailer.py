#!/usr/bin/python
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

'''
# list of email accounts to send to
to = ['robert.cudmore@gmail.com']

# Change to your own account information to send from
gmail_user = 'cudmore.raspberry@gmail.com'
gmail_password = 'poetry7d'
'''

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

