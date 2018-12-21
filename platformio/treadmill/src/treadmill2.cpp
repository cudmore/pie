/*
 * Author: Robert Cudmore
 * http://robertcudmore.org
 * 20160214
 *
 * Purpose: Run a trial based experiment
 *
 *	20180618, making some changes
 *	  - add serial command to stop, call stop_ISR
 *	  - add serial command to control direction, motor.direction
 */

/*

 *	IMPORTANT:
 *
 *	Currently configured to respond to start trigger that is FALLING
 *	This is because Bruker PrairieView Scope is configured this way
 *	  pinMode(startTrialPin, INPUT_PULLUP); // prairie expects trigger to be LOW
 *	  attachInterrupt(startTrialPin, startTrial_ISR, FALLING); // prairie expects trigger to be LOW
 *	If your scope is the opposite (e.g. triggered on RISING), you need to reverse this
 *	  pinMode(startTrialPin, INPUT); // INPUT has implicit PULLDOWN !!!
 *	  attachInterrupt(startTrialPin, startTrial_ISR, RISING);
*/

// For information on exposing low-vevel interrupts on Arduino Uno
// http://www.geertlangereis.nl/Electronics/Pin_Change_Interrupts/PinChange_en.html
// No need to do this on Teensy, all pins allow low-level interrupts
//
//for easy motor driver tutorial, see
// https://learn.sparkfun.com/tutorials/easy-driver-hook-up-guide

#include "Arduino.h"
//#include "bSimulateScope.h"
//#include "main.h"

#include <AccelStepper.h> // http://www.airspayce.com/mikem/arduino/AccelStepper/index.html
#include <Encoder.h> // http://www.pjrc.com/teensy/td_libs_Encoder.html

//input

// new 20180701
const int extTriggerInPin = 8; //start trial when this pin goes hi (external trigger from scope)
const int passThroughExtTriggerInPin = 9; //pulsed high when extTriggerInPin is received in extTrigger_ISR()
										//connect this pin to raspberry (rising, pull_down)
										
const int startTrialPin = 3; //start trial when this pin goes hi (from Raspberry)

const int framePin = 5; //5V input, trigger a frame when this pin goes high

const int emergencyStopPin = 20; //emergency shutdown when this pin goes hi

//output
const int passThroughFramePin = 6; //output pulse when we receive a frame on framePin, see frame_ISR()
const int trialRunningPin = 14;//output high when trial is running (see startTrial() and stopTrial())
const int motorOnPin = 11; //output high when motor on
const int newEpochPin = 12;//output pulse when new motor epoch
const int encoderOutPin = 10; //output pulse when encoder changes

//encoder pins (these pins need to have low level interrupts)
//todo: 20181220, this is not working any more. Give encoder unique pins and make sure output to raspberry is working
const int encoderPinA = 21;
const int encoderPinB = 22;

//motor pins (assuming easydriver board)
const int motorStepPin = 17;
const int motorDirPin = 16;
//When set LOW, all STEP commands are ignored and all FET functionality is turned off. Must be pulled HIGH to enable STEP control
const int motorResetPin = 19; // high to engage step control
//Logic Input. Enables the FET functionality within the motor driver. If set to HIGH, the FETs will be disabled, and the IC will not drive the motor. If set to LOW, all FETs will be enabled, allowing motor control.
const int motorEnabledPin = 20; //low to engage, high to dis-engage

volatile unsigned long newTrialTime = 0;
volatile unsigned long newFrameTime = 0;
volatile unsigned long forceStop = 0;

//4500 frames == 2.5 min * 60 seconds/minute * 30 frames/second
const int kMaxEvents = 4500 * 1;
unsigned long eventTimes[kMaxEvents];
short eventType[kMaxEvents];
short eventValue[kMaxEvents];
//int eventNumber = 0;

//const int outputSerial = 1; //turn this on for debugging (WILL BLOCK MOTOR)

struct trial
{
	//parameters
	int  armed; //boolean, added 20180702

	//was this
	//int  preDur; //ms
	//int  postDur; //ms
	unsigned long  preDur; //ms
	unsigned long  postDur; //ms

	//was this
	//int epochDur;
	unsigned long epochDur;
	int numEpoch;
	
	//int numPulse;
	//int pulseDur; //ms
	
	boolean useMotor;
	int motorDel; //ms
	int motorDur; //ms
	int motorSpeed; //

