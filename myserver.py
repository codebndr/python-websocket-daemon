import sys
import logging

import os
import serial
from serial.tools import list_ports

import thread

from twisted.internet import reactor
from twisted.python import log

from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS

import json

import time

import subprocess


import base64
import tempfile

import platform

logging.basicConfig(filename='app.log', level=logging.INFO)

def check_ports():
	list = list_ports.comports()

	ports = []
	for port in list:
		if(port[0].startswith("/dev/tty.")):
			ports.append(port[0])
	return ports

def update_ports(websocket):
	old_ports = []
	while 1:
		ports = check_ports()
		if(ports != old_ports):
			for port in ports:
				print port
			websocket.sendMessage(json.dumps({"type":"ports", "ports":ports}))
		old_ports = ports
		time.sleep(500)

class EchoServerProtocol(WebSocketServerProtocol):

	def onMessage(self, msg, binary):
		logging.info("Received message: %s", msg)
		print "Received message: ", msg
		message = json.loads(msg)
		
		if message["type"] == "version":
			self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
		elif message["type"] == "flash":
			bash_shell_cmd = "./avrdudes/" + platform.system() + "/avrdude"
			bash_shell_cnf = " -C./avrdudes/" + platform.system() + "/avrdude.conf"
			bash_shell_cpu = " -p" + message["cpu"]
			bash_shell_ptc = " -c" + message["ptc"]
			bash_shell_prt = " -P" + message["prt"]
			bash_shell_bad = " -b" + message["bad"]
			binary = base64.b64decode(message["binary"])
			bin_file = tempfile.NamedTemporaryFile()
			print "file name: ", bin_file.name
			bin_file.write(binary)
			bash_shell_file = " -Uflash:w:" + bin_file.name + ":i"
			bash_shell = bash_shell_cmd + bash_shell_cnf + " -v -v -v -v" + bash_shell_cpu + bash_shell_ptc + bash_shell_prt + bash_shell_bad + " -D" + bash_shell_file
			print "Flashing: ", bash_shell
			process = subprocess.Popen(bash_shell.split())
			print "FLASHING!!!"
		elif message["type"] == "message":
			print message["text"]
		else:
			self.sendMessage(msg, binary)

	def onOpen(self):
		self.sendMessage(json.dumps({"text":"Socket Opened"}));
		ports = check_ports()
		self.sendMessage(json.dumps({"type":"ports", "ports":ports}))
		self.sendMessage(json.dumps({"type":"version", "version":"0.1"}))

		# Create a thread as follows
		try:
			thread.start_new_thread(update_ports, (self, ))
		except:
			print "Error: unable to start thread"

log.startLogging(sys.stdout)

list = []

# ?
if __name__ == '__main__':

	factory = WebSocketServerFactory("ws://localhost:9000", debug = False)
	factory.protocol = EchoServerProtocol
	listenWS(factory)
	reactor.run()
