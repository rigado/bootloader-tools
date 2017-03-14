#!/usr/bin/python

'''
  Tool to build RigDfu firmware images from hex files
  
  @copyright (c) Rigado, LLC. All rights reserved.

  Source code licensed under BMD-200 Software License Agreement.
  You should have received a copy with purchase of BMD-200 product.
  If not, contact info@rigado.com for for a copy. 
'''

import sys
import struct

sys.path.append('../../')
sys.path.append('../../tools')
sys.path.append('../common')

import ihex
from intelhex import IntelHex
from utils import Utils
from imageutils import *
from multihexfile import MultiHexFile
from rigdfugen import RigDfuGen
from rigdfugen import RigError
import tupperware
import configparser
import os
import fnmatch

utils = Utils()

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

#"Configuration file (nrf52832-sd132v2.0.1.cfg nrf52832-sd132v3.x.0.cfg)""

if __name__ == "__main__":
    import argparse

    description = "Generate images for RigDFU bootloader"
    parser = argparse.ArgumentParser(description = description)

    parser.add_argument("--hexfile", metavar = "HEXFILE", nargs = "+",
                        help = "Hex file(s) to load")

    parser.add_argument("--output", "-o", metavar = "BIN",
                        help = "Output file")
    parser.add_argument("--quiet", "-q", action = "store_true",
                        help = "Print less output")

    parser.add_argument("-f", "--family", type=str, help=get_config_files_string('config/'), default="")

    group = parser.add_argument_group(
        "Images to include",
        "If none are specified, images are determined automatically based "
        "on the hex file contents.")
    group.add_argument("--softdevice", "-s", action = "store_true",
                       help = "Include softdevice")
    group.add_argument("--bootloader", "-b", action = "store_true",
                       help = "Include bootloader")
    group.add_argument("--application", "-a", action = "store_true",
                       help = "Include application")

    group = parser.add_argument_group(
        "Image locations in the HEX files",
        "If unspecified, locations are guessed heuristically.  Format "
        "is LOW-HIGH, for example 0x1000-0x16000 and 0x16000-0x3b000.")
    group.add_argument("--softdevice-addr", "-S", metavar="LOW-HIGH",
                       help = "Softdevice location")
    group.add_argument("--bootloader-addr", "-B", metavar="LOW-HIGH",
                       help = "Bootloader location")
    group.add_argument("--application-addr", "-A", metavar="LOW-HIGH",
                       help = "Application location")

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config_file = ''
    constructed_config = ''

    if os.path.isfile(args.family.lower()):
        config_file = args.family.lower()
    else:
        utils.errorHandler('Device not supported', None)

    config.read(config_file)
    cfg = tupperware.tupperware(config._sections)

    if not args.output:
        parser.error("must specify --output file")

    def parse_addr(s):
        if not s:
            return None
        (l, h) = s.split('-')
        return (int(l, 0), int(h, 0))

    try:
        rigdfugen = RigDfuGen(inputs = args.hexfile,
                              sd = args.softdevice,
                              bl = args.bootloader,
                              app = args.application,
                              sd_addr = parse_addr(args.softdevice_addr),
                              bl_addr = parse_addr(args.bootloader_addr),
                              app_addr = parse_addr(args.application_addr),
                              config = cfg,
                              verbose = not args.quiet)
        img = rigdfugen.gen_image()
        with open(args.output, "wb") as f:
            f.write(rigdfugen.gen_image())
        if not args.quiet:
            sys.stderr.write("Wrote %d bytes to %s\n" % (len(img), args.output))
    except RigError as e:
        sys.stderr.write("Error: %s\n" % str(e))
        raise SystemExit(1)
