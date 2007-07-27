import re

TAG_OPTIONAL=1
TAG_REQUIRED=0
TAG_FORBIDDEN=2

def validationMapParser (inputData):
	regex = re.compile ('("([^"]*)"(,?))|(,)')
	endtagmap = {None:None, 'R': TAG_REQUIRED, 'F': TAG_FORBIDDEN, 'O': TAG_OPTIONAL}
	tagmap = {}
	namemap = {}
	# Skip the first line
	for line in inputData.splitlines()[1:]:
		colCount = 0
		name = None
		endTag = None
		validContents = None
		removeContents = None
		match = regex.match (line)
		while (match is not None):
			if (colCount == 0):
				name = match.group(2)
			elif (colCount == 1):
				endTag = endtagmap [match.group(2)]
			elif (colCount == 2):
				validContents = match.group(2)
			elif (colCount == 3):
				removeContents = match.group(2)
			match = regex.match (line, match.end(0))
			colCount += 1

		tagList = []
		if (validContents is not None):
			for tag in validContents.split (','):
				try:
					tagName = tag.strip()
					if (tagName.startswith ('%')):
						tagList.extend (namemap [tagName])
					else:
						tagList.append (tagName)
				except KeyError, err:
					print "Error adding %s to %s" % (tagName, name)
					raise err
		if (removeContents is not None):
			# We need to remove some values.
			for tag in removeContents.split (','):
				tagName = tag.strip()
				if (tagName.startswith ('%')):
					for realTagName in namemap [tagName]:
						tagList.remove (realTagName)
				else:
					tagList.remove (tagName)
				# Are we defining a name, or a tag?
		if (name.startswith ('%')):
			# Defining a name
			namemap [name] = tagList
		else:
			tagmap [name] = (tagList,endTag)
	return tagmap, namemap

def printMap (aMap, aVarname):
	print "%s = {" % aVarname ,
	itemsList = aMap.items()
	name, values = itemsList [0]
	print "'%s': %s" % (name, str (values)) ,
	
	for name, values in itemsList[1:-1]:
		print ",'%s': %s" % (name, str (values))
	name, values = itemsList [-1]
	print ",'%s': %s}" % (name, str (values))
	
def printBlockList (nameList, aVarname):
	print "%s = %s" % (aVarname, str (nameList))
	
htmlmap, htmlnamemap = validationMapParser (open ("html-validation-map.csv").read())
xhtmlmap, xhtmlnamemap = validationMapParser (open ("xhtml-validation-map.csv").read())

printMap (htmlmap, 'HTML_TAG_MAP')
printMap (xhtmlmap, 'XHTML_TAG_MAP')

printBlockList (htmlnamemap ['%block'], 'HTML_BLOCK_LIST')
printBlockList (xhtmlnamemap ['%block'], 'XHTML_BLOCK_LIST')
