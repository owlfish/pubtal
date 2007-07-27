import copy, xml.sax
try:
	import logging
except:
	from pubtal import InfoLogging as logging

# These are the tags that we explicitly handle.  We also handle all field elements as well, but only by 
# ignoring them.
#~ office:document-content
#~ meta:keyword
#~ style:style
#~ style:properties

#~ text:h
#~ text:p
#~ text:ordered-list
#~ text:unordered-list
#~ text:list-item
#~ text:span
#~ text:a
#~ text:footnote
#~ text:endnote
#~ text:footnote-body
#~ text:endnote-body
#~ text:bookmark-start
#~ text:bookmark
#~ text:line-break

#~ draw:image
#~ draw:a
#~ svg:desc

#~ table:table
#~table:sub-table
#~ table:table-header-rows
#~ table:table-row
#~ table:table-cell

# ALL Dublin core elements.

# The TAG_MAP lists all tags we can handle
			# meta.xml has document-meta as root element.
TAG_MAP = {'office:document-meta': ['office:meta']
		  ,'office:meta': ['meta:keywords', 'meta:creation-date', 'dc:title', 'dc:description', 'dc:subject', 'dc:creator', 'dc:date', 'dc:language']
		  ,'meta:keywords': ['meta:keyword']
		  ,'meta:keyword': []
		  ,'meta:creation-date': []
		  ,'dc:title': []
		  ,'dc:description': []
		  ,'dc:subject': []
		  ,'dc:creator': []
		  ,'dc:date': []
		  ,'dc:language': []
		  # styles.xml has document-styles
		  ,'office:document-styles': ['office:styles']
		  ,'office:styles': ['style:style']
		  # style:style is used in both style.xml and content.xml, and only contains style:properties.
		  ,'style:style': ['style:properties']
		  ,'style:properties': []
		  # The content.xml starts with office:document-content.  We only care about styles and the body.
		  ,'office:document-content': ['office:automatic-styles', 'office:body']
		  ,'office:automatic-styles': ['style:style']
		  ,'office:body': ['text:h', 'text:p', 'text:ordered-list', 'text:unordered-list'
						  ,'table:table', 'draw:a', 'text:section']}

# This list is taken from the OO DTD (text.mod) from the %fields ENTITY
# The following elements have been removed, because our parser does not have
# any code to handle them:
# 'office:annotation', 
FIELD_ELEMENTS = ['text:date','text:time','text:page-number','text:page-continuation','text:sender-firstname','text:sender-lastname','text:sender-initials'
,'text:sender-title','text:sender-position','text:sender-email','text:sender-phone-private','text:sender-fax'
,'text:sender-company','text:sender-phone-work','text:sender-street','text:sender-city','text:sender-postal-code'
,'text:sender-country','text:sender-state-or-province','text:author-name','text:author-initials','text:placeholder','text:variable-set'
,'text:variable-get','text:variable-input','text:user-field-get','text:user-field-input','text:sequence','text:expression'
,'text:text-input','text:database-display','text:database-next','text:database-select','text:database-row-number','text:database-name'
,'text:initial-creator','text:creation-date','text:creation-time','text:description','text:user-defined','text:print-time','text:print-date'
,'text:printed-by','text:title','text:subject','text:keywords','text:editing-cycles','text:editing-duration','text:modification-time'
,'text:modification-date','text:creator','text:conditional-text','text:hidden-text','text:hidden-paragraph','text:chapter','text:file-name'
,'text:template-name','text:page-variable-set','text:page-variable-get','text:execute-macro','text:dde-connection','text:reference-ref'
,'text:sequence-ref','text:bookmark-ref','text:footnote-ref','text:endnote-ref','text:sheet-name','text:bibliography-mark','text:page-count'
,'text:paragraph-count','text:word-count','text:character-count','text:table-count','text:image-count','text:object-count'
,'text:script','text:measure']

# FIELD_ELEMENTS need to be all empty for us to handle them
# These are the ones we can handle, despite not doing so explicitly
for elmn in FIELD_ELEMENTS:
	TAG_MAP [elmn] = []

INLINE_ELEMENTS = copy.copy (FIELD_ELEMENTS)
# This is based on the defintion in the text.mod DTD.
# I've NOT listed those elements that are harmless but unimplemented (e.g. tab-stop)
# Excluded: text:tab-stop, text:bookmark-stop, text:reference-mark, text:reference-mark-start, text:reference-mark-end
# %shape, text:toc-mark-start, text:toc-mark-end, text:toc-mark, text:user-index-mark-start, text:user-index-mark-end
# text:user-index-mark, text:alphabetical-index-mark-start, text:alphabetical-index-mark-end, text:alphabetical-index-mark
# %change-marks;, text:ruby
#
# We do list draw:text-box as implemented, otherwise we can not handle images with captions.
INLINE_ELEMENTS.extend (['text:span', 'text:line-break', 'text:footnote', 'text:endnote'
					   , 'text:a', 'text:s', 'text:bookmark', 'text:bookmark-start', 'draw:a'
					   , 'draw:image'])
# Now we need to add these extra elements to the TAG_MAP, otherwise we'll filter them out!
TAG_MAP ['text:span'] = INLINE_ELEMENTS
TAG_MAP ['text:line-break'] = []
TAG_MAP ['text:footnote'] = ['text:footnote-body']
TAG_MAP ['text:footnote-body'] = ['text:h', 'text:p', 'text:ordered-list', 'text:unordered-list']
TAG_MAP ['text:endnote'] = ['text:endnote-body']
TAG_MAP ['text:endnote-body'] = ['text:h', 'text:p', 'text:ordered-list', 'text:unordered-list']
TAG_MAP ['text:a'] = INLINE_ELEMENTS
TAG_MAP ['text:s'] = []
TAG_MAP ['text:bookmark'] = []
TAG_MAP ['text:bookmark-start'] = []
TAG_MAP ['draw:a'] = ['draw:image']
TAG_MAP ['draw:image'] = ['svg:desc']
TAG_MAP ['svg:desc'] = []

