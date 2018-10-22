## Release Notes

### Current To Do

 - Make sure streaming stops when browser tab is closed or browser is quit.
 - Expand sunrise/sunset to fractional hour.
 - [partially done 20180831] Add warning when video/ drive space remaining is less than 1 GB. Do this by updating status.trial.systemInfo.gbRemaining at the end of each recording (record video thread, and armed recording thread). I am doing this with hard-coded 5GB warning in index.html, see: ng-if="videoArray[$index].status.trial.systemInfo.gbRemaining < 5"
 - Have some mechanism to roll-over or otherwise replace the continuous environment log file.
 - [done 20181018] Add code to check the camera as PiE server starts. This way, user can look at logs to troubleshoot.
 - Add popup to web interface for selecting supported DHT (AM2302, DHT11) sensors
 
### Major Changes

20181013

 - Moved environment logs to /home/pie/video/logs. This way they can be browsed and will not be trashed on full reinstall
 
20180801

 - Lots of changes
 
20180722

 - Lots of changes
 
## Development Notes

### 20180710

(1) motor interface

- make setup not engage motor

- add motor on, motor off to web interface
   pass to teensy with serial useMotor/motorOn, see trial.useMotor

```
//When set LOW, all STEP commands are ignored and all FET functionality is turned off. Must be pulled HIGH to enable STEP control
const int motorResetPin = 19;

//Logic Input. Enables the FET functionality within the motor driver. If set to HIGH, the FETs will be disabled, and the IC will not drive the motor. If set to LOW, all FETs will be enabled, allowing motor control.
const int motorEnabledPin = 20; //low to engage, high to dis-engage
```

(2) [done]finish writing docs for 'scope' configuration.

(3) [done] make sure all config files still load

(4) [done] add 'last response' to interface
   - update self.lastResponse throughout code

(6) look at starting ./pie at boot, make sure it catches the serial


### Reduce png file size

see:

https://www.cyberciti.biz/faq/linux-unix-optimize-lossless-png-images-with-optipng-command/

sudo apt-get install optipng

### Remember

Pins GPIO2 and GPIO3 have fixed pull-up resistors, but for other pins this can be configured in software.

### Gunicorn

```
source env/bin/activate
cd ~/pie/pie_app
/home/pi/pie/env/bin/gunicorn -w 1 --bind 192.168.1.15:5010 treadmill_app:app
```

### MkDocs

Had to install with

	sudo pip install mkdocs
	
Run on an external port

	cd ~/pie/docs
	mkdocs serve -a 192.168.1.4:8000

Push to github

	cd ~/pie/docs
	mkdocs gh-deploy
