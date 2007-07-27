""" Classes to convert entered content into HTML

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
"""

import os, sgmllib, StringIO, cgi, re, codecs
import xml.sax

try:
	import logging
except:
	import InfoLogging as logging
	
import HTMLWriter
	
# Used to spot already escaped attributes in HTMLText
ESCAPED_TEXT_REGEX=re.compile (r"\&\S+?;")

# Used to determine how much of the resulting output should be shown:
MAX_CONTEXT=200

class ContentParseException (Exception):
	def __init__ (self, msg):
		self.msg = msg

	def __str__ (self):
		return self.msg
		
class BaseContentConverter:
	def handleAccumulatedData (self, openingNewBlock=0, docEnded=0):
		data = u"".join (self.characterData)
		if (docEnded):
			if (len (data.strip()) == 0):
				# We do nothing - it's the last thing!
				return
		# We are not in a block, so let's do the paragraph thing.
		paraData = data.split ('\n\n')
		paraCount = len (paraData) - 1
		for para in paraData:
			# We have something useful in this paragraph data.
			lines = para.split ('\n')
			# Loop over *all* lines.
			lineCount = len (lines) - 1
			for line in lines:
				# Check to see whether we have already written data.
				if (self.currentParagraph.getDataLength() > 0):
					# Yes, see whether we wanted to write a newline.
					if (self.writeNewLine):
						# Special case: When we are about to open a new block level item and we are on the last
						# paragraph and last line, we don't want a newline!
						if (openingNewBlock == 1 and paraCount == 0 and lineCount == 0):
							self.log.debug ("Suppressing new line for last bit!")
						else:
							if (not self.ignoreNewLines):
								self.currentParagraph.lineBreak ()
							else:
								self.currentParagraph.write ('\n')
					# We've done this request now.
					self.writeNewLine = 0
				self.currentParagraph.write (line)
				# We want a newline next...
				self.writeNewLine = 1
				lineCount -= 1
			# We have finished paragraph, so clear the new line flag
			self.writeNewLine = 0
			if (paraCount > 0):
				# We have another paragraph coming, so close this one.
				self.closeParagraph()
			paraCount -= 1
		self.characterData = []
		
	def closeParagraph (self):
		self.currentParagraph.endElement ('p')
		outputStream = self.currentParagraph.getOutput()
		asData = outputStream.getvalue()
		outputStream.close()
		withNoPTags = asData [3:-5]
		if (len (withNoPTags.strip()) > 0):
			# There is actual, useful, content in this paragraph.
			self.result.write (asData)
		# Prepare a new paragraph for the future.
		if (self.plainTextOuput):
			self.currentParagraph = HTMLWriter.PlainTextWriter (outputStream = StringIO.StringIO(), outputXHTML=self.outputXHTML, preserveSpaces = self.preserveSpaces, exceptionOnError=1)
		else:
			self.currentParagraph = HTMLWriter.HTMLWriter (outputStream = StringIO.StringIO(), outputXHTML=self.outputXHTML, preserveSpaces = self.preserveSpaces, exceptionOnError=1)
		self.currentParagraph.startElement ('p')
		

