# Bootloader Tools
This repository provides access to various tools for using the Rigado Secure Bootloader.

The Rigado Secure Bootloader provides an encryption scheme allowing module users to secure their firmware image during over-the-air and serial-wire transfer. This method works by first installing a private 128-bit key on each device. The update images are then encrypted using the key for the device. After transfer of the encrypyted image, the image is decrypted on the device side and validated using a checksum. If all checks pass, the new firmware image is flashed to the application bank on the device.

The repository is organized in to two distinct support trees.

# SoftDevice S110 7.1.0 Tree (sd71)
This directory contains all files pertaining to the Rigado Secure DFU running on Softdevice S110 7.1.0.  The scripts and tools contained within this directory should be used for applications running on Softdevice S110 7.0 and 7.1.

# SoftDevice S110 8.0.0 Tree (sd8)
This directory contains all files pertaining to the Rigado Secure DFU running on SoftDevice S110 8.0.0.  The scripts and tools contained within this directory should be used for applications running on SoftDevice S110 8.0.

# Directory Structure
Both the sd71 and sd8 directory trees are very similar.  The following information describes each directory and its contents:

- Programming
  + This folder contains tools, scripts, and binaries for programming BMD-200 modules via a connected JLink programmer.

- OTA Image Tools
  + This folder contains tools for generating firmware update images including ecrypting images for secure data transfer.

- Update Tools
  + This folder contains scripts for performing Over-the-air and Serial updates.  Over-the-air Updates are currently only available for OS X and Linux systems that can run the Noble module for Node.js.
