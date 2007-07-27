""" Classes to handle HTMLText and Catalogues in PubTal.

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
	
import SitePublisher, CatalogueContent, ContentToHTMLConverter, SiteUploader, FtpLibrary
import os, time, anydbm, codecs
import timeformat
from simpletal import simpleTAL, simpleTALES
						
# getPluginInfo provides the list of built-in supported content.
def getPluginInfo ():
	builtInContent = [{'functionality': 'content', 'content-type': 'HTMLText' ,'file-type': 'txt','class': HTMLTextPagePublisher}
					, {'functionality': 'content', 'content-type': 'Catalogue','file-type': 'catalogue','class': CataloguePublisher}
					, {'functionality': 'upload-method', 'method-type': 'FTP', 'class': FTPUploadMethod}]
	return builtInContent

class CataloguePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.CataloguePublisher")
		self.ui = pagePublisher.getUI ()
		
	def publish (self, page):
		indexTemplate = self.templateConfig.getTemplate (page.getOption ('catalogue-index-template', 'template.html'))
		itemTemplate = self.templateConfig.getTemplate (page.getOption ('catalogue-item-template', 'template.html'))
		
		maxCols = int (page.getOption ('catalogue-max-columns', '5'))
		buildIndexPage = 0
		buildItemPages = 0
		catalogueBuildPages = page.getOption ('catalogue-build-pages', 'index,item')
		for option in catalogueBuildPages.split (','):
			if (option == "index"):
				if (indexTemplate is not None):
					buildIndexPage = 1
				else:
					msg = "Unable to build the index page for catalogue %s because no catalogue-index-template has been specified." % page.getSource()
					self.log.warn (msg)
					self.ui.warn (msg)
			elif (option == "item"):
				if (itemTemplate is not None):
					buildItemPages = 1
				else:
					msg = "Unable to build the item pages for catalogue %s because no catalogue-item-template has been specified." % page.getSource()
					self.log.warn (msg)
					self.ui.warn (msg)
		
		if (not buildIndexPage | buildItemPages):
			msg = "Neither index or item pages are being built for catalogue %s" % page.getSource()
			self.log.warn (msg)
			self.ui.warn (msg)
			return
			
		itemContentType = page.getOption ('catalogue-item-content-type', None)
		if (itemContentType is None or itemContentType.lower() == 'none'):
			# We wish to turn off item content publishing
			itemContentPublisher = None
		else:
			itemContentPublisher = self.pagePublisher.getContentPublisher (itemContentType)
			if (itemContentPublisher is None):
				msg = "Unable to find a publisher for catalogue item content type %s." % itemContentType
				self.log.error (msg)
				raise SitePublisher.PublisherException (msg)
		# Build the context pieces we are going to need
		pageCharSet = page.getOption ('character-set', None)
		if (pageCharSet is not None):
			# This page has it's own character set
			pageCodec = codecs.lookup (self.pageCharSet)
		else:
			# This page uses the default character set.
			pageCodec = self.characterSetCodec
			
		catalogue = CatalogueContent.CatalogueContent (page.getSource(), pageCodec)
		items = []
		rows = []
		col = []
		lastModDate = timeformat.format ('%a[SHORT], %d %b[SHORT] %Y %H:%M:%S %Z', time.localtime (page.getModificationTime()))
		copyrightYear = timeformat.format ('%Y')
		# Source paths
		relativeSourcePath = page.getRelativePath()
		contentDir = self.contentDir
		absSourcePath = page.getSource()
		localDestinationDir = os.path.dirname (page.getRelativePath())
		depth = page.getDepthString()
		
		self.log.debug ("Building the context for each item in the catalogue.")
		for itemHeaders in catalogue.getItems():
			# Destination paths
			filename = itemHeaders.get ('filename', None)
			if (filename is None):
				msg = "Unable to publish catalogue %s.  Missing filename header in catalogue." % page.getSource()
				self.log.error (msg)
				raise SitePublisher.PublisherException (msg)

			actualHeaders = {}
			actualHeaders.update (page.getHeaders())
			actualHeaders.update (itemHeaders)
			
			# Used to determine the file to write to, kept in case the pageContext doesn't contain them.
			relativeDestPath = os.path.join (localDestinationDir, os.path.splitext (filename)[0] + '.html')
			destPath = os.path.join (self.destDir, relativeDestPath)
			
			if (itemContentPublisher is not None):
				self.log.debug ("Retrieving page context for this catalogue entry.")
				
				# We need a page for this entry so that we can get it's content.
				itemPageList = self.contentConfig.getPages (os.path.join (contentDir, filename), {})
				
				if (len (itemPageList) > 1):
					self.ui.warn ("Catalogue contains content type that returns more than one page!  Only building first page.")
				itemPage = itemPageList [0]
				
				pageContext = itemContentPublisher.getPageContext (itemPage, itemTemplate)
				actualHeaders.update (pageContext.get ('headers', {}))
				pageContext ['headers'] = actualHeaders
				if (not pageContext.has_key ('destinationPath')):
					pageContext ['destinationPath'] = relativeDestPath
				if (not pageContext.has_key ('absoluteDestinationPath')):
					pageContext ['absoluteDestinationPath'] = destPath
			else:
				self.log.debug ("No content type for this catalogue entry - just publish what we have.")
				
				# Get the generic page information for this file
				relativeDestPath = os.path.join (localDestinationDir, os.path.splitext (filename)[0] + '.' + itemTemplate.getTemplateExtension())
				destPath = os.path.join (self.destDir, relativeDestPath)
				destFilename = os.path.basename (destPath)
				actualHeaders = {}
				actualHeaders.update (page.getHeaders())
				actualHeaders.update (itemHeaders)
				
				pageContext = {'lastModifiedDate': lastModDate
							,'copyrightYear': copyrightYear
							,'sourcePath': relativeSourcePath
							,'absoluteSourcePath': absSourcePath
							,'destinationPath': relativeDestPath
							,'absoluteDestinationPath': destPath
							,'destinationFilename': destFilename
							,'depth': depth
							,'headers': actualHeaders
							}
				
			items.append (pageContext)
			if (len (col) == maxCols):
				rows.append (col)
				col = []
			col.append (pageContext)
		if (len (col) > 0):
			rows.append (col)
			col = []
		
		# Build the Catalogue context
		catalogueMap = {'entries': items, 'rows': rows, 'headers': catalogue.getCatalogueHeaders()}
		# Do the individual items now
		if (buildItemPages):
			itemCount = 0
			itemLength = len (items)
			for item in items:
				relativeDestPath = item['destinationPath']
				context = simpleTALES.Context(allowPythonPath=1)
				context.addGlobal ('page', item)
				if (itemCount > 0):
					catalogueMap ['previous'] = items[itemCount - 1]
				elif (catalogueMap.has_key ('previous')):
					del catalogueMap ['previous']
				if (itemCount < itemLength - 1):
					catalogueMap ['next'] = items[itemCount + 1]
				elif (catalogueMap.has_key ('next')):
					del catalogueMap ['next']
					
				context.addGlobal ('catalogue', catalogueMap)
				
				macros = page.getMacros()
				self.pagePublisher.expandTemplate (itemTemplate, context, relativeDestPath, macros)
				itemCount += 1
				
		if (buildIndexPage):
			# Cleanup the catalogueMap from the items pages.
			if (catalogueMap.has_key ('previous')):
				del catalogueMap ['previous']
			if (catalogueMap.has_key ('next')):
				del catalogueMap ['next']
			
			indexMap = self.getPageContext (page, indexTemplate, catalogue)			
			relativeDestPath = indexMap ['destinationPath']
			
			context = simpleTALES.Context(allowPythonPath=1)
			context.addGlobal ('page', indexMap)			
			context.addGlobal ('catalogue', catalogueMap)
			
			macros = page.getMacros()
			self.pagePublisher.expandTemplate (indexTemplate, context, relativeDestPath, macros)
			
	def getPageContext (self, page, template, catalogue=None):
		# The page context for a Catalogue is fairly boring, but someone might use it
		indexMap = SitePublisher.ContentPublisher.getPageContext (self, page, template)
		
		if (catalogue is None):
			localCatalogue = CatalogueContent.CatalogueContent (page.getSource(), self.characterSetCodec)
		else:
			localCatalogue = catalogue
		
		actualHeaders = indexMap ['headers']
		actualHeaders.update (localCatalogue.getCatalogueHeaders())
		indexMap ['headers'] = actualHeaders

		return indexMap
		
		
class HTMLTextPagePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.htmlConverter = ContentToHTMLConverter.ContentToHTMLConverter()
		self.xhtmlConverter = ContentToHTMLConverter.ContentToXHTMLConverter()
		self.log = logging.getLogger ("PubTal.HTMLTextPagePublisher")
		
	def publish (self, page):
		templateName = page.getOption ('template')
		# Get this template's configuration
		template = self.templateConfig.getTemplate (templateName)
		
		context = simpleTALES.Context(allowPythonPath=1)
		
		# Get the page context for this content
		map = self.getPageContext (page, template)
		
		# Determine the destination for this page
		relativeDestPath = map ['destinationPath']
						
		context.addGlobal ('page', map)
		
		macros = page.getMacros()
		self.pagePublisher.expandTemplate (template, context, relativeDestPath, macros)
		
	def getPageContext (self, page, template):
		pageMap = SitePublisher.ContentPublisher.getPageContext (self, page, template)
		
		ignoreNewlines = page.getBooleanOption ('htmltext-ignorenewlines')
		preserveSpaces = page.getBooleanOption ('preserve-html-spaces', 1)
		headers, rawContent = self.readHeadersAndContent(page)
		# Determine desired output type, HTML or XHTML
		outputType = template.getOption ('output-type')
		if (outputType == 'HTML'):
			content = self.htmlConverter.convertContent (rawContent, ignoreNewLines=ignoreNewlines, preserveSpaces=preserveSpaces)
		elif (outputType == 'XHTML'):
			content = self.xhtmlConverter.convertContent (rawContent, ignoreNewLines=ignoreNewlines, preserveSpaces=preserveSpaces)
		elif (outputType == 'PlainText'):
			# It doesn't actually matter how the markup has been entered in the HTMLText, because we
			# are going to output Plain Text anyway.  We use HTML because it's the least demanding.
			content = self.htmlConverter.convertContent (rawContent, ignoreNewLines=ignoreNewlines, plainTextOuput=1)
		else:
			msg = "HTMLText content doesn't support output in type '%s'." % outputType
			self.log.error (msg)
			raise SitePublisher.PublisherException (msg)
		
		actualHeaders = pageMap ['headers']
		actualHeaders.update (headers)
		pageMap ['headers'] = actualHeaders
		pageMap ['content'] = content
		pageMap ['rawContent'] = rawContent
		
		return pageMap

class FTPUploadMethod (SiteUploader.UploadMethod):
	def __init__ (self, siteConfig, uploadConfig):
		self.siteConfig = siteConfig
		self.uploadConfig = uploadConfig
		self.utfencoder = codecs.lookup ("utf8")[0]
		self.utfdecoder = codecs.lookup ("utf8")[1]
		self.db = None
		self.ftpClient = None
		self.log = logging.getLogger ("FTPUploadMethod")
		try:
			conf = 'host'
			self.hostname = uploadConfig [conf]
			conf = 'username'
			self.username = uploadConfig [conf]
		except:
			raise "Missing FTP configuration option %s" % conf
		self.password = uploadConfig.get ('password', None)
		self.initialDir = uploadConfig.get ('base-dir')
		
	def getDB (self):
		if (self.db is None):
			self.db = anydbm.open (os.path.join (self.siteConfig.getDataDir(), 'FtpCache-%s-%s' % (self.hostname, self.username)), 'c')
		return self.db
		
	def uploadFiles (self, fileDict, userInteraction):
		"Return 1 for success, 0 for failure.  Must notify userInteraction directly."
		if (self.ftpClient is None):
			self.log.debug ("First file, there is no ftp client yet.")
			if (self.password is None):
				self.log.debug ("Asking for password - none in config file.")
				self.password = userInteraction.promptPassword ("Password required (%s@%s)" % (self.username, self.hostname))
			self.ftpClient = FtpLibrary.FTPUpload (self.hostname, self.username, self.password, self.initialDir)
			try:
				self.log.info ("Connecting to FTP site.")
				userInteraction.info ("Connecting to FTP site.")
				if (not self.ftpClient.connect (userInteraction)):
					return 0
				self.log.info ("Connected.")
				userInteraction.info ("Connected.")
			except Exception, e:
				msg = "Error connecting to FTP site: %s" % str (e)
				userInteraction.taskError ("Error connecting to FTP site: %s" % str (e))
				return 0
		
		percentageDone = 0.0
		incrementSize = 100.0/float (len (fileDict))
		db = self.getDB()
		for fName in fileDict.keys():
			userInteraction.taskProgress ("Uploading %s" % fName, percentageDone)
			percentageDone += incrementSize
			if (self.ftpClient.uploadFile (self.siteConfig.getDestinationDir(), fName, userInteraction)):
				db [self.utfencoder (fName)[0]] = fileDict [fName]
		return 1
		
	def finished (self):
		if (self.ftpClient is not None):
			self.ftpClient.disconnect()
			self.ftpClient = None
			
		if (self.db is not None):
			self.db.close()
			self.db = None