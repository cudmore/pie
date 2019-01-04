/*
 Robert Cudmore
# 20180701: created
# 20181013: wrapping everything n angular so we can set end date, number of days, and y-axis
#
# Javascript code to render a page with a plotly plot and table
*/

var app = angular.module('environment_app', ['ngRoute']);

/*
app.directive('fdInput', ['$timeout', function ($timeout) {
    console.log('fdinput')
    return {
        link: function (scope, element, attrs) {
            element.on('change', function  (evt) {
                var files = evt.target.files;
                console.log(files[0].name);
                console.log(files[0].size);
            });
        }
    }
}]);
*/


app.controller('environmentController', function($scope, $rootScope, $http, $interval, $route, $location) {

	// this is experimental code to allow user to specify download folder
	//should only by active when $scope.myUrl contains 'localhost'
	/*
	input = document.getElementById("fileURL")

	input.addEventListener("change", function (e) {
		files = e.target.files;
		//output.innerHTML = "";

		//for (var i = 0, len = files.length; i < len; i++) {
		for (var i = 0, len = 1; i < len; i++) {
			file = files[i];
			console.log('file.webkitRelativePath:', file.webkitRelativePath)
			//extension = file.name.split(".").pop();
			//output.innerHTML += "<li class='type-" + extension + "'>" + file.name + " (" +  Math.floor(file.size/1024 * 100)/100 + "KB)</li>";
		}
	}, false);
	*/
	

	//
	// ANGULARJS
	//
	
	// will have /sync
	$scope.myUrl = $location.absUrl(); //with port :5000
	
	//var myurl = window.location.href;
	var myUrl = $location.absUrl(); //with port :5000
	console.log('myUrl:', myUrl)

	$scope.weAreLocalhost = myUrl.includes('localhost')
	
	document.title = "Commander Sync";

    //
    // global variables
	$scope.deleteAfterCopy = false;
	
	//
	// commander_sync
	//

	$scope.selectFolder = function(event) {
		console.log('selectFolder() event:', events)
	}
	
	// check for files to be copied from server
	$scope.checkForNewFilesButton = function() {
		console.log('checkForNewFilesButton()')
		//checkForNewFiles()
		url = $scope.myUrl + '/fetchfiles' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}
	
	// start copy/sync from remote server to local host
	$scope.synchronizeButton = function() {
		console.log('synchronizeButton()')
		//synchronize()
		url = $scope.myUrl + '/run' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});

	}

	// cancel a sync (will cancel after current file is finished)
	$scope.cancelButton = function() {
		console.log('cancelButton()')
		//mycancel()
		url = $scope.myUrl + '/cancel' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}

	// when delete after copy checkbox is clicked
	$scope.deleteAfterCopyChange = function(isValid) {
		//console.log('$scope.deleteAfterCopyChange() $scope.deleteAfterCopy', $scope.deleteAfterCopy)
		// convert true/false to 1/0
		onoff = $scope.deleteAfterCopy ? 1 : 0
		url = $scope.myUrl + '/deleteaftercopy' + '/' + onoff // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	
    // get server status, called at an interval
    $scope.getStatus = function () {
		url = $scope.myUrl + '/status' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    $scope.status = response.data;
        	    console.log('response.data.deleteRemoteFiles:', response.data.deleteRemoteFiles)
        	    $scope.deleteAfterCopy = response.data.deleteRemoteFiles
        	});
	};

	/*
	var checkForNewFiles = function () {
		url = $scope.myUrl + '/fetchfiles' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	*/
	
	/*
	var synchronize = function () {
		console.log('$scope.deleteAfterCopy', $scope.deleteAfterCopy)
		url = $scope.myUrl + '/run' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	*/
	
	/*
	// cancel a sync (will cancel after current file is finished)
	var mycancel = function () {
		url = $scope.myUrl + '/cancel' // $scope.myUrl ends in /sync
		//console.log('$scope.getStatus url:', url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	*/
	

// main
var defaultInterval = 400; // 800
var interval = $interval($scope.getStatus, defaultInterval);


}); // environmentController

