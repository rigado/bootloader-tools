import os
import binascii
import sys
import platform
import subprocess
import re
import stat

class Utils(object):

	__loglevel = 2

	LOG_LEVEL_ERROR = 0
	LOG_LEVEL_WARNING = 1
	LOG_LEVEL_INFO = 2
	LOG_LEVEL_DEBUG = 3
	LOG_LEVEL_VERBOSE = 4

	def errorHandler(self, errString, errorFunc):
		self.log(0, 'Error: ' + errString)
		if(errorFunc):
			errorFunc()
		sys.exit(1)

	def deleteIfExists(self, fileName, errorFunc):
		try:
			if os.path.exists(fileName):
				os.remove(fileName)
		except FileError as e:
			self.errorHanlder("File error ({0}): {1}".format(e.errno, e.strerror), errorFunc)
		except:
			self.errorHanlder("Filesystem Error!", errorFunc)

	def runCommand(self, cmd, useShell):
		self.log(self.LOG_LEVEL_VERBOSE, 'utils.runCommand')
		self.log(self.LOG_LEVEL_DEBUG, cmd)
        
		p = subprocess.Popen(cmd, shell=useShell, stdout=subprocess.PIPE)

		jOutString = ""
		#start displaying output immediately
		while 1:
			out = p.stdout.readline()
			if len(out) == 0 and p.poll() != None:
				break
			if len(out) != 0:
				strIn = str(out,"utf-8")
				jOutString += strIn

		return jOutString

	def setLogLevel(self, level):
		Utils.__loglevel = level

	def log(self, level, msg):
		if level <= self.__loglevel:
			print(msg)