#!/usr/bin/python
#	
#	uploadSite.py - Part of PubTal
#
#	Usage: uploadSite.py [options] site.config [dest-dir | dest-file] [...]
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

from pubtal import SitePublisher, SiteConfiguration, SiteUploader, SiteUtils

class UploadSite:
	def __init__ (self, configFile, ui = SiteUtils.UserInteraction()):
		self.config = SiteConfiguration.SiteConfig (configFile)
		self.uploader = SiteUploader.SiteUploader (self.config)
		self.log = logging.getLogger ("UploadSite")
		self.ui = ui
		
	def uploadSite (self, args, options):
		if (len (args) == 0):
			targets = None
		else:
			targets = args
		
		allUploadConfigs = self.config.getUploadConfigs()
		if (len (allUploadConfigs) == 0):
			self.log.warn ("No upload methods defined.")
			self.ui.warn ("No upload methods defined.")
		for config in allUploadConfigs:
			self.uploader.uploadSite (config, self.ui, targets, options)
		self.config.finished()
		
def usage ():
	print """
  uploadSite.py [options] site.config [dest-dir | dest-file] [...]
  version: %s
  
  PubTal utilty to upload a generated website.
  options include:
    -h | --help            : Print this message.
    -a | --all             : Process all files, not just ones PubTal produces.
         --force           : Process files that haven't changed.
         --uptodate        : Mark the files as having already been uploaded.
         --dry-run         : Print out what would have been done, but
                             take no action.
         --logging         : Enable logging, defaults to INFO messages only.
         --logfile name    : Specify the log file location (defaults to 
                             uploadSite.log)
         --debug           : Add DEBUG messages to the logfile (implies
                             --logging)
""" % pubtal.__version__
		
def main (args):
	try:
		opts, args = getopt.getopt (args, "ha", ["help", "all", "force", "uptodate", "dry-run", "logging", "logfile=", "debug", "debug-simpletal"])
	except getopt.GetoptError:
		usage()
		sys.exit (2)
		
	if (len (args) == 0):
		usage()
		sys.exit (2)
	
	options = {}
	enableLogging = 0
	pubtalLogging = logging.INFO
	simpletalLogging = logging.INFO
	logFile = "uploadSite.log"
	for opt, arg in opts:
		if (opt == '-h' or opt == '--help'):
			usage()
			sys.exit (0)
		elif (opt == '-a' or opt == '--all'):
			options ['allFiles'] = 1
		elif (opt == "--logging"):
			enableLogging=1
		elif (opt == "--logfile"):
			logFile = arg
		elif (opt == '--force'):
			options ['forceUpload'] = 1
		elif (opt == '--uptodate'):
			options ['markFilesUpToDate'] = 1
		elif (opt == '--dry-run'):
			options ['dry-run'] = 1
		elif (opt == '--debug'):
			pubtalLogging = logging.DEBUG
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
	
	update = UploadSite (args[0])
	update.uploadSite(args[1:], options)

if __name__ == '__main__':
	main (sys.argv [1:])
		
