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
	
from pubtal import SiteUtils
import updateSite

import unittest, copy, os.path

if __name__ == '__main__':
	logging.basicConfig()
	
root = logging.getLogger()
root.setLevel (logging.WARN)

TEMPLATE1 = '<html><body><h1 tal:content="page/headers/title"></h1> <div tal:content="structure page/content"></div></body></html>'
CONTENT1 = """title: Test1

This is the <b>first</b> test.  It has spaces.

And a paragraph.

1
2
3

So there, jimmy lad!"""
CONFIG1 = ""
RESULT1 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.&nbsp; It has spaces.</p>
<p>And a paragraph.</p>
<p>1<br>
2<br>
3</p>
<p>So there, jimmy lad!</p>
</div></body></html>"""}

# Test 2
CONFIG2 = """<Content>
preserve-html-spaces 0
</Content>"""

RESULT2 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.  It has spaces.</p>
<p>And a paragraph.</p>
<p>1<br>
2<br>
3</p>
<p>So there, jimmy lad!</p>
</div></body></html>"""}

# XHTML version
CONFIG3 = """<Template>
output-type XHTML
</Template>"""

RESULT3 = {'index.html': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.&nbsp; It has spaces.</p>
<p>And a paragraph.</p>
<p>1<br />
2<br />
3</p>
<p>So there, jimmy lad!</p>
</div></body></html>"""}

class PreserveSpacesTests (unittest.TestCase):
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
		
	def testDefaultConfiguration (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testNotPreserveSpaces (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG2)
		self._runTest_ (RESULT2)
	
	def testPreserveSpacesXHTML (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runTest_ (RESULT3)
		
if __name__ == '__main__':
	unittest.main()
	
