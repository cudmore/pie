// Author: Robert Cudmore
// Date: 20181026
//
// Purpose: Script to show how to interact with the treadmill arduino code

import processing.serial.*;

int lf = 10;    // Linefeed in ASCII
int cr = 13;    // Linefeed in ASCII

String myString = null;
Serial myPort;       

void setup() {
  // List all the available serial ports:
  printArray(Serial.list());

  // You can get a better idea of which port to use by
  // looking at the automatically detected Teensy port in the Arduino IDE
  // [7] "/dev/tty.usbmodem4531961"
  String portName = Serial.list()[7];
  Integer baud = 115200;
  println("Using serial port: ", portName, " at baud ", baud);

  // Open the port you are using at the rate you want:
  myPort = new Serial(this, portName, baud);
  
  // h : treadmill help
  myPort.write("h" + "\n");

  // p : print treadmill parameters
  myPort.write("p" + "\n");

  // set,param,value : set a parameter
  myPort.write("set,motorDel,100" + "\n");
  myPort.write("set,motorDur,200" + "\n");
  
  // start : start a trial
  //myPort.write("start");
  
  // d : dump/return the events of the last trial
  //myPort.write("d" + "\n");
}

void draw() {
  while (myPort.available() > 0) {
    myString = myPort.readStringUntil(lf);
    if (myString != null) {
      print(myString);
    }
  }
}
