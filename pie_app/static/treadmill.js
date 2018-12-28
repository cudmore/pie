// Robert Cudmore
// 20180601

// Factory
//		statusFactory
// Controller
//		configFormController
//			has CallParentMethod to be called when other controlers (e.g.  arduinoFormController) modify config
//		arduinoFormController
//		treadmill

var app = angular.module('demo', ['uiSwitch', 'ngRoute']);

///
///
/*
var socket = io.connect('http://192.168.1.15:5010');
socket.on('connect', function() {
    // we emit a connected message to let knwo the client that we are connected.
    console.log('socket.on connect')
    socket.emit('client_connected', {data: 'New client!'});
    console.log('2 socket.on connect')
});

socket.on('my_response', function(msg) {
	console.log('socket.on my_response msg:', msg)


        	    //console.log('msg.status:', msg.status)
        	    $scope.status = msg.status;
				// for armed checkbox, it needs a model
				$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
				
				//for streaming
				var tmpWidth = parseInt($scope.status.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.status.trial.config.video.streamResolution.split(',')[1],10)
				$scope.streamWidth = tmpWidth + (tmpWidth * 0.04)
				$scope.streamHeight = tmpHeight + (tmpWidth * 0.04)

				// for recording
				$scope.lastImage = $scope.myUrl + 'api/lastimage' + '?' + new Date().getTime()
				//console.log('$scope.lastImage:', $scope.lastImage)
				
				//$rootScope.$emit("CallParentMethod", {});
				//console.log('$scope.status:', $scope.status)
				//$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
				//if ( $scope.status.runtime.xxxChange) {
				//}
				//console.log('xxx $scope.configData:', $scope.configData)
				$rootScope.$emit("CallParentMethod_SetConfigData", msg.status);

				$route.reload();
});
*/
///
///

//////////////////////////////////////////////////////////////////////////////
app.factory('statusFactory', function($http, $location, $interval) {
	var myUrl = $location.absUrl(); //with port :5000
	var getStatus = function () {
		var url = myUrl + 'status'
		return $http.get(url).
        	then(function(response) {
				//console.log('statusFactory status=', response.data)
				return response.data
        	});
    };
    return {getStatus: getStatus}
});

