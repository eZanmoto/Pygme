# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class Cartridge:
    """Provides access to the ROM of a Gameboy cartridge."""

    MAX_ADDR = 0x7fff

    def __init__(self, rom):
        self._rom = rom

    def set8(self, addr, val):
        self._chkAddr(addr)

    def _chkAddr(self, addr):
        if addr < 0 or addr > self.MAX_ADDR:
            raise IndexError( "Address (0x%x) is out of range [0x0-0x%x]"
                % (addr, self.MAX_ADDR))
