# Raspberry Pi Controlled Experiment (PiE)

A feature rich web based experiment.

## Disclaimer

This repository is a work in progess. It is functioning in my hands and fingers but may not in yours. Please email robert.cudmore [at] gmail.com with questions or better yet, open an [issue](https://github.com/cudmore/pie/issues). If this code is used in any way, please be a good scientist/colleague and give me credit. If you see utility in this system and would like to see it customized for a particular experiment, contact me and we can collaborate.


## Features

 - Configurable web interface
 - Video recording
 - Video streaming to a browser
 - Trigger video recording with from standard lab equipment
 - Watermark video with events including frame numbers
 - Control a motorized treadmill during video recording
 - Save all experimental events into an easy to parse text file

## There are options

 1. **Video recording.** Use the PiE server to record video. All that is needed is a Raspberry Pi and a Pi camera.
 2. **Home cage video.** Use the PiE server to record video, control IR and white lights, and log the temperature.
 3. **On the scope video recording.** Use the PiE server to record video triggered from a microscope and to log a scanning microscopes frames.
 4. **Full treadmill system.** Use the PiE server to record synchronized video on a scope (option 3) while controlling a motorized treadmill.

## 1) Get a functioning Raspberry Pi

We assume you have a functioning Raspberry Pi 2/3. To get started, see our [installation][install-stretch] recipe.

## 2) Download the code

	# update your system
	sudo apt-get update
	sudo apt-get upgrade

	# if you don't already have git
	sudo apt-get install git
	
	# clone the main PiE repository
	git clone https://github.com/cudmore/pie.git
	
## 3) Install the PiE server

	cd ~/pie
	./install-pie

Thats it, the PiE server should be running and you can use the web interface at `http://[ip]:5010`. Where `[ip]` is the IP address of your Raspberry Pi. Make sure you specify port `5010` in the web address. By default, the PiE server will start when the machine is booted.

## 4) Install [uv4l][uv4l] for video streaming.

The [uv4l][uv4l] software runs at the system level (not within the PiE folder) and only needs to be installed once per machine.

	cd ~/pie
	./install-uv4l

## 5) Install the DHT temperature/humidity sensor Python package (optional)

If you are using a [DHT temperature/humidity sensor][am2302], the [Adafruit DHT python package][dht] needs to be installed.

	cd ~/pie
	./install-dht

## 6) Checking the status of the PiE server.

If all goes well, the web interface is all this is needed. If the PiE server does not work as expected, it is useful to check its log files. Do this with:

	more ~/pie/pie_app/pie.log

## 7) Controlling the PiE server from the command line

The [pie/install-pie](install-pie) script installs a system service allowing the PiE server to run in the background. This background PiE server can be controlled as follows:

```
cd ~/pie
	
./pie start    - start background PiE server"
./pie stop     - stop background PiE server"
./pie status   - check the status of background PiE server"

./pie enable   - enable background PiE server at boot"
./pie disable  - disable background PiE server at boot"

./pie run      - run PiE server on command line"
```

For debugging, use `./pie run` to print the logs of the PiE server to the command line. The logs can also be viewed from the web interface or using `more ~/pie/pie_app/pie.log`.

## Web interface

In all cases, when the PiE server is running it will provide a web interface on port `5010`. To access the website, point a browser to `http://[ip]:5010`. See the [web interface readme](readme-web.md) for more information.

<table><tr><td>
<IMG SRC="docs/img/web/web_main.png">
</td></tr></table>

### Configure

<table><tr><td>
<IMG SRC="docs/img/web/web_config.png">
</td></tr></table>

## Parts list

See the complete [parts list](readme-parts.md) for more information.


## Wiring the system

**Important**. The Raspberry Pi is **NOT** 5V tolerant. Connecting standard lab equipment using 5V TTL pulses can damage the Pi. These 5V lines can be converted to 3V with a [dedicated level shifter][adafruit-level-shfter]. Or, if you are using a Teensy, these 5V lines can pass through the Teensy which **IS** 5V tolerant but then outputs 3V which can go into the Raspberry Pi. In this way, the Teensy can act as a programmable [level shifter][level-shifter].

### Option 1: Recording video

 - All you need is a Raspberry Pi 2/3, a Raspberry camera and the PiE server and you are good to go.

### Option 2: Recording homecage video
 
 - See the [readme-homecage-wiring](readme-homecage-wiring.md) for details.
 - Wire a 2-channel relay with white and IR LEDs connected to 12V power.
 - Wire a Temperature/Humidity sensor like the [AM2302][am2302].
    
### Option 3: Record video on a scope (no Teensy)

 - See the [scope wiring tutorial](readme-scope.md).
 - Wire a level shifter connected to `Scope Trigger In`, `Scope Trigger Out`, and `Scope Frame out`.
  
### Option 4: Record video on a scope and use a Teensy and a motorized treadmill

 - See the [treadmill wiring tutorial](readme-treadmill.md).
 
## Running the PiE server (details)

### Running the PiE server at boot

The main `./install-pie` script will set the PiE server to run at boot. This can be controlled as follows.

```
# To make the background server run at boot
cd ~/pie
./pie enable

# To make the background server NOT run at boot
cd ~/pie
./pie disable
```

### Running the PiE server on the command line

The PiE server is run as a background system service following installation with `./install-pie` and can be controlled with `./pie start` and `./pie stop`. Specifically, the PiE server is using `systemctl` which is a subset of [systemd][systemd]. If the PiE server is not running correctly, it can be run directly on the command line using `./pie run`.

```
# Make sure the background PiE server is stopped
cd ~/pie
./pie stop

# Run the PiE server and output logs to the command line window
# Once running, use ctrl+c to stop the server
./pie run

# To start the background server again
./pie start
```

### Manually running the PiE server

Normally, the PiE server will run in the background after installation with '~/pie/install-pie'. If there are errors during the install or the PiE server is not running, the pie server can be run manually as follows.

```
# stop background pie server
cd ~/pie
./pie stop

# (optional) if neccessary, install virtualenv
sudo apt-get -qy install python-virtualenv

# (optional) if you do not have 'pie_env/bin/activate' then manually make the virtual environment
mkdir pie_env
virtualenv -p python3 --no-site-packages pie_env

# activate pie server virtual environment in pie_env/
# Once activated, the command prompt should start with (pie_env)
cd ~/pie
source pie_env/bin/activate

# finally, manually run the pie server
cd ~/pie/pie_app
python treadmill_app.py

```

### Uninstalling the PiE server

Run the uninstall script `./uninstall-pie` and remove the ~/pie folder with `sudo -Rf ~/pie`.

```
# run the uninstall script
cd ~/pie
./uninstall-pie

# remove the pie folder
sudo -Rf ~/pie
```

### Full reinstall of the PiE server

Issue these commands to remove and reinstall the PiE server.

```
# stop the PiE server
cd ~/pie
./pie stop

# remove existing ~/pie folder
cd
sudo rm -Rf pie

# download/clone a new copy of pie folder
cd ~
git clone https://github.com/cudmore/pie.git

# install PiE server
cd ~/pie
./install-pie

# install dht sensor (optional)
cd ~/pie
./install-dht

# restart the server again
cd ~/pie
./pie restart

```

## Troubleshooting

See the [troubleshooting](readme-troubleshooting.md) readme.

## GPIO timing

The Raspberry Pi is running a fully functional operating system which provides many features including USB, ethernet, and HDMI. Thus, there will be unpredictable delays in receiving and generating digital input and output (DIO). 

The PiE server uses the Raspberry [GPIO][gpio] python package by default and will use the [pigpio daemon][pigpiod] if it is installed and running. The GPIO package has a jitter of approximately +/- 2 ms for all DIO with occasional, < 1%, events having absurd jitter on the order of 100-200 ms. This includes trigger in, frame in, and any output. If you are using the PiE server to record video this should be fine. If you want more precision, either offload your timing critical tasks on a Teensy or use the Raspberry [pigpiod][pigpiod] daemon.

See the Jupyter notebooks in the [analysis/](analysis/) folder for a comparising of frame arrival times using GPIO versus pigpio.

### Download and install pigpio

```
cd
rm pigpio.zip
sudo rm -rf PIGPIO
wget abyz.me.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd PIGPIO
make
sudo make install
```

### To start the pigpio daemon

    sudo pigpiod

### To stop the pigpio daemon

    sudo killall pigpiod


## Manually editing user config

The PiE server comes with three default sets of options: Homecage, Scope, and Treadmill. There is an additional `User` configuration that can be edited manually to configure the PiE server.

To edit the `User` file, open [pie_app/config/config_user.json](pie_app/config/config_user.json). The format of the file is [json][json] and basically specifies key/value pairs. Do not add or remove any keys, just change their values. The json format is very strict, if there are any syntax errors, the file will not load and the PiE server will not run.

To check your work, use

```
cd ~/pie/pie_app/config
cat config_user.json | python -m json.tool
```

If your edits are syntatically correct, this command will output the contents of the file. If you have created an error, they will be reported on the command line. For example, if your forget a comma  after `"enabled": true` like this

```
        "triggerIn": {
            "enabled": true
            "pin": 23,
            "polarity": "rising",
            "pull_up_down": "down"
        },
```

You will get an error

```
Expecting , delimiter: line 27 column 13 (char 648)
```


## To Do

 - Make sure streaming stops when browser tab is closed or browser is quit.
 - Expand sunrise/sunset to fractional hour.
 - [partially done 20180831] Add warning when video/ drive space remaining is less than 1 GB. Do this by updating status.trial.systemInfo.gbRemaining at the end of each recording (record video thread, and armed recording thread). I am doing this with hard-coded 5GB warning in index.html, see: ng-if="videoArray[$index].status.trial.systemInfo.gbRemaining < 5"
 - Have some mechanism to roll-over or otherwise replace the continuous environment log file.
 - Add code to check the camera as PiE server starts. This way, user can look at logs to troubleshoot.
 
  
[install-stretch]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[steppermotor]: https://www.sparkfun.com/products/9238
[easydriver]: https://www.sparkfun.com/products/12779
[teensy]: https://www.pjrc.com/teensy/
[platformio]: https://platformio.org/
[relay]: https://en.wikipedia.org/wiki/Relay
[sainsmart-relay]: https://www.amazon.com/SainSmart-101-70-100-2-Channel-Relay-Module/dp/B0057OC6D8
[uv4l]: https://www.linux-projects.org/uv4l/
[libav]: https://libav.org/
[dht]: https://github.com/adafruit/DHT-sensor-library
[level-shifter]: https://en.wikipedia.org/wiki/Level_shifter
[fritzing]: http://fritzing.org/home/
[raspberry-pi]: https://www.raspberrypi.org/
[buy-raspberry-pi]: https://www.raspberrypi.org/products/
[buy-noir]: https://www.adafruit.com/product/3100?src=raspberrypi
[raspbian]: https://www.raspberrypi.org/downloads/raspbian/
[raspberry-pi-noir]: https://www.raspberrypi.org/products/pi-noir-camera-v2/
[raspberry-pi-camera]: https://www.raspberrypi.org/products/camera-module-v2/
[am2302]: https://www.adafruit.com/product/393
[json]: https://www.json.org/
[systemd]: https://en.wikipedia.org/wiki/Systemd
[gpio]: https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/
[pigpiod]: http://abyz.me.uk/rpi/pigpio/pigpiod.html
[pigpio]: http://abyz.me.uk/rpi/pigpio/python.html
[loginlevelconverter_sparkfun]: https://www.sparkfun.com/products/12009
[loginlevelconverter_adafruit]: https://www.adafruit.com/products/757
