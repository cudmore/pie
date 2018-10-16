General low level testing of PiE server components. Each of these is designed to run indepent of the PiE server. If you cannot get a component to work here, it generally will not work in the PiE server.

## Camera

	raspistill -o test.jpg

After about 5 seconds, you should have a still image from the camera in `test.jpg`
	
## DHT Temperature/Humidity sensor

The `test_dht.py` file assumes you are using an AM2302 sensor connected to GPIO 4. If this is not the case, then edit the `test_dht.py` file.

```
cd ~/pie/testing
source ../pie_env/bin/activate # activate the virtual environment used by the PiE server
python test_dht.py
```
The test should return a temperature reading like:

```
Trying to read temp/hum, this may take up to 30 seconds ...
sensor: 22
pin: 4
Temp=20.9*C  Humidity=43.0%
```

If you get an error like the following then keep troubleshooting

```
Trying to read temp/hum, this may take up to 30 seconds ...
sensor: 22
pin: 4
Failed to get reading. Try again!
```

Check that the Adafruit DHT driver is installed by listing all the Python packages with `pip freeze`.

```
cd ~/pie/testing
source ../pie_env/bin/activate # activate the virtual environment used by the PiE server
pip freeze
```

`pip freeze` should output a list of installed Python packages. In this list, you should see

```
Adafruit-DHT==1.3.4
```

If you do not, then install the DHT driver again

```
cd ~/pie
./install-dht
```
