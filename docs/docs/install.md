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
git clone https://github.com/cudmore/pie.git
```

## 3) Install the PiE server

```bash
cd ~/pie
./install-pie
```

Thats it, the PiE server should be running and you can use the [web interface](web-interface.md) at `http://[ip]:5010`. Where `[ip]` is the IP address of your Raspberry Pi. Make sure you specify port `5010` in the web address. By default, the PiE server will start when the machine is booted.

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

If all goes well, the [web interface](web-interface.md) is all this is needed. If the PiE server does not work as expected, it is useful to check its log files. Do this with:

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

For debugging, use `./pie run` to print the logs of the PiE server to the command line. The logs can also be viewed from the [web interface](web-interface.md) or the command line using `more ~/pie/pie_app/pie.log`.

[install-stretch]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[dht]: https://github.com/adafruit/DHT-sensor-library
[am2302]: https://www.adafruit.com/product/393
[uv4l]: https://www.linux-projects.org/uv4l/
