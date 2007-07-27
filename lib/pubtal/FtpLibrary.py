import string, os, ftplib, os.path, string

try:
	import logging
except:
	import InfoLogging as logging
	
class FTPDirList:
	""" Brings back a list of the entries in the currrent working directory on 
		an FTP server."""
	def __init__ (self, client):
		self.list = []
		client.retrlines ('LIST', self.callback)
		
	def callback (self, entry):
		self.list.append (entry)
		
	def getList (self):
		newList = []
		for dir in self.list:
			components = dir.split ()
			if (len (components) > 8):
				# We have an actual FTP entry...
				newList.append ("".join (components[8:]))
		return newList
		
class DirectoryMaker:
	""" A class that creates directories on an FTP site.
	
		This class will ensure that a directory already exists, or make
		it if required.  It cache's the available directory list to 
		reduce load on the server.
	"""
	def __init__ (self):
		self.dirCache = {}
		self.log = logging.getLogger ("FtpLibrary.DirectoryMaker")
		
	def makeDir (self, aDir, client):
		""" Make this directory structure if required.
			NOTE: This only works on relative paths!
		"""
		curDir = client.pwd()
		head, tail = os.path.split (aDir)
		dirsList = []
		while (len (head) > 0):
			# We have a directory element to check
			dirsList.insert (0,tail)
			head, tail = os.path.split (head)
		dirsList.insert (0, tail)
			
		# We have a list of directories to check - now get to it!
		currentLocation = ""
		skippedDirs = []
		hadToMove = 0
		for dirToCheck in dirsList:
			currentLocation = os.path.join (currentLocation, dirToCheck)
			# Check the cache first.
			if (self.dirCache.has_key (os.path.join (curDir, currentLocation))):
				self.log.debug ("Directory %s already exists - found in cache." % currentLocation)
				skippedDirs.append (dirToCheck)
			else:
				self.log.debug ("Directory %s not found in cache." % currentLocation)
				# Note that we changed directory.
				hadToMove = 1
				for skipDir in skippedDirs:
					self.log.debug ("Changing skipped directory to %s" % skipDir)
					client.cwd (skipDir)
				skippedDirs = []
				dirList = FTPDirList (client)
				if (dirToCheck not in dirList.getList()):
					# Does not exists!
					self.log.info ("Directory %s does not exist, creating dir." % currentLocation)
					client.mkd (dirToCheck)
				# Add the directory to the cache as one that exists!
				self.dirCache [os.path.join (curDir, currentLocation)] = 1
				client.cwd (dirToCheck)
		if (hadToMove):
			self.log.debug ("Had to move directories, going back to original.")
			client.cwd (curDir)
		else:
			self.log.debug ("Cache saved us moving directory.")
		
class FTPUpload:
	def __init__ (self, host, username, password, initialDir=None):
		self.host = host
		self.username = username
		self.password = password
		self.initialDir = initialDir
		self.log = logging.getLogger ("FtpLibrary.FTPUpload")
		self.dirMaker = DirectoryMaker()
		self.client = None
		
	def connect (self, userInteraction):
		self.client = self._getClient_ (userInteraction)
		if (self.client is None):
			return 0
		return 1
	
	def uploadFile (self, localDir, fName, userInteraction):
		if (self.client is None):
			return 0
			
		self.log.debug ("Processing file %s" % fName)
		remoteDir, remoteFile = os.path.split (fName)
		# Ensure that the directory is present
		if (len (remoteDir) > 0):
			self.dirMaker.makeDir (remoteDir, self.client)
		path = os.path.join (localDir, fName)
		
		self.log.debug ("Attempting to upload %s to %s" % (path, fName))
		try:
			uploadFile = open (path,'r')
			self.client.storbinary ('STOR %s' % fName, uploadFile)
			uploadFile.close()
			self.log.debug ("Uploaded: " + fName)
		except Exception, e:
			self.log.error ("Error uploading: " + str (e))
			userInteraction.taskError ("Error uploading: " + str (e))
			return 0
		return 1
		
	def disconnect (self):
		try:
			self.client.quit()
		except Exception:
			self.log.warn ("Exception occured while closing FTP connection")
			
		
	def _getClient_ (self, userInteraction):
		try:
			client = ftplib.FTP (self.host, self.username, self.password)
		except (ftplib.all_errors), e:
			self.log.error ("Error connecting to FTP Site: " + str (e))
			userInteraction.taskError ("Error connecting to FTP Site: " + str (e))
			return None
		
		if (self.initialDir is not None):
			self.log.debug ("Attempting to change directory to: " + str (self.initialDir))
			try:
				client.cwd (self.initialDir)
			except (ftplib.all_errors), e:
				self.log.error ("Error changing directory: " + str (e))
				userInteraction.taskError ("Error changing directory: " + str (e))
				return None
		
		return client
