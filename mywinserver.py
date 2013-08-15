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
from autobahn.websocket import HttpException, WebSocketServerFactory, WebSocketServerProtocol, listenWS
from autobahn import httpstatus

import json

import time

import subprocess


import base64
import tempfile

import platform


list = []
serial_port = None
serial_device = None
serial_baudrate = None


logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info("Starting")


def check_drivers_osx(websocket):
	if(os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.FTDIUSBSerialDriver-2.pkg.bom") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.FTDIUSBSerialDriver-2.pkg.plist") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.postflight.pkg.bom") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.postflight.pkg.plist") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.preflight.pkg.bom")):
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
	else:
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))

def check_drivers_windows(websocket):
	if(os.path.exists("C:\Windows/System32/DriverStore/FileRepository/arduino.inf_x86_neutral_f13cf06b4049adb5/arduino.inf") or os.path.exists("C:\Windows/System32/DriverStore/FileRepository/arduino.inf_amd64_neutral_f13cf06b4049adb5/arduino.inf")):
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
	else:
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))

def check_permissions_linux(websocket):
	output = os.popen("groups | grep $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)").read()
	if output != "":
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
	else:
		websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))

#ToDo: rename this to make more sense
def check_drivers(websocket):
	if platform.system() == "Darwin":
		check_drivers_osx(websocket)
	elif platform.system() == "Windows":
		check_drivers_windows(websocket)
	elif platform.system() == "Linux":
		check_permissions_linux(websocket)



def install_drivers_osx():
	return os.system("""osascript -e 'do shell script "/usr/sbin/installer -pkg drivers/Darwin/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/ -target /" with administrator privileges'""")	

def install_drivers_windows():
        if platform.architecture()[0] == "32bit":
                return os.system(os.getcwd() + "/drivers/Windows/dpinst-x86.exe /sw")
        else:
                return os.system(os.getcwd() + "/drivers/Windows/dpinst-amd64.exe /sw")

def fix_permissions_linux():
	os.system("pkexec gpasswd -a " + os.getlogin() + " $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)")

def install_drivers(websocket):
	if platform.system() == "Darwin":
		return_val = install_drivers_osx()
		if(return_val == 0):
			websocket.sendMessage(json.dumps({"type":"installation_output", "success":True}))
		else:
			websocket.sendMessage(json.dumps({"type":"installation_output", "success":False, "error":return_val}))
	elif platform.system() == "Windows":
		return_val = install_drivers_windows()
		if(return_val == 256):
			websocket.sendMessage(json.dumps({"type":"installation_output", "success":True}))
		else:
			websocket.sendMessage(json.dumps({"type":"installation_output", "success":False, "error":return_val}))
	elif platform.system() == "Linux":
		fix_permissions_linux()

def do_install_drivers(websocket):
	# Create a thread as follows
	try:
		thread.start_new_thread(install_drivers, (websocket,))
	except:
		print "Error: unable to start thread"

def check_ports_posix():
	list = list_ports.comports()

	ports = []
	for port in list:
		if(port[0].startswith("/dev/tty") and not port[0].startswith("/dev/ttyS")):
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
        except WindowsError, e:
                if e.errno == 2:
                        return []
                else:
                        raise e

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

def flash_arduino(cpu, ptc, prt, bad, binary):
	bash_shell_cmd = "./avrdudes/" + platform.system() + "/avrdude"
	bash_shell_cnf = " -C./avrdudes/" + platform.system() + "/avrdude.conf"
	bash_shell_cpu = " -p" + cpu
	bash_shell_ptc = " -c" + ptc
	bash_shell_prt = " -P" + prt
	bash_shell_bad = " -b" + bad
	binary = base64.b64decode(binary)
	if platform.system() == "Windows":
                bin_file = tempfile.NamedTemporaryFile(delete=False)
        else:
                bin_file = tempfile.NamedTemporaryFile()
	print "file name: ", bin_file.name
	logging.info("temp filename: %s\n", bin_file.name)
	bin_file.write(binary)
	if platform.system() == "Windows":
                bin_file.close()
	bash_shell_file = " -Uflash:w:" + bin_file.name + ":i"
	bash_shell = bash_shell_cmd + bash_shell_cnf + " -v -v -v -v" + bash_shell_cpu + bash_shell_ptc + bash_shell_prt + bash_shell_bad + " -D" + bash_shell_file
	print "Flashing: ", bash_shell
	logging.info("Flashing cmd:")
	logging.info(bash_shell)
	process = subprocess.Popen(bash_shell.split())
	print "FLASHING!!!"
	#ToDo: Delete the temp file after it's done

