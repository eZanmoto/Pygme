# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu import z80
from pygme.memory import array

class TestZ80(unittest.TestCase):

    # The default number of times each test should be run
    numTests = 10

    def setUp(self):
        self.mem = array.Array(1 << 16)
        self.z80 = z80.Z80(self.mem)

    def test_nop(self):
        opc = 0x00
        self.validOpc(opc, self.z80.nop, 0)
        for _ in range(0, self.numTests):
            self.runOp(opc, 1, 4)

    def test_ldBCnn(self):
        opc = 0x01
        self.validOpc(opc, self.z80.ldBCnn, 2)
        for i in range(0, self.numTests):
            self.runOp(opc, 3, 12, i * 2, i * 4)
            self.regEq("B", self.z80.b, i * 2)
            self.regEq("C", self.z80.c, i * 4)

    def test_ldBCnn_maxValue(self):
        self.z80.ldBCnn(0xff, 0xff)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(0x100, 0x00)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(0x00, 0x100)

    def test_ldBCnn_minValue(self):
        self.z80.ldBCnn(0, 0)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(-1, 0)
        with self.assertRaises(ValueError):
            self.z80.ldBCnn(0, -1)

    def test_ldMemBCA(self):
        opc = 0x02
        self.validOpc(opc, self.z80.ldMemBCA, 0)
        for i in range(0, self.numTests):
            self.z80.a = i
            self.z80.ldBCnn(i * 2, i * 4)
            addr = (self.z80.b << 8) + self.z80.c
            self.assertEquals(self.mem.get8(addr), 0)
            self.runOp(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a)

    def test_incBC(self):
        opc = 0x03
        self.validOpc(opc, self.z80.incBC, 0)
        self.regEq("B", self.z80.b, 0)
        for i in range(0, 0x200):
            self.regEq("C", self.z80.c, i & 0xff)
            self.runOp(opc, 1, 4)
        self.regEq("B", self.z80.b, 2)

    def test_incB(self):
        opc = 0x04
        self.validOpc(opc, self.z80.incB, 0)
        self.z80.n = True
        self.z80.c = True
        for i in range(1, 0x200):
            c = self.z80.c
            self.runOp(opc, 1, 4)
            self.regEq("B", self.z80.b, i & 0xff)
            self.regEq("Z", self.z80.z, self.z80.b == 0)
            self.regEq("N", self.z80.n, False)
            self.regEq("C", self.z80.c, c)
            self.regEq("H", self.z80.h, (i - 1) & 0xf == 0xf)

    def test_decB(self):
        opc = 0x05
        self.validOpc(opc, self.z80.decB, 0)
        self.z80.ldBCnn(0x1ff & 0xff, 0)
        self.z80.n = False
        self.z80.c = False
        for i in range(0x1ff, 0, -1):
            self.assertEquals(self.z80.b, i & 0xff)
            c = self.z80.c
            self.runOp(opc, 1, 4)
            self.regEq("Z", self.z80.z, self.z80.b == 0)
            self.regEq("N", self.z80.n, True)
            self.regEq("C", self.z80.c, c)
            self.regEq("H", self.z80.h, i & 0xf != 0)

    def test_ldBn(self):
        opc = 0x06
        self.validOpc(opc, self.z80.ldBn, 1)
        for i in range(0, self.numTests):
            self.runOp(opc, 1, 4, i)
            self.regEq("B", self.z80.b, i)

    def test_ldBn_maxValue(self):
        self.z80.ldBn(0xff)
        with self.assertRaises(ValueError):
            self.z80.ldBn(0x100)

    def test_ldBn_minValue(self):
        self.z80.ldBn(0)
        with self.assertRaises(ValueError):
            self.z80.ldBn(-1)

    def test_rlcA(self):
        opc = 0x07
        self.validOpc(opc, self.z80.rlcA, 0)
        self.z80.a = 1
        self.z80.n = True
        self.z80.h = True
        for i in range(0, self.numTests):
            (i >> 7) & i
            self.regEq("A", self.z80.a, (1 << (i % 8)) & 0xff)
            c = (self.z80.a >> 7) & 1
            self.runOp(opc, 1, 4)
            self.regEq("Z", self.z80.z, self.z80.a == 0)
            self.regEq("N", self.z80.n, False)
            self.regEq("H", self.z80.h, False)
            self.regEq("C", self.z80.c, c)

    def validOpc(self, opc, func, argc):
        self.assertTrue(opc < len(self.z80.instr),
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

    def regEq(self, n, reg, val):
        self.assertEquals(reg, val, "%s should be %d, is %d" % (n, val, reg))

    def tearDown(self):
        self.mem = None
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
