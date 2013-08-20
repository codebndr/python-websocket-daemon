def install_drivers_osx():
	os.system("""osascript -e 'do shell script "/usr/sbin/installer -pkg drivers/Darwin/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/ -target /" with administrator privileges'""")	

def install_drivers_windows():
        if platform.architecture()[0] == "32bit":
                os.system(os.getcwd() + "/drivers/Windows/dpinst-x86.exe /sw")
        else:
                os.system(os.getcwd() + "/drivers/Windows/dpinst-amd64.exe /sw")

def fix_permissions_linux():
	os.system("pkexec gpasswd -a " + os.getlogin() + " $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)")

def install_drivers():
	if platform.system() == "Darwin":
		install_drivers_osx()
	elif platform.system() == "Windows":
                install_drivers_windows()
	elif platform.system() == "Linux":
		fix_permissions_linux()

def do_install_drivers():
	# Create a thread as follows
	try:
		thread.start_new_thread(install_drivers, ())
	except:
		print "Error: unable to start thread"
