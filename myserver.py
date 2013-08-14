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

def install_drivers_osx():
	os.system("""osascript -e 'do shell script "/usr/sbin/installer -pkg drivers/Darwin/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/ -target /" with administrator privileges'""")	

def install_drivers():
	if platform.system() == "Darwin":
		install_drivers_osx()

def do_install_drivers():
	# Create a thread as follows
	try:
		thread.start_new_thread(install_drivers, ())
	except:
		print "Error: unable to start thread"
	
def check_drivers_osx(websocket):
	if(os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.FTDIUSBSerialDriver-2.pkg.bom") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.FTDIUSBSerialDriver-2.pkg.plist") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.postflight.pkg.bom") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.postflight.pkg.plist") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.preflight.pkg.bom")):
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
	else:
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))

def check_drivers(websocket):
	if platform.system() == "Darwin":
		check_drivers_osx(websocket)

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
	
def check_ports_posix():
	list = list_ports.comports()

	ports = []
	for port in list:
		if(port[0].startswith("/dev/tty.")):
			ports.append(port[0])
	return ports

try:
	import _winreg as winreg
	import itertools
except ImportError:
	pass

def check_ports_windows():
        """ Uses the Win32 registry to return an
        iterator of serial (COM) ports
        existing on this computer.
        """
        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        except WindowsError:
                raise IterationError

        ports = []
        for i in itertools.count():
                try:
                        val = winreg.EnumValue(key, i)
                        ports.append(str(val[1]))
                except EnvironmentError:
                        break
        return ports

def check_ports():
        if platform.system() == "Windows":
                return check_ports_windows()
        else:
                return check_ports_posix()

def update_ports(websocket):
	print "Starting check for ports"
	old_ports = []
	while 1:
		ports = check_ports()
		if(ports != old_ports):
			for port in ports:
				print port
			print "Sending Ports Message"
			websocket.sendMessage("hello")
			# websocket.sendMessage(json.dumps({"type":"ports", "ports":ports}))
		old_ports = ports
		# time.sleep(0.05)

class EchoServerProtocol(WebSocketServerProtocol):

	def sendPorts(self):
		ports = check_ports()
		self.sendMessage(json.dumps({"type":"ports", "ports":ports}))

	def onMessage(self, msg, binary):
		logging.info("Received message: %s", msg)
		print "Received message: ", msg
		message = json.loads(msg)
		
		if message["type"] == "version":
			self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
		elif message["type"] == "flash":
			if platform.system() == "Windows":
                                message["prt"] = '\\\\.\\' + message["prt"]
			flash_arduino(message["cpu"], message["ptc"], message["prt"], message["bad"], message["binary"])
		elif message["type"] == "message":
			print message["text"]
		elif message["type"] == "list_ports":
			reactor.callLater(1, self.sendPorts)
		elif message["type"] == "check_drivers":
			check_drivers(self)
		elif message["type"] == "install_drivers":
			do_install_drivers()
		else:
			self.sendMessage(msg, binary)

	def onOpen(self):
		self.sendMessage(json.dumps({"text":"Socket Opened"}));

		# # Create a thread as follows
		# try:
		# 	thread.start_new_thread(update_ports, (self, ))
		# except:
		# 	print "Error: unable to start thread"

log.startLogging(sys.stdout)

list = []

# ?
if __name__ == '__main__':

	factory = WebSocketServerFactory("ws://localhost:9000", debug = False)
	factory.protocol = EchoServerProtocol
	listenWS(factory)
	reactor.run()
