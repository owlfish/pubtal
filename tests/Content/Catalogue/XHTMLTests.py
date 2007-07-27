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
	LOCATION=''
else:
	LOCATION=os.path.join(os.getcwd(), "tests", "Content", "Catalogue")
root = logging.getLogger()
root.setLevel (logging.WARN)

INDEX_TEMPLATE = '<?xml version="1.0" encoding="iso-8859-15"?>\n<html><body><h1 tal:content="page/headers/title"></h1> <div tal:repeat="item catalogue/entries" tal:content="item/headers/title"></div></body></html>'
ITEM_TEMPLATE = '<?xml version="1.0" encoding="iso-8859-15"?>\n<html><body><h1 tal:content="page/headers/title"></h1> <div tal:condition="exists: page/content" tal:content="structure page/content"></div> <a tal:condition="exists: catalogue/previous" tal:attributes="href catalogue/previous/destinationFilename">Previous</a> <a tal:condition="exists: catalogue/next" tal:attributes="href catalogue/next/destinationFilename">Next</a></body></html>'
CATALOGUE = """title: Testing Catalogue

filename: one.txt
title: Cat one

filename: two.txt
title: Cat two
"""
ONE_TXT = """title: Item One

This is the <b>first</b> item!
So there!
"""
TWO_TXT = """title: Item Two

This is the second item!"""
CONFIG1 = """<SiteConfig>
# Ignore the .txt files because we don't care about them in this test.
ignore-filter .*\.txt
</SiteConfig>
<Template>
output-type XHTML
</Template>
<Content>
catalogue-index-template template.xhtml
catalogue-item-template item-template.xhtml
</Content>"""
RESULT1 = {'index.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Testing Catalogue</h1> <div>Cat one</div><div>Cat two</div></body></html>"""
,'one.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Cat one</h1>   <a href="two.xhtml">Next</a></body></html>"""
,'two.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Cat two</h1>  <a href="one.xhtml">Previous</a> </body></html>"""}

# Test 2
CONFIG2 = """<SiteConfig>
# Ignore the .txt files because we publish them as part of the catalogue.
ignore-filter .*\.txt
</SiteConfig>
<Content>
catalogue-item-content-type HTMLText
catalogue-index-template template.xhtml
catalogue-item-template item-template.xhtml
</Content>

<Template>
output-type XHTML
</Template>"""

RESULT2 = {'index.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Testing Catalogue</h1> <div>Item One</div><div>Item Two</div></body></html>"""
,'one.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Item One</h1> <div><p>This is the <b>first</b> item!<br />
So there!<br />
</p>
</div>  <a href="two.xhtml">Next</a></body></html>"""
,'two.xhtml': """<?xml version="1.0" encoding="iso-8859-15"?>
<html><body><h1>Item Two</h1> <div><p>This is the second item!</p>
</div> <a href="one.xhtml">Previous</a> </body></html>"""}

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
		
	def testBasicCatalogue (self):
		self.site.createTemplate ('template.xhtml', INDEX_TEMPLATE)
		self.site.createTemplate ('item-template.xhtml', ITEM_TEMPLATE)
		self.site.createContent ('index.catalogue', CATALOGUE)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testItemContentCatalogue (self):
		self.site.createTemplate ('template.xhtml', INDEX_TEMPLATE)
		self.site.createTemplate ('item-template.xhtml', ITEM_TEMPLATE)
		self.site.createContent ('index.catalogue', CATALOGUE)
		self.site.createContent ('one.txt', ONE_TXT)
		self.site.createContent ('two.txt', TWO_TXT)
		self.site.createConfigFile ('test.config', CONFIG2)
		self._runTest_ (RESULT2)
		
if __name__ == '__main__':
	unittest.main()
	
