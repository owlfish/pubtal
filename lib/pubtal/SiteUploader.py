""" Utility classes to help automate the PubTal testing.

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

try:
	import logging
except:
	import InfoLogging as logging
	
import os, os.path, copy, hashlib, getpass, codecs
		
class UploadMethod:
	""" An upload method should implement these methods, although
		it isn't a requirment to inherit from this class.
	"""
	def __init__ (self, siteConfig, uploadConfig):
		self.siteConfig = siteConfig
		self.uploadConfig = uploadConfig
		
	def getDB (self):
		return {}
		
	def uploadFiles (self, fileDict, userInteraction):
		"Return 1 for success, 0 for failure.  Must notify UserInteraction directly."
		pass
		
	def markFilesUpToDate (self, fileDict, userInteraction):
		percentage = 0.0
		increment = 100.0/float (len (fileDict))
		db = self.getDB()
		for fName in fileDict.keys():
			userInteraction.taskProgress ("Marking file %s as already uploaded." % fName, percentage)
			db [fName] = fileDict [fName]
			percentage += increment
		
	def finished (self):
		pass

class SiteUploader:
	""" A class that determines which files should be uploaded at this time."""
	def __init__ (self, config):
		self.config = config
		self.log = logging.getLogger ('SiteUploader')
		self.currentDestFiles = []
		self.destDir = config.getDestinationDir()
		self.localCache = config.getLocalCacheDB()
		self.utfencode = codecs.lookup ("utf8")[0]
		self.utfdecode = codecs.lookup ("utf8")[1]
		self.ignoreFilters = config.getIgnoreFilters()
		
	def uploadSite (self, uploadConfig, userInteraction, target=None, options = {}):
		""" Determines what the upload method is, finds a provider to use that
			method, then determines what files need to be uploaded, and then
			does the actual upload.
		"""
		# Get the options being used for the upload
		allFiles = options.get ('allFiles', 0)
		forceUpload = options.get ('forceUpload', 0)
		markFilesUpToDate = options.get ('markFilesUpToDate', 0)
		dryRun = options.get ('dry-run', 0)
		
		# Get the method
		try:
			uploadMethod = uploadConfig['method']
		except:
			self.log.warn ("Upload method not specified, assuming FTP")
			uploadMethod = 'FTP'
		
		try:
			methodKlass = self.config.getSupportedUploadMethods ()[uploadMethod]
		except:
			msg = "There is no support for upload method %s" % uploadMethod
			self.log.error (msg)
			userInteraction.taskError (msg)
			return
			
		# Get an instance of the UploadMethod
		self.log.debug ("Creating upload method instance.")
		method = methodKlass (self.config, uploadConfig)
		self.log.debug ("Asking for database.")
		self.uploadDB = method.getDB()
		self.log.debug ("Getting files to upload...")
		fileDict = self._getFilesToUpload_ (target, allFiles, forceUpload)
		if (len (fileDict) == 0):
			self.log.info ("No files in file dictionary.")
			userInteraction.info ("No files to process, the site is up-to-date.")
			self.uploadDB = None
			method.finished()
			userInteraction.taskDone()
			return
			
		if (markFilesUpToDate):
			if (dryRun):
				userInteraction.info ("dry-run: Would mark the following files as being up-to-date")
				for fName in fileDict.keys():
					userInteraction.info ("dry-run: Would mark %s as up-to-date" % fName)
			else:
				userInteraction.info ("Marking files as being up-to-date.")
				method.markFilesUpToDate (fileDict, userInteraction)
		else:
			if (dryRun):
				userInteraction.info ("dry-run: Would upload the following files.")
				for fName in fileDict.keys():
					userInteraction.info ("dry-run: Would upload %s" % fName)
			else:
				method.uploadFiles (fileDict, userInteraction)
		self.uploadDB = None
		method.finished()
		userInteraction.taskDone()
		
	def _getFilesToUpload_ (self, target, allFiles, forceUpload):
		""" Returns a dictionary of files that need uploading.
			The key is the filepath, the value is the current checksum.
		
			target is either:
				None 							- Get all files
				List of files or dir paths		- Get only files in these paths
				
			allFiles is a flag.  True means include files PubTal didn't create.
			forceUpload is a flag.  True means upload files even if they haven't changed.
		"""
		result = {}
		
		if (target is None):
			self.log.debug ("Looking at whole site for upload material.")
			targetList = [self.destDir]
		else:
			targetList = []
			for t in target:
				targetList.append (os.path.abspath (t))
				
		for targetPath in targetList:
			self.log.debug ("Checking target path: %s" % targetPath)
			# Are we doing just one file or a dir?
			if (os.path.isfile (targetPath)):
				qualified = self.qualifyPath (targetPath, allFiles, forceUpload)
				if (qualified is not None):
					relPath, curChecksum = qualified
					result [relPath] = curChecksum
			else:
				os.path.walk (targetPath, self.walkPaths, None)
				for destFile in self.currentDestFiles:
					qualified = self.qualifyPath (destFile, allFiles, forceUpload)
					if (qualified is not None):
						relPath, curChecksum = qualified
						result [relPath] = curChecksum
			self.currentDestFiles = []
		return result
		
	def qualifyPath (self, path, allFiles, forceUpload):
		# Determine whether the path should be uploaded, and turn into a relative path if so.
		
		# Get the relative path as first step.
		commonRoot = os.path.commonprefix ([self.destDir, path])
		relativePath = path[len (commonRoot)+1:]
		utfRelativePath = self.utfencode (relativePath)[0]
		
		if (not allFiles):
			# Check that PubTal created this file.
			if (not self.localCache.has_key (utfRelativePath)):
				self.log.debug ("File %s is not in localCache, but allFiles is false." % utfRelativePath)
				return None
				
		# We always need the current checksum
		try:
			curChecksum = self.localCache [utfRelativePath]
			# This was a PubTal generated file
		except:
			# Not a PubTal generated file, so we need to generate our own checksum on the real file.
			curChecksum = self._getChecksum_ (path)
		
		if (not forceUpload):
			if (self.uploadDB.has_key (utfRelativePath)):
				# We've uploaded this file before, time to compare checksums
				lastChecksum = self.uploadDB [utfRelativePath]
				
				if (lastChecksum == curChecksum):
					self.log.debug ("File %s has same checksum as last upload, and forceUpload is false." % relativePath)
					return None
				self.log.info ("File %s has changed since last upload." % relativePath)
			else:
				# We have never seen the file before, so we assume that we must upload it!
				self.log.info ("File %s is new and has never been uploaded." % relativePath)
		else:
			self.log.info ("Forcing upload of file %s" % relativePath)
		
		return (relativePath, curChecksum)
		
	def _getChecksum_ (self, path):
		sum = hashlib.md5()
		readFile = open (path, 'r')
		while 1:
			buffer = readFile.read(1024*1024)
			if len(buffer) == 0:
				break
			sum.update(buffer)
		
		readFile.close()
		return sum.hexdigest()
	
	def walkPaths (self, arg, dirname, names):
		for name in names:
			realName = os.path.join (dirname, name)
			if (os.path.isfile (realName)):
				# Check to see whether it is a file we should ignore.
				addFile = 1
				for filter in self.ignoreFilters:
					if (filter.match (realName)):
						addFile = 0
				if (addFile):
					self.currentDestFiles.append (realName)
		