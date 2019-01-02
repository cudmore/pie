// Robert Cudmore
// 20180515

angular.module('commander', ['uiSwitch'])
.controller('commander', function($scope, $window, $http, $location, $interval, $sce, $timeout, $document) {
	
	document.title = 'Commander'
	
	//console.log('angular.version:', angular.version)
	
	//url of page we loaded
	$scope.myUrl = $location.absUrl(); //with port :8000

	var restPort = 5010; //the port that PiE server is running on
	var adminPort = 5011; //the port that PiE server is running on
	
	// these will be assigned on page load in $scope.loadServers()
	$scope.numServers = 2;
	// this is an array of dict {ip:'', 'username':'', password:''}
	var defaultServerDict = {"ip":"", "username":"", "password":""}
	$scope.serverList = ['192.168.1.2', '192.168.1.3']

	//
	// manager server list
	//
	$scope.showServerPanel = false //video wall
	$scope.showServerConfig = true
	$scope.showServerConfig2 = false
	$scope.showSwarmStatus = false
	$scope.editIPList = false
	$scope.doDebug = false
	
	$scope.lastAction = 'None'
	
	$scope.toggleVideoPanels = function () {
		$scope.showServerPanel = ! $scope.showServerPanel
	}

	$scope.toggleServerConfig = function () {
		$scope.showServerConfig = ! $scope.showServerConfig
	}
	
	$scope.toggleshowServerConfig2 = function () {
		$scope.showServerConfig2 = ! $scope.showServerConfig2
	}
	
	$scope.toggleEditIPList = function () {
		$scope.editIPList = ! $scope.editIPList
	}
	
	$scope.toggleshowSwarmStatus = function () {
		$scope.showSwarmStatus = ! $scope.showSwarmStatus
	}
	
	//
	// Manage server list
	//
	$scope.addServer = function() {
		$scope.numServers += 1
		$scope.serverList.push(defaultServerDict)
		initVideoWall()
		//$scope.$apply();
	}

	$scope.removeServer = function(idx) {
		removeOK = $window.confirm('Are you sure you want to remove server "' + $scope.serverList[idx].ip + '"?');
		if (removeOK) {
			$scope.numServers -= 1
			$scope.serverList.splice(idx,1)
			initVideoWall()
			$scope.$apply();
		}
	}

	$scope.setServer = function(idx, str) {
		console.log('$scope.setServer():', idx, str)
		$scope.serverList[idx].ip = str
		initVideoWall();
	}

	// Save config_commander.txt
	$scope.saveServers = function() {
		console.log('saveServers()')
		//var str = JSON.stringify($scope.serverList, null, 4);
		var str = $scope.serverList
		var url = $scope.myUrl + 'saveconfig/' + str
		$http.get(url).
        	then(function(response) {
        	    console.log('saveServers response.data;', response.data)
        	}, function errorCallback(response) {
        		console.log('saveServers() error')
        	});
	}
	
	// Load config from commander, config_commander.txt
	$scope.loadServers = function() {
		var url = $scope.myUrl + 'loadconfig'
		$http.get(url).
        	then(function(response) {
        	    //commander.py loadconfig returns a list of dict
        	    // {ip:'', username:'', password:''}
        	    console.log('loadconfig response.data:', response.data)
        	    //var array = JSON.parse(response.data)
        	    var array = response.data
        	    //20181229, was this
        	    //$scope.serverList = array
        	    $scope.numServers = array.length
        	    for (i=0; i<$scope.numServers; i+=1) {
        	    	$scope.serverList[i] = response.data[i] // .ip
				}
				
        	    console.log('loadServers()')
        	    console.log('$scope.serverList:', $scope.serverList)
        	    console.log('$scope.numServers:', $scope.numServers)

        	    initVideoWall()

        	}, function errorCallback(response) {
        		console.log('loadServers() error')
        	});
	}
	
	//removed 20181229
	/*
	$scope.changeDebug = function(doDebug) {
		console.log('changeDebug()', doDebug)
		//$scope.doDebug = ! $scope.doDebug
		console.log('$scope.doDebug:', $scope.doDebug)
		//initVideoWall()
	}
	*/
	
	//
	// main interface
	//
	function initVideoWall() {
		$scope.videoArray = new Array($scope.numServers)
		for (i=0; i<$scope.numServers; i+=1) {
			id = "v" + i
			$scope.videoArray[i] = {}
			$scope.videoArray[i].myIdx = i
			
			$scope.videoArray[i].restUrl = "http://" + $scope.serverList[i].ip + ":" + restPort + "/"
			$scope.videoArray[i].adminUrl = "http://" + $scope.serverList[i].ip + ":" + adminPort + "/"
			
			getStatus(i) // uses restUrl
						
			//$scope.videoArray[i].animalID = ''
			//$scope.videoArray[i].conditionID = ''

			myStreamUrl = "http://" + $scope.serverList[i].ip + ":8080/stream"
			$scope.videoArray[i].streamUrl = $sce.trustAsResourceUrl(myStreamUrl)
			$scope.videoArray[i].myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
			
			$scope.videoArray[i].image = new Image()
			$scope.videoArray[i].image.src = "" // the image source
			$scope.videoArray[i].image.canvasID = id // the canvas id
			$scope.videoArray[i].image.myIdx = i // the canvas id
			$scope.videoArray[i].image.onload = function(thisEvent) {
				// this is an Image object
				//console.log('this.canvasID:', this.canvasID)
				//console.log('this.src:', this.src)
				var canvas = document.getElementById(this.canvasID);
				if (canvas) {
					var context = canvas.getContext("2d");

					// backgorund color
					context.fillStyle = "blue";
					context.fillRect(0, 0, canvas.width, canvas.height);

					var hRatio = canvas.width / this.width    ;
					var vRatio = canvas.height / this.height  ;
			
					var ratio  = Math.min ( hRatio, vRatio );
			
					context.drawImage(this, 0,0, this.width, this.height, 0,0,this.width*ratio, this.height*ratio);

					//text
					context.font = "18px Arial";
					context.fillStyle = "red";
					//var myStr = $scope.videoArray[this.myIdx].status.lastStillTime
					var myStr = $scope.videoArray[this.myIdx].status.trial.runtime.lastStillTime
					
					context.fillText(myStr,5,20);
					
					//if ($scope.videoArray[this.myIdx].status.isRecording == false) {
					if (! $scope.isState(this.myIdx, 'recording')) {
						context.font = "56px Arial";
						context.fillStyle = "red";
						var myStr = "Stopped"
					    //context.fillStyle = '#f50';
						//var stoppedWidth = context.measureText(myStr).width;
					    //context.fillRect(180, 200, stoppedWidth, parseInt(56, 10));
						context.fillText(myStr,180,200);
					}
				}			
			};
			//streaming
			$scope.videoArray[i].hardCloseStream = 0
			//$scope.videoArray[i].myStreamUrl = $sce.trustAsResourceUrl(streamList[i]) //'http://' + $location.host() + ':8080/stream';
			$scope.videoArray[i].streamWidth = 640
			$scope.videoArray[i].streamHeight = 480
		
			$scope.videoArray[i].showConfig = false
		}
	}
		
	//
	$scope.isState = function(idx, thisState) {
		//if (idx > 0) {
		//	console.log(idx)
		//}
		//console.log('$scope.videoArray[idx].status:', $scope.videoArray[idx].status)
		if ($scope.videoArray && $scope.videoArray[idx].status) {
			return $scope.videoArray[idx].status.trial.runtime.cameraState == thisState
		} else {
			return false
		}
	}

	$scope.toggleConfig = function(idx) {
		console.log('toggleConfig()', idx)
		$scope.videoArray[idx].showConfig = $scope.videoArray[idx].showConfig === false ? true: false;
	};

    //read the state from homecage backend, do this at an interval
    //also get bash status (black windows) from admin server
    function getStatus(i) {
		// from main PiE server
		url = $scope.videoArray[i].restUrl
		$http.get(url + 'status').
        	then(function(response) {
        	    $scope.videoArray[i].status = response.data;
        	    $scope.videoArray[i].isAlive = true;

				var tmpWidth = parseInt($scope.videoArray[i].status.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.videoArray[i].status.trial.config.video.streamResolution.split(',')[1],10)
				//console.log('tmpWidth:', tmpWidth)
				//console.log('tmpHeight:', tmpHeight)
				$scope.videoArray[i].streamWidth = tmpWidth + (tmpWidth * 0.03)
				$scope.videoArray[i].streamHeight = tmpHeight + (tmpWidth * 0.03)

				//console.log('$scope.videoArray[i].status:', $scope.videoArray[i].status)
				
        	}, function errorCallback(response) {
        		//console.log('getStatus() error', url, i)
        	    $scope.videoArray[i].isAlive = false;
        	});
        	
        // from admin server, get bash status
		// added if 20190102
		if ($scope.showSwarmStatus) {
			url = $scope.videoArray[i].adminUrl
			$http.get(url + 'status').
				then(function(response) {
					$scope.videoArray[i].adminStatus = response.data;
				}, function errorCallback(response) {
					//console.log('getStatus() error', url, i)
					//$scope.videoArray[i].isAlive = false;
					$scope.videoArray[i].adminStatus = ["http error in commander.js"]
				});
		}        
	};

//get rid of .config in general, use .status
/*
    function getConfig(i) {
		url = $scope.videoArray[i].restUrl
		console.log('getConfig() i:', i, 'url:', url)
		$http.get(url + 'status').
        	then(function successCallback(response) {
        	    $scope.videoArray[i].config = response.data;
        	    console.log($scope.videoArray[i])
        	    //$scope.videoArray[i].config.url = url;

				var tmpWidth = parseInt($scope.videoArray[i].config.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.videoArray[i].config.trial.config.video.streamResolution.split(',')[1],10)
				//console.log('tmpWidth:', tmpWidth)
				//console.log('tmpHeight:', tmpHeight)
				$scope.videoArray[i].streamWidth = tmpWidth + (tmpWidth * 0.03)
				$scope.videoArray[i].streamHeight = tmpHeight + (tmpWidth * 0.03)
        	}, function errorCallback(response) {
        		console.log('getConfig() error', url, i)
        	});
	};
*/

	$scope.refreshStatusButton = function() {
		console.log('refreshStatusButton()')
		for (i=0; i<$scope.numServers; i+=1) {
			getStatus(i)
		}
		console.log($scope.videoArray)
	}
	
	//
	// Load config on PiE server
    $scope.loadPieConfig = function (idx) {
		console.log("loadPieConfig()", idx);		
		var thisConfig = 'homecage'
		url = $scope.videoArray[idx].restUrl + 'api/submit/loadconfig/' + thisConfig
		console.log(url)
		$http.get(url).
        	then(function(response) {
        		//console.log('success: loaded config ' + thisConfig)
        		var tmpHostname = $scope.videoArray[idx].status.trial.systemInfo.hostname
        		$scope.lastAction = tmpHostname + ': Loaded Homecage config'
        	}, function errorCallback(response) {
        		//console.log('failed: loaded config ' + thisConfig)
        		var tmpHostname = $scope.videoArray[idx].status.trial.systemInfo.hostname
        		$scope.lastAction = tmpHostname + ': ERROR Homecage config'
        	});
	};

	//
	// restart PiE server
	$scope.restartserver = function (idx) {
		console.log("restartserver()", idx);		
		var restartOK = $window.confirm('Are you sure you want to restart the PiE server "' + $scope.videoArray[idx].status.trial.systemInfo.hostname + '"');
		if (restartOK) {
			url = $scope.videoArray[idx].adminUrl + 'api/restartserver'
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].adminStatus = response.data;
        		}, function errorCallback(response) {
        			console.log('restartserver() error url:', url)
        		});
        }
	};

	//
	// rebootmachine pi
	$scope.rebootmachine = function (idx) {
		console.log("rebootmachine()", idx);		
		var rebootOK = $window.confirm('Are you sure you want to reboot "' + $scope.videoArray[idx].status.trial.systemInfo.hostname + '"');
		if (rebootOK) {
			url = $scope.videoArray[idx].adminUrl + 'api/rebootmachine'
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].adminStatus = response.data;
        		}, function errorCallback(response) {
        			console.log('rebootmachine() error url:', url)
        		});
        }
	};

	//
	// update software
	$scope.updatesoftware = function (idx) {
		console.log("updatesoftware()", idx);		
		var updateOK = $window.confirm('Are you sure you want to update the PiE server software for "' + $scope.videoArray[idx].status.trial.systemInfo.hostname + '"');
		if (updateOK) {
			url = $scope.videoArray[idx].adminUrl + 'api/updatesoftware'
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].adminStatus = response.data;
        	    	//console.log('$scope.videoArray[idx].adminStatus:', $scope.videoArray[idx].adminStatus)
        	    	
        		}, function errorCallback(response) {
        			console.log('updatesoftware() error url:', url)
        		});
        }
	};

	//
	// update software
	$scope.reverttostable = function (idx) {
		console.log("updatesoftware()", idx);		
		var updateOK = $window.confirm('Are you sure you want to revert the PiE server software to stable version for "' + $scope.videoArray[idx].status.trial.systemInfo.hostname + '"');
		if (updateOK) {
			url = $scope.videoArray[idx].adminUrl + 'api/reverttostable'
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].adminStatus = response.data;
        	    	//console.log('$scope.videoArray[idx].adminStatus:', $scope.videoArray[idx].adminStatus)
        	    	
        		}, function errorCallback(response) {
        			console.log('updatesoftware() error url:', url)
        		});
        }
	};

	//
	// update software
	$scope.clearbashqueue = function (idx) {
		console.log("clearbashqueue()", idx);		
			url = $scope.videoArray[idx].adminUrl + 'api/clearbashqueue'
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].adminStatus = response.data;
        		}, function errorCallback(response) {
        			console.log('clearbashqueue() error url:', url)
        		});
	};
	

	//
	// refreshsysteminfo including system uptime and hard-drive space remaining
	$scope.refreshsysteminfo = function (idx) {
		console.log("refreshsysteminfo()", idx);		
		url = $scope.videoArray[idx].restUrl + 'api/refreshsysteminfo'
		console.log(url)
		$http.get(url).
			then(function(response) {
				$scope.videoArray[idx].status = response.data;
			}, function errorCallback(response) {
				console.log('refreshsysteminfo() error url:', url)
			});
	};

	//
	// RECORDING
	$scope.startstoprecord = function (idx, startstop) {
		console.log("startstoprecord()", idx, startstop);		
		stopOK = 1;
		if (startstop == 0) {
			stopOK = $window.confirm('Are you sure you want to stop the recording on  "' + $scope.videoArray[idx].status.trial.systemInfo.hostname + '"');
		}
		if (stopOK) {
			if (startstop) {
				url = $scope.videoArray[idx].restUrl + 'api/action/startRecord'
			} else {
				url = $scope.videoArray[idx].restUrl + 'api/action/stopRecord'
			}
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].status = response.data;
        		}, function errorCallback(response) {
        			console.log('startstoprecord() error url:', url)
        		});
        }
	};

	//
	//STREAMING
	$scope.startstopstream = function (idx, startstop) {
		console.log("startstopstream() idx:", idx, 'startstop:', startstop);		
		// if we are stopping, we need to force close the live stream
		if (startstop==1) {
			$scope.videoArray[idx].hardCloseStream = 0
			url = $scope.videoArray[idx].restUrl + 'api/action/startStream'
			callAtTimeout(idx)
		} else {
			//startstop == 0
			$scope.videoArray[idx].hardCloseStream = 1
			callAtTimeout(idx)
			url = $scope.videoArray[idx].restUrl + 'api/action/stopStream'
		}
		
		$http.get(url).
        	then(function(response) {
        	    $scope.videoArray[idx].status = response.data;
        	    callAtTimeout(idx)
        	}, function errorCallback(response) {
        		console.log('startstopstream() error url:', url)
        	});
        //refresh stream
		/*
		if (startstop==1) {
			//callAtTimeout()
			$timeout(callAtTimeout(idx), 2000);
		}
		*/
	};


	//
	//change led status
