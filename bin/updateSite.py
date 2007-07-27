#!/usr/bin/python
#	
#	updateSite.py - Part of PubTal
#
#	Usage: updateSite.py site.config [content-dir | content-file] [...]
#
#	Copyright (c) 2004 Colin Stewart (http://www.owlfish.com/)
#	All rights reserved.
#		
#	Redistribution and use in source and binary forms, with or without
#	modification, are permitted provided that the following conditions
#	are met:
#	1. Redistributions of source code must retain the above copyright
#	   notice, this list of conditions and the following disclaimer.
#	2. Redistributions in binary form must reproduce the above copyright
#	   notice, this list of conditions and the following disclaimer in the
#	   documentation and/or other materials provided with the distribution.
#	3. The name of the author may not be used to endorse or promote products
#	   derived from this software without specific prior written permission.
#		
#	THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#	IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#	OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#	IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#	INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#	NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#	DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#	THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#	(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#	THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#	
#	If you make any bug fixes or feature enhancements please let me know!
#

try:
	import logging
	LOGGING_EXISTS=1

except:
	from pubtal import InfoLogging as logging
	LOGGING_EXISTS=0
	
import sys, os.path, os, stat, getopt

import pubtal

from pubtal import SitePublisher, SiteConfiguration, SiteUtils

class UpdateSite:
	def __init__ (self, configFile, path=None, options={}, ui=SiteUtils.UserInteraction()):
		self.ui = ui
		self.config = SiteConfiguration.SiteConfig (configFile)
		self.pageBuilder = SiteUtils.PageBuilder (self.config, self.ui)
		self.options = options
		self.target = path
		self.log = logging.getLogger ("UpdateSite")
		self.publisher = SitePublisher.PagePublisher (self.config, self.ui)
		
	def buildSite (self):
		pagesToBuild = self.pageBuilder.getPages (self.target, self.options)
		if (len (pagesToBuild) == 0):
			self.ui.info ("No pages to build.")
		else:
			self.log.debug ("Found pages: %s" % str (pagesToBuild))
			percentage=0.0
			increment = 100.0 / float (len (pagesToBuild))
			for aPage in pagesToBuild:
				self.log.info ("Publishing: %s" % str (aPage))
				self.ui.taskProgress ("Publishing %s" % str (aPage), percentage)
				percentage += increment
				if (not self.publisher.publish (aPage)):
					self.config.finished()
					return
		self.config.finished()
		
def usage ():
	print """
  updateSite.py [options] site.config [content-dir | content-file] [...]
  version: %s
  
  PubTal utilty to upload a generated website.
  options include:
    -h | --help            : Print this message.
    -a | --all             : Build all classes of content, not just normal content.
         --class classList : Comma separated list of classes to build.
         --logging         : Enable logging, defaults to INFO messages only.
         --logfile name    : Specify the log file location (defaults to 
                             updateSite.log)
         --debug           : Add DEBUG messages to the logfile (implies
                             --logging)
         --debug-simpletal : Add SimpleTAL DEBUG messages to the logfile
                             (implies --logging)
""" % pubtal.__version__

def main (args):
	try:
		opts, leftargs = getopt.getopt (args, "ha", ["help", "all", "class=", "logging", "logfile=", "debug", "debug-simpletal"])
	except getopt.GetoptError:
		usage()
		sys.exit (2)
		
	if (len (args) == 0):
		usage()
		sys.exit (2)
	
	enableLogging = 0
	options = {}
	pubtalLogging = logging.INFO
	simpletalLogging = logging.INFO
	logFile = "updateSite.log"
	for opt, arg in opts:
		if (opt == '-h' or opt == '--help'):
			usage()
			sys.exit (0)
		elif (opt == "--all" or opt == "-a"):
			options ['buildAllClasses'] = 1
		elif (opt == "--class"):
			options ['classes'] = arg
		elif (opt == "--logging"):
			enableLogging=1
		elif (opt == "--logfile"):
			logFile = arg
		elif (opt == '--debug'):
			pubtalLogging = logging.DEBUG
			enableLogging=1
		elif (opt == '--debug-simpletal'):
			simpletalLogging = logging.DEBUG
			enableLogging=1
	
	if (LOGGING_EXISTS):
		root = logging.getLogger()
		if (enableLogging):
			handler = logging.FileHandler (logFile)
			root.addHandler (handler)
			handler.setFormatter (logging.Formatter ('%(asctime)s %(levelname)s  %(name)s - %(message)s'))
			root.setLevel (pubtalLogging)
			talLogger = logging.getLogger ("simpleTAL")
			talLogger.setLevel (simpletalLogging)
			talesLogger = logging.getLogger ("simpleTALES")
			talesLogger.setLevel (simpletalLogging)
		else:
			root.addHandler (logging.StreamHandler())
			root.addFilter (SiteUtils.BlockFilter())
			logging.disable (logging.CRITICAL)
		
	if (len (leftargs) == 0):
		usage()
		sys.exit (1)
	elif (len (leftargs) == 1):
		update = UpdateSite (leftargs[0], path=None, options=options)
	else:
		update = UpdateSite (leftargs[0], path=leftargs[1:], options=options)
	update.buildSite()
	
	
if __name__ == '__main__':
	main(sys.argv[1:])