	String duringPulse; // ("Rotate", "Locked", "Free")
	String betweenPulse; // ("Locked", "Free")
	String betweenTrial; // ("Locked", "Free")
	
	//runtime
	boolean trialIsRunning;
	int trialNumber;
	unsigned long trialStartMillis;
	//was this
	//int trialDur; //ms, numEpoch*epochDur
	unsigned long trialDur; //ms, numEpoch*epochDur
	int currentEpoch;
	unsigned long epochStartMillis;
	//unsigned int currentPulse; //count 0,1,2,... as we run
	//unsigned long pulseStartMillis; //millis at start of currentPulse

	//use these to index into global arrays
	int currentFrame;
	//int currentEncoderIndex;
	int eventNumber;
};

struct steppermotor
{
   //boolean useMotor;
   boolean isRunning;
   int direction;
   int speed;
   int maxSpeed;
   //int stepPin;
   //int dirPin;
   int resetPin;
};

struct rotaryencoder
{
	//int pinA; // use pin 2
	//int pinB; // use pin 3
	long position;
	unsigned long updateInterval; //ms
	unsigned long lastUpdateTime; //now - trial.trialStartMillis
};

String versionStr = "20160918"; //"20160322";
typedef struct trial Trial;
typedef struct steppermotor StepperMotor;
typedef struct rotaryencoder RotaryEncoder;

Trial trial;
StepperMotor motor;
RotaryEncoder rotaryencoder;

//sep2016, these should go into setup()
//stepper and myEncoder are the variable names we will use below
AccelStepper stepper(AccelStepper::DRIVER,motorStepPin,motorDirPin);
Encoder myEncoder(encoderPinA, encoderPinA);

//phase out bSimulateScope
//make an input pin and when it goes up, start a trial
//
//have this arduino simulate a scope
//once started, it outputs pulses on triggerPin and framePin (like a real scope)
//int simTriggerPin = 20; //trial
//int simFramePin = 21; //frame
//int simLedPin = 13;
//bSimulateScope fakeScope(simTriggerPin, simFramePin, simLedPin);

/////////////////////////////////////////////////////////////
void serialOut(unsigned long now, String str, unsigned long val) {
	Serial.println(String(now) + "," + str + "," + val);
}

/////////////////////////////////////////////////////////////
// Interrupt Service (ISR) Routines
/////////////////////////////////////////////////////////////
void extTrigger_ISR() {
	// this is truly a pass through to act as a level shifter for Pi
	// if you want to run without a pi, this should call startTrial_ISR()
	digitalWrite(passThroughExtTriggerInPin, 1);
	//delay(1000);
	digitalWrite(passThroughExtTriggerInPin, 0);	
}

/////////////////////////////////////////////////////////////
void startTrial_ISR() {
	//start trial received
	//serialOut(millis(),"startTrial_ISR()",0);
	if (trial.armed) {
		if (newTrialTime == 0) {
			newTrialTime = millis();
		}
	}
}
/////////////////////////////////////////////////////////////
void frame_ISR() {
	//frame received
	//serialOut(millis(),"frame_ISR()",0);
	if (newFrameTime == 0) {
		newFrameTime = millis();
		//pulse a 3.5V pin for each frame
		digitalWrite(passThroughFramePin, 1);
		
		//delayMicroseconds(100);
		
		digitalWrite(passThroughFramePin, 0);	
	}
}
/////////////////////////////////////////////////////////////
void stop_ISR() {
	//emergency stop received
	forceStop = 1;
}


