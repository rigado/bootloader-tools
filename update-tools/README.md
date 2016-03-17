#Update Tools

This folder contains tools for performing application firmware updates.  Two types of update are supported depending on the development system.  On Windows, only wired serial updates are available.  On OS X and Linux, with Bluetooth 4.0 hardware, both wired serial and Bluetooth Low Energy OTA updates are supported.  The BLE interface is provided by the Node.js module [Noble](https://github.com/sandeepmistry/noble).

##Bluetooth Low Energy (ble) Folder

The BLE folder contains two scripts: dfu.js and monitor.js.

### Monitor.js

Monitor.js is a Node.js script which provides a simple utility to scan for BLE devices in the area.  The device list can be filtered by invoking the script with the name of the device of interest.

For example, if the script is run with no parameters:
```
  sudo node monitor.js
```
The script will output all devices found.

However, if instead a device name is supplied:
```
  sudo node monitor.js RigDfu
```
The output will be filtered to only devices that advertise the name RigDfu.  RigDfu is the advertising name of the Rigado Bootloader.

### Dfu.js

Dfu.js is a Node.js script that interacts with the Rigado Bootloader to perform OTA updates.  Both unencrypted and encrypted OTA updates are supported by this script.  Additionally, the script can support setting the key on a device that currently has no key.  This is useful for when device provisioning is performed post manufacture.  For more details on the usage of this script, check out [README.md](https://github.com/rigado/bootloader-tools/tree/combined/sd8/update-tools/ble) in the ble folder.

## Serial Folder

The serial folder contains the Python script dfu.py.  This script is used to perform application firmware updates via a wired serial port.  The required serial port parameters are:

| Setting | Value |
|---------|:---------:|
| Baud Rate | 115200 |
| Data Bits | 8 |
| Stop Bits | 1 |
| Parity | Off |
| Flow Control | None |

For more information on this script, check out README.md in the Serial folder.
