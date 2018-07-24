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
    
    //rebuild plotly but do not submit
    $scope.motorParamChange = function() {
    	// if form fields don't pass validation, they will be 'undefined'
    	console.log('motorParamChange()', $scope.data)
    	buildPlotly($scope.data)
    }
    
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
			x: [],
			y: [],
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
app.controller('treadmill', function($scope, $rootScope, $window, $http, $location, $interval, $sce, $timeout, $document) {
	
	//console.log('angular.version:', angular.version)
	
	$scope.myUrl = $location.absUrl(); //with port :5000
	console.log('$scope.myUrl:', $scope.myUrl)
	
    myStreamUrl = 'http://' + $location.host() + ':8080/stream';
    $scope.myStreamUrl0 = myStreamUrl
    $scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
	
	$scope.showConfig = false;
	$scope.showPins = false;
	$scope.showMotor = false;
	$scope.showDebug = true;
	$scope.showConfigTable = false;
	$scope.showLastImage = false
	//$scope.allowArming = false
	
    //read the state from homecage backend, do this at an interval
    $scope.getStatus = function () {
		$http.get($scope.myUrl + 'status').
        	then(function(response) {
        	    $scope.status = response.data;
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
				$rootScope.$emit("CallParentMethod_SetConfigData", response.data);
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
				url = $scope.myUrl + 'api/action/' + buttonID
				$http.get(url).
    		    	then(function(response) {
        				$scope.status = response.data;
        			});
				break;
			case 'toggleArm':
				if ($scope.isState('armed')) {
					url = $scope.myUrl + 'api/action/stopArm'
					$http.get(url).
							then(function(response) {
								$scope.status = response.data;
							});
				} else if ($scope.isState('idle')) { //safety check, index interface should handle
					url = $scope.myUrl + 'api/action/startArm'
					$http.get(url).
							then(function(response) {
								$scope.status = response.data;
								
								//removed
								//$rootScope.$emit("CallParentMethod", {});
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
	
	$interval($scope.getStatus, 400); // no () in function call !!!	


}); // treadmill controller
