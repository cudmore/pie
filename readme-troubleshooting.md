### Troubleshooting the camera

Capture a still image with the Pi camera with:

```
raspistill -o test.jpg
```

If you get any errors then there is a problem with the Pi Camera.

Make sure the Pi Camera is activated.

```
# type this at a command prompt
sudo raspi-config

# select '5 Interface Options'
# select 'P1 Camera'
# Answer 'Yes' to question 'Would you like the camera interface to be enabled?'
```

### Checking if uv4l (Streaming) is running

In rare instances the [uv4l][uv4l] streaming server does not stop properly. Streaming with uv4l runs at the system level and not in Python. As such, uv4l needs to be controlled via the command line.

```
#list all uv4l processes
ps -aux | grep uv4l

# will yield something like
root     23117  9.8  1.3 140796 12312 ?        Ssl  20:34   0:02 uv4l --driver raspicam --auto-video_nr --encoding h264 --width 640 --height 480 --enable-server on
pi       23262  0.0  0.1   6644  1316 pts/1    S+   20:34   0:00 grep --color=auto uv4l

# kill uv4l with its process id (PID)
# '--' is needed to kill parent and child processes
sudo kill -- 23117

#check the uv4l process is no longer running
ps -aux | grep uv4l

# should yield
pi         674  0.0  0.1   6644  1320 pts/0    S+   21:06   0:00 grep --color=auto uv4l
```

#### uv4l will not go away

Worst case senario is `ps -aux | grep uvl4` yields something like this

```
root     23117 17.2  0.0      0     0 ?        Zsl  20:34   0:37 [uv4l] <defunct>
```

If you see the `<defunct>` then restart the Pi with `sudo reboot` and it should be fixed.

### Converting video

The PiE server uses [libav (avconv)][libav] to convert video from .h264 to .mp4. If labav (avconv) does not install during `~/pie/install-pie`, this conversion will not work.

### bCamera PiCameraMMALError: Failed to enable connection: Out of resources

If you receive this error in the web interface or logs, it means the camera is in use by some other process. The Raspberry camera can only do one thing at a time, it can stream or record but not both at the same time. In addition, the camera can not record (or stream) in two different programs simultaneously.

Make sure other programs are not using the camera and try again. Rebooting with 'sudo reboot' usually does the trick unless these programs, like the PiE server, are set up to run at boot.


### OSError: [Errno 98] Address already in use

This happens when you try and start the server but it is already running. Usually when it is running in the background and you run it again with `./pie run`. Just stop the server with `./pie stop` and then try again with `./pie run`.

[uv4l]: https://www.linux-projects.org/uv4l/
[libav]: https://libav.org/

