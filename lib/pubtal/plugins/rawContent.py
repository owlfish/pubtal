""" Raw content plugin for PubTal

	Copyright (c) 2003 Florian Schulze (http://proff.crowproductions.com/)
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

import os, os.path

try:
	import logging
except:
	from pubtal import InfoLogging as logging

from pubtal import SitePublisher
from simpletal import simpleTAL, simpleTALES

def getPluginInfo ():
	builtInContent = [{'functionality': 'content', 'content-type': 'Raw', 'class': RawPagePublisher}]
	return builtInContent

class RawPagePublisher(SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.RawPagePublisher")

	def publish (self, page):
		template = self.templateConfig.getTemplate (page.getOption ('template', 'template.html'))
		context = simpleTALES.Context(allowPythonPath=1)

		# Get the page context for this content
		map = self.getPageContext (page, template)
		context.addGlobal ('page', map)

		# Determine the destination for this page
		relativeDestPath = map ['destinationPath']

		macros = page.getMacros()
		self.pagePublisher.expandTemplate (template, context, relativeDestPath, macros)

	def getPageContext (self, page, template):
		pageMap = SitePublisher.ContentPublisher.getPageContext (self, page, template)
		headers, rawContent = self.readHeadersAndContent(page)

		actualHeaders = pageMap ['headers']
		actualHeaders.update (headers)
		pageMap ['headers'] = actualHeaders
		pageMap ['content'] = rawContent
		pageMap ['rawContent'] = rawContent

		return pageMap
