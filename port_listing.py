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
			websocket.sendMessage(json.dumps({"type":"ports", "ports":ports}))
		old_ports = ports
		time.sleep(0.05)
