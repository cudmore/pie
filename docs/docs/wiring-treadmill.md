# Wiring a treadmill

## Upload code to a Teensy

Please refer to the [pie/platformio][platformio-folder] readme. The Arduino/Teensy code is in [pie/platformio/treadmill/src/treadmill2.cpp][treadmill2].

## Parts

See the main [parts](parts.md) page, scroll down to the treadmill section.

## Wiring

This is a full wiring diagram for microscope triggered video recording and using a Teensy with a motorized treadmill. To just wire a Raspberry Pi to a scope, please see the [scope wiring tutorial](wiring-scope.md). This wiring diagram is made with [Fritzing][fritzing], download the [pie.fzz](../img/pie.fzz) file.

 - Wire the Teensy  to `Scope Trigger In`, `Scope Trigger Out`, and `Scope Frame out`.
 - Wire the Teensy to the Raspberry Pi
 - Wire the stepper motor to the motor controller.
 - Wire the motor controller to the Raspberry Pi

<IMG SRC="../img/pie_fritzing.png">

### Important

 - The Raspberry Pi is **NOT** 5V tolerant. Connecting standard lab equipment using 5V TTL pulses can damage the Pi. These 5V lines can be converted to 3V with a [dedicated level shifter][adafruit-level-shifter]. Or, if you are using a Teensy, these 5V lines can pass through the Teensy which **IS** 5V tolerant but then outputs 3V which can go into the Raspberry Pi. In this way, the Teensy can act as a programmable [level shifter][level-shifter].

 - The [Easy Driver][easy-driver] Motor Driver has a nasty feature. If you connect the 12V line to the board, the Stepper motor **must** be plugged in or else you will fry the driver board. Thus, check the stepper motor is connected before plugging in the 12V line and check the 12V line is not plugged in before disconnecting the stepper motor.


### Pin table

This table shows all the pin connections for the full treadmill system (option #4). To wire a Raspberry Pi to a scope without a Teensy (option #3), make sure you connect the Raspberry Pi `triggerOut`, `frame`, and `triggerIn` pins to a level-shifter and then to the scope. See the [scope wiring tutorial](wiring-scope.md) for details.

[Download pdf](../img/pie_pins.pdf) of this table.

|   |  | **Scope** | **Other Devices** | **Raspberry** |  |  |  |  | **Teensy** |  |  |  |  | **Motor Controller** |  |
|  ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ |
|  **Category** | **Ground** | **Description** |  | **Description** | **Config FIle** | **Pin #** | **Input** | **Output** | **Description** | **Config FIle** | **Pin #** | **Input** | **Output** | **Pin** |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  Raspberry Ground | X |  |  | Gnd |  | Gnd |  |  |  |  |  |  |  |  |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  Scope Ground | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  Scope Trigger In |  | Trigger In (5V) |  | triggerOut | hardware.eventOut[0].pin | 15 |  | X | startTrialPin | treadmill.cpp | 3 | X |  |  |  |
|  Scope Trigger Out |  | Trigger Out (5V) |  |  |  |  |  |  | extTriggerInPin | treadmill.cpp | 8 | X |  |  |  |
|   |  |  |  | triggerIn | hardware.eventIn[0].pin | 24 | X |  | passThroughExtTriggerInPin | treadmill.cpp | 9 |  | X |  |  |
|  Scope Frame Out |  | Frame Out (5V) |  |  |  |  |  |  | framePin | treadmill.cpp | 5 | X |  |  |  |
|   |  |  |  | frame | hardware.eventIn[1].pin | 23 | X |  | passThroughFramePin | treadmill.cpp | 6 |  | X |  |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  LEDs |  |  | LED 1 (+) | whiteLED | hardware.eventOut[1].pin | 19 |  | X |  |  |  |  |  |  |  |
|   | X |  | LED 1 (-) |  |  |  |  |  |  |  |  |  |  |  |  |
|   |  |  | LED 2 (+) | irLED | hardware.eventOut[2].pin | 18 |  | X |  |  |  |  |  |  |  |
|   | X |  | LED 2 (-) |  |  |  |  |  |  |  |  |  |  |  |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  DHT Sensor |  |  | data (yellow) | dhtSensor | hardware.dhtSensor.pin | 4 | X |  |  |  |  |  |  |  |  |
|   |  |  | 5V (red) |  |  | 5V |  |  |  |  |  |  |  |  |  |
|   | X |  | Gnd (black) |  |  |  |  |  |  |  |  |  |  |  |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  Stepper Motor | X |  |  |  |  |  |  |  |  |  |  |  |  | Gnd |  |
|   |  |  |  |  |  |  |  |  | motorStepPin | treadmill.cpp | 17 |  | X | Step |  |
|   |  |  |  |  |  |  |  |  | motorDirPin | treadmill.cpp | 16 |  | X | Dir |  |
|   |  |  |  |  |  |  |  |  | motorResetPin | treadmill.cpp | 19 |  | X | RST |  |
|   |  |  |  |  |  |  |  |  | motorEnabledPin | treadmill.cpp | 20 |  | X | Enable |  |
|   |  |  |  |  |  | 5V |  |  |  |  |  |  |  | 5V (+) |  |
|   | X |  |  |  |  |  |  |  |  |  |  |  |  | Gnd |  |
|   |  |  | 12V DV (+) |  |  |  |  |  |  |  |  |  |  | PWR In (M+) |  |
|   | X |  | 12V DC (Gnd) |  |  |  |  |  |  |  |  |  |  | PWR In (Gnd) |  |
|   |  |  |  | arduinoMotor | hardware.eventIn[2].pin | 8 | X |  | motorOnPin | treadmill.cpp | 11 |  | X |  |  |
|   |  |  |  | arduinoNewEpoch | hardware.eventIn[3].pin | 7 | X |  | newEpochPin | treadmill.cpp | 12 |  | X |  |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  Rotary Encoder |  |  | Encoder 1 |  |  |  |  |  | encoderPinA | treadmill.cpp | 15 | X |  |  |  |
|   |  |  | Encoder 1 |  |  |  |  |  | encoderPinB | treadmill.cpp | 16 | X |  |  |  |
|   |  |  | Encoder 1 (+5V) |  |  |  |  |  |  |  | 5V |  |  |  |  |
|   | X |  | Encoder 1 (Gnd) |  |  |  |  |  |  |  |  |  |  |  |  |
|   |  |  |  |  | ??? |  | X |  | encoderOutPin | treadmill.cpp | 10 |  | X |  |  |
|   |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  Emergency Stop Button |  |  | Push button (+3V) | ??? | ??? | ??? | X |  | emergencyStopPin | treadmill.cpp | 20 | X |  |  |  |
|   | X |  | Push button (Gnd) |  |  |  |  |  |  |  |  |  |  |  |  |

[fritzing]: http://fritzing.org/home/
[adafruit-level-shifter]: https://www.adafruit.com/product/757
[level-shifter]: https://en.wikipedia.org/wiki/Level_shifter
[easy-driver]: https://www.sparkfun.com/products/12779
[treadmill2]: https://github.com/cudmore/pie/blob/master/platformio/treadmill/src/treadmill2.cpp
[platformio-folder]: https://github.com/cudmore/pie/tree/master/platformio