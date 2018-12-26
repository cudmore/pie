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

	document.title = "Commander Sync";

    //
    // global variables
	$scope.deleteAfterCopy = true;
	
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

	// when checkbox is clicked
	$scope.deleteAfterCopyChange = function(isValid) {
		console.log('$scope.deleteAfterCopy', $scope.deleteAfterCopy)
		onoff = $scope.deleteAfterCopy ? 1 : 0
		url = $scope.myUrl + '/deleteaftercopy' + '/' + onoff // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	
	var checkForNewFiles = function () {
		url = $scope.myUrl + '/fetchfiles' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};

	var synchronize = function () {
		console.log('$scope.deleteAfterCopy', $scope.deleteAfterCopy)
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

