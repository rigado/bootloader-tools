import sys
import struct
from imageutils import *

sys.path.append('../../tools')

import ihex

class MultiHexFile(object):
    """Some tools to help manage multiple hex files and pull padded regions of
    data out of them."""
    def __init__(self, hexfiles, pad):
        self.data = ihex.IHex();
        for hexfile in hexfiles:
            ih = ihex.IHex.read_file(hexfile)
            # Combine new file with self.data
            for start, data in sorted(ih.areas.items()):
                end = start + len(data)
                if start == end:
                    continue
                # Check for overlap
                for ostart, odata in sorted(self.data.areas.items()):
                    oend = ostart + len(odata)
                    if start < oend and end >= ostart:
                        # Don't complain if the overlapping data is the same
                        if start == ostart and end == oend and data == odata:
                            continue
                        raise RigError(("data region [%x-%x] in %s "
                                        "overlaps earlier data") %
                                       (start, end, hexfile))
                self.data.insert_data(start, data)

    def extents(self, minaddr, maxaddr, round = 4):
        """Return a tuple containing the extents of data that are
        present between 'minaddr' and 'maxaddr'.  Addresses are
        rounded to 'round' bytes."""
        ext_min = None
        ext_max = None
        for start, data in sorted(self.data.areas.items()):
            end = start + len(data)
            if minaddr < end and ext_min is None:
                ext_min = max(minaddr, start)
            if maxaddr > start and ext_min is not None:
                ext_max = min(maxaddr, end)
        if ext_min is None or ext_max is None:
            return (None, None)
        def round_down(x, n):
            return x - (x % n)
        ext_min = round_down(ext_min, round)
        ext_max = round_down(ext_max + (round - 1), round)
        return (ext_min, ext_max)

    def extract(self, minaddr, maxaddr, pad = 0xff):
        """Return all data in the specified range, padding missing values"""
        buf = b''
        addr = minaddr
        for start, data in sorted(self.data.areas.items()):
            end = start + len(data)
            if addr > end:
                continue
            if maxaddr <= start:
                continue
            if addr < start:
                buf += int2byte(pad) * (start - addr)
                addr = start
            if end > maxaddr:
                end = maxaddr
            buf += data[addr-start:end-start]
            addr = end
        buf += int2byte(pad) * (maxaddr - addr)
        return buf

    def uint32le(self, addr):
        return struct.unpack("<I", self.extract(addr, addr+4))[0]