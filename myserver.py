import sys
import logging

import os
import serial
from serial.tools import list_ports

import thread
import threading

#needed for py2exe
import zope.interface
from twisted.internet import reactor
from twisted.python import log

#needed for py2exe
import autobahn.resource
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS

import json

import time

import subprocess


import base64
import tempfile

import platform

import check_requirements
import fix_requirements
import port_listing

logging.basicConfig(filename='app.log', level=logging.INFO)

def flash_arduino(cpu, ptc, prt, bad, binary):
	bash_shell_cmd = "./avrdudes/" + platform.system() + "/avrdude"
	bash_shell_cnf = " -C./avrdudes/" + platform.system() + "/avrdude.conf"
	bash_shell_cpu = " -p" + cpu
	bash_shell_ptc = " -c" + ptc
	bash_shell_prt = " -P" + prt
	bash_shell_bad = " -b" + bad
	binary = base64.b64decode(binary)
	bin_file = tempfile.NamedTemporaryFile()
	print "file name: ", bin_file.name
	bin_file.write(binary)
	bash_shell_file = " -Uflash:w:" + bin_file.name + ":i"
	bash_shell = bash_shell_cmd + bash_shell_cnf + " -v -v -v -v" + bash_shell_cpu + bash_shell_ptc + bash_shell_prt + bash_shell_bad + " -D" + bash_shell_file
	print "Flashing: ", bash_shell
	process = subprocess.Popen(bash_shell.split())
	print "FLASHING!!!"
	#ToDo: Delete the temp file after it's done

class EchoServerProtocol(WebSocketServerProtocol):
	def onMessage(self, msg, binary):
		logging.info("Received message: %s", msg)
		print "Received message: ", msg
		message = json.loads(msg)
		
		if message["type"] == "version":
			self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
		elif message["type"] == "ack":
			self.sendMessage(msg, binary)
		elif message["type"] == "flash":
			if platform.system() == "Windows":
                                message["prt"] = '\\\\.\\' + message["prt"]
			flash_arduino(message["cpu"], message["ptc"], message["prt"], message["bad"], message["binary"])
		elif message["type"] == "message":
			print message["text"]
		elif message["type"] == "list_ports":
			ports = check_ports()
			self.sendMessage(json.dumps({"type":"ports", "ports":ports}))
		elif message["type"] == "check_drivers":
			check_drivers(self)
		elif message["type"] == "install_drivers":
			do_install_drivers()

	def onOpen(self):
		self.sendMessage(json.dumps({"text":"Socket Opened"}));

		# Create a thread as follows
		try:
			thread.start_new_thread(update_ports, (self, ))
		except:
			print "Error: unable to start thread"


################ WEBSERIAL CODE

class ReaderThread(threading.Thread, ):
	"""Thread class with a stop() method. The thread itself has to check
	regularly for the stopped() condition."""

	def __init__(self, websocket_port, serial_port):
		super(ReaderThread, self).__init__()
		self._stop = threading.Event()
		self.websocket_port = websocket_port
		self.serial_port = serial_port

	def stop(self):
		self.run = False
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def run(self):
		self.run = True
		self.read()

	def read(self):
		"""loop and copy serial->console"""
		try:
			while self.run:
				data = self.serial_port.read(10).decode("ascii")
				if(data != ""):
					sys.stdout.write(data)
					sys.stdout.flush()
					self.websocket_port.sendMessage(json.dumps({"type":"data", "data":data}))
		except serial.SerialException, e:
			raise

def writer(serial_port, data):
	serial_port.write(data)

class WebserialProtocol(WebSocketServerProtocol):
	def __init__(self):
		self.myserial = None

	def onMessage(self, msg, binary):
		logging.info("Received message: %s", msg)
		print "Received message: ", msg
		message = json.loads(msg)

		if message["type"] == "version":
			self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
		elif message["type"] == "ack":
			self.sendMessage(msg, binary)
		elif message["type"] == "serial_connect":
			print "Connect Message Received"
			self.myserial = serial.Serial(message["port"], baudrate= message["baudrate"], timeout=0)
			self.read_thread = ReaderThread(self, self.myserial)
			self.read_thread.daemon = True
			self.read_thread.start()
		elif message["type"] == "serial_disconnect":
			print "Disconnect Message Received"
			if self.myserial != None:
				oldserial = self.myserial
				self.myserial = None
				self.read_thread.stop()
				self.read_thread.join()
				oldserial.close()
		elif message["type"] == "data":
			if self.myserial != None:
				writer(self.myserial, message["data"])
			else:
				print "Could not send data. No active serial connections"

	def onOpen(self):		
		self.sendMessage(json.dumps({"text":"Socket Opened"}));


################ END OF WEBSERIAL CODE

log.startLogging(sys.stdout)

list = []

# ?
if __name__ == '__main__':

	#initializing serial flashing etc utilities socket
	factory = WebSocketServerFactory("ws://localhost:9000", debug = False)
	factory.protocol = EchoServerProtocol
	listenWS(factory)

	#initializing webserial socket
	factory2 = WebSocketServerFactory("ws://localhost:9001", debug = False)
	factory2.protocol = WebserialProtocol
	listenWS(factory2)

	reactor.run()
