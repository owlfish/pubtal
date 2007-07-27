""" Weblog plugin for PubTal

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
import os.path, time

try:
	import logging
except:
	from pubtal import InfoLogging as logging
	
from pubtal import SitePublisher, DateContext
from simpletal import simpleTAL, simpleTALES

import WeblogContent

# These two maps provide a fast lookup for month names
SHORT_MONTH_MAP = {}
LONG_MONTH_MAP = {}
for month in range (1,13):
	SHORT_MONTH_MAP[month] = time.strftime ('%b', (2004,month,1,1,1,1,0,1,0))
	LONG_MONTH_MAP[month] = time.strftime ('%B', (2004,month,1,1,1,1,0,1,0))

def getPluginInfo ():
	builtInContent = [{'functionality': 'content', 'content-type': 'Weblog' ,'file-type': 'post','class': WeblogPagePublisher}]
	return builtInContent
	
class WeblogPagePublisher (SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.WeblogPagePublisher")
		self.manager = WeblogContent.WeblogManager(pagePublisher)
		self.log.info ("Registering page builder with content config.")
		siteConfig = pagePublisher.getConfig()
		contentConfig = siteConfig.getContentConfig()
		contentConfig.registerPageBuilder ('Weblog', self.manager.pageBuilder)
		self.templateConfig = siteConfig.getTemplateConfig()
		self.contentConfig = contentConfig
		self.contentDir = siteConfig.getContentDir()
		
	def publish (self, page):
		pageType = page.getOption ('weblogPageType')
		weblog = self.manager.getWeblog(page)
		if (pageType == 'day'):
			self.log.debug ("Getting template for day page.")
			template = self.templateConfig.getTemplate (page.getOption ('weblog-day-template', 'template.html'))
			self.log.debug ("Found weblog day template name of: " + str (template))
		elif (pageType == 'index'):
			self.log.debug ("Getting template for index page.")
			template = self.templateConfig.getTemplate (page.getOption ('weblog-index-template', 'template.html'))
			self.log.debug ("Found weblog index template name of: " + str (template))
		elif (pageType == 'syndication'):
			self.log.debug ("Getting templates for syndication pages.")
			weblogSyndicationTemplates = page.getListOption ('weblog-syndication-template')
			if (weblogSyndicationTemplates is None or len (weblogSyndicationTemplates) == 0):
				msg = "Syndication attempted, but no templates are defined!"
				self.log.error (msg)
				raise SitePublisher.PublisherException (msg) 
				msg = "Syndication attempted, but no template defined!"
				
			for templateName in weblogSyndicationTemplates:
				context = simpleTALES.Context(allowPythonPath=1)
				template = self.templateConfig.getTemplate (templateName)
				# Get the page context for this content
				map = self.getPageContext (page, template)
				context.addGlobal ('page', map)
				macros = page.getMacros()
				# Determine the destination for this page
				relativeDestPath = map ['destinationPath']
				self.pagePublisher.expandTemplate (template, context, relativeDestPath, macros)
			weblog.notePagePublished (page.getOption ('pageName'))
		elif (pageType == 'month'):
			self.log.debug ("Getting template for monthly archive page.")
			template = self.templateConfig.getTemplate (page.getOption ('weblog-month-template', 'template.html'))
		
		if (pageType != 'syndication'):
			self.log.debug ("Building non-syndication page.")
			context = simpleTALES.Context(allowPythonPath=1)
			
			# Get the page context for this content
			self.log.debug ("Getting page context.")
			map = self.getPageContext (page, template)
			self.log.debug ("Adding 'page' object to SimpleTALES.Context")
			context.addGlobal ('page', map)
			macros = page.getMacros()
			
			# Determine the destination for this page
			relativeDestPath = map ['destinationPath']
			self.log.debug ("Expanding template.")
			self.pagePublisher.expandTemplate (template, context, relativeDestPath, macros)
			weblog.notePagePublished (page.getOption ('pageName'))
		
	def getPageContext (self, page, template):
		pageMap = SitePublisher.ContentPublisher.getPageContext (self, page, template)
		# The pageMap will contain two top level entries: months and days.
		# Pages go in the following locations:
		# day - yyyy/mm/ddmmyyyy.html
		# index - index.html
		# syndication - rss.xml
		# archive - yyyy/mm/archive.html
		#  links are to the URL location: ddmmyyyy.html#HH:mi:ss
		
		# Default depth is 0.  i.e. posts appear in weblog/a.post and we want to generate the index
		# no directories higher, in weblog/
		self.log.debug ("Determining weblog home.")
		weblogDepth = int (page.getOption ('weblog-post-depth', '0')) + 1
		# The monthly template is used to determine whether to generate the monthlyArchive object.
		monthlyTemplate = page.getOption ('weblog-month-template', None)
		# The site's hostname is needed for creating absolute URLs
		siteURLPrefix = page.getOption ('url-prefix')
		# Used for the default value for header/weblog-name
		weblogName = page.getOption ('weblog-name', 'Weblog')
		
		outputType = template.getOption ('output-type')
		plainTextMaxSize = template.getOption ('plaintext-maxsize')
		if (plainTextMaxSize is not None):
			plainTextMaxSize = int (plainTextMaxSize)
		destExtension = '.' + template.getTemplateExtension()
		# We need the day's extension for permaLinks - so let's work that out.
		dailyTemplateName = page.getOption ('weblog-day-template', None)
		if (dailyTemplateName is not None):
			dayTemplate = self.templateConfig.getTemplate (dailyTemplateName)
			dayExtension = '.' + dayTemplate.getTemplateExtension()
		else:
			dayExtension = None
			
		weblogRelativeHomeDestDir = pageMap ['destinationPath']
		# Takes weblog/2004/01/12-34.html and turns it into weblog
		for depth in range (weblogDepth):
			weblogRelativeHomeDestDir = os.path.split (weblogRelativeHomeDestDir)[0]
			
		self.log.debug ("weblogRelativeHomeDestDir is %s" % weblogRelativeHomeDestDir)
		
		# Now get the depth of the weblog...
		head, tail = os.path.split (weblogRelativeHomeDestDir)
		weblogDepth = 0
		while (tail != ''):
			weblogDepth += 1
			head, tail = os.path.split (head)
			
		# We need the data associated with this weblog
		self.log.debug ("Getting weblog data object.")
		weblog = self.manager.getWeblog(page)
		postData = weblog.getPostData()
		postTree = weblog.getPostTree()
		pageType = page.getOption ('weblogPageType')
		
		if (pageType == 'day'):
			# We need to generate the list of posts for this day.
			dayStr = page.getOption ("weblogPageDay")
			self.log.debug ("Determining all posts for day %s." % dayStr)
			postList = postTree.getDaysPosts (dayStr)
			relativeDestPath = os.path.join (weblogRelativeHomeDestDir, dayStr[0:4], dayStr[4:6], "%s%s%s%s" % (dayStr [6:8],dayStr [4:6], dayStr [0:4], destExtension))
		elif (pageType == 'index' or pageType == 'syndication'):
			# We need to get the index list of posts.
			indexSize = int (page.getOption ('weblog-index-size', '5'))
			self.log.debug ("Determining latest posts for index or syndication.")
			postList = postTree.getLatestPosts (indexSize)
			if (pageType == 'index'):
				relativeDestPath = os.path.join (weblogRelativeHomeDestDir, "index%s" % destExtension)
			else:
				self.log.debug ("Determining name of syndication file (template name is %s." % template.getTemplateName())
				relativeDestPath = os.path.join (weblogRelativeHomeDestDir, "%s" % os.path.split (template.getTemplateName())[1])
		elif (pageType == 'month'):
			archiveStr = page.getOption ("weblogArchiveYearMonth")
			self.log.debug ("Determining all posts for monthly archive %s." % archiveStr)
			postList = postTree.getMonthsPosts (archiveStr)
			relativeDestPath = os.path.join (weblogRelativeHomeDestDir, archiveStr[0:4], archiveStr[4:6], "archive%s" % destExtension)
		
		dayList = []
		curDay = "00000000"
		curRealDate = None
		dayMap = None
		lastModifiedDate = None
		for post in postList:
			# Get the context for this post
			self.log.debug ("Getting context for post %s" % post)
			fullPathToPost = os.path.join (self.contentDir, post)
			self.log.debug ("Full path to the post is %s" % fullPathToPost)
			pageForPost = self.contentConfig.getPage (fullPathToPost)
			postLastModified = pageForPost.getModificationTime()
			if (lastModifiedDate is None or (lastModifiedDate < postLastModified)):
				lastModifiedDate = postLastModified
			postContext = postData.getPostContextMap (pageForPost, template)
			postCreationDate = postContext ['headers']['postCreationDate']
			if (curDay != postCreationDate [0:8]):
				self.log.debug ("Found a new day %s." % postCreationDate)
				# It's a brand new day!
				if (dayMap is not None):
					self.log.debug ("Adding old day to the map.")
					# Get the date as Monday, 11 November 2002
					dayMap ['date'] = DateContext.Date (curRealDate, '%a[LONG], %d[NP] %b[LONG] %Y')
					dayMap ['posts'] = dayPostList
					dayList.append (dayMap)
				dayMap = {}
				dayPostList = []
				curRealDate = time.strptime (postCreationDate, WeblogContent.INTERNAL_DATE_FORMAT)
				curDay = postCreationDate [0:8]
			
			# Just need to add permaLink to postContext and we are done!
			# We only do perma-links if daily archives are enabled.
			# Perma-links are relative to the current file only for day pages.
			if (dayExtension is not None):
				permaLink = "#%s" % postCreationDate [8:16]
				if (pageType == 'index' or pageType == 'syndication'):
					# Permalinks for posts have to index into the yyyy/mm/ddmmyyyy.html
					permaLink = os.path.join (postCreationDate [0:4], postCreationDate [4:6], "%s%s%s%s%s" % (postCreationDate [6:8],postCreationDate [4:6], postCreationDate [0:4], dayExtension, permaLink))
				elif (pageType == 'month'):
					# Permalinks for posts have to index into the yyyy/mm/ddmmyyyy.html
					permaLink = "%s%s%s%s%s" % (postCreationDate [6:8],postCreationDate [4:6], postCreationDate [0:4], dayExtension, permaLink)
				if (pageType == 'day'):
					# Permalink name
					postContext ['permaLinkName'] = postCreationDate [8:16]
						
				if (pageType != 'day'):
					postContext ['permaLink'] = permaLink
					if (siteURLPrefix is not None):
						postContext ['absolutePermaLink'] = '%s/%s' % (siteURLPrefix, os.path.join (weblogRelativeHomeDestDir, permaLink))
			
			# RSS requires truncating of output, so we need to check for that here.
			if (pageType == 'syndication' and outputType == 'PlainText' and plainTextMaxSize is not None):
				self.log.info ("Truncating syndication PlainText output to %s" % str (plainTextMaxSize))
				postBody = postContext.get ('content', None)
				if (postBody is not None):
					if (len (postBody) > plainTextMaxSize):
						postBody = postBody [:plainTextMaxSize] + "..."
					postContext ['content'] = postBody
				else:
					self.log.warn ("Post body not found!")
			dayPostList.append (postContext)
		
		if (dayMap is not None):
			self.log.debug ("Adding final day to the map.")
			# Get the date as Monday, 11 November 2002
			dayMap ['date'] = DateContext.Date (curRealDate, '%a[LONG], %d[NP] %b[LONG] %Y')
			dayMap ['posts'] = dayPostList
			dayList.append (dayMap)
			
		pageMap ['days'] = dayList
		
		# Now do the months object if applicable...
		if (monthlyTemplate is not None):
			self.log.debug ("Monthly template is defined, so creating monthlyArchive object.")
			monthlyArchiveList = []
			yearObject = {}
			yearsMonthList = []
			currentYear = None
			for monthYearStr in postTree.getAllMonthlyNames():
				# monthlyYearStr is yyyymm
				self.log.debug ("Handling year/month %s" % monthYearStr)
				year = int (monthYearStr [0:4])
				month = int (monthYearStr [4:6])
				if (currentYear != year):
					self.log.debug ("A new year found.")
					if (currentYear is not None):
						self.log.debug ("Old year will be added to the list.")
						yearObject ['yearName'] = str (currentYear)
						yearObject ['monthList'] = yearsMonthList
						monthlyArchiveList.append (yearObject)
						yearObject = {}
						yearsMonthList = []
					currentYear = year
				monthLong = LONG_MONTH_MAP [month]
				monthShort = SHORT_MONTH_MAP [month]
				# archiveLink depends on current page type, but should point to yyyy/mm/archive.html
				if (pageType == 'index' or pageType == 'syndication'):
					# Montly archives have to index into the yyyy/mm/archive.html
					archiveLink = os.path.join (monthYearStr [0:4], monthYearStr [4:6], "archive%s" % destExtension)
				elif (pageType == 'month' or pageType == 'day'):
					# Monthly archives and posts have to index into ../../yyyy/mm/archive.html
					archiveLink = os.path.join ('..', '..', monthYearStr [0:4], monthYearStr [4:6], "archive%s" % destExtension)
				yearsMonthList.append ({'monthNameLong': monthLong, 'monthNameShort': monthShort
										,'monthNumber': str (month), 'archiveLink': archiveLink})
			# Do the final year...
			if (currentYear is not None):
				self.log.debug ("A final year found.")
				yearObject ['yearName'] = str (currentYear)
				yearObject ['monthList'] = yearsMonthList
				monthlyArchiveList.append (yearObject)
		
			pageMap ['monthlyArchive'] = monthlyArchiveList
		
		if (pageType == 'month'):
			# We do special things for monthly archives.
			month = int (archiveStr[4:6])
			monthLong = LONG_MONTH_MAP [month]
			monthShort = SHORT_MONTH_MAP [month]
			pageMap ['yearName'] = archiveStr[0:4]
			pageMap ['monthNameLong'] = monthLong
			pageMap ['monthNameShort'] = monthShort
			pageMap ['depth'] = "../"*(weblogDepth + 2)
		elif (pageType == 'day'):
			pageMap ['dayDate'] = DateContext.Date (curRealDate, '%a[LONG], %d[NP] %b[LONG] %Y')
			pageMap ['depth'] = "../"*(weblogDepth + 2)
		else:
			pageMap ['depth'] = "../"*(weblogDepth)
			
		# The last modified date of this page is the latest modification date of its components.
		pageMap ['lastModifiedDate'] = DateContext.Date (time.localtime (lastModifiedDate), '%a[SHORT], %d %b[SHORT] %Y %H:%M:%S %Z')
		pageMap ['weblog-name'] = weblogName
		weblogTagPrefix = page.getOption ('weblog-tag-prefix')
		if (weblogTagPrefix is not None):
			pageMap ['weblog-tag-prefix'] = "tag:%s" % weblogTagPrefix
		if (siteURLPrefix is not None):
			if (len (weblogRelativeHomeDestDir) > 0):
				pageMap ['weblog-link'] = "%s/%s/" % (siteURLPrefix, weblogRelativeHomeDestDir)
			else:
				pageMap ['weblog-link'] = "%s/" % siteURLPrefix
		if (siteURLPrefix is not None):
			pageMap ['absoluteDestinationURL'] = '%s/%s' % (siteURLPrefix, relativeDestPath)
		pageMap ['destinationPath'] = relativeDestPath
		pageMap ['absoluteDestinationPath'] = os.path.join (self.destDir, relativeDestPath)
		return pageMap
		