""" Classes to determine and cache character set capabilities.

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

try:
	import logging
except:
	import InfoLogging as logging
	
import codecs

# List of tests and capability names.
tests = [(u'\u201c\u201d', 'SmartQuotes'), (u'\u2013', 'Hyphen')]
	
class EncodingCapabilities:
	def __init__ (self):
		""" Class for deteriming character set encoding capabilities."""
		self.log = logging.getLogger ("PubTal.SiteConfig")
		self.cache = {}
		
	def getCapability (self, characterSet, capability):
		if (not self.cache.has_key (characterSet)):
			self.log.debug ("Cache miss for character set %s" % characterSet)
			self._getCapabilities_ (characterSet)
		else:
			self.log.debug ("Cache hit for character set %s" % characterSet)
		return self.cache [characterSet][capability]
	
	def _getCapabilities_ (self, characterSet):
		try:
			encoder = codecs.lookup (characterSet)[0]
		except Exception, e:
			self.log.error ("Character set %s not supported." % characterSet)
			raise e
		
		capabilities = {}
		
		self.log.debug ("Testing capabilities for character set %s" % characterSet)
		for testcase, testname in tests:
			try:
				self.log.info ("About to execute testcase: %s" % repr (testcase))
				encoder (testcase, "strict")
				capability = 1
				self.log.debug ("%s supported." % testname)
			except:
				capability = 0
				self.log.debug ("%s not supported." % testname)
				
			capabilities [testname] = capability
		
		self.cache [characterSet] = capabilities
		

	