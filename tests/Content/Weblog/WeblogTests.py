""" Unit tests cases.

	Copyright (c) 2009 Colin Stewart (http://www.owlfish.com/)
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
WEBLOG_TEMPLATE = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<title tal:content="page/weblog-name"></title>
	</head>
	<body>
		<!-- Loop over all days in the index. -->
		<div tal:repeat="day page/days">
			<h2 tal:content="day/date">Date of the day goes here</h2>
			<!-- Loop over all posts in the day.  -->
			<div tal:repeat="post day/posts">
				<h3>
					<b tal:replace="post/headers/date">Time of post</b>
					<b tal:condition="post/headers/title" tal:omit-tag> - </b><b tal:replace="post/headers/title">Post Title</b>
				</h3>
				<div>
					<p tal:replace="structure post/content">Content of post goes here</p>
				</div>
			</div> 
		</div> 
	</body>
</html>
"""

POST1 = """creation-date: 2004-04-28 22:21:26
title: The first post.

This is a first post to a new weblog.  The post is written in <b>HTMLText</b> format, but could have been written using <b>Open Office</b> instead.
"""

POST2 = """creation-date: 2004-05-01 14:37
title: A second post.

This is the second post.
"""

POST3 = """creation-date: 2004-05-01 15:37
title: A third post.

This is the third post.
"""

POST4 = """creation-date: 2004-05-02 21:00
title: A fourth post.

This is the fourth post.
"""

POST5 = """creation-date: 2004-05-03 14:37
title: A fifth post.

This is the fifth post - the next post will push the first one out of the index.
"""

CONFIG1 = """<SiteConfig>
ignore-filter .*\.svn.*
</SiteConfig>"""
RESULT1 = {'index.html': """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<title>Weblog</title>
	</head>
	<body>
		<!-- Loop over all days in the index. -->
		<div>
			<h2>Monday, 3 May 2004</h2>
			<!-- Loop over all posts in the day.  -->
			<div>
				<h3>
					2:37 PM
					 - A fifth post.
				</h3>
				<div>
					<p>This is the fifth post - the next post will push the first one out of the index.</p>

				</div>
			</div> 
		</div><div>
			<h2>Sunday, 2 May 2004</h2>
			<!-- Loop over all posts in the day.  -->
			<div>
				<h3>
					9:00 PM
					 - A fourth post.
				</h3>
				<div>
					<p>This is the fourth post.</p>

				</div>
			</div> 
		</div><div>
			<h2>Saturday, 1 May 2004</h2>
			<!-- Loop over all posts in the day.  -->
			<div>
				<h3>
					3:37 PM
					 - A third post.
				</h3>
				<div>
					<p>This is the third post.</p>

				</div>
			</div><div>
				<h3>
					2:37 PM
					 - A second post.
				</h3>
				<div>
					<p>This is the second post.</p>

				</div>
			</div> 
		</div><div>
			<h2>Wednesday, 28 April 2004</h2>
			<!-- Loop over all posts in the day.  -->
			<div>
				<h3>
					10:21 PM
					 - The first post.
				</h3>
				<div>
					<p>This is a first post to a new weblog.&nbsp; The post is written in <b>HTMLText</b> format, but could have been written using <b>Open Office</b> instead.</p>

				</div>
			</div> 
		</div> 
	</body>
</html>
"""}

# Test 2
CONFIG2 = """<SiteConfig>
ignore-filter .*\.svn.*
</SiteConfig>
<Content>
weblog-index-disabled True
</Content>
"""

RESULT2 = {}

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
		
	def testBasicWeblog (self):
		self.site.createTemplate ('template.html', WEBLOG_TEMPLATE)
		self.site.createContent ('first.post', POST1)
		self.site.createContent ('second.post', POST2)
		self.site.createContent ('third.post', POST3)
		self.site.createContent ('fourth.post', POST4)
		self.site.createContent ('fifth.post', POST5)
		self.site.createConfigFile ('test.config', CONFIG1)
		self._runTest_ (RESULT1)
		
	def testWeblogIndexDisabled (self):
		self.site.createTemplate ('template.html', WEBLOG_TEMPLATE)
		self.site.createContent ('first.post', POST1)
		self.site.createContent ('second.post', POST2)
		self.site.createContent ('third.post', POST3)
		self.site.createContent ('fourth.post', POST4)
		self.site.createContent ('fifth.post', POST5)
		self.site.createConfigFile ('test.config', CONFIG2)
		self._runTest_ (RESULT2)
		
if __name__ == '__main__':
	unittest.main()
	
