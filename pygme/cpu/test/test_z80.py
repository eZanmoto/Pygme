# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu import z80
from pygme.memory import array

class TestZ80(unittest.TestCase):

    # The default number of times each test should be run
    NUM_TESTS = 10

    # Registers
    A   = 0
    B   = 1
    C   = 2
    D   = 3
    E   = 4
    H   = 5
    L   = 6
    M   = 7
    T   = 8
    F_Z = 9
    F_N = 10
    F_H = 11
    F_C = 12

    def setUp(self):
        self.mem = array.Array(1 << 16)
        self.z80 = z80.Z80(self.mem)
        self.regNames = {self.A:   "A",
                         self.B:   "B",
                         self.C:   "C",
                         self.D:   "D",
                         self.E:   "E",
                         self.H:   "H",
                         self.L:   "L",
                         self.M:   "M",
                         self.T:   "T",
                         self.F_Z: "F.Z",
                         self.F_N: "F.N",
                         self.F_H: "F.H",
                         self.F_C: "F.C",
                        }

    def test_nop(self):
        opc = 0x00
        self.validOpc(opc, self.z80.nop, 0)
        for _ in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 1, 4)

    def test_ldBCnn(self):
        opc = 0x01
        self.validOpc(opc, self.z80.ldBCnn, 2)
        for i in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 3, 12, i * 2, i * 4)
            self.regEq(self.B, i * 2)
            self.regEq(self.C, i * 4)

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
        for i in range(0, self.NUM_TESTS):
            self.z80.a = i
            self.z80.ldBCnn(i * 2, i * 4)
            addr = (self.z80.b << 8) + self.z80.c
            self.assertEquals(self.mem.get8(addr), 0)
            self.flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a)

    def test_incBC(self):
        opc = 0x03
        self.validOpc(opc, self.z80.incBC, 0)
        self.regEq(self.B, 0)
        for i in range(0, 0x200):
            self.regEq(self.C, i & 0xff)
            self.flagsFixed(opc, 1, 4)
        self.regEq(self.B, 2)

    def test_incB(self):
        opc = 0x04
        self.validOpc(opc, self.z80.incB, 0)
        for i in range(1, 0x200):
            self.incOp8(opc, self.B, 1, 1, 4)
            self.regEq(self.B, i & 0xff)

    def test_decB(self):
        opc = 0x05
        self.validOpc(opc, self.z80.decB, 0)
        self.z80.ldBn(0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self.regEq(self.B, i & 0xff)
            self.incOp8(opc, self.B, -1, 1, 4)
        self.z80.ldBn(1)
        self.incOp8(opc, self.B, -1, 1, 4)
        self.regEq(self.B, 0)
        self.z80.ldBn(0)
        self.incOp8(opc, self.B, -1, 1, 4)
        self.regEq(self.B, 0xff)

    def test_ldBn(self):
        opc = 0x06
        self.validOpc(opc, self.z80.ldBn, 1)
        for i in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 1, 4, i)
            self.regEq(self.B, i)

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
        self.z80.f.n = True
        self.z80.f.h = True
        for i in range(0, self.NUM_TESTS):
            (i >> 7) & i
            self.regEq(self.A, (1 << (i % 8)) & 0xff)
            c = (self.z80.a >> 7) & 1
            self.timeOp(opc, 1, 4)
            self.flagEq(self.F_Z, self.z80.a == 0)
            self.flagEq(self.F_N, False)
            self.flagEq(self.F_H, False)
            self.flagEq(self.F_C, c)

    def test_rlcA(self):
        opc = 0x07
        self.validOpc(opc, self.z80.rlcA, 0)
        self.z80.a = 1
        self.z80.f.n = True
        self.z80.f.h = True
        for i in range(0, self.NUM_TESTS):
            (i >> 7) & i
            self.regEq(self.A, (1 << (i % 8)) & 0xff)
            c = (self.z80.a >> 7) & 1
            self.timeOp(opc, 1, 4)
            self.flagEq(self.F_Z, self.z80.a == 0)
            self.flagEq(self.F_N, False)
            self.flagEq(self.F_H, False)
            self.flagEq(self.F_C, c)

    def test_ldMemnnSP(self):
        opc = 0x08
        self.validOpc(opc, self.z80.ldMemnnSP, 2)

    def test_addHLBC(self):
        opc = 0x09
        self.validOpc(opc, self.z80.addHLBC, 0)
        self.z80.h, self.z80.l = 0x13, 0x34
        self.z80.ldBCnn(0x23, 0x67)
        z, n = (self.z80.f.z, True)
        self.timeOp(opc, 3, 12)
        self.regEq(self.H, 0x36)
        self.regEq(self.L, 0x9b)
        self.flagEq(self.F_Z, z)
        self.flagEq(self.F_N, False)
        self.flagEq(self.F_H, 0x133 + 0x236 > 0xfff)
        self.flagEq(self.F_C, 0x1334 + 0x2367 > 0xffff)
        self.z80.ldBCnn(0xff, 0xff)
        self.timeOp(opc, 3, 12)
        self.regEq(self.H, 0x36)
        self.regEq(self.L, 0x9a)
        self.flagEq(self.F_Z, z)
        self.flagEq(self.F_N, False)
        self.flagEq(self.F_H, 0x336 + 0xfff > 0xfff)
        self.flagEq(self.F_C, 0x1334 + 0xffff > 0xffff)

    def test_ldAMemBC(self):
        opc = 0x0a
        self.validOpc(opc, self.z80.ldAMemBC, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.ldBCnn(i * 2, i * 4)
            addr = (self.z80.b << 8) + self.z80.c
            val = (i * 3) & 0xff
            self.mem.set8(addr, val)
            self.z80.a = 0
            self.flagsFixed(opc, 2, 8)
            self.regEq(self.A, val)

    def test_decBC(self):
        opc = 0x0b
        self.validOpc(opc, self.z80.decBC, 0)
        self.z80.ldBCnn(0x01, 0x00)
        self.flagsFixed(opc, 1, 4)
        self.regEq(self.B, 0x00)
        self.regEq(self.C, 0xff)
        self.z80.ldBCnn(0x00, 0x01)
        self.flagsFixed(opc, 1, 4)
        self.regEq(self.B, 0x00)
        self.regEq(self.C, 0x00)
        self.z80.ldBCnn(0x00, 0x00)
        self.flagsFixed(opc, 1, 4)
        self.regEq(self.B, 0xff)
        self.regEq(self.C, 0xff)

    def test_incC(self):
        opc = 0x0c
        self.validOpc(opc, self.z80.incC, 0)
        for i in range(1, 0x200):
            self.incOp8(opc, self.C, 1, 1, 4)
            self.regEq(self.C, i & 0xff)

    def test_decC(self):
        opc = 0x0d
        self.validOpc(opc, self.z80.decC, 0)
        self.z80.ldBCnn(0, 0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self.regEq(self.C, i & 0xff)
            self.incOp8(opc, self.C, -1, 1, 4)
        self.z80.ldBCnn(0, 1)
        self.incOp8(opc, self.C, -1, 1, 4)
        self.regEq(self.C, 0)
        self.z80.ldBCnn(0, 0)
        self.incOp8(opc, self.C, -1, 1, 4)
        self.regEq(self.C, 0xff)

    def validOpc(self, opc, func, argc):
        self.assertTrue(opc < len(self.z80.instr),
            "Opcode out of instruction range")
        func_, argc_ = self.z80.instr[opc]
        self.assertEquals(func, func_,
            "Opcode should be 0x%02x(%d)" % (opc, opc))
        self.assertEquals(argc, argc_,
            "Instruction should take %d args, got %d" % (argc, argc_))

    def incOp8(self, opc, reg, inc, m_, t_, a=None, b=None):
        if inc == 0:
            raise ValueError("Can't increase register by 0")
        else:
            pos = inc > 0
        val = self.regVal(reg)
        self.z80.n = pos
        c = self.z80.f.c
        self.timeOp(opc, m_, t_, a, b)
        self.flagEq(self.F_Z, self.regVal(reg) == 0)
        self.flagEq(self.F_N, not pos)
        self.flagEq(self.F_C, c)
        self.flagEq(self.F_H, val & 0xf == 0xf if pos else val & 0xf != 0x0)

    def flagsFixed(self, opc, m_, t_, a=None, b=None):
        """Flags are unaffected by running instruction opc with a and b"""
        f = self.z80.f
        z, n, h, c = (f.z, f.n, f.h, f.c)
        self.timeOp(opc, m_, t_, a, b)
        self.flagEq(self.F_Z, z)
        self.flagEq(self.F_N, n)
        self.flagEq(self.F_H, h)
        self.flagEq(self.F_C, c)

    def timeOp(self, opc, m_, t_, a=None, b=None):
        m = self.z80.m
        t = self.z80.t
        self.runOp(opc, a, b)
        self.regEq(self.M, self.z80.m)
        self.regEq(self.T, self.z80.t)

    def runOp(self, opc, a=None, b=None):
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

    def flagEq(self, flag, val):
        flagVal = self.flagVal(flag)
        self.assertEquals(flagVal, val, "Flag %s is 0x%d, should be 0x%d" %
            (self.regNames[flag], flagVal, val))

    def flagVal(self, flag):
        if flag == self.F_Z:
            return self.z80.f.z
        elif flag == self.F_N:
            return self.z80.f.n
        elif flag == self.F_H:
            return self.z80.f.h
        elif flag == self.F_C:
            return self.z80.f.c
        else:
            raise KeyError("%d does not represent any register flag" % flag)

    def regEq(self, reg, val):
        regVal = self.regVal(reg)
        self.assertEquals(regVal, val,
                "Register %s is 0x%02x(%d), should be 0x%02x(%d)"
                % (self.regNames[reg], regVal, regVal, val, val))

    def regVal(self, reg):
        if reg == self.A:
            return self.z80.a
        if reg == self.B:
            return self.z80.b
        if reg == self.C:
            return self.z80.c
        if reg == self.D:
            return self.z80.d
        if reg == self.E:
            return self.z80.e
        if reg == self.H:
            return self.z80.h
        if reg == self.L:
            return self.z80.l
        if reg == self.M:
            return self.z80.m
        if reg == self.T:
            return self.z80.t
        else:
            raise KeyError("%d does not represent any register" % reg)

    def tearDown(self):
        self.mem = None
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
