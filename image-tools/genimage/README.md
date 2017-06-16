Rigado DFU Image Generation Tool
================================

This tool is used to translate build output files (Intel HEX or binary formats) into
firmware update files that can then be tranferred over-the-air or via serial.

## Requirements

This tool requires Python 3.x.

## Script Usage

```
usage: genimage.py [-h] [--hexfile HEXFILE [HEXFILE ...]] [--output BIN]
                   [--quiet] [-f FAMILY] [--softdevice] [--bootloader]
                   [--application] [--softdevice-addr LOW-HIGH]
                   [--bootloader-addr LOW-HIGH] [--application-addr LOW-HIGH]

Generate images for RigDFU bootloader

optional arguments:
  -h, --help            show this help message and exit
  --hexfile HEXFILE [HEXFILE ...]
                        Hex file(s) to load
  --output BIN, -o BIN  Output file
  --quiet, -q           Print less output
  -f FAMILY, --family FAMILY
                        Configuration file: config/nrf52832-sd132v2.0.1.cfg
                        config/nrf52832-sd132v3.x.0.cfg

Images to include:
  If none are specified, images are determined automatically based on the
  hex file contents.

  --softdevice, -s      Include softdevice
  --bootloader, -b      Include bootloader
  --application, -a     Include application

Image locations in the HEX files:
  If unspecified, locations are guessed heuristically. Format is LOW-HIGH,
  for example 0x1000-0x16000 and 0x16000-0x3b000.

  --softdevice-addr LOW-HIGH, -S LOW-HIGH
                        Softdevice location
  --bootloader-addr LOW-HIGH, -B LOW-HIGH
                        Bootloader location
  --application-addr LOW-HIGH, -A LOW-HIGH
                        Application location
```

## Notes

* At least `--family (-f)`, '--output (-o)', and `--hexfile` must be specified.

* `genimage.py` will, in most cases, figure out the addresses as necessary provided the memory map as
  specified in the Rigado Bootloader documentation is used.  This means that generally, `-s`, `-b`, and
  `-a` are not required.
