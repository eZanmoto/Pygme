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

    def test_set8_accessingCartridge_raisesException(self):
        for addr in range(0x0000, 0x8000):
            with self.assertRaises(IndexError):
                self._mem.set8(addr, 0)

    def test_set8_accessingRAM_isSuccessful(self):
        for addr in range(0x8000, 0x10000):
            self._mem.set8(addr, 0)

    def test_set8_withNegativeAddress_raisesException(self):
        with self.assertRaises(IndexError):
            self._mem.set8(0x0000 - 1, 0)

    def test_set8_withOverflowAddress_raisesException(self):
        with self.assertRaises(IndexError):
            self._mem.set8(0xffff + 1, 0)

    def test_set8_withNegativeValue_raisesException(self):
        with self.assertRaises(ValueError):
            self._mem.set8(0x8000, -1)

    def test_set8_withByteValue_isSuccessful(self):
        for val in range(0x00, 0x100):
            self._mem.set8(0x8000, val)

    def test_set8_withOverflowValue_raisesException(self):
        with self.assertRaises(ValueError):
            self._mem.set8(0x8000, 0x100)

    def test_get8_withSetMemoryAddress_getsCorrectData(self):
        for addr in [0x8000, 0xffff]:
            self._expect8(addr, 0x00)
            for val in [0x00, 0xff]:
                self._mem.set8(addr, val)
                self._expect8(addr, val)

    def _expect8(self, addr, v):
        b = self._mem.get8(addr)
        self.assertEquals(b, v, "Expected 0x%02x(%d), got 0x%02x(%d) at 0x%x" %
                          (v, v, b, b, addr))

    def tearDown(self):
        self._mem = None


if __name__ == '__main__':
    unittest.main()
