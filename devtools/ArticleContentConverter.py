#!/usr/bin/python

import time, string, sys, os, shutil, codecs
import xml.sax, xml.sax.saxutils

import logging

DATE_FORMAT="%d-%m-%Y"
TIME_FORMAT="%H:%M:%S"


def ListDirectory (dir):
	dirList = os.listdir (dir)
	goodList = []
	for dir in dirList:
		if (dir[0] == '.'):
			# Hidden file - don't include
			pass
		elif (dir == "CVS"):
			# CVS Directory - don't include
			pass
		else:
			goodList.append (dir)
	return goodList
	
class EntryPathFinder:
	def __init__ (self, srcDir):
		self.srcDir = srcDir
		
	def findEntriesInDay (self, dayPath):
		"""Find all entries that are present in this day
		"""
		dayList = ListDirectory (dayPath)
		dayList.sort()
		# Work through the list backwards
		dayList.reverse()
		return dayList

	def findEntries (self, numDaysToFind, multipleEntriesPerDay=0):
		"""Look for path entries.
		   If numDaysToFind is not -1 then limit the number found to that many days worth
		   If multipleEntriesPerDay is true then return all entries found for a given day
		"""
		if (numDaysToFind == -1):
			findAll = 1
		else:
			findAll = 0
			
		daysFound = 0
			
		# Get all years
		# Get all months in a year
		# Get all days in a year
		# Get one day entry in a given day
		# When required number of entries is found - stop
		foundPaths = []
		srcDir = self.srcDir
		yearList = ListDirectory (srcDir)
		yearList.sort()
		# Work through the list backwards
		yearList.reverse()
		for year in yearList:
			yearPath = os.path.join (srcDir, year)
			monthList = ListDirectory (yearPath)
			monthList.sort()
			# Work through the list backwards
			monthList.reverse()
			for month in monthList:
				monthPath = os.path.join (yearPath, month)
				dayList = ListDirectory (monthPath)
				dayList.sort()
				dayList.reverse()
				for day in dayList:
					daysFound += 1
					# Get one day entry - even if there are multiple present!
					dayPath = os.path.join (monthPath, day)
					entryList = ListDirectory (dayPath)
					if (multipleEntriesPerDay):
						# We need to grab all the entries in here
						entryList.sort()
						entryList.reverse()
						for entry in entryList:
							foundPaths.append (os.path.join (dayPath, entry))
					else:						
						if (len (entryList) > 0):
							# Grab the first entry we come across in this day
							foundPaths.append (os.path.join (dayPath, entryList[0]))
						
					if (not findAll):
						if (daysFound == numDaysToFind):
							return foundPaths
		return foundPaths

class ArticleContent:
	def __init__ (self, existingArticle=None):
		self.log = logging.getLogger ("ArticleContent.ArticleContent")
		if (existingArticle is None):
			self.log.debug ("Creating a new article.")
			self.creationDate = time.localtime()
			self.modificationDate = self.creationDate
			self.articleTitle = u""
			self.articleBody = u""
		else:
			self.log.debug ("Loading existing article from: %s" % existingArticle)
			articleReader = ArticleContentReader (existingArticle, self)
			self.existingArticlePath = existingArticle
			
	def setArticleBody (self, newBody):
		self.articleBody = newBody
		
	def setArticleTitle (self, newTitle):
		self.articleTitle = newTitle
		
	def getArticleBody (self):
		return self.articleBody
		
	def getArticleTitle (self):
		return self.articleTitle
		
	def getArticleCreationDate (self):
		return self.creationDate
		
	def getArticleModificationDate (self):
		return self.modificationDate
		
	def getDateShort (self):
		# Return the date as dd-mm-yyyy
		return time.strftime (DATE_FORMAT,self.getArticleCreationDate())
		
	def getDateLong (self):
		# Return the date as Monday, 11 November 2002
		dayStr = str (int (time.strftime ('%d', self.getArticleCreationDate())))
		return time.strftime ('%A, %%s %B %Y', self.getArticleCreationDate()) % dayStr
		
	def getRFC822Date (self):
		# Returns the date in RFC822 format
		return time.strftime ('%a, %d %b %Y %H:%M:%S %Z', self.getArticleCreationDate())
		
	def getTime24Hour (self):
		# Return the time as HH:MM in 24Hr format
		return time.strftime (TIME_FORMAT,self.getArticleCreationDate())
		
	def getTime12Hour (self):
		# Return the time as hh:mm am/pm in 12 Hr format
		# We can't use %p because of a strange bug in 2.1
		dateTime = self.getArticleCreationDate()
		if (dateTime[3] >= 12):
			amPM = "pm"
			if (dateTime[3] == 12):
				hour = '12'
			else:
				hour = str (dateTime[3] - 12)
		else:
			amPM = "am"
			if (dateTime[3] == 0):
				hour = '12'
			else:
				hour = str (dateTime[3])
		return hour + ':' + string.zfill (str (dateTime[4]), 2) + " " + amPM
		
	def saveArticle (self, path):
		self.modificationDate = time.localtime()
		articleWriter = ArticleContentWriter (self)
		articleWriter.write (path)
	
