""" Unit tests cases.

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
	from simpletal import DummyLogger as logging
	
from pubtal import HTMLWriter

import unittest, copy, os.path

if __name__ == '__main__':
	logging.basicConfig()

root = logging.getLogger()
root.setLevel (logging.CRITICAL)

CONTENT = """Welcome to the content.

<ul>
	<li>A - Always.  But not forever.</li>
</ul>

<b class="There.  But not here.">Something is fishy</b>

<blockquote>And again.

Second part?</blockquote>

Ordinary fellas here.  And there.
"""
		
class HTMLWriterLibraryTests (unittest.TestCase):
	def setUp (self):
		pass
		
	def tearDown (self):
		pass
		
	def testBasicWrite (self):
		writer = HTMLWriter.HTMLWriter()
		writer.startElement ("p")
		writer.startElement ("b")
		writer.write ("Here's.  A sentence of words.")
		writer.endElement ("b")
		writer.endElement ("p")
		
		result = writer.getOutput().getvalue()
		expectedResult = """<p><b>Here's.&nbsp; A sentence of words.</b></p>\n"""
		
		self.failUnless (result == expectedResult, "Write combination expected:\n[%s] but received:\n[%s]" % (expectedResult, result))
		
	def testWriteCombination (self):
		writer = HTMLWriter.HTMLWriter()
		writer.startElement ("p")
		writer.startElement ("b")
		writer.write ("Here's. ")
		writer.write (" Some sentence.  Type device.")
		writer.endElement ("b")
		writer.write ("A single sentence.")
		writer.endElement ("p")
		
		result = writer.getOutput().getvalue()
		expectedResult = """<p><b>Here's.&nbsp; Some sentence.&nbsp; Type device.</b>A single sentence.</p>\n"""
		
		self.failUnless (result == expectedResult, "Write combination expected:\n[%s] but received:\n[%s]" % (expectedResult, result))
	
	def testNoSpaces (self):
		writer = HTMLWriter.HTMLWriter(preserveSpaces=0)
		writer.startElement ("p")
		writer.startElement ("b")
		writer.write ("Here's. ")
		writer.write (" Some sentence.  Type device.")
		writer.endElement ("b")
		writer.write ("A single sentence.")
		writer.endElement ("p")
		
		result = writer.getOutput().getvalue()
		expectedResult = """<p><b>Here's.  Some sentence.  Type device.</b>A single sentence.</p>\n"""
		
		self.failUnless (result == expectedResult, "No spaces test expected:\n[%s] but received:\n[%s]" % (expectedResult, result))
		
if __name__ == '__main__':
	unittest.main()
	