/////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////
void setup()
{
  //
  //install callback interrupts for start and frame

  //
  // pin to receive start trial when scope is master
  // pin to receive 5V external trigger (extTriggerInPin) and pass on to 3V Raspberry (passThroughExtTriggerInPin)
  pinMode(extTriggerInPin, INPUT);
  attachInterrupt(extTriggerInPin, extTrigger_ISR, RISING); //
  pinMode(passThroughExtTriggerInPin, OUTPUT);
  // this is a pass through (using the teensy as a level shifter) to Raspberry 3V (passThroughExtTriggerInPin)
  digitalWrite(passThroughExtTriggerInPin, 0);
  
  // pin to receive start trial when Raspberry is master
  pinMode(startTrialPin, INPUT_PULLUP); // prairie expects trigger to be FALLING (when pin goes low)
  attachInterrupt(startTrialPin, startTrial_ISR, FALLING); // prairie expects trigger to be FALLING (when pin goes low)
  // replace with this to reverse, make trigger be RISING
  //pinMode(startTrialPin, INPUT);
  //attachInterrupt(startTrialPin, startTrial_ISR, RISING);

  
  //
  // pin to receive 5V frames from scope (framePin) and pass on to 3V Raspberry (passThroughFramePin)
  //pinMode(framePin, INPUT);
  //attachInterrupt(framePin, frame_ISR, RISING); //prairie frames are RISING
  //  replace with this to reverse, scanimage will be FALLING
  pinMode(framePin, INPUT_PULLUP);
  attachInterrupt(framePin, frame_ISR, FALLING); //prairie frames are RISING
  
  pinMode(passThroughFramePin, OUTPUT);
  digitalWrite(passThroughFramePin, 0);

  //
  // emergency stop (not implemented)
  pinMode(emergencyStopPin, INPUT);
  attachInterrupt(emergencyStopPin, stop_ISR, RISING); //scanimage will be FALLING
  
  //
  //pins for LED/Raspberry to indicate state
  pinMode(trialRunningPin, OUTPUT);
  digitalWrite(trialRunningPin, 0);

  pinMode(motorOnPin, OUTPUT);
  digitalWrite(motorOnPin, 0);

  pinMode(newEpochPin, OUTPUT);
  digitalWrite(newEpochPin, 0);

  pinMode(encoderOutPin, OUTPUT);
  digitalWrite(encoderOutPin, 0);

  pinMode(motorEnabledPin, OUTPUT); //low to engage motor, high to dis-engage motor
  digitalWrite(motorEnabledPin, 0); //low to engage motor, high to dis-engage motor

  pinMode(motorDirPin, OUTPUT);
  digitalWrite(motorDirPin, 0);
  
  //
  //trial
  trial.armed = false;
  trial.trialIsRunning = false;
  trial.trialNumber = 0;
  trial.trialStartMillis = 0;

  trial.epochDur = 500; // epoch has to be >= (preDur + xxx + postDur)
  trial.numEpoch = 3;
  trial.preDur = 100;
  trial.postDur = 100;
  trial.trialDur = trial.preDur + (trial.numEpoch*trial.epochDur) + trial.postDur;
  trial.useMotor = 0;
  trial.motorDel = 100; //within each epoch/pulse
  trial.motorDur = 300;

  trial.duringPulse = "Rotate";
  trial.betweenPulse = "Locked";
  trial.betweenTrial = "Locked"; // ("Locked", "Free")
  
  trial.currentFrame = 0;
  //trial.currentEncoderIndex = 0;
  trial.eventNumber = 0;
  
  //
  //motor
  //motor.useMotor = true;
  motor.isRunning = false;
  motor.speed = -120; //larger abs(motor.speed) is faster, sign gives direction
  //motor.direction = -1; // +1 and -1
  motor.maxSpeed = 1000;
  //motor.stepPin = motorStepPin;
  //motor.dirPin = motorDirPin;
  // normally high input signal will reset the internal translator and disable all output drivers when pulled low.
  motor.resetPin = motorResetPin;
 
  pinMode(motor.resetPin, OUTPUT);
  digitalWrite(motor.resetPin, ! trial.useMotor);

  //AccelStepper stepper(AccelStepper::DRIVER,motor.stepPin,motor.dirPin);
  stepper.setMaxSpeed(motor.maxSpeed);
  //stepper.setSpeed((float) (motor.direction * motor.speed) );	
  stepper.setSpeed((float) motor.speed );	
 
  //
  //rotary encoder
  //rotaryencoder.pinA = encoderPinA;
  //rotaryencoder.pinB = encoderPinB;
  rotaryencoder.position = -999;
  rotaryencoder.updateInterval = 30; //ms
  rotaryencoder.lastUpdateTime = -999;
  
  //Encoder myEncoder(rotaryencoder.pinA, rotaryencoder.pinB);

  //
  //pinMode(LED_BUILTIN, OUTPUT);
  pinMode(13, OUTPUT);
  
  Serial.begin(115200);

  //fakeScope.set("numFrames", 1800);
  
  newTrialTime = 0;
  newFrameTime = 0;

  //if (outputSerial) {
  //	serialOut(millis(), "setup", 1);
  //}
}

