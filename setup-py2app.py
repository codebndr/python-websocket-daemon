from setuptools import setup

setup(
	options=dict(py2app=dict(
		resources = ['avrdudes/Darwin/avrdude.conf', 'avrdudes/Darwin/avrdude', 'drivers/Darwin/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg'],
		plist = dict(LSBackgroundOnly=True),
		iconfile = "codebender.icns",
	)),
	app=["myserver.py"],
	name="codebender",
	version="0.6",
	setup_requires=["py2app"],
)


# setup(options = {"py2app": {"compressed": 1, "bundle_files": 1} },
#       zipfile = None,
#       data_files = my_data_files,
#       console=['myserver.py'])
