""" Classes to handle HTMLText and Catalogues in PubTal.

	Copyright (c) 2015 Colin Stewart (http://www.owlfish.com/)
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
	
import SitePublisher

try:
	import markdown2
except:
	pass

import os, time, anydbm, codecs
import timeformat
from simpletal import simpleTAL, simpleTALES
						
# getPluginInfo provides the list of built-in supported content.
def getPluginInfo ():
	builtInContent = [{'functionality': 'content', 'content-type': 'Markdown' ,'file-type': 'md','class': MarkdownPagePublisher}]
	return builtInContent


class MarkdownPagePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.MarkdownPagePublisher")
		
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
		
		headers, rawContent = self.readHeadersAndContent(page)

		# Convert the body from markdown to HTML
		content = markdown2.markdown (rawContent)
		
		actualHeaders = pageMap ['headers']
		actualHeaders.update (headers)
		pageMap ['headers'] = actualHeaders
		pageMap ['content'] = content
		pageMap ['rawContent'] = rawContent
		
		return pageMap
