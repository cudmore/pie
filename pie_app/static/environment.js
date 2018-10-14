/*
 Robert Cudmore
# 20180701
#
# Javascript code to render a page with a plotly plot and table
*/

var myurl = window.location.href;
console.log(myurl)

// set the browser tab title
var myurl2 = myurl.replace("http://", "");
myurl2 = myurl2.replace(":5010/environment", "");
document.title = myurl2 + " Environment";

//Plotly.d3.csv("https://raw.githubusercontent.com/plotly/datasets/master/Mining-BTC-180.csv", function(err, rows){
Plotly.d3.csv(myurl + 'log', function(err, rows){
  
  function unpack(rows, key) {
  	return rows.map(function(row) { return row[key]; });
  }
   
  var headerNames = Plotly.d3.keys(rows[0]);
  
  //console.log(headerNames)
  
  var headerValues = [];
  var cellValues = [];
  var temperatureValues = [];
  var humidityValues = [];
  var xValues = [];
  for (i = 0; i < headerNames.length; i++) { 
    headerValue = [headerNames[i]];
    headerValues[i] = headerValue; 
    cellValue = unpack(rows, headerNames[i]); 
    cellValues[i] = cellValue;
    
    if (headerNames[i] == 'Temperature') {
    	temperatureValues = cellValue
    }
    if (headerNames[i] == 'Humidity') {
    	humidityValues = cellValue
    }
    if (headerNames[i] == 'DateTime') {
    	xValues = cellValue
    }
  }
  
  // clean date
  if (0) {
  	for (i = 0; i < cellValues[1].length; i++) {
  		var dateValue = cellValues[1][i].split(' ')[0]
  		//cellValues[1][i] = dateValue
  	} 
  }

var data = [{
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
    values: cellValues,
    align: ["center", "center"],
    line: {color: "black", width: 1},
    //fill: {color: ['rgba(228, 222, 249, 0.65)','rgb(235, 193, 238)', 'rgba(228, 222, 249, 0.65)']},
    fill: {color: ['rgba(220, 220, 220, 0.65)']},
    font: {family: "Arial", size: 11, color: ["black"]}
  }
}]

var layout = {
  //title: "Bitcoin mining stats for 180 days",
  height: 600,
  width: 1000,
}

Plotly.plot('graph', data, layout); 

//
// my plot

//console.log(xValues)

var trace1 = {
  x: xValues,
  y: temperatureValues,
  name: 'Temperature',
  mode: 'lines+markers',
  type: 'scatter'
};

var trace2 = {
  x: xValues,
  y: humidityValues,
  name: 'Humidity',
  yaxis: 'y2',
  mode: 'lines+markers',
  type: 'scatter'
};

var mylayout = {
	yaxis: {
        title: 'Temperature (deg celcius)'
	},
	yaxis2: {
        title: 'Humidity (%)',
		overlaying: 'y',
        side: 'right'
	}
}

mydata = [trace1, trace2]

Plotly.plot('myplot', mydata, mylayout)

});  