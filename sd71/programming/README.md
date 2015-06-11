# Bootloader Programming

This folder contains bootloader binaries, JLink programming scripts, and the main Python programming script, program.py.

## Requirements

The programming script requires Python 3.x and the Segger JLink tools.

## Script Usage

```
usage: program.py [-h] [-m MAC] [-k KEY] [-t TAG] [-sm] [--verbose]
                  [--logfile LOGFILE] [-a]

BMD-200 Programmer
required arguments:
  -m MAC, --mac MAC  MAC address (6 octets, big-endian)
         or
  -sm, --savemac     use the MAC written in the module
optional arguments:
  -h, --help         show this help message and exit
  -k KEY, --key KEY  encryption key (16 bytes, big-endian)
  -t TAG, --tag TAG  device tag for output log
  --verbose          enable verbose output
  --logfile LOGFILE  log file output
  -a, --app          program application binary (application.bin)
```
  
### MAC Address Notes

The nRF series does not have any permanent storage for non-volatile data.  However, the UICR allows for data that can only be changed by performing a full chip erase.  Rigado stores the MAC address in this location.  When the bootloader is programmed a full chip erase must be performed.  The programming script provides a mechanism for either saving the currently programmed MAC address or writing in a new one.  If the current MAC address is saved, the address will be read from the UICR, saved to disk, and then re-written to the UICR during programming.  If the MAC address in the UICR is set to all 0s or Fs, then the MAC address will be the factory assigned random public static address from the factory FICR.

The Rigado module MAC address is stored at 0x10001080.

### Key Notes

The private key for a device is stored in the Rigado Bootloader storage data at 0x3FC00.  This key is used for decryption of application images during secure OTA updates.  If the key is not specified, then the bootloader will behave in an unsecure manner.  This means that no encryption of the application image is necessary to use the bootloader.  This is equally true if a key of all 0s or all Fs is specified.

### Application Programming

The device application can be programmed at the same time as the bootloader.  This operation is performed by adding the '-a' option when running program.py.  To program the application, put the application binary in the same folder as program.py (this folder), and rename to application.bin.  If the binary is not named application.bin, then it will not be flashed to the device.

> IMPORTANT: The application binary must come from the build tools used to build the application and NOT the tools used to generate firmware update images.  Firmware update images contain extra data used by the bootloader.  If a firmware update image is programmed using program.py, it will not run properly.

### Tags

During initial device manufacture, it can be useful to associate a MAC address to a particular device serial number.  This is particularly useful when the manufacturing process covers the MAC address of the BMD-200 removing the ability to read it in a physical manner.  To create this mapping, the -t or --tag option is used.  When a tag is specified, program.py will output, to log.txt, the MAC address, the private key, and the provided tag.
