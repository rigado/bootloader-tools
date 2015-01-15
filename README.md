Bootloader Tools
=========================

This repository provide access to various tools for using the Rigado Secure OTA Update.

The Rigado Secure OTA Update provides an encryption scheme allowing module users to secure
their firmware image during over the air transfer.  This method works by first installing
a private 128-bit key on each device.  The update images are then encrypted using the key 
for the device.  After transfer of the encrypyted image, the image is decrypted on the 
device side and validated using a checksum.  If all checks pass, the new firmware image is 
flashed to the application bank on the device.

Required Resources
------------------

The following resources are required:
* Total Image size of < 77 KB
* Total application storage space of < 4 KB
* Secure Bootloader requires 22 KB of storage space along with 4 KB for settings and information
storage (e.g. private key)

Setup
-----