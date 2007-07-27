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

root = logging.getLogger()
root.setLevel (logging.WARN)

# Default test
TEMPLATE1 = '<html><body><h1 tal:content="page/headers/title"></h1> <div tal:content="structure page/content"></div></body></html>'
TEMPLATE2 = '<html><body><h1 tal:content="page/headers/title"></h1> <h2>Content</h2><div tal:content="structure page/content"></div></body></html>'
TEMPLATE3 = '<html><body><h1 tal:content="page/headers/title"></h1> <h3>Content</h3><div tal:content="structure page/content"></div></body></html>'
TEMPLATE4 = '<html><body><h1 tal:content="page/headers/title"></h1> <h4>Content</h4><div tal:content="structure page/content"></div></body></html>'
CONTENT1 = """title: Test1

This is the <b>first</b> test."""
CONFIG1 = """
<Content onedir>
template template2.html
</Content>

<Content onedir/two.txt>
template template3.html
</Content>

<Content *.xtxt>
template template4.xhtml
content-type HTMLText
</Content>

"""

RESULT1 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'onedir/one.html': """<html><body><h1>Test1</h1> <h2>Content</h2><div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'onedir/two.html': """<html><body><h1>Test1</h1> <h3>Content</h3><div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'twodir/three.xhtml': """<html><body><h1>Test1</h1> <h4>Content</h4><div><p>This is the <b>first</b> test.</p>
</div></body></html>"""}

CONFIG2 = """
<Content onedir>
template template2.html
</Content>

<Content onedir/two.txt>
template template3.xhtml2
</Content>

<Content *.xtxt>
template template4.xhtml
content-type HTMLText
</Content>

<Template *.xhtml2>
output-type XHTML
</Template>

<Template template4.xhtml>
output-type XHTML
</Template>

"""

RESULT2 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'onedir/one.html': """<html><body><h1>Test1</h1> <h2>Content</h2><div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'onedir/two.xhtml2': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Test1</h1> <h3>Content</h3><div><p>This is the <b>first</b> test.</p>
</div></body></html>""", 'twodir/three.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Test1</h1> <h4>Content</h4><div><p>This is the <b>first</b> test.</p>
</div></body></html>"""}

class TemplateConfCases (unittest.TestCase):
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
		
	def testContentConfigs (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createTemplate ('template2.html', TEMPLATE2)
		self.site.createTemplate ('template3.html', TEMPLATE3)
		self.site.createTemplate ('template4.xhtml', TEMPLATE4)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createContent ('onedir/one.txt', CONTENT1)
		self.site.createContent ('onedir/two.txt', CONTENT1)
		self.site.createContent ('twodir/three.xtxt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testTemplateConfigs (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createTemplate ('template2.html', TEMPLATE2)
		self.site.createTemplate ('template3.xhtml2', TEMPLATE3)
		self.site.createTemplate ('template4.xhtml', TEMPLATE4)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createContent ('onedir/one.txt', CONTENT1)
		self.site.createContent ('onedir/two.txt', CONTENT1)
		self.site.createContent ('twodir/three.xtxt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG2)
		self._runTest_ (RESULT2)
		
if __name__ == '__main__':
	unittest.main()
	
