Commander is a web server (port 8000) to control any number of PiE servers running on different computers (port 5010).

## Install

	cd ~/pie/commander
	./install-commander


## Browse

	http://[IP]:8000

Once `install-commander` is finished and assuming there are no errors, the commander interface can be browsed at `http://[IP]:8000` where [IP] is the IP address of your Raspberry Pi.

## Starting and stopping commander server

The commander server is designed to run in the background and can be controlled using the `~/pie/commander/commander` command.

	cd ~/pie/commander

	./commander start		- start the background commander server
	./commander stop		- stop the backgorund commander server
	./commander restart		- restart the background commander server
	./commander status		- get the status of the background commander server
	./commander enable		- start the background commander server at boot
	./commander disable		- do not start the background commander server at boot
	./commander disable		- do not start the background commander server at boot
	====================
	./commander run			- run commander on command line

If you run into trouble with the commander, run it on the command line to see the output with `./commander run`.
		

## Example

<IMG SRC="img/commander.png">

