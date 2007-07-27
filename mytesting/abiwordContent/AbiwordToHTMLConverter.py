""" Abiword to HTML Converter for PubTal

	Copyright (c) 2003 Colin Stewart (http://www.owlfish.com/)
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

import xml.sax, StringIO, cgi
import logging
#font-weight: bold; font-style: italic; text-decoration: underline, line-through, overline

HTML_StyleMap = {'italic': ('font-style', 'italic'), 'bold': ('font-weight', 'bold')
				,'subscript': ('vertical-align', 'sub'), 'superscript': ('vertical-align', 'super')
				,'underline': ('text-decoration', 'underline'), 'line-through': ('text-decoration', 'line-through')
				,'overline': ('text-decoration', 'overline')}
HTML_StartTagMap = {'text-style': '<span style="%s">', 'Bullet List': '<ul>'
					,'Numbered List': '<ol>', 'List Item': '<li>', 'link': '<a href="%s">'
					,'Start Bookmark': '<a name="%s">'
					,'Start endnote': '<a href="#%s">%s</a>'
					,'Endnote Anchor': '<a name="%s" style="vertical-align: super">%s</a>'
					,'table': '<table>', 'tablerow': '<tr>', 'tablecell': '<td%s>'
					,'p': '<p>', 'h1': '<h1>', 'h2': '<h2>', 'h3': '<h3>', 'h4': '<h4>'
					, 'h5': '<h5>', 'Plain Text': '<pre>'}
# Note that we don't have any <br> end tag - it's not used in either HTML or XHTML 
HTML_EndTagMap = {'text-style': '</span>', 'Bullet List': '</ul>'
					,'Numbered List': '</ol>', 'List Item': '</li>', 'link': '</a>'
					,'End Bookmark': '</a>'
					,'table': '</table>', 'tablerow': '</tr>', 'tablecell': '</td>'
					,'p': '</p>', 'h1': '</h1>', 'h2': '</h2>', 'h3': '</h3>', 'h4': '</h4>'
					, 'h5': '</h5>', 'Plain Text': '</pre>'}

class AbiwordToHTMLConverter (xml.sax.handler.ContentHandler, xml.sax.handler.DTDHandler):
	""" Convert AbiWord format to HTML or XHTML
	"""
	def __init__ (self):
		xml.sax.handler.ContentHandler.__init__ (self)
		self.log = logging.getLogger ("PubTal.AbiwordToHTMLConverter")
		
	def convertContent (self, content):
		self.result = StringIO.StringIO()
		self.scopeStack = []
		
		self.StartTagMap = HTML_StartTagMap
		self.EndTagMap = HTML_EndTagMap
		self.StyleMap = HTML_StyleMap
		
		self.ourParser = xml.sax.make_parser()
		self.log.debug ("Setting features of parser")
		self.ourParser.setFeature (xml.sax.handler.feature_external_ges, 0)
		self.ourParser.setFeature (xml.sax.handler.feature_namespaces, 0)
		self.ourParser.setContentHandler (self)
		
		# Initialise our state
		self.metaData = {}
		self.data = []
		self.currentAttributes = None
		
		self.statefulMarkup = StatefulMarkup (self.result, self.StartTagMap, self.EndTagMap)
		
		# Dictionary of current text styles (e.g. bold, italic, etc)
		self.textStyle = {}
		
		# List of endNotes that we've built up.  Tuple of (linkName, linkHTML)
		self.endNoteNum = 1
		self.endNoteToNumMap = {}
		self.endNotes = []
		
		# Parse the content as XML
		self.ourParser.parse (content)
		
	def getBody (self):
		return self.result.getvalue()
		
	def getFootnotes (self):
		return u"".join (self.endNotes)
		
	def getMetadata (self):
		return self.metaData

	def startElement (self, tag, attributes):
		self.log.debug ("Recieved Start Tag: " + tag + " Attributes: " + str (attributes))
		self.currentAttributes = attributes
		propertiesList = attributes.get ('props', "").split (';')
		properties = {}
		for prop in propertiesList:
			breakPoint = prop.find (':')
			properties [prop[0:breakPoint].strip()] = prop [breakPoint + 1:].strip()
		self.log.debug ("Character properties: %s" % str (properties))
		if (tag == "abiword"):
			try:
				fileformat = attributes ['fileformat']
			except:
				msg = ("No fileformat attribute on abiword element!")
				self.log.error (msg)
				raise AbiwordFormatException (msg)
			
			if (fileformat != "1.1"):
				self.log.warn ("Only file format 1.1 has been tested.  Content is version %s" % fileformat)
		elif (tag == "p"):
			self.data = []
			self.statefulMarkup.startParagraph (tag, attributes, properties)
		elif (tag == "c"):
			self.writeStyledText()
			if (properties.get ("font-weight", "") == "bold"):
				self.textStyle ['bold'] = 1
			if (properties.get ("font-style","") == "italic"):
				self.textStyle ['italic'] = 1
			# This handles superscript and subscript
			textPosition = properties.get ("text-position", "")
			self.textStyle [textPosition] = 1
			# This handles overline, line-through, and underline
			textDecoration = properties.get ("text-decoration", "").split (" ")
			for decor in textDecoration:
				self.textStyle [decor] = 1
				
		elif (tag == "a"):
			linkDest = attributes ['xlink:href']
			self.result.write (self.StartTagMap ['link'] % cgi.escape (linkDest))
		elif (tag == "br"):
			# Write out any styled text and re-open SPANs as needed.
			self.writeStyledText()
			self.result.write (self.StartTagMap ['br'])
		elif (tag == "bookmark"):
			self.writeStyledText()
			self.statefulMarkup.startBookmark (tag, attributes, properties)
		elif (tag == "field"):
			self.writeStyledText()
			# Is this a footnote or endnote?
			type = attributes ['type']
			id = None
			if (type == "footnote_ref"):
				id = "footnote-id-%s" % attributes ['footnote-id']
				self.endNoteToNumMap [id] = self.endNoteNum
				self.result.write (self.StartTagMap ['Start endnote'] % (id, str (self.endNoteNum)))
				self.endNoteNum = self.endNoteNum + 1
			elif (type == "endnote_ref"):
				id = "endnote-id-%s" % attributes ['endnote-id']
				self.endNoteToNumMap [id] = self.endNoteNum
				self.result.write (self.StartTagMap ['Start endnote'] % (id, str (self.endNoteNum)))
				self.endNoteNum += 1
			elif (type == "endnote_anchor"):
				# The anchor text.
				id = "endnote-id-%s" % attributes ['endnote-id']
				self.result.write (self.StartTagMap ['Endnote Anchor'] % (id, str (self.endNoteToNumMap[id])))
			elif (type == "footnote_anchor"):
				# The anchor text for a footnote.
				id = "footnote-id-%s" % attributes ['footnote-id']
				self.result.write (self.StartTagMap ['Endnote Anchor'] % (id, str (self.endNoteToNumMap[id])))
		elif (tag == "foot" or tag == "endnote"):
			# Capture the footnote/endnote separately.
			self.scopeStack.append ((self.result, self.statefulMarkup))
			self.result = StringIO.StringIO()
			self.statefulMarkup = StatefulMarkup (self.result, self.StartTagMap, self.EndTagMap)
		elif (tag == "table"):
			# The begining of a table can mean the end of a list.
			self.statefulMarkup.structureChange()
			self.result.write (self.StartTagMap ['table'])
		elif (tag == "cell"):
			leftAttach = int (properties ['left-attach'])
			rightAttach = int (properties ['right-attach'])
			bottomAttach = int (properties ['bot-attach'])
			topAttach = int (properties ['top-attach'])
			width = rightAttach - leftAttach
			cellAtts = u""
			if (width > 1):
				cellAtts += ' colspan="%s"' % str (width)
			height = bottomAttach - topAttach
			if (height > 1):
				cellAtts += ' rowspan="%s"' % str (height)
			# Do we have to close a TR?
			if (leftAttach == 0):
				if (topAttach != 0):
					# This isn't the first row, so we need to close a previous one!
					self.result.write (self.EndTagMap ['tablerow'])
				self.result.write (self.StartTagMap ['tablerow'])
			self.result.write (self.StartTagMap ['tablecell'] % cellAtts)
		elif (tag == "m"):
			# For metadata we want to clear out any previous text we've accumulated.
			self.data = []
		else:
			#self.log.warn ("Unknown start element %s" % tag)
			self.statefulMarkup.structureChange()
			
	def endElement (self, tag):
		self.log.debug ("Recieved Real End Tag: " + tag)
		if (tag == "m"):
			keyName = self.currentAttributes ['key']
			if (keyName.startswith ("dc.")):
				keyName = keyName [3:]
			if (keyName == "creator"):
				# Used in PubTal to keep things the same as the examples.
				keyName = "author"
			data = u"".join (self.data)
			self.log.debug ("Meta information key=%s value=%s" % (keyName, data))
			self.metaData [keyName] = data
		elif (tag == "p"):
			self.writeStyledText()
			self.statefulMarkup.endParagraph (tag)
		elif (tag == "c"):
			self.writeStyledText()
			self.textStyle = {}
		elif (tag == "a"):
			self.result.write (self.EndTagMap ['link'])
		elif (tag == "foot" or tag == "endnote"):
			self.endNotes.append (self.result.getvalue())
			self.result, self.statefulMarkup = self.scopeStack.pop()
		elif (tag == "table"):
			self.statefulMarkup.structureChange()
			self.result.write (self.EndTagMap ['tablerow'])
			self.result.write (self.EndTagMap ['table'])
		elif (tag == "cell"):
			# Ends of cells can mean the end of a list - best check
			self.statefulMarkup.structureChange()
			self.result.write (self.EndTagMap ['tablecell'])
		elif (tag == "bookmark"):
			pass
		elif (tag == "field"):
			pass
		else:
			#self.log.warn ("Unknown end element %s" % tag)
			self.statefulMarkup.structureChange()
			
	def characters (self, data):
		# Accumulate the character data together so that we can merge all the newline events
		self.log.debug ("Recieved character data: " + data)
		self.data.append (data)
		
	def writeStyledText (self):
		if (len (self.data) == 0):
			self.log.debug ("No text to write.")
			return
		styleDictionary = {}
		for style in self.textStyle.keys():
			styleProperty, styleValue = self.StyleMap.get (style, (None, None))
			if (styleProperty is not None):
				curPropVal = styleDictionary.get (styleProperty, u"")
				if (len (curPropVal) > 0):
					curPropVal += ', ' + styleValue
				else:
					curPropVal = styleValue
				styleDictionary [styleProperty] = curPropVal
		# Now build the style attribute value.
		if (len (styleDictionary) > 0):
			styleValueList = []
			for property in styleDictionary.keys():
				# Get the value for this property
				value = styleDictionary [property]
				styleValueList.append (property + ": " + value)
			self.result.write (self.StartTagMap ['text-style'] % u"; ".join (styleValueList))
		
		# Write out the text
		self.result.write (cgi.escape (u"".join (self.data)))
		self.data = []
		if (len (styleDictionary) > 0):
			self.result.write (self.EndTagMap ['text-style'])
		

class StatefulMarkup:
	def __init__ (self, result, startTagMap, endTagMap):
		"""	The StatefulMarkup class is used to maintain the context for 
			either the main document or a footnote or endnote.
			
			It handles the complications of lists.
		"""
		self.log = logging.getLogger ("PubTal.AbiwordToHTMLConverter.StatefulMarkup")
		self.result = result
		self.StartTagMap = startTagMap
		self.EndTagMap = endTagMap
		self.paragraphType = None
		# List of currently open boomark (anchor) links.
		self.bookmarks = []
		# Current stack of lists.
		self.listStack = []
		
	def startParagraph (self, tag, attributes, properties):
		paragraphType = attributes.get ('style', "")
		self.log.debug ("Starting a new paragraph, type %s" % paragraphType)
		if (attributes.has_key ('listid')):
			# This is a list item.
			listStyle = properties.get ('list-style', 'Bullet List')
			listLevel = attributes ['level']
			if (len (self.listStack) > 0):
				# We already have a list opened, so let's compare levels
				oldListLevel, oldListType = self.listStack[-1]
				if (oldListLevel < listLevel):
					# We are growing outwards with this item.
					self.result.write (self.StartTagMap [listStyle])
					# Add this list to the stack
					self.listStack.append ((listLevel, listStyle))
				elif (oldListLevel > listLevel):
					# We are going down a level!
					# Take this opportunity to close out the list item.
					self.result.write (self.EndTagMap ['List Item'])
					# Close the actual list
					self.result.write (self.EndTagMap [oldListType])
					# Also close out the containing list item.
					# Take this opportunity to close out the list item.
					self.result.write (self.EndTagMap ['List Item'])
					self.listStack.pop()
				else:
					# This is an item in an existing list, so close out the last item.
					self.result.write (self.EndTagMap ['List Item'])
			else:
				# This is the first item in a new list!
				# Add this list to the stack
				self.listStack.append ((listLevel, listStyle))
				self.result.write (self.StartTagMap [listStyle])
			# This paragraph type is really a list item.
			self.paragraphType = "List Item"
		else:
			# This is not a list item - check for the possibility of an open list
			while (len (self.listStack) > 0):
				self.log.debug ("We have an open list, but the next P element is not a list item!")
				oldListLevel, oldListType = self.listStack.pop()
				# Take this opportunity to close out the list item.
				self.result.write (self.EndTagMap ['List Item'])
				# Close the old list type
				self.result.write (self.EndTagMap [oldListType])
				
			if (paragraphType.startswith ("Heading")):
				headingLevel = paragraphType [-1:]
				self.paragraphType = u"h" + headingLevel
			elif (paragraphType == "Plain Text"):
				self.paragraphType = "Plain Text"
			else:
				self.paragraphType = "p"
		self.result.write (self.StartTagMap [self.paragraphType])
		
	def endParagraph (self, tag):
		self.log.debug ("Closing paragraph of type %s" % self.paragraphType)
		while (len (self.bookmarks) > 0):
			oldBookmark = self.bookmarks.pop()
			self.result.write (self.EndTagMap ['End Bookmark'])
		# Don't write out the </li> for lists here - it depends on what follows next!
		if (self.paragraphType != 'List Item'):
			self.result.write (self.EndTagMap [self.paragraphType] + '\n')
		
	def startBookmark (self, tag, attributes, properties):
		# Is this the start, or end of a bookmark?
		type = attributes ['type']
		name = attributes ['name']
		if (type == "end" and name in self.bookmarks):
			# Closing a bookmark
			self.result.write (self.EndTagMap ['End Bookmark'])
			self.bookmarks.remove (name)
		elif (type == "start"):
			# Opening a new bookmark.
			self.result.write (self.StartTagMap ['Start Bookmark'] % name)
			self.bookmarks.append (name)
		
	def structureChange (self):
		"""	Called to indicate that the next tag type was not a paragraph.
			Used for when <table> closes a list, etc.
		"""
		while (len (self.listStack) > 0):
			self.log.debug ("We have an open list, but the next P element is not a list item!")
			oldListLevel, oldListType = self.listStack.pop()
			# Take this opportunity to close out the list item.
			self.result.write (self.EndTagMap ['List Item'])
			# Close the old list type
			self.result.write (self.EndTagMap [oldListType])
	
class AbiwordFormatException (Exception):
	pass
	
