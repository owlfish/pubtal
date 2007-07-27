class CatalogueContent:
	def __init__ (self, contentFile, codec):
		self.filename = contentFile
		self.codec = codec
		
		sourceFile = open (contentFile, 'r')
		self.items = []
		
		self.catalogueHeaders = self._readHeaders_(sourceFile)
		headers = self._readHeaders_ (sourceFile)
		while (len (headers) > 0):
			self.items.append (headers)
			headers = self._readHeaders_ (sourceFile)
			
	def getCatalogueHeaders (self):
		return self.catalogueHeaders
		
	def getItems (self):
		return self.items
			
	def _readHeaders_ (self, sourceFile):
		readingHeaders = 1
		headers = {}
		while (readingHeaders):
			line = self.codec (sourceFile.readline())[0]
			offSet = line.find (':')
			if (offSet > 0):
				headers [line[0:offSet]] = line[offSet + 1:].strip()
			else:
				readingHeaders = 0
		return headers
