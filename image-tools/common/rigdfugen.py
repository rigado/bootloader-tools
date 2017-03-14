import sys
import struct

sys.path.append('../../tools')

from imageutils import *
from multihexfile import MultiHexFile
from utils import Utils

class RigError(Exception):
    pass

class RigDfuGen(object):

    def __init__(self, inputs, sd, bl, app, sd_addr, bl_addr, app_addr, config,
                 verbose = True):
        """Parse hex files for image data.

        inputs: a list of hex files to load.

        sd, bl, app: If any are True, include
           them in the image.  If all are False, determine which ones
           to include in the image based on what's found in the input
           files.

        sd_addr, bl_addr, app_addr: tuples containing fixed (min, max)
           addresses to use for each of the 3 segments, rather than
           searching.  Data is (max-min) bytes starting at min.
        """
        self.inputs = inputs
        self.sd = sd
        self.bl = bl
        self.app = app
        self.sd_addr = sd_addr
        self.bl_addr = bl_addr
        self.app_addr = app_addr
        self.cfg = config
        self.verbose = verbose

        self.data = MultiHexFile(inputs, pad = 0xff)

        self.find_sd()
        self.find_bl()
        self.find_app()

        search = False
        if not (self.sd or self.bl or self.app):
            # Guess which ones are present based on addresses we have
            search = True

        def check(which, flag, addr):
            if getattr(self, flag) or (search and getattr(self, addr)):
                setattr(self, flag, True)
                a = getattr(self, addr)
                if not a:
                    raise RigError("Want %s, but can't find it" % which)
                if self.verbose:
                    sys.stderr.write("%12s: 0x%05x - 0x%05x (%d bytes)\n"
                                     % (which, a[0], a[1], a[1] - a[0]))

        # Make sure we have addresses for everything we want to write
        check("Softdevice", 'sd', 'sd_addr')
        check("Bootloader", 'bl', 'bl_addr')
        check("Application", 'app', 'app_addr')

        if not (self.sd or self.bl or self.app):
            raise RigError("No softdevice, bootloader, or application found")

        if self.app and (self.sd or self.bl):
            raise RigError("Unsupported image combination; application must be "
                           "updated alone")

    def to_int(self, val):
        return int(val, 16)

    def gen_image(self):
        """Generate output image, returning it as a byte stream"""
        sd_data = self.data.extract(*self.sd_addr) if self.sd else b''
        bl_data = self.data.extract(*self.bl_addr) if self.bl else b''
        app_data = self.data.extract(*self.app_addr) if self.app else b''
        header = struct.pack('<3I', len(sd_data), len(bl_data), len(app_data))
        iv = int2byte(0) * 16
        tag = int2byte(0) * 16
        data = sd_data + bl_data + app_data
        return header + iv + tag + data

    def find_sd(self):
        if self.cfg.softdevice.compatible == "False":
            return False
        """Look for a Softdevice"""
        if self.sd_addr:
            return True
        # Must have data starting at 0x1000 to at least 0x300c
        cfg_min = self.to_int(self.cfg.softdevice.min_address)
        cfg_max = self.to_int(self.cfg.softdevice.max_address)
        (minaddr, maxaddr) = self.data.extents(cfg_min, cfg_max)
        if minaddr != cfg_min:
            return False
        if maxaddr != cfg_max:
            return False
        # Size is stored at 0x3008
        end = self.data.uint32le(self.to_int(self.cfg.softdevice.size_address))
        # Valid code has to exist
        if not self.valid_code(cfg_min, end):
            return False
        # Address of SD is the extent of valid code in its size
        self.sd_addr = (cfg_min, self.data.extents(cfg_min, end)[1])
        return True

    def find_bl(self):
        if self.cfg.softdevice.compatible == "False":
            return False
        """Look for a bootloader"""
        found = False
        max_extent = 0
        if self.bl_addr:
            return True
        size = self.to_int(self.cfg.device.page_size)
        cfg_bl_min = self.to_int(self.cfg.bootloader.min_address)
        cfg_bl_max = self.to_int(self.cfg.bootloader.max_address)
        (minaddr, maxaddr) = self.data.extents(cfg_bl_min, cfg_bl_max)
        max_extent = cfg_bl_max
        if minaddr is None:
            return False

        for addr in range(minaddr, maxaddr, size):
            if self.valid_code(addr, maxaddr):
                found = True
                break

        if not found:
            return False

        # Address of BL is the extent of valid code we found
        self.bl_addr = self.data.extents(addr, max_extent)
        
        return True

    def find_app(self):
        """Look for an application"""
        if self.app_addr:
            return True

        cfg_app_min = self.to_int(self.cfg.app.min_address)
        cfg_app_max = self.to_int(self.cfg.app.max_address)
        cfg_sd_min = self.to_int(self.cfg.softdevice.min_address)
        cfg_sd_max = self.to_int(self.cfg.softdevice.max_address)
        cfg_end_offset = self.to_int(self.cfg.softdevice.end_offset)
        cfg_page_size = self.to_int(self.cfg.device.page_size)

        (minaddr, maxaddr) = (cfg_app_min, cfg_app_max)
        # If we have a bootloader, we know the app must end before it
        if self.bl_addr:
            maxaddr = self.bl_addr[0]
        # If we have a softdevice, it tells us where the app starts.
        if self.sd_addr:
            sd_end = self.data.uint32le(self.sd_addr[0] + cfg_end_offset)
            if sd_end > cfg_sd_min and sd_end < cfg_sd_max:
                minaddr = sd_end
        (minaddr, maxaddr) = self.data.extents(minaddr, maxaddr, cfg_page_size)

        if minaddr is None:
            return False
        for addr in range(minaddr, maxaddr, cfg_page_size):
            if self.valid_code(addr, maxaddr):
                break
        else:
            return False
        # Address of app is the extent of valid code we found
        self.app_addr = self.data.extents(addr, maxaddr)
        return True

    def valid_code(self, minaddr, maxaddr):
        """Return True if the initial SP and reset values provided
        correspond to a valid application residing between 'minaddr'
        and 'maxaddr'"""
        initial_sp = self.data.uint32le(minaddr + 0);
        reset = self.data.uint32le(minaddr + 4);
        # unaligned?
        if (initial_sp % 4) != 0:
            return False
        # invalid SP?
        cfg_min_sp = self.to_int(self.cfg.device.min_stack_pointer)
        cfg_max_sp = self.to_int(self.cfg.device.max_stack_pointer)
        if initial_sp < cfg_min_sp or initial_sp > cfg_max_sp:
            return False
        # non-thumb reset vector?
        if (reset % 2) != 1:
            return False
        # reset vector pointing outside address range?
        if reset < minaddr or reset >= maxaddr:
            return False
        return True