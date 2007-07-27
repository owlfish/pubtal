""" Utility classes to help automate the PubTal testing.

	Copyright (c) 2004 Colin Stewart (http://www.owlfish.com/)
	All rights reserved.
		
	Redistribution and use in source and binary forms, with or without
	modification, are permitted provided that the following conditions
	are met:
	1. Redistributions of source code must retain the above copyright
	   notice, this list of conditions and the following disclaimer.
	2. Redistributions in binary form must reproduce the above copyright
	   notice, this list of conditions and the following disclaimer in the
	   documentation and/or other materials provided with the distribution.
	3. The name of the author may not be used to endorse or promote products
	   derived from this software without specific prior written permission.
	
	THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
	IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
	OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
	IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
	INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
	NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
	DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
	THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
	THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
	
	If you make any bug fixes or feature enhancements please let me know!

"""

try:
	import logging
except:
	import InfoLogging as logging
	
import os, os.path, copy, md5, getpass
import xml.sax, xml.sax.handler, StringIO

class BlockFilter:
	def filter (self, msg):
		return 0

class UserInteraction:
	""" This class defines the interface that should be provided to 
		interact with the core PubTal library.
		
		This implementation is for command line clients.
		It isn't neseccary to inherit from this class.
	"""
	def prompt (self, msg):
		return raw_input ('%s: ' % msg)
		
	def promptPassword (self, msg):
		return getpass.getpass ('%s: ' % msg)
	
	def taskProgress (self, msg, percentageDone):
		print "(%s %%) %s" % (str (int (percentageDone)), msg)
		
	def taskError (self, msg):
		print "ERROR: %s" % msg
	
	def taskDone (self):
		print "Finished."
		
	def warn (self, msg):
		print "Warning: %s" % msg
	
	def info (self, msg):
		print msg
		
class SilentUI (UserInteraction):
	def prompt (self, msg):
		return ""
		
	def promptPassword (self, msg):
		return ""
	
	def taskProgress (self, msg, percentageDone):
		pass
		
	def taskError (self, msg):
		pass
	
	def taskDone (self):
		pass
		
	def warn (self, msg):
		pass
	
	def info (self, msg):
		pass

class SiteBuilder:
	def __init__ (self, location=None):
		self.log = logging.getLogger ("PubTal.SiteCreation")
		if (location is None):
			self.siteDir = os.tempnam()
		else:
			self.siteDir = location
		
		if (os.access (self.siteDir, os.F_OK)):
			msg = "Directory %s already exists!" % self.siteDir
			self.log.error (msg)
			raise Exception (msg)
	
	def buildDirs (self, templateDir="template", destinationDir="dest", contentDir="content"):
		self.log.debug ("Building site directory %s" % self.siteDir)
		os.mkdir (self.siteDir)
		
		self.contentDir = os.path.join (self.siteDir, contentDir)
		self.log.debug ("Building content directory %s" % self.contentDir)
		os.mkdir (self.contentDir)
		
		self.destinationDir = os.path.join (self.siteDir, destinationDir)
		self.log.debug ("Building destination directory %s" % self.destinationDir)
		os.mkdir (self.destinationDir)
			
		self.templateDir = os.path.join (self.siteDir, templateDir)
		self.log.debug ("Building template directory %s" % self.templateDir)
		os.mkdir (self.templateDir)
		
	def createContent (self, filePath, content):
		self.log.debug ("Creating content file %s" % filePath)		
		destPath = os.path.join (self.contentDir, filePath)
		self._createDirsAndFile_ (destPath, content)
		
	def createTemplate (self, filePath, template):
		self.log.debug ("Creating template file %s" % filePath)		
		destPath = os.path.join (self.templateDir, filePath)
		self._createDirsAndFile_ (destPath, template)
		
	def createConfigFile (self, filePath, config):
		self.log.debug ("Creating configuration file %s" % filePath)		
		destPath = os.path.join (self.siteDir, filePath)
		self._createDirsAndFile_ (destPath, config)
		
	def getSiteDir (self):
		return self.siteDir
		
	def getContentDir (self):
		return self.contentDir
		
	def getDestDir (self):
		return self.destinationDir
		
	def _createDirsAndFile_ (self, destPath, content):
		# Make directories if required.
		destDir = os.path.split (destPath)[0]
		if (not os.path.exists (destDir)):
			os.makedirs (destDir)
		dest = open (destPath, 'w')
		dest.write (content)
		dest.close()
		
	def destroySite (self):
		self.log.debug ("Destroying site directory and contents")
		pathCleaner = pathRemover ()
		pathCleaner.walk (self.siteDir)
		
