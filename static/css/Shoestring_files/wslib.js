
function wsClient()
{
	var self = this;
	this.debug = true;
	this.url = "";
	this.msgCallbacks=[];
	this.onConnectCallback=null
	this.onDisconnectCallback=null

	this.connect = function(url) {
		self.wsocket = new WebSocket(url);
		self.url = url;
							
		self.wsocket.onopen = function(event) {
	  		if(self.debug)
				console.log("websocket connected to ",self.url);
			if (self.onConnectCallback !== null){
				if (self.debug)
					console.log("Calling connect callback ",self.onConnectCallback);
				self.onConnectCallback();
			}
		};

		self.wsocket.onmessage = function(event) {
			if(self.debug)
				console.log("Got ws message: "+event.data);
			var msg = JSON.parse(event.data);
			self.map_to_callback(msg)
		};

		self.wsocket.onclose = function (event) {
	  		if (event.wasClean) {
	  			console.log("Connection closed cleanly");
	  		} else {
	    			console.error('Connection died. code: ',event.code," reason: ",event.reason);
				setTimeout(function(){
					if(self.debug)
						console.log("reconnecting ...");
					self.connect(self.url);
				},1000);
			}
			if (self.onDisconnectCallback !== null){
				if (self.debug)
					console.log("Calling disconnect callback ",self.onDisconnectCallback);
				self.onDisconnectCallback();
			}
		};

		self.wsocket.onerror = function(error) {
	  		console.error("websocket error: ",error.message);
		};
	};
	
	this.register_connect_callback = function(cb){
		if(self.debug)
			console.log("registering connect callback ",cb);
		self.onConnectCallback = cb;
	}
	
	this.register_disconnect_callback = function(cb){
		if(self.debug)
			console.log("registering disconnect callback ",cb);
		self.onDisconnectCallback = cb;
	}

	this.register_callback = function(cbtag,callback,cbargs){
		if(self.debug)
			console.log("registering ",callback," to tag ",cbtag," with args ",cbargs);
		if(!cbargs)
			cbargs={};
		self.msgCallbacks.push({tag:cbtag,cb:callback,args:cbargs});
	}
	
	this.map_to_callback = function(msg){
		var m_tag = msg["tag"];
		var i;
		for(i=0;i<self.msgCallbacks.length;i++){
			var cbset = self.msgCallbacks[i];
			if(cbset.tag==m_tag){
				if(self.debug)
					console.log("calling callback ",cbset.cb," with msg ",msg["content"]," and args ",cbset.args);
				cbset.cb(msg["content"],cbset.args);
				break;
			}
		}
	}

	this.send = function(m_tag,m_content){
		self.wsocket.send(JSON.stringify({tag:m_tag,content:m_content}));
	}
}
