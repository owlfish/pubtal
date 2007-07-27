import copy, StringIO, re

try:
	import logging
except:
	import InfoLogging as logging

import dtdcode

# HTML Class uses this to suppress end-tag output, XHTML class uses these to write singletons.
TAG_OPTIONAL=1
TAG_REQUIRED=0
TAG_FORBIDDEN=2

MLT_SPACE = re.compile ('  +')
NBSP_REF = "&nbsp;"

class TagNotAllowedException (Exception):
	def __init__ (self, tag, stack):
		stackMsg = []
		self.tag = tag
		for oldtag, atts in stack:
			stackMsg.append ("<%s%s>" % (oldtag, atts))
		stackMsg = " ".join (stackMsg)
		self.msg = "Tag %s not allowed here: %s" % (tag, stackMsg)
	
	def getTag (self):
		return self.tag
		
	def __str__ (self):
		return self.msg
		
class BadCloseTagException (Exception):
	def __init__ (self, tag, stack, expected=None):
		stackMsg = []
		self.tag = tag
		for oldtag, atts in stack:
			stackMsg.append ("<%s%s>" % (oldtag, atts))
		stackMsg = " ".join (stackMsg)
		if (expected is None):
			self.msg = "Close tag %s has no corresponding open tag.  (Elements currently open are: %s)" % (tag, stackMsg)
		else:
			self.msg = "Received close tag %s when expecting %s.  (Elements currently open are: %s)" % (tag, expected, stackMsg)
		
	def getTag (self):
		return self.tag
		
	def __str__ (self):
		return self.msg

		
