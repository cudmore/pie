## Assuming platformio.ini looks like this

	[env:teensy31]
	platform = teensy
	board = teensy31
	framework = arduino

	[env:teensy35]
	platform = teensy
	board = teensy35
	framework = arduino

The next commands assume you have installed platformio using `~pie/platformio/install-platformio` and the Python 2 virtual environment is in `~/pie/platformio/env`.

## Upload to teensy 3.1/3.2

	sudo ../env/bin/platformio run -e teensy31 --target upload

## Upload to teensy 3.5

	sudo ../env/bin/platformio run -e teensy35 --target upload

## Clean teensy 3.1/3.2

	sudo ../env/bin/platformio run -e teensy31 --target clean

## Clean teensy 3.5

	sudo ../env/bin/platformio run -e teensy35 --target clean