class ContentToXHTMLConverter (xml.sax.handler.ContentHandler, xml.sax.handler.DTDHandler, xml.sax.handler.ErrorHandler, BaseContentConverter):
	""" Convert entered markup into XHTML1.  Paragraph and line break elements are added to
		the content, taking into consideration any block level markup that might have 
		been entered by the user.
	"""
	def __init__ (self):
		xml.sax.handler.ContentHandler.__init__ (self)
		self.log = logging.getLogger ("PubTal.ContentToXHTMLConverter")
		self.outputXHTML = 1
		# Use utf-8 instead of utf-16 internally because the Python SAX implementation is
		# a bit broken, and doesn't understand U+feff and keeps it when sending it to the SAX handler
		self.utf8Encoder = codecs.lookup ("utf-8")[0]
		self.SPECIAL_START_TAG = self.utf8Encoder (u'<?xml version="1.0" encoding="utf-8"?>\n<XMLCONTENTTYPESPECIALTAG>')[0]
		self.SPECIAL_END_TAG = self.utf8Encoder (u'</XMLCONTENTTYPESPECIALTAG>')[0]
		
	def convertContent (self, content, ignoreNewLines=0, preserveSpaces=1, plainTextOuput=0):
		self.ignoreNewLines = ignoreNewLines
		self.preserveSpaces = preserveSpaces
		# This is how deep the non-paragraph tags have reached.
		self.depthOfTags = 0
		self.writeNewLine = 0
		self.characterData = []
		self.plainTextOuput = plainTextOuput
		if (plainTextOuput):
			self.result = HTMLWriter.PlainTextWriter (outputStream = StringIO.StringIO(), outputXHTML=1, exceptionOnError=1)
			self.currentParagraph = HTMLWriter.PlainTextWriter (outputStream = StringIO.StringIO(), outputXHTML=1, exceptionOnError=1)
		else:
			self.result = HTMLWriter.HTMLWriter (outputStream = StringIO.StringIO(), outputXHTML=1, preserveSpaces = self.preserveSpaces, exceptionOnError=1)
			self.currentParagraph = HTMLWriter.HTMLWriter (outputStream = StringIO.StringIO(), outputXHTML=1, preserveSpaces = self.preserveSpaces,  exceptionOnError=1)
		self.currentParagraph.startElement ('p')
		
		self.ourParser = xml.sax.make_parser()
		self.log.debug ("Setting features of parser")
		self.ourParser.setFeature (xml.sax.handler.feature_external_ges, 0)

		self.ourParser.setContentHandler (self)
		self.ourParser.setErrorHandler (self)
		
		file = StringIO.StringIO (self.SPECIAL_START_TAG + self.utf8Encoder (content)[0] + self.SPECIAL_END_TAG)
		
		# Parse the content as XML
		try:
			self.ourParser.parse (file)
		except Exception, e:
			self.log.error ("Error parsing input: " + str (e))
			raise
		
		# Handle any accumulated character data 
		if len (self.characterData) > 0:
			self.handleAccumulatedData(docEnded=1)
		
		# See if there is anything not yet written out
		self.closeParagraph()
		
		resultFile = self.result.getOutput()
		data = resultFile.getvalue()
		resultFile.close()
		return data

	def startElement (self, origtag, attributes):
		#self.log.debug ("Recieved Real Start Tag: " + origtag + " Attributes: " + str (attributes))
		tag = origtag.lower()
		# Convert attributes into a list of tuples
		atts = []
		for att in attributes.getNames():
			self.log.debug ("Attribute name %s has value %s" % (att, attributes[att]))
			atts.append (' ')
			atts.append (att)
			atts.append ('="')
			atts.append (cgi.escape (attributes[att], quote=1))
			atts.append ('"')
		atts = u"".join (atts)
		
		if (origtag != u"XMLCONTENTTYPESPECIALTAG"):
			if (self.depthOfTags > 0):
				# We are simply writing this out
				self.depthOfTags += 1
				try:
					self.result.startElement (tag, atts)
				except HTMLWriter.TagNotAllowedException, tagErr:
					curResult = self.result.getOutput().getvalue()
					if (len (curResult) > MAX_CONTEXT):
						curResult = "...%s" % curResult [-MAX_CONTEXT:]
					msg = "Element <%s%s> is not allowed in current location: %s" % (tag, atts, curResult)
					self.log.error (msg)
					raise ContentParseException (msg)
			else:
				# We are currently writing to a paragraph.  Can this continue?
				# Find out whether this tag can go in a paragraph.
				if (self.currentParagraph.isElementAllowed (tag)):
					self.log.debug ("Element %s found to be allowed." % str (tag))
					# We can keep going.
					# Handle any accumulated character data 
					if len (self.characterData) > 0:
						self.handleAccumulatedData()
					self.currentParagraph.startElement (tag, atts)
				else:
					self.log.debug ("Element %s not allowed, closing paragraph." % str (tag))
					# Handle any accumulated character data 
					if len (self.characterData) > 0:
						self.handleAccumulatedData(openingNewBlock=1)
				
					# We aren't allowed this element in a paragraph.
					# We have to assume that the user knows it can go into the template as-is.
					# First we check that there aren't any tags left open that need to be closed...
					paraStack = self.currentParagraph.getCurrentElementStack()
					if (len (paraStack) > 1):
						paraResult = self.currentParagraph.getOutput().getvalue()
						if (len (paraResult) > MAX_CONTEXT):
							paraResult = "...%s" % paraResult [-MAX_CONTEXT:]
						msg = "Element <%s%s> is not allowed in current location: %s" % (tag, atts, paraResult)
						self.log.error (msg)
						raise ContentParseException (msg)
					
					# Write out the current paragraph, and then pass this on directly to the output
					self.closeParagraph()
					# Now write this out...
					self.depthOfTags += 1
					self.result.startElement (tag, atts)
	
	def endElement (self, tag):
		#self.log.debug ("Recieved Real End Tag: " + tag)
		if (tag != u"XMLCONTENTTYPESPECIALTAG"):
			tag = tag.lower()
			# Handle any accumulated character data 
			if len (self.characterData) > 0:
				self.handleAccumulatedData()
				
			if (self.depthOfTags > 0):
				# This doesn't belong to a paragraph
				self.result.endElement (tag)
				self.depthOfTags -= 1
			else:
				# This is destined for a paragraph
				self.currentParagraph.endElement (tag)
	
	def fatalError (self, msg):
		self.error (msg)
		
	def error (self, msg):
		if (self.depthOfTags > 0):
			# Error occured in the main document.
			curResult = self.result.getOutput().getvalue()
			if (len (curResult) > MAX_CONTEXT):
				curResult = "...%s" % curResult [-MAX_CONTEXT:]
			msg = "Error %s occured shortly after: %s" % (msg, curResult)
			self.log.error (msg)
			raise ContentParseException (msg)
		else:
			# Flush out any remaining data so that our error message is more complete.
			if len (self.characterData) > 0:
				self.handleAccumulatedData()
			curResult = self.currentParagraph.getOutput().getvalue()
			if (len (curResult) > MAX_CONTEXT):
				curResult = "...%s" % curResult [-MAX_CONTEXT:]
			msg = "Error %s occured shortly after: %s" % (msg, curResult)
			self.log.error (msg)
			raise ContentParseException (msg)
		
	def characters (self, data):
		if (self.depthOfTags > 0):
			# We are in a block, so just output
			self.result.write (cgi.escape (data))
			return
		
		# Accumulate the character data together so that we can merge all the newline events
		self.characterData.append (cgi.escape (data))
		

