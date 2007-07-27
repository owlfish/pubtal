""" Unit tests cases.

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
	from simpletal import DummyLogger as logging
	
from pubtal import SiteUtils
import updateSite

import unittest, copy, os.path

root = logging.getLogger()
root.setLevel (logging.WARN)

# Default test
TEMPLATE1 = '<html><body><h1 tal:content="page/headers/title"></h1> <div tal:content="structure page/content"></div></body></html>'
CONTENT1 = """title: Test1

This is the <b>first</b> test."""
CONFIG1 = ""
RESULT1 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.</p>
</div></body></html>"""}

# Macro tests
TEMPLATE_TESTMAC = '<html><body><h1 tal:content="page/headers/title"></h1> <b metal:use-macro="macros/head/test"></b> <div tal:content="structure page/content"></div></body></html>'
TEMPLATE_MAC1 = '<html><body><h1 tal:content="page/headers/title"></h1> <h2 metal:define-macro="test">MacroTest</h2> <div tal:content="structure page/content"></div></body></html>'
TEMPLATE_MAC2 = '<html><body><h1 tal:content="page/headers/title"></h1> <h3 metal:define-macro="test">MacroTest2</h3> <div tal:content="structure page/content"></div></body></html>'

CONFIG_MACROS = """<Content sub1>
macro head mac.html
</Content>

<Content sub1/sub3>
macro head mac2.html
</Content>
"""
RESULT_MACROS = {'index.html': """<html><body><h1>Test1</h1>  <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/index.html': """<html><body><h1>Test1</h1> <h2>MacroTest</h2> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub2/index.html': """<html><body><h1>Test1</h1> <h2>MacroTest</h2> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub3/index.html': """<html><body><h1>Test1</h1> <h3>MacroTest2</h3> <div><p>This is the <b>first</b> test.</p>
</div></body></html>"""}

# Header tests
TEMPLATE_TESTHEADER = '<html><body><h1 tal:content="page/headers/title"></h1> <b tal:content="page/headers/subject"></b> <div tal:content="structure page/content"></div></body></html>'
CONTENT_TESTHEADER = """title: Test1
subject: Header test

This is the <b>first</b> test."""
CONFIG_HEADERS = """<Content sub1>
header subject Config1 Header
</Content>

<Content sub1/sub3>
header subject Config2 Header
</Content>
"""
RESULT_HEADERS = {'index.html': """<html><body><h1>Test1</h1> <b></b> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/index.html': """<html><body><h1>Test1</h1> <b>Config1 Header</b> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub2/index.html': """<html><body><h1>Test1</h1> <b>Config1 Header</b> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub3/index.html': """<html><body><h1>Test1</h1> <b>Config2 Header</b> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub3/test.html': """<html><body><h1>Test1</h1> <b>Header test</b> <div><p>This is the <b>first</b> test.</p>
</div></body></html>"""}

# Options tests
TEMPLATE_OPT1 = '<html><body><h1 tal:content="page/headers/title"></h1> <p>Opt1 Template</p> <div tal:content="structure page/content"></div></body></html>'
TEMPLATE_OPT2 = '<html><body><h1 tal:content="page/headers/title"></h1> <p>Opt2 Template</p> <div tal:content="structure page/content"></div></body></html>'
CONFIG_OPTIONS = """<Content sub1>
template opt1.html
</Content>

<Content sub1/sub3>
template opt2.html
</Content>
"""

RESULT_OPTIONS = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/index.html': """<html><body><h1>Test1</h1> <p>Opt1 Template</p> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub2/index.html': """<html><body><h1>Test1</h1> <p>Opt1 Template</p> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'sub1/sub3/index.html': """<html><body><h1>Test1</h1> <p>Opt2 Template</p> <div><p>This is the <b>first</b> test.</p>
</div></body></html>"""}

class InheritanceTestCases (unittest.TestCase):
	def setUp (self):
		self.site = SiteUtils.SiteBuilder()
		self.site.buildDirs()
		
	def tearDown (self):
		self.site.destroySite()
		pass
		
	def _runTest_ (self, expectedResult, configFile=None):
		if (configFile is None):
			conf = os.path.join (self.site.getSiteDir(), "test.config")
		else:
			conf = configFile
		update = updateSite.UpdateSite (conf, None, ui=SiteUtils.SilentUI())
		update.buildSite()
		comp = SiteUtils.DirCompare()
		res = comp.compare (self.site.getDestDir(), expectedResult)
		self.failUnless (res is None, res)
		
	def testDefaultConfig (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testMacroInheritance (self):
		self.site.createTemplate ('template.html', TEMPLATE_TESTMAC)
		self.site.createTemplate ('mac.html', TEMPLATE_MAC1)
		self.site.createTemplate ('mac2.html', TEMPLATE_MAC2)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createContent ('sub1/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub2/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub3/index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG_MACROS)
		self._runTest_ (RESULT_MACROS)
		
	def testHeaderInheritance (self):
		self.site.createTemplate ('template.html', TEMPLATE_TESTHEADER)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createContent ('sub1/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub2/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub3/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub3/test.txt', CONTENT_TESTHEADER)
		self.site.createConfigFile ('test.config', CONFIG_HEADERS)
		self._runTest_ (RESULT_HEADERS)
		
	# Options include template, catalogue-index-template, etc
	def testOptionsInheritance (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createTemplate ('opt1.html', TEMPLATE_OPT1)
		self.site.createTemplate ('opt2.html', TEMPLATE_OPT2)
		
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createContent ('sub1/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub2/index.txt', CONTENT1)
		self.site.createContent ('sub1/sub3/index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG_OPTIONS)
		self._runTest_ (RESULT_OPTIONS)
		
if __name__ == '__main__':
	unittest.main()
	
