#from treadmill_app import app
import treadmill_app

if __name__ == "__main__":
	#app.run()
	#app = treadmill_app.app
	
	debug = False
	treadmill_app.socketio.run(treadmill_app.app, host='0.0.0.0', debug=debug)