class ArticleContentReader (xml.sax.handler.ContentHandler):
	def __init__ (self, file, article):
		self.log = logging.getLogger ("ArticleContent.ArticleContentReader")
		self.elementMap = {'creationDate': (u"", {})
											,'creationTime': (u"", {})
											,'modificationDate': (u"", {})
											,'modificationTime': (u"", {})
											,'title': (u"", {})
											,'body': (u"", {})}
		self.inArticle = 0
		self.articleVersion = 1.0
		self.currentData = u""
		self.currentAttributes = []
		self.log.debug ("Creating XML parser.")
		self.parser = xml.sax.parse (file, self)
		if (self.articleVersion != 1.1):
			raise "Unsupported article version."
		
		self.log.debug ("Determining creation date.")
		article.creationDate = time.strptime (self.getData ('creationDate')+self.getData ('creationTime')
																					, DATE_FORMAT + TIME_FORMAT)

		article.modificationDate = time.strptime (self.getData ('modificationDate')+self.getData ('modificationTime')
																							,DATE_FORMAT + TIME_FORMAT)																					
		self.log.debug ("Getting article title")
		article.articleTitle = self.getData ('title')
		self.log.debug ("Getting article body")
		article.articleBody = self.getData ('body')
		
	def getData (self, name, attName=None):
		data = self.elementMap [name]
		if (attName is not None):
			return data[1][attName]
		return data[0]
		
	def startElement (self, name, attributes):
		if (name == "article"):
			self.inArticle = 1
			self.articleVersion = float (attributes ["version"])
		if (self.inArticle and self.elementMap.has_key (name)):
			# Get the attributes
			self.currentAttributes = attributes
			self.currentData = u""
		
	def endElement (self, name):
		if (name == "article"):
			self.inArticle = 0
		if (self.inArticle and self.elementMap.has_key (name)):
			self.elementMap [name] = (self.currentData, self.currentAttributes)
		
	def characters (self, txt):
		self.currentData = self.currentData + txt
	
class ArticleContentWriter:
	""" creation-date: date
		title: title
		
		body.
		"""
	def __init__ (self, article):
		self.log = logging.getLogger ("ArticleContent.ArticleContentWriter")
		self.article = article
		
	def write (self, path):
		ENCODING = 'UTF-8'
		codec = codecs.lookup (ENCODING)[0]
		file = open (path, 'w')
		
		createDate = self.article.getArticleCreationDate()
		modDate = self.article.getArticleModificationDate()
		self.log.debug ("Writing out date/time")
		file.write ("creation-date: %s\n" % time.strftime ("%Y-%m-%d %H:%M:%S", createDate))
		
		self.log.debug ("Getting title")
		title = self.article.getArticleTitle()
		if (len (title.strip()) > 0):
			self.log.debug ("Found title - writing out")
			file.write ("title: %s\n" % codec (title)[0])
		
		self.log.debug ("Writing out body")	
		file.write ("\n")
		file.write (codec (self.article.getArticleBody())[0])
		file.close()
		print "Setting last-modified time, etc."
		shutil.copystat (self.article.existingArticlePath, path)

print "Weblog conversion utility"
srcDir = sys.argv[1]
print "Using source directory %s" % srcDir

print "Getting all entries."
finder = EntryPathFinder(srcDir)
allEntries = finder.findEntries (-1, multipleEntriesPerDay=1)
for entry in allEntries:
	print "Reading old article %s" % entry
	article = ArticleContent (entry)
	newFilename = entry[:-4]+".post"
	print "Saving in new format as %s" % newFilename
	article.saveArticle (newFilename)
	
print "Finished!"
							