""" Classes to handle configuration of a PubTal site.

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
	
import pubtal
import ConfigurationParser, BuiltInPlugins, EncodingCapabilities, MessageBus
import os, os.path, stat, re, sys, anydbm, copy, fnmatch
	
class SiteConfig:
	def __init__ (self, configFile):
		self.log = logging.getLogger ("PubTal.SiteConfig")
		# Get the real path to the config file
		configFile = os.path.normpath (configFile)
		if (hasattr (os.path, "realpath")):
			# Under Unix and 2.2 we can remove symlinks.
			configFile = os.path.realpath (configFile)
		self.log.info ("Normalised configuration file path: " + configFile)
		
		self.contentConfig = ContentConfig (self)
		self.templateConfig = TemplateConfig (self)
		self.messageBus = MessageBus.MessageBus()
		self.encodingCapabilities = EncodingCapabilities.EncodingCapabilities()
		# List of upload config objects.
		self.uploadList = []
		# List of regular expressions that match files to be ignored
		self.ignoreFilters = []
		# Supported content types
		self.supportedContent = {}
		# Supported upload types
		self.supportedUploadMethods = {}
		# Directories where plugins may reside
		self.extraPluginDirs = []
		self.plugins = []
		self.baseDir = os.path.abspath (os.path.split (configFile)[0])
		self.localCacheDB = None
		
		# Defaults
		self.setDefaultCharacterSet ('ISO-8859-15')
		self.contentDir = os.path.join (self.baseDir, 'content')
		self.destDir = os.path.join (self.baseDir, 'dest')
		self.templateDir = os.path.join (self.baseDir, 'template')
		self.pubtalDataDir = os.path.join (self.baseDir, 'PubTalData')
		
		self.readConfig(configFile)
		
		# Load plugins
		self.log.info ("Loading plugins...")
		systemPlugins = self.getPluginModules(os.path.join (pubtal.__path__[0],'plugins'))
		self.plugins.extend (systemPlugins)
		self.log.debug ("Loading extra plugins.")
		for extraDir in self.extraPluginDirs:
			self.log.debug ("Looking for plugins in %s" % extraDir)
			morePlugins = self.getPluginModules (extraDir)
			self.plugins.extend (morePlugins)
		
		# Add in the built in supported content
		self.plugins.append (BuiltInPlugins)
		for plugin in self.plugins:
			for pluginInfo in plugin.getPluginInfo():
				pluginType = pluginInfo.get ('functionality', None)
				if (pluginType == None):
					sef.log.warn ("Plugin did not include 'functionality' key - skipping.")
				elif (pluginType == "content"):
					contentType = pluginInfo ['content-type']
					klass = pluginInfo ['class']
					self.supportedContent [contentType] = klass
					if (pluginInfo.has_key ('file-type')):
						fileTypeInfo = pluginInfo ['file-type']
						if (type (fileTypeInfo) == type ([])):
							fileTypeInfos = fileTypeInfo
						else:
							fileTypeInfos = [fileTypeInfo]
						for fileTypeInfo in fileTypeInfos:
							contentTypeConfig = PageConfigItem()
							contentTypeConfig.setOption ('content-type', contentType)
							self.log.debug ("Adding plugin file-type config for %s" % fileTypeInfo)
							self.contentConfig.addFileType (fileTypeInfo, contentTypeConfig)
				elif (pluginType == "upload-method"):
					methodType = pluginInfo ['method-type']
					klass = pluginInfo ['class']
					self.supportedUploadMethods [methodType] = klass
					self.log.info ("Upload method %s supported." % methodType)
				else:
					self.log.warn ("Plugin offer functionality %s which is not understood." % pluginType)
		
		self.messageBus.notifyEvent ("PubTal.InitComplete")
	
	def getMessageBus (self):
		return self.messageBus
		
	def finished (self):
		""" Called to let us know that no further publishing is going to happen. """
		self.messageBus.notifyEvent ("PubTal.Shutdown")
		
	def getContentDir (self):
		return self.contentDir
		
	def getDestinationDir (self):
		return self.destDir
		
	def getTemplateDir (self):
		return self.templateDir
		
	def getDataDir (self):
		return self.pubtalDataDir
		
	def getIgnoreFilters (self):
		return self.ignoreFilters
		
	def getDefaultCharacterSet (self):
		return self.characterSet
		
	def setDefaultCharacterSet (self, charSet):
		self.characterSet = charSet
		
	def getSupportedContent (self):
		return self.supportedContent
		
	def getSupportedUploadMethods (self):
		return self.supportedUploadMethods
		
	def getUploadConfigs (self):
		return self.uploadList
		
	def getEncodingCapabilities (self):
		return self.encodingCapabilities
		
	def getContentConfig (self):
		return self.contentConfig
	
	def getTemplateConfig (self):
		return self.templateConfig
		
	def getLocalCacheDB (self):
		if (self.localCacheDB is None):
			# Create the directory if needed and open the DB.
			dataDir = self.getDataDir()
			if (not os.path.exists (dataDir)):
				self.log.info ("Creating PubTal Data directory %s" % dataDir)
				os.makedirs (dataDir)
			self.localCacheDB = anydbm.open (os.path.join (dataDir, 'localCache'), 'c')
			self.messageBus.registerListener ("PubTal.Shutdown", self._shutdown_)
		return self.localCacheDB
		
	def readConfig (self, configFile):
		parser = ConfigurationParser.ConfigurationParser()
		parser.addTopLevelHandler ('SiteConfig', self)
		parser.addTopLevelHandler ('Content', self.contentConfig)
		parser.addTopLevelHandler ('Template', self.templateConfig)
		
		self.currentDirective = []
		confFile = open (configFile, 'r')
		parser.parse(confFile)
		confFile.close()
		
		self.contentConfig.configFinished()
		self.templateConfig.configFinished()
		
	def startDirective (self, directive, options):
		self.currentDirective.append (directive)
		if (directive == 'UPLOAD'):
			self.uploadList.append ({})
		
	def endDirective (self, directive):
		self.currentDirective.pop()
		
	def option (self, line):
		if (len (self.currentDirective) == 0):
			self.log.warn ("Received option with no directive in place.")
			return
		directive = self.currentDirective [-1]
		if (directive == 'SITECONFIG'):
			if (line.lower().startswith ('content-dir')):
				self.contentDir = os.path.join (self.baseDir, line [line.find (' ')+1:])
			elif (line.lower().startswith ('template-dir')):
				self.templateDir = os.path.join (self.baseDir, line [line.find (' ')+1:])
			elif (line.lower().startswith ('dest-dir')):
				self.destDir = os.path.join (self.baseDir, line [line.find (' ')+1:])
			elif (line.lower().startswith ('ignore-filter')):
				filter = line [line.find (' ')+1:]
				self.log.info ("Adding filter of content to ignore: %s" % filter)
				self.ignoreFilters.append (re.compile (filter))
			elif (line.lower().startswith ('character-set')):
				self.setDefaultCharacterSet (line[line.find (' ') + 1:])
			elif (line.lower().startswith ('additional-plugins-dir')):
				self.extraPluginDirs.append (os.path.join (self.baseDir, line [line.find (' ')+1:]))
			elif (line.lower().startswith ('pubtal-data-dir')):
				self.pubtalDataDir = os.path.join (self.baseDir, line [line.find (' ')+1:])
			else:
				self.log.warn ("SiteConfig Option %s not supported" % line)
		elif (directive == 'UPLOAD'):
			uploadConf = self.uploadList[-1]
			nvBreak = line.find (' ')
			uploadConf [line [0:nvBreak]] = line [nvBreak + 1:]
	
	def getPluginModules (self, path):
		try:
			dirList = os.listdir (path)
		except:
			return []
			
		self.log.debug ("Adding %s to the Python path." % path)
		sys.path.insert(0, path)
		foundPlugins = []
		for fileName in dirList:
			try:
				if (os.path.isfile (os.path.join (path,fileName))):
					if (fileName == "__init__.py"):
						self.log.debug ("Skipping init file for plugins dir.")
					elif (fileName.endswith ('.py')):
						pluginModuleName = fileName[:-3]
						plugin = __import__ (pluginModuleName, globals(), locals(), pluginModuleName)
						foundPlugins.append (plugin)
						self.log.info ("Loaded PubTal plugin %s" % pluginModuleName)
					else:
						self.log.debug ("Skipping file %s while looking for plugins." % fileName)
				elif (os.path.isdir (os.path.join (path, fileName))):
					pluginModuleName = fileName
					try:
						plugin = __import__ (pluginModuleName, globals(), locals(), pluginModuleName)
						foundPlugins.append (plugin)
						self.log.info ("Loaded PubTal plugin %s" % pluginModuleName)
					except:
						self.log.warn ("Error trying to load dir %s as a module." % pluginModuleName)
				else:
					self.log.warn ("Found neither file nor dir in plugin directory.")
			except ImportError, e:
				self.log.warn ("Error loading PubTal plugin %s." % fileName)
				self.log.debug ("Exception was: %s" % str (e))
				
		return foundPlugins
		
	def _shutdown_ (self, event, data):
		# Only called when PubTal is shutting down.
		self.localCacheDB.close()

class ContentConfig:
	def __init__ (self, siteConfig):
		self.log = logging.getLogger ("PubTal.ContentConfig")
		self.patternMap = {}
		self.directoryMap = {}
		self.fileMap = {}
		
		self.pageBuilders = {}
		self.currentConfigItem = None
		self.siteConfig = siteConfig
		
	def getPage (self, contentPath):
		""" This returns a single page with all configuration information
			populated.  It does *NOT* call page builders or respect classes.
		"""
		page = Page (contentPath, self.siteConfig.contentDir)
		
		# Now work through directory and pattern  maps
		dirConfigItems = []
		head, tail = os.path.split (contentPath)
		contentFilename = tail
		while (tail != ''):
			self.log.debug ("Looking for directory and pattern configuration at: %s" % head)
				
			# Do directories first - they have higher priorities than pattern matches
			configItem = self.directoryMap.get (head, None)
			if (configItem is not None):
				dirConfigItems.insert (0,configItem)
			
			# Do the pattern matching second.
			patternList = self.patternMap.get (head, [])
			for pattern, configItem in patternList:
				if (fnmatch.fnmatch (contentFilename, pattern)):
					# We have a match
					dirConfigItems.insert (0, configItem)
			
			if (self.siteConfig.contentDir.startswith (head)):
				# We have reached the top of the content dir, so stop now
				tail = ''
			else:
				head, tail = os.path.split (head)
			
		for confItem in dirConfigItems:
			self.log.debug ("Updating config using %s" % str (confItem))
			confItem.updatePage (page)
		
		# Now look for this specific file
		configItem = self.fileMap.get (contentPath)
		self.log.debug ("Looking for file config item for %s", contentPath)
		if (configItem is not None):
			self.log.debug ("Found file config item of %s", str (configItem))
			configItem.updatePage (page)
		return page
		
	def getPages (self, contentPath, options):
		""" Returns a list of pages (i.e. elements to be built) for a given 
			content path.
			
			This method determines the content type that applies for this page,
			then filters the page based on content.  Finally content-specific 
			methods are called (if applicable) which can in turn create their
			own page objects.
		"""
		# See what, if any, classes we should check for.
		classList = options.get ('classes', 'normal').split (',')
		allowAllClasses = options.get ('buildAllClasses', 0)
		
		page = self.getPage (contentPath)
			
		# Now filter based on class.
		pageClasses = page.getOption ('class', 'normal').split (',')
		self.log.debug ("Checking that page class %s is in the list of classes to build." % str (pageClasses))
		allow = 0
		if (allowAllClasses):
			allow = 1
		else:
			for pageClass in pageClasses:
				if (pageClass in classList):
					allow = 1
				
		if (not allow):
			return []
		
		# Now see whether this content type has it's own page builder.
		pageContentType = page.getOption ('content-type')
		if (self.pageBuilders.has_key (pageContentType)):
			self.log.debug ("Page content type %s has builder - calling." % pageContentType)
			return self.pageBuilders [pageContentType] (page, options)
		else:
			return [page]
		
	def addFileType (self, fileExtension, extensionConfig):
		""" Adds default configuration options for a file type.
		"""
		newPattern = "*.%s" % fileExtension
		self.addPattern (self.siteConfig.contentDir, newPattern, extensionConfig)
			
	def addPattern (self, targetDirectory, newPattern, newConfig):
		count = 0
		foundExisting = 0
		existingExtensions = self.patternMap.get (targetDirectory, [])
		for existingPattern, existingConfig in existingExtensions:
			if (existingPattern == newPattern):
				self.log.debug ("Configuration for existing pattern %s already exists, merging." % existingPattern)
				# We already have a config.
				# The existing configuration should take precedence - so merge it into the new config
				newConfig.updateConfigItem (existingConfig)
				# Update the existing entry
				existingExtensions [count] = (existingPattern, newConfig)
				foundExisting = 1
			count = count + 1
		if (not foundExisting):
			existingExtensions.append ((newPattern, newConfig))
		self.patternMap [targetDirectory] = existingExtensions
		
	def registerPageBuilder (self, contentType, builderMethod):
		self.pageBuilders [contentType] = builderMethod
		
	def startDirective (self, directive, options):
		self.currentDirective = directive
		if (directive == 'CONTENT'):
			self.currentConfigItem = PageConfigItem()
			targetPath = os.path.join (self.siteConfig.contentDir, options)
			targetDirectory, targetFilename = os.path.split (targetPath)
			if (os.path.isfile (targetPath)):
				# This is an individual file
				self.log.debug ("Found file configuration item: %s", targetPath)
				self.fileMap [targetPath] = self.currentConfigItem
			elif (os.path.isdir (targetPath)):
				# This is a directory directive
				self.log.debug ("Found directory configuration item: %s", targetPath)
				if (targetPath.endswith (os.sep)):
					targetPath = targetPath [:-1]
				self.directoryMap [targetPath] = self.currentConfigItem
			else:
				# Pattern for matching file content.
				self.log.debug ("Found pattern configuration item.")
				self.addPattern (targetDirectory, targetFilename, self.currentConfigItem)
		else:
			self.currentConfigItem = None
			
	def option (self, line):
		if (self.currentConfigItem is not None):
			if (line.lower().startswith ('macro')):
				mnStart = line.find (' ')
				mnEnd = line.find (' ', mnStart+1)
				macroName = line [mnStart+1:mnEnd]
				macro = line [mnEnd + 1:]
				self.currentConfigItem.addMacro (macroName, os.path.join (self.siteConfig.templateDir, macro))
			elif (line.lower().startswith ('header')):
				mnStart = line.find (' ')
				mnEnd = line.find (' ', mnStart+1)
				headerName = line [mnStart+1:mnEnd]
				header = line [mnEnd + 1:]
				self.currentConfigItem.addHeader (headerName, header)
			else:
				firstSpace = line.find (' ')
				name = line [:firstSpace]
				value = line [firstSpace+1:]
				self.currentConfigItem.setOption (name, value)
				
	def endDirective (self, directive):
		self.currentDirective = None
		self.currentConfigItem = None
		
	def configFinished (self):
		# Some debug messages if enabled.
		if (self.log.isEnabledFor (logging.DEBUG)):
			for directory in self.patternMap.keys():
				configDump = []
				for pattern, configValue in self.patternMap [directory]:
					configDump.append ("Pattern %s: Config values: %s" % (pattern, str (configValue)))
					
				self.log.debug ("PatternMap %s has Configuration: %s" % (directory, "".join (configDump)))
			for dir in self.directoryMap.keys():
				self.log.debug ("Directory %s has Configuration: %s" % (dir, str (self.directoryMap [dir])))
			for file in self.fileMap.keys():
				self.log.debug ("File %s has Configuration: %s" % (file, str (self.fileMap [file])))

class TemplateConfig:
	def __init__ (self, siteConfig):
		self.log = logging.getLogger ("PubTal.TemplateConfig")
		self.patternMap = {}
		self.fileMap = {}
		self.directoryMap = {}
		self.currentConfigItem = None
		self.siteConfig = siteConfig
		
	def getTemplate (self, templateName):
		""" Get a Template object which hold the configuration information for this template.
		
			Note that the templateName is relative to the templateDirectory - not absolute!
		"""
		
		template = Template (templateName, self.siteConfig.templateDir)
		templatePath = template.getTemplatePath()
		
		# Now work through directory map
		dirConfigItems = []
		head, tail = os.path.split (templatePath)
		templateFilename = tail
		while (tail != ''):
			self.log.debug ("Looking for directory configuration at: %s" % head)
			configItem = self.directoryMap.get (head, None)
			if (configItem is not None):
				dirConfigItems.insert (0,configItem)
				
			# Do the pattern matching second.
			patternList = self.patternMap.get (head, [])
			for pattern, configItem in patternList:
				if (fnmatch.fnmatch (templateFilename, pattern)):
					# We have a match
					dirConfigItems.insert (0, configItem)
				
			if (self.siteConfig.templateDir.startswith (head)):
				# We have reached the top of the content dir, so stop now
				tail = ''
			else:
				head, tail = os.path.split (head)
			
		for confItem in dirConfigItems:
			template.options.update (confItem)
		
		# Now look for this specific file
		configItem = self.fileMap.get (templatePath)
		if (configItem is not None):
			template.options.update (configItem)
			
		return template
		
	def addFileType (self, fileExtension, extensionConfig):
		newPattern = "*.%s" % fileExtension
		self.addPattern (self.siteConfig.templateDir, newPattern, extensionConfig)
		
	def addPattern (self, targetDirectory, newPattern, newConfig):
		count = 0
		foundExisting = 0
		existingExtensions = self.patternMap.get (targetDirectory, [])
		for existingPattern, existingConfig in existingExtensions:
			if (existingPattern == newPattern):
				self.log.debug ("Configuration for existing pattern %s already exists, merging." % existingPattern)
				# We already have a config.
				# The existing configuration should take precedence - so merge it into the new config
				newConfig.updateConfigItem (existingConfig)
				# Update the existing entry
				existingExtensions [count] = (existingPattern, newConfig)
				foundExisting = 1
			count = count + 1
		if (not foundExisting):
			existingExtensions.append ((newPattern, newConfig))
		self.patternMap [targetDirectory] = existingExtensions
		
	def startDirective (self, directive, options):
		self.currentDirective = directive
		if (directive == 'TEMPLATE'):
			self.currentConfigItem = {}
			targetPath = os.path.join (self.siteConfig.templateDir, options)
			targetDirectory, targetFilename = os.path.split (targetPath)
			if (os.path.isfile (targetPath)):
				# This is an individual file
				self.log.debug ("Found file configuration item.")
				self.fileMap [targetPath] = self.currentConfigItem
			elif (os.path.isdir (targetPath)):
				# This is a directory directive
				self.log.debug ("Found directory configuration item: %s" % targetPath)
				if (targetPath.endswith (os.sep)):
					targetPath = targetPath [:-1]
				self.directoryMap [targetPath] = self.currentConfigItem
			else:
				# Pattern for matching file content.
				self.log.debug ("Found pattern configuration item.")
				self.addPattern (targetDirectory, targetFilename, self.currentConfigItem)
		else:
			self.currentConfigItem = None
			
	def option (self, line):
		if (self.currentConfigItem is not None):
			firstSpace = line.find (' ')
			name = line [:firstSpace]
			value = line [firstSpace+1:]
			self.currentConfigItem [name] = value
				
	def endDirective (self, directive):
		self.currentDirective = None
		self.currentConfigItem = None
		
	def configFinished (self):
		# Some debug messages if enabled.
		if (self.log.isEnabledFor (logging.DEBUG)):
			for dir in self.patternMap.keys():
				self.log.debug ("PatternMap directory %s has Configuration: %s" % (dir, str (self.patternMap [dir])))
			for dir in self.directoryMap.keys():
				self.log.debug ("Directory %s has Configuration: %s" % (dir, str (self.directoryMap [dir])))
			for file in self.fileMap.keys():
				self.log.debug ("File %s has Configuration: %s" % (file, str (self.fileMap [file])))


class PageConfigItem:
	def __init__ (self):
		self.macros = {}
		self.headers = {}
		self.options = {}
		
	def updatePage (self, page):
		page.macros.update (self.macros)
		page.headers.update (self.headers)
		page.options.update (self.options)
		
	def updateConfigItem (self, anotherItem):
		""" This method merges in the configuration options held by another
			item.
		"""
		self.macros.update (anotherItem.macros)
		self.headers.update (anotherItem.headers)
		self.options.update (anotherItem.options)
			
	def addMacro (self, name, template):
		self.macros [name] = template
		
	def addHeader (self, name, header):
		self.headers [name] = header
		
	def setOption (self, name, value):
		if (not self.options.has_key (name)):
			self.options [name] = value
		else:
			curVal = self.options [name]
			if (type (curVal) == type ([])):
				curVal.append (value)
			else:
				curVal = [curVal, value]
				self.options [name] = curVal
		
	def __str__ (self):
		desc = ""
		if (len (self.macros) > 0):
			desc += "Macros: %s\n" % str (self.macros)
		if (len (self.headers) > 0):
			desc += "Headers: %s\n" % str (self.headers)
		if (len (self.options) > 0):
			desc += "Options: %s\n" % str (self.options)
		return desc

class Page:
	def __init__ (self, source, contentDir):
		# Things we need
		self.source = source
		self.macros = {}
		self.options = {'template': 'template.html'}
		self.headers = {}
		self.contentDir = contentDir
		
		commonRoot = os.path.commonprefix ([contentDir, source])
		self.relativePath = source[len (commonRoot)+1:]
		# relativePath is of the form: [dir/]file
		depth = 0
		head, tail = os.path.split (self.relativePath)
		while (tail != ''):
			depth += 1
			head, tail = os.path.split (head)
		# We go to far, so knock one off!
		self.depth = depth - 1
		self.name = self.relativePath
		
	def getDuplicatePage (self, newSource):
		newPage = Page (newSource, self.contentDir)
		newPage.macros = copy.deepcopy (self.macros)
		newPage.options = copy.deepcopy (self.options)
		newPage.headers = copy.deepcopy (self.headers)
		return newPage
		
	def setName (self, name):
		self.name = name
		
	def setOption (self, name, value):
		self.options [name] = value
		
	def hasOption (self, name):
		return self.options.has_key (name)
		
	def getOption (self, name, defaultValue=None):
		return self.options.get (name, defaultValue)
		
	def getBooleanOption (self, name, defaultValue='0'):
		value = self.getOption (name, str (defaultValue))
		lowerValue = value.lower()
		if (lowerValue == 'y' or lowerValue == 'true'):
			return 1
		if (lowerValue == 'n' or lowerValue == 'false'):
			return 0
			
		try:
			val = int (lowerValue)
			return val
		except:
			return 0
			
	def getListOption (self, name):
		if (self.options.has_key (name)):
			option = self.options [name]
			if (type (option) == type ([])):
				return option
			return [option]
		return None

	def getSource (self):
		return self.source
		
	def getRelativePath (self):
		return self.relativePath
		
	def getMacros (self):
		return self.macros
		
	def getHeaders (self):
		return self.headers
		
	def getDepthString (self):
		return "../"*self.depth
		
	def getModificationTime (self):
		""" Returns a tuple of the creation and modification date/time. """
		info = os.stat (self.source)
		return info[stat.ST_MTIME]
		
	def __str__ (self):
		return self.name
		
class Template:
	def __init__ (self, templateName, templateDir):
		self.templateName = templateName
		self.templatePath = os.path.join (templateDir, templateName)
		self.options = {'output-type': 'HTML'}
		
	def getTemplateName (self):
		return self.templateName
		
	def getTemplatePath (self):
		return self.templatePath
		
	def getTemplateExtension (self):
		return os.path.splitext (self.templateName)[1][1:]
		
	def getOption (self, name, defaultValue=None):
		return self.options.get (name, defaultValue)
		
	def getBooleanOption (self, name, defaultValue='0'):
		value = self.getOption (name, str (defaultValue))
		lowerValue = value.lower()
		if (lowerValue == 'y' or lowerValue == 'true'):
			return 1
		if (lowerValue == 'n' or lowerValue == 'false'):
			return 0
			
		try:
			val = int (lowerValue)
			return val
		except:
			return 0
			
	def __str__ (self):
		return self.templateName
