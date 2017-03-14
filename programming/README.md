Rigado Module Programmer
========================

This folder contains bootloader binaries, JLink programming scripts, and the main Python programming script, program.py.

## Requirements

The programming script requires Python 3.x.  The Segger JLink Tools are provided as part of the
bootloader-tools distribution.

## Script Usage

```
Rigado Module Programming Tool
-------------------------

usage: program.py [-h] [-f FAMILY] [-m MAC] [-k KEY] [-t TAG] [-sm] [-r] [-R]
                  [-v VERBOSE] [--logfile LOGFILE] [-a APP] [-b BOOTLOADER]

Rigado Module Programmer

optional arguments:
  -h, --help            show this help message and exit
  -f FAMILY, --family FAMILY
                        Configuration file: config/nrf52832-sd132v2.0.1.cfg
                        config/nrf52832-sd132v3.0.0.cfg
                        config/nrf52832-sd132v3.1.0.cfg
  -m MAC, --mac MAC     MAC address (6 octets, big-endian)
  -k KEY, --key KEY     encryption key (16 bytes, big-endian)
  -t TAG, --tag TAG     device tag for output log
  -sm, --savemac        use the MAC written in module
  -r, --disablereadback
                        set to disable readback protection
  -R, --enablereadback  set to enable readback protection
  -v VERBOSE, --verbose VERBOSE
                        enable verbose output, available options from least to
                        most are 0, 1, 2, 3, 4, 5
  --logfile LOGFILE     log file output
  -a APP, --app APP     program application binary
  -b BOOTLOADER, --bootloader BOOTLOADER
                        specify an alternative dfu image
```
  
### MAC Address Notes - nRF Based Modules

The nRF series does not have any permanent storage for non-volatile data.  However, the UICR allows for data that can only be changed by performing a full chip erase.  Rigado stores the MAC address in this location.  When the bootloader is programmed a full chip erase must be performed.  The programming script provides a mechanism for either saving the currently programmed MAC address or writing in a new one.  If the current MAC address is saved, the address will be read from the UICR, saved to disk, and then re-written to the UICR during programming.  If the MAC address in the UICR is set to all 0s or Fs, then the MAC address will be the factory assigned random public static address from the factory FICR.

The Rigado module MAC address is stored at `0x10001080`.

### Key Notes

The private key for a device is stored in the Rigado Bootloader storage area.  This key is used for decryption of application images during secure firmware updates.  If the key is not specified, then the bootloader will behave in an unsecure manner.  Unsecured behavior means that encryption of the application image is not required to use the bootloader.  This is equally true if a key of all `0`s or all `F`s is specified.

### Application Programming

The device application can be programmed at the same time as the bootloader.  This operation is performed by adding the `--app` option when running `program.py`.  The path to the application should be specified.

> IMPORTANT: The application binary must come from the build tools used to build the application and NOT the tools used to generate firmware update images (i.e. `genimage`).  Firmware update images contain extra data used by the bootloader.  If a firmware update image is programmed using program.py, it will not execute.

### Tags

During initial device manufacture, it can be useful to associate a MAC address to a particular device serial number.  This is particularly useful when the manufacturing process covers the MAC address of the Rigado module removing the ability to read it in a physical manner.  To create this mapping, the `--tag` option is used.  When a tag is specified, `program.py` will output, to `log.txt`, the MAC address, the private key, and the provided tag.

### Readback protection

As of release v3.0.0, readback protection is no longer enabled by default on any Rigado Module.  The bootloader will automatically enable readback protection if a key is set during programming.  In addition, `program.py` will autoatmically enable readback protection if a key is specified or if `-R` is supplied.  Note that due to this change, it is not possible to program a key and have readback protection disabled.  Since the bootloader firmware will enable it, even using `-r` does not get around this.  Rigado recommends enabling security as soon as possible.  In addition, `-r` is now the default option but is kept for backwards compatibility.
