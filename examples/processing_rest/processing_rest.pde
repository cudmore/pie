// Author: Robert Cudmore
// Date: 20181026

// This code assumes that http.request library is installed
// To install, select menu 'Sketch - Import Library... - Add Library...' and search for 'http requests'
import http.requests.GetRequest;

  // search and replace 192.168.1.4 with the IP address of a PiE server
  
  // grab the PiE server 'status' using endpoint /status
  JSONObject status = loadJSONObject("http://192.168.1.4:5010/status");
  
  // (0) parse the PiE server 'status' into its different pieces
  JSONObject trial = status.getJSONObject("trial");
  JSONObject config = trial.getJSONObject("config");
  JSONObject hardware = config.getJSONObject("hardware");
  JSONArray eventOut = hardware.getJSONArray("eventOut"); // eventOut is a JSON array
  
  // specify the white and IR LED indices (these are indices into JSON eventOut array)
  Integer whiteIdx = 1;
  Integer irIdx = 2;
  
  // (1) get the the initial 'state' of white and IR LEDs
  JSONObject whiteLED = eventOut.getJSONObject(whiteIdx);
  JSONObject irLED = eventOut.getJSONObject(irIdx);
  println("1");
  println("whiteLED 'state' was:", whiteLED.getBoolean("state"));
  println("irLED 'state' was:", irLED.getBoolean("state"));

  // (2) toggle/invert the 'state' of white and IR leds
  Boolean newWhiteState = ! whiteLED.getBoolean("state");
  Boolean newIRState = ! irLED.getBoolean("state");
  println("2");
  println("newWhiteState:", newWhiteState);
  println("newIRState:", newIRState);
  
  // convert from Boolean to int
  // endpoint /api/v2/set/led/<ledIdx>/<value> expects <value> in (0,1) and not in (true, false)
  int newWhiteStateInt = newWhiteState ? 1 : 0;
  int newIRStateInt = newIRState ? 1 : 0;

  // set the new values on the PiE server using REST endpoint /api/v2/set/led/<ledIdx>/<value>
  // where:
  //    <ledIdx>: 1 for white, 2 for IR (e.g. whiteIdx and irIdx)
  //    <value>: 1 for on, 0 for off
  GetRequest postWhite = new GetRequest("http://192.168.1.4:5010/api/v2/set/led/" + whiteIdx + "/" + newWhiteStateInt);
  postWhite.send();
  GetRequest postIR = new GetRequest("http://192.168.1.4:5010/api/v2/set/led/" + irIdx + "/" + newIRStateInt);
  postIR.send();

  // (3) grab the PiE server 'status' using endpoint /status again to ensure our changes took effect
  // You can also look at the web interface to see if the LED changes took effect !!!
  status = loadJSONObject("http://192.168.1.4:5010/status");
  
  // parse the PiE server 'status' into its different pieces, the same as step (0) above
  trial = status.getJSONObject("trial");
  config = trial.getJSONObject("config");
  hardware = config.getJSONObject("hardware");
  eventOut = hardware.getJSONArray("eventOut");
  whiteLED = eventOut.getJSONObject(whiteIdx);
  irLED = eventOut.getJSONObject(whiteIdx);
  
  println("3");
  println("whiteLED 'state' is now:", whiteLED.getBoolean("state"));
  println("irLED 'state' is now:", irLED.getBoolean("state"));
