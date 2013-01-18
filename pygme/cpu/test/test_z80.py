# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu import z80
from pygme.memory import array

class TestZ80(unittest.TestCase):

    numTests = 10

    def setUp(self):
        self.mem = array.Array(1 << 16)
        self.z80 = z80.Z80(self.mem)

    def test_nop(self):
        opc = 0
        self.validOpc(opc, self.z80.nop, 0)
        for _ in range(0, self.numTests):
            self.runOp(opc, 1, 4)

    def test_ldBCnn(self):
        opc = 1
        self.validOpc(opc, self.z80.ldBCnn, 2)
        for i in range(0, self.numTests):
            b = self.z80.b
            c = self.z80.c
            self.runOp(opc, 3, 12, i * 2, i * 4)
            self.regEq("B", i * 2, self.z80.b)
            self.regEq("C", i * 4, self.z80.c)

    def test_ldBCnn_maxValue(self):
        self.z80.ldBCnn(0x00, 0x00)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(0xff, 0x00)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(0x00, 0xff)

    def test_ldBCnn_minValue(self):
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(-1, 0)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(0, -1)

    def test_ldMemBCA(self):
        opc = 2
        self.validOpc(opc, self.z80.ldMemBCA, 0)
        for i in range(0, self.numTests):
            self.z80.a = i
            self.z80.ldBCnn(i * 2, i * 4)
            addr = (self.z80.b << 8) + self.z80.c
            self.assertEquals(self.mem.get8(addr), 0)
            self.runOp(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a)

    def validOpc(self, opc, func, argc):
        self.assertTrue(opc <= len(self.z80.instr),
            "Opcode out of instruction range")
        func_, argc_ = self.z80.instr[opc]
        self.assertEquals(func, func_,
            "Opcode should be 0x%02x(%d)" % (opc, opc))
        self.assertEquals(argc, argc_,
            "Instruction should take %d args, got %d" % (argc, argc_))

    def runOp(self, opc, m_, t_, a=None, b=None):
        m = self.z80.m
        t = self.z80.t
        op, n = self.z80.instr[opc]
        if n == 0:
            self.assertIsNone(a, "Expect 0 instructions, got 'a'")
            self.assertIsNone(b, "Expect 0 instructions, got 'b'")
            op()
        else:
            self.assertIsNotNone(a, "Expect %d instructions, need 'a'" % n)
            if n == 1:
                self.assertIsNone(b, "Expect %d instructions, got 'b'" % n)
                op(a)
            else:
                self.assertIsNotNone(b, "Expect %d instructions, need 'b'" % n)
                op(a, b)
        self.regEq("M", m + m_, self.z80.m)
        self.regEq("T", t + t_, self.z80.t)

    def regEq(self, n, old, new):
        self.assertEquals(old, new, "%s should be %d, is %d" % (n, old, new))

    def tearDown(self):
        self.mem = None
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
