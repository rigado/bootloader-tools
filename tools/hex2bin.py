import os
import argparse
import shutil
from intelhex import IntelHex

parser = argparse.ArgumentParser(description="IntexHEX to Binary Utility")
parser.add_argument("-i",	"--input", type=str, help="input file name")
parser.add_argument("-o", 	"--output", type=str, help="output file name", default="output.bin")
args = parser.parse_args()

if not args.input:
	print("Input file must be specified")

if os.path.exists(args.output):
	try:
		os.path.delete(args.output)
	except FileError as e:
		print("File error ({0}): {1}".format(e.errno, e.strerror))
	except:
		print("Filesystem Error!")

try:
	if(os.path.exists(args.input) == False):
		errorHandler("Application file missing!")
	
	filename, file_ext = os.path.splitext(args.input)
	#convert hex to bin
	if file_ext == ".hex":
		print("Convert HEX to Binary: " + args.input)
		ih = IntelHex(args.input)
		ih.tobinfile(args.output)
	else:
		print("File is not HEX type; aborting!")
except FileError as e:
	print("File error ({0}): {1}".format(e.errno, e.strerror))
except:
	errorHandler("Filesystem Error!")