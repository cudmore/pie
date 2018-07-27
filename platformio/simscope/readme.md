# Sim Scope

Sim Scope is microcontroller code to simulate a microscope.

Start a trial with a GPIO trigger (startPin, GPIO 8) or serial command 's'. Once a trial starts, frames are output on a GPIO (frameOutPin, GPIO 6).

There are globals to control the duration of a trial, the delay before the first frame, and the frame rate.

## Upload

```
sudo ../env/bin/platformio run -e teensy35 --target upload
```

## Screen serial

```
screen /dev/ttyACM0 115200
```



