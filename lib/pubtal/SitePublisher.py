""" Classes to handle publishing of a PubTal site.

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
	
import time, codecs, os, os.path, md5

from simpletal import simpleTAL, simpleTALES, simpleTALUtils
import pubtal
import timeformat

import ContentToHTMLConverter, SiteUtils, DateContext

class PagePublisher:
	def __init__ (self, config, ui=SiteUtils.SilentUI()):
		self.ui = ui
		self.templateCache = simpleTALUtils.TemplateCache()
		self.templateDir = config.getTemplateDir()
		self.destDir = config.getDestinationDir()
		self.characterSet = config.getDefaultCharacterSet()
		self.templateConfig = config.getTemplateConfig()
		self.config = config
		self.messageBus = self.config.getMessageBus()
		self.localCache = config.getLocalCacheDB()
		
		supportedContent = config.getSupportedContent()
		self.supportedContent = {}
		
		self.log = logging.getLogger ("PubTal.PagePublisher")
		
		self.log.info ("Looking for supported content types...")
		for contentType in supportedContent.keys():
			klass = supportedContent [contentType]
			obj = klass (self)
			self.supportedContent [contentType] = obj
		
		msg = "Support for content types: %s" % ", ".join (self.supportedContent.keys())		
		self.log.info (msg)
		ui.info (msg)
			
		# Used in the Context
		self.ContextFunctions = ContextFunctions(self.config)
		self.pubTalInfo = {'version': pubtal.__version__
							,'url': "http://www.owlfish.com/software/PubTal/"
							,'linkText': """<p title="PubTal is a template driven web site publisher.">Made with <a href="http://www.owlfish.com/software/PubTal/">PubTal</a> %s</p>""" % pubtal.__version__
						}
		self.messageBus.notifyEvent ("PagePublisher.InitComplete")
	
	def getUI (self):
		return self.ui
	
	def getConfig (self):
		return self.config
		
	def getContentPublisher (self, contentType):
		return self.supportedContent.get (contentType, None)
		
	def publish (self, page):
		contentType = page.getOption ('content-type')
		try:
			publisher = self.supportedContent [contentType]
		except:
			msg = "Unsupported content type: %s" % contentType
			self.log.warn (msg)
			self.ui.warn (msg)
			return 1
		
		try:
			publisher.publish (page)
			return 1
		except Exception, e:
			self.log.error ("Exception publishing page: %s" % repr (e))
			self.ui.taskError ("Page Publication failed: %s " % str (e))
			return 0
		
	def expandTemplate (self, template, context, relativeOutputPath, macros):
		""" Expand the given Template object using the context, writing to the
			output path.
			
			Looks up the character-set for each template and macro.
		"""
		absTemplateName = template.getTemplatePath()
		templateCharset = template.getOption ('character-set', self.characterSet)
		suppressXMLDeclaration = template.getOption ('suppress-xmldecl')
		outputType = template.getOption ('output-type')
		if (outputType == 'HTML'):
			# For HTML output-type we guess as to the SimpleTAL template kind
			taltemplate = self.templateCache.getTemplate (absTemplateName, inputEncoding=templateCharset)				
		else:
			# Assume it's XML
			taltemplate = self.templateCache.getXMLTemplate (absTemplateName)
		
		# Handle XHTML DOCTYPE
		xmlDoctype = template.getOption ('xml-doctype', None)
		
		self.ContextFunctions.setCurrentPage (relativeOutputPath, context)
		context.addGlobal ('ispage', self.ContextFunctions.isPage)
		context.addGlobal ('readFile', self.ContextFunctions.readFile)
		context.addGlobal ('pubtal', self.pubTalInfo)
		
		# Add macros to the context
		macroTemplates = {}
		for macroName in macros.keys():
			macTemplate = self.templateConfig.getTemplate (macros [macroName])
			macroCharSet = macTemplate.getOption ('character-set', self.characterSet)
			
			mTemp = self.templateCache.getTemplate (macros [macroName], inputEncoding=macroCharSet)
			macroTemplates [macroName] = mTemp.macros
		
		context.addGlobal ('macros', macroTemplates)
		
		if (self.log.isEnabledFor (logging.DEBUG)):
			self.log.debug (str (context))
		dest = self.openOuputFile (relativeOutputPath)
		if (isinstance (taltemplate, simpleTAL.XMLTemplate)):
			if (xmlDoctype is not None):
				taltemplate.expand (context, dest, outputEncoding=templateCharset, docType=xmlDoctype, suppressXMLDeclaration=suppressXMLDeclaration)
				dest.close()
				return
			else:
				taltemplate.expand (context, dest, outputEncoding=templateCharset, suppressXMLDeclaration=suppressXMLDeclaration)
				dest.close()
				return
		taltemplate.expand (context, dest, outputEncoding=templateCharset)
		dest.close()
		
	def openOuputFile (self, relativeOutputPath):
		""" Creates and required directories and opens a file-like object to the
			destination path.
		
			This provides a common point for PubTal to note all directories it has
			created and files it has written.  The file-like object will keep track
			of the MD5 of the file written.
		"""
		# Make directories if required.
		outputPath = os.path.join (self.destDir, relativeOutputPath)
		destDir = os.path.split (outputPath)[0]
		if (not os.path.exists (destDir)):
			os.makedirs (destDir)
		dest = MD5File (outputPath, relativeOutputPath, 'wb', self.localCache)
		return dest
		
class MD5File:
	""" This presents a file object to the world, and calculates an MD5 checksum
		on the fly.  When the file is closed it updates a dictionary with the 
		resulting hex digest.
		
		This file type should only be used for writing!
	"""
	def __init__ (self, filePath, relativeOutputPath, mode, dictionary):
		self.dictionary = dictionary
		self.ourmd5 = md5.new()
		self.ourFile = open (filePath, mode)
		# We need to transform the path name into ascii compatible strings for some anydbm implementations.
		utfencode = codecs.lookup ("utf8")[0]
		self.relativeOutputPath = utfencode (relativeOutputPath)[0]
		self.closed = 0
		
	def close (self):
		self.ourFile.close()
		self.dictionary [self.relativeOutputPath] = self.ourmd5.hexdigest()
		self.closed = 1
		
	def __del__ (self):
		if (not self.closed):
			self.close()
		
	def flush (self):
		return self.ourFile.flush()
		
	def fileno (self):
		return self.ourFile.fileno()
		
	def read (self, size=None):
		return self.ourFile.read(size)
	
	def readline (self, size=None):
		return self.ourFile.readline(size)
		
	def readlines (self, size=None):
		return self.ourFile.readlines (size)
		
	def xreadlines (self):
		return self.ourFile.xreadlines()
		
	def seek (self, offset, wence=0):
		return self.ourFile.seek(offset, wence)
		
	def tell (self):
		return self.ourFile.tell()
		
	def truncate (self, size=None):
		return self.ourFile.truncate (size)
		
	def write (self, str):
		self.ourFile.write (str)
		self.ourmd5.update (str)
		
	def writelines (self, aseq):
		for value in aseq:
			self.ourmd5.update (value)
			self.ourFile.write (value)
			
	def __itter__ (self):
		return self.ourFile.__itter__()

class ContextFunctions:
	def __init__ (self, siteConfig):
		self.log = logging.getLogger ("PubTal.PagePublisher")
		self.currentTargetPath = None
		self.currentContext = None
		self.config = siteConfig
		self.contentDir = self.config.getContentDir()
		self.destinationDir = self.config.getDestinationDir()
		self.isPage = simpleTALES.PathFunctionVariable (self.isCurrentPage)
		self.readFile = simpleTALES.PathFunctionVariable (self.readExternalFile)
		
	def setCurrentPage (self, targetPath, context):
		self.currentTargetPath = targetPath.replace (os.sep, '/')
		self.currentContext = context
		
	def isCurrentPage (self, targetPath):
		if (self.currentTargetPath == targetPath.replace (os.sep, '/')):
			return 1
		return 0
		
	def readExternalFile (self, targetPath):
		# Start by evaluating the targetPath to resolve the filename
		targetFileName = self.currentContext.evaluate (targetPath)
		self.log.info ("Resolved path %s to filename %s" % (targetPath, str (targetFileName)))
		if (targetFileName):
			# Read the file (relative to the content directory)
			try:
				targetFile = open (os.path.join (self.contentDir, targetFileName))
				targetData = targetFile.read()
				targetFile.close()
				return targetData
			except Exception, e:
				self.log.error ("Error reading file %s: %s" % (os.path.join (self.contentDir, targetFileName), str (e)))
				raise 
		return None
		
		

class ContentPublisher:
	def __init__ (self, pagePublisher):
		self.pagePublisher = pagePublisher
		self.config = self.pagePublisher.config
		self.contentConfig = self.config.getContentConfig()
		self.templateConfig = self.config.getTemplateConfig()
		self.characterSet = self.config.getDefaultCharacterSet()
		self.characterSetCodec = codecs.lookup (self.characterSet)[1]
		self.destDir = self.config.getDestinationDir()
		self.contentDir = self.config.getContentDir()
		
	def readHeadersAndContent (self, page, preserveCharacterSet = 0):
		""" This method reads the source file for this page, and then
			returns the headers defined in this file and the raw
			content of the body of the file.
			
			If preserveCharacterSet is false then Unicode is returned.
		"""
		sourceFile = open (page.getSource(), 'r')
		readingHeaders = 1
		headers = {}
		if (not preserveCharacterSet):
			pageCharSet = page.getOption ('character-set', None)
			if (pageCharSet is not None):
				# This page has it's own character set
				pageCodec = codecs.lookup (pageCharSet)[1]
			else:
				# This page uses the default character set.
				pageCodec = self.characterSetCodec
		else:
			# We use a dummy function that doesn't alter the string if we are preserving the character set.
			pageCodec = lambda decodedString: (decodedString, 0)
		while (readingHeaders):
			line = pageCodec (sourceFile.readline())[0]
			offSet = line.find (':')
			if (offSet > 0):
				headers [line[0:offSet]] = line[offSet + 1:].strip()
			else:
				readingHeaders = 0
		rawContent = pageCodec (sourceFile.read())[0]
		sourceFile.close()
		return (headers, rawContent)
						
	def getPageContext (self, page, template):
		""" Returns the default context which will apply to most pages of
			content.  Template is the template that this context will 
			eventually be used in, and is used to extract the type
			of output (HTML, XHTML, WML, etc) and the destination
			file extension.
		"""
		copyrightYear = timeformat.format ('%Y')
		
		destExtension = '.' + template.getTemplateExtension()
		relativeDestPath = os.path.splitext (page.getRelativePath())[0] + destExtension
		destPath = os.path.join (self.destDir, relativeDestPath)
		destFilename = os.path.basename (destPath)
		
		pageContext = {'lastModifiedDate': DateContext.Date (time.localtime (page.getModificationTime()), '%a[SHORT], %d %b[SHORT] %Y %H:%M:%S %Z')
					,'copyrightYear': DateContext.Date (time.localtime(), '%Y')
					,'sourcePath': page.getRelativePath()
					,'absoluteSourcePath': page.getSource()
					,'destinationPath': relativeDestPath
					,'absoluteDestinationPath': destPath
					,'destinationFilename': destFilename
					,'depth': page.getDepthString()
					,'headers': page.getHeaders()
					}
		
		siteURLPrefix = page.getOption ('url-prefix')
		if (siteURLPrefix is not None):
			pageContext ['absoluteDestinationURL'] = '%s/%s' % (siteURLPrefix, relativeDestPath)
					
		return pageContext
	
class PublisherException (Exception):
	pass