//////////////////////////////////////////////////////////////////////////////
// change parameters in config json file
app.controller('configFormController', function($scope, $rootScope, $http, $interval, $route, statusFactory) {

    // call this from other controllers to update new values from server
    //removed
    //removed this and now updating at an interval from main controller
    /*
    $rootScope.$on("CallParentMethod", function() {
        //console.log('in CallParentMethod:')
        $scope.getPromise();
    });
	*/

	//console.log('angular.version:', angular.version)
	
    //called from main controller at an interval
    $rootScope.$on("CallParentMethod_SetConfigData", function(event, thisConfig) {
        //console.log('CallParentMethod_SetConfigData thisConfig:', thisConfig)
        $scope.configData = thisConfig
        
        if ($scope.configData.trial.runtime.cameraState == 'armed' || $scope.configData.trial.runtime.cameraState == 'armedrecording') {
        	//20180718, get this working
        	//console.log('CallParentMethod_SetConfigData() is calling $route.reload()')
        	
        	// this gets called at an interval (very expensive for Pi to be serving this)
        	//console.log('$rootScope.$on("CallParentMethod_SetConfigData" is calling $route.reload')
        	$route.reload();
        }
        
    });
	
    //
    // save and load config files
    $scope.saveConfig = function() {
        //console.log('saveConfig()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/saveconfig'
        //console.log('$scope.configData:', $scope.configData.trial.config)
        $http.get(url).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        	});
    };

    $scope.loadConfig = function(loadThis) {
        console.log('loadConfig()', loadThis);
        url = $scope.myUrl + 'api/submit/loadconfig/' + loadThis
        //console.log('$scope.configData:', $scope.configData.trial.config)
        $http.get(url).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        		// update values in table
        		//$scope.configData = result	
        		//$scope.getPromise()
        		
        		//removed
        		//$rootScope.$emit("CallParentMethod", {}); //CallParentMethod calls getPromise()
    	},
    	function(data) {
    	    // Handle error here
    	    console.log('loadConfig http error')
        });
    };

    //
    // submit changes to backend server
    $scope.submitConfigForm = function() {
        console.log('submitConfigForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/configparams'
        //console.log('$scope.configData:', $scope.configData.trial.config)
        $http.post(url, JSON.stringify($scope.configData.trial.config)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        		//$scope.getPromise();
        	});
    };
    
    $scope.submitPinForm = function() {
        console.log('submitPinForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/pinparams'
        //console.log('$scope.configData:', $scope.configData.trial.config)
        $http.post(url, JSON.stringify($scope.configData.trial.config)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        		//$scope.getPromise();
        	});
    };
    
    $scope.submitAnimalForm = function() {
        console.log('submitAnimalForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/animalparams'
        //console.log('$scope.configData:', $scope.configData.trial.config)
        $http.post(url, JSON.stringify($scope.configData.trial.config)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        		//$scope.configData = response.data
        	});
    };
    
    //
    // roll each of these into one function, e.g. merge animalParamChange and submitAnimalForm
    $scope.animalParamChange = function(isValid) {
    	// if form fields don't pass validation, they will be 'undefined'
    	//console.log('animalParamChange()', 'isValid:', isValid, $scope.configData)
    	if (isValid) {
    		$scope.submitAnimalForm()
    	}
    }
    
    // called on each change of a config parameter (keystroke, tab, enter)
    $scope.configParamChange = function(isValid) {
    	// if form fields don't pass validation, they will be 'undefined'
    	//console.log('configParamChange()', 'isValid:', isValid, $scope.configData)
    	if (isValid) {
    		$scope.submitConfigForm()
    	} else {
    		//console.log('no action taken')
    	}
    }
    
    $scope.pinParamChange = function(isValid) {
    	// if form fields don't pass validation, they will be 'undefined'
    	//console.log('configParamChange()', 'isValid:', isValid, $scope.configData)
    	if (isValid) {
    		$scope.submitPinForm()
    	}
    }
    
	//
	// get data from the server
// not used -->> remove
	$scope.getPromise = function() {
		//console.log('getPromise')
		var  myPromise = statusFactory.getStatus()
    	myPromise.then(function(result) {
			
			//console.log('getPromise() then clause')
			$scope.configData = result				
    		
    		//$route.reload();
    		//$rootScope.$emit("CallParentMethod", {});
    		
    		//console.log('getPromise() got $scope.configData')
    		//console.log($scope.configData)
    	},
    	function(data) {
    	    // Handle error here
    	    console.log('configFormController error in myPromise')
		}); // mypromise.then
	}
	
	//$scope.getPromise()
	//$interval($scope.getPromise, 400); // no () in function call !!!	
	
}); // configFormController



