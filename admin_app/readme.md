# PiE Admin Server

The `PiE Admin` server is a web server providing a REST interface (port 5011) to control the main PiE server (port 5010). This is needed for restarting the PiE server, rebooting the maching, and updating the PiE server software from the cloud (Github).

This server is installed with the main install script [pie/install-pie](../install-pie).
 
If there is only one machine running the PiE server, this `PiE Admin` server is not needed and can be ignored.

If you are controlling multiple PiE servers from a [commander](../commander_app/readme.md) server, the commaner server (port 8000) uses the `PiE Admin` server (port 5011) to control a number of PiE servers (port 5010).

## Manually controlling the `PiE Admin` server

The `PiE Admin` server is designed to run in the background and can be controlled from the command line as follows:

```
cd ~/pie/admin_app

# control the PiE Admin server
./pieadmin start		- start background pie admin server
./pieadmin stop			- stop background pie admin server
./pieadmin status		- check the status of background pie admin server
-----------------
./pieadmin enable		- enable background pie admin server at boot
./pieadmin disable		- disable background pie admin server at boot
-----------------
./pieadmin run			- run pie admin server on command line
```

## PiE Admin server REST interface

The `PiE Admin` server provides a REST insterface (port 5011) to control a PiE server (port 5010). Each REST endpoint of the `PiE Admin` server (restartserver, rebootmachine, updatesoftware) calls a bash script whose output is available at the REST endpoint `status`.

 - Restart PiE server, [bin/restart_server.sh](bin/restart_server.sh)

	/api/restartserver
	
 - Reboot machine, [bin/reboot_machine.sh](bin/reboot_machine.sh)
 
	/api/rebootmachine
	
 - Update PiE server code, [bin/update_software.sh](bin/update_software.sh)
 
 	/api/updatesoftware
 
 
 - Get status of work the `PiE Admin` server has done
  
	/status
 
