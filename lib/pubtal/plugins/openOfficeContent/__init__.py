""" OpenOffice to HTML Plugin for PubTal

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
from simpletal import simpleTAL, simpleTALES

import OpenOfficeToHTMLConverter

def getPluginInfo ():
	builtInContent = [{'functionality': 'content', 'content-type': 'OpenOffice' ,'file-type': 'sxw','class': OpenOfficePagePublisher}]
	return builtInContent
	
class OpenOfficePagePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.OpenOfficePagePublisher")
		self.converter = OpenOfficeToHTMLConverter.OpenOfficeConverter()
		# Get the default character set for the site.
		config = pagePublisher.getConfig()
		self.defaultCharset = config.getDefaultCharacterSet()
		self.encodingCapabilities = config.getEncodingCapabilities()
		
	def publish (self, page):
		template = self.templateConfig.getTemplate (page.getOption ('template', 'template.html'))
		context = simpleTALES.Context(allowPythonPath=1)
		
		# Get the page context for this content
		map = self.getPageContext (page, template)
		context.addGlobal ('page', map)
		macros = page.getMacros()
		
		# Determine the destination for this page
		relativeDestPath = map ['destinationPath']
		self.pagePublisher.expandTemplate (template, context, relativeDestPath, macros)
		
		# Publish any bundled pictures.
		for fileName, data in self.converter.getPictures():
			destFile = self.pagePublisher.openOuputFile (fileName)
			destFile.write (data)
			destFile.close()
		
	def getPageContext (self, page, template):
		pageMap = SitePublisher.ContentPublisher.getPageContext (self, page, template)
		
		# Determine the character set that will be used on output
		templateCharset = template.getOption ('character-set', self.defaultCharset)
		
		# Now determine what capabilities this character set offers
		smartQuotes = not self.encodingCapabilities.getCapability (templateCharset, 'SmartQuotes')
		hyphens = not self.encodingCapabilities.getCapability (templateCharset, 'Hyphen')
		
		# Parse the page
		options = {'CleanSmartQuotes': smartQuotes, 'CleanHyphens': hyphens}
		options ['DestinationFile'] = pageMap ['destinationPath']
		options ['output-type'] = template.getOption ('output-type', 'HTML')
		options ['preserveSpaces'] = page.getBooleanOption ('preserve-html-spaces', 1)
		self.converter.convert (page.getSource(), options)
		
		headers = self.converter.getMetaInfo()
		content = self.converter.getContent()
		footNotes = self.converter.getFootNotes()
		
		actualHeaders = pageMap ['headers']
		actualHeaders.update (headers)
		pageMap ['headers'] = actualHeaders
		pageMap ['content'] = content
		pageMap ['footnotes'] = footNotes
		
		return pageMap
		