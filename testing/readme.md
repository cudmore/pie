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
 