//////////////////////////////////////////////////////////////////////////////
// controller for motor
app.controller('arduinoFormController', function($scope, $rootScope, $http, statusFactory) {
    
    // take current params and submit
    $scope.submitForm = function() {
        console.log("posting data....", $scope.data, $scope.data.$valid);
        url = $scope.myUrl + 'api/submit/motorparams'
        $http.post(url, JSON.stringify($scope.data)).
        	then(function(response) {
			    // call the other controller with this
			    //This updates configFormController configData from server again
			    
			    //removed
			    //$rootScope.$emit("CallParentMethod", {});
			    
			    // html code has ng-form arduinoForm
			    $scope.arduinoForm.$setPristine();
        	});
    };
    
    // 20181220
	//$scope.$on('someEvent', function(event, args) {
	/*
	$scope.$on('someEvent', function(event, data) {
		//args is secondsElapsedStr
		console.log('arduinoFormController received someEvent')
		//$scope.refreshPlotly(args);
	});
	*/
	
	//
	//
	//
	//
	//
	//
	//
	//
	// THIS IS FUCKING IMPOSSIBLE TO GET WORKING
	// I CAN NOT DEAL WITH THESE JAVASCRIPT FRAMEWORKS !!!!!!!!!!!!!!!!!
	// THEY MAKE MY CODING STALL FOR DAYS AND WEEKS
	// COME ON GOOD AND FACEBOOK, THIS IS FUCKING BULLSHIT
	//
	//
	//
	//
	//
	//
	//
	//
	//
	
	/*
	$rootScope.$on("rootEvent", function(event, thisConfig) {
		console.log('arduinoFormController received rootEvent')
	})
	$scope.$on("rootEvent", function(event, thisConfig) {
		console.log('arduinoFormController received rootEvent')
	})
	*/
	
	$scope.$on('rootEvent2', function (event, secondsElapsedStr) {        
			console.log('I am from motor controller', secondsElapsedStr);
			var msElapsed = parseFloat(secondsElapsedStr) * 1000;
			Plotly.restyle('test_plotly', 'x', [[msElapsed, msElapsed]]);
		});
	
	/*
	$scope.$on('rootEvent', function(event, data){
		console.log('arduinoFormController received rootEvent')
	})
	$rootScope.$on('rootEvent', function(event, data){
		console.log('arduinoFormController received rootEvent')
	})
	*/
	
	//rebuild plotly but do not submit
    $scope.motorParamChange = function() {
    	// if form fields don't pass validation, they will be 'undefined'
    	console.log('motorParamChange()', $scope.data)
    	buildPlotly($scope.data)
    }
    
    // respond to new secondsElapsedStr
    /*
    $scope.updateRuntime - function() {
    	// Plotly.react(gd, data, layout, config)
    	//buildPlotly($scope.data) //$scope.data is motorParams
    	$scope.refreshPlotly($scope.status)
    }
    */
    
    var myPromise = statusFactory.getStatus()
    myPromise.then(function(result) {
    	var status = result
    	console.log('arduinoFormController myPromise:', status)

		// motorParams
		// remember, repeatDuration is in seconds, repeatduration is in ms
		// todo: clean up numberofrepeats versus numberOfRepeats
		
		// this is coming from config.json file.
		// we want to be very careful NOT to modify its field names
		$scope.data = status.trial.config.motor;
		
		buildPlotly($scope.data)
		
	}); // mypromise.then

    // respond to new secondsElapsedStr
	$scope.refreshPlotly = function(status) {
		console.log('refreshPlotly()')
	}
	
	var buildPlotly = function(motorParams){
		var trialMS = motorParams.motorNumEpochs * motorParams.motorRepeatDuration
		//console.log('buildPlotly() trialMS:', trialMS)
		//console.log('buildPlotly() motorParams:', motorParams)
		
		//
		// plotly
		var d3 = Plotly.d3;
		var WIDTH_IN_PERCENT_OF_PARENT = 100
		var HEIGHT_IN_PERCENT_OF_PARENT = 12;

		  var gd3 = d3.select("#test_plotly")
			  .style({
				width: WIDTH_IN_PERCENT_OF_PARENT + '%',
				//'margin-left': (100 - WIDTH_IN_PERCENT_OF_PARENT) / 2 + '%',
		
				height: HEIGHT_IN_PERCENT_OF_PARENT + 'vh',
				//'margin-top': (100 - HEIGHT_IN_PERCENT_OF_PARENT) / 2 + 'vh'
			  });

		var gd = gd3.node();

		var data = [
		  {
			x: [100,100],
			y: [0, 1],
			type: 'scatter'
		  }
		];

		var lineColor = 'rgba(100,100,100,1)'
		
		// make a list of rect shapes, one per epoch/repeat
		var i
		var shapeList = []
		for (i=0; i<motorParams.motorNumEpochs; i++) {
			thisStart = motorParams.motorRepeatDuration * i + motorParams.motorDel
			thisStop = thisStart + motorParams.motorDur
			thisRect = {
				'type': 'rect',
				'x0': thisStart,
				'y0': 0,
				'x1': thisStop,
				'y1': 1,
				'line': {
					'color': lineColor,
				},
				'fillcolor': lineColor,
				opacity: 0.5,
			};
			shapeList.push(thisRect)
		}
		
		var layout = {
		  showlegend: false,
		  margin: {
			l: 25,
			t: 25,
			r: 25,
			b: 40,
			pad: 4,
		  },
		  'xaxis': {
		  	'range': [0, trialMS],
		  	'zeroline': false,
		  	'title': 'ms'
		  },
		  'yaxis': {
		  	'showticklabels': false,
		  	//'zeroline': false,
		  	'showline': false,
		  	'showgrid': false,
		  	'ticks': '',
		  	'showticklabels': false,
		  	'range': [0, 1],
		  },
		  //paper_bgcolor: '#7f7f7f',
		  //plot_bgcolor: '#c7c7c7',
		'shapes': shapeList,
		};
		
		var config = {
    	    'displayModeBar': false
	    }

		Plotly.plot(gd, data, layout, config)
		// todo: seperate new lpot from update plot
		// this is for when we update
		Plotly.react(gd, data, layout, config)
		
		window.onresize = function() {
			Plotly.Plots.resize('test_plotly');
		};

	}; // $scope.buildPlotly
}); // arduinoFormController

