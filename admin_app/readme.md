## PiE Admin Server

The `PiE Admin` server is a web server providing a REST interface (port 5011) to control the main PiE server (port 5010). This is needed for restarting the PiE server, rebooting the maching, and updating the software from the cloud (Github).

This server is installed with the main install script [pie/install-pie](../install-pie).
 
If you are only running one machine with a PiE server, this `PiE Admin` server is not needed and can be ignored.

If you are controlling multiple PiE servers from a [commander](../commander_app/readme.md) server, the commaner server uses this admin server (5011) to control a number of Pie servers (5010).

The `PiE Admin` server can be controlled from the command line as follows:

```
cd ~/pie/admin_app

# control the PiE Admin server
./pieadmin start		- start background pieadmin server
./pieadmin stop			- stop background pieadmin server
./pieadmin status		- check the status of background pieadmin server
-----------------
./pieadmin enable		- enable background pieadmin server at boot
./pieadmin disable		- disable background pieadmin server at boot
-----------------
./pieadmin run			- run pieadmin server on command line
```

The `PiE Admin` server provides a REST insterface to control a PiE server. Each REST endpoint (restartserver, rebootmachine, updatesoftware) calls a bash script whose output is available at the REST endpoint `/status`.

 - Restart PiE server, [bin/restart_server.sh](bin/restart_server.sh)

	/api/restartserver
	
 - Reboot machine, [bin/reboot_machine.sh](bin/reboot_machine.sh)
 
	/api/rebootmachine
	
 - Update PiE server code, [bin/update_software.sh](bin/update_software.sh)
 
 	/api/updatesoftware
 
 
 - Get status of work the admin_app has done
  
	/status
 
