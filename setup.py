# setup.py
from distutils.core import setup
import py2exe

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.1.0"
        self.company_name = "codebender"
        self.copyright = "no copyright"
        self.name = "codebender"


my_data_files = [('avrdudes/Windows', ['avrdudes/Windows/avrdude.conf']),
                ('avrdudes/Windows', ['avrdudes/Windows/avrdude.exe']),
                ('avrdudes/Windows', ['avrdudes/Windows/libusb0.dll']),
                ('drivers/Windows', ['drivers/Windows/arduino.cat']),
                ('drivers/Windows', ['drivers/Windows/arduino.inf']),
                ('drivers/Windows', ['drivers/Windows/dpinst-x86.exe']),
                ('drivers/Windows', ['drivers/Windows/dpinst-amd64.exe']),
                ('vcredist_x86.exe')]

myservice = Target(
    description = 'codebender',
    modules = ['mywinserver'],
    cmdline_style='pywin32'
)

#    console=["mywinserver.py"],
setup(
    options = {"py2exe": {"compressed": 1, "bundle_files": 1} },
    data_files = my_data_files,
    zipfile = None,
    service=[myservice]
)
