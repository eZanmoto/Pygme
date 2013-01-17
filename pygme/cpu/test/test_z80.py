# Copyright 2013 Sean Kelleher. All rights reserved.

import unittest

from pygme.cpu import z80

class TestZ80(unittest.TestCase):

    def setUp(self):
        self.z80 = z80.Z80()

    def test_nop(self):
        self.validOpc("NOP", 0, self.z80.nop)
        for _ in range(1, 10):
            m = self.z80.m
            t = self.z80.t
            self.z80.nop()
            self.regEq("M", m + 1, self.z80.m)
            self.regEq("T", t + 4, self.z80.t)

    def validOpc(self, name, opc, func):
        self.assertTrue(opc <= len(self.z80.instr),
            "%s instruction out of instruction range" % name)
        self.assertEquals(self.z80.instr[opc], func,
            "%s should be 0x%02x(%d)" % (name, opc, opc))

    def regEq(self, n, old, new):
        self.assertEquals(old, new, "%s should be %d, is %d" % (n, old, new))

    def tearDown(self):
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
