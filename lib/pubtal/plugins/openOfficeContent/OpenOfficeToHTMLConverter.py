""" OpenOffice to HTML Converter for PubTal

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

import xml.sax, zipfile, StringIO, cgi, re, os.path
try:
	import logging
except:
	from pubtal import InfoLogging as logging

import OOFilter

from pubtal import HTMLWriter

OFFICE_URI='http://openoffice.org/2000/office'
TEXT_URI='http://openoffice.org/2000/text'
STYLE_URI='http://openoffice.org/2000/style'
TABLE_URI='http://openoffice.org/2000/table'
FORMAT_URI='http://www.w3.org/1999/XSL/Format'
DUBLIN_URI='http://purl.org/dc/elements/1.1/'
META_URI='http://openoffice.org/2000/meta'
XLINK_URI='http://www.w3.org/1999/xlink'
SVG_URI='http://www.w3.org/2000/svg'
DRAW_URI='http://openoffice.org/2000/drawing'

# These are the fo styles that will be treated as CSS styles.
SUPPORTED_FO_STYLES = {'text-align':1, 'font-weight':1, 'font-style':1, 'margin-left':1}

# These lists act as filters on which styles are applied to which kind of elements.
HEADING_STYLE_FILTER = ['text-align', 'margin-left']
PARAGRAPH_STYLE_FILTER = ['text-align', 'underline', 'line-through', 'overline'
						 ,'font-weight', 'font-style', 'vertical-align', 'margin-left']
SPAN_STYLE_FILTER = PARAGRAPH_STYLE_FILTER
						 
# These are the assumed defaults for paragraphs - OO setting these will be ignored.
DEFAULT_PARAGRAPH_STYLES = { 'text-align': 'start', 'font-weight': 'normal'
							,'font-style': 'normal', 'margin-left': '0cm'}

class OpenOfficeConverter:
	""" Convert OpenOffice format to HTML, XHTML or PlainText
	"""
	def __init__ (self):
		self.log = logging.getLogger ("PubTal.OOC")
		self.contentParser = SXWContentPraser ()
		
	def convert (self, fileName, config={}):		
		archive = zipfile.ZipFile (fileName, 'r')
		self.contentParser.parseContent (archive, config)
		archive.close()
		
	def getMetaInfo (self):
		return self.contentParser.getMetaInfo()
		
	def getContent (self):
		return self.contentParser.getContent()
		
	def getFootNotes (self):
		return self.contentParser.getFootNotes()
		
	def getPictures (self):
		return self.contentParser.getPictures()
		
		
class SXWContentPraser (xml.sax.handler.DTDHandler):
	""" Convert OpenOffice format to HTML, XHTML or PlainText
	"""
	def __init__ (self):
		self.log = logging.getLogger ("PubTal.OOC.SWXContentParser")
		self.saxFilter = OOFilter.SAXFilter ()
		
	def parseContent (self, archive, config):
		self.officeHandler = OfficeHandler(config)
		self.styleHandler = StyleHandler(config)
		self.textHandler = TextHandler (self.styleHandler, config)
		self.tableHandler = TableHandler (self.styleHandler, self.textHandler.result, config)
		self.drawHandler = DrawHandler (self.styleHandler, self.textHandler, config)
		self.saxFilter.setHandler (OFFICE_URI, self.officeHandler)
		self.saxFilter.setHandler (DUBLIN_URI, self.officeHandler)
		self.saxFilter.setHandler (META_URI, self.officeHandler)
		self.saxFilter.setHandler (STYLE_URI, self.styleHandler)
		self.saxFilter.setHandler (TEXT_URI, self.textHandler)
		self.saxFilter.setHandler (TABLE_URI, self.tableHandler)
		self.saxFilter.setHandler (DRAW_URI, self.drawHandler)
		self.saxFilter.setHandler (SVG_URI, self.drawHandler)
		
		self.ourParser = xml.sax.make_parser()
		self.log.debug ("Setting features of parser")
		self.ourParser.setFeature (xml.sax.handler.feature_external_ges, 0)
		self.ourParser.setFeature (xml.sax.handler.feature_namespaces, 1)
		self.ourParser.setContentHandler (self.saxFilter)
		
		# Initialise our variables
		self.pictureList = []
		
		self.log.debug ("Parsing meta data.")
		sxwContent = archive.read ('meta.xml')
		contentFile = StringIO.StringIO (sxwContent)
		self.ourParser.parse (contentFile)
		
		self.log.debug ("Parsing styles.")
		sxwContent = archive.read ('styles.xml')
		contentFile = StringIO.StringIO (sxwContent)
		self.ourParser.parse (contentFile)
		
		self.log.debug ("Parsing actual content.")
		sxwContent = archive.read ('content.xml')
		contentFile = StringIO.StringIO (sxwContent)
		self.ourParser.parse (contentFile)
		
		# Read pictures
		for pictureFilename, newFilename in self.drawHandler.getBundledPictures():
			self.pictureList.append ((newFilename, archive.read (pictureFilename)))
			
	def getMetaInfo (self):
		return self.officeHandler.getMetaInfo()
		
	def getContent (self):
		return self.textHandler.getContent()
		
	def getFootNotes (self):
		return self.textHandler.getFootNotes()
		
	def getPictures (self):
		return self.pictureList
		
class OfficeHandler:
	def __init__ (self, config):
		self.log = logging.getLogger ("PubTal.OOC.OfficeHandler")
		self.metaData = {}
		self.keywords = []
		self.charData = []
		self.cleanSmartQuotes = config.get ('CleanSmartQuotes', 0)
		self.cleanHyphens = config.get ('CleanHyphens', 0)
		
	def startElementNS (self, name, qname, atts):
		self.charData = []
		if (name[1] == 'document-content'):
			try:
				version = atts [(OFFICE_URI,'version')]
				self.log.debug ("Open Office format %s found." % version)
				if (float (version) != 1.0):
					self.log.warn ("Only OpenOffice format 1.0 is supported, version %s detected." % version)
			except Exception, e:
				msg = "Error determining OO version.  Error: " + str (e)
				self.log.error (msg)
				raise OpenOfficeFormatException (msg)
		
	def endElementNS (self, name, qname):
		data = u"".join (self.charData)
		self.charData = []
		if (name[0] == META_URI):
			if (name [1] == 'keyword'):
				self.keywords.append (data)
			elif (name [1] == 'creation-date'):
				self.metaData [name [1]] = data
		if (name[0] == DUBLIN_URI):
			self.metaData [name [1]] = data
	
	def characters (self, data):
		if (self.cleanSmartQuotes):
			data = data.replace (u'\u201c', '"')
			data = data.replace (u'\u201d', '"')
		if (self.cleanHyphens):
			data = data.replace (u'\u2013', '-')
		self.charData.append (data)
		
	def getMetaInfo (self):
		self.metaData ['keywords'] = self.keywords
		return self.metaData

class StyleHandler:
	def __init__ (self, config):
		self.log = logging.getLogger ("PubTal.OOC.StyleHandler")
		self.textStyleMap = {}
		self.paragraphStyleMap = {}
		
		self.currentStyleFamily = None
		self.currentStyle = None
		
	def startElementNS (self, name, qname, atts):
		realName = name [1]
		if (realName == 'style'):
			try:
				self.currentStyle = {}
				self.currentStyle ['name'] = atts [(STYLE_URI, 'name')]
				self.currentStyleFamily = atts [(STYLE_URI, 'family')]
				self.currentStyle ['parent-name'] = atts.get ((STYLE_URI, 'parent-style-name'), None)
			except Exception, e:
				msg = "Error parsing style information.  Error: " + str (e)
				self.log.error (msg)
				raise OpenOfficeFormatException (msg)
		if (realName == 'properties' and self.currentStyle is not None):
			for uri, attName in atts.keys():
				if (uri == FORMAT_URI):
					if SUPPORTED_FO_STYLES.has_key (attName): 
						attValue = atts [(FORMAT_URI, attName)]
						self.currentStyle [attName] = attValue
				if (uri == STYLE_URI):
					attValue = atts [(STYLE_URI, attName)]
					if (attValue != 'none'):
						if (attName == 'text-underline'):
							self.currentStyle ['underline'] = 'underline'
						if (attName == 'text-crossing-out'):
							self.currentStyle ['line-through'] = 'line-through'
						if (attName == 'text-position'):
							actualPosition = attValue [0:attValue.find (' ')]
							self.currentStyle ['vertical-align'] = actualPosition
		
	def endElementNS (self, name, qname):
		if (name[1] == 'style'):
			if (self.currentStyle is not None):
				name = self.currentStyle ['name']
				if (self.currentStyleFamily == "paragraph"):
					self.log.debug ("Recording paragraph style %s" % name)
					self.paragraphStyleMap [name] = self.currentStyle
				elif (self.currentStyleFamily == "text"):
					self.log.debug ("Recording text style %s" % name)
					self.textStyleMap [name] = self.currentStyle
				else:
					self.log.debug ("Unsupported style family %s" % self.currentStyleFamily)
				self.currentStyle = None
				self.currentStyleFamily = None
	
	def characters (self, data):
		pass
		
	def getTextStyle (self, name):
		return self.styleLookup (name, self.textStyleMap)
			
		return foundStyle
		
	def getParagraphStyle (self, name):
		return self.styleLookup (name, self.paragraphStyleMap)
		
	def styleLookup (self, name, map):
		foundStyle = {}
		styleHierachy = []
		lookupName = name
		while (lookupName is not None):
			lookupStyle = map.get (lookupName, None)
			if (lookupStyle is not None):
				styleHierachy.append (lookupStyle)
				lookupName = lookupStyle ['parent-name']
			else:
				self.log.debug ("Style %s not found!" % lookupName)
				lookupName = None
		styleHierachy.reverse()
		for style in styleHierachy:
			foundStyle.update (style)
			
		return foundStyle

class TextHandler:
	def __init__ (self, styleHandler, config):
		self.log = logging.getLogger ("PubTal.OOC.TextHandler")
		
		self.styleHandler = styleHandler
		# Check for the kind of output we are generating
		outputType = config.get ('output-type', 'HTML')
		
		self.outputPlainText = 0
		if (outputType == 'HTML'):
			self.outputXHTML = 0
		elif (outputType == 'XHTML'):
			self.outputXHTML = 1
		elif (outputType == 'PlainText'):
			# Plain text trumps outputXHTML
			self.outputPlainText = 1
		else:
			msg = "Attempt to configure for unsupported output-type %s. " + outputType
			self.log.error (msg)
			raise OpenOfficeFormatException (msg)
			
		if (self.outputPlainText):
			# We do not preserve spaces with &nbsp; because our output is not space clean.
			self.result = HTMLWriter.PlainTextWriter(outputStream=StringIO.StringIO(), outputXHTML=1, preserveSpaces = 0)
		else:
			self.result = HTMLWriter.HTMLWriter(outputStream=StringIO.StringIO(), outputXHTML=self.outputXHTML, preserveSpaces = 0)
		# We use this stack to re-direct output into footnotes.
		self.resultStack = []
		
		# We treat footnotes and endnotes the same.
		self.footNoteID = None
		self.footnotes = []
		
		self.charData = []
		# The closeTagsStack holds one entry per open OO text tag.
		# Those that have corresponding HTML tags have text, everything else has None
		self.closeTagsStack = []
		# The effectiveStyleStack holds the effective style (e.g. paragraph) and is used to filter out
		# un-needed style changes.
		self.effectiveStyleStack = [DEFAULT_PARAGRAPH_STYLES]
			
		self.cleanSmartQuotes = config.get ('CleanSmartQuotes', 0)
		self.cleanHyphens = config.get ('CleanHyphens', 0)
		self.preserveSpaces = config.get ('preserveSpaces', 1)
		
	def startElementNS (self, name, qname, atts):
		#self.log.debug ("Start: %s" % name[1])
		realName = name [1]
		styleName = atts.get ((TEXT_URI, 'style-name'), None)
		if (realName == 'h'):
			self.charData = []
			# We have a heading - get the level and style.
			try:
				headingLevel = int (atts [(TEXT_URI, 'level')])
				applicableStyle = self.styleHandler.getParagraphStyle (styleName)
				if (headingLevel > 6):
					self.log.warn ("Heading level of %s used, but HTML only supports up to level 6." % str (headingLevel))
					headingLevel = 6
				self.result.startElement ('h%s' % str (headingLevel), self.getCSSStyle (applicableStyle, HEADING_STYLE_FILTER))
				self.closeTagsStack.append ('h%s' % str (headingLevel))
			except Exception, e:
				msg = "Error parsing heading.  Error: " + str (e)
				self.log.error (msg)
				raise OpenOfficeFormatException (msg)
		elif (realName == 'p'):
			# We have a paragraph
			self.charData = []
			applicableStyle = self.styleHandler.getParagraphStyle (styleName)
			if (styleName == "Preformatted Text"):
				# We have PRE text
				self.result.startElement ('pre', self.getCSSStyle (applicableStyle, PARAGRAPH_STYLE_FILTER))
				self.closeTagsStack.append ('pre')
			elif (styleName == "Quotations"):
				# We have a block qutoe.
				self.result.startElement ('blockquote')
				self.result.startElement ('p',  self.getCSSStyle (applicableStyle, PARAGRAPH_STYLE_FILTER))
				self.closeTagsStack.append (['p', 'blockquote'])
			else:
				self.result.startElement ('p', self.getCSSStyle (applicableStyle, PARAGRAPH_STYLE_FILTER))
				self.closeTagsStack.append ('p')
			# Footnotes can start with either paragraphs or lists.
			if (self.footNoteID is not None):
				self.result.startElement ('a', ' name="%s" style="vertical-align: super" href="#src%s"'% (self.footNoteID, self.footNoteID))
				self.result.write (str (len (self.footnotes) + 1))
				self.result.endElement ('a')
				self.footNoteID = None
		elif (realName == 'ordered-list'):
			self.charData = []
			applicableStyle = self.styleHandler.getParagraphStyle (styleName)
			self.result.startElement ('ol', self.getCSSStyle (applicableStyle, PARAGRAPH_STYLE_FILTER))
			self.closeTagsStack.append ('ol')
			# Footnotes can start with either paragraphs or lists.
			if (self.footNoteID is not None):
				self.result.startElement ('a', ' name="%s" style="vertical-align: super" href="#src%s"'% (self.footNoteID, self.footNoteID))
				self.result.write (str (len (self.footnotes) + 1))
				self.result.endElement ('a')
				self.footNoteID = None
		elif (realName == 'unordered-list'):
			self.charData = []
			applicableStyle = self.styleHandler.getParagraphStyle (styleName)
			self.result.startElement ('ul', self.getCSSStyle (applicableStyle, PARAGRAPH_STYLE_FILTER))
			self.closeTagsStack.append ('ul')
			# Footnotes can start with either paragraphs or lists.
			if (self.footNoteID is not None):
				self.result.startElement ('a', ' name="%s" style="vertical-align: super" href="#src%s"'% (self.footNoteID, self.footNoteID))
				self.result.write (str (len (self.footnotes) + 1))
				self.result.endElement ('a')
				self.footNoteID = None
		elif (realName == 'list-item'):
			applicableStyle = self.styleHandler.getTextStyle (styleName)
			self.result.startElement ('li', self.getCSSStyle (applicableStyle, SPAN_STYLE_FILTER))
			self.closeTagsStack.append ('li')
		elif (realName == 'span'):
			# We have some text formatting - write out any data already accumulated.
			self.writeData()
			applicableStyle = self.styleHandler.getTextStyle (styleName)
			if (styleName == "Source Text"):
				# We have PRE text
				self.result.startElement ('code', self.getCSSStyle (applicableStyle, SPAN_STYLE_FILTER))
				self.closeTagsStack.append ('code')
			else:
				cssStyle = self.getCSSStyle (applicableStyle, SPAN_STYLE_FILTER)
				if (len (cssStyle) > 0):
					self.result.startElement ('span', cssStyle)
					self.closeTagsStack.append ('span')
				else:
					#self.log.debug ("Suppressing span - no change in style.")
					self.closeTagsStack.append (None)
		elif (realName == 'a'):
			self.writeData()
			linkDest = atts.get ((XLINK_URI, 'href'), None)
			if (linkDest is not None):
				self.result.startElement ('a', ' href="%s"' % linkDest)
				self.closeTagsStack.append ('a')
			else:
				self.closeTagsStack.append (None)
			# Links are underlined - we want this done by the style sheet, so ignore the underline.
			newEffectiveStyle = {}
			newEffectiveStyle.update (self.effectiveStyleStack[-1])
			newEffectiveStyle ['underline'] = 'underline'
			self.effectiveStyleStack.append (newEffectiveStyle)
		elif (realName == 'footnote' or realName == 'endnote'):
			try:
				footnoteID = atts[(TEXT_URI, 'id')]
			except Exception, e:
				msg = "Error getting footnoteid.  Error: " + str (e)
				self.log.error (msg)
				raise OpenOfficeFormatException (msg)
				
			# Write out any data we have currently stored.
			self.writeData()
			
			# Now write out the link to the footnote
			self.result.startElement ('a', ' name="src%s" style="vertical-align: super" href="#%s"' % (footnoteID, footnoteID))
			self.result.write (str (len (self.footnotes) + 1))
			self.result.endElement ('a')
			self.resultStack.append (self.result)
			if (self.outputPlainText):
				self.result = HTMLWriter.PlainTextWriter (outputStream = StringIO.StringIO(), outputXHTML=1, preserveSpaces = 0)
			else:
				self.result = HTMLWriter.HTMLWriter(outputStream = StringIO.StringIO(), outputXHTML=self.outputXHTML, preserveSpaces = 0)
			self.closeTagsStack.append (None)
			# Re-set the style stack for the footenote
			self.effectiveStyleStack.append (DEFAULT_PARAGRAPH_STYLES)
			# Keep this foonote id around for the first paragraph.
			self.footNoteID = footnoteID
		elif (realName == 'footnote-body' or realName == 'endnote-body'):
			self.closeTagsStack.append (None)
			# Keep the effective style as-is
			self.effectiveStyleStack.append (self.effectiveStyleStack[-1])
		elif (realName == 'bookmark-start' or realName == 'bookmark'):
			try:
				bookmarkName = atts[(TEXT_URI, 'name')]
			except Exception, e:
				msg = "Error getting bookmark name.  Error: " + str (e)
				self.log.error (msg)
				raise OpenOfficeFormatException (msg)
			self.writeData()
			self.result.startElement ('a', ' name="%s"' % bookmarkName)
			self.closeTagsStack.append ('a')
			# Keep the effective style as-is
			self.effectiveStyleStack.append (self.effectiveStyleStack[-1])
		elif (realName == 'line-break'):
			self.writeData()
			self.result.lineBreak()
			self.closeTagsStack.append (None)
			# Keep the effective style as-is
			self.effectiveStyleStack.append (self.effectiveStyleStack[-1])
		elif (realName == 's'):
			# An extra space or two
			# Remove the leading space if possible so that we can output '&nbsp; ' instead of ' &nbsp;'
			removedSpace = 0
			if (len (self.charData) > 0):
				if (self.charData [-1][-1] == u" "):
					self.charData [-1] = self.charData [-1][:-1]
					removedSpace = 1
				
			self.writeData()
			count = int (atts.get ((TEXT_URI, 'c'), 1))
			if (self.preserveSpaces):
				for spaces in xrange (count):
					self.result.nonbreakingSpace()
			if (removedSpace):
				# Add it back now
				self.charData.append (u" ")
			# Keep the effective style as-is, and ignore the close element
			self.effectiveStyleStack.append (self.effectiveStyleStack[-1])
			self.closeTagsStack.append (None)
		else:
			# We have no HTML output associated with this OO tag.
			self.closeTagsStack.append (None)
			# Keep the effective style as-is
			self.effectiveStyleStack.append (self.effectiveStyleStack[-1])
		
	def endElementNS (self, name, qname):
		if (len (self.closeTagsStack) > 0):
			htmlTag = self.closeTagsStack.pop()
			if (htmlTag is not None):
				self.writeData()
				if (type (htmlTag) == type ([])):
					for a in htmlTag:
						self.result.endElement (a)
				else:
					self.result.endElement (htmlTag)
		# Remove this effective style.
		self.effectiveStyleStack.pop()
		
		if (name[1] == 'footnote' or name[1] == 'endnote'):
			# We have just closed a footnote or endnote - record the result, pop the stack.
			outputFile = self.result.getOutput()
			self.footnotes.append (outputFile.getvalue())
			outputFile.close()
			self.result = self.resultStack.pop()
	
	def characters (self, data):
		if (self.cleanSmartQuotes):
			data = data.replace (u'\u201c', '"')
			data = data.replace (u'\u201d', '"')
		if (self.cleanHyphens):
			data = data.replace (u'\u2013', '-')
		self.charData.append (data)
		
	def writeData (self):
		data = u"".join (self.charData)
		self.result.write (cgi.escape (data))
		self.charData = []
		
	def getCSSStyle (self, applicableStyle, styleList):
		#self.log.debug ("Filtering styles %s for styles %s" % (str (applicableStyle), str (styleList)))
		textDecoration = []
		cssStyles = []
		# Take a look at the effective styles.
		effectiveStyles = self.effectiveStyleStack [-1]
		# Store the new effective style for future comparison
		newEffectiveStyle = {}
		newEffectiveStyle.update (effectiveStyles)
		
		for style in styleList:
			if (applicableStyle.has_key (style)):
				if (style in ["underline", "line-through", "overline"]):
					if (not effectiveStyles.has_key (style)):
						textDecoration.append (style)
				else:
					# We check to see whether the effective style already has this value
					# I.e. handle paragraph of font-style=normal and span of font-style=normal
					styleValue = applicableStyle [style]
					if (effectiveStyles.has_key (style)):
						if (effectiveStyles[style] != styleValue):
							cssStyles.append (u"%s:%s" % (style, styleValue))
						else:
							#self.log.debug ("Style %s already in effect with value %s" % (style, styleValue))
							pass
					else:
						cssStyles.append (u"%s:%s" % (style, styleValue))
					# Note this new effective style
					newEffectiveStyle [style] = styleValue
		if (len (textDecoration) > 0):
			cssStyles.append (u"text-decoration: %s" % u",".join (textDecoration))
		
		#self.log.debug ("Adding real effective style (%s) to stack." % str (newEffectiveStyle))
		self.effectiveStyleStack.append (newEffectiveStyle)
		
		cssStyleList = ";".join (cssStyles)
		if (len (cssStyleList) > 0):
			return ' style="%s"' % cssStyleList
		return ''
		
	def getContent (self):
		return self.result.getOutput().getvalue()
		
	def getFootNotes (self):
		return self.footnotes
		
class DrawHandler:
	def __init__ (self, styleHandler, textHandler, config):
		self.log = logging.getLogger ("PubTal.OOC.DrawHandler")
		
		self.styleHandler = styleHandler
		self.result = textHandler.result
		self.textHandler = textHandler
		
		self.charData = []
		
		# The effectiveStyleStack holds the effective style (e.g. paragraph) and is used to filter out
		# un-needed style changes.
		self.effectiveStyleStack = [DEFAULT_PARAGRAPH_STYLES]
		self.closeTagsStack = []
		self.bundledPictureList = []
		
		self.currentImage = None
		
		# Check for the kind of output we are generating
		self.cleanSmartQuotes = config.get ('CleanSmartQuotes', 0)
		self.cleanHyphens = config.get ('CleanHyphens', 0)
		self.picturePrefix = os.path.join ('Pictures', config.get ('DestinationFile', '').replace ('.', '_'))
		self.log.debug ("Determined picture prefix as %s" % self.picturePrefix)
		
	def getBundledPictures (self):
		return self.bundledPictureList
		
	def startElementNS (self, name, qname, atts):
		theURI = name [0]
		realName = name [1]
		if (theURI == DRAW_URI):
			if (realName == 'image'):
				styleName = atts.get ((DRAW_URI, 'style-name'), None)
				href = atts.get ((XLINK_URI, 'href'), None)
				if (href is None):
					self.log.warn ("No href attribute found for image!")
					self.closeTagsStack = None
					return
				# Deal with bundled pictures
				if (href.startswith ('#Pictures/')):
					self.log.debug ("Found bundled picture %s" % href)
					archivePicName = href [1:]
					href = self.picturePrefix + archivePicName[9:]
					self.bundledPictureList.append ((archivePicName, href))
				alt = atts.get ((DRAW_URI, 'name'), None)
				self.currentImage = {'href': href, 'alt': alt}
				self.closeTagsStack.append (None)
			elif (realName == 'a'):
				linkDest = atts.get ((XLINK_URI, 'href'), None)
				if (linkDest is not None):
					self.textHandler.writeData()
					self.result.startElement ('a', ' href="%s"' % linkDest)
					self.closeTagsStack.append ('a')
				else:
					self.closeTagsStack.append (None)
		elif (theURI == SVG_URI):
			if (realName == 'desc'):
				self.charData = []
				self.closeTagsStack.append (None)
		else:
			self.closeTagsStack.append (None)
		
	def endElementNS (self, name, qname):
		if (len (self.closeTagsStack) > 0):
			htmlTag = self.closeTagsStack.pop()
			if (htmlTag is not None):
				self.result.endElement (htmlTag)
		# Remove this effective style.
		#self.effectiveStyleStack.pop()
		
		theURI = name [0]
		realName = name [1]
		if (theURI == SVG_URI):
			if (realName == 'desc'):
				# We have an image description - note it!
				altText = cgi.escape (u"".join (self.charData))
				self.charData = []
				if (self.currentImage is not None):
					self.currentImage ['alt'] = altText
		elif (theURI == DRAW_URI):
			if (realName == 'image'):
				self.textHandler.writeData()
				self.result.startElement ('img', ' src="%s" alt="%s"' % (self.currentImage ['href'], self.currentImage ['alt']))
				self.result.endElement ('img')
				self.currentImage = None
	
	def characters (self, data):
		if (self.cleanSmartQuotes):
			data = data.replace (u'\u201c', '"')
			data = data.replace (u'\u201d', '"')
		if (self.cleanHyphens):
			data = data.replace (u'\u2013', '-')
		self.charData.append (data)
		
class TableHandler:
	def __init__ (self, styleHandler, resultWriter, config):
		self.log = logging.getLogger ("PubTal.OOC.TextHandler")
		self.styleHandler = styleHandler
		self.result = resultWriter
		self.closeTagsStack = []
		self.tableStatusStack = []
	
	def startElementNS (self, name, qname, atts):
		#self.log.debug ("Start: %s" % name[1])
		realName = name [1]
		styleName = atts.get ((TABLE_URI, 'style-name'), None)
		if (realName == 'table' or realName == 'sub-table'):
			self.result.startElement ('table')
			self.closeTagsStack.append ('table')
			self.tableStatusStack.append ({'inHeader':0, 'firstRow': 1})
		elif (realName == 'table-header-rows'):
			status = self.tableStatusStack [-1]
			status ['inHeader'] = 1
			self.result.startElement ('thead')
			self.closeTagsStack.append ('thead')
		elif (realName == 'table-row'):
			status = self.tableStatusStack [-1]
			if ((not status ['inHeader']) and (status ['firstRow'])):
				status ['firstRow'] = 0
				self.result.startElement ('tbody')
			self.result.startElement ('tr')
			self.closeTagsStack.append ('tr')
		elif (realName == 'table-cell'):
			status = self.tableStatusStack [-1]
			colSpan = int (atts.get ((TABLE_URI, 'number-columns-spanned'), 0))
			if (colSpan != 0):
				colSpanTxt = ' colspan="%s"' % str (colSpan)
			else:
				colSpanTxt = ''
			if (status ['inHeader']):
				self.result.startElement ('th', colSpanTxt)
				self.closeTagsStack.append ('th')
			else:
				self.result.startElement ('td', colSpanTxt)
				self.closeTagsStack.append ('td')
		else:
			self.closeTagsStack.append (None)
			
	
	def endElementNS (self, name, qname):
		realName = name [1]
		# We check for table because we want to insert tbody close before table close.
		if (len (self.tableStatusStack) > 0):
			status = self.tableStatusStack [-1]

		if (realName == 'table' or realName == 'sub-table'):
			if (not status ['firstRow']):
				# The table actually had content.
				self.result.endElement ('tbody')
				
		if (len (self.closeTagsStack) > 0):
			htmlTag = self.closeTagsStack.pop()
			if (htmlTag is not None):
				self.result.endElement (htmlTag)
				
		# We check for table header rows here.
		if (realName == 'table-header-rows'):
			status ['inHeader'] = 0
			
		if (realName == 'table'):
			# Pop this table status off the stack
			self.tableStatusStack.pop()
				
	def characters (self, data):
		pass

class OpenOfficeFormatException (Exception):
	pass

