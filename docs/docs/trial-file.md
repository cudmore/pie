
Trial files are text files to log events that occur during a video recording. Trial file names are automatically generated with the date, time, and trial number as 'yyyymmdd_hhmmss_t[trial].txt' where [trial] is the trial number.

Events are accumulated during each video recording, including 'record' and 'arm', and saved at the end of each recording into a trial file.

## Trial File Format

All trial files begin with a one line header, followed by one line of column names and then any number of events (one line per event). Trial files are comma delimited except for the one line header. Here is an example trial file with 8 events:

```
date=20180902;time=19:26:49;startTimeSeconds=1535930809.9245791;hostname="pi15";id="";condition="";trialNum=4;numRepeats=1;repeatDuration=301;numRepeatsRecorded=1;repeatInfinity="False";scopeFilename"";video_fps=30;video_resolution="640,480";
date,time,linuxSeconds,secondsSinceStart,event,value,str,tick
20180902,19:26:49,1535930809.9245791,0.0,startTrial,4,,None
20180902,19:26:49,1535930809.95922,0.03464078903198242,newRepeat,1,,None
20180902,19:26:49,1535930809.9660773,0.04149818420410156,beforefilepath,1,/home/pi/video/20180902/20180902_192649_t4_r1_before.h264,None
20180902,19:26:49,1535930809.9661162,0.04153704643249512,afterfilepath,1,/home/pi/video/20180902/20180902_192649_t4_r1_after.h264,None
20180902,19:26:50,1535930810.1416507,0.217071533203125,frame,1,1654442841,710240.945
20180902,19:26:50,1535930810.1694624,0.24488329887390137,frame,2,1654476158,710270.944
20180902,19:26:51,1535930811.1701634,1.24558424949646,triggerIn,False,,711270.812
20180902,19:26:51,1535930811.252085,1.3275058269500732,stopTrial,4,,None
```

Note that the date and start time of a trial (yyyymmdd and hh:mm:ss) appears in (i) the file name, (ii) the header, and (iii) the first 'startTrial' event.

### Trial File Header

The trial file header is a single line with a semi-colon delimited list of token=value pairs. Tokens with a string or boolean type use double quotes ("") around their value. If there is no value for a string token, the double quotes are always included.

| Token				| Format	| Meaning
|  ------ 			| ------ 	| -----
| date					|	yyyymmdd | 
| time					|	hh:mm:ss |
| startTimeSeconds	| float | 
| hostname			| string | The hostname of the Raspberry Pi. Useful to keep track of multiple machines.
| id					| string | The id that is entered in the web, can be empty (e.g. "").interface.
| condition			| string | The condition that is entered in the web interface, can be empty (e.g. "").
| trialNum			| integer |	
| numRepeats			| integer |	
| repeatDuration		| float |	
| numRepeatsRecorded| integer |	The number of repeats actually recorded. Can be different from numRepeats if the user stops the video recording before it is finished.
| repeatInfinity		| boolean |	
| scopeFilename		| string |	
| video_fps			| integer | The frames-per-second of the recorded video, set in the web interface.
| video_resolution	| string | The width and height of the video recording (in pixels). For example "640,480" or "1024,768"

### Trial File Events

All events begin with date, time, linuxSeconds, and secondsSinceStart tokens.

| Token	| Value
|  ------ | ------
| date			| yyyymmdd
| time		|	hh:mm:ss
| linuxSeconds	| A long float representing the time since the linux epoch, this value comes from the Python time package time.time().
| secondsSinceStart	| A long float representing the number of seconds (with fraciton) soince the 'start trigger was received'.

All events end with a 'tick' token. Tick tokens are unsigned float that represents the micro-seconds since the startTrial event. These are only used if the pigpio daemon has been activated. If the pigpiod is not active, all ticks will be logged as 'None' (without the single-quotes). Using pigpio gives better precision for GPIO events compared to the standard Python time.time() function. Keep in mind, although events are more precise, they can still be missed!

| Event			| Class		| value	| str | tick
|  ------ | ------ | ------ | ------ | ------
| startTrial | bTrial	| The trial number | |
| stopTrial	| bTrial	| The trial number | |
| newRepeat	| bTrial	| The repeat (epoch) number | |
| whiteLED	| bTrial	| 1 for on, 0 for off | |
| irLED	| bTrial	| 1 for on, 0 for off | |
| temperature	| bTrial	| The temperature in celcius (assumes using a DHT sensor)
| humidity	| bTrial	| The % relative humidity (assumes using a DHT sensor)
|				|			| | |
| triggerIn	| bPins	|
| frame		| bPins	| The frame number| |
| generic		| bPins	|
| user2		| bPins	|
|				|			|
| beforefilepath		| bCamera		| n/a | Full path to pre trigger video file. | 
| afterfilepath		| bCamera		| n/a | Full path to main video file. The whole point of the PiE server. |
| startArmedRecording		| bCamera		| Time armed recording was started. The code to retrieve this time is immediately after the code to start the camera. As such, it is a more precide time-stamp for the actual time the video was started. |
| stopArmedRecording		| bCamera		| Same idea but at the stop of armed recording, see startArmedRecording. |
| startVideoRecord		| bCamera		| See startArmedRecording. |
| stopVideoRecord		| bCamera		| Same idea but at the stop of recording, see startArmedRecording |

