
i am now getting this error

[2018-12-19 09:35:09,744] {bPins.py configPin:228} ERROR - eventIn add_event_detect: Failed to add edge detection, name:triggerIn pin:24 polarity:31 bouncetime:20


see

https://www.raspberrypi.org/forums/viewtopic.php?t=205327

fuck this is error n newest RPi GPIO, see

https://github.com/RPi-Distro/python-gpiozero/issues/687

fix by downgrading

source pie_env/bin/activate
sudo pip install RPi.GPIO==0.6.3


