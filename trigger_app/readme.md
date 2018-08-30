# Trigger App

A dead simple zero configuration app that uses GPIO input to start a trial and then receive frames. Do not use/run this at the same time as the main PiE server.

## Install

```
sudo apt-get install python3-pip

pip3 install -r requirements.txt
```

## Run

```
python3 trigger.py
```

## Usage

Run [simscope](../platformio/simscope) on a microcontroller, use screen to monitor the serial port and start a trial with 's'.

Install screen

```
sudo apt-get install screen
```

Monitor serial port

```
screen /dev/ttyACM0 115200
```

Exit screen with 'ctrl-a' then ':' then 'quit'. Scroll screen with 'ctrl-a' then 'esc'.