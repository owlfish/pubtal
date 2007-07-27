import md5, anydbm, logging, os, os.path, time

logging.basicConfig()
root = logging.getLogger ()
root.setLevel (logging.INFO)

class CheckSumAll:
	def __init__ (self, dbFile):
		self.log = logging.getLogger ("CheckSumAll")
		self.db = anydbm.open (dbFile, 'c')
		self.foundFiles = []
		
	def checkSumAll (self, dir):
		os.path.walk (dir, self.walkPaths, None)
		for fName in self.foundFiles:
			#self.log.info ("Getting checksum for %s" % fName)
			self.db [fName] = self._getChecksum_ (fName)
			
	def finished (self):
		self.db.close()
		
	def walkPaths (self, arg, dirname, names):
		for name in names:
			self.log.debug ("Checking path %s for files." % os.path.join (dirname, name))
			realName = os.path.join (dirname, name)
			if (os.path.isfile (realName)):
				self.foundFiles.append (realName)
	
	def _getChecksum_ (self, path):
		sum = md5.new()
		readFile = open (path, 'r')
		while 1:
			buffer = readFile.read(1024*1024)
			if len(buffer) == 0:
				break
			sum.update(buffer)
		
		readFile.close()
		return sum.hexdigest()
		
if __name__ == '__main__':
	start = time.clock()
	summer = CheckSumAll ('/tmp/cmsDB')
	summer.checkSumAll ('owlfish.com/weblog/src')
	#summer.checkSumAll ('owlfish.com/weblog/src/weblog/2004/02')
	summer.finished
	end = time.clock()
	print "Total time for checksumming: %s" % str (end-start)
	