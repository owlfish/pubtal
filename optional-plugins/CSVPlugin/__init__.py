""" Classes to generate tables from CSV files in PubTal.

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
	from pubtal import InfoLogging as logging
	
from pubtal import SitePublisher
import os, time, codecs

import CSVSortedTableConfigParser, CSVContext

from simpletal import simpleTAL, simpleTALES
						
def getPluginInfo ():
	builtInContent = [{'functionality': 'content', 'content-type': 'CSVSortedTables' ,'file-type': 'csvst','class': CSVPagePublisher}]
	return builtInContent
	
class CSVPagePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("CSVPagePublisher")
		siteConfig = pagePublisher.getConfig()
		contentConfig = siteConfig.getContentConfig()
		self.log.info ("Registering page builder with content config.")
		contentConfig.registerPageBuilder ('CSVSortedTables', self.pageBuilder)
		
		# Our config file parser.
		self.parser = CSVSortedTableConfigParser.csvSortedTableConfig (pagePublisher.getUI())
		
		# Context factory cache.
		self.cache = {}
		
	def publish (self, page):
		self.log.info ("Being asked to publish %s" % page.getRelativePath())
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
		pageCharSet = page.getOption ('character-set', None)
		if (pageCharSet is not None):
			# This page has it's own character set
			pageCodec = codecs.lookup (pageCharSet)[1]
		else:
			# This page uses the default character set.
			pageCodec = self.characterSetCodec
			
		theSource = page.getSource()
		if (self.cache.has_key (theSource)):
			contextFactory = self.cache [theSource]
		else:
			contextFactory = CSVContext.CsvContextCreator (theSource, pageCodec)
			self.cache [theSource] = contextFactory
		
		try:
			pageMap ['content'] = contextFactory.getContextMap (page.getOption ('column-sorter'))
		except Exception, e:
			self.log.error ("Exception getting CSV context map: " + str (e))
			raise e
		#pageMap ['rawContent'] = contextFactory.getRawData()
		
		relativeDestPath = page.getOption ('destinationNamePath')
		if (relativeDestPath is not None):
			destPath = os.path.join (self.destDir, relativeDestPath)
			destFilename = os.path.basename (destPath)
			pageMap ['destinationPath'] = relativeDestPath
			pageMap ['absoluteDestinationPath'] = destPath
			pageMap ['destinationFilename'] = destFilename
		
		return pageMap
		
	def pageBuilder (self, page, options):
		self.log.info ("Building pages for input page %s" % str (page.getRelativePath))
		return self.parser.parseConfig (page)
		