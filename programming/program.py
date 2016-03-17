#!/usr/bin/python

import binascii
import os
import sys
import subprocess
import re
import binascii
import argparse
import platform
import stat
import shutil
from intelhex import IntelHex
from jlink import JLink
from utils import Utils

jlink = JLink()
utils = Utils()

ICVersionNRF51 = 1
ICVersionNRF52 = 6

#check chip hardware id register
def checkHwId(min, max):
	#delete any old mac_save.bin files
	utils.deleteIfExists(jlinkHWIDFile, None)

	jlink.runJLink(jlinkScriptHWID) 
		
	#on osx and linux, jlinkexe creates files with no permissions; add them so we can open
	sys_type = platform.system()
	if(sys_type == "Darwin" or sys_type == "Linux"):
		os.chmod(jlinkHWIDFile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
	
	#open the generated file and read
	if os.stat(jlinkHWIDFile).st_size == 2:
		f = open(jlinkHWIDFile,'rb')
		hwid_data = f.read()
		f.close()
	else:
		errorHandler('Invalid size for Hardware ID output file!')

	os.remove(jlinkHWIDFile)

	hwid = hwid_data[0] + (hwid_data[1] << 8)
	if args.verbose:
		print("Found hardware version: " + hex(hwid))
	if hwid >= min and hwid <= max:
		return True

	if args.verbose:
		print("Expected hardward version " + min + " - " + max)
	return False


####################
#script entry point#
####################

#parse the arguments
parser = argparse.ArgumentParser(description="BMD Series Programmer")
parser.add_argument("-m", 	"--mac", type=str, help="MAC address (6 octets, big-endian)", default="")
parser.add_argument("-k", 	"--key", type=str, help="encryption key (16 bytes, big-endian)", default="00000000000000000000000000000000")
parser.add_argument("-t", 	"--tag", type=str, help="device tag for output log", default="noTag")
parser.add_argument("-sm", 	"--savemac", action="store_true", help="use the MAC written in module")
parser.add_argument("-r",	"--disablereadback", action="store_true", help="set to disable readback protection (not typical!)")
parser.add_argument("-v",   "--verbose", type=str, help="enable verbose output, available options from least to most are 0, 1, 2, 3, 4, 5")
parser.add_argument("--logfile", type=str, help="log file output", default="log.txt")
parser.add_argument("-a",   "--app", type=str, help="program application binary (application.bin)")
#unsure about support for S120 bootloader yet
parser.add_argument("-s",	"--softdevice", type=str, help="program specific softdevice, if not specificed, 110 for nrf51 and s132 for nrf52; valid values 110, 130, 132")
args = parser.parse_args()

if args.verbose:
	try:
		logLevel = int(args.verbose)
		utils.setLogLevel(logLevel)
	except:
		utils.errorHandler("Verbosity level invalid: " + args.verbose)
 
#strip colons from mac/key input
args.mac = args.mac.replace(":","")
args.key = args.key.replace(":","")

#if application programming was specified, verify the binary exists
if args.app and len(args.app) != 0:	
	if(os.path.exists(args.app) == False):
		utils.errorHandler("Application file missing: " + args.app + "!", None)

#validate input mac and key if available
if args.savemac == False and len(args.mac) != 12:
	utils.errorHandler('Invalid MAC Address; Expected length 12, received ' + len(args.mag) + "!", None)

if len(args.key) != 32:
	utils.errorHandler('Invalid Key Length; Expected length 32, received ' + len(args.key) + "!", None)

ic = 0
rev = 0
device = 'NRF51822_XXAA'

try:
	ic, rev = jlink.read_ic_data(device)
except:
	utils.errorHandler("Could not read IC type; is the JLink connected to the system?", jlink.cleanup)

ic = int(ic)
rev = int(rev)
utils.log(2, "IC " + str(ic))
if ic == ICVersionNRF52:
	device = 'NRF52832_XXAA'

if args.softdevice:
	if device == 'NRF52832_XXAA' and args.softdevice != '132':
		utils.log(1, "Invalid Softdevice specified for IC; ignoring input and using S132")
		args.softdevice = '132'
	elif device == 'NRF51822_XXAA' and args.softdevice == '132':
		utils.log(1, "Invalid Softdevice specified for IC; ignoring input and using S110")
		args.softdevice = '110'
else:
	if device == 'NRF52832_XXAA':
		utils.log(2, 'Programming for NRF52832, Softdevice S132')
		args.softdevice = '132'
	else:
		utils.log(2, 'Programming for NRF51822, Softdevice S110')
		args.softdevice = '110'

#default to s110 no app
appStr = None
appAddrNeeded = False
appAddr = '0x18000'
bootloaderStr = 'binaries/rigdfu2_nrf51_s110_rel_3_1_3.hex'
bootloaderAddr = '0x3A800'
bootloaderBinaryAddr = '0003A800'
datapageAddr = '0x3FC00'
softdeviceStr = 'binaries/s110_nrf51_8.0.0_softdevice.hex'

if args.softdevice == '130':
	appAddr = '0x1b000'
	softdeviceStr = 'binaries/s130_nrf51_2.0.0_softdevice.hex'
	bootloaderStr = 'binaries/rigdfu2_nrf51_s130_rel_3_2_0.hex'
elif args.softdevice == '132':
	appAddr = '0x1c000'
	device = 'NRF52832_XXAA'
	softdeviceStr = 'binaries/s132_nrf52_2.0.0_softdevice.hex'
	bootloaderAddr = '0x75000'
	bootloaderStr = 'binaries/rigdfu2_nrf52_s132_rel_3_2_0.hex'
	bootloaderBinaryAddr = '00075000'
	datapageAddr = '0x7f000'
else:
	if len(args.softdevice) > 0 and args.softdevice != '110':
		utils.errorHandler('Unknown softdevice!', None)

#see if we are preserving the mac
mac = None
if args.savemac:
	mac = jlink.make_mac_bin(None, device)		
else:
	mac = jlink.make_mac_bin(args.mac, None)

if args.app:
	appStr = args.app

#validate existence of all necessary binary files; application validated earlier in script
if not os.path.exists(softdeviceStr):
	utils.errorHandler("Missing Softdevice Binary: " + softdeviceStr + "!", None)

if not os.path.exists(bootloaderStr):
	utils.errorHandler("Missing Bootloader Binary: " + bootloaderStr + "!", None)	

#key to binary
key = jlink.make_datapage_bin(args.key, device)

utils.log(utils.LOG_LEVEL_DEBUG, "Make JLink Script parameters")
utils.log(utils.LOG_LEVEL_DEBUG, "Device: " + device)
utils.log(utils.LOG_LEVEL_DEBUG, "Softdevice: " + softdeviceStr)
utils.log(utils.LOG_LEVEL_DEBUG, "Bootloader: " + bootloaderStr)
utils.log(utils.LOG_LEVEL_DEBUG, "Bootloader Addr: " + bootloaderAddr)
if args.app:
	utils.log(utils.LOG_LEVEL_DEBUG, "Application: " + appStr)
	utils.log(utils.LOG_LEVEL_DEBUG, "Application Addr: " + appAddr)
utils.log(utils.LOG_LEVEL_DEBUG, "Datapage Addr: " + datapageAddr)
utils.log(utils.LOG_LEVEL_DEBUG, "Mac Address: " + str(binascii.b2a_hex(bytes(mac)[::-1]),"utf-8").upper())
utils.log(utils.LOG_LEVEL_DEBUG, "Private Key: " + str(binascii.b2a_hex(bytes(key)),"utf-8").upper())
utils.log(utils.LOG_LEVEL_DEBUG, "Disable Readback?: " + str(args.disablereadback))

script = jlink.make_script(device, softdeviceStr, bootloaderStr, bootloaderAddr,
	appStr, appAddr, datapageAddr, args.disablereadback)

jlink.make_uicr_bin(bootloaderBinaryAddr)
result = jlink.runJLink(script)
if result == False:
	utils.errorHandler("Jlink Programming Error!", jlink.cleanup)
jlink.cleanup()

#write log
logString = "mac: " + str(binascii.b2a_hex(bytes(mac)[::-1]),"utf-8").upper() + ", key: " + str(binascii.b2a_hex(bytes(key)),"utf-8").upper() + ", tag: " + args.tag + "\n"
with open(args.logfile,'a') as f: f.write(logString)

#script complete!
utils.log(utils.LOG_LEVEL_INFO, "Wrote log @ " + args.logfile + ": " + logString.strip() )
utils.log(utils.LOG_LEVEL_ERROR, "Programming completed successfully!")
