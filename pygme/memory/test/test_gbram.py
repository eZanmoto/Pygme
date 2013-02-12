# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.memory import gbram

class TestGBRAM(unittest.TestCase):

    numTests = 10

    def setUp(self):
        self._mem = gbram.GBRAM()

    def test_get8_accessingCartridge_raisesException(self):
        for addr in range(0x0000, 0x8000):
            with self.assertRaises(IndexError):
                self._mem.get8(addr)

    def test_get8_accessingRAM_isSuccessful(self):
        for addr in range(0x8000, 0x10000):
            self._mem.get8(addr)

    def test_get8_withNegativeAddress_raisesException(self):
        with self.assertRaises(IndexError):
            self._mem.get8(0x0000 - 1)

    def test_get8_withOverflowAddress_raisesException(self):
        with self.assertRaises(IndexError):
            self._mem.get8(0xffff + 1)

    def tearDown(self):
        self._mem = None


if __name__ == '__main__':
    unittest.main()
