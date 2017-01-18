// server file 170118
// drew mcarthur
// trump stock monitor

// requirements
var express = require('express');
var app = express();
var http = require('http').Server(app);

// routes
app.set('views', __dirname + "/public");
app.set('view engine', 'pug');

app.use(express.static(__dirname + '/public'));

var port = 8000;

// listen
http.listen(port, function() {
	logger("Server is running on port " + port);
});
