// server file 170118
// drew mcarthur
// trump stock monitor

// requirements
var express = require('express');
var app = express();
var http = require('http').Server(app);
var fs = require('fs');

// routes
app.set('views', __dirname + "/public");

app.use(express.static(__dirname + '/public'));

var port = 8000;

// listen
http.listen(port, function() {
	logger("Server is running on port " + port);
});

var logger = function(msg) {
	console.log(msg);
	fs.appendFile(
		__dirname + "/server.log", 
		new Date().toUTCString() + "	" + msg.toString() + "\n", 
		function(err){ 
			if(err) { console.log(err); } 
		}
	);
}
