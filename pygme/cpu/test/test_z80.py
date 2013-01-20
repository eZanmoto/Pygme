# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu import z80
from pygme.memory import array

class TestZ80(unittest.TestCase):

    # The default number of times each test should be run
    NUM_TESTS = 10

    def setUp(self):
        self.mem = array.Array(1 << 16)
        self.z80 = z80.Z80(self.mem)

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
            self.regEq(self.z80.b, i * 2)
            self.regEq(self.z80.c, i * 4)

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
            self.z80.a.ld(i)
            self.z80.b.ld(i * 2)
            self.z80.c.ld(i * 4)
            addr = (self.z80.b.val() << 8) + self.z80.c.val()
            self.assertEquals(self.mem.get8(addr), 0)
            self.flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())

    def test_incBC(self):
        opc = 0x03
        self.validOpc(opc, self.z80.incBC, 0)
        self.regEq(self.z80.b, 0)
        for i in range(0, 0x200):
            self.regEq(self.z80.c, i & 0xff)
            self.flagsFixed(opc, 1, 4)
        self.regEq(self.z80.b, 2)

    def test_incB(self):
        opc = 0x04
        self.validOpc(opc, self.z80.incB, 0)
        for i in range(1, 0x200):
            self.incOp8(opc, self.z80.b, 1, 1, 4)
            self.regEq(self.z80.b, i & 0xff)

    def test_decB(self):
        opc = 0x05
        self.validOpc(opc, self.z80.decB, 0)
        self.z80.b.ld(0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self.regEq(self.z80.b, i & 0xff)
            self.incOp8(opc, self.z80.b, -1, 1, 4)
        self.z80.b.ld(1)
        self.incOp8(opc, self.z80.b, -1, 1, 4)
        self.regEq(self.z80.b, 0)
        self.z80.b.ld(0)
        self.incOp8(opc, self.z80.b, -1, 1, 4)
        self.regEq(self.z80.b, 0xff)

    def test_ldBn(self):
        opc = 0x06
        self.validOpc(opc, self.z80.ldBn, 1)
        for i in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 1, 4, i)
            self.regEq(self.z80.b, i)

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
        self.z80.a.ld(1)
        self.z80.f.n.set()
        self.z80.f.h.set()
        for i in range(0, self.NUM_TESTS):
            self.regEq(self.z80.a, (1 << (i % 8)) & 0xff)
            z, c = (self.z80.f.z.val(), (self.z80.a.val() >> 7) & 1)
            self.timeOp(opc, 1, 4)
            self.flagEq(self.z80.f.z, z)
            self.flagEq(self.z80.f.n, False)
            self.flagEq(self.z80.f.h, False)
            self.flagEq(self.z80.f.c, c)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self.timeOp(opc, 1, 4)
        self.flagEq(self.z80.f.z, False)

    def test_ldMemnnSP(self):
        opc = 0x08
        self.validOpc(opc, self.z80.ldMemnnSP, 2)

    def test_addHLBC(self):
        opc = 0x09
        self.validOpc(opc, self.z80.addHLBC, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.b.ld(0x23)
        self.z80.c.ld(0x67)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self.timeOp(opc, 3, 12)
        self.regEq(self.z80.h, 0x36)
        self.regEq(self.z80.l, 0x9b)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self.flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.b.ld(0xff)
        self.z80.c.ld(0xff)
        self.timeOp(opc, 3, 12)
        self.regEq(self.z80.h, 0x36)
        self.regEq(self.z80.l, 0x9a)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, 0x336 + 0xfff > 0xfff)
        self.flagEq(self.z80.f.c, 0x1334 + 0xffff > 0xffff)

    def test_ldAMemBC(self):
        opc = 0x0a
        self.validOpc(opc, self.z80.ldAMemBC, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.b.ld(i * 2)
            self.z80.c.ld(i * 4)
            addr = (self.z80.b.val() << 8) + self.z80.c.val()
            val = (i * 3) & 0xff
            self.mem.set8(addr, val)
            self.z80.a.ld(0)
            self.flagsFixed(opc, 2, 8)
            self.regEq(self.z80.a, val)

    def test_decBC(self):
        opc = 0x0b
        self.validOpc(opc, self.z80.decBC, 0)
        self.z80.ldBCnn(0x01, 0x00)
        self.flagsFixed(opc, 1, 4)
        self.regEq(self.z80.b, 0x00)
        self.regEq(self.z80.c, 0xff)
        self.z80.ldBCnn(0x00, 0x01)
        self.flagsFixed(opc, 1, 4)
        self.regEq(self.z80.b, 0x00)
        self.regEq(self.z80.c, 0x00)
        self.z80.ldBCnn(0x00, 0x00)
        self.flagsFixed(opc, 1, 4)
        self.regEq(self.z80.b, 0xff)
        self.regEq(self.z80.c, 0xff)

    def test_incC(self):
        opc = 0x0c
        self.validOpc(opc, self.z80.incC, 0)
        for i in range(1, 0x200):
            self.incOp8(opc, self.z80.c, 1, 1, 4)
            self.regEq(self.z80.c, i & 0xff)

    def test_decC(self):
        opc = 0x0d
        self.validOpc(opc, self.z80.decC, 0)
        self.z80.ldBCnn(0, 0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self.regEq(self.z80.c, i & 0xff)
            self.incOp8(opc, self.z80.c, -1, 1, 4)
        self.z80.ldBCnn(0, 1)
        self.incOp8(opc, self.z80.c, -1, 1, 4)
        self.regEq(self.z80.c, 0)
        self.z80.ldBCnn(0, 0)
        self.incOp8(opc, self.z80.c, -1, 1, 4)
        self.regEq(self.z80.c, 0xff)

    def test_ldCn(self):
        opc = 0x0e
        self.validOpc(opc, self.z80.ldCn, 1)
        for i in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 1, 4, i)
            self.regEq(self.z80.c, i)

    def test_rrcA(self):
        opc = 0x0f
        self.validOpc(opc, self.z80.rrcA, 0)
        self.z80.a.ld(0x80)
        self.z80.f.n.set()
        self.z80.f.h.set()
        for i in range(0, self.NUM_TESTS):
            self.regEq(self.z80.a, (0x80 >> (i % 8)) & 0xff)
            z, c = (self.z80.f.z.val(), self.z80.a.val() & 1)
            self.timeOp(opc, 1, 4)
            self.flagEq(self.z80.f.z, z)
            self.flagEq(self.z80.f.n, False)
            self.flagEq(self.z80.f.h, False)
            self.flagEq(self.z80.f.c, c)
        self.z80.a.ld(1)
        self.timeOp(opc, 1, 4)
        self.regEq(self.z80.a, 0x80)
        self.flagEq(self.z80.f.c, True)
        self.timeOp(opc, 1, 4)
        self.regEq(self.z80.a, 0x40)
        self.flagEq(self.z80.f.c, False)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self.timeOp(opc, 1, 4)
        self.flagEq(self.z80.f.z, False)

    def test_stop(self):
        opc = 0x10
        self.validOpc(opc, self.z80.stop, 0)

    def test_ldDEnn(self):
        opc = 0x11
        self.validOpc(opc, self.z80.ldDEnn, 2)
        for i in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 3, 12, i * 2, i * 4)
            self.regEq(self.z80.d, i * 2)
            self.regEq(self.z80.e, i * 4)

    def test_ldDEnn_maxValue(self):
        self.z80.ldDEnn(0xff, 0xff)
        with self.assertRaises(ValueError):
            self.z80.ldDEnn(0x100, 0x00)
        with self.assertRaises(ValueError):
            self.z80.ldDEnn(0x00, 0x100)

    def test_ldDEnn_minValue(self):
        self.z80.ldDEnn(0, 0)
        with self.assertRaises(ValueError):
            self.z80.ldDEnn(-1, 0)
        with self.assertRaises(ValueError):
            self.z80.ldDEnn(0, -1)

    def test_ldMemDEA(self):
        opc = 0x12
        self.validOpc(opc, self.z80.ldMemDEA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.d.ld(i * 2)
            self.z80.e.ld(i * 4)
            addr = (self.z80.d.val() << 8) + self.z80.e.val()
            self.assertEquals(self.mem.get8(addr), 0)
            self.flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())

    def test_incDE(self):
        opc = 0x13
        self.validOpc(opc, self.z80.incDE, 0)
        self.regEq(self.z80.d, 0)
        for i in range(0, 0x200):
            self.regEq(self.z80.e, i & 0xff)
            self.flagsFixed(opc, 1, 4)
        self.regEq(self.z80.d, 2)

    def test_incD(self):
        opc = 0x14
        self.validOpc(opc, self.z80.incD, 0)
        for i in range(1, 0x200):
            self.incOp8(opc, self.z80.d, 1, 1, 4)
            self.regEq(self.z80.d, i & 0xff)

    def test_decD(self):
        opc = 0x15
        self.validOpc(opc, self.z80.decD, 0)
        self.z80.ldDEnn(0x1ff & 0xff, 0)
        for i in range(0x1ff, 0, -1):
            self.regEq(self.z80.d, i & 0xff)
            self.incOp8(opc, self.z80.d, -1, 1, 4)
        self.z80.ldDEnn(1, 0)
        self.incOp8(opc, self.z80.d, -1, 1, 4)
        self.regEq(self.z80.d, 0)
        self.z80.ldDEnn(0, 0)
        self.incOp8(opc, self.z80.d, -1, 1, 4)
        self.regEq(self.z80.d, 0xff)

    def test_ldDn(self):
        opc = 0x16
        self.validOpc(opc, self.z80.ldDn, 1)
        for i in range(0, self.NUM_TESTS):
            self.flagsFixed(opc, 1, 4, i)
            self.regEq(self.z80.d, i)

    def test_rlA(self):
        opc = 0x17
        self.validOpc(opc, self.z80.rlA, 0)
        z = True
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.a.ld(0x80)
        self.timeOp(opc, 1, 4)
        self.regEq(self.z80.a, 0x00)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, False)
        self.flagEq(self.z80.f.c, True)
        self.timeOp(opc, 1, 4)
        self.regEq(self.z80.a, 0x01)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, False)
        self.flagEq(self.z80.f.c, False)
        self.timeOp(opc, 1, 4)
        self.regEq(self.z80.a, 0x02)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, False)
        self.flagEq(self.z80.f.c, False)

    def test_jrn(self):
        opc = 0x18
        self.validOpc(opc, self.z80.jrn, 1)
        self.z80.pc.ld(126)
        self.flagsFixed(opc, 1, 4, 0x00)
        self.regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self.flagsFixed(opc, 1, 4, 0xff)
        self.regEq(self.z80.pc, 129)

    def test_addHLDE(self):
        opc = 0x19
        self.validOpc(opc, self.z80.addHLDE, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.d.ld(0x23)
        self.z80.e.ld(0x67)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self.timeOp(opc, 3, 12)
        self.regEq(self.z80.h, 0x36)
        self.regEq(self.z80.l, 0x9b)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self.flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.d.ld(0xff)
        self.z80.e.ld(0xff)
        self.timeOp(opc, 3, 12)
        self.regEq(self.z80.h, 0x36)
        self.regEq(self.z80.l, 0x9a)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, False)
        self.flagEq(self.z80.f.h, 0x336 + 0xfff > 0xfff)
        self.flagEq(self.z80.f.c, 0x1334 + 0xffff > 0xffff)

    def test_ldAMemDE(self):
        opc = 0x1a
        self.validOpc(opc, self.z80.ldAMemDE, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.d.ld(i * 2)
            self.z80.e.ld(i * 4)
            addr = (self.z80.d.val() << 8) + self.z80.e.val()
            val = (i * 3) & 0xff
            self.mem.set8(addr, val)
            self.z80.a.ld(0)
            self.flagsFixed(opc, 2, 8)
            self.regEq(self.z80.a, val)

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
        val = reg.val()
        self.z80.n = pos
        c = self.z80.f.c.val()
        self.timeOp(opc, m_, t_, a, b)
        self.flagEq(self.z80.f.z, reg.val() == 0)
        self.flagEq(self.z80.f.n, not pos)
        self.flagEq(self.z80.f.c, c)
        self.flagEq(self.z80.f.h, val & 0xf == 0xf if pos else val & 0xf != 0x0)

    def flagsFixed(self, opc, m_, t_, a=None, b=None):
        """Flags are unaffected by running instruction opc with a and b"""
        f = self.z80.f
        z, n, h, c = (f.z.val(), f.n.val(), f.h.val(), f.c.val())
        self.timeOp(opc, m_, t_, a, b)
        self.flagEq(self.z80.f.z, z)
        self.flagEq(self.z80.f.n, n)
        self.flagEq(self.z80.f.h, h)
        self.flagEq(self.z80.f.c, c)

    def timeOp(self, opc, m_, t_, a=None, b=None):
        m = self.z80.m
        t = self.z80.t
        self.runOp(opc, a, b)
        self.assertEqual(self.z80.m, m + m_)
        self.assertEqual(self.z80.t, t + t_)

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
        self.assertEquals(flag.val(), val, "Flag %s is 0x%d, should be 0x%d" %
            (flag.name(), flag.val(), val))

    def regEq(self, reg, val):
        self.assertEquals(reg.val(), val,
                "Register %s is 0x%02x(%d), should be 0x%02x(%d)"
                % (reg.name(), reg.val(), reg.val(), val, val))

    def tearDown(self):
        self.mem = None
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
