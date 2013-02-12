# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

from pygme.memory import array

class GBRAM:
    """
    Concrete implementation of Gameboy RAM.
    """

    ROM_START = 0x0000
    RAM_START = 0x8000

    def __init__(self):
        self._ram = array.Array(1 << 15)

    def get8(self, addr):
        self._assertNotCartridge(addr)
        return self._ram.get8(addr - self.RAM_START)

    def _assertNotCartridge(self, addr):
        if self.ROM_START <= addr < self.RAM_START:
            raise IndexError("Can't access Cartridge data")
