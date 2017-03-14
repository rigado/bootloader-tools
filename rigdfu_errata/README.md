RigDFU v3.2.0 and v3.2.1 Errata
===============================

## Updating RigDFU v3.2.1 to another version renders device inoperable

### Background

This errata was discovered while testing the next version of the Rigado Bootloader, RigDFU.  The errata manifests when an OTA update of the bootloader and/or bootloader plus SoftDevice is performed.  This errata does not affect application firmware updates.  The Nordic S132 SoftDevice MBR requires some non-volatile swap memory to perform some operations.  This location of this non-volatile memory space is specified at a certain address in the UICR.  The Rigado factory programming tool does not properly specify this location due to lack of inclusion in the RigDFU v3.2.1 Intel HEX file.

### Workaround

Rigado has supplied an application update that corrects the UICR and loads an update of RigDFU to version.  This application is sent to the device using RigDFU and any associated tools.  After it is loaded, the bootloader will be upgraded to RigDFU v3.2.3.45.

## Updating SoftDevice to S132 v3.x.0 using RigDFU v3.2.0, v3.2.1, or v3.2.2 renders device inoperable

### Background

When a new SoftDevice is programmed, it may be larger (or smaller) than the previous SoftDevice.  In order to prepare the flash for the new SoftDevice's larger size, an offset must be added to the start of the SoftDevice image when it is transferred.  RigDFU v3.2.0, v3.2.1, and v3.2.2 do not properly calculate this offset.

### Workaround

Rigado has supplied an application update that corrects the UICR and loads an update of RigDFU to version.  This application is sent to the device using RigDFU and any associated tools.  After it is loaded, the bootloader will be upgraded to RigDFU v3.2.3.
