Bootloader Tools
=========================

This repository provides access to various tools for using the Rigado Secure OTA Update.

The Rigado Secure OTA Update provides an encryption scheme allowing module users to secure
their firmware image during over the air transfer.  This method works by first installing
a private 128-bit key on each device.  The update images are then encrypted using the key 
for the device.  After transfer of the encrypyted image, the image is decrypted on the 
device side and validated using a checksum.  If all checks pass, the new firmware image is 
flashed to the application bank on the device.

Required Resources
------------------

The following resources are required:
* Total application image size of < 77 KB
* Total application storage space of < 4 KB
* Secure Bootloader requires 17 KB of storage space along with 4 KB for settings and information
storage (e.g. private key)

Application Setup
-----------------

The application must have an initial start location at 0x16000 which is currently the end of the
S110 soft device as of version 7.1.0.  Application settings are reserved at the start of memory
location 0x27000 and has as size of 4 KB (1 page on the nrf51822 256KB part).  The remainder of
flash memory is used for swap space storage and the bootloader.

Memory Organization Table
-------------------------

* 0x00000 - 0x15FFF: S110 Soft Device v7.1.0
* 0x16000 - 0x26FFF: User Application
* 0x27000 - 0x27FFF: User Application storage
* 0x28000 - 0x3A7FF: Bootloader swap space
* 0x3A800 - 0x3F7FF: Secure Bootloader
* 0x3F800 - 0x3FBFF: Secure Bootloader settings
* 0x3FC00 - 0x3FFFF: Rigado storage for bootloader data

Setup for a blank module
------------------------

To flash the bootloader and soft device to a blank module, a few tools are provided.

Windows
-------

1. Install the following tools:
    * Python 2.7.x for Windows
        + https://www.python.org/downloads/
    * Segger J-Link software & documentation pack for windows
        + https://www.segger.com/jlink-software.html
	
2. Add Python 2.7.X and Segger J-Link to your path.
3. Run the installer batch file:
    * flashall.bat mac_address private_key

OS X and Linux
--------------

WIP