# Used by %textSections
TEXT_SECTIONS_ELEMENTS = ['text:p', 'text:h', 'text:ordered-list', 'text:unordered-list'
						 ,'table:table', 'text:section']
# We have the following elements left over that need to be defined in the TAG_MAP:
# 'text:h', 'text:p', 'text:ordered-list', 'text:unordered-list', 'table:table', 'text:section'
TAG_MAP ['text:h'] = INLINE_ELEMENTS
TAG_MAP ['text:p'] = INLINE_ELEMENTS
TAG_MAP ['text:unordered-list'] = ['text:list-item'] 
TAG_MAP ['text:ordered-list'] = ['text:list-item']
TAG_MAP ['text:list-item'] = ['text:p', 'text:h', 'text:ordered-list', 'text:unordered-list']
TAG_MAP ['table:table'] = ['table:table-header-rows', 'table:table-row', 'table:table-cell']
TAG_MAP ['table:table-header-rows'] = ['table:table-row']
TAG_MAP ['table:table-row'] = ['table:table-cell']
TAG_MAP ['table:table-cell'] = ['table:sub-table', 'text:h', 'text:p', 'text:ordered-list'
							   ,'text:unordered-list']
TAG_MAP ['table:sub-table'] = ['table:table-header-rows', 'table:table-row', 'table:table-cell']
TAG_MAP ['text:section'] = TEXT_SECTIONS_ELEMENTS


URLMAP = {'http://openoffice.org/2000/office': 'office'
		 ,'http://openoffice.org/2000/text': 'text'
		 ,'http://openoffice.org/2000/style': 'style'
		 ,'http://openoffice.org/2000/table': 'table'
		 ,'http://www.w3.org/1999/XSL/Format': 'fo'
		 ,'http://purl.org/dc/elements/1.1/': 'dc'
		 ,'http://openoffice.org/2000/meta': 'meta'
		 ,'http://www.w3.org/1999/xlink': 'xlink'
		 ,'http://www.w3.org/2000/svg': 'svg'
		 ,'http://openoffice.org/2000/drawing': 'draw'}

def validateTagMap():
	errorMap = {}
	for element in TAG_MAP.keys():
		for child in TAG_MAP [element]:
			if (not TAG_MAP.has_key (child)):
				errorMap [child] = 1
	return errorMap.keys()

class SAXFilter(xml.sax.handler.ContentHandler):
	"""	The purpose of this class is to filter out calls that we don't handle.
		It also dispatches to other SAX handlers based on the namespaces that
		they register with.
	"""
	def __init__ (self):
		xml.sax.handler.ContentHandler.__init__ (self)
		self.log = logging.getLogger ("PubTal.OOC.SAXFilter")
		self.debugOn = self.log.isEnabledFor (logging.DEBUG)
		self.documentHandlers = {}
		self.handlerStack = []
		self.allowedElementsStack = []
		self.skipDepth = 0
		
	def setHandler (self, namespace, handler):
		self.documentHandlers [namespace] = handler
		
	def startElementNS (self, name, qname, atts):
		# Are we skipping elements?
		if (self.skipDepth != 0):
			# Skipping, so just increment the depth
			self.skipDepth += 1
			if (self.debugOn):
				self.log.debug ("Skipping element %s - depth now %s" % ('%s:%s' % (URLMAP.get (name[0],''), name[1]), str (self.skipDepth)))
			return
			
		# Determine whether this tag is allowed or not.
		elementName = '%s:%s' % (URLMAP.get (name[0],''), name[1])
		if (not self.__checkAllowed__ (elementName)):
			self.skipDepth += 1
			return
		
		# This element is allowed, so find a handler and pass it through
		handler = self.documentHandlers.get (name[0], None)
		self.handlerStack.append (handler)
		if (handler is not None):
			handler.startElementNS (name, qname, atts)
		
	def endElementNS (self, name, qname):
		if (self.skipDepth != 0):
			self.skipDepth -= 1
			if (self.debugOn):
				self.log.debug ("Skipping END element %s - depth now %s" % ('%s:%s' % (URLMAP.get (name[0],''), name[1]), str (self.skipDepth)))
			return
		
		handler = self.handlerStack.pop()
		self.allowedElementsStack.pop()
		if (self.debugOn):
			self.log.debug ("Allowed END element %s" % '%s:%s' % (URLMAP.get (name[0],''), name[1]))
		if (handler is not None):
			handler.endElementNS (name, qname)
		
	def characters (self, data):
		if (self.skipDepth != 0):
			return
		
		handler = self.handlerStack [-1]
		if (handler is not None):
			handler.characters (data)
	
	def __checkAllowed__ (self, tagName):
		if (len (self.allowedElementsStack) == 0):
			# We are allowed, so let's record what we expect next.
			self.log.debug ("Root element passed, adding allowed elements to stack.")
			self.allowedElementsStack.append (TAG_MAP.get (tagName, []))
			# We re-check for debug status when we see a root element, that way if logging
			# config is changed between runs we will pick it up.
			self.debugOn = self.log.isEnabledFor (logging.DEBUG)
			return 1
			
		if tagName in self.allowedElementsStack[-1]:
			# We are allowed, so let's record what we expect next.
			if (self.debugOn):
				self.log.debug ("Found element %s, allowing" % tagName)
			self.allowedElementsStack.append (TAG_MAP.get (tagName, []))
			return 1
		#self.log.debug ("Element %s blocked." % tagName)
		return 0
