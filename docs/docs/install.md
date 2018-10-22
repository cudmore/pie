# Install the PiE server

## 1) Get a functioning Raspberry Pi

We assume you have a functioning Raspberry Pi 2/3. To get started, see our [installation][install-stretch] recipe.

## 2) Download the code

```bash
# update your system
sudo apt-get update
sudo apt-get upgrade

# if you don't already have git
sudo apt-get install git

# clone the main PiE repository
cd
git clone https://github.com/cudmore/pie.git
```

## 3) Install the PiE server

```bash
cd ~/pie
./install-pie
```

Thats it, the PiE server should be running and you can use the [web interface](web-interface.md) at `http://[ip]:5010`. Where `[ip]` is the IP address of your Raspberry Pi. Make sure you specify port `5010` in the web address. By default, the PiE server will start when the Raspberry Pi is booted.

## 4) Install [uv4l][uv4l] for video streaming.

The [uv4l][uv4l] software runs at the system level (not within the PiE folder) and only needs to be installed once per machine.

```bash
cd ~/pie
./install-uv4l
```

## 5) Install the DHT temperature/humidity sensor Python package (optional)

If you are using a [DHT temperature/humidity sensor][am2302], the [Adafruit DHT python package][dht] needs to be installed.

```bash
cd ~/pie
./install-dht
```

## 6) Checking the status of the PiE server.

If all goes well, the [web interface](web-interface.md) is all this is needed. If the PiE server does not work as expected, it is useful to check its log file. Do this from the [web interface](web-interface.md) or from the command line with:

```bash
more ~/pie/pie_app/pie.log
```

## 7) Controlling the PiE server from the command line

The [pie/install-pie](install-pie) script installs a system service allowing the PiE server to run in the background. This background PiE server can be controlled as follows:

```bash
cd ~/pie
	
./pie start    - start background PiE server"
./pie stop     - stop background PiE server"
./pie status   - check the status of background PiE server"

./pie enable   - enable background PiE server at boot"
./pie disable  - disable background PiE server at boot"

./pie run      - run PiE server on command line"
```

For debugging, use `./pie run` to print the PiE server log to the command line. The logs can also be viewed from the [web interface](web-interface.md) or the command line using `more ~/pie/pie_app/pie.log`.

## Running the PiE server at boot

By default, the PiE server will run when the Raspberry Pi is booted and this can be controlled as follows.

```
# To make the background server run at boot
cd ~/pie
./pie enable

# To make the background server NOT run at boot
cd ~/pie
./pie disable
```

## Manually running the PiE server

Normally, the PiE server will run in the background after installation with './install-pie'. If there are errors during the install or the PiE server is not running, the pie server can be run manually as follows.

```
# stop background pie server
cd ~/pie
./pie stop

# activate the pie server python virtual environment in pie_env/
# Once activated, the command prompt will start with (pie_env)
cd ~/pie
source pie_env/bin/activate

# manually run the pie server
cd ~/pie/pie_app
python treadmill_app.py

# don't forget to deactivate the python virtual environment with
deactivate
```

## Uninstalling the PiE server

Run the uninstall script `./uninstall-pie` and remove the ~/pie folder with `sudo -Rf ~/pie`.

```
# run the uninstall script
cd ~/pie
./uninstall-pie

# remove the pie folder
sudo -Rf ~/pie
```

## Full reinstall of the PiE server

Issue these commands to remove and reinstall the PiE server.

```
# stop the PiE server
cd ~/pie
./pie stop

# remove existing ~/pie folder
cd
sudo rm -Rf ~/pie

# download/clone a new copy of pie folder
cd 
git clone https://github.com/cudmore/pie.git

# install PiE server
cd ~/pie
./install-pie

# install dht sensor (optional)
cd ~/pie
./install-dht
```

[install-stretch]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[dht]: https://github.com/adafruit/DHT-sensor-library
[am2302]: https://www.adafruit.com/product/393
[uv4l]: https://www.linux-projects.org/uv4l/
[systemd]: https://www.freedesktop.org/wiki/Software/systemd/