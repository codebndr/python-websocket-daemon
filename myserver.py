import sys
import logging

from twisted.internet import reactor
from twisted.python import log

from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS

import json

logging.basicConfig(filename='app.log', level=logging.INFO)


class EchoServerProtocol(WebSocketServerProtocol):

	def onMessage(self, msg, binary):
		logging.info("Received message: %s", msg)
		print "sending echo:", msg
		json_decode = json.loads('{"type":"version"}')
		type = json_decode["type"]
		
		if msg == "version":
			self.sendMessage("0.1" ,binary)
		else:
			self.sendMessage(msg, binary)


if __name__ == '__main__':

   log.startLogging(sys.stdout)

   factory = WebSocketServerFactory("ws://localhost:9000", debug = False)
   factory.protocol = EchoServerProtocol
   listenWS(factory)

   reactor.run()