//////////////////////////////////////////////////////////////////////////////
app.controller('exitController', function($scope, $window) {
    $scope.onExit = function() {
		console.log('user is closing tab')
		sleep(5000)
		//if ($scope.isstate('streaming')) {
		
				console.log('user is closing tab and stream is running -->> stop it')
				url = $scope.myUrl + 'api/action/' + 'stopStream'
				console.log(url)
				sleep(5000)
				$http.get(url).
    		    	then(function(response) {
        				// window/tab has been closed, do nothing
        				//$scope.status = response.data;
        			});
      	//}
      	return ('bye bye');
    };

   $window.onbeforeunload =  $scope.onExit;

   var leavingPageText = "xxx You'll lose your changes if you leave xxx";
    window.onbeforeunload = function(){
        console.log('in window.onbeforeunload')
        return leavingPageText;
    }

    $scope.$on('$locationChangeStart', function(event, next, current) {
        if(!confirm(leavingPageText + "\n\nxxx Are you sure you want to leave this page? xxx")) {
            event.preventDefault();
        }
    });

  });

//////////////////////////////////////////////////////////////////////////////
app.controller('treadmill', function($scope, $rootScope, $window, $http, $location, $interval, $route, $sce, $timeout, $document) {
	
	//console.log('angular.version:', angular.version)
	
	$scope.myUrl = $location.absUrl(); //with port :5000
	console.log('$scope.myUrl:', $scope.myUrl)
	
	document.title = 'PiE ' + $location.host()
	
    myStreamUrl = 'http://' + $location.host() + ':8080/stream';
    $scope.myStreamUrl0 = myStreamUrl
    $scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
	
	$scope.showConfig = false;
	$scope.showPins = false;
	$scope.showMotor = false;
	$scope.showDebug = true;
	$scope.showConfigTable = false;
	$scope.showLastImage = false;
	//$scope.allowArming = false;
	
	//$scope.isArmed = false;
	
    //read the state from homecage backend, do this at an interval
    $scope.getStatus = function () {
		$http.get($scope.myUrl + 'status').
        	then(function(response) {
        	    $scope.status = response.data;
				// for armed checkbox, it needs a model
				//$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
				
				//console.log('after status $scope.isArmed:', $scope.isArmed)
				//console.log('$scope.status.trial.runtime.cameraState:', $scope.status.trial.runtime.cameraState)

				//for streaming
				var tmpWidth = parseInt($scope.status.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.status.trial.config.video.streamResolution.split(',')[1],10)
				$scope.streamWidth = tmpWidth + (tmpWidth * 0.04)
				$scope.streamHeight = tmpHeight + (tmpWidth * 0.04)

				// for recording
				$scope.lastImage = $scope.myUrl + 'api/lastimage' + '?' + new Date().getTime()
				//console.log('$scope.lastImage:', $scope.lastImage)
				
				//$rootScope.$emit("CallParentMethod", {});
				//console.log('$scope.status:', $scope.status)
				//$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
				//if ( $scope.status.runtime.xxxChange) {
				//}
				//console.log('xxx $scope.configData:', $scope.configData)
				$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
				
				// turn of interval updates that call REST
				$scope.setInterval($scope.status.trial.runtime.cameraState)
				
        	});
	};

    // mixing controllers, this submits main $scope.config
    $scope.submitLEDForm = function() {
        //console.log('submitLEDForm() $scope.status.trial.config:', $scope.status.trial.config.hardware.eventOut);
        url = $scope.myUrl + 'api/submit/ledparams'
        $http.post(url, JSON.stringify($scope.status.trial.config)).
        	then(function(response) {
        		$scope.status = response.data
        		//console.log('$scope.status:', $scope.status)
        	});
    };
    
	// new 20181225
	$scope.hardCloseStream = 0
	function callStreamAtTimeout() {
		console.log("callStreamAtTimeout()");
		if ($scope.hardCloseStream) {
			console.log('hardCloseStream')
			$scope.myStreamUrl = ''
		} else {
			myStreamUrl = 'http://' + $location.host() + ':8080/stream' + '?' + new Date().getTime()
			$scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
		}
	}

	// one button callback
	$scope.buttonCallback = function(buttonID) {
		console.log('buttonCallback() buttonID=', buttonID)
		switch (buttonID) {
			case 'startRecord':
			case 'stopRecord':
			case 'startStream':
			case 'stopStream':
			case 'startArmVideo':
			case 'stopArmVideo':
				
		        // new 20181225
				// try and get stream to always show on first click
				if (buttonID == 'startStream') {
					$scope.hardCloseStream = 0;
				}
				if (buttonID == 'stopStream') {
					$scope.hardCloseStream = 1;
					callStreamAtTimeout();
				}
				
				// was this 20181225
				url = $scope.myUrl + 'api/action/' + buttonID
				$http.get(url).
    		    	then(function(response) {
        				$scope.status = response.data;
        				
        				//$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
						//$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
 						//$route.reload();
						//console.log('$scope.isArmed:', $scope.isArmed)
       				
        				$scope.setInterval($scope.status.trial.runtime.cameraState)
        			});

		        // new 20181225
		        //refresh stream
				if (buttonID == 'startStream') {
					//callAtTimeout()
					// give strem some time to refresh after rest call???
					$timeout(callStreamAtTimeout, 3000);
				}

				break;
			case 'toggleArm':
				if ($scope.isState('armed')) {
					console.log('button callback toggleArm armed')
					url = $scope.myUrl + 'api/action/stopArm'
					$http.get(url).
							then(function(response) {
								$scope.status = response.data;

								//$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
								
								//$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
								//$route.reload();

								//console.log('after stopArm $scope.isArmed:', $scope.isArmed)
								//console.log('$scope.status.trial.runtime.cameraState:', $scope.status.trial.runtime.cameraState)
								
								// start javascript counter
								//setTimeout(myTimeoutFunction, 5000);
								//interval = setInterval(myIntervalFunction, 5000);
								//$scope.setInterval($scope.status.trial.runtime.cameraState)
							});
				} else if ($scope.isState('idle')) { //safety check, index interface should handle
					console.log('button callback toggleArm idle')
					url = $scope.myUrl + 'api/action/startArm'
					$http.get(url).
							then(function(response) {
								console.log('response.data.trial.runtime.cameraState:', response.data.trial.runtime.cameraState)
								$scope.status = response.data;
								
								//$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
								
								//$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
								//$route.reload();
								
								//console.log('after startArm $scope.isArmed:', $scope.isArmed)
								//console.log('$scope.status.trial.runtime.cameraState:', $scope.status.trial.runtime.cameraState)
								
								// start javascript counter
								//setTimeout(myTimeoutFunction, 800);
								//interval = setInterval(myIntervalFunction, 800);
								//$scope.setInterval('startArm')
								
								//removed
								//$scope.setInterval($scope.status.trial.runtime.cameraState)
							});
				}
				break;
			default:
				console.log('buttonCallback() case not taken, buttonID=',buttonID);
				break;
		}
	}
	
	$scope.isState = function(state) {
		if ($scope.status) {
			return $scope.status.trial.runtime.cameraState == state
		} else {
			return ''
		}
	}
	
	$scope.allowParamEdit = function() {
		return $scope.isState('idle')
	}
	
	/*
	$scope.getLastImage2 = function () {
		$scope.lastImage2 = $scope.myUrl + 'api/lastimage' + '?' + new Date().getTime()
	}
	*/
	
	// reduce this to improve GPIO frame in????
	//$interval($scope.getStatus, 400); // no () in function call !!!	
	//$interval($scope.getStatus, 800); // no () in function call !!!	
	$scope.getStatus()

	///////////////////////////////////////////////////////////////////////////
	// counter to display elapsed recording time rather than hitting REST with http.get
	// this is used while we are acquiring data, VERY IMPORTANT
	var defaultInterval = 800; // 800
	var counter = 0;
	$scope.myIntervalFunction = function(){
		clearInterval(interval);
		//console.log('myIntervalFunction counter:', counter)
		//interval = setInterval(myIntervalFunction, counter);
		counter += 0.4
		counter = Math.round(counter * 100) / 100
		$scope.status.trial.runtime.secondsElapsedStr = counter
		
		//
		//
		//
		//
		//
		//
		//
		//
		// THIS IS FUCKING IMPOSSIBLE TO GET WORKING
		// I CAN NOT DEAL WITH THESE JAVASCRIPT FRAMEWORKS !!!!!!!!!!!!!!!!!
		// THEY MAKE MY CODING STALL FOR DAYS AND WEEKS
		// COME ON GOOD AND FACEBOOK, THIS IS FUCKING BULLSHIT
		//
		//
		//
		//
		//
		//
		//
		//
		//

		// see: https://stackoverflow.com/questions/9293423/can-one-angularjs-controller-call-another
		// 20181220, update plot of motor !!!
		//$scope.refreshPlotly($scope.status)
		
		// emit an update (for motor controller)
		//$rootScope.$broadcast('someEvent', $scope.status.trial.runtime.secondsElapsedStr);
		
		//broadcast from rootScope and receive on $scope, this is fucking confusing
		//console.log('emit someEvent', $scope.status.trial.runtime.secondsElapsedStr)
		//$rootScope.$broadcast('someEvent', $scope.status.trial.runtime.secondsElapsedStr);
		
		console.log('emit rootEvent', $scope.status.trial.runtime.secondsElapsedStr)
		//$rootScope.$broadcast('rootEvent', 'Hello from the rootScope!'); 
		//$rootScope.$emit("rootEvent", 'Hello from the rootScope!'); 
		$rootScope.$broadcast("rootEvent2", $scope.status.trial.runtime.secondsElapsedStr); 
		//$scope.$broadcast('rootEvent', 'Hello from the rootScope!'); 
		//$scope.$emit('rootEvent', 'Hello from the rootScope!'); 
		
		//$scope.$emit('someEvent', $scope.status.trial.runtime.secondsElapsedStr);
		// this will be captured/responded in motor controller with
		// motor controller repsonds with
		//$scope.$on('someEvent', function(event, args) {});
	}

	$scope.setInterval = function(state) {
		//console.log('setInterval()', state)
		$interval.cancel(interval);
		if (state == 'armedrecording') {
			counter = 0
			interval = $interval($scope.myIntervalFunction, 400);
		} else {
			interval = $interval($scope.getStatus, defaultInterval);
		}
	}

	var interval = $interval($scope.getStatus, defaultInterval);

	///////////////////////////////////////////////////////////////////////////
	// SOCKETIO
	//var socket = io.connect($scope.myUrl);

	///
	///
    angular.element(document).ready(function () {

		//var socket = io.connect('http://192.168.1.15:5010');
		var socket = io.connect($scope.myUrl);
		socket.on('connect', function() {
			// we emit a connected message to let knwo the client that we are connected.
			//console.log('socket.on connect aaa')
			socket.emit('client_connected', {data: 'New client!', clientUrl: $scope.myUrl});
			//console.log('socket.on connect bbb')
		});

		socket.on('my_response', function(msg) {
			console.log('socket.on my_response msg:') //, msg)

			/*
						//console.log('msg.status:', msg.status)
						$scope.status = msg.status;
						// for armed checkbox, it needs a model
						$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
				
						//for streaming
						var tmpWidth = parseInt($scope.status.trial.config.video.streamResolution.split(',')[0],10)
						var tmpHeight = parseInt($scope.status.trial.config.video.streamResolution.split(',')[1],10)
						$scope.streamWidth = tmpWidth + (tmpWidth * 0.04)
						$scope.streamHeight = tmpHeight + (tmpWidth * 0.04)

						// for recording
						$scope.lastImage = $scope.myUrl + 'api/lastimage' + '?' + new Date().getTime()
						//console.log('$scope.lastImage:', $scope.lastImage)
				
						//$rootScope.$emit("CallParentMethod", {});
						//console.log('$scope.status:', $scope.status)
						//$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
						//if ( $scope.status.runtime.xxxChange) {
						//}
						//console.log('xxx $scope.configData:', $scope.configData)
						$rootScope.$emit("CallParentMethod_SetConfigData", msg.status);

						$route.reload();
				*/
		});

		socket.on('socket_startTrial', function(msg) {
			console.log('START socket_startTrial() msg:', msg)
			$scope.status = msg.status
// todo: this is going to cause problems !!!!
			$scope.isArmed = true //$scope.isState('armed') || $scope.isState('armedrecording')
			//$scope.setInterval($scope.status.trial.runtime.cameraState)
			$scope.setInterval('armedrecording')
			console.log($scope.status.trial.runtime.cameraState)
		});
		socket.on('socket_stopTrial', function(msg) {
			console.log('STOP socket_stopTrial() msg:', msg)
			$scope.status = msg.status
// todo: this is going to cause problems !!!!
			$scope.isArmed = false //$scope.isState('armed') || $scope.isState('armedrecording')
			//$scope.setInterval($scope.status.trial.runtime.cameraState)
			$scope.setInterval('armed')
			console.log($scope.status.trial.runtime.cameraState)
		});
    });



	///////////////////////////////////////////////////////////////////////
	// does nothing for ~/pie/pie run
	$scope.restartpieserver = function() {
		restartOK = $window.confirm('Are you sure you want to restart the PiE server?');
		if (restartOK) {
			url = $scope.myUrl + 'api/restartpieserver'
			console.log('restartpieserver() url: ' + url)
			$http.get(url).
				then(function(response) {
					// do nothing
					//$scope.status = response.data;
				});
		}
	}
	///////////////////////////////////////////////////////////////////////
    // if streaming then stop streaming on window/tab close
	function sleep(ms) {
	  return new Promise(resolve => setTimeout(resolve, ms));
	}


}); // treadmill controller
