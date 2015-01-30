#!/usr/bin/python

import binascii
import os
import sys
import subprocess
import re
import binascii
import argparse

#error handler
def errorHandler(errString):
	print('Error: ' + errString)
	sys.exit(1)

#run Jlink.exe
def runJLink(scriptFileName):
	#command to run, jlink must be in same directory
	cmd = "./JLinkExe " + scriptFileName
	 
	#run it
	#p = os.popen(cmd, 'r')
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	#os.system(cmd)
	jOutString = ""

	#start displaying output immediately
	while 1:
		out = p.stdout.readline()
		if len(out) == 0 and p.poll() != None:
			break
		if len(out) != 0:
			strIn = str(out,"utf-8")
			jOutString += strIn
			#sys.stdout.write(strIn)
			#sys.stdout.flush()

	#once we are done, parse the output
	result = verifyJLinkOutput(jOutString)
	return result

#verify the output from the jlink script
def verifyJLinkOutput(jlinkoutput):
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
			if args.verbose:
				print(">>> " + str(line))

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


####################
#script entry point#
####################
#output file data
outFileName = 'datapage.bin'
outFilelength = 0x400
writeOffset = 0x3e0
outFileData = []

#Jlink Scripts
jlinkScriptReadMAC 	= 'jlink_readmacuicr.script'
jlinkScriptLoad 	= 'jlink_loader.script'
jlinkScriptLoadWApp = 'jlink_loader_wapp.script'
jlinkMACFile		= 'mac.bin'
jlinkAppFile		= 'application.bin'

#parse the arguments
parser = argparse.ArgumentParser(description="BMD-200 Programmer")
parser.add_argument("-m", 	"--mac", type=str, help="MAC address (6 octets, big-endian)", default="")
parser.add_argument("-k", 	"--key", type=str, help="encryption key (16 bytes, big-endian)", default="00000000000000000000000000000000")
parser.add_argument("-t", 	"--tag", type=str, help="device tag for output log", default="noTag")
parser.add_argument("-sm", 	"--savemac", action="store_true", help="use the MAC written in module")
parser.add_argument("--verbose", action="store_true", help="enable verbose output")
parser.add_argument("--logfile", type=str, help="log file output", default="log.txt")
parser.add_argument("-a",   "--app", action="store_true", help="program application binary (application.bin)")
args = parser.parse_args()

#strip colons from mac/key input
args.mac = args.mac.replace(":","")
args.key = args.key.replace(":","")

#if application programming was specified, verify the binary exists
if args.app:
	try:
		if(os.path.exists(jlinkAppFile) != True):
			errorHandler("Application binary missing!")
	except:
		errorHandler("Filesystem Error!")

if args.savemac == False and len(args.mac) != 12:
	errorHandler('Invalid MAC Address')

if len(args.key) != 32:
	errorHandler('Invalid Key Length')

#see if we are preserving the mac
if args.savemac:
	#delete any old mac_save.bin files
	if(os.path.exists(jlinkMACFile)):
		os.remove(jlinkMACFile)

	#ok read the mac out from the UICR and check that the output was generated
	if runJLink(jlinkScriptReadMAC) != True or os.path.exists(jlinkMACFile) != True:
		errorHandler('Error reading MAC from UICR!')

	#open the generated file and read
	if os.stat(jlinkMACFile).st_size == 6:
		f = open(jlinkMACFile,'rb')
		mac = f.read()
	else:
		errorHandler('Invalid size for MAC output file!')
else:
	try:
		#mac is stored little endian
		mac = binascii.a2b_hex(args.mac)[::-1]

		#output the mac to a binary file so we can write it from jlink to the UICR...
		if(os.path.exists(jlinkMACFile)):
			os.remove(jlinkMACFile)

		#create and write file
		fd = os.open(jlinkMACFile,os.O_RDWR|os.O_CREAT)

		if os.write(fd,bytes(mac)) != 6:
			errorHandler("Write error, wrote " + str(bytesWritten) + " expected 6")

		#close file
		os.close(fd)

	except:
		errorHandler('MAC Parse Failed!')

#key to binary
try:
	#key is stored big endian
	key = binascii.a2b_hex(args.key)
except:
	errorHandler('Key Parse Failed!')

#build the datapage binary
try:
	outFileData += [0] * writeOffset
	outFileData += key
	outFileData += mac
	outFileData += [0] * (outFilelength - len(outFileData))
except:
	errorHandler("File generation error!")
		
#save the file to disk
try:
	#delete the old file
	if(os.path.exists(outFileName)):
		os.remove(outFileName)

	#create and write file
	fd = os.open(outFileName,os.O_RDWR|os.O_CREAT)
	bytesWritten = os.write(fd,bytes(outFileData))

	#check everything was ok
	if(bytesWritten != outFilelength):
		errorHandler("Write error, wrote " + str(bytesWritten) + " expected " + str(outFilelength))
	else:
		os.close(fd)
		print("Generated " + outFileName + " successfully!")
except:
	errorHandler("Filesystem error!")

#run jlink programming
if args.app:
	try:
		if(runJLink(jlinkScriptLoadWApp) != True):
			errorHandler("JLink Programming Error!")

	except:
		errorHandler("JLink error!")
else:
	try:
		if(runJLink(jlinkScriptLoad) != True):
			errorHandler("JLink Programming Error!")

	except:
		errorHandler("JLink error!")


#write log
logString = "mac: " + str(binascii.b2a_hex(bytes(mac)[::-1]),"utf-8").upper() + ", key: " + str(binascii.b2a_hex(bytes(key)),"utf-8").upper() + ", tag: " + args.tag + "\n"
with open(args.logfile,'a') as f: f.write(logString)

#script complete!
print("Wrote log @ " + args.logfile + ": " + logString.strip() )
print("Programming completed successfully!")
