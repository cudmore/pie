/*
 Robert Cudmore
# 20180701: created
# 20181013: wrapping everything n angular so we can set end date, number of days, and y-axis
#
# Javascript code to render a page with a plotly plot and table
*/

var app = angular.module('environment_app', ['ngRoute']);

app.controller('environmentController', function($scope, $rootScope, $http, $interval, $route, $location) {

	//var myurl = window.location.href;
	var myUrl = $location.absUrl(); //with port :5000
	console.log('myUrl:', myUrl)

	// set the browser tab title
	var myUrl2 = myUrl.replace("http://", "");
	myUrl2 = myUrl2.replace(":5010/environment", "");
	document.title = myUrl2 + " Env";

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

	$scope.reloadDataButton = function() {
		console.log('reloadDataButton()')
		loadData()
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
	
	var loadData = function() {
		Plotly.d3.csv(myUrl + 'log', function(err, rows){
  
			function myUnpack(rows, key) {
				return rows.map(function(row) { return row[key]; });
			}
   
			headerNames = Plotly.d3.keys(rows[0]);
        		
			var headerValues = [];
			var cellValues = [];
			var tableCellValues = [];
			//var temperatureValues = [];
			//var humidityValues = [];
			//var xValues = [];
			for (i = 0; i < headerNames.length; i++) { 
				headerValue = [headerNames[i]];
				headerValues[i] = headerValue; 
				
				cellValue = myUnpack(rows, headerNames[i]); 
				cellValues[i] = cellValue;
				
				// reverse rows for table, need slice() to not mutate original cellValue !!!
				tableCellValues[i] = cellValue.slice().reverse();
				
				if (headerNames[i] == 'Temperature') {
					temperatureValues = cellValue
				}
				if (headerNames[i] == 'Humidity') {
					humidityValues = cellValue
				}
				if (headerNames[i] == 'DateTime') {
					// looks like: 2018-10-18 20:02:14
					// but angular expects 20140313T00:00:00
					xValues = cellValue
				}
				if (headerNames[i] == 'Seconds') {
					xSeconds = cellValue
				}
			} // i

    		// grab the last datetime
    		lastDatetime = xValues[xValues.length -1]
    		// date
    		/*
    		tmpDate = lastDatetime.split(' ')[0] //+ "T" + lastDatetime.split(' ')[1]
    		yyyy = tmpDate.split('-')[0]
    		mm = tmpDate.split('-')[1] - 1
    		dd = tmpDate.split('-')[2]
    		// time
    		tmpTime = lastDatetime.split(' ')[1] //+ "T" + lastDatetime.split(' ')[1]
    		hour = tmpTime.split(':')[0]
    		minute = tmpTime.split(':')[1]
    		second = tmpTime.split(':')[2]
    		$scope.endDate.value = new Date(yyyy, mm, dd, hour, minute, second)
			console.log('$scope.endDate.value:', $scope.endDate.value)
			*/
			
			$scope.lastTime = lastDatetime
			$scope.lastTemp = temperatureValues[temperatureValues.length - 1]
			$scope.lastHum = humidityValues[humidityValues.length - 1]
			//console.log('$scope.lastTime:', $scope.lastTime)
			
			// build a table once (always all values)
			var tableData = [{
				type: 'table',
				columnwidth: [200,600,600,400,400,400,400,400,400],
				columnorder: [0,1,2,3,4,5,6,7,8,9],
				header: {
					values: headerValues, 
					align: "center",
					line: {width: 1, color: 'rgb(50, 50, 50)'},
					fill: {color: ['rgb(100, 100, 100)']},
					font: {family: "Arial", size: 12, color: "white"}
				},
				cells: {
					values: tableCellValues,
					//values: reverseSellValues,
					align: ["center", "center"],
					line: {color: "black", width: 1},
					//fill: {color: ['rgba(228, 222, 249, 0.65)','rgb(235, 193, 238)', 'rgba(228, 222, 249, 0.65)']},
					fill: {color: ['rgba(220, 220, 220, 0.65)']},
					font: {family: "Arial", size: 12, color: ["black"]},

				}
			}]

			var tableLayout = {
				//title: "Bitcoin mining stats for 180 days",
				//height: 600,
				//width: 1000,
				margin: {
					l: 20,
					r: 20,
					b: 20,
					t: 20,
					pad: 5
				},
				autosize: true
			}

			Plotly.plot('mytable', tableData, tableLayout);
			
			//buildPlotly()
			//refreshPlotly2()
			//Plotly.redraw('myplot');
			buildPlotly(doRedraw=true)
			
		})
		}
		
	// plot
	var trace1 = []
	var trace2 = []
	var mydata = []
	var mylayout = []
	var buildPlotly = function(doRedraw=false){

			// clean date
			if (0) {
				for (i = 0; i < cellValues[1].length; i++) {
					var dateValue = cellValues[1][i].split(' ')[0]
					//cellValues[1][i] = dateValue
				} // i
			} // 0

			trace1 = {
				x: xValues,
				y: temperatureValues,
				name: 'Temperature',
				mode: 'markers',
				type: 'scatter'
			};

			trace2 = {
				x: xValues,
				y: humidityValues,
				name: 'Humidity',
				yaxis: 'y2',
				mode: 'markers',
				type: 'scatter'
			};

			mylayout = {
				yaxis: {
					title: 'Temperature (&deg;C)',
					titlefont: {size: 18},
					range: [$scope.yAxisMin, $scope.yAxisMax],
					automargin: true
				},
				yaxis2: {
					title: 'Humidity (%)',
					titlefont: {size: 18},
					overlaying: 'y',
					side: 'right',
					range: [0, 80]
				},
				legend: {
					x: 0.01,
					y: 0.01
				},
				margin: {
					l: 60,
					r: 60,
					b: 60,
					t: 60,
					pad: 5
				},
				autosize: true			}

			mydata = [trace1, trace2]

			if (doRedraw) {
				console.log('redraw')
				//Plotly.redraw('myplot');
				//Plotly.restyle('myplot', 'data', mydata);
				Plotly.react('myplot', mydata, mylayout)
				$scope.$apply();
			} else {
				console.log('plot')
				Plotly.plot('myplot', mydata, mylayout)
			}

	} //buildPlotly
//
//

    //get status ONCE so we can get hostname
    $scope.getStatus = function () {
		var tmpURl = myUrl.replace("environment", "status");

		$http.get(tmpURl).
        	then(function(response) {
        	    $scope.status = response.data;
				console.log('$scope.status:', $scope.status)
				
				//set title once
				document.title = $scope.status.trial.systemInfo.hostname + ' Env'
        	});
	};

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
	
// main
$scope.getStatus()
loadData()
buildPlotly()


}); // environmentController