class PageBuilder:
	""" A class for determining the pages to be generated."""
	def __init__ (self, config, ui=SilentUI()):
		self.ui = ui
		self.config = config
		self.messageBus = self.config.getMessageBus()
		self.contentConfig = config.getContentConfig()
		self.currentContent = []
		self.log = logging.getLogger ('PageBuilder')
		self.contentDir = config.getContentDir()
		self.destDir = config.getDestinationDir()
		self.ignoreFilters = config.getIgnoreFilters()
		
	def getPages (self, target, options={}):
		""" Returns a Page list
		
			target is either:
				None 		- Get all files
				List of files or dir paths.
		"""
		result = []
		
		self.messageBus.notifyEvent ("PageBuilder.Start", options)
		if (target is None):
			self.log.info ("Building whole site.")
			self.ui.info ("Building whole site.")
			targetList = [self.contentDir]
		else:
			targetList = []
			for t in target:
				tFile = os.path.normpath (os.path.abspath (t))
				if (hasattr (os.path, "realpath")):
					# Under Unix and 2.2 we can remove symlinks.
					tFile = os.path.realpath (tFile)
				targetList.append (os.path.abspath (tFile))
			
		self.log.debug ("Target path: %s" % str (targetList))
		for targetPath in targetList:
			self.log.debug ("Checking target path: %s" % targetPath)
			# Are we doing just one file or a dir?
			if (os.path.isfile (targetPath)):
				# Just get this entry
				try:
					result.extend (self.contentConfig.getPages (targetPath, options))
				except:
					self.ui.taskError ("Unable to build Page %s" % targetPath)
					self.messageBus.notifyEvent ("PageBuilder.Error")
					raise
			else:
				os.path.walk (targetPath, self.walkPaths, None)
				for content in self.currentContent:
					try:
						result.extend (self.contentConfig.getPages (content, options))
					except:
						self.ui.taskError ("Unable to build Page %s" % content)
						self.messageBus.notifyEvent ("PageBuilder.Error")
						raise
			self.currentContent = []
		self.messageBus.notifyEvent ("PageBuilder.End")
		return result
		
	def walkPaths (self, arg, dirname, names):
		for name in names:
			self.log.debug ("Checking path %s for content." % os.path.join (dirname, name))
			realName = os.path.join (dirname, name)
			if (os.path.isfile (realName)):
				contentFile = 1
				for filter in self.ignoreFilters:
					if (filter.match (realName)):
						contentFile = 0
				if (contentFile):
					self.currentContent.append (realName)
				else:
					self.log.debug ("Ignoring path %s" % realName)
		
class pathRemover:
	def __init__ (self):
		self.dirsToRemove = []
		self.log = logging.getLogger ("PubTal.SiteCreation.pathRemover")
		
	def walk (self, path):
		self.dirsToRemove = [path]
		os.path.walk (path, self.walking, None)
		# Now remove all of the directories we saw, starting with the last one
		self.dirsToRemove.reverse()
		for dir in self.dirsToRemove:
			os.rmdir (dir)
		self.dirsToRemove = []
		
	def walking (self, arg, dirname, names):
		for name in names:
			#self.log.debug ("Would delete file: %s" % os.path.join (dirname, name))
			target = os.path.join (dirname, name)
			if (os.path.islink (target)):
				os.remove (target)
			elif (os.path.isfile (target)):
				os.remove (target)
			elif (os.path.isdir (target)):
				self.dirsToRemove.append (target)
			else:
				self.log.error ("Path %s is neither a directory or a file!" % target)
				
