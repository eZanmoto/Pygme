# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.memory import array

class TestArray(unittest.TestCase):

    numTests = 10

    def setUp(self):
        self.mem = array.Array(0x1000)

    def test_change(self):
        for addr in [0, self.mem.size() - 1]:
            self.expect8(addr, 0)
            self.mem.set8(addr, 0xba)
            self.expect8(addr, 0xba)

    def test_get8_minAddr(self):
        self.mem.get8(0)
        with self.assertRaises(IndexError):
            self.mem.get8(-1)

    def test_get8_maxAddr(self):
        self.mem.get8(self.mem.size() - 1)
        with self.assertRaises(IndexError):
            self.mem.get8(self.mem.size())

    def test_set8_minAddr(self):
        self.mem.set8(0, 0)
        with self.assertRaises(IndexError):
            self.mem.set8(-1, 0)

    def test_set8_maxAddr(self):
        self.mem.set8(self.mem.size() - 1, 0)
        with self.assertRaises(IndexError):
            self.mem.set8(self.mem.size(), 0)

    def test_set8_minVal(self):
        self.mem.set8(0, 0)
        with self.assertRaises(ValueError):
            self.mem.set8(0, -1)

    def test_set8_maxVal(self):
        self.mem.set8(0, 0xff)
        with self.assertRaises(ValueError):
            self.mem.set8(0, 0x100)

    def expect8(self, addr, v):
        b = self.mem.get8(addr)
        self.assertEquals(b, v, "Expected 0x%02x(%d), got 0x%02x(%d) at 0x%x"
            % (v, v, b, b, addr))

    def tearDown(self):
        self.mem = None


if __name__ == '__main__':
    unittest.main()