//final
    $scope.submitConfigForm = function(idx) {
        url = $scope.videoArray[idx].restUrl + 'api/submit/configparams'
        console.log('submitConfigForm(), url:', url)
        $http.post(url, JSON.stringify($scope.videoArray[idx].status.trial.config)).
        	then(function(response) {
        		$scope.videoArray[idx].status = response.data
        	});
    };

    $scope.submitLEDForm = function(idx) {
        url = $scope.videoArray[idx].restUrl + 'api/submit/ledparams'
        console.log('submitLEDForm(), url:', url)
        $http.post(url, JSON.stringify($scope.videoArray[idx].status.trial.config)).
        	then(function(response) {
        		$scope.videoArray[idx].status = response.data
        	});
    };

    $scope.submitAnimalForm = function(idx) {
        //console.log('submitConfigForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.videoArray[idx].restUrl + 'api/submit/animalparams'
        console.log('submitAnimalForm(), url:', url)
        console.log($scope.videoArray[idx].status.trial.config)
        $http.post(url, JSON.stringify($scope.videoArray[idx].status.trial.config)).
        	then(function(response) {
        		$scope.videoArray[idx].status = response.data
        	});
    };


	function callAtTimeout(idx) {
		console.log("callAtTimeout() idx:", idx, '$scope.videoArray[idx].hardCloseStream', $scope.videoArray[idx].hardCloseStream);
		if ($scope.videoArray[idx].hardCloseStream) {
			$scope.videoArray[idx].myStreamUrl = ''
		} else {
			//myStreamUrl = streamList[idx] + '?' + new Date().getTime() //'http://' + $location.host() + ':8080/stream' + '?' + new Date().getTime()
			myStreamUrl = $scope.videoArray[idx].streamUrl + '?' + new Date().getTime()
			console.log('myStreamUrl:', myStreamUrl)
			$scope.videoArray[idx].myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
		}
	}

	//
	// call this at an interval
	$scope.getLastImage = function () {
		for (i=0; i<$scope.numServers; i+=1) {
			//getStatus($scope.videoArray[i].restUrl, i)
			
			//getConfig($scope.videoArray[i].restUrl, i)
			
			if ($scope.showServerPanel) {
				$scope.videoArray[i].image.src = $scope.videoArray[i].restUrl + 'api/lastimage' + '?' + new Date().getTime()
			}
		}
	}

	$scope.loadServers()
	//initVideoWall()
	
	//treadmill put this back in
	$interval($scope.getLastImage, 900);      	
	
	//$scope.hardCloseStream = 0

	myUpdate = function() {
		for (i=0; i<$scope.numServers; i+=1) {
			getStatus(i)
		}
	}	
	$interval(myUpdate, 1000); // ms
}); //controller
