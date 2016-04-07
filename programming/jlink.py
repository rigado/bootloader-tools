import os
import binascii
import sys
import platform
import subprocess
import re
import stat
import struct
import time
from utils import Utils

utils = Utils()

jlinkUICRFile = "uicr.bin"
jlinkMACFile = "mac.bin"
jlinkDatapageFile = "datapage.bin"
jlinkICFile = 'ic.bin'
jlinkICRevFile = 'icrev.bin'
jlinkScriptFile = 'jlink.script'
jlinkScriptReadMAC = 'jlink_scripts/jlink_readmacuicr.script'
jlinkScriptReadData = 'jlinkdata.script'

class JLink(object):
	def make_uicr_bin(self, device, bootloader_addr):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_uicr_bin")
		try:
			uicr = binascii.a2b_hex(bootloader_addr)[::-1]
			if device == "NRF52832_XXAA":
				uicr += binascii.a2b_hex('0007d000')[::-1]

			utils.log(utils.LOG_LEVEL_VERBOSE, "Write rigdfu2_uicr.bin")
			utils.deleteIfExists(jlinkUICRFile, self.cleanup)

			#create and write file
			fd = os.open(jlinkUICRFile, os.O_RDWR | os.O_CREAT)

			bin_size = 4
			if device == "NRF52832_XXAA":
				bin_size = 8

			if os.write(fd, bytes(uicr)) != bin_size:
				utils.errorHandler("Write error, wrote " + str(bytesWritten) + " expected 8", self.cleanup)

			#close file
			os.close(fd)
		except:
			utils.errorHandler('UICR binary creation failed!', self.cleanup)

	def make_mac_bin(self, macStr, device):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_mac_bin")
		mac = ''

		if macStr == None and (device == None or device == ''):
			utils.errorHandler("Cannot read MAC without knowing device!", self.cleanup)

		if macStr != None:
			utils.log(utils.LOG_LEVEL_VERBOSE, "Create mac from user input")
			#mac is stored little endian
			try:
				mac = binascii.a2b_hex(macStr)[::-1]
				utils.log(utils.LOG_LEVEL_DEBUG, str(mac))

				#output the mac to a binary file so we can write it from jlink to the UICR...
				utils.log(utils.LOG_LEVEL_VERBOSE, "Delete mac.bin")
				utils.deleteIfExists(jlinkMACFile, self.cleanup)

				#create and write file
				fd = os.open(jlinkMACFile,os.O_RDWR|os.O_CREAT)
				utils.log(utils.LOG_LEVEL_VERBOSE, "Write mac.bin")
				bytesWritten = os.write(fd,bytes(mac))

				if bytesWritten != 6:
					utils.errorHandler("Write error, wrote " + str(bytesWritten) + " expected 6", self.cleanup)

				#close file
				utils.log(utils.LOG_LEVEL_VERBOSE, "Close mac.bin")
				os.close(fd)
			except:
				utils.errorHandler('MAC Parse Failed!', self.cleanup)
		else:
			utils.log(utils.LOG_LEVEL_VERBOSE, "Reading mac from nrf")
			#delete any old mac_save.bin files
			utils.log(utils.LOG_LEVEL_VERBOSE, "Delete mac.bin")
			utils.deleteIfExists(jlinkMACFile, self.cleanup)

			#ok read the mac out from the UICR and check that the output was generated
			self.__make_read_data_script(device, '0x10001080', '6', jlinkMACFile)
			if self.runJLink(jlinkScriptReadData) != True or os.path.exists(jlinkMACFile) != True:
				utils.errorHandler('Error reading MAC from UICR!', self.cleanup)

			#on osx and linux, jlinkexe creates files with no permissions; add them so we can open
			sys_type = platform.system()
			if(sys_type == "Darwin" or sys_type == "Linux"):
				os.chmod(jlinkMACFile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

			#open the generated file and read
			if os.stat(jlinkMACFile).st_size == 6:
				f = open(jlinkMACFile,'rb')
				mac = f.read()
				f.close()
			else:
				utils.errorHandler('Invalid size for MAC output file!', self.cleanup)

		return mac

	def make_datapage_bin(self, keyStr, device):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_datapage_bin")
		outFilelength = 0
		writeOffset = 0
		utils.log(utils.LOG_LEVEL_VERBOSE, "Setup datapage address and offset")
		if device == 'NRF51822_XXAA':
			outFilelength = 0x400
			writeOffset = 0x3e0
		elif device == 'NRF52832_XXAA':
			outFilelength = 0x1000
			writeOffset = 0xfe0
		else:
			utils.errorHandler('Unknown device!', self.cleanup)

		outFileData = []
		key = 0
		
		#save the file to disk
		try:
			if len(keyStr) > 0:
				utils.log(utils.LOG_LEVEL_VERBOSE, "Update datapage with user input key")
				key = binascii.a2b_hex(keyStr)
				outFileData += [0] * writeOffset
				outFileData += key
				outFileData += [0] * (outFilelength - len(outFileData))

			#delete the old file
			utils.log(utils.LOG_LEVEL_VERBOSE, "Delete old datapage file")
			utils.deleteIfExists(jlinkDatapageFile, self.cleanup)

			#create and write file
			fd = os.open(jlinkDatapageFile,os.O_RDWR|os.O_CREAT)
			bytesWritten = os.write(fd,bytes(outFileData))

			#check everything was ok
			if(bytesWritten != outFilelength):
				utils.errorHandler("Write error, wrote " + str(bytesWritten) + " expected " + str(outFilelength), self.cleanup)
			else:
				os.close(fd)
				utils.log(utils.LOG_LEVEL_DEBUG, "Generated " + jlinkDatapageFile + " successfully!")
		except:
			utils.errorHandler("Filesystem error!", self.cleanup)

		return key

	def __unlock(self):
		utils.deleteIfExists(jlinkScriptReadData, self.cleanup)
		
		jlink_file = open(jlinkScriptReadData, 'w')
	
		jlink_file.write('SWDSelect\n')
		jlink_file.write('SWDWriteDP 1 0x50000000\n')
		jlink_file.write('SWDWriteDP 2 0x01000000\n')
		jlink_file.write('SWDWriteAP 1 0x00000001\n')
		jlink_file.write('sleep 500\n')
		jlink_file.write('exit\n')

		jlink_file.close()
		self.runJLink(jlinkScriptReadData)

		time.sleep(.500)

	def __make_read_data_script(self, device, address, size, binaryFileName):

		utils.deleteIfExists(jlinkScriptReadData, self.cleanup)

		jlink_file = open(jlinkScriptReadData, 'w')

		jlink_file.write('usb 0\nsi 1\nspeed 4000\n')
		jlink_file.write('device ' + device + '\n')
		jlink_file.write('r\ng\nsleep 200\n')
		jlink_file.write('savebin ' + binaryFileName + ' ' + address + ' ' + size + '\n')
		jlink_file.write('r\ng\nexit\n')
		jlink_file.close()

	def read_ic_data(self, device):
		utils.deleteIfExists(jlinkICFile, self.cleanup)
		utils.deleteIfExists(jlinkICRevFile, self.cleanup)

		self.__unlock()

		self.__make_read_data_script(device, '0xf0000fe0', '1', jlinkICFile)
		self.runJLink(jlinkScriptReadData)

		time.sleep(.125)

		self.__make_read_data_script(device, '0xf0000fe8', '1', jlinkICRevFile)
		self.runJLink(jlinkScriptReadData)

		time.sleep(.125)

		ic = 0
		rev = 0

		if os.stat(jlinkICFile).st_size == 1:
				f = open(jlinkICFile,'rb')
				ic = f.read()
				f.close()
		else:
			utils.errorHandler('Invalid size for IC data output file!', self.cleanup)

		if os.stat(jlinkICRevFile).st_size == 1:
				f = open(jlinkICFile,'rb')
				rev = f.read()
				f.close()
		else:
			utils.errorHandler('Invalid size for IC data output file!', self.cleanup)

		retic = ic[0]
		retrev = rev[0]

		return (retic, retrev)


	def make_script(self, device, softdevice, bootloader, 
		bootloader_addr, app_binary, app_address, 
		datapage_addr, disable_protect):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_script")
		utils.deleteIfExists(jlinkScriptFile, self.cleanup)

		jlink_file = open(jlinkScriptFile, 'w')

		utils.log(utils.LOG_LEVEL_VERBOSE, "Generate script setup for device " + device)

		jlink_file.write('usb 0\nsi 1\nspeed 1000\n')
		jlink_file.write('device ' + device + '\n')
		jlink_file.write('r\n')
		jlink_file.write('w4 4001e504 2\nw4 4001e50c 1\nsleep 200\nr\n')
		jlink_file.write('w4 4001e504 1\n')
		
		if len(softdevice) > 0:
			filename, extenstion = os.path.splitext(softdevice)
			if extenstion == '.hex':
				jlink_file.write('loadfile ' + softdevice + '\n')
				jlink_file.write('verifyfile ' + softdevice + '\n')
			else:
				jlink_file.write('loadbin ' + softdevice + ' 0x0\n') 
				jlink_file.write('verifybin ' + softdevice + ' 0x0\n')

		if len(bootloader) > 0:
			filename, extenstion = os.path.splitext(bootloader)
			if extenstion == '.hex':
				jlink_file.write('loadfile ' + bootloader + '\n')
				jlink_file.write('verifyfile ' + bootloader + '\n')
			else:
				jlink_file.write('loadbin ' + bootloader + ' ' + bootloader_addr + '\n')
				jlink_file.write('verifybin ' + bootloader + ' ' + bootloader_addr + '\n')
				jlink_file.write('loadbin ' + jlinkUICRFile + ' 0x10001014\n')
				jlink_file.write('verifybin ' + jlinkUICRFile + ' 0x10001014\n')

		jlink_file.write('loadbin mac.bin 0x10001080\n')
		jlink_file.write('verifybin mac.bin 0x10001080\n')

		if app_binary != None:
			filename, extenstion = os.path.splitext(app_binary)
			if extenstion == '.hex':
				jlink_file.write('loadfile ' + app_binary + '\n')
				jlink_file.write('verifyfile ' + app_binary + '\n')
			else:
				jlink_file.write('loadbin ' + app_binary + ' ' + app_address + '\n')
				jlink_file.write('verifybin ' + app_binary + ' ' + app_address + '\n')

		jlink_file.write('loadbin datapage.bin ' + datapage_addr + '\n')
		jlink_file.write('verifybin datapage.bin ' + datapage_addr + '\n')

		if not disable_protect:
			if device == 'NRF51822_XXAA':
				jlink_file.write('w4 4001e504 1\nw4 10001004 ffff00ff\nsleep 200\n')
				jlink_file.write('r\ng\nexit\n')
			elif device == 'NRF52832_XXAA':
				jlink_file.write('w4 4001e504 1\nw4 10001208 0\nsleep 200\n')
				jlink_file.write('exit\n')
			else:
				utils.errorHandler('Unknown device type!')
		else:
			jlink_file.write('r\ng\nexit\n')
		jlink_file.close()

		return jlinkScriptFile

	def cleanup(self):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.cleanup")
		utils.deleteIfExists(jlinkMACFile, None)
		#utils.deleteIfExists(jlinkUICRFile, None)
		utils.deleteIfExists(jlinkDatapageFile, None)
		utils.deleteIfExists(jlinkScriptFile, None)
		utils.deleteIfExists(jlinkICFile, None)
		utils.deleteIfExists(jlinkICRevFile, None)
		utils.deleteIfExists(jlinkScriptReadData, None)

	def __getJLinkExe(self):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.__getJLinkExe")
		sys_type = platform.system()

		cmd = ""
		if(sys_type == "Linux"):
			#command to run, jlink must be in same directory
			is_64bits = sys.maxsize > 2**32
			if is_64bits:
				cmd = "../jlink/linux/x86_64/JLinkExe"
			else:
				cmd = "../jlink/linux/i386/JLinkExe"
			use_shell = True
		elif(sys_type == "Windows"):
			#command to run, jlink must be in same directory
			cmd = "..\jlink\windows\jlink.exe"
			use_shell = False
		elif(sys_type == "Darwin"):
			#command to run, jlink must be in same directory
			cmd = "../jlink/osx/JLinkExe"
			use_shell = True
		else:
			utils.errorHandler("Unknown system", self.cleanup)

		return (cmd, use_shell)

	#run Jlink.exe
	def runJLink(self, scriptFileName):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.runJLink")
		jlink_tuple = self.__getJLinkExe()
		
		cmd = jlink_tuple[0] + " " + scriptFileName
		
		#run it
		p = subprocess.Popen(cmd, shell=jlink_tuple[1], stdout=subprocess.PIPE)
		
		jOutString = ""

		#start displaying output immediately
		while 1:
			out = p.stdout.readline()
			if len(out) == 0 and p.poll() != None:
				break
			if len(out) != 0:
				strIn = str(out,"utf-8")
				jOutString += strIn

		#once we are done, parse the output
		result = self.__verifyJLinkOutput(jOutString)

		return result

	#verify the output from the jlink script
	def __verifyJLinkOutput(self, jlinkoutput):
		utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.__verifyJLinkOutput")
		result = False

		if len(jlinkoutput) != 0:

			verifyCount = 0
			saveCount = 0
			loadCount = 0
			errorCount = 0
			verifyOK = 0
			saveOK = 0
			loadOK = 0

			result = True

			lines = jlinkoutput.split("\n")


			for line in lines:
				utils.log(utils.LOG_LEVEL_DEBUG, ">>> " + str(line))

				#load
				if re.match("Writing bin data into target memory @ 0x[0-9a-fA-F]+\.", line):
					loadCount+=1
				if re.match("Info: J-Link: Flash download: Flash programming performed for [1-9] range", line):
					loadOK+=1

				#save
				if re.match("Opening binary file for writing\.\.\. \[.+\]", line):
					saveCount+=1
				if re.match("Reading [0-9]+ bytes from addr 0x[0-9a-fA-F]+ into file\.\.\.O\.K\.", line):
					saveOK+=1

				#verify
				if re.match("Reading [0-9]+ bytes data from target memory @ 0x[0-9a-fA-F]+\.", line):
					verifyCount+=1
				if re.match("Verify successful", line):
					verifyOK+=1

				#catch errors...
				if "error" in line.lower():
					errorCount+=1

			if( verifyCount != verifyOK ):
				print("verifyJlinkOutput: verifybin error " + str(verifyOK) + "/" +str(verifyCount))
				result = False

			if( saveCount != saveOK ):
				print("verifyJlinkOutput: savebin error " + str(saveOK) + "/" +str(saveCount))
				result = False

			if( loadCount != loadOK ):
				print("verifyJlinkOutput: loadbin error " + str(loadOK) + "/" +str(loadCount))
				result = False

			if( errorCount != 0 ):
				print("verifyJlinkOutput: found errors " + str(errorCount))
				result = False

			if( verifyCount == 0 and saveCount == 0 and loadCount == 0 ):
				print("verifyJlinkOutput: no operations")
				result = False

			if(result == True):
				print("verifyJlinkOutput: success - load " + str(loadOK) + "/" +str(loadCount) + " verify " + str(verifyOK) + "/" +str(verifyCount) + " save " + str(saveOK) + "/" +str(saveCount))

		#todo verify the results
		return result
