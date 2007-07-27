""" A really simple internal message bus for PubTal.

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
import logging

class MessageBus:
	def __init__ (self):
		# This contains eventType: FunctionDictionary pairs.
		self.listeners = {}
		# This contains (eventType, dataValue):FunctionDictionary pairs
		self.filterListeners = {}
		self.log = logging.getLogger ("MessageBus")
	
	def registerListener (self, eventType, func):
		currentListeners = self.listeners.get (eventType, {})
		currentListeners [func] = func
		self.listeners [eventType] = currentListeners
		self.log.info ("Function %s registered for event type %s" % (repr (func), eventType))
		
	def unregisterListener (self, eventType, func):
		currentListeners = self.listeners.get (eventType, {})
		try:
			del currentListeners [func]
			self.log.info ("Function %s un-registered for event type %s" % (repr (func), eventType))
		except:
			self.log.warn ("Function %s was not registered for event type %s, but tried to unregister." % (repr (func), eventType))
	
	def registerFilterListener (self, eventType, dataValue, func):
		currentListeners = self.filterListeners.get ((eventType, dataValue), {})
		currentListenter [func] = func
		self.filterListeners [(eventType, dataValue)] = currentListeners
		
	def unregisterFilterListener (self, eventType, dataValue, func):
		currentListeners = self.filterListeners.get ((eventType, dataValue), {})
		try:
			del currentListeners [func]
		except:
			self.log.warn ("Function %s was not registered for event type %s, but tried to unregister." % (repr (func), eventType))
		
	def notifyEvent (self, eventType, data=None):
		currentListeners = self.listeners.get (eventType, {})
		for listener in currentListenters.values():
			listener (eventType, data)
		filterListeners = self.filterListeners.get ((eventType, data), None)
		if (filterListeners is not None):
			for listener in filterListeners.values():
				listener (eventType, data)
				
	