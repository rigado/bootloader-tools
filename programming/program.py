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


sys.path.append('../tools')
sys.path.append('../tools/jlink')
sys.path.append('../tools/nrfjprog')

from intelhex import IntelHex
from jlink import JLink
from nrfjprog import Nrfjprog
from utils import Utils
import configparser
import tupperware
import fnmatch

jlink = JLink()
nrfjprog = Nrfjprog()
utils = Utils()

ICVersionNRF51 = 1
ICVersionNRF52 = 6


def get_all_config_files(directory):

  if len(directory) == 0:
    directory = '.'

  #get all files in directory
  all_files = os.listdir(directory)

  #list to hold config files
  config_files = []

  #iterate over list of all files
  for file in all_files:
    
    #if this file matches the pattern .cfg
    if fnmatch.fnmatch(file, '*.cfg'):
      #split the path into the last section (short_file), and everything else (head)
      head, short_file = os.path.split(file) 

      short_file = "{0}{1}".format(directory, short_file)
      #add the file to the list of config files
      config_files.append(short_file)

  return config_files

def get_config_files_string(directory):

  #get all config files in a list, and convert that to a comma separated string
  config_file_string = '\n'.join(get_all_config_files(directory))

  #put instructions in front of the list of options
  prompt_string = 'Configuration file: {0}'.format(config_file_string)

  return prompt_string



####################
#script entry point#
####################

assert sys.version_info >= (3,0)

utils.log(utils.LOG_LEVEL_ERROR, '\nRigado Module Programming Tool\n-------------------------\n')

#parse the arguments
parser = argparse.ArgumentParser(description="Rigado Module Programmer")
parser.add_argument("-f",	"--family", type=str, help=get_config_files_string('config/'), default="")
parser.add_argument("-m", 	"--mac", type=str, help="MAC address (6 octets, big-endian)", default="")
parser.add_argument("-k", 	"--key", type=str, help="encryption key (16 bytes, big-endian)", default="00000000000000000000000000000000")
parser.add_argument("-t", 	"--tag", type=str, help="device tag for output log", default="noTag")
parser.add_argument("-sm", 	"--savemac", action="store_true", help="use the MAC written in module")
parser.add_argument("-r",	"--disablereadback", action="store_true", help="set to disable readback protection")
parser.add_argument("-R",	"--enablereadback", action="store_true", help="set to enable readback protection")
parser.add_argument("--logfile", type=str, help="log file output", default="log.txt")
parser.add_argument("-a",   "--app", type=str, help="program application binary")
parser.add_argument("-b",   "--bootloader", type=str, help="specify an alternative dfu image")
parser.add_argument("-v",   "--verbose", type=str, help="enable verbose output, available options from least to most are 0, 1, 2, 3, 4, 5")
args = parser.parse_args()

if args.verbose:
	try:
		logLevel = int(args.verbose)
		utils.setLogLevel(logLevel)
	except:
		utils.errorHandler("Verbosity level invalid: " + args.verbose)

if args.family == "":
	utils.errorHandler("Module processor family must be specified!", None)

#strip colons from mac/key input
args.mac = args.mac.replace(":","")
args.key = args.key.replace(":","")

#if application programming was specified, verify the binary exists
if args.app and len(args.app) != 0:
	if(os.path.exists(args.app) == False):
		utils.errorHandler("Application file missing: " + args.app + "!", None)

#validate input mac and key if available
if args.savemac == False and len(args.mac) != 12:
	utils.errorHandler('Invalid MAC Address; Expected length 12, received ' + str(len(args.mac)) + "!", None)

if len(args.key) != 32:
	utils.errorHandler('Invalid Key Length; Expected length 32, received ' + str(len(args.key)) + "!", None)

config = configparser.ConfigParser()
config_file = ''



if os.path.isfile(args.family.lower()):
	config_file = args.family.lower()
else:
	utils.errorHandler('Device not supported', None)


if os.path.exists(config_file):
	utils.log(utils.LOG_LEVEL_DEBUG, 'Config file exists')
else:
	utils.log(utils.LOG_LEVEL_DEBUG, 'Config file not found')

config.read(config_file)
cfg = tupperware.tupperware(config._sections)

if args.bootloader != None:
	cfg.bootloader.hex = args.bootloader

if cfg.readback_protect.default == 'True':
	readback_protection = True
else:
	readback_protection = False

if readback_protection and args.enablereadback:
	utils.log(utils.LOG_LEVEL_INFO, 'Warning: Readback protection already enabled by default. You can drop -R')
elif readback_protection == False and args.disablereadback == True:
	utils.log(utils.LOG_LEVEL_INFO, 'Warning: Readback protection already disabled by default. You can drop -r')

