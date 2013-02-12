# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cartridge import cart

class TestCartridge(unittest.TestCase):
    """Tests for Cartridge class."""

    MIN_ADDR = 0x0000
    MAX_ADDR = 0x7fff

    CART_TYPE_ADDR = 0x0147

    CART_TYPE_MBC1 = 1

    def test_set8_ofNegativeMBC1Address_raisesIndexError(self):
        cartridge = cart.Cartridge(self._newMBC1())
        with self.assertRaises(IndexError):
            cartridge.set8(self.MIN_ADDR - 1, 0)

    def _newMBC1(self):
        rom = []
        for i in range(0, 4):
            rom.extend([i for _ in range(self.MIN_ADDR, self.MAX_ADDR)])
        rom[self.CART_TYPE_ADDR] = self.CART_TYPE_MBC1
        return rom

    def test_set8_withOverflowAddress_raisesIndexError(self):
        cartridge = cart.Cartridge(self._newMBC1())
        with self.assertRaises(IndexError):
            cartridge.set8(self.MAX_ADDR + 1, 0)


if __name__ == '__main__':
    unittest.main()