/////////////////////////////////////////////////////////////
void newevent(unsigned long time, String event, short value) {

	trial.eventNumber += 1;
	//check for overflow
	if (trial.eventNumber >= kMaxEvents) {
		//overflow
		eventTimes[kMaxEvents-1] = time;
		eventType[kMaxEvents-1] = 999;
		eventValue[kMaxEvents-1] = trial.eventNumber + 1; //total number of events	
		return;	
	}
	//keep track of events we add
	eventTimes[0] = time;
	eventType[0] = 0;
	eventValue[0] = trial.eventNumber + 1; //total number of events	

	short int eventTypeNum = 0;
	if (event == "startTrial") {
		eventTypeNum = 1;
	}
	else if (event == "startEpoch") {
		eventTypeNum = 2;
	}
	else if (event == "startMotor") {
		eventTypeNum = 3;
	}
	else if (event == "stopMotor") {
		eventTypeNum = 4;
	}
	else if (event == "frame") {
		eventTypeNum = 5;
	}
	else if (event == "rotaryPos") {
		eventTypeNum = 6;
	}
	else if (event == "stopTrial") {
		eventTypeNum = 7;
	}
	else if (event == "encoder") {
		eventTypeNum = 8;
	}
	
	if (eventTypeNum>0) {
		eventTimes[trial.eventNumber] = time;
		eventType[trial.eventNumber] = eventTypeNum;
		eventValue[trial.eventNumber] = value;	
	}
	
	//if (outputSerial) {
	//	serialOut(time, event, value);
	//}
}
/////////////////////////////////////////////////////////////
void DumpTrial() {
	//Serial.println("=== DumpTrial ===");
	Serial.println("eventTime,eventType,eventValue");	
	for (int i = 0; i<=trial.eventNumber; i+=1) {
		String eventTypeStr = "";
		if (eventType[i] == 0) {
			eventTypeStr = "numEvents";
		} else if (eventType[i] == 1) {
			eventTypeStr = "startTrial";
		} else if (eventType[i] == 2) {
			eventTypeStr = "startEpoch";
		} else if (eventType[i] == 3) {
			eventTypeStr = "startMotor";
		} else if (eventType[i] == 4) {
			eventTypeStr = "stopMotor";
		} else if (eventType[i] == 5) {
			eventTypeStr = "frame";
		} else if (eventType[i] == 6) {
			eventTypeStr = "rotaryPos";
		} else if (eventType[i] == 7) {
			eventTypeStr = "stopTrial";
		} else if (eventType[i] == 8) {
			eventTypeStr = "encoder";
		}
		Serial.println(String(eventTimes[i]) + "," + eventTypeStr + "," + String(eventValue[i]));	
	}
}

