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
        self.name = "py2exe sample files"


myservice = Target(
    description = 'codebender python webserial daemon service',
    modules = ['service'],
    cmdline_style='pywin32'
)

setup(
    options = {"py2exe": {"compressed": 1, "bundle_files": 1} },
    console=["mywinserver.py"],
    zipfile = None,
    service=[myservice]
)
