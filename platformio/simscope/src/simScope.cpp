/*
Robert Cudmore
20180725

	Simulate a scope trigger out and frame out.

*/

#include "Arduino.h"

// like when user hits scan on scope
const int triggerInPin = 8;

//
const int triggerOutPin = 9;
const int frameOutPin = 6;

// global variables
unsigned long frameStartDelayMillis = 50;	// ms, delay of first frame after startTrialMillis
unsigned long frameIntervalMillis = 30;		// ms, frame interval
unsigned long trialDurMillis = 60000;		// ms, trial duration

boolean useMicroseconds = true;

// runtime variables
boolean trialIsRunning = false;				// runtime
unsigned long gNow = 0;						// runtime
int trialNumber = 0;			// runtime
unsigned long startTrialMillis = 0;			// runtime
unsigned long lastFrameMillis = 0;			// runtime
unsigned int numFrames = 0;					// runtime
int serialIn;

/////////////////////////////////////////////////////////////
void startTrial(unsigned long now) {
	if (trialIsRunning) {
		// trial is already running
	} else {
		trialNumber += 1;
		startTrialMillis = now;
		lastFrameMillis = now + frameStartDelayMillis; //so we don't get a frame immediately
		numFrames = 0;
		trialIsRunning = true;
		
		//
		digitalWrite(triggerOutPin, 1);
		delay(5);
		digitalWrite(triggerOutPin, 0);

		Serial.println("start trial " + trialNumber);
	}
}
/////////////////////////////////////////////////////////////
void stopTrial(unsigned long now) {
 	trialIsRunning = false;
 	
 	unsigned long dur = now - startTrialMillis;

	digitalWrite(triggerOutPin, 1);
	delay(5);
	digitalWrite(triggerOutPin, 0);

 	Serial.println("stop trial " + String(trialNumber) + " dur=" + dur + " startTrialMillis=" + String(startTrialMillis));
}
/////////////////////////////////////////////////////////////
void triggerIn_ISR() {
	startTrial(gNow);
}
/////////////////////////////////////////////////////////////
void newFrame(unsigned long now) {
	numFrames += 1;
	
	unsigned long trialTimeElapsed = now-startTrialMillis;
	unsigned long lastFrameInterval = now-lastFrameMillis;
	
	lastFrameMillis = now;
	
	//
	digitalWrite(frameOutPin, 1);
	delay(5);
	digitalWrite(frameOutPin, 0);

	Serial.println(String(trialTimeElapsed) + " lastInterval=" + String(lastFrameInterval) + " frame " + String(numFrames));
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
void serialInput(int inChar) {
	if (inChar == 115) {
		// 's'
		// same behavior as triggerInPin
		if (trialIsRunning) {
			stopTrial(gNow);
		} else {
			startTrial(gNow);
		}
	}
	if (inChar == 100) {
		// 'd'
		Serial.println("start debug trigger out with 100 fast pulses");
		int i;
		for (i=0; i<20; i+=1) {
			digitalWrite(triggerOutPin, 1); // start
			delay(5);
			digitalWrite(triggerOutPin, 0); // stop
			delay(5);
		}
		Serial.println("done debug trigger out with 100 fast pulses");
	}
}
/////////////////////////////////////////////////////////////
void setup()
{
	if (useMicroseconds) {
		frameStartDelayMillis *= 1000;
		frameIntervalMillis *= 1000;
		trialDurMillis *= 1000;
	}

	// with INPUT_PULLUP, startPin can be floating and goes LOW/GND when button is pushed
	pinMode(triggerInPin, INPUT_PULLUP);
	attachInterrupt(triggerInPin, triggerIn_ISR, FALLING); //

	pinMode(triggerOutPin, OUTPUT);
	digitalWrite(triggerOutPin, 0);

	pinMode(frameOutPin, OUTPUT);
	digitalWrite(frameOutPin, 0);

	Serial.begin(115200);
}
/////////////////////////////////////////////////////////////
void loop()
{
	if (useMicroseconds) {
		gNow = micros();
	} else {
		gNow = millis();
	}
	
	updateTrial(gNow);

	if (Serial.available() > 0) {
		serialIn = Serial.read();
		serialInput(serialIn);
	}
}
