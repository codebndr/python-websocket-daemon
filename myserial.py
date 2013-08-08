import os
import serial
from serial.tools import list_ports

import thread

# def list_serial_ports():
#	  # Windows
#	  if os.name == 'nt':
#		  # Scan for available ports.
#		  available = []
#		  for i in range(256):
#			  try:
#				  s = serial.Serial(i)
#				  available.append('COM'+str(i + 1))
#				  s.close()
#			  except serial.SerialException:
#				  pass
#		  return available
#	  else:
#		  # Mac / Linux
#		  return [port[0] for port in list_ports.comports()]
# 
# print(list(list_ports.comports()))
def check_ports():
	list = list_ports.comports()

	ports = []
	for port in list:
		if(port[0].startswith("/dev/tty.")):
			ports.append(port[0])
	return ports

def update_ports():
	old_ports = []
	while 1:
		ports = check_ports()
		if(ports != old_ports):
			for port in ports:
				print port
		old_ports = ports
list = []

# Create a thread as follows
try:
	thread.start_new_thread(update_ports, ())
except:
	print "Error: unable to start thread"

while 1:
	pass

