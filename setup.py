#!/usr/bin/env python

import sys, os
sys.path.insert(0, os.path.join(os.getcwd(),'lib'))
from distutils.core import setup
import pubtal

# Remove any old MANIFEST file.
if (os.access ("MANIFEST", os.F_OK)):
	os.remove ("MANIFEST")
setup(name="PubTal",
	version=pubtal.__version__,
	description="A template driven web site builder for small sites.",
	long_description="PubTal is a template driven web site builder for small web sites.",
	author="Colin Stewart",
	author_email="colin@owlfish.com",
	url="http://www.owlfish.com/software/PubTal/index.html",
	packages=[
		'pubtal', 'pubtal.plugins', 'pubtal.plugins.openOfficeContent'
		,'pubtal.plugins.weblog'
	],
	package_dir = {'': 'lib'},
	scripts = ['bin/updateSite.py', 'bin/uploadSite.py'],
)
