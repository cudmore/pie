## Platformio

This folder contains code to be uploaded to a teensy/arduino microcontroller. To do this from the command line on a Raspberry Pi, we will use [platformio][platformio].

The code relies on two teensy/arduino libraries

 - [AccelStepper library](https://www.pjrc.com/teensy/td_libs_AccelStepper.html)
 - [Encoder library](https://www.pjrc.com/teensy/td_libs_Encoder.html)
 
See [this][blog1] blog post for getting started. Also, see a recent bug report and the fix in the [teensy forum][teensy-forum] and the [platformio forum][platformio-forum]. As always with open source, it is not good because it is free, it is good because it improves with user feedback. Please contribute.


## Teensy microcontrollers

Teensy microcontrollers are Arduino compatible but generally have many more features and power (ram, low level interrupts, DIO pins, etc). See the [Teensy comparison chart](https://www.pjrc.com/teensy/techspecs.html), the best option is Teensy 3.2 or 3.5. If you are connecting to a scope or other equipment with 5V triggers (TTL), Teensy 3.2 and 3.5 are ideal as their input is 5V tolerant but they always output 3V which can be connected directly to a Raspberry Pi.


## Configure the Raspberry Pi to use serial ports

### 1) Activating serial ports

The serial ports on the Raspberry Pi need to be activated. Run the raspberry pi configuration utility

	sudo raspi-config

And select the following

	5 Interfacing Options - Configure connections to peripherals 

	P6 Serial - Enable/Disable shell and kernel messages on the serial connection  
	
	Would you like a login shell to be accessible over serial? -->> No

	Would you like the serial port hardware to be enabled?   -->> Yes


### 2) Add user pi to dialout group

This is handled by `install-platformio`.

	sudo usermod -a -G dialout pi

### 3) Create a `/etc/udev/rules.d/49-teensy.rules` file

This is handled by `install-platformio`.

The Raspberry Pi needs this file to communicate with serial ports on usb. Either download [49-teensy.rules](https://www.pjrc.com/teensy/49-teensy.rules) or see the end of this page for a copy of its contents.

```
# edit the file
sudo pico /etc/udev/rules.d/49-teensy.rules

# manually copy and paste the contents (see contents below)
# ctrl+x to exit pico

# reboot the raspberry pi
sudo reboot
```

## Install platformio (using our script)

	cd ~/pie/platformio
	./install-platformio
	
## Upload treadmill/src/treadmill2.cpp to a teensy

IMPORTANT: The PiE server can not be running while uploading code, stop the server with `~/pie/pie stop` or if running on command line use `ctrl+c`.

Upload with provided `upload` script

	# upload treadmill/src/treadmill2.cpp to a teensy 3.1/3.2
	cd ~/pie/platformio/
	./upload teensy31
	
	# upload treadmill/src/treadmill2.cpp to a teensy 3.5
	cd ~/pie/platformio/
	./upload teensy35

Upload manually

	cd ~/pie/platformio/treadmill
	
	# upload treadmill.cpp to a teensy 3.1/3.2
	sudo ../env/bin/platformio run -e teensy31 --target upload
	
	# upload treadmill.cpp to a teensy 3.5
	sudo ../env/bin/platformio run -e teensy35 --target upload
	
After a lot of output, you should see something like

```
AVAILABLE: jlink, teensy-cli, teensy-gui
CURRENT: upload_protocol = teensy-cli
Rebooting...
Uploading .pioenvs/teensy31/firmware.hex
Teensy Loader, Command Line, Version 2.1
Read ".pioenvs/teensy31/firmware.hex": 30332 bytes, 11.6% usage
Soft reboot performed
Waiting for Teensy device...
(hint: press the reset button)
Found HalfKay Bootloader
Read ".pioenvs/teensy31/firmware.hex": 30332 bytes, 11.6% usage
Programming..............................
Booting
======================================== [SUCCESS] Took 19.42 seconds ========================================
```

# Troubleshooting

## Uploading to Teensy says '(hint: press the reset button)'

```
Error opening USB device: No error
Waiting for Teensy device...
(hint: press the reset button)
```

You might see this error on the first upload to a Teensy. Guess what, push the reset button.

## Check that platformio.ini specifies your particular board

```
more ~/pie/platformio/treadmill/platform.ini
```

```
[env:teensy31]
platform = teensy
board = teensy31
framework = arduino

[env:teensy35]
platform = teensy
board = teensy35
framework = arduino
```

If you don't see your board, get a full list of supported boards with

```
cd ~/pie/platformio
env/bin/platformio boards atmelavr
```

Go through that list and find your board

```
Platform: atmelavr
----------------------------------------------------------------------------------------------------------------------------------------
ID                    MCU            Frequency  Flash   RAM    Name
----------------------------------------------------------------------------------------------------------------------------------------
uno                   ATMEGA328P     16MHz     31.50KB 2KB    Arduino Uno
megaatmega1280        ATMEGA1280     16MHz     124KB   8KB    Arduino Mega or Mega 2560 ATmega1280
```

As an example, add an Arduino Uno platformio.ini with

```
cd ~/pie/platformio/treadmill
../env/bin/platformio init --board=uno
```

## Check which serial ports platformio is using

```
cd ~/pie/platformio/
env/bin/platformio device list
```

```
/dev/ttyACM0
------------
Hardware ID: USB VID:PID=16C0:0483 SER=1756190 LOCATION=1-1.1.2:1.0
Description: USB Serial

/dev/ttyAMA0
------------
Hardware ID: 3f201000.serial
Description: ttyAMA0
```

If you don't see `/dev/ttyACM0` in the output you will have to configure [config_factory_defaults.json](../pie_app/config_factory_defaults.json) to include your serial in the 'serial' section:

```
"serial": {
	"useSerial": true,
	"port": "/dev/ttyACM0",
	"baud": 115200
}
```


## The PiE server cannot communicate with the serial after uploading code to the Teensy.

When code is uploaded to the Teensy, the PiE server can **not** be running.

Check your serial ports with

```
ls -al /dev/ttyA*
```

Should yield

```
crw-rw-rw- 1 root dialout 166,  0 Jul  2 20:11 /dev/ttyACM0
```

If you end up with a `/dev/ttyACM1` then stop the PiE server and upload again.

```
# Stop the server
cd ~/pie
./pie stop

# upload again
cd ~/pie/platformio/treadmill
sudo ../env/bin/platformio run -e teensy31 --target upload
```

## I get errors in the Encoder library while uploading code

Sometimes updating to the most recent version of the Encoder library fixes this. The library can be found in the [Encoder](https://github.com/PaulStoffregen/Encoder) GitHub repository. 

```
cd ~/pie/platformio/treadmill/lib/Encoder
git pull
```

Then, try and uploading the code again.

## Make a simple project to debug uploading to teensy

If nothing is working. Make your own dead-simple project for debugging.

```
cd ~/pie/platformio/
mkdir blink
cd blink

#Initialize blink project with teensy 3.1/3.2 boards
# this will create file platformio.ini and 
# folders /src and /lib
../env/bin/platformio init --board=teensy31

# or initialize with an uno
../env/bin/platformio init --board=uno
```
	
Copy the following into blink/src/main.cpp

	pico src/main.cpp

```
/*
 * Blink
 * Turns on an LED on for one second,
 * then off for one second, repeatedly.
 */
#include "Arduino.h"

void setup()
{
  // initialize LED digital pin as an output.
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop()
{
  int myDelay = 1000;

  // turn the LED on
  digitalWrite(LED_BUILTIN, HIGH);
  delay(myDelay);

  // turn the LED off
  digitalWrite(LED_BUILTIN, LOW);
  delay(myDelay);
}
```

Upload the blink project to teensy. In the following we assume you are using a Teensy 3.1/3.2. If you want to use a Teensy 3.5, then replace `-e teensy31` with `-e teensy35` or for an Uno use `-e uno`.

```
sudo ../env/bin/platformio run -e teensy31 --target upload

# if running into problems, try to clean and then upload again
sudo ../env/bin/platformio run -e teensy31 --target clean
```

## To sudo or not

To upload to teensy you should use sudo. To create a new project you should not.

## Monitor the serial connection on the command line

```
# install screen
sudo apt-get install screen

#Use screen to connect to serial port
screen /dev/ttyACM0 115200
```

You might have to hit `return` to get it going. Exit screen with `ctrl+a` then type `:` then type `quit`

## udev rules

Here is the contents of [49-teensy.rules](https://www.pjrc.com/teensy/49-teensy.rules). This needs to be copied and pasted into `/etc/udev/rules.d/49-teensy.rules`.

Edit `/etc/udev/rules.d/49-teensy.rules`

	sudo pico /etc/udev/rules.d/49-teensy.rules
	
And paste these contents. Exit the pico editor with ctrl+x

```
# UDEV Rules for Teensy boards, http://www.pjrc.com/teensy/
#
# The latest version of this file may be found at:
#   http://www.pjrc.com/teensy/49-teensy.rules
#
# This file must be placed at:
#
# /etc/udev/rules.d/49-teensy.rules    (preferred location)
#   or
# /lib/udev/rules.d/49-teensy.rules    (req'd on some broken systems)
#
# To install, type this command in a terminal:
#   sudo cp 49-teensy.rules /etc/udev/rules.d/49-teensy.rules
#
# Or use the alternate way (from this forum message) to download and install:
#   https://forum.pjrc.com/threads/45595?p=150445&viewfull=1#post150445
#
# After this file is installed, physically unplug and reconnect Teensy.
#
ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789B]?", ENV{ID_MM_DEVICE_IGNORE}="1"
ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789A]?", ENV{MTP_NO_PROBE}="1"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789ABCD]?", MODE:="0666"
KERNEL=="ttyACM*", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789B]?", MODE:="0666"
#
# If you share your linux system with other users, or just don't like the
# idea of write permission for everybody, you can replace MODE:="0666" with
# OWNER:="yourusername" to create the device owned by you, or with
# GROUP:="somegroupname" and mange access using standard unix groups.
#
#
# If using USB Serial you get a new device each time (Ubuntu 9.10)
# eg: /dev/ttyACM0, ttyACM1, ttyACM2, ttyACM3, ttyACM4, etc
#    apt-get remove --purge modemmanager     (reboot may be necessary)
#
# Older modem proding (eg, Ubuntu 9.04) caused very slow serial device detection.
# To fix, add this near top of /lib/udev/rules.d/77-nm-probe-modem-capabilities.rules
#   SUBSYSTEMS=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789]?", GOTO="nm_modem_probe_end" 
#
```

[blog1]: http://blog.cudmore.io/post/2016/02/13/Programming-an-arduino-with-platformio/
[teensy-forum]: https://forum.pjrc.com/threads/52805-Uploading-to-teensy-with-platformio-gives-error-teensy_reboot-not-found-(Raspberry-Pi
[platformio-forum]: https://github.com/platformio/platform-teensy/issues/38
[platformio]: https://platformio.org/

