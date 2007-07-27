""" Binary copy plugin for PubTal

	Copyright (c) 2003 Florian Schulze (http://proff.crowproductions.com/)
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

import os, os.path

try:
	import logging
except:
	from pubtal import InfoLogging as logging

from pubtal import SitePublisher

def getPluginInfo ():
	defaultFileTypes = ['jpg', 'png', 'gif', 'gz', 'zip']
	builtInContent = [{'functionality': 'content', 'file-type': defaultFileTypes, 'content-type': 'Binary', 'class': BinaryCopyPublisher}]
	return builtInContent

class BinaryCopyPublisher(SitePublisher.ContentPublisher):
	def __init__ (self, pagePublisher):
		SitePublisher.ContentPublisher.__init__ (self, pagePublisher)
		self.log = logging.getLogger ("PubTal.BinaryCopyPublisher")

	def publish (self, page):
		# get paths
		sourceFilePath = page.getSource()
		
		# open files
		sourceFile = open(sourceFilePath, 'rb')
		destFilePath = page.getRelativePath()
		destFile = self.pagePublisher.openOuputFile (destFilePath)

		self.log.debug ('Copying to %s' % destFilePath)

		# get bufferSize (added for testing, not really useful)
		try:
			bufferSize = int(page.getOption('buffer-size', 1024*1024))
		except ValueError:
			bufferSize = 1024*1024
		self.log.debug('bufferSize %s' % bufferSize)

		# copy
		while 1:
			buffer = sourceFile.read(bufferSize)
			if len(buffer) == 0:
				break
			destFile.write(buffer)
		
		sourceFile.close()
		destFile.close()
		
