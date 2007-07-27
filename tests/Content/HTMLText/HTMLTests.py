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
root.setLevel (logging.CRITICAL)

TEMPLATE1 = '<html><body><h1 tal:content="page/headers/title"></h1> <div tal:content="structure page/content"></div></body></html>'
CONTENT1 = """title: Test1

This is the <b>first</b> test.
With a newline
Or two

And a paragraph.

1
2
3

So there, jimmy lad!"""
CONFIG1 = ""
RESULT1 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.<br>
With a newline<br>
Or two</p>
<p>And a paragraph.</p>
<p>1<br>
2<br>
3</p>
<p>So there, jimmy lad!</p>
</div></body></html>"""}

# Test 2
CONFIG2 = """<Content>
htmltext-ignorenewlines 1
</Content>
"""

RESULT2 = {'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.
With a newline
Or two</p>
<p>And a paragraph.</p>
<p>1
2
3</p>
<p>So there, jimmy lad!</p>
</div></body></html>"""}

# Test 3
CONFIG3 = ""

CONTENT3 = """title: Test1

<p>This is the <b>first</b> test.
With a manual newline<br>
Or two
</p>

<p>And a paragraph.</p>

1
2
3

So there, jimmy lad!"""

RESULT3={'index.html': """<html><body><h1>Test1</h1> <div><p>This is the <b>first</b> test.
With a manual newline<br>
Or two
</p>
<p>And a paragraph.</p>
<p>1<br>
2<br>
3</p>
<p>So there, jimmy lad!</p>
</div></body></html>"""}

CONTENT4 = """title: Test4

<p>This is the <b>fourth</b> test in which <a href="here"><img src="here" title="title"></a> is used.
With a manual newline<br>
Or two
</p>

<p>And a paragraph.</p>

1
2
3

So there, jimmy lad <a href="there"><img src="there" title="Some title"></a>!"""

RESULT4={'index.html': """<html><body><h1>Test4</h1> <div><p>This is the <b>fourth</b> test in which <a href="here"><img src="here" title="title"></a> is used.
With a manual newline<br>
Or two
</p>
<p>And a paragraph.</p>
<p>1<br>
2<br>
3</p>
<p>So there, jimmy lad <a href="there"><img src="there" title="Some title"></a>!</p>
</div></body></html>"""}

# Test 5
CONTENT5 = """title: Test5

This is the <b>first</b> test.
With a newline"""
RESULT5 = {'index.html': """<html><body><h1>Test5</h1> <div><p>This is the <b>first</b> test.<br>
With a newline</p>
</div></body></html>"""}

# Error test - we *want* this to throw errors.
CONTENT6 = """title: Error test

This is simple text with a <a href="somewhere">link<body id="thebody">and body</body></a> and so on.
"""

# Test 7
CONTENT7 = """title: Test7

This is the <b>first</b> test &amp;lt hello.

Now for some character entities inside a pre:
<pre><code>This is &lt; that.</code></pre>"""
RESULT7 = {'index.html': """<html><body><h1>Test7</h1> <div><p>This is the <b>first</b> test &amp;lt hello.</p>
<p>Now for some character entities inside a pre:</p>
<pre><code>This is &lt; that.</code></pre>
</div></body></html>"""}

# Error test - we *want* this to throw errors.
CONTENT8 = """title: Error test

<pre><code>This is simple text with a <a href="somewhere">link<p class="cool" title="cool">and body</p></a> and so on.
</code></pre>
"""

# Error test - we *want* this to throw errors.
CONTENT9 = """title: Error test

This is simple text with a <a href="somewhere">link and body</p></a> and so on.
"""

# Error test - we *want* this to throw errors.
CONTENT10 = """title: Error test

<pre><code>This is simple text with a <a href="somewhere">link and body</p></a> and so on.
</code></pre>
"""

class ErrorUI (SiteUtils.SilentUI):
	def taskError (self, msg):
		self.errorMessage = msg
		
class HTMLTestCases (unittest.TestCase):
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
		
	def _runErrorTest_ (self, expectedResult, configFile=None):
		if (configFile is None):
			conf = os.path.join (self.site.getSiteDir(), "test.config")
		else:
			conf = configFile
		ui = ErrorUI()
		root = logging.getLogger()
		root.setLevel (logging.CRITICAL)
		update = updateSite.UpdateSite (conf, None, ui=ui)
		update.buildSite()
		self.failUnless (ui.errorMessage == expectedResult, "Received error: \n[%s] expected error \n[%s]" % (ui.errorMessage, expectedResult))
		
	def testDefaultConfiguration (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testIgnoreNewLines (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT1)
		self.site.createConfigFile ('test.config', CONFIG2)
		self._runTest_ (RESULT2)
		
	def testHTMLContent (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT3)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runTest_ (RESULT3)
		
	def testSingletonHTMLContent (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT4)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runTest_ (RESULT4)
		
	def testSingleParagraph (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT5)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT5)
		
	def testBadlyNestedHTML (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT6)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runErrorTest_ ('Page Publication failed: Element <body id="thebody"> is not allowed in current location: <p>This is simple text with a <a href="somewhere">link ')
	
	def testBadlyNestedHTML2 (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT8)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runErrorTest_ ('Page Publication failed: Element <p class="cool" title="cool"> is not allowed in current location: <pre><code>This is simple text with a <a href="somewhere">link ')
	
	def testBadlyEndTag (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT9)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runErrorTest_ ('Page Publication failed: End tag </p> is not allowed in current location: <p>This is simple text with a <a href="somewhere">link and body ')
	
	def testBadlyEndTag2 (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT10)
		self.site.createConfigFile ('test.config', CONFIG3)
		self._runErrorTest_ ('Page Publication failed: End tag </p> is not allowed in current location: <pre><code>This is simple text with a <a href="somewhere">link and body ')
	
	def testCharEntities (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		self.site.createContent ('index.txt', CONTENT7)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT7)
		
if __name__ == '__main__':
	unittest.main()
	
