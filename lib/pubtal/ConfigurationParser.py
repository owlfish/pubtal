""" Configuration Parser - Part of PubTal.

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

import re

try:
	import logging
except:
	import InfoLogging as logging

class ConfigurationParser:
	def __init__ (self):
		self.handlers = {}
		self.directiveRegex = re.compile ('^\s*<([^ /]+)(.*)>$')
		self.endDirective = re.compile ('^\s*</(.*)>$')
		self.commentRegex = re.compile ('(^\s*#.*$)|(^\W*$)')
		self.log = logging.getLogger ("PubTal.ConfigurationParser")
		self.defaultHandler = None
		
	def addTopLevelHandler (self, directive, handler):
		self.handlers [directive.upper()] = handler
		
	def setDefaultHandler (self, handler):
		self.defaultHandler = handler
		
	def parse (self, fileStream):
		directiveStack = []
		currentHandler = None
		for line in fileStream.readlines():
			lineHandled = 0
			match = self.directiveRegex.match (line)
			if (match is not None):
				directiveStack.append (match.group(1).upper())
				if (currentHandler is None):
					# Do we have an handler?
					handler = self.handlers.get (match.group(1).upper(), None)
					if (handler is not None):
						# We have a good handler for this!
						currentHandler = handler
						currentHandler.startDirective (match.group(1).upper(), match.group(2).strip())
					else:
						if (self.defaultHandler is not None):
							self.defaultHandler.startDirective (match.group(1).upper(), match.group(2).strip())
						else:
							self.log.warn ("Handler not found for directive %s" % match.group(1))
				else:
					# We already have a handler, just pass them the nested directive.
					currentHandler.startDirective (match.group(1).upper(), match.group(2).strip())
				lineHandled = 1
			match = self.endDirective.match (line)
			if (not lineHandled and match is not None):
				# Pop off a directive.
				looking = 1
				while (looking and len (directiveStack) > 0):
					lastDir = directiveStack.pop()
					if (lastDir == match.group(1).upper()):
						looking = 0
					else:
						self.log.warn ("Un-closed directive tag: %s (looking for %s)" % (lastDir, match.group(1).upper()))
						if (currentHandler is not None):
							currentHandler.endDirective (lastDir)
						elif (self.defaultHandler is not None):
							self.defaultHandler.endDirective (lastDir)
				
				if (currentHandler is not None):
					currentHandler.endDirective (match.group(1).upper())
					if (len (directiveStack) == 0):
						currentHandler = None
				elif (self.defaultHandler is not None):
					self.defaultHandler.endDirective (match.group(1).upper())
				lineHandled = 1
			if (not lineHandled):
				if (not self.commentRegex.match (line)):
					if (currentHandler is not None):
						currentHandler.option (line.strip())
					elif (self.defaultHandler is not None):
						self.defaultHandler.option (line.strip())
						