class XMLChecksumHandler (xml.sax.handler.ContentHandler, xml.sax.handler.DTDHandler, xml.sax.handler.ErrorHandler):
	""" A class that parses an XML document and generates an MD5 checksum for the document.
		This allows two XML documents to be compared, ignoring differences in attribute ordering and other
		such differences.
	"""
	def __init__ (self, parser):
		xml.sax.handler.ContentHandler.__init__ (self)
		self.ourParser = parser
		
	def startDocument (self):
		self.digest = md5.new()
		
	def startPrefixMapping (self, prefix, uri):
		self.digest.update (prefix)
		self.digest.update (uri)
		
	def endPrefixMapping (self, prefix):
		self.digest.update (prefix)
		
	def startElement (self, name, atts):
		self.digest.update (name)
		allAtts = atts.getNames()
		allAtts.sort()
		for att in allAtts:
			self.digest.update (att)
			self.digest.update (atts [att])
			
	def endElement (self, name):
		self.digest.update (name)
		
	def characters (self, data):
		self.digest.update (data)
		
	def processingInstruction (self, target, data):
		self.digest.update (target)
		self.digest.update (data)
		
	def skippedEntity (self, name):
		self.digest.update (name)
		
	# DTD Handler
	def notationDecl(self, name, publicId, systemId):
		self.digest.update (name)
		self.digest.update (publicId)
		self.digest.update (systemId)
		
	def unparsedEntityDecl(name, publicId, systemId, ndata):
		self.digest.update (name)
		self.digest.update (publicId)
		self.digest.update (systemId)
		self.digest.update (ndata)
		
	def error (self, excpt):
		print "Error: %s" % str (excpt)
		
	def warning (self, excpt):
		print "Warning: %s" % str (excpt)
		
	def getDigest (self):
		return self.digest.hexdigest()


class DirCompare:
	def __init__ (self):
		self.xmlParser = None
		
	def compare (self, path, expected, comparisonFunc = None):
		""" By default do a string comparison between all files in the given path, and all expected files.
			Use compare (path, expected, comparisonFun = dirCompare.compareXML) to do an XML comparison.
		"""
		self.expected = copy.copy (expected)
		self.path = path
		self.badFile = None
		if (comparisonFunc is None):
			comparisonFunc = self.compareStrings
		
		os.path.walk (path, self.walking, comparisonFunc)
		
		if (self.badFile is not None):
			return self.badFile
			
		if (len (self.expected) > 0):
			return "Missing files: " + str (self.expected.keys())
		return None
		
	def compareStrings (self, target, relTarget):
		testFile = open (target, 'r')
		content = testFile.read()
		testFile.close()
		if (content != self.expected [relTarget]):
			self.badFile = "File %s had content:\n%s\nexpected:\n%s\n" % (relTarget, content, self.expected [relTarget])
			return 0
		return 1
		
	def compareXML (self, target, relTarget):
		""" Compares XML documents, discounting ordering of attributes, etc.
		"""
		if (self.xmlParser is None):
			self.xmlParser = xml.sax.make_parser()
			self.xmlParser.setFeature (xml.sax.handler.feature_external_ges, 0)
			self.xmlParser.setFeature (xml.sax.handler.feature_namespaces, 1)
			self.checksumHandler = XMLChecksumHandler(self.xmlParser)
			self.xmlParser.setContentHandler (self.checksumHandler)
			self.xmlParser.setDTDHandler (self.checksumHandler)
			self.xmlParser.setErrorHandler (self.checksumHandler)
			
		# Get the XML checksum of the file we are testng.
		testFile = open (target, 'r')
		self.xmlParser.parse (testFile)
		realChecksum  = self.checksumHandler.getDigest()
		testFile.close()
		
		# Get the XML checksu mof the expected result.
		testFile = StringIO.StringIO (self.expected [relTarget])
		self.xmlParser.parse (testFile)
		expectedChecksum  = self.checksumHandler.getDigest()
		testFile.close()
		
		if (realChecksum != expectedChecksum):
			testFile = open (target, 'r')
			content = testFile.read()
			testFile.close()
			self.badFile = "File %s had content:\n%s\nexpected:\n%s\n" % (relTarget, content, self.expected [relTarget])
			return 0
		return 1
		
	def walking (self, arg, dirname, names):
		if (self.badFile is not None):
			return
		comparisonFunc = arg
		commonRoot = os.path.commonprefix ([self.path, dirname])
		for name in names:
			target = os.path.join (dirname, name)
			relTarget = target[len (commonRoot)+1:]
			if (os.path.isfile (target)):
				if (not self.expected.has_key (relTarget)):
					self.badFile = "Found unexepected file %s" % relTarget
					return
					
				if (not comparisonFunc (target, relTarget)):
					return
				del self.expected [relTarget]
					
