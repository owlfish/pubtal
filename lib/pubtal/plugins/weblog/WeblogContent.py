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

import anydbm, os, os.path, re, time, string, md5, codecs
from pubtal import timeformat

FIELDREGEX=re.compile ('(?<!,),(?!,)')
SUPPORTED_DATES= ["%Y %m %d %H:%M:%S", "%Y %m %d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
INTERNAL_DATE_FORMAT="%Y%m%d%H:%M:%S"

try:
	import logging
except:
	from pubtal import InfoLogging as logging

from pubtal import SitePublisher, DateContext
from simpletal import simpleTAL, simpleTALES

class WeblogPostTree:
	""" This class maintains a tree of all posts in a weblog.  The tree is indexed by
		date, and the value stored is the relative path to the individual post.
		
		Additionally the cache of last 'N' posts is maintained here.
	"""
	def __init__ (self):
		# A dictionary of years, months, days, time.  A post consists of key 'time' and then value 'path/to/post'
		self.postMap = {}
		# Cache of the last 'n' posts
		self.lastNPostsCache = {}
		self.log = logging.getLogger ("PubTal.WeblogContent.WeblogPostTree")
		
	def getMonthsPosts (self, monthStr):
		# monthStr is in yyyymm format
		foundPosts = []
		dayMap = self.postMap [int (monthStr[0:4])][int (monthStr[4:6])]
		dayList = dayMap.keys()
		dayList.sort()
		dayList.reverse()
				
		for day in dayList:
			postMap = dayMap [day]
			postList = postMap.keys()
			postList.sort()
			postList.reverse()
			for post in postList:
				foundPosts.append (postMap [post])
		return foundPosts
		
	def getDaysPosts (self, dayStr):
		# dayStr is in yyyymmdd format
		foundPosts = []
		dayMap = self.postMap [int (dayStr[0:4])][int (dayStr[4:6])][int (dayStr [6:8])]
		dayList = dayMap.keys()
		dayList.sort()
		dayList.reverse()
		for postTime in dayList:
			foundPosts.append (dayMap [postTime])
		return foundPosts

	def getLatestPosts (self, numberOfPosts):
		if (self.lastNPostsCache.has_key (numberOfPosts)):
			self.log.debug ("Cache hit for %s last number of posts." % str (numberOfPosts))
			return self.lastNPostsCache [numberOfPosts]
		else:
			self.log.debug ("Cache miss for %s last number of posts." % str (numberOfPosts))
		foundPosts = []
		yearList = self.postMap.keys()
		yearList.sort()
		yearList.reverse()
		for year in yearList:
			monthMap = self.postMap [year]
			monthList = monthMap.keys()
			monthList.sort()
			monthList.reverse()
			for month in monthList:
				dayMap = monthMap [month]
				dayList = dayMap.keys()
				dayList.sort()
				dayList.reverse()
				for time in dayList:
					timeMap = dayMap [time]
					timeList = timeMap.keys()
					timeList.sort()
					timeList.reverse()
					for postTime in timeList:
						foundPosts.append (timeMap [postTime])
						if (len (foundPosts) == numberOfPosts):
							self.lastNPostsCache [numberOfPosts] = foundPosts
							return foundPosts
		self.lastNPostsCache [numberOfPosts] = foundPosts
		return foundPosts
		
	def getAllMonthlyNames (self):
		# Unlike all the other functions, this one returns earliest year/month first.
		foundNames = []
		yearList = self.postMap.keys()
		yearList.sort()
		yearList.reverse()
		for year in yearList:
			monthMap = self.postMap [year]
			monthList = monthMap.keys()
			monthList.sort()
			for month in monthList:
				if (month < 10):
					foundNames.append ("%s0%s" % (str (year), str (month)))
				else:
					foundNames.append ("%s%s" % (str (year), str (month)))
		return foundNames
		
	def getAllPostPaths (self):
		# Returns the relative paths of all of the posts we know about.
		foundPosts = []
		yearList = self.postMap.keys()
		for year in yearList:
			monthMap = self.postMap [year]
			monthList = monthMap.keys()
			for month in monthList:
				dayMap = monthMap [month]
				dayList = dayMap.keys()
				for time in dayList:
					timeMap = dayMap [time]
					timeList = timeMap.keys()
					for postTime in timeList:
						foundPosts.append (timeMap [postTime])
		return foundPosts
		
	def notePost (self, creationDate, postPath):
		self.lastNPostsCache = {}
		year = int (creationDate [0:4])
		month = int (creationDate [4:6])
		day = int (creationDate [6:8])
		# Time is in format hh:mi:ss
		postTime = creationDate [8:16]
		# Put this post into the map
		# First get, or create, the dayMap
		try:
			yearMap = self.postMap [year]
		except KeyError:
			yearMap = {}
			self.postMap [year] = yearMap
		try:
			monthMap = yearMap [month]
		except KeyError:
			monthMap = {}
			yearMap [month] = monthMap
		try:
			dayMap = monthMap [day]
		except KeyError:
			dayMap = {}
			monthMap [day] = dayMap
			
		# There's not going to be a post already in here, so we add it.
		dayMap [creationDate] = postPath
		
	def deletePost (self, creationDate):
		self.lastNPostsCache = {}
		year = int (creationDate [0:4])
		month = int (creationDate [4:6])
		day = int (creationDate [6:8])
		# Time is in format hh:mi:ss
		postTime = creationDate [8:16]
		# Put this post into the map
		# First get, or create, the dayMap
		try:
			yearMap = self.postMap [year]
			monthMap = yearMap [month]
			dayMap = monthMap [day]
		except KeyError:
			self.log.error ("Unable to find existing post for date %s" % creationDate)
			raise 
			
		del dayMap [creationDate]
		# If the day is empty then remove it.
		if (len (dayMap) == 0):
			del monthMap [day]
		if (len (monthMap) == 0):
			del yearMap [month]
		if (len (yearMap) == 0):
			del self.postMap [year]
			
class WeblogPostData:
	""" This class maintains a cache of Page context's and provides methods for 
		interacting with individual posts.
	"""
	def __init__ (self, templateConfig, pagePublisher):
		# This dictionary holds dictionaries that hold contexts.
		# The keys to this dictionary are output-types
		# The keys to the dictionary values are relative paths
		self.postContextCache = {}
		self.pagePublisher = pagePublisher
		self.templateConfig = templateConfig
		self.log = logging.getLogger ("PubTal.WeblogContent.WeblogPostData")
		
	def getPostCreationDate (self, page):
		""" Get the date a post was created.  This will usually cause the post to be
			read, unless it is already in a cache.
		"""
		context = self.getPostContextMap (page)
		return context ['headers']['postCreationDate']
		
	def getPostChecksum (self, page):
		""" Checksum the physical post file. """
		sum = md5.new()
		readFile = open (page.getSource(), 'r')
		while 1:
			buffer = readFile.read(1024*1024)
			if len(buffer) == 0:
				break
			sum.update(buffer)
		
		readFile.close()
		return sum.hexdigest()
		
	def invalidateCache (self, page):
		""" Invalidate caches for this post, causing the re-parsing of the post when the 
			context is next required.
		"""
		postRelativePath = page.getRelativePath()
		for contextCache in self.postContextCache.values():
			if (contextCache.has_key (postRelativePath)):
				del contextCache [postRelativePath]
		
	def getPostContextMap (self, page, pageTemplate=None):
		""" Returns the context for a particular post.  This will parse the post file
			if required, or return the context from cache.
		"""
		postRelativePath = page.getRelativePath()
		if (pageTemplate is None):
			# We use the index template to get the context.
			indexTemplate = self.templateConfig.getTemplate (page.getOption ('weblog-index-template', 'template.html'))
			outputType = indexTemplate.getOption ('output-type')
		else:
			outputType = pageTemplate.getOption ('output-type')
			
		if (self.postContextCache.has_key (outputType)):
			contextCache = self.postContextCache [outputType]
		else:
			contextCache = {}
			self.postContextCache [outputType] = contextCache
		
		# We use the relativePath as the key into the cache.
		if (contextCache.has_key (postRelativePath)):
			# Return a copy so that we can add/alter the context safely.
			return contextCache [postRelativePath].copy()
		
		postContentType = page.getOption ('weblog-content-type', 'HTMLText')
		postContentPublisher = self.pagePublisher.getContentPublisher (postContentType)
		if (postContentPublisher is None):
			msg = "Unable to find a publisher for weblog post item content type %s." % postContentType
			self.log.error (msg)
			raise SitePublisher.PublisherException (msg)
			
		self.log.info ("Retrieving page context for weblog post %s." % postRelativePath)
		if (pageTemplate is None):
			# We use the index template to get the context.
			pageContext = postContentPublisher.getPageContext (page, indexTemplate)
		else:
			pageContext = postContentPublisher.getPageContext (page, pageTemplate)			
		
		# Ideally this would be generalised, but for now we need to do content type specific stuff.
		headers = pageContext.get ('headers', {})
		try:
			if (postContentType == "OpenOffice"):
				#self.log.debug ("OO Headers are: " + str (headers))
				creationDate = time.strptime (headers ['creation-date'], "%Y-%m-%dT%H:%M:%S")
			else:
				creationDateStr = None
				creationDateStr = headers.get ('CreationDate', None)
				if (creationDateStr is None): creationDateStr = headers.get ('creationdate', None)
				if (creationDateStr is None): creationDateStr = headers ['creation-date']
				looking = 1
				attemptIndex = 0
				while (looking):
					# This will raise an exception if we have run out of formats to try.
					strFormat = SUPPORTED_DATES [attemptIndex]
					try:
						creationDate = time.strptime (creationDateStr, strFormat)
						looking = 0
					except ValueError:
						attemptIndex += 1
		except:
			msg = "Unable to determine post creation date!"
			self.log.error (msg)
			raise SitePublisher.PublisherException (msg)
			
		headers ['postCreationDate'] = timeformat.format (INTERNAL_DATE_FORMAT, creationDate)
		headers ['date'] = DateContext.Date (creationDate, "%I[NP]:%M %p")
		headers ['lastModifiedDate'] = DateContext.Date (time.localtime (page.getModificationTime()))
		weblogTagPrefix = page.getOption ('weblog-tag-prefix')
		if (weblogTagPrefix is not None):
			headers ['id'] = "tag:%s.%s" % (weblogTagPrefix, timeformat.format ('%Y%m%d%H%M%S', creationDate))
		# Need to do this in case we created all the headers
		pageContext ['headers'] = headers
		contextCache [postRelativePath] = pageContext
		return pageContext.copy()
		
class WeblogDatabase:
	def __init__ (self, weblogName, messageBus, dbDir, postTree, weblog):
		self.log = logging.getLogger ("PubTal.WeblogContent.WeblogDatabase")
		self.messageBus = messageBus
		self.dbDir = dbDir
		self.weblogName = weblogName
		self.weblog = weblog
		self.postTree = postTree
		# We need to transform the path name into ascii compatible strings for some anydbm implementations.
		self.utfencode = codecs.lookup ("utf8")[0]
		self.utfdecode = codecs.lookup ("utf8")[1]
		self._readDB_(dbDir)
		
	def getMonthOfLastPost (self):
		if (self.dataDB.has_key ('MonthOfLastPost')):
			monthOfLastPost = self.dataDB ['MonthOfLastPost']
			return (int (monthOfLastPost[0:4]), int (monthOfLastPost[4:6]))
		return (0,0)
		
	def setMonthOfLastPost (self, yearMonthTuple):
		self.monthOfLastPost = yearMonthTuple
		yearStr = str (yearMonthTuple [0])
		monthStr = str (yearMonthTuple [1])
		if (len (monthStr) == 1):
			self.dataDB ['MonthOfLastPost'] = "%s0%s" % (yearStr, monthStr)
		else:
			self.dataDB ['MonthOfLastPost'] = "%s%s" % (yearStr, monthStr)
			
	def getPostDateTime (self, page):
		postKey = 'POST:%s' % self.utfencode (page.getRelativePath())[0]
		if (self.dataDB.has_key (postKey)):
			self.log.debug ("Found post %s in database." % postKey)
			creationDate, checksum = FIELDREGEX.split (self.dataDB [postKey])
			return creationDate
		return None
		
	def getPostChecksum (self, page):
		postKey = 'POST:%s' % self.utfencode (page.getRelativePath())[0]
		if (self.dataDB.has_key (postKey)):
			creationDate, checksum = FIELDREGEX.split (self.dataDB [postKey])
			return checksum
		return None
		
	def isPostInDB (self, page):
		postKey = 'POST:%s' % self.utfencode (page.getRelativePath())[0]
		return self.dataDB.has_key (postKey)
		
	def setPostInfo (self, relativePath, creationDate, checksum):
		self.dataDB ['POST:%s' % self.utfencode (relativePath)[0]] = "%s,%s" % (creationDate, checksum)
		
	def deletePostInfo (self, relativePath):
		del self.dataDB ['POST:%s' % self.utfencode (relativePath)[0]]
		
	def _finished_ (self, eventType, data):			
		self.dataDB.close()
		
	def _readDB_ (self, dataDir):
		if (not os.path.exists (dataDir)):
			self.log.info ("Creating PubTal Data directory %s" % dataDir)
			os.makedirs (dataDir)
		dataDB = anydbm.open (os.path.join (dataDir, 'weblog-state-%s' % self.weblogName), 'c')
		self.dataDB = dataDB
		for key in dataDB.keys():
			if (key.startswith ('POST:')):
				postPath = self.utfdecode (key [5:])[0]
				# Value is in two fields, creationDate and checkSum
				creationDate, checksum = FIELDREGEX.split (dataDB[key])
				self.postTree.notePost (creationDate, postPath)
		# We need to close our database before shutdown.
		self.messageBus.registerListener ("PubTal.Shutdown", self._finished_)

class Weblog:
	def __init__ (self, name, dbDir, pagePublisher, config):
		self.log = logging.getLogger ("PubTal.WeblogContent.Weblog.%s" % name)
		self.weblogName = name
		self.dbDir = dbDir
		self.config = config
		self.messageBus = self.config.getMessageBus()
		self.contentConfig = self.config.getContentConfig()
		self.templateConfig = self.config.getTemplateConfig()
		self.pagePublisher = pagePublisher
		
		self.postTree = WeblogPostTree()
		self.postData = WeblogPostData (self.templateConfig, pagePublisher)
		
		# This dictionary records the names of the pages we have already generated.  
		# Possible values are 'yyyymm', 'yymmdd',  'index.html', 'rss.xml'
		self.pagesGenerated = {}
		# This is a tuple of year, month
		self.monthOfLastPost = None
		# Posts that aren't yet in the DB are cached in here until they are built, then they are added to the DB
		# We do this in order to avoid re-reading the file, and so that any fatal errors during page publication
		# do not update the database.
		self.newPostsCache = {}
		self.weblogDatabase = WeblogDatabase (name, self.messageBus, dbDir, self.postTree, self)
		self.messageBus.registerListener ("PageBuilder.Start", self._pageBuildStart_)
		
	def getPostTree (self):
		return self.postTree
		
	def getPostData (self):
		return self.postData
		
	def getMonthOfLastPost (self):
		if (self.monthOfLastPost is None):
			# First weblog page we've seen - read from the database
			self.monthOfLastPost = self.weblogDatabase.getMonthOfLastPost()
		return self.monthOfLastPost
		
	def setMonthOfLastPost (self, yearMonthTuple):
		self.monthOfLastPost = yearMonthTuple
		
	def getPostDateTime (self, page):
		relativePath = page.getRelativePath()
		dbValue = self.weblogDatabase.getPostDateTime (page)
		if (dbValue is not None):
			self.log.debug ("Post %s is in database, returning DB values." % relativePath)
			return dbValue
		elif (self.newPostsCache.has_key (relativePath)):
			self.log.info ("Post %s not yet in database, but has been read earlier." % relativePath)
			creationDate, checksum = self.newPostsCache [relativePath]
			return creationDate
		else:
			self.log.info ("Post %s not in database, and not yet read." % relativePath)
			# We need to determine the post date, which means reading in the file...
			creationDate = self.postData.getPostCreationDate (page)
			checksum = self.postData.getPostChecksum (page)
			# Store this for future reference
			self.newPostsCache [relativePath] = (creationDate, checksum)
			# Add it to the list of posts.
			self.postTree.notePost (creationDate, relativePath)
			return creationDate
	
	def checkPostForChange (self, page):
		# Checks the checksums of the file against that in the DB.
		# Updates the DB if it is out of sync.
		relativePath = page.getRelativePath()
		realChecksum = self.postData.getPostChecksum (page)
		dbChecksum = self.weblogDatabase.getPostChecksum (page)
		creationDate = self.weblogDatabase.getPostDateTime (page)
		
		if (self.newPostsCache.has_key (relativePath)):
			self.log.info ("NewPostsCache has page %s - it can't have changed yet." % relativePath)
			return 0
		if (dbChecksum is not None):
			if (realChecksum == dbChecksum):
				return 0
		self.log.info ("Post %s has changed, removing entry from DB and invalidating caches." % relativePath)
		if (creationDate is not None):
			# Remove the old version of it from the DB map.
			self.postTree.deletePost (creationDate)
			# Remove the old version from the database.
			self.weblogDatabase.deletePostInfo (relativePath)
			# Clear any context cache we might have
		self.postData.invalidateCache (page)
		
		# We need to determine the post date, which means reading in the file...
		realCreationDate = self.postData.getPostCreationDate (page)
		# Store this for future reference
		self.newPostsCache [relativePath] = (realCreationDate, realChecksum)
		# Add it to the list of posts.
		self.postTree.notePost (realCreationDate, relativePath)
		return 1
	
	def isPostInDB (self, page):
		return self.weblogDatabase.isPostInDB (page)
		
	def isPageGenerated (self, pageName):
		return self.pagesGenerated.has_key (pageName)
		
	def noteGeneratedPage (self, pageName):
		self.pagesGenerated [pageName] = 1
		
	def notePagePublished (self, pageName):
		if (self.pagesGenerated.has_key (pageName)):
			self.log.debug ("Page %s was published successfully." % pageName)
			del self.pagesGenerated [pageName]
			if (len (self.pagesGenerated) == 0):
				self.log.info ("All pages that we built have been published successfully - persisting cache to DB.")
				for key in self.newPostsCache.keys():
					creationDate, checksum = self.newPostsCache [key]
					self.weblogDatabase.setPostInfo (key, creationDate, checksum)
				if (self.monthOfLastPost is not None):
					# We referred to it, so we might have changed it.
					self.log.info ("Persisting the month of the last post (%s)." % str (self.monthOfLastPost))
					self.weblogDatabase.setMonthOfLastPost (self.monthOfLastPost)
		else:
			self.log.warn ("Page named %s was not built by us, but we published it anyway!" % pageName)
		
	def _pageBuildStart_ (self, eventType, data):
		# We have started page building, so we clear data from any previous page generation run
		self.pagesGenerated = {}
		self.newPostsCache = {}
		self.monthOfLastPost = self.weblogDatabase.getMonthOfLastPost()
		
class WeblogManager:
	def __init__ (self, pagePublisher):
		self.log = logging.getLogger ("PubTal.WeblogContent.WeblogManager")
		self.pagePublisher = pagePublisher
		self.weblogs = {}
		self.config = pagePublisher.getConfig()
		self.templateConfig = self.config.getTemplateConfig()
		self.dataDir = self.config.getDataDir()
		
	def getWeblog (self, page):
		weblogName = page.getOption ('weblog-name', 'Weblog')
		return self.weblogs [weblogName]
		
	def pageBuilder (self, page, options):
		pageList = []
		self.log.info ("Determing pages to build for input page %s" % str (page.getRelativePath()))
		buildAllClasses = options.get ('buildAllClasses', 0)
		monthlyTemplate = page.getOption ('weblog-month-template', None)
		indexTemplate = page.getOption ('weblog-index-template', "template.html")
		dayTemplate = page.getOption ('weblog-day-template', None)
		weblogSyndicationTemplates = page.getListOption ('weblog-syndication-template')
		weblogName = page.getOption ('weblog-name', 'Weblog')
		# We need to get the date/time that this post lives in.
		weblog = self.weblogs.get (weblogName, None)
		if (weblog is None):
			self.log.info ("This is the first post for weblog %s, loading weblog data." % weblogName)
			weblog = Weblog (weblogName, self.dataDir, self.pagePublisher, self.config)
			self.weblogs [weblogName] = weblog
		
		postTree = weblog.getPostTree()
		buildDayPage = 0
		
		if (buildAllClasses):
			self.log.info ("Build all classes detected.")
			# We build everything.
			buildDayPage = 1
		else:
			# We are only building the pages that have changed.
			indexSize = int (page.getOption ('weblog-index-size', '5'))
			if (weblog.isPostInDB (page)):
				self.log.debug ("Post is in the DB.")
				# We already know about this post, so let's see whether it is in the index.
				indexList = postTree.getLatestPosts (indexSize)
				if (page.getRelativePath() in indexList):
					self.log.debug ("Page is in the index.")
					# Page is in the index, so we better check to see whether it has changed or not.
					if (weblog.checkPostForChange(page)):
						# Page *has* changed since the last publication
						self.log.info ("Page %s has changed since last publication, re-building." % str (page))
						buildDayPage = 1
			else:
				self.log.info ("Potential new Post %s detected." % str (page))
				buildDayPage = 1
				if (monthlyTemplate is not None):
					# We need to check to see whether the monthly pages need re-building.
					# Causes the post to be read, but it is cached for later use.
					postDate = weblog.getPostDateTime (page)
					ourMonthYear = (int (postDate[0:4]), int (postDate [4:6]))
						
					if (weblog.getMonthOfLastPost() < ourMonthYear):
						self.log.info ("Detected first post of the month - need to rebuild all day and month pages!")
						monthlyTemplateConfig = self.templateConfig.getTemplate (monthlyTemplate)
						if (not monthlyTemplateConfig.getBooleanOption ('weblog-suppress-monthly-rebuild', 0)):
							self.log.info ("Monthly rebuild of month template is NOT suppressed.")
							for monthlyPageName in postTree.getAllMonthlyNames():
								if (not weblog.isPageGenerated (monthlyPageName)):
									self.log.info ("Generating month name %s archive." % monthlyPageName)
									# We've not done an archive page for this month yet, so let's generate one!
									archivePage = page.getDuplicatePage (page.getSource())
									archivePage.setName ('%s monthly archive for %s' % (weblogName, monthlyPageName))
									archivePage.setOption ('weblogPageType', 'month')
									archivePage.setOption ('weblogArchiveYearMonth', monthlyPageName)
									archivePage.setOption ('pageName', monthlyPageName)
									pageList.append (archivePage)
									weblog.noteGeneratedPage (monthlyPageName)
						else:
							self.log.info ("Monthly rebuild of month template IS suppressed.")
						
						if (dayTemplate is not None):
							dayTemplateConfig = self.templateConfig.getTemplate (dayTemplate)
							if (not dayTemplateConfig.getBooleanOption ('weblog-suppress-monthly-rebuild', 0)):
								self.log.info ("Monthly rebuild of day template is NOT suppressed.")
								contentDir = self.config.getContentDir()
								contentConfig = self.config.getContentConfig()
								for postRelativePath in postTree.getAllPostPaths():
									# Firstly we need a page for this post.
									postAbsPath = os.path.join (contentDir, postRelativePath)
									thisPostPage = contentConfig.getPage (postAbsPath)
									# Get the post page name (yyyymmdd)
									postDate = weblog.getPostDateTime (thisPostPage)
									postPageName = postDate [0:8]
									if (not weblog.isPageGenerated (postPageName)):
										self.log.debug ("No page for day %s has been built yet." % postPageName)
										thisPostPage.setOption ('weblogPageType','day')
										thisPostPage.setOption ('weblogPageDay', postPageName)
										thisPostPage.setOption ('pageName', postPageName)
										self.log.info ("Adding day to list of pages to be built.")
										pageList.append (thisPostPage)
										weblog.noteGeneratedPage (postPageName)
							else:
								self.log.info ("Monthly rebuild of day template IS suppressed.")
						
						weblog.setMonthOfLastPost (ourMonthYear)
					
		if (buildDayPage):
			postDate = weblog.getPostDateTime (page)
			# Post page name is yyyymmdd
			postPageName = postDate [0:8]
			if (dayTemplate is not None):
				if (not weblog.isPageGenerated (postPageName)):
					self.log.debug ("No page for day %s has been built yet." % postPageName)
					page.setOption ('weblogPageType','day')
					page.setOption ('weblogPageDay', postPageName)
					page.setOption ('pageName', postPageName)
					self.log.info ("Adding day to list of pages to be built.")
					pageList.append (page)
					weblog.noteGeneratedPage (postPageName)
			
			if (monthlyTemplate is not None):
				# Archive pageName is yyyymm
				monthlyPageName = postDate [0:6]
				if (not weblog.isPageGenerated (monthlyPageName)):
					self.log.info ("Generating monthly archive page %s to be built" % monthlyPageName)
					# We've not done an archive page for this month yet, so let's generate one!
					archivePage = page.getDuplicatePage (page.getSource())
					archivePage.setName ('%s monthly archive for %s' % (weblogName, monthlyPageName))
					archivePage.setOption ('weblogPageType', 'month')
					archivePage.setOption ('weblogArchiveYearMonth', monthlyPageName)
					archivePage.setOption ('pageName', monthlyPageName)
					pageList.append (archivePage)
					weblog.noteGeneratedPage (monthlyPageName)
			if (weblogSyndicationTemplates is not None):
				if (not weblog.isPageGenerated ("syndication.xml")):
					self.log.info ("Generating syndication page to be built")
					syndicationPage = page.getDuplicatePage (page.getSource())
					syndicationPage.setName ('%s Syndication Feed.' % weblogName)
					syndicationPage.setOption ('weblogPageType', 'syndication')
					syndicationPage.setOption ('pageName', 'syndication.xml')
					pageList.append (syndicationPage)
					weblog.noteGeneratedPage ("syndication.xml")
			if (not weblog.isPageGenerated (indexTemplate)):
				self.log.info ("Generating index page to be built")
				indexPage = page.getDuplicatePage (page.getSource())
				indexPage.setName ('%s Index.' % weblogName)
				indexPage.setOption ('weblogPageType', 'index')
				indexPage.setOption ('pageName', indexTemplate)
				pageList.append (indexPage)
				weblog.noteGeneratedPage (indexTemplate)
		
		return pageList

