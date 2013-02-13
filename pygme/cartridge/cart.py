# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class Cartridge:
    """Provides access to the ROM of a Gameboy cartridge."""

    MAX_ADDR = 0x7fff

    MODE_SWITCH_ADDR = 0x6000
    BANK_SWITCH_ADDR = 0x2000

    CART_TYPE_ADDR = 0x0147

    CART_TYPE_ROM_ONLY = 0

    def __init__(self, rom):
        self._rom = rom
        self._cartType = self._rom[self.CART_TYPE_ADDR]
        self._mode = 0
        self._bank = 1

    def set8(self, addr, val):
        self._chkAddr(addr)
        if addr >= self.MODE_SWITCH_ADDR:
            self._switchMode(val)
        elif addr >= 0x4000:
            pass
        elif addr >= self.BANK_SWITCH_ADDR:
            self._switchBank(val)

    def _chkAddr(self, addr):
        if addr < 0 or addr > self.MAX_ADDR:
            raise IndexError( "Address (0x%x) is out of range [0x0-0x%x]"
                % (addr, self.MAX_ADDR))

    def _switchMode(self, val):
        if self._cartType == self.CART_TYPE_ROM_ONLY:
            raise RuntimeError("Mode can't be changed of ROM ONLY cartridge")
        self._mode = val & 1

    def _switchBank(self, val):
        if self._cartType == self.CART_TYPE_ROM_ONLY:
            raise RuntimeError("Bank of ROM ONLY cartridge can't be changed")
        self._bank = 1 if val == 0 else val & 0x1f

    def getMode(self):
        return self._mode

    def getBank(self):
        return self._bank
