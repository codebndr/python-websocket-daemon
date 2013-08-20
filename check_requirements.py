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