class ContentToHTMLConverter (sgmllib.SGMLParser, BaseContentConverter):
	""" Convert entered markup into HTML.  Paragraph and line break elements are added to
		the content, taking into consideration any block level markup that might have 
		been entered by the user.
		
	""" 
	def __init__ (self):
		self.outputXHTML = 0
		self.log = logging.getLogger ("PubTal.HTMLText.ContentToHTMLConverter")
		sgmllib.SGMLParser.__init__ (self)
		
	def convertContent (self, content, ignoreNewLines=0, preserveSpaces = 1, plainTextOuput=0):
		self.ignoreNewLines = ignoreNewLines
		self.preserveSpaces = preserveSpaces
		# This is how deep the non-paragraph tags have reached.
		self.depthOfTags = 0
		self.writeNewLine = 0
		self.characterData = []
		self.plainTextOuput = plainTextOuput
		if (plainTextOuput):
			self.result = HTMLWriter.PlainTextWriter (outputStream = StringIO.StringIO(), outputXHTML=0, exceptionOnError=1)
			self.currentParagraph = HTMLWriter.PlainTextWriter (outputStream = StringIO.StringIO(), outputXHTML=0, exceptionOnError=1)
		else:
			self.result = HTMLWriter.HTMLWriter (outputStream = StringIO.StringIO(), outputXHTML=0, preserveSpaces = self.preserveSpaces, exceptionOnError=1)
			self.currentParagraph = HTMLWriter.HTMLWriter (outputStream = StringIO.StringIO(), outputXHTML=0, preserveSpaces = self.preserveSpaces, exceptionOnError=1)
		self.currentParagraph.startElement ('p')
		
		self.feed (content.strip())

		# Handle any accumulated character data 
		if len (self.characterData) > 0:
			self.handleAccumulatedData(docEnded=1)
		
		# See if there is anything not yet written out
		self.closeParagraph()
		
		resultFile = self.result.getOutput()
		data = resultFile.getvalue()
		resultFile.close()
		return data

	def unknown_starttag (self, origtag, attributes):
		attStack = []
		for name, value in attributes:		
			attStack.append (' ')
			attStack.append (name)
			attStack.append ('="')
			if (ESCAPED_TEXT_REGEX.search (value) is not None):
				# We already have some escaped characters in here, so assume it's all valid
				attStack.append (value)
			else:
				attStack.append (cgi.escape (value))
			attStack.append ('"')
		atts = u"".join (attStack)
		
		tag = origtag.lower()
		
		self.log.debug ("Recieved start tag %s" % tag)		
		if (self.depthOfTags > 0):
			# We are simply writing this out
			# Are we expecting an end tag?
			if (not self.result.isEndTagForbidden (tag)):
				# Yes, we'll count it 
				self.depthOfTags += 1
			try:
				self.result.startElement (tag, atts)
			except HTMLWriter.TagNotAllowedException, tagErr:
				curResult = self.result.getOutput().getvalue()
				if (len (curResult) > MAX_CONTEXT):
					curResult = "...%s" % curResult [-MAX_CONTEXT:]
				msg = "Element <%s%s> is not allowed in current location: %s" % (tag, atts, curResult)
				self.log.error (msg)
				raise ContentParseException (msg)
		else:
			# We are currently writing to a paragraph.  Can this continue?
			# Find out whether this tag can go in a paragraph.
			if (self.currentParagraph.isElementAllowed (tag)):
				self.log.debug ("Element %s found to be allowed." % str (tag))
				# We can keep going.
				# Handle any accumulated character data 
				if len (self.characterData) > 0:
					self.handleAccumulatedData()
				self.currentParagraph.startElement (tag, atts)
			else:
				self.log.debug ("Element %s not allowed, closing paragraph." % str (tag))
				# Handle any accumulated character data 
				if len (self.characterData) > 0:
					self.handleAccumulatedData(openingNewBlock=1)
				# We aren't allowed this element in a paragraph.
				# We have to assume that the user knows it can go into the template as-is.
				# First we check that there aren't any tags left open that need to be closed...
				paraStack = self.currentParagraph.getCurrentElementStack()
				if (len (paraStack) > 1):
					paraResult = self.currentParagraph.getOutput().getvalue()
					if (len (paraResult) > MAX_CONTEXT):
						paraResult = "...%s" % paraResult [-MAX_CONTEXT:]
					msg = "Element <%s%s> is not allowed in current location: %s" % (tag, atts, paraResult)
					self.log.error (msg)
					raise ContentParseException (msg)
						
				# Write out the current paragraph, and then pass this on directly to the output
				self.closeParagraph()
				# Now write this out...
				if (not self.result.isEndTagForbidden (tag)):
					# Yes, we'll count it 
					self.depthOfTags += 1
				self.result.startElement (tag, atts)

	def unknown_endtag (self, tag):
		tag = tag.lower()
		# Handle any accumulated character data 
		if len (self.characterData) > 0:
			self.handleAccumulatedData()
			
		if (self.depthOfTags > 0):
			# This doesn't belong to a paragraph
			try:
				self.result.endElement (tag)
			except HTMLWriter.BadCloseTagException, badTag:
				curResult = self.result.getOutput().getvalue()
				if (len (curResult) > MAX_CONTEXT):
					curResult = "...%s" % curResult [-MAX_CONTEXT:]
				msg = "End tag </%s> is not allowed in current location: %s" % (tag, curResult)
				self.log.error (msg)
				raise ContentParseException (msg)
			self.depthOfTags -= 1
		else:
			# This is destined for a paragraph
			try:
				self.currentParagraph.endElement (tag)
			except HTMLWriter.BadCloseTagException, badTag:
				curResult = self.currentParagraph.getOutput().getvalue()
				if (len (curResult) > MAX_CONTEXT):
					curResult = "...%s" % curResult [-MAX_CONTEXT:]
				msg = "End tag </%s> is not allowed in current location: %s" % (tag, curResult)
				self.log.error (msg)
				raise ContentParseException (msg)
	
	def handle_data (self, data):
		if (self.depthOfTags > 0):
			# We are in a block, so just output
			self.result.write (cgi.escape (data))
			return
		
		# Accumulate the character data together so that we can merge all the newline events
		self.characterData.append (cgi.escape (data))
		
	def handle_charref (self, ref):
		data = u'&#%s;' % ref
		if (self.depthOfTags > 0):
			# We are in a block, so just output
			self.result.write (data)
		else:
			# Write to the paragraph
			# We *don't* call cgi.escape because we already have it in encoded form.
			self.characterData.append (data)
		
	def handle_entityref (self, ref):
		data = u'&%s;' % ref
		if (self.depthOfTags > 0):
			# We are in a block, so just output
			self.result.write (data)
		else:
			# Write to the paragraph
			# We *don't* call cgi.escape because we already have it in encoded form.
			self.characterData.append (data)

	def report_unbalanced (self, tag):
			raise ContentParseException ("Recieved close tag '%s', but no corresponding open tag." % tag)