/////////////////////////////////////////////////////////////
void startTrial(unsigned long now) {
	if (trial.trialIsRunning==0) {
		// motor speed
		//stepper.setSpeed((float) (motor.direction * motor.speed));	
		//stepper.setSpeed((float) (motor.direction * trial.motorSpeed));	

		// motor enable
		digitalWrite(motorEnabledPin, ! trial.useMotor);
		
		trial.trialNumber += 1;
		trial.eventNumber = 0;
		
		trial.trialStartMillis = now;
		//trial.epochStartMillis = now;

		//trial.trialDur = trial.preDur + (trial.numEpoch * trial.epochDur) + trial.postDur;
		trial.currentEpoch = 0;
		//trial.currentPulse = -1;
		
		trial.currentFrame = 0;
		//trial.currentEncoderIndex = 0;
		
		trial.trialIsRunning = 1;

		digitalWrite(trialRunningPin, HIGH);

		newevent(0, "startTrial", trial.trialNumber);
		
		// removed 20180724
		//Serial.println("startTrial " + String(now));
		
		//if (outputSerial) {
		//	serialOut(0, "startTrial", trial.trialNumber);
		//}
	}
}
/////////////////////////////////////////////////////////////
void stopTrial(unsigned long now) {
	if (trial.trialIsRunning==1) {
		trial.trialIsRunning = 0;
		motor.isRunning = false; //make sure motor is NOT running

		unsigned long stoptime = now - trial.trialStartMillis;		
		newevent(stoptime, "stopTrial", trial.trialNumber);

		digitalWrite(trialRunningPin, LOW);

		// removed 20180724
		//Serial.println("stopTrial " + String(now));
		
		//digitalWrite(motorOnPin, LOW); //stop motor just in case
	}
}
/////////////////////////////////////////////////////////////
void newFrame(unsigned long now) {
	if (trial.trialIsRunning==1) {
		trial.currentFrame += 1;
		
		unsigned long frametime = now - trial.trialStartMillis;
		
		newevent(frametime, "frame", trial.currentFrame);
		//if (outputSerial) {
		//	serialOut(frametime, "newFrame", trial.currentFrame);
		//}
	}
}
/////////////////////////////////////////////////////////////
void PrintHelp() {
	Serial.println("=== treadmill help ===");
	Serial.println("start : start");
	Serial.println("stop : stop");
	Serial.println("p : print state of the trial parameters");
	Serial.println("d : dump information about last trial");
	Serial.println("set,param,val : set");
	Serial.println("h : help");
	Serial.println("v : version");
}
/////////////////////////////////////////////////////////////
void GetState() {
	//trial
	Serial.println("");
	Serial.println("armed=" + String(trial.armed));

	Serial.println("trialNumber=" + String(trial.trialNumber));
	Serial.println("trialDur=" + String(trial.trialDur)); // this is calculated, not a parameter

	Serial.println("numEpoch=" + String(trial.numEpoch));
	Serial.println("epochDur=" + String(trial.epochDur));

	Serial.println("preDur=" + String(trial.preDur));
	Serial.println("postDur=" + String(trial.postDur));

	//Serial.println("numPulse=" + String(trial.numPulse));
	//Serial.println("pulseDur=" + String(trial.pulseDur));

	Serial.println("useMotor=" + String(trial.useMotor));
	Serial.println("motorDel=" + String(trial.motorDel));
	Serial.println("motorDur=" + String(trial.motorDur));
	//motor
	Serial.println("motorSpeed=" + String(trial.motorSpeed));
	Serial.println("motorMaxSpeed=" + String(motor.maxSpeed));

	Serial.println("versionStr=" + String(versionStr));
}
/////////////////////////////////////////////////////////////
void SetTrial(String name, String strValue) {
	
	// be careful, for name=="arm" I am passing strValue = (True, False)
	int value = strValue.toInt();
	
	//trial
	if (name=="numEpoch") {
		trial.numEpoch = value;
		Serial.println("trial.numEpoch=" + String(trial.numEpoch));
	} else if (name=="epochDur") {
		trial.epochDur = value;
		Serial.println("trial.epochDur=" + String(trial.epochDur));

	} else if (name=="preDur") {
		trial.preDur = value;
		Serial.println("trial.preDur=" + String(trial.preDur));
	} else if (name=="postDur") {
		trial.postDur = value;
		Serial.println("trial.postDur=" + String(trial.postDur));

	} else if (name=="useMotor") {
		if (strValue=="motorOn") {
			trial.useMotor = true;
		} else {
			trial.useMotor = false;
		}
		Serial.println("trial.useMotor=" + String(trial.useMotor));

	} else if (name=="motorDel") {
		trial.motorDel = value;
		Serial.println("trial.motorDel=" + String(trial.motorDel));
	} else if (name=="motorDur") {
		trial.motorDur = value;
		Serial.println("trial.motorDur=" + String(trial.motorDur));
	} else if (name=="motorSpeed") {
		// order matters, this uses motor.direction
		// caller needs to indicate direction (+1, -1) with speed
		trial.motorSpeed = value;
		//stepper.setSpeed((float) (motor.direction * trial.motorSpeed));
		stepper.setSpeed((float) trial.motorSpeed);
		Serial.println("trial.motorSpeed=" + String((float) trial.motorSpeed));
	//} else if (name=="direction") {
	//	trial.direction = value;
	//	Serial.println("trial.direction=" + String(trial.direction));

	} else if (name=="arm") {
		if (strValue == "True") {
			trial.armed = true;
		} else {
			trial.armed = false;
		}
		Serial.println("trial.armed=" + String(trial.armed));

	} else if (name=="duringPulse") {
		trial.duringPulse = strValue;
		Serial.println("trial.duringPulse=" + trial.duringPulse);
	} else if (name=="betweenPulse") {
		trial.betweenPulse = strValue;
		Serial.println("trial.betweenPulse=" + trial.betweenPulse);

	} else {
		Serial.println("SetValue() did not handle '" + name + "'");
	}

	trial.trialDur = trial.preDur + (trial.numEpoch * trial.epochDur) + trial.postDur;
	
}
/////////////////////////////////////////////////////////////
//respond to incoming serial
void SerialIn(unsigned long now, String str) {
	String delimStr = ",";
		
	if (str.length()==0) {
		return;
	}
	if (str == "v") {
		Serial.println("version=" + versionStr);
	} else if (str == "start") {
		startTrial(millis());
	}
	else if (str == "stop") {
		stopTrial(now);
	}
	else if (str.startsWith("p")) {
		GetState();
	}
	else if (str.startsWith("d")) {
		DumpTrial();
	}
	else if (str.startsWith("h")) {
		PrintHelp();
	}
	else if (str.startsWith("set")) {
		//set is {set,name,value}
		int firstComma = str.indexOf(delimStr,0);
		int secondComma = str.indexOf(delimStr,firstComma+1);
		String nameStr = str.substring(firstComma+1,secondComma); //first is inclusive, second is exclusive
		String valueStr = str.substring(secondComma+1,str.length());
		SetTrial(nameStr, valueStr);
	}
	else {
		Serial.println("treadmill did not handle serial: '" + str + "'");
	}
		
}