class HTMLWriter:
	"""	The purpose of this class is to provide a simple way of writing valid HTML fragements.
		The class has enough logic to keep track of simple HTML rules (e.g. <p> elements
		can not be nested), and to silently correct when an attempt is made to write
		HTML that would break those rules.
		
		The class will not enforce rules such as <table> only having no more than
		one <thead> element.
		
		WARNING: All Start calls must be matched by End calls, this class will not magically
		nest elements correctly!
		
		outputStream   - File like object to write output to.
		outputXHTML    - Whether to generate XHTML or HTML tags.
		preserveSpaces - If true then &nbsp; will be inserted into the output as required.
		
	"""
	def __init__ (self, outputStream=None, outputXHTML=1, preserveSpaces = 1, exceptionOnError=0):
		if (outputStream is None):
			self.output = StringIO.StringIO()
		else:
			self.output = outputStream
		self.exceptionOnError = exceptionOnError
		self.log = logging.getLogger ("HTMLWriter")
		self.debugOn = self.log.isEnabledFor (logging.DEBUG)
		self.allowedElementsStack = []
		self.currentElementsStack = []
		self.currentText = []
		self.skipDepth = 0
		self.outputXHTML = outputXHTML
		self.preserveSpaces = preserveSpaces
		self.dataLength = 0
		self.log.debug ("XHTML Status :%s " % str (self.outputXHTML))
		if (self.outputXHTML):
			self.tagmap = dtdcode.XHTML_TAG_MAP
			self.blocklist = dtdcode.XHTML_BLOCK_LIST
			self.log.info ("Selected XHTML tag map.")
		else:
			self.tagmap = dtdcode.HTML_TAG_MAP
			self.blocklist = dtdcode.HTML_BLOCK_LIST
			self.log.info ("Selected HTML tag map.")
			
	def getOutput (self):
		self.flush()
		return self.output
		
	def startElement (self, elementName, attributes=""):
		if (self.skipDepth != 0):
			self.skipDepth += 1
			return
			
		if (not self.__checkAllowed__ (elementName)):
			self.skipDepth += 1
			self.log.warn ("Element %s not allowed." % elementName)
			if (self.log.isEnabledFor (logging.DEBUG)):
				self.log.debug ("Allowed stack follows:")
				for nest in self.allowedElementsStack:
					self.log.debug ("Elements %s allowed" % str (nest))
			if (self.exceptionOnError):
				raise TagNotAllowedException (elementName, self.currentElementsStack)
			return
		if (self.debugOn):
			self.log.debug ("Writing start element %s atts: %s" % (elementName, attributes))
		
		# Write out any pending data
		if (self.currentText): self.__outputText__()
		try:
			allowedTags, endTagPolicy = self.tagmap [elementName]
			# Only put the tag on the stacks if it *can* have an end tag.
			if (endTagPolicy != TAG_FORBIDDEN):
				self.allowedElementsStack.append (allowedTags)
				self.currentElementsStack.append ((elementName, attributes))
			
			if (self.outputXHTML and endTagPolicy == TAG_FORBIDDEN):
				self.output.write (u'<%s%s />' % (elementName, attributes))
			else:
				self.output.write (u'<%s%s>' % (elementName, attributes))
		except KeyError, e:
			msg = "HTML element %s is not supported!" % elementName
			self.log.warn (msg)
			if (self.exceptionOnError):
				raise msg
		
	def endElement (self, elementName):
		if (self.skipDepth != 0):
			self.log.warn ("End element %s is not allowed (start tag was suppressed)." % elementName)
			self.skipDepth -= 1
			return
		
		if (self.currentText): self.__outputText__()	
		# Ensure that this type of end element is allowed, if not then ignore it.
		allowedTags, endTagPolicy = self.tagmap [elementName]
		if (endTagPolicy == TAG_FORBIDDEN):
			self.log.debug ("End tag %s forbidden, skipping." % elementName)
			return
			
		if (len (self.currentElementsStack) == 0):
			raise BadCloseTagException (elementName, self.currentElementsStack)
			
		self.allowedElementsStack.pop()
		expectedElement = self.currentElementsStack.pop()[0]
		if (elementName != expectedElement):
			looking = 1
			while (looking):
				expectedElementTagPolicy = self.tagmap [expectedElement][1]
				self.log.debug ("Tag %s has policy %s" % (expectedElement, str (expectedElementTagPolicy)))
				# No end-tag-forbidden elements ever go on the stack, which means we have an un-closed tag!
				if (self.exceptionOnError):
					raise BadCloseTagException (elementName, self.currentElementsStack, expectedElement)
				self.log.warn ("Closing un-closed tag %s" % expectedElement)
				if (elementName in self.blocklist):
					self.output.write (u'</%s>\n' % expectedElement)
				else:
					self.output.write (u'</%s>' % expectedElement)
						
				if (len (self.currentElementsStack) > 0):
					self.allowedElementsStack.pop()
					expectedElement = self.currentElementsStack.pop()[0]
					if (expectedElement == elementName):
						looking = 0
				else:
					raise BadCloseTagException (elementName, self.currentElementsStack)
					
		if (self.debugOn):
			self.log.debug ("Writing end element %s" % elementName)
		if (elementName in self.blocklist):
			self.output.write (u'</%s>\n' % elementName)
		else:
			self.output.write (u'</%s>' % elementName)
				
	def write (self, data):
		if (self.skipDepth == 0):
			if (self.preserveSpaces):
				# Ensure that we are allowed to write text into this element.
				if (len (self.currentElementsStack) > 0):
					if (dtdcode.TEXT_ALLOWED_MAP.has_key (self.currentElementsStack [-1][0])):
						# We are allowed text, so feel free to do the &nbsp; thing.
						self.currentText.append (data)
					else:
						# We could just suppress this output, but it might include white space that is good for formatting.
						# Using a regex to validate that would allow for even more checking!
						self.output.write (data)
				else:
					# We have no open element, assume that this is OK.
					self.currentText.append (data)
			else:
				self.output.write (data)
			self.dataLength += len (data)
			
	def flush (self):
		""" Write out any cached data. """
		if (self.currentText): self.__outputText__()
			
	def lineBreak (self):
		if (not self.__checkAllowed__ ('br')):
			return
		if (self.currentText): self.__outputText__()
		if (self.outputXHTML):
			self.output.write (u'<br />\n')
		else:
			self.output.write (u'<br>\n')
			
	def nonbreakingSpace (self):
		if (self.skipDepth == 0):
			if (self.preserveSpaces):
				self.currentText.append (NBSP_REF)
			else:
				self.output.write (NBSP_REF)
			
	def getCurrentElementStack (self):
		return self.currentElementsStack
		
	def isElementAllowed (self, tagName):
		return self.__checkAllowed__ (tagName)
		
	def isEndTagForbidden (self, tagName):
		allowedTags, endTagPolicy = self.tagmap [tagName]
		if (endTagPolicy == TAG_FORBIDDEN):
			return 1
			
	def getDataLength (self):
		return self.dataLength
		
	def __outputText__ (self):
		# Get one big text string
		realText = "".join (self.currentText)
		# Determine whether there are any double spaces to escape.
		match = MLT_SPACE.search (realText)
		pos = 0
		while (match):
			# Output the current chunk of text
			start, end = match.start(), match.end()
			self.output.write (realText [pos:start])
			self.output.write (NBSP_REF*(end - start - 1) + " ")
			pos = end
			match = MLT_SPACE.search (realText, pos)
		self.output.write (realText [pos:])
		self.currentText = []
	
	def __checkAllowed__ (self, tagName):
		if (len (self.allowedElementsStack) == 0):
			return 1
			
		if tagName in self.allowedElementsStack[-1]:
			return 1
		return 0

