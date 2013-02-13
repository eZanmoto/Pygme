# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cartridge import cart

MIN_ADDR = 0x0000
HEADER_END_ADDR = 0x0150

CART_TYPE_MBC1 = 1

class TestCartridge(unittest.TestCase):
    """Tests for Cartridge class."""

    def test_set8_ofNegativeMBC1Address_raisesIndexError(self):
        cartridge = cart.Cartridge(self._newMBC1())
        with self.assertRaises(IndexError):
            cartridge.set8(MIN_ADDR - 1, 0)

    def _newMBC1(self):
        rom = []
        for i in range(0, 4):
            rom.extend([i for _ in range(MIN_ADDR, cart.MAX_ADDR)])
        rom[cart.CART_TYPE_ADDR] = CART_TYPE_MBC1
        return rom

    def test_set8_withOverflowAddress_raisesIndexError(self):
        cartridge = cart.Cartridge(self._newMBC1())
        with self.assertRaises(IndexError):
            cartridge.set8(cart.MAX_ADDR + 1, 0)

    def test_set8_ofMBC1FourthQuarter_setsMode(self):
        cartridge = cart.Cartridge(self._newMBC1())
        self.assertEquals(cartridge.getMode(), 0)
        for addr in [0x0000, 0x1fff, 0x2000, 0x3fff, 0x4000, 0x5fff]:
            cartridge.set8(addr, 1)
            self.assertEquals(cartridge.getMode(), 0)
        for addr in [0x6000, 0x7fff]:
            cartridge.set8(addr, 0b11)
            self.assertEquals(cartridge.getMode(), 1)
            cartridge.set8(addr, 0b10)
            self.assertEquals(cartridge.getMode(), 0)
            cartridge.set8(addr, 0b01)
            self.assertEquals(cartridge.getMode(), 1)
            cartridge.set8(addr, 0b00)
            self.assertEquals(cartridge.getMode(), 0)

    def test_set8_ofROMFourthQuarter_raisesRuntimeError(self):
        cartridge = cart.Cartridge(self._newROM())
        with self.assertRaises(RuntimeError):
            cartridge.set8(0x6000, 0)

    def _newROM(self):
        return [0 for _ in range(MIN_ADDR, cart.MAX_ADDR + 1)]

    def test_set8_ofMBC1SecondQuarter_setsBank(self):
        cartridge = cart.Cartridge(self._newMBC1())
        self.assertEquals(cartridge.getBank(), 1)
        for addr in [0x0000, 0x1fff, 0x4000, 0x5fff, 0x6000, 0x7fff]:
            cartridge.set8(addr, 0x1f)
            self.assertEquals(cartridge.getBank(), 1)
        for addr in [0x2000, 0x3fff]:
            cartridge.set8(addr, 0x00)
            self.assertEquals(cartridge.getBank(), 1)
            cartridge.set8(addr, 0x1f)
            self.assertEquals(cartridge.getBank(), 31)
            cartridge.set8(addr, 0x01)
            self.assertEquals(cartridge.getBank(), 1)
            cartridge.set8(addr, 0x22)
            self.assertEquals(cartridge.getBank(), 2)
            cartridge.set8(addr, 0x00)
            self.assertEquals(cartridge.getBank(), 1)

    def test_set8_ofROMSecondQuarter_raisesRuntimeError(self):
        cartridge = cart.Cartridge(self._newROM())
        with self.assertRaises(RuntimeError):
            cartridge.set8(0x2000, 0)

    def test_get8_ofMBC1FirstHalf_doesntChangeWithBanking(self):
        cartridge = cart.Cartridge(self._newMBC1())
        for addr in range(HEADER_END_ADDR, (cart.MAX_ADDR + 1) / 2):
            val = cartridge.get8(addr)
            self.assertEquals(val, 0, "ROM[0x%04x] = 0x%02x, expected 0x%02x" %
                    (addr, val, 0))

if __name__ == '__main__':
    unittest.main()
