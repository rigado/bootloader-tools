# Bootloader Tools
This repository provides access to various tools for using the Rigado Secure OTA Update.

The Rigado Secure OTA Update provides an encryption scheme allowing module users to secure their firmware image during over the air transfer. This method works by first installing a private 128-bit key on each device. The update images are then encrypted using the key for the device. After transfer of the encrypyted image, the image is decrypted on the device side and validated using a checksum. If all checks pass, the new firmware image is flashed to the application bank on the device.

The repository is organized in to two distinct support trees.

# Softdevice 7.1.0 Tree (sd71)
This directory contains all files pertaining to the Rigado Secure DFU running on Softdevice 7.1.0.  The scripts and tools contained within this directory should be used for applications running on Softdevice 7.0 and 7.1.

# Softdevice 8.0.0 Tree (sd8)
This directory contains all files pertaining to the Rigado Secure DFU running on Sfotdevice 8.0.0.  The scripts and tools contained within this directory should be used for applications running on Softdevice 8.0.

# Directory Structure
Both the SD71 and SD8 directory trees are extremely similar.  The following information describes each directory and its contents.

- Programming
    - This folder contains tools, scripts, and binaries for programming BMD-200 modules via a connected JLink programmer.

- OTA Image Tools
  + This folder contains tools for generating Over-the-air update images including ecrypting images for secure data transfer.

- Update Tools
  + This folder contains scripts for performing Over-the-air and Serial updates.  Over-the-air Updates are currently only available for OS X and Linux systems that can run the Noble module for Node.js.
