# Bootloader Tools Version 2.0

## Highlights

### New Bootloader Binaries
This release includes updated bootloader binaires.  The SoftDevice S110 version
has received a few changes.  In addition, bootloader binaires are now available
for S130 and S132 both version 2.0.0.  These are built using the latest SDK
release from Nordic.

### New Service UUID
The S130 and S132 binaries used a different UUID.  This is to differentiate
them from the S110 version.  Note that the S110, S130, and S132 versions
behave essential the same.

### User Data Location Changed
To ensure default pstorage driver settings can be used, the S130 and S132
versions of the bootloader have had their User storage location moved to
just after the Bootloader swap space.  Please see the Memory Layout in the
documentation for further details.

### New Programming Options
The programming script (program.py) has undergone a few significant changes.
It no longer relies on pre-written JLink script files and instead generates
the JLink script files on the fly.  This allows us to more easily add support
in the future.  

In addition, the `-a` option for programming application binaires now expects 
a path.  The input file can now be a HEX file or a binary file.

A option, `-r` has been added to program.py to disable readback protection.  This
eases debugging efforts.  *HOWEVER*, this option should *ONLY* be used for
development purposes.  If it is used during factory programming, readback
protection will be disabled and your firmware WILL be a risk for theft.  In
addition, the security part of the bootloader will be useless as the private
key can easily be read out of the device.  Use at your own *RISK*.

Finally, the SoftDevice version can now be specified with the `-s` option.
The available options are `-s 110`, `-s 130`, and `-s 132`.  If this option is
not specified, programming will default to `110` on the BMD-200 and `132` on
the BMD-300.  The programming script verifies the IC before starting programming.
If a conflict occurs, the default option will be used.

### New Bootloader Features
Bootloader version information is now available at a static location within
the bootloader binary.  See the documentation for more details.  The src folder 
of this repository contains C files to help in gathering this information.

### Upcoming features
Tired of slow OTA updates?  Make a patch!  Instead of sending the whole
firmware image, a patch is simply the difference between a previous firmware
version and the latest firmware version.  The patch generation tools will
be available on Rigdo's webiste.  Rigablue will be updated to support the
patching feature once it is ready.

### SoftDevice S110 7.1 Support removed
SoftDevice S110 7.x support has been removed from this release.  It will reamin
available for the previous release of bootloader-tools.  Due to this, the
folder structure for bootloader tools has been condensed into one tree.
