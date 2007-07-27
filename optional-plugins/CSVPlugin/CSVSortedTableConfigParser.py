from pubtal import ConfigurationParser, SiteConfiguration

import os.path

try:
	import logging
except:
	from pubtal import InfoLogging as logging
	
import CSVContext

class csvSortedTableConfig:
	def __init__ (self, ui):
		self.ui = ui
		
	def parseConfig (self, configPage):
		self.log = logging.getLogger ("csvSortedTableConfig")
		self.configPage = configPage
		self.directiveStack = []
		self.pageList = []
		self.pageConfigItem = None
		self.pageSorterList = []
		self.pageSorterColumnName = None
		self.pageSorterMapping  = None
		self.sourceFile = None
		self.warningGiven = 0
		self.baseDir = os.path.dirname (configPage.getSource())
		self.relativeBaseDir = os.path.dirname (configPage.getRelativePath())
		
		parser = ConfigurationParser.ConfigurationParser()
		parser.setDefaultHandler (self)
		
		confFile = open (self.configPage.getSource(), 'r')
		parser.parse(confFile)
		confFile.close()
		return self.pageList
		
	def startDirective (self, directive, options):
		if (self.sourceFile is None):
			if (not self.warningGiven):
				self.ui.warn ("No source file specified in CSVSortedTables config file %s" % self.configPage.getRelativePath())
				self.warningGiven = 1
			return
		self.directiveStack.append (directive)
		if (directive == 'PAGE'):
			newPage = self.configPage.getDuplicatePage (self.sourceFile)
			self.pageList.append (newPage)
			self.pageConfigItem = SiteConfiguration.PageConfigItem()
			if (len (options) > 0):
				self.pageConfigItem.setOption ('destinationNamePath', os.path.join (self.relativeBaseDir, options))
		elif (directive == 'SORT'):
			self.pageSorterColumnName = options
			self.pageSorterMapping  = None
		
	def endDirective (self, directive):
		if (self.sourceFile is None):
			return
		if (directive == 'PAGE'):
			self.pageConfigItem.setOption ('column-sorter', CSVContext.ColumnSorter (self.pageSorterList))
			self.pageSorterList = []
			self.pageConfigItem.updatePage (self.pageList [-1])
			self.pageConfigItem = None
		elif (directive == 'SORT'):
			self.pageSorterList.append ((self.pageSorterColumnName, self.pageSorterMapping))
			
		self.directiveStack.pop()
		
	def option (self, line):
		if (self.warningGiven):
			# We have already warned the user about the lack of source-file, so stop parsing.
			return
			
		if (len (self.directiveStack) > 0):
			directive = self.directiveStack [-1]
		else:
			directive = None
		if (directive is None):
			if (line.lower().startswith ('source-file')):
				self.sourceFile = os.path.join (self.baseDir, line [line.find (' ')+1:])
		elif (directive == 'PAGE'):
			if (line.lower().startswith ('header')):
				mnStart = line.find (' ')
				mnEnd = line.find (' ', mnStart+1)
				headerName = line [mnStart+1:mnEnd]
				header = line [mnEnd + 1:]
				self.pageConfigItem.addHeader (headerName, header)
		elif (directive == 'SORT'):
			if (self.pageSorterMapping is None):
				self.pageSorterMapping = {}
				
			if (line.lower().startswith ('value')):
				mnStart = line.find (' ')
				mnEnd = line.rfind (' ')
				self.pageSorterMapping [line [mnStart+1:mnEnd]] = line [mnEnd + 1:]
			elif (line.lower().startswith ('empty-value')):
				self.pageSorterMapping [''] = line [line.find (' ')+1:]