class PlainTextWriter (HTMLWriter):
	""" This class works like the HTMLWriter class, except that it doesn't 
		output any markup.  This is useful when we need to produce output
		suitable for including in an RSS feed.
		
		The class still enforces correct nesting of elements so that callers
		can rely on this logic.
	"""
	def __init__ (self, outputStream=StringIO.StringIO(), outputXHTML=1, preserveSpaces=1, exceptionOnError=0):
		HTMLWriter.__init__ (self, outputStream, outputXHTML, preserveSpaces = 0, exceptionOnError = exceptionOnError)
		self.log = logging.getLogger ("PlainTextWriter")

	def startElement (self, elementName, attributes=""):
		if (self.skipDepth != 0):
			self.skipDepth += 1
			return
		
		if (not self.__checkAllowed__ (elementName)):
			self.skipDepth += 1
			self.log.warn ("Element %s not allowed." % elementName)
			if (self.log.isEnabledFor (logging.DEBUG)):
				self.log.debug ("Allowed stack follows:")
				for nest in self.allowedElementsStack:
					self.log.debug ("Elements %s allowed" % str (nest))
			if (self.exceptionOnError):
				raise TagNotAllowedException (elementName, self.currentElementsStack)
			return
		
		if (self.currentText): self.__outputText__()
		try:
			allowedTags, endTagPolicy = self.tagmap [elementName]
			# Only put the tag on the stacks if it *can* have an end tag.
			if (endTagPolicy != TAG_FORBIDDEN):
				self.allowedElementsStack.append (allowedTags)
				self.currentElementsStack.append ((elementName, attributes))
		except KeyError, e:
			msg = "HTML element %s is not supported!" % elementName
			self.log.warn (msg)
			if (self.exceptionOnError):
				raise msg
		
	def endElement (self, elementName):
		if (self.skipDepth != 0):
			self.log.warn ("End element %s is not allowed (start tag was suppressed)." % elementName)
			self.skipDepth -= 1
			return
			
		if (self.currentText): self.__outputText__()
		
		# Ensure that this type of end element is allowed, if not then ignore it.
		allowedTags, endTagPolicy = self.tagmap [elementName]
		if (endTagPolicy == TAG_FORBIDDEN):
			self.log.debug ("End tag %s forbidden, skipping." % elementName)
			return
			
		if (len (self.currentElementsStack) == 0):
			raise BadCloseTagException (elementName, self.currentElementsStack)
			
		self.allowedElementsStack.pop()
		expectedElement = self.currentElementsStack.pop()[0]
		if (elementName != expectedElement):
			looking = 1
			while (looking):
				expectedElementTagPolicy = self.tagmap [expectedElement][1]
				self.log.debug ("Tag %s has policy %s" % (expectedElement, str (expectedElementTagPolicy)))
				# No end-tag-forbidden elements ever go on the stack, which means we have an un-closed tag!
				if (self.exceptionOnError):
					raise BadCloseTagException (elementName, self.currentElementsStack, expectedElement)
				self.log.warn ("Closing un-closed tag %s" % expectedElement)
				if (elementName in self.blocklist):
					self.output.write (u'\n')
				
				if (len (self.currentElementsStack) > 0):
					self.allowedElementsStack.pop()
					expectedElement = self.currentElementsStack.pop()[0]
					if (expectedElement == elementName):
						looking = 0
				else:
					raise BadCloseTagException (elementName, self.currentElementsStack)
		if (elementName in self.blocklist):
			self.output.write (u'\n')
		
	def lineBreak (self):
		if (self.currentText): self.__outputText__()
		self.output.write (u'\n')
	
	def write (self, data):
		if (self.skipDepth == 0):
			self.output.write (data)
			self.dataLength += len (data)
	