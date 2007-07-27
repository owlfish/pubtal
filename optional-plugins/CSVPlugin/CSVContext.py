import ASV

from simpletal import simpleTAL, simpleTALES

try:
	import logging
except:
	import InfoLogging as logging

import codecs

class ColumnSorter:
	def __init__ (self, columnList):
		self.columnList = columnList
		self.log = logging.getLogger ('ColumnSorter')
		
	def setup (self, fieldNames):
		mapList = []
		for columnName, translationMap in self.columnList:
			try:
				colNum = fieldNames.index (columnName)
				mapList.append ((colNum, translationMap))
			except ValueError, e:
				self.log.error ("No such column name as %s" % name)
				raise e
		self.mapList = mapList
			
	def sort (self, row1, row2):
		result = 0
		for colNum, map in self.mapList:
			result = self.doSort (row1, row2, colNum, map)
			if (result != 0):
				return result
		return result
		
	def doSort (self, row1, row2, colNum, map):
		if (map is None):
			col1 = row1[colNum]
			col2 = row2[colNum]
		else:
			try:
				col1 = map [row1[colNum]]
			except KeyError, e:
				self.log.warn ("No key found for key %s - assuming low value" % row1[colNum])
				return -1
			try:
				col2 = map [row2[colNum]]
			except KeyError, e:
				self.log.warn ("No key found for key %s - assuming low value" % row1[colNum])
				return 1
		if (col1 < col2):
			return -1
		if (col1 == col2):
			return 0
		if (col1 > col2):
			return 1

class CsvContextCreator:
	def __init__ (self, fileName, fileCodec):
		self.log = logging.getLogger ("CSVTemplate.CsvContextCreator")
		self.csvData = ASV.ASV()
		self.csvData.input_from_file(fileName, ASV.CSV(), has_field_names = 1)
		self.fieldNames = self.csvData.get_field_names()
		self.conv = fileCodec
		
	def getContextMap (self, sorter=None):
		orderList = []
		for row in self.csvData:
			orderList.append (row)
			
		if (sorter is not None):
			sorter.setup (self.fieldNames)
			try:
				orderList.sort (sorter.sort)
			except Exception, e:
				self.log.error ("Exception occured executing sorter: " + str (e))
				raise e
		contextList = []
		for row in orderList:
			rowMap = {}
			colCount = 0
			for col in row:
				if (col != ""):
					rowMap[self.fieldNames[colCount]] = self.conv(col)[0]
				colCount += 1
			contextList.append (rowMap)
		return contextList
		
	def getRawData (self):
		return unicode (self.csvData)

class CSVTemplateExpander:
	def __init__ (self, sourceFile, name="csvList"):
		self.contextFactory = CsvContextCreator (sourceFile)
		self.name = name
		self.template=None
		
	def expandTemplate (self, templateName, outputName, additionalContext = None, sorter=None):
		context = simpleTALES.Context()
		context.addGlobal (self.name, self.contextFactory.getContextMap (sorter))
		
		if (additionalContext is not None):
			context.addGlobal (additionalContext[0], additionalContext[1])
		
		if (self.template is None):
			templateFile = open (templateName, 'r')
			self.template = simpleTAL.compileHTMLTemplate (templateFile)
			templateFile.close()
		
		outputFile = open (outputName, 'w')
		self.template.expand (context, outputFile)
		outputFile.close()
		