if args.enablereadback or \
  (args.key != '00000000000000000000000000000000' and \
   args.key != 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'):
	readback_protection = True

if args.disablereadback:
	readback_protection = False

ic = 0
rev = 0

device = cfg.device.name
jlink.set_speed(cfg.jlink.speed)
jlink.set_ic_address(cfg.ic.address)
jlink.set_rev_address(cfg.rev.address)
jlink.set_sd_address(cfg.softdevice.address)

jlink.set_page_size(cfg.datapage.length)
jlink.set_write_offset(cfg.datapage.offset)

if cfg.uicr.compatible == 'True':
	jlink.set_uicr_address(cfg.uicr.address)

if cfg.mac.compatible == 'True':
	jlink.set_mac_address(cfg.mac.address)

args.softdevice = cfg.softdevice.version

if device == '':
	utils.errorHandler("Unknown device family!")

if cfg.ic.compatible == 'True' and cfg.rev.compatible == 'True':
	try:
		ic, rev = jlink.read_ic_data(device)
	except:
		utils.errorHandler("Could not read IC type; is the JLink connected to the system?", jlink.cleanup)

	ic = int(ic)
	rev = int(rev)
	utils.log(utils.LOG_LEVEL_DEBUG, "IC " + str(ic))
	utils.log(2, 'Programming for {0}, Softdevice {1}'.format(cfg.device.name, cfg.softdevice.version))

else:
	utils.log(2, 'Programming for {0}'.format(cfg.device.name))

appStr = None
appAddrNeeded = False
appAddr = cfg.app.address
bootloaderStr = cfg.bootloader.hex
bootloaderAddr = cfg.bootloader.address
datapageAddr = cfg.datapage.address
bootloaderBinaryAddr = cfg.bootloader.binary_address
if cfg.softdevice.compatible == "True":
	softdeviceStr = cfg.softdevice.hex

blSettingsAddr = cfg.bootloader.settings_address


#see if we are preserving the mac
mac = None
if args.savemac:
	mac = jlink.make_mac_bin(None, device)
else:
	mac = jlink.make_mac_bin(args.mac, None)

if args.app:
	appStr = args.app

	#get size of app and create binary file
	filename, extension = os.path.splitext(args.app)
	appSize = 0
	if extension == '.hex':
		utils.deleteIfExists('temp.bin', None)
		ih = IntelHex(args.app)
		ih.tobinfile('temp.bin')
		appSize = os.path.getsize('temp.bin')
	else:
		appSize = os.path.getsize(args.app)
	jlink.make_bl_settings_bin(appSize)
	print(appSize)
	utils.deleteIfExists('temp.bin', None)
else:
	jlink.make_bl_settings_bin(0)

#validate existence of all necessary binary files; application validated earlier in script

if cfg.softdevice.compatible == 'True':
	if not os.path.exists(softdeviceStr):
		if args.softdevice != 'none':
			utils.errorHandler("Missing Softdevice Binary: " + softdeviceStr + "!", None)

if not os.path.exists(bootloaderStr):
	utils.errorHandler("Missing Bootloader Binary: " + bootloaderStr + "!", None)


#if the mac is stored seperately, only send the key
if cfg.mac.compatible == 'True':
	#key to binary
	key = jlink.make_datapage_bin(args.key, device)
#if the mac is stored in the datapage, send it along with the key
else:
	key, mac = jlink.make_datapage_bin(args.key, device, args.mac)

utils.log(utils.LOG_LEVEL_DEBUG, "Make JLink Script parameters")
utils.log(utils.LOG_LEVEL_INFO, "Device: " + device)

if cfg.softdevice.compatible == "True":
	utils.log(utils.LOG_LEVEL_INFO, "Softdevice: " + softdeviceStr)

utils.log(utils.LOG_LEVEL_INFO, "Bootloader: " + bootloaderStr)
utils.log(utils.LOG_LEVEL_INFO, "Bootloader Addr: " + bootloaderAddr)
if args.app:
	utils.log(utils.LOG_LEVEL_INFO, "Application: " + appStr)
	utils.log(utils.LOG_LEVEL_INFO, "Application Addr: " + appAddr)
utils.log(utils.LOG_LEVEL_INFO, "Datapage Addr: " + datapageAddr)
utils.log(utils.LOG_LEVEL_INFO, "Mac Address: " + str(binascii.b2a_hex(bytes(mac)[::-1]),"utf-8").upper())
utils.log(utils.LOG_LEVEL_INFO, "Private Key: " + str(binascii.b2a_hex(bytes(key)),"utf-8").upper())

if readback_protection:
	utils.log(utils.LOG_LEVEL_INFO, "Readback Protection On\n")
else:
	utils.log(utils.LOG_LEVEL_INFO, "Readback Protection Off\n")

if cfg.softdevice.compatible == 'False':
	softdeviceStr = ''

script = jlink.make_script(device, softdeviceStr, bootloaderStr, bootloaderAddr,
	appStr, appAddr, datapageAddr, blSettingsAddr, readback_protection)

jlink.make_uicr_bin(device, bootloaderBinaryAddr)
result = jlink.runJLink(script)
if result == False:
	utils.errorHandler("Jlink Programming Error!", jlink.cleanup)
jlink.cleanup()

if cfg.device.family == 'nrf51' or cfg.device.family == 'nrf52':
	if readback_protection:
		nrfjprog.protect(device)
	nrfjprog.reset(device)

#write log
logString = "mac: " + str(binascii.b2a_hex(bytes(mac)[::-1]),"utf-8").upper() + ", key: " + str(binascii.b2a_hex(bytes(key)),"utf-8").upper() + ", tag: " + args.tag + "\n"
with open(args.logfile,'a') as f: f.write(logString)

#script complete!
utils.log(utils.LOG_LEVEL_INFO, "Wrote log @ " + args.logfile + ": " + logString.strip() )
utils.log(utils.LOG_LEVEL_ERROR, "Programming completed successfully!")
