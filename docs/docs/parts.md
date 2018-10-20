[Jump to the actual parts list](#parts-list)

### Raspberry Pi

The [Raspberry Pi][raspberry-pi] is a complete computer system in an almost credit card size. It has ethernet, USB, general-purpose-input-output pins (GPIO), a dedicated camera port, and runs a version of Debian Linux called [Rasbian][raspbian]. You can pick up the current model, a [Raspberry Pi 3 Model B+][buy-raspberry-pi].

### Raspberry Pi Camera

The Raspberry Pi has a dedicated camera port for the Raspberry Pi Camera. This is an 8 megapixel camera capable of frame rates as high as 90 frames-per-second and comes in two flavors, the [Pi NOIR Camera][raspberry-pi-noir] which can capture images/video using infrared (IR) lights and the '[normal][raspberry-pi-camera]' camera which can capture images/video using visible (white) light. We generally use the [Pi NOIR][raspberry-pi-noir] version to record video in behavior boxes during both the daytime (white LEDs) and night-time (IR LEDs) as well as on the scope to record video during two-photon imaging in the dark using IR LEDs.

### Two channel relay

A [relay][relay] is a switch allowing you to turn higher voltage devices (usually LEDs connected to 12V power) on and off with 3V GPIO pins. We are using a [sainsmart 2-channel relay][sainsmart-relay].

### LEDs

If you end up with lots of LEDs, you could try an [IR LED strip](https://www.amazon.com/LightingWill-Non-waterproof-Multitouch-Application-IR850NM3528X300N/dp/B01DM9AT9C
) and/or a [white LED strip](https://www.sparkfun.com/products/12621).

### Level shifter

If you need to connect the Raspberry Pi directly to 5V TTL lab equipment you **need** a [level shifter][level-shifter] to convert the 5V signal to 3V as the Raspberry Pi is only 3V tolerant. We normally use [Adafruit](loginlevelconverter_adafruit) or [Sparkfun](loginlevelconverter_sparkfun) level shifters.


### Teensy microcontroller

We are using [Teensy 3.2 or 3.5][teensy] microcontrollers. They are Arduino compatible but have a lot more features. These microcontrollers can be programmed from the command line using [platformio][platformio], no need for the Arduino IDE. To use platformio, the Raspberry Pi needs a few simple system wide configurations, see the readme in [pie/platformio](platformio/). 

### Stepper motor and  driver

Use a [Bipolar stepper motor][steppermotor] with the [Easy Driver][easydriver] motor driver.

<A id="parts-list"></a>
## Parts List

Total cost for home-cage and/or on the scope video recording is around $200.

### For video recording

|Quatity	|Item	| Purpose |Cost	| Vendor Link
| -----		| -----	| -----	| -----	| -----
|1	|Raspberry Pi 3 Model B  | Computer system including computer, SD card, power, case, etc. etc. |$75	|[amazon](https://www.amazon.com/CanaKit-Raspberry-Complete-Starter-Kit/dp/B01C6Q2GSY)
|1	| USB Flash Drive, 64GB | To save recorded video | $17 | [amazon][usb-flash-drive]
|1	|Pi NoIR Camera v2, 8MP	 | IR video camera |$30	|[adafruit](https://www.adafruit.com/products/3100)
|1	|(either this) Pi Camera Ribbon cable (2 meters)	| Flat ribbon cable to connect camera to computer (not optimal) |$6	|[adafruit](https://www.adafruit.com/products/2144)
|1	|(or this 1/2) Pi Camera HDMI extension cable	| Allows camera to connect to computer using an HDMI cable |$15	|[tindie](https://www.tindie.com/products/freto/pi-camera-hdmi-cable-extension/)
|1	|(and this 2/2) HDMI Cable of sufficient length	| Male/Male HDMI cable | $7 - $15	| [amazon][hdmi-cable]	| 
|1	| SainSmart 2-Channel Relay Module | Allow computer to switch LEDs on/off | $9 | [amazon][two-channel-relay]
|>4	|IR LEDs, 840-850 nm	| Illuminate in light proof imaging box. Original v1 camera did not work well with 960nm LEDs, need to check v2 camera. |$1 each	|[sparkfun][irled_sparkfun]
|>1	|Universal 4-LED Miniature Wedge Base PCB	| To mount 4x LEDs + required resistor |$1 each	|[super-bright-led][super-bright-led-board]
|1	| 12V 2A LED Driver (does not come with wall plug)	| Power the IR LEDs | $12	| [amazon][led-driver]
| 1				| Ethernet cable	of sufficient length | Connect the computer to the network | $5 - $20	| [amazon][ethernet-cable]

### For video recording on a scope with triggering and frame clock

|Quatity	|Item	| Purpose |Cost	| Vendor Link
| -----		| -----	| -----	| -----	| -----
|1	|4-channel Logic Level Converter (Bi-Directional)	| To connect 5V TTL lab equipment to 3V computer GPIO |$4	|[Sparkfun][loginlevelconverter_sparkfun], [Adafruit][loginlevelconverter_adafruit]
| 1	| Tripod Swivel | To mount the camera on an optical post and be able to angle it. | $9 | [amazon][tripod-mount]

### Miscellaneous
|Quatity	|Item	| Purpose |Cost	| Vendor Link
| -----		| -----	| -----	| -----	| -----
| 1 	| Breadboard and jumper cables | A breadboard and a mixture of jumper cables: male/male, male/female, and female/female | $11 | [amazon][breadboard]
| 1	| Wire | To wire LEDs into light proof box | $17 | [sparkfun][sparkfun-wire]


### For controlling a motorized treadmill with a microcontroller

|Quatity	|Item	| Purpose |Cost	| Vendor Link
| -----		| -----	| -----	| -----	| -----
| 1			| Teensy 3.5	| Arduino compatible microcontroller	| $25	| [teensy][teensy35]
| 1			| EasyDriver - Stepper Motor Driver	| Motor controller for stepper motor	| $15 | [sparkfun][big-easy-driver]
| 1			| Stepper Motor | Share 12V 2A LED Driver for power | $15 | [sparkfun][stepper-motor]
| 1			| Rotary encoder	| Honeywell-600-128-CBL | $51 | [digi-key][rotary-encoder] or [this][rotary-encoder-2]

### Building a treadmill

These are **Actobotics** parts from [ServoCity][servocity]

|Quatity	|Item	|Cost	|Part #	|Link
| -----		| -----	| -----	| -----	| -----
|	|[**Aluminum channels**](https://www.servocity.com/html/aluminum_channel.html)	|	|	|[link](https://www.servocity.com/html/aluminum_channel.html)
|4	|1.50 inch Aluminum Channel	|2.99	|585440
|4	|6.00 inch Aluminum Channel	|5.99	|585446
|1	|9.00 inch Aluminum Channel	|7.99	|585450
|1	|15 inch Aluminum Channel	|11.99	|585458
|	|[**Shafts and shaft couplers**](https://www.servocity.com/html/shafting___tubing.html)	|	|	|[link](https://www.servocity.com/html/shafting___tubing.html)
|2	|1/4 inch x12 inch Precision Shaft	|3.59	|634178
|2	|1/4 inch x4 inch Precision Shaft	|1.49	|634164
|1	|1/4 inch x6 inch Precision Shaft	|2.09	|634168
|2	|1/4 inch to 5mm Set Screw Shaft Coupler	|4.99	|625120
|2	|1/4 inch to 1/4 inch Set Screw Shaft Coupler	|4.99	|625104
|	|[**Couplers and adapters**](https://www.servocity.com/html/hubs__couplers___adaptors.html)	|	|	|[link](https://www.servocity.com/html/hubs__couplers___adaptors.html)
|8	|1/4 inch Bore Clamping Hub (0.770 inch)	|7.99	|545588	
|4	|1/4 inch Bore Set Screw Hub (0.770 inch)	|4.99	|545548
|2	|Stepper Motor Mount (NEMA 17)	|7.49	|555152
|4	|1/4-20 Round Screw Plate	|3.99	|545468
|2	|Large Square Screw Plate	|2.69	|585430
|1	|90 Degree Quad Hub Mount C	|5.99	|545360
|1	|90 Degree Quad Hub Mount D	|5.99	|545324
|	|[**Ball bearings**](https://www.servocity.com/html/bearings___bushings.html)	|	|	|[link](https://www.servocity.com/html/bearings___bushings.html)
|3	|.250 inch ID x .500 inch OD Flanged Ball Bearing (Stainless Steel) 2 pack	|1.99	|535198
|1	|Dual Ball Bearing Hub A	|6.99	|545444
|1	|1/4 inch Shafting & Tubing Spacers (12 pk)	|1.69	|633104
|	|[**Gears**](https://www.servocity.com/html/gears.html)	|	|	|[link](https://www.servocity.com/html/gears.html)
|1	|16T, 0.250 inch Bore, 32P Bevel Gear	|5.99	|615442
|1	|32T, 0.250 inch Bore, 32P Bevel Gear	|7.99	|615444
|1	|16T, 5mm Bore, 32P Bevel Gear	|5.99	|615438
|2	|48 Tooth, 32 Pitch Hub Gear (3/16 inch Face)	|5.20	|RHA32-36-48
|	|[**Fasteners**](https://www.servocity.com/html/fasteners___hardware1.html)	|	|	|[link](https://www.servocity.com/html/fasteners___hardware1.html)
|24	|6-32x3/8 inch Pan Head Phillips Machine Screws (Zinc-Plated)	|0.06	|90272A146
|8	|1/2 inch 1/4-20 Flat Head Phillips Machine Screws	|0.38	|90273A537
|1	|3/32 Hex Key	|1.39	|57185A11
|6	|.250 in L x 6-32 Zinc-Plated Alloy Steel Socket Head Cap Screw (25 pk)	|1.69	|632106


[super-bright-led-board]: https://www.superbrightleds.com/moreinfo/resistors/universal-4-led-miniature-wedge-base-pcb-mled-pcb/403/1387/
[irled_sparkfun]: https://www.sparkfun.com/products/9469
[loginlevelconverter_sparkfun]: https://www.sparkfun.com/products/12009
[loginlevelconverter_adafruit]: https://www.adafruit.com/products/757
[hdmi-cable]: https://www.amazon.com/AmazonBasics-High-Speed-HDMI-Cable-1-Pack/dp/B014I8SSD0/ref=sr_1_1?s=aht&srs=10112675011&ie=UTF8&qid=1537972136&sr=1-1
[led-driver]: https://www.amazon.com/dp/B016FG9KWQ/ref=sspa_dk_detail_6?psc=1
[ethernet-cable]: https://www.amazon.com/AmazonBasics-RJ45-Cat-6-Ethernet-Patch-Cable-25-Feet-7-6-Meters/dp/B00N2VIWPY/ref=sr_1_1_sspa?s=hi&ie=UTF8&qid=1537972791&sr=1-1-spons&keywords=ethernet&psc=1
[usb-flash-drive]: https://www.amazon.com/SanDisk-Ultra-Flash-Drive-SDCZ43-032G-GAM46/dp/B01BGTG3JA/ref=sr_1_22?s=pc&ie=UTF8&qid=1537973231&sr=1-22&keywords=usb%2Bkey&th=1
[two-channel-relay]: https://www.amazon.com/SainSmart-101-70-100-2-Channel-Relay-Module/dp/B0057OC6D8/ref=sr_1_1?ie=UTF8&qid=1509654257&sr=8-1&keywords=sainsmart+2-channel+relay+module&dpID=51eyw8a9hKL&preST=_SY300_QL70_&dpSrc=srch
[tripod-mount]: https://www.amazon.com/UTEBIT-Aluminum-Ballhead-Compatible-Recorder/dp/B06XKW7V14/ref=sr_1_17?s=electronics&ie=UTF8&qid=1537974250&sr=1-17&keywords=tripod+mount
[sparkfun-wire]: https://www.sparkfun.com/products/11375
[breadboard]: https://www.amazon.com/Breadboard-Solderless-Prototype-Male-Female-Female-Female/dp/B073X7GZ1P/ref=sr_1_1_sspa?s=electronics&ie=UTF8&qid=1537975002&sr=1-1-spons&keywords=breadboard+400&psc=1
[teensy35]: https://www.pjrc.com/store/teensy35.html
[big-easy-driver]: https://www.sparkfun.com/products/12779
[stepper-motor]: https://www.sparkfun.com/products/9238
[rotary-encoder]: https://www.digikey.com/product-detail/en/600128CBL/600CS-ND/53504
[rotary-encoder-2]: https://www.digikey.com/product-detail/en/honeywell-sensing-and-productivity-solutions/600128CN1/480-5967-ND/4381908
[servocity]: http://servocity.com

[raspberry-pi]: https://www.raspberrypi.org/
[buy-raspberry-pi]: https://www.raspberrypi.org/products/
[buy-noir]: https://www.adafruit.com/product/3100?src=raspberrypi
[raspbian]: https://www.raspberrypi.org/downloads/raspbian/
[raspberry-pi-noir]: https://www.raspberrypi.org/products/pi-noir-camera-v2/
[raspberry-pi-camera]: https://www.raspberrypi.org/products/camera-module-v2/
[level-shifter]: https://en.wikipedia.org/wiki/Level_shifter
[relay]: https://en.wikipedia.org/wiki/Relay
[steppermotor]: https://www.sparkfun.com/products/9238
[easydriver]: https://www.sparkfun.com/products/12779
[sainsmart-relay]: https://www.amazon.com/SainSmart-101-70-100-2-Channel-Relay-Module/dp/B0057OC6D8
[teensy]: https://www.pjrc.com/teensy/
[platformio]: https://platformio.org/
