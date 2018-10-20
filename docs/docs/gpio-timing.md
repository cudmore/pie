The Raspberry Pi is running a fully functional operating system which provides many features including USB, ethernet, and HDMI. Thus, there will be unpredictable delays in receiving and generating general purpose input and output (GPIO). 

The PiE server uses the Raspberry [GPIO][gpio] python package by default and will use the [pigpio daemon][pigpiod] if it is installed and running. The GPIO package has a jitter of approximately +/- 2 ms for all DIO with occasional, < 1%, events having absurd jitter on the order of 100-200 ms. This includes trigger in, frame in, and any output. If you are using the PiE server to record video this should be fine. If you want more precision, either offload your timing critical tasks on a Teensy or use the Raspberry [pigpiod][pigpiod] daemon.

See the Jupyter notebooks in the [pie/analysis/][analysis-folder] folder for a comparising of frame arrival times using GPIO versus pigpio.

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

[gpio]: https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/
[pigpiod]: http://abyz.me.uk/rpi/pigpio/pigpiod.html
[analysis-folder]: https://github.com/cudmore/pie/tree/master/analysis