class EchoServerProtocol(WebSocketServerProtocol):
	def onMessage(self, msg, binary):
		try:
			message = json.loads(msg)
		except ValueError:
			logging.info("Received message: %s", msg)
			print "Received message: ", msg
		if message["type"] == "ack":
			self.sendMessage(msg, binary)
		else:
			logging.info("Received message: %s", msg)
			print "Received message: ", msg


		if message["type"] == "version":
			self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
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
			do_install_drivers(self)
		elif message["type"] == "set_serial":
			global serial_port
			global serial_device
			global serial_baudrate
			if serial_port == None:
				serial_device = message["port"]
				serial_baudrate = message["baudrate"]
			else:
				self.sendMessage(json.dumps({"type":"error", "message":"You cannot set port while a serial connection is still open"}))
			

	def onConnect(self, request):
		print "peer " + str(request.peer)
		print "peer_host " + request.peer.host
		print "peerstr " + request.peerstr
		print "headers " + str(request.headers)
		print "host " + request.host
		print "path " + request.path
		print "params " + str(request.params)
		print "version " + str(request.version)
		print "origin " + request.origin
		print "protocols " + str(request.protocols)

		#TODO: For development purposes only. Fix this so it doesn't work for null (localhost) as well.
		if(request.peer.host != "127.0.0.1" or (request.origin != "null" and request.origin != "http://codebender.cc")):
			raise HttpException(httpstatus.HTTP_STATUS_CODE_UNAUTHORIZED[0], "You are not authorized for this!")

	def onOpen(self):
		self.factory.register(self)
		self.sendMessage(json.dumps({"text":"Socket Opened"}));
		ports = check_ports()
		print "Sending Ports Message"
		self.sendMessage(json.dumps({"type":"ports", "ports":ports}))

	def connectionLost(self, reason):
		self.factory.unregister(self)
		WebSocketServerProtocol.connectionLost(self, reason)


def update_ports(factory):
	print "Starting check for ports"
	old_ports = []
	while 1:
		ports = check_ports()
		if(ports != old_ports):
			for port in ports:
				print port
			print "Sending Ports Message"
			factory.broadcast(json.dumps({"type":"ports", "ports":ports}))
		old_ports = ports
		time.sleep(0.05)

################### CUSTOM FACTORY ###################
class BroadcastServerFactory(WebSocketServerFactory):
	"""
	Simple broadcast server broadcasting any message it receives to all
	currently connected clients.
	"""

	def __init__(self, url):
		WebSocketServerFactory.__init__(self, url)
		self.clients = []
		self.tick()

		#TODO: Move this to threading model and start/stop the thread only when we have registered clients
		# Create a thread as follows
		try:
			thread.start_new_thread(update_ports, (self, ))
		except:
			print "Error: unable to start thread"

	def tick(self):
		self.broadcast(json.dumps({"type":"heartbeat"}))
		reactor.callLater(1, self.tick)

	def register(self, client):
		if not client in self.clients:
			print "registered client " + client.peerstr
			self.clients.append(client)

	def unregister(self, client):
		if client in self.clients:
			print "unregistered client " + client.peerstr
			self.clients.remove(client)

	def broadcast(self, msg):
		# print "broadcasting message '%s' .." % msg
		for c in self.clients:
			c.sendMessage(msg)
			# print "message sent to " + c.peerstr

################### END CUSTOM FACTORY ###################

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
				data = self.serial_port.read().decode("ascii")
				if(data != ""):
					# sys.stdout.write(data)
					# sys.stdout.flush()
					self.websocket_port.sendMessage(str(data))
		except serial.SerialException, e:
			raise

def writer(serial_port, data):
	serial_port.write(data)


class WebSerialProtocol(WebSocketServerProtocol):
	def __init__(self):
		self.connection_invalid = False

	def onMessage(self, msg, binary):
		# logging.info("Received message: %s", msg)
		# print "Received message: ", msg

		global serial_port
		global serial_device
		global serial_baudrate

		if serial_port != None:
			writer(serial_port, msg)
		else:
			print "Could not send data. No active serial connections"

	def onConnect(self, request):
		print "peer " + str(request.peer)
		print "peer_host " + request.peer.host
		print "peerstr " + request.peerstr
		print "headers " + str(request.headers)
		print "host " + request.host
		print "path " + request.path
		print "params " + str(request.params)
		print "version " + str(request.version)
		print "origin " + request.origin
		print "protocols " + str(request.protocols)

		#TODO: For development purposes only. Fix this so it doesn't work for null (localhost) as well.
		if(request.peer.host != "127.0.0.1" or (request.origin != "null" and request.origin != "http://codebender.cc")):
			self.connection_invalid = True
			raise HttpException(httpstatus.HTTP_STATUS_CODE_UNAUTHORIZED[0], "You are not authorized for this!")

		global serial_port
		global serial_device
		global serial_baudrate

		if(serial_port != None):
			self.connection_invalid = True
			raise HttpException(httpstatus.HTTP_STATUS_CODE_UNAUTHORIZED[0], "You cannot open 2 serial ports!")

		if(serial_device == None or serial_baudrate == None):
			self.connection_invalid = True
			raise HttpException(httpstatus.HTTP_STATUS_CODE_UNAUTHORIZED[0], "You must set serial device first!")

	def onOpen(self):
		global serial_port
		global serial_device
		global serial_baudrate

		print "Connect Message Received"
		serial_port = serial.Serial(serial_device, baudrate= serial_baudrate, timeout=0)
		self.read_thread = ReaderThread(self, serial_port)
		self.read_thread.daemon = True
		self.read_thread.start()

	def connectionLost(self, reason):
		global serial_port
		global serial_device
		global serial_baudrate

		if not self.connection_invalid:
			print "Disconnect Message Received"
			if serial_port != None:
				oldserial = serial_port
				serial_port = None
				serial_device = None
				serial_baudrate = None
				self.read_thread.stop()
				self.read_thread.join()
				oldserial.close()
		WebSocketServerProtocol.connectionLost(self, reason)

################ END OF WEBSERIAL CODE


log.startLogging(sys.stdout)


'''
 Original windows service code:
 
 Author: Alex Baker
 Date: 7th July 2008
 Description : Simple python program to generate wrap as a service based on example on the web, see link below.
 
 http://essiene.blogspot.com/2005/04/python-windows-services.html

 Usage : python aservice.py install
 Usage : python aservice.py start
 Usage : python aservice.py stop
 Usage : python aservice.py remove
 
 C:\>python aservice.py  --username <username> --password <PASSWORD> --startup auto install

'''


import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import os

#import win32traceutil

def main():
      #initializing serial flashing etc utilities socket
      ServerFactory = BroadcastServerFactory

      factory = ServerFactory("ws://localhost:9000")
      # factory = WebSocketServerFactory("ws://localhost:9000", debug = False)
      factory.protocol = EchoServerProtocol
      listenWS(factory)

      factory2 = WebSocketServerFactory("ws://localhost:9001")
      factory2.protocol = WebSerialProtocol
      listenWS(factory2)

      reactor.run()

import servicemanager      

def checkForStop(self):
        
      self.timeout = 3000

      while 1:
         # Wait for service stop signal, if I timeout, loop again
         rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
         # Check to see if self.hWaitStop happened
         if rc == win32event.WAIT_OBJECT_0:
            # Stop signal encountered
            servicemanager.LogInfoMsg("codebender - STOPPED")
            #TODO: Improve this. Windows consider it an error right now
            os._exit(0)
         else:
            servicemanager.LogInfoMsg("codebender - is alive and well")   


class aservice(win32serviceutil.ServiceFramework):
   
   _svc_name_ = "codebender python websocket daemon"
   _svc_display_name_ = "allows the browser to communicate with the usb devices"
   _svc_description_ = "works with awesome"
         
   def __init__(self, args):
           win32serviceutil.ServiceFramework.__init__(self, args)
           self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)           

   def SvcStop(self):
           self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
           win32event.SetEvent(self.hWaitStop)                    
         
   def SvcDoRun(self):
      #import win32traceutil
      #logging.basicConfig(filename='app.log', level=logging.INFO)
      logging.info("running daemon")
      servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))

      servicemanager.LogInfoMsg(os.getcwd())

      #TODO: Move this to threading model and start/stop the thread only when we have registered clients
      # Create a thread as follows
      try:
         thread.start_new_thread(checkForStop, (self, ))
      except:
         print "Error: unable to start thread"
      main()
      
def ctrlHandler(ctrlType):
   return True
                  
if __name__ == '__main__':   
   win32api.SetConsoleCtrlHandler(ctrlHandler, True)   
   win32serviceutil.HandleCommandLine(aservice)
