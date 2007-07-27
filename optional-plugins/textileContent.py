""" Textile plugin for PubTal

	Requires PyTextile (http://dealmeida.net/en/Projects/PyTextile/)

	Copyright (c) 2003 Colin Stewart (http://www.owlfish.com/)
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

textileSupported = 1

import os, os.path, codecs

import logging
from pubtal import SitePublisher
from simpletal import simpleTAL, simpleTALES

try:
	import textile
except:
	textileSupported = 0
	
utf16Decoder = codecs.lookup ("utf16")[1]
	
def getPluginInfo ():
	if (not textileSupported):
		# No textile support - so we add no content support
		logging.warn ("Textile plugin present, but no textile support found.")
		return []
	builtInContent = [{'functionality': 'content', 'content-type': 'Textile' ,'file-type': 'text','class': TextilePagePublisher}]
	return builtInContent
	
class TextilePagePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.TextilePagePublisher")
		
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
		
	def getPageContext (self, page, template):
		pageMap = SitePublisher.ContentPublisher.getPageContext (self, page, template)
		
		# We need to preserve the original character set because Textile does it's own conversion.
		headers, rawContent = self.readHeadersAndContent(page, preserveCharacterSet = 1)
		pageCharSet = page.getOption ('character-set', None)
		if (pageCharSet is None):
			pageCharSet = self.characterSet
		pageCharSetDecoder = codecs.lookup (pageCharSet)[1]
				
		# Pass in the encoding of the file, and get output in utf-16
		content = textile.textile (rawContent, encoding=pageCharSet, output="utf16")
		# Now convert the body from utf16 back to Unicode
		content = utf16Decoder (content)[0]
		# Now convert al l the headers (would normally have been done in readHeadersAndContent)
		convHeaders = {}
		for headerName, headerValue in headers.items():
			convHeaders [pageCharSetDecoder(headerName)[0]] = pageCharSetDecoder (headerValue)[0]
		
		actualHeaders = pageMap ['headers']
		actualHeaders.update (convHeaders)
		pageMap ['headers'] = actualHeaders
		pageMap ['content'] = content
		# Raw content wasn't converted
		pageMap ['rawContent'] = pageCharSetDecoder (rawContent)[0]
		
		return pageMap
		