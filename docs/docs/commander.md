Commander is a web server (port 8000) to control any number of PiE servers running on different computers (port 5010).

## Install

	cd ~/pie/commander
	./install-commander


## Browse

	http://[IP]:8000

Once `install-commander` is finished and assuming there are no errors, the commander interface can be browsed at `http://[IP]:8000` where [IP] is the IP address of your Raspberry Pi.

## Starting and stopping commander server

The commander server is designed to run in the background and can be controlled using the `~/pie/commander_app/commander` command.

	cd ~/pie/commander_app

	./commander start       - start the background commander server
	./commander stop        - stop the backgorund commander server
	./commander restart     - restart the background commander server
	./commander status      - get the status of the background commander server
	./commander enable      - start the background commander server at boot
	./commander disable     - do not start the background commander server at boot
	====================
	./commander run         - run commander on command line

If you run into trouble with the commander, run it on the command line to see the output with `./commander run`.
		
## Web interface

### Editing IP addresses

In the config section, turn on 'edit ip' checkbox. Enter a valid IP and hit enter. If the IP is for a running PiE server (no port number needed), the red (bad connection) will be replaced with the current status of the specified PiE server.

### Warnings and errors

When a PiE server is connected, the corresponding row in 'Server Swarm' will be filled in and active. When there is a connection error, the first column will appear red and all other controls will be inactive.

When the drive space remaining goes below 5 GB, the 'File' column will be displayed in red. Currently, there is no interface to set this trip-point, 5 GB is  **hard-coded** in the commander index.html. Feel free to change it yourself.

## Troubleshooting

### Run the commander manually

`install-commander` installs a python virtual env in ~/pie/commander_app/commander_env. The commander server needs to be run in this environment.

```
# activate virtual environment in commander_env
cd ~/pie/commander_app
source commander_env/bin/activate

# command prompt should now start with '(commander_env)'.

# run the commander server manually
python commander.py
```


## Example screen shot of the commander controlling 8 PiE servers.

<table>
<tr><td>
<IMG SRC="../img/video-wall-screenshot-1.png" width="450">
</td></tr>
<tr><td>
<IMG SRC="../img/video-wall-screenshot-2.png" width="450">
</td></tr>
</table>