unsigned long g_msIntoTrial;
unsigned long g_msIntoEpoch;
unsigned long g_inEpochNum;
boolean g_inPreTrial;
boolean g_inPulseTrial; //in the pulse portion of the trial
boolean g_inPostTrial;

/////////////////////////////////////////////////////////////
void updateTrial(unsigned long now) {
	//
	//update epoch
	if ( trial.trialIsRunning == 0 ) {
		return;
	}
	
	g_msIntoTrial = now - trial.trialStartMillis;

	if (g_msIntoTrial > trial.trialDur) {
		stopTrial(now);
		return;
	}

	// '<' is critical here!!!, <= and the first epoch overlaps with 2nd
	g_inPreTrial = (g_msIntoTrial < trial.preDur);
	g_inPostTrial = (g_msIntoTrial > (trial.preDur + (trial.epochDur * trial.numEpoch)));
	g_inPulseTrial = ((!g_inPreTrial) && (!g_inPostTrial));
	
	//if (!g_inPreTrial) {
	if (g_inPulseTrial) {
		int tmpCurrEpoch = int(floor((g_msIntoTrial-trial.preDur) / trial.epochDur) + 1);
		if (tmpCurrEpoch>0 && tmpCurrEpoch<=trial.numEpoch) {
			//epoch
			if (tmpCurrEpoch != trial.currentEpoch) {
				trial.currentEpoch = tmpCurrEpoch;
				trial.epochStartMillis = now;
				newevent(g_msIntoTrial, "startEpoch", trial.currentEpoch);
				//pulse 
				digitalWrite(newEpochPin, HIGH);
				digitalWrite(newEpochPin, LOW);
			}

			//was here
			g_msIntoEpoch = now - trial.epochStartMillis;

		}
		//g_msIntoEpoch = now - trial.epochStartMillis;

	}
	//g_msIntoEpoch = now - trial.epochStartMillis;
}

