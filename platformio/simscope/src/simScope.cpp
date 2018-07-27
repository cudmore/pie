/*
Robert Cudmore
20180725

Simulate a scope trigger out and frame out

*/

#include "Arduino.h"

// like when user hits scan on scope
const int startPin = 8;

//
const int triggerOutPin = 9;
const int frameOutPin = 6;

// global variables
boolean trialIsRunning = false;
unsigned long gNow = 0;
unsigned long frameStartDelayMillis = 50; // delay of first frame after startTrialMillis
unsigned long frameIntervalMillis = 30;
unsigned long startTrialMillis = 0;
unsigned long trialDurMillis = 4000;
unsigned long lastFrameMillis = 0;
unsigned int numFrames = 0;
int serialIn;

/////////////////////////////////////////////////////////////
void startTrial(unsigned long now) {
	if (trialIsRunning) {
		// trial is already running
	} else {
  		Serial.println(String(0) + " start trial");
		startTrialMillis = now;
		lastFrameMillis = now + frameStartDelayMillis; //so we don't get a frame immediately
		numFrames = 0;
		trialIsRunning = true;
		//
		digitalWrite(triggerOutPin, 1);
		digitalWrite(triggerOutPin, 0);
	}
}
/////////////////////////////////////////////////////////////
void stopTrial(unsigned long now) {
 	trialIsRunning = false;
 	Serial.println(String(now-startTrialMillis) + " stop trial startTrialMillis=" + String(startTrialMillis));
}
/////////////////////////////////////////////////////////////
void startPin_ISR() {
	startTrial(gNow);
}
/////////////////////////////////////////////////////////////
void newFrame(unsigned long now) {
  numFrames += 1;
  
  Serial.println(String(now-startTrialMillis) + " lastInterval=" + String(now-lastFrameMillis) + " frame " + String(numFrames));

  lastFrameMillis = now;
  
  //
  digitalWrite(frameOutPin, 1);
  //delay(5);
  digitalWrite(frameOutPin, 0);
}
/////////////////////////////////////////////////////////////
void updateTrial(unsigned long now) {
 if (trialIsRunning) {
 	// new frame ?
 	if (now > (lastFrameMillis + frameIntervalMillis)) {
 		newFrame(now);
 	}

 	// end trial ?
 	if (now > (startTrialMillis + trialDurMillis)) {
 		stopTrial(now);
 	}
 } // trialIsRunning
}
/////////////////////////////////////////////////////////////
void setup()
{
  // with INPUT_PULLUP, can be floating and goes LOW/GND when button is pushed
  pinMode(startPin, INPUT_PULLUP);
  attachInterrupt(startPin, startPin_ISR, RISING); //

  pinMode(triggerOutPin, OUTPUT);
  digitalWrite(triggerOutPin, 0);

  pinMode(frameOutPin, OUTPUT);
  digitalWrite(frameOutPin, 0);

  Serial.begin(115200);
}
/////////////////////////////////////////////////////////////
void loop()
{
	gNow = millis();
	
	updateTrial(gNow);

	if (Serial.available() > 0) {
		serialIn = Serial.read();
		if (serialIn == 115) {
			// 's'
			startTrial(gNow);
		}
	}
}
