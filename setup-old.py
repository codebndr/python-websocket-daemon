from distutils.core import setup
import py2exe

my_data_files = [('avrdudes/Windows', ['avrdudes/Windows/avrdude.conf']),
                ('avrdudes/Windows', ['avrdudes/Windows/avrdude.exe']),
                ('avrdudes/Windows', ['avrdudes/Windows/libusb0.dll']),
                ('drivers/Windows', ['drivers/Windows/arduino.cat']),
                ('drivers/Windows', ['drivers/Windows/arduino.inf']),
                ('drivers/Windows', ['drivers/Windows/dpinst-x86.exe']),
                ('drivers/Windows', ['drivers/Windows/dpinst-amd64.exe']),
                ('vcredist_x86.exe')]



setup(options = {"py2exe": {"compressed": 1, "bundle_files": 1} },
      zipfile = None,
      data_files = my_data_files,
      console=['myserver.py'])
