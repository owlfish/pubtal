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

import unittest, copy, os.path, os, codecs

if __name__ == '__main__':
	logging.basicConfig()
	LOCATION=''
else:
	LOCATION=os.path.join(os.getcwd(), "tests", "Content", "OpenOffice")
root = logging.getLogger()
root.setLevel (logging.WARN)
utf8encoder = codecs.lookup ('utf-8')[0]

TEMPLATE1 = '<?xml version="1.0" encoding="iso-8859-15"?>\n<html><body><h1 tal:content="page/headers/title"></h1> <div tal:content="structure page/content"></div></body></html>'
CONTENT1_FILE = os.path.join(LOCATION, "smartquotes.sxw")
CONFIG1 = """<Template>
output-type XHTML
character-set ISO-8859-15
</Template>

<Content>
preserve-html-spaces false
</Content>"""
RESULT1 = {'index.html': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1></h1> <div><p>This is a "test" with some - fairly good hyphens.</p>
</div></body></html>"""}

TEMPLATE2 = '<?xml version="1.0" encoding="utf-8"?>\n<html><body><h1 tal:content="page/headers/title"></h1> <div tal:content="structure page/content"></div></body></html>'
CONFIG2 = """<Template>
output-type XHTML
character-set utf-8
</Template>

<Content>
preserve-html-spaces false
</Content>"""
RESULT2 = {'index.html': utf8encoder (u"""<?xml version="1.0"?>
<html><body><h1></h1> <div><p>This is a \u201ctest\u201d with some \u2013 fairly good hyphens.</p>
</div></body></html>""")[0]}

CONTENT3_FILE = os.path.join(LOCATION, "linebreaks.sxw")
RESULT3 = {'index.html': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1></h1> <div><p>This is a test with a newline<br />
or two.</p>
</div></body></html>"""}

CONTENT4_FILE = os.path.join (LOCATION, "imagedoc.sxw")
temp = open (os.path.join (LOCATION, 'hut.jpg'))
IMAGE_DATA = temp.read()
temp.close()
RESULT4 = {'index.html': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1></h1> <div><p>This test contains two images. This first one <img src="linked-image.jpg" alt="Graphic1" /> and another one: </p>
<p><img src="Pictures/index_html1000000000000101000000ABE5AC9EED.jpg" alt="Graphic2" /></p>
</div></body></html>""", 'Pictures/index_html1000000000000101000000ABE5AC9EED.jpg': IMAGE_DATA}

CONTENT5_FILE = os.path.join (LOCATION, "specialchars.sxw")
RESULT5 = {'index.html': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1></h1> <div><p>There is an ampersand escape in HTML: &amp;amp;</p>
<p>This is a bold tag: &lt;b&gt;Bold&lt;/b&gt;</p>
<p>Fun eh?</p>
</div></body></html>"""}

CONFIG6 = """<Template>
output-type XHTML
character-set ISO-8859-15
</Template>
"""

RESULT6 = {'index.html': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1></h1> <div><p>This test contains two images.&nbsp; This first one <img src="linked-image.jpg" alt="Graphic1" /> and another one: </p>
<p><img src="Pictures/index_html1000000000000101000000ABE5AC9EED.jpg" alt="Graphic2" /></p>
</div></body></html>""", 'Pictures/index_html1000000000000101000000ABE5AC9EED.jpg': IMAGE_DATA}

class XHTMLTestCases (unittest.TestCase):
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
		
	def testISO8859_15 (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		contentf = open (CONTENT1_FILE, 'r')
		content = contentf.read()
		contentf.close()
		self.site.createContent ('index.sxw', content)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testISO8859_1 (self):
		self.site.createTemplate ('template.html', TEMPLATE2)
		contentf = open (CONTENT1_FILE, 'r')
		content = contentf.read()
		contentf.close()
		self.site.createContent ('index.sxw', content)
		self.site.createConfigFile ('test.config', CONFIG2)
		self._runTest_ (RESULT2)
		
	def testLineBreaks (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		contentf = open (CONTENT3_FILE, 'r')
		content = contentf.read()
		contentf.close()
		self.site.createContent ('index.sxw', content)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT3)
	
	def testImageSupport (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		contentf = open (CONTENT4_FILE, 'r')
		content = contentf.read()
		contentf.close()
		self.site.createContent ('index.sxw', content)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT4)
		
	def testNonbreakingSpaceSupport (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		contentf = open (CONTENT4_FILE, 'r')
		content = contentf.read()
		contentf.close()
		self.site.createContent ('index.sxw', content)
		self.site.createConfigFile ('test.config', CONFIG6)
		self._runTest_ (RESULT6)

	def testSepcialCharSupport (self):
		self.site.createTemplate ('template.html', TEMPLATE1)
		contentf = open (CONTENT5_FILE, 'r')
		content = contentf.read()
		contentf.close()
		self.site.createContent ('index.sxw', content)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT5)
		
if __name__ == '__main__':
	unittest.main()
	