/////////////////////////////////////////////////////////////
void updateMotor(unsigned long now) {
	//need to use g_inPulseTrial as g_msIntoEpoch is not defined until g_msIntoEpoch is defined
	unsigned long tmpMillis = (now - trial.trialStartMillis - trial.preDur) % (trial.epochDur);
	//if (trial.trialIsRunning && trial.useMotor && g_inPulseTrial) {
	if (trial.trialIsRunning && trial.useMotor) {
		unsigned long motorStart = trial.motorDel;
		unsigned long motorStop = motorStart + trial.motorDur;
		//if (!motor.isRunning && (g_msIntoEpoch >= motorStart) && (g_msIntoEpoch < motorStop)) {
		if (!motor.isRunning && (tmpMillis > motorStart) && (tmpMillis <= motorStop)) {
			digitalWrite(motorOnPin, HIGH);
			motor.isRunning = true;
			newevent(g_msIntoTrial, "startMotor", trial.currentEpoch);
		//} else if (motor.isRunning && (g_msIntoEpoch > motorStop)) {
		} else if (motor.isRunning && (tmpMillis <= motorStart)) {
			digitalWrite(motorOnPin, LOW);
			motor.isRunning = false;
			newevent(g_msIntoTrial, "stopMotor", trial.currentEpoch);
		}
		if (motor.isRunning) {
			//stepper.setSpeed(motor.direction * motor.speed);	
			
			
			if (trial.duringPulse == "Rotate") {
				//digitalWrite(motorEnabledPin, LOW); //low to engage, high to dis-engage
				digitalWrite(motorResetPin, HIGH); // high to engage step control
				//
				stepper.runSpeed();
				//
			} else if (trial.duringPulse == "Locked") {
				//digitalWrite(motorEnabledPin, LOW); //low to engage, high to dis-engage
				digitalWrite(motorResetPin, HIGH); // high to engage step control
			} else if (trial.duringPulse == "Free") {
				//digitalWrite(motorEnabledPin, HIGH); //low to engage, high to dis-engage
				digitalWrite(motorResetPin, LOW); // high to engage step control
			}
		} else {
			// we are between pulses
			if (trial.betweenPulse == "Locked") {
				//digitalWrite(motorEnabledPin, LOW); //low to engage, high to dis-engage
				digitalWrite(motorResetPin, HIGH); // high to engage step control
			} else if (trial.betweenPulse == "Free") {
				//digitalWrite(motorEnabledPin, HIGH); //low to engage, high to dis-engage
				digitalWrite(motorResetPin, LOW); // high to engage step control
			}
		}
		
	} else {
		// this should not effect arduino code (it is just visual output)
		// treadmill.py WILL receive a motor off event and log it !!!

		// motor is free to spin when not running a trial
		//digitalWrite(motorOnPin, LOW);
		// motor is locked when not running a trial
		if (trial.betweenTrial == "Locked") {
			digitalWrite(motorResetPin, HIGH);
		} else if (trial.betweenTrial == "Free") {
			digitalWrite(motorResetPin, LOW);
		}
	}
}

/////////////////////////////////////////////////////////////
void updateEncoder(unsigned long now, long newPosition) {

	//only deal with rotary encoder when motor is off (wheel is free to turn)
	long encoderDiff = newPosition - rotaryencoder.position;
	if (encoderDiff != 0) {
		digitalWrite(encoderOutPin, HIGH);
		digitalWrite(encoderOutPin, LOW);
		rotaryencoder.position = newPosition;
		if (trial.useMotor == 0) {
			if ( (g_msIntoTrial - rotaryencoder.lastUpdateTime) > rotaryencoder.updateInterval ) {
				rotaryencoder.lastUpdateTime = g_msIntoTrial;
				//trial.currentEncoderIndex += 1;
				//encoderTimes[trial.currentEncoderIndex] = g_msIntoTrial;
				//encoderPositions[trial.currentEncoderIndex] = newPosition;
				newevent(g_msIntoTrial, "encoder", newPosition);
				//pulse
				//digitalWrite(encoderOutPin, HIGH);
				//digitalWrite(encoderOutPin, LOW);
			}
		} //encoderDiff
	} // useMotor
}

// for loop
long newEncoderPos = -999;
long lastEncoderPos = -999;
boolean serialHandled;
String inString;
unsigned long now;

/////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////
void loop()
{
	now = millis(); // returns unsigned long

	//
	//process trial and frame triggers
	if (newTrialTime > 0) {
		//serialOut(newTrialTime, "  newTrialTime", now);
		startTrial(newTrialTime);	
		newTrialTime = 0; //reset startTrial_ISR()
	}
	if (newFrameTime > 0) {
		//serialOut(newFrameTime, "  newFrameTime", now);
		newFrame(newFrameTime);	
		newFrameTime = 0; //reset frame_ISR()
	}

	if (forceStop) {
		forceStop = 0;
		stopTrial(now);
	}
	
	//
	//trial
	updateTrial(now);
		
  	//
  	//motor
  	updateMotor(now);
  	
	//
	//encoder
	newEncoderPos = myEncoder.read();
	updateEncoder(now, newEncoderPos);
	
	//
	//fakeScope.Update();	

	//
	//serial
	if (Serial.available() > 0) {
		inString = Serial.readStringUntil('\n');
		//serialHandled = fakeScope.SerialIn(now, inString);
		inString.replace("\n","");
		inString.replace("\r","");
		SerialIn(now, inString);
	}

} // loop()


