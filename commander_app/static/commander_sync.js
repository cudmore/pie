/*
 Robert Cudmore
# 20180701: created
# 20181013: wrapping everything n angular so we can set end date, number of days, and y-axis
#
# Javascript code to render a page with a plotly plot and table
*/

var app = angular.module('environment_app', ['ngRoute']);

app.controller('environmentController', function($scope, $rootScope, $http, $interval, $route, $location) {

	// will have /sync
	$scope.myUrl = $location.absUrl(); //with port :5000
	
	//var myurl = window.location.href;
	var myUrl = $location.absUrl(); //with port :5000
	console.log('myUrl:', myUrl)

	// set the browser tab title
	var myUrl2 = myUrl.replace("http://", "");
	myUrl2 = myUrl2.replace(":5010/environment", "");
	document.title = myUrl2 + " Environment";

    //
    // global variables
    /*
    $scope.daysBefore = 7;
    $scope.endDate = {
		value: new Date() // month index is 0 bases, WTF
	};
    */
    $scope.yAxisMin = 10; // celcius
    $scope.yAxisMax = 30; // celcius
    
    $scope.lastTime = 'None'
    $scope.lastTemp = '-'
    $scope.lastHum = '-'
    
    //
    // callback functions
    /*
    $scope.setDaysBefore = function() {
    	console.log('setDaysBefore() $scope.daysBefore:', $scope.daysBefore)
    }
	*/
	
    /*
    $scope.setEndDate = function() {
    	console.log('setEndDate():', $scope.endDate.value)
    }
	*/
	
	$scope.setYMin = function() {
		console.log('setYMin() yAxisMin:', $scope.yAxisMin)
		refreshPlotly()
	}

	$scope.setYMax = function() {
		console.log('setYMax() yAxisMax:', $scope.yAxisMax)
		refreshPlotly()
	}

//
//
	//
	// plot temp/hum using plotly
	
	// refresh
	var refreshPlotly = function() {
		console.log('refreshPlotly()')
		Plotly.relayout('myplot', 'yaxis.range', [$scope.yAxisMin, $scope.yAxisMax])	
	}
	
	var refreshPlotly2 = function() {
		console.log('refreshPlotly()')
		Plotly.restyle('myplot', 'data[0].y', temperatureValues)	
		Plotly.restyle('myplot', 'data[0].x', xValues)	
	}
	
	// load all environmental data from server
	var temperatureValues = []
	var humidityValues = []
	var xValues = [] // yyyy-mm-dd hh:mm:ss
	var xSeconds = [] // Linux epoch (remember javascript is in milliseconds)
	
//
//

window.onresize = function() {
    //buildPlotly(doRedraw=true)
    /*
    Plotly.relayout('myplot', {
        'xaxis.autorange': true,
        'yaxis.autorange': true
    });
    */
    
    //Plotly.Plots.resize('myplot')
    //Plotly.Plots.resize('mytable')

	Plotly.relayout('myplot', 'layout.width', '100%')
	Plotly.relayout('mytable', 'layout.width', '100%')

};
	
//
// commander_sync
//

	$scope.checkForNewFilesButton = function() {
		console.log('checkForNewFilesButton()')
		checkForNewFiles()
	}
	$scope.synchronizeButton = function() {
		console.log('synchronizeButton()')
		synchronize()
	}
	$scope.cancelButton = function() {
		console.log('cancelButton()')
		mycancel()
	}


	var checkForNewFiles = function () {
		url = $scope.myUrl + '/fetchfiles' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};

	var synchronize = function () {
		url = $scope.myUrl + '/run' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};

	// cancel a sync (will cancel after current file is finished)
	var mycancel = function () {
		url = $scope.myUrl + '/cancel' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};

    $scope.getStatus = function () {
		url = $scope.myUrl + '/status' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    $scope.status = response.data;
        	});
	};

// main
var defaultInterval = 400; // 800
var interval = $interval($scope.getStatus, defaultInterval);


}); // environmentController

