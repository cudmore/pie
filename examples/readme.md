## Uploading code to a Teensy

### Setting up a Teensy

 1. [Download][arduino-ide-download] and install the Arduino IDE.
 2. [Download][teensyduino] and install Teensyduino. 
 

### Required Libraries

When Teensyduino is installed, it will automatically install a number of Arduino libraries including the required libraries.

 - [AccelStepper][[accellstepper-library]]
 - [Encoder][encoder-library]

### Upload to Teensy using Arduino IDE

 - Open teensy_treadmill in the Arduino IDE
 - Make sure you select a Teensy board with menu 'Tools - Board'.
 - Make sure you choose the port where the Teensy is attached with menu 'Tools - Port'
 - Compile and upload code
 
## Processing

[Processing][processing] is an easy to use scripting language. It is particularly easy to interact with an Arduino/Teensy via serial.

### processing_serial

Processing sketch to interact with treadmill code on an Arduino/Teensy via serial

[processing]: http://processing.org
[arduino-ide-download: https://www.arduino.cc/en/Main/Software
[teensyduino]: https://www.pjrc.com/teensy/td_download.html
[accellstepper-library]: https://www.pjrc.com/teensy/td_libs_AccelStepper.html
[encoder-library]: https://www.pjrc.com/teensy/td_libs_Encoder.html