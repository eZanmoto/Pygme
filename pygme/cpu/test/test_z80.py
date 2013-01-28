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
        self._validOpc(opc, self.z80.nop, 0)
        for _ in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4)

    def test_ldBCnn(self):
        opc = 0x01
        self._validOpc(opc, self.z80.ldBCnn, 2)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 3, 12, i * 2, i * 4)
            self._regEq(self.z80.b, i * 2)
            self._regEq(self.z80.c, i * 4)

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
        self._validOpc(opc, self.z80.ldMemBCA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.b.ld(i * 2)
            self.z80.c.ld(i * 4)
            addr = (self.z80.b.val() << 8) + self.z80.c.val()
            self.assertEquals(self.mem.get8(addr), 0)
            self._flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())

    def test_incBC(self):
        opc = 0x03
        self._validOpc(opc, self.z80.incBC, 0)
        self._regEq(self.z80.b, 0)
        for i in range(0, 0x200):
            self._regEq(self.z80.c, i & 0xff)
            self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.b, 2)

    def test_incB(self):
        opc = 0x04
        self._validOpc(opc, self.z80.incB, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.b, 1, 1, 4)
            self._regEq(self.z80.b, i & 0xff)

    def test_decB(self):
        opc = 0x05
        self._validOpc(opc, self.z80.decB, 0)
        self.z80.b.ld(0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.b, i & 0xff)
            self._incOp8(opc, self.z80.b, -1, 1, 4)
        self.z80.b.ld(1)
        self._incOp8(opc, self.z80.b, -1, 1, 4)
        self._regEq(self.z80.b, 0)
        self.z80.b.ld(0)
        self._incOp8(opc, self.z80.b, -1, 1, 4)
        self._regEq(self.z80.b, 0xff)

    def test_ldBn(self):
        opc = 0x06
        self._validOpc(opc, self.z80.ldBn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.b, i)

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
        self._validOpc(opc, self.z80.rlcA, 0)
        self.z80.a.ld(1)
        self.z80.f.n.set()
        self.z80.f.h.set()
        for i in range(0, self.NUM_TESTS):
            self._regEq(self.z80.a, (1 << (i % 8)) & 0xff)
            z, c = (self.z80.f.z.val(), (self.z80.a.val() >> 7) & 1)
            self._timeOp(opc, 1, 4)
            self._flagEq(self.z80.f.z, z)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self._timeOp(opc, 1, 4)
        self._flagEq(self.z80.f.z, False)

    def test_ldMemnnSP(self):
        opc = 0x08
        self._validOpc(opc, self.z80.ldMemnnSP, 2)

    def test_addHLBC(self):
        opc = 0x09
        self._validOpc(opc, self.z80.addHLBC, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.b.ld(0x23)
        self.z80.c.ld(0x67)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.b.ld(0xff)
        self.z80.c.ld(0xff)
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9a)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x336 + 0xfff > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0xffff > 0xffff)

    def test_ldAMemBC(self):
        opc = 0x0a
        self._validOpc(opc, self.z80.ldAMemBC, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.b.ld(i * 2)
            self.z80.c.ld(i * 4)
            addr = (self.z80.b.val() << 8) + self.z80.c.val()
            val = (i * 3) & 0xff
            self.mem.set8(addr, val)
            self.z80.a.ld(0)
            self._flagsFixed(opc, 2, 8)
            self._regEq(self.z80.a, val)

    def test_decBC(self):
        opc = 0x0b
        self._validOpc(opc, self.z80.decBC, 0)
        self.z80.ldBCnn(0x01, 0x00)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.b, 0x00)
        self._regEq(self.z80.c, 0xff)
        self.z80.ldBCnn(0x00, 0x01)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.b, 0x00)
        self._regEq(self.z80.c, 0x00)
        self.z80.ldBCnn(0x00, 0x00)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.b, 0xff)
        self._regEq(self.z80.c, 0xff)

    def test_incC(self):
        opc = 0x0c
        self._validOpc(opc, self.z80.incC, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.c, 1, 1, 4)
            self._regEq(self.z80.c, i & 0xff)

    def test_decC(self):
        opc = 0x0d
        self._validOpc(opc, self.z80.decC, 0)
        self.z80.ldBCnn(0, 0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.c, i & 0xff)
            self._incOp8(opc, self.z80.c, -1, 1, 4)
        self.z80.ldBCnn(0, 1)
        self._incOp8(opc, self.z80.c, -1, 1, 4)
        self._regEq(self.z80.c, 0)
        self.z80.ldBCnn(0, 0)
        self._incOp8(opc, self.z80.c, -1, 1, 4)
        self._regEq(self.z80.c, 0xff)

    def test_ldCn(self):
        opc = 0x0e
        self._validOpc(opc, self.z80.ldCn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.c, i)

    def test_rrcA(self):
        opc = 0x0f
        self._validOpc(opc, self.z80.rrcA, 0)
        self.z80.a.ld(0x80)
        self.z80.f.n.set()
        self.z80.f.h.set()
        for i in range(0, self.NUM_TESTS):
            self._regEq(self.z80.a, (0x80 >> (i % 8)) & 0xff)
            z, c = (self.z80.f.z.val(), self.z80.a.val() & 1)
            self._timeOp(opc, 1, 4)
            self._flagEq(self.z80.f.z, z)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self.z80.a.ld(1)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x80)
        self._flagEq(self.z80.f.c, True)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x40)
        self._flagEq(self.z80.f.c, False)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self._timeOp(opc, 1, 4)
        self._flagEq(self.z80.f.z, False)

    def test_stop(self):
        opc = 0x10
        self._validOpc(opc, self.z80.stop, 0)

    def test_ldDEnn(self):
        opc = 0x11
        self._validOpc(opc, self.z80.ldDEnn, 2)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 3, 12, i * 2, i * 4)
            self._regEq(self.z80.d, i * 2)
            self._regEq(self.z80.e, i * 4)

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
        self._validOpc(opc, self.z80.ldMemDEA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.d.ld(i * 2)
            self.z80.e.ld(i * 4)
            addr = (self.z80.d.val() << 8) + self.z80.e.val()
            self.assertEquals(self.mem.get8(addr), 0)
            self._flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())

    def test_incDE(self):
        opc = 0x13
        self._validOpc(opc, self.z80.incDE, 0)
        self._regEq(self.z80.d, 0)
        for i in range(0, 0x200):
            self._regEq(self.z80.e, i & 0xff)
            self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.d, 2)

    def test_incD(self):
        opc = 0x14
        self._validOpc(opc, self.z80.incD, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.d, 1, 1, 4)
            self._regEq(self.z80.d, i & 0xff)

    def test_decD(self):
        opc = 0x15
        self._validOpc(opc, self.z80.decD, 0)
        self.z80.ldDEnn(0x1ff & 0xff, 0)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.d, i & 0xff)
            self._incOp8(opc, self.z80.d, -1, 1, 4)
        self.z80.ldDEnn(1, 0)
        self._incOp8(opc, self.z80.d, -1, 1, 4)
        self._regEq(self.z80.d, 0)
        self.z80.ldDEnn(0, 0)
        self._incOp8(opc, self.z80.d, -1, 1, 4)
        self._regEq(self.z80.d, 0xff)

    def test_ldDn(self):
        opc = 0x16
        self._validOpc(opc, self.z80.ldDn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.d, i)

    def test_rlA(self):
        opc = 0x17
        self._validOpc(opc, self.z80.rlA, 0)
        z = True
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.a.ld(0x80)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x00)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, True)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x01)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x02)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)

    def test_jrn(self):
        opc = 0x18
        self._validOpc(opc, self.z80.jrn, 1)
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 129)

    def test_addHLDE(self):
        opc = 0x19
        self._validOpc(opc, self.z80.addHLDE, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.d.ld(0x23)
        self.z80.e.ld(0x67)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.d.ld(0xff)
        self.z80.e.ld(0xff)
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9a)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x336 + 0xfff > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0xffff > 0xffff)

    def test_ldAMemDE(self):
        opc = 0x1a
        self._validOpc(opc, self.z80.ldAMemDE, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.d.ld(i * 2)
            self.z80.e.ld(i * 4)
            addr = (self.z80.d.val() << 8) + self.z80.e.val()
            val = (i * 3) & 0xff
            self.mem.set8(addr, val)
            self.z80.a.ld(0)
            self._flagsFixed(opc, 2, 8)
            self._regEq(self.z80.a, val)

    def test_decBC(self):
        opc = 0x1b
        self._validOpc(opc, self.z80.decDE, 0)
        self.z80.d.ld(0x01)
        self.z80.e.ld(0x00)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.d, 0x00)
        self._regEq(self.z80.e, 0xff)
        self.z80.d.ld(0x00)
        self.z80.e.ld(0x01)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.d, 0x00)
        self._regEq(self.z80.e, 0x00)
        self.z80.d.ld(0x00)
        self.z80.e.ld(0x00)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.d, 0xff)
        self._regEq(self.z80.e, 0xff)

    def test_incE(self):
        opc = 0x1c
        self._validOpc(opc, self.z80.incE, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.e, 1, 1, 4)
            self._regEq(self.z80.e, i & 0xff)

    def test_decE(self):
        opc = 0x1d
        self._validOpc(opc, self.z80.decE, 0)
        self.z80.ldDEnn(0, 0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.e, i & 0xff)
            self._incOp8(opc, self.z80.e, -1, 1, 4)
        self.z80.ldDEnn(0, 1)
        self._incOp8(opc, self.z80.e, -1, 1, 4)
        self._regEq(self.z80.e, 0)
        self.z80.ldDEnn(0, 0)
        self._incOp8(opc, self.z80.e, -1, 1, 4)
        self._regEq(self.z80.e, 0xff)

    def test_ldEn(self):
        opc = 0x1e
        self._validOpc(opc, self.z80.ldEn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.e, i)

    def test_rrA(self):
        opc = 0x1f
        self._validOpc(opc, self.z80.rrA, 0)
        self.z80.a.ld(0x02)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x01)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, True)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x80)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x40)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)

    def test_jrNZn(self):
        opc = 0x20
        self._validOpc(opc, self.z80.jrNZn, 1)
        self.z80.f.z.set()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 126)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 0)
        self.z80.f.z.reset()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 129)

    def test_ldHLnn(self):
        opc = 0x21
        self._validOpc(opc, self.z80.ldHLnn, 2)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 3, 12, i * 2, i * 4)
            self._regEq(self.z80.h, i * 2)
            self._regEq(self.z80.l, i * 4)

    def test_ldiMemHLA(self):
        opc = 0x22
        self._validOpc(opc, self.z80.ldiMemHLA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.h.ld(i * 2)
            self.z80.l.ld(i * 4)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            self.assertEquals(self.mem.get8(addr), 0)
            self._flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())
            self._regEq(self.z80.l, (i * 4 + 1) & 0xff)
            self._regEq(self.z80.h, (i * 2) + ((i * 4 + 1) >> 8))

    def test_incHL(self):
        opc = 0x23
        self._validOpc(opc, self.z80.incHL, 0)
        self._regEq(self.z80.h, 0)
        for i in range(0, 0x200):
            self._regEq(self.z80.l, i & 0xff)
            self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.h, 2)

    def test_incH(self):
        opc = 0x24
        self._validOpc(opc, self.z80.incH, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.h, 1, 1, 4)
            self._regEq(self.z80.h, i & 0xff)

    def test_decH(self):
        opc = 0x25
        self._validOpc(opc, self.z80.decH, 0)
        self.z80.h.ld(0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.h, i & 0xff)
            self._incOp8(opc, self.z80.h, -1, 1, 4)
        self.z80.h.ld(1)
        self._incOp8(opc, self.z80.h, -1, 1, 4)
        self._regEq(self.z80.h, 0)
        self.z80.h.ld(0)
        self._incOp8(opc, self.z80.h, -1, 1, 4)
        self._regEq(self.z80.h, 0xff)

    def test_ldHn(self):
        opc = 0x26
        self._validOpc(opc, self.z80.ldHn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.h, i)

    def test_daa(self):
        opc = 0x27
        self._validOpc(opc, self.z80.daa, 0)

    def test_jrZn(self):
        opc = 0x28
        self._validOpc(opc, self.z80.jrZn, 1)
        self.z80.f.z.set()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 129)
        self.z80.f.z.reset()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 126)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 0)

    def test_addHLHL(self):
        opc = 0x29
        self._validOpc(opc, self.z80.addHLHL, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x36)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x26)
        self._regEq(self.z80.l, 0x6c)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x133 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1336 + 0x1336 > 0xffff)
        self.z80.h.ld(0xff)
        self.z80.l.ld(0xff)
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0xff)
        self._regEq(self.z80.l, 0xfe)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0xfff + 0xfff > 0xfff)
        self._flagEq(self.z80.f.c, 0xffff + 0xffff > 0xffff)

    def test_ldiAMemHL(self):
        opc = 0x2a
        self._validOpc(opc, self.z80.ldiAMemHL, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.h.ld(i * 2)
            self.z80.l.ld(i * 4)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            val = (i * 3) & 0xff
            self.mem.set8(addr, val)
            self.z80.a.ld(0)
            self._flagsFixed(opc, 2, 8)
            self._regEq(self.z80.a, val)
            if i * 4 == 0xff:
                self._regEq(self.z80.h, i * 2 + 1)
                self._regEq(self.z80.l, 0)
            else:
                self._regEq(self.z80.h, i * 2)
                self._regEq(self.z80.l, i * 4 + 1)
        self.z80.h.ld(0x00)
        self.z80.l.ld(0xff)
        self._flagsFixed(opc, 2, 8)
        self._regEq(self.z80.h, 0x01)
        self._regEq(self.z80.l, 0x00)

    def test_decHL(self):
        opc = 0x2b
        self._validOpc(opc, self.z80.decHL, 0)
        self.z80.ldHLnn(0x01, 0x00)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.h, 0x00)
        self._regEq(self.z80.l, 0xff)
        self.z80.ldHLnn(0x00, 0x01)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.h, 0x00)
        self._regEq(self.z80.l, 0x00)
        self.z80.ldHLnn(0x00, 0x00)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.h, 0xff)
        self._regEq(self.z80.l, 0xff)

    def test_incL(self):
        opc = 0x2c
        self._validOpc(opc, self.z80.incL, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.l, 1, 1, 4)
            self._regEq(self.z80.l, i & 0xff)

    def test_decL(self):
        opc = 0x2d
        self._validOpc(opc, self.z80.decL, 0)
        self.z80.l.ld(0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.l, i & 0xff)
            self._incOp8(opc, self.z80.l, -1, 1, 4)
        self.z80.l.ld(1)
        self._incOp8(opc, self.z80.l, -1, 1, 4)
        self._regEq(self.z80.l, 0)
        self.z80.l.ld(0)
        self._incOp8(opc, self.z80.l, -1, 1, 4)
        self._regEq(self.z80.l, 0xff)

    def test_ldLn(self):
        opc = 0x2e
        self._validOpc(opc, self.z80.ldLn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.l, i)

    def test_cpl(self):
        opc = 0x2f
        self._validOpc(opc, self.z80.cpl, 0)
        z, c = (self.z80.f.z.val(), self.z80.f.c.val())
        self.z80.f.h.reset()
        self.z80.f.n.reset()
        self.z80.a.ld(0x00)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0xff)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x00)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)
        self.z80.a.ld(0x5a)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0xa5)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.a, 0x5a)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)

    def test_jrNCn(self):
        opc = 0x30
        self._validOpc(opc, self.z80.jrNCn, 1)
        self.z80.f.c.set()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 126)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 0)
        self.z80.f.c.reset()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 129)

    def test_ldSPnn(self):
        opc = 0x31
        self._validOpc(opc, self.z80.ldSPnn, 2)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 3, 12, i * 2, i * 4)
            self._regEq(self.z80.sp, ((i * 2) << 8) + i * 4)

    def test_lddMemHLA(self):
        opc = 0x32
        self._validOpc(opc, self.z80.lddMemHLA, 0)
        test = lambda v, e: self._test_ldd(opc, self.z80.h, self.z80.l, v, e)
        test(0x0100, 0x00ff)
        test(0x0001, 0x0000)
        test(0x0000, 0xffff)

    def _test_ldd(self, opc, hiReg, loReg, param, value):
        hiReg.ld((param >> 8) & 0xff)
        loReg.ld(param & 0xff)
        self.z80.a.ld(0xa5)
        self.mem.set8(param, 0)
        self._flagsFixed(opc, 2, 8)
        self.assertEquals(self.mem.get8(param), self.z80.a.val())
        self._regEq(hiReg, (value >> 8) & 0xff)
        self._regEq(loReg, value & 0xff)

    def test_incSP(self):
        opc = 0x33
        self._validOpc(opc, self.z80.incSP, 0)
        init = 0xfff0
        self.z80.sp.ld(init)
        for i in range(0, 0x200):
            self._regEq(self.z80.sp, (init + i) & 0xffff)
            self._flagsFixed(opc, 1, 4)

    def test_incMemHL(self):
        opc = 0x34
        self._validOpc(opc, self.z80.incMemHL, 0)
        for i in range(1, 0x200):
            self.z80.n = True
            c = self.z80.f.c.val()
            self._timeOp(opc, 3, 12)
            val = self.mem.get8((self.z80.h.val() << 8) + self.z80.l.val())
            self.assertEquals(val, i & 0xff)
            self._flagEq(self.z80.f.z, i & 0xff == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.c, c)
            self._flagEq(self.z80.f.h, (i - 1) & 0xf == 0xf)

    def test_decMemHL(self):
        opc = 0x35
        self._validOpc(opc, self.z80.decMemHL, 0)
        self.z80.b.ld(0x1ff & 0xff)
        self.mem.set8((self.z80.h.val() << 8) + self.z80.l.val(), 0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            self.assertEquals(self.mem.get8(addr), i & 0xff)

            self.z80.n = False
            c = self.z80.f.c.val()
            self._timeOp(opc, 3, 12)
            self._flagEq(self.z80.f.z, (i - 1) & 0xff == 0)
            self._flagEq(self.z80.f.n, True)
            self._flagEq(self.z80.f.c, c)
            self._flagEq(self.z80.f.h, i & 0xf == 0x0)

    def test_ldMemHLn(self):
        opc = 0x36
        self._validOpc(opc, self.z80.ldMemHLn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 3, 12, i)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            self.assertEquals(self.mem.get8(addr), i)

    def test_scf(self):
        opc = 0x37
        self._validOpc(opc, self.z80.scf, 0)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.reset()
        self._timeOp(opc, 1, 4)
        self._regEq(self.z80.f.z, z)
        self._regEq(self.z80.f.n, False)
        self._regEq(self.z80.f.h, False)
        self._regEq(self.z80.f.c, True)

    def test_jrCn(self):
        opc = 0x38
        self._validOpc(opc, self.z80.jrCn, 1)
        self.z80.f.c.set()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 129)
        self.z80.f.c.reset()
        self.z80.pc.ld(126)
        self._flagsFixed(opc, 1, 4, 0x00)
        self._regEq(self.z80.pc, 126)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1, 4, 0xff)
        self._regEq(self.z80.pc, 0)

    def test_addHLSP(self):
        opc = 0x39
        self._validOpc(opc, self.z80.addHLSP, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.sp.ld(0x2367)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.sp.ld(0xffff)
        self._timeOp(opc, 3, 12)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9a)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x336 + 0xfff > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0xffff > 0xffff)

    def test_lddAMemHL(self):
        opc = 0x3a
        self._validOpc(opc, self.z80.lddAMemHL, 0)
        test = lambda v, e: self._test_lddm(opc, self.z80.h, self.z80.l, v, e)
        test(0x0100, 0x00ff)
        test(0x0001, 0x0000)
        test(0x0000, 0xffff)

    def _test_lddm(self, opc, hiReg, loReg, param, value):
        hiReg.ld((param >> 8) & 0xff)
        loReg.ld(param & 0xff)
        self.z80.a.ld(0)
        self.mem.set8(param, 0xa5)
        self._flagsFixed(opc, 2, 8)
        self._regEq(self.z80.a, self.mem.get8(param))
        self._regEq(hiReg, (value >> 8) & 0xff)
        self._regEq(loReg, value & 0xff)

    def test_decSP(self):
        opc = 0x3b
        self._validOpc(opc, self.z80.decSP, 0)
        self.z80.sp.ld(0x0100)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.sp, 0x00ff)
        self.z80.sp.ld(0x0001)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.sp, 0x0000)
        self.z80.sp.ld(0x0000)
        self._flagsFixed(opc, 1, 4)
        self._regEq(self.z80.sp, 0xffff)

    def test_incA(self):
        opc = 0x3c
        self._validOpc(opc, self.z80.incA, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.a, 1, 1, 4)
            self._regEq(self.z80.a, i & 0xff)

    def test_decA(self):
        opc = 0x3d
        self._validOpc(opc, self.z80.decA, 0)
        self.z80.a.ld(0x1ff & 0xff)
        for i in range(0x1ff, 0, -1):
            self._regEq(self.z80.a, i & 0xff)
            self._incOp8(opc, self.z80.a, -1, 1, 4)
        self.z80.a.ld(1)
        self._incOp8(opc, self.z80.a, -1, 1, 4)
        self._regEq(self.z80.a, 0)
        self.z80.a.ld(0)
        self._incOp8(opc, self.z80.a, -1, 1, 4)
        self._regEq(self.z80.a, 0xff)

    def test_ldAn(self):
        opc = 0x3e
        self._validOpc(opc, self.z80.ldAn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, 1, 4, i)
            self._regEq(self.z80.a, i)

    def test_ccf(self):
        opc = 0x3f
        self._validOpc(opc, self.z80.ccf, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.f.z.setTo(i % 2 == 0)
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._timeOp(opc, 1, 4)
            self._flagEq(self.z80.f.z, i % 2 == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, i % 2 == 0)

    def test_ldBB(self):
        self._test_ldRR(0x40, self.z80.ldBB, self.z80.b, self.z80.b)

    def test_ldBC(self):
        self._test_ldRR(0x41, self.z80.ldBC, self.z80.b, self.z80.c)

    def test_ldBD(self):
        self._test_ldRR(0x42, self.z80.ldBD, self.z80.b, self.z80.d)

    def test_ldBE(self):
        self._test_ldRR(0x43, self.z80.ldBE, self.z80.b, self.z80.e)

    def test_ldBH(self):
        self._test_ldRR(0x44, self.z80.ldBH, self.z80.b, self.z80.h)

    def test_ldBL(self):
        self._test_ldRR(0x45, self.z80.ldBL, self.z80.b, self.z80.l)

    def test_ldBMemHL(self):
        self._test_ldRMemHL(0x46, self.z80.ldBMemHL, self.z80.b)

    def test_ldBA(self):
        self._test_ldRR(0x47, self.z80.ldBA, self.z80.b, self.z80.a)

    def test_ldCB(self):
        self._test_ldRR(0x48, self.z80.ldCB, self.z80.c, self.z80.b)

    def test_ldCC(self):
        self._test_ldRR(0x49, self.z80.ldCC, self.z80.c, self.z80.c)

    def test_ldCD(self):
        self._test_ldRR(0x4a, self.z80.ldCD, self.z80.c, self.z80.d)

    def test_ldCE(self):
        self._test_ldRR(0x4b, self.z80.ldCE, self.z80.c, self.z80.e)

    def test_ldCH(self):
        self._test_ldRR(0x4c, self.z80.ldCH, self.z80.c, self.z80.h)

    def test_ldCL(self):
        self._test_ldRR(0x4d, self.z80.ldCL, self.z80.c, self.z80.l)

    def test_ldCMemHL(self):
        self._test_ldRMemHL(0x4e, self.z80.ldCMemHL, self.z80.c)

    def test_ldCA(self):
        self._test_ldRR(0x4f, self.z80.ldCA, self.z80.c, self.z80.a)

    def test_ldDB(self):
        self._test_ldRR(0x50, self.z80.ldDB, self.z80.d, self.z80.b)

    def test_ldDC(self):
        self._test_ldRR(0x51, self.z80.ldDC, self.z80.d, self.z80.c)

    def test_ldDD(self):
        self._test_ldRR(0x52, self.z80.ldDD, self.z80.d, self.z80.d)

    def test_ldDE(self):
        self._test_ldRR(0x53, self.z80.ldDE, self.z80.d, self.z80.e)

    def test_ldDH(self):
        self._test_ldRR(0x54, self.z80.ldDH, self.z80.d, self.z80.h)

    def test_ldDL(self):
        self._test_ldRR(0x55, self.z80.ldDL, self.z80.d, self.z80.l)

    def test_ldDMemHL(self):
        self._test_ldRMemHL(0x56, self.z80.ldDMemHL, self.z80.d)

    def test_ldDA(self):
        self._test_ldRR(0x57, self.z80.ldDA, self.z80.d, self.z80.a)

    def test_ldEB(self):
        self._test_ldRR(0x58, self.z80.ldEB, self.z80.e, self.z80.b)

    def test_ldEC(self):
        self._test_ldRR(0x59, self.z80.ldEC, self.z80.e, self.z80.c)

    def test_ldED(self):
        self._test_ldRR(0x5a, self.z80.ldED, self.z80.e, self.z80.d)

    def test_ldEE(self):
        self._test_ldRR(0x5b, self.z80.ldEE, self.z80.e, self.z80.e)

    def test_ldEH(self):
        self._test_ldRR(0x5c, self.z80.ldEH, self.z80.e, self.z80.h)

    def test_ldEL(self):
        self._test_ldRR(0x5d, self.z80.ldEL, self.z80.e, self.z80.l)

    def test_ldEMemHL(self):
        self._test_ldRMemHL(0x5e, self.z80.ldEMemHL, self.z80.e)

    def test_ldEA(self):
        self._test_ldRR(0x5f, self.z80.ldEA, self.z80.e, self.z80.a)

    def test_ldHB(self):
        self._test_ldRR(0x60, self.z80.ldHB, self.z80.h, self.z80.b)

    def test_ldHC(self):
        self._test_ldRR(0x61, self.z80.ldHC, self.z80.h, self.z80.c)

    def test_ldHD(self):
        self._test_ldRR(0x62, self.z80.ldHD, self.z80.h, self.z80.d)

    def test_ldHE(self):
        self._test_ldRR(0x63, self.z80.ldHE, self.z80.h, self.z80.e)

    def test_ldHH(self):
        self._test_ldRR(0x64, self.z80.ldHH, self.z80.h, self.z80.h)

    def test_ldHL(self):
        self._test_ldRR(0x65, self.z80.ldHL, self.z80.h, self.z80.l)

    def test_ldHMemHL(self):
        self._test_ldRMemHL(0x66, self.z80.ldHMemHL, self.z80.h)

    def test_ldHA(self):
        self._test_ldRR(0x67, self.z80.ldHA, self.z80.h, self.z80.a)

    def test_ldLB(self):
        self._test_ldRR(0x68, self.z80.ldLB, self.z80.l, self.z80.b)

    def test_ldLC(self):
        self._test_ldRR(0x69, self.z80.ldLC, self.z80.l, self.z80.c)

    def test_ldLD(self):
        self._test_ldRR(0x6a, self.z80.ldLD, self.z80.l, self.z80.d)

    def test_ldLE(self):
        self._test_ldRR(0x6b, self.z80.ldLE, self.z80.l, self.z80.e)

    def test_ldLH(self):
        self._test_ldRR(0x6c, self.z80.ldLH, self.z80.l, self.z80.h)

    def test_ldLL(self):
        self._test_ldRR(0x6d, self.z80.ldLL, self.z80.l, self.z80.l)

    def test_ldLMemHL(self):
        self._test_ldRMemHL(0x6e, self.z80.ldLMemHL, self.z80.l)

    def test_ldLA(self):
        self._test_ldRR(0x6f, self.z80.ldLA, self.z80.l, self.z80.a)

    def test_ldLA(self):
        self._test_ldRR(0x6f, self.z80.ldLA, self.z80.l, self.z80.a)

    def test_ldMemHLB(self):
        self._test_ldMemHLR(0x70, self.z80.ldMemHLB, self.z80.b)

    def test_ldMemHLC(self):
        self._test_ldMemHLR(0x71, self.z80.ldMemHLC, self.z80.c)

    def test_ldMemHLD(self):
        self._test_ldMemHLR(0x72, self.z80.ldMemHLD, self.z80.d)

    def test_ldMemHLE(self):
        self._test_ldMemHLR(0x73, self.z80.ldMemHLE, self.z80.e)

    def test_ldMemHLH(self):
        self._test_ldMemHLR(0x74, self.z80.ldMemHLH, self.z80.h)

    def test_ldMemHLL(self):
        self._test_ldMemHLR(0x75, self.z80.ldMemHLL, self.z80.l)

    def test_halt(self):
        opc = 0x76
        self._validOpc(opc, self.z80.halt, 0)

    def test_ldMemHLA(self):
        self._test_ldMemHLR(0x77, self.z80.ldMemHLA, self.z80.a)

    def test_ldAB(self):
        self._test_ldRR(0x78, self.z80.ldAB, self.z80.a, self.z80.b)

    def test_ldAC(self):
        self._test_ldRR(0x79, self.z80.ldAC, self.z80.a, self.z80.c)

    def test_ldAD(self):
        self._test_ldRR(0x7a, self.z80.ldAD, self.z80.a, self.z80.d)

    def test_ldAE(self):
        self._test_ldRR(0x7b, self.z80.ldAE, self.z80.a, self.z80.e)

    def test_ldAH(self):
        self._test_ldRR(0x7c, self.z80.ldAH, self.z80.a, self.z80.h)

    def test_ldAL(self):
        self._test_ldRR(0x7d, self.z80.ldAL, self.z80.a, self.z80.l)

    def test_ldAMemHL(self):
        self._test_ldRMemHL(0x7e, self.z80.ldAMemHL, self.z80.a)

    def test_ldAA(self):
        self._test_ldRR(0x7f, self.z80.ldAA, self.z80.a, self.z80.a)

    def test_addAB(self):
        self._test_addAR(0x80, self.z80.addAB, self.z80.b)

    def test_addAC(self):
        self._test_addAR(0x81, self.z80.addAC, self.z80.c)

    def test_addAD(self):
        self._test_addAR(0x82, self.z80.addAD, self.z80.d)

    def test_addAE(self):
        self._test_addAR(0x83, self.z80.addAE, self.z80.e)

    def test_addAH(self):
        self._test_addAR(0x84, self.z80.addAH, self.z80.h)

    def test_addAL(self):
        self._test_addAR(0x85, self.z80.addAL, self.z80.l)

    def test_addAMemHL(self):
        opc = 0x86
        self._validOpc(opc, self.z80.addAMemHL, 0)
        self.z80.a.ld(0x2b)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x47)
        self.z80.f.n.set()
        self._expectFlags(opc, 2, 8,
                          False, False, 0xa + 0x7 > 0xf, 0x2a + 0x47 > 0xff)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0xff)
        self._expectFlags(opc, 2, 8,
                          False, False, 0x2 + 0xf > 0xf, 0x72 + 0xff > 0xff)
        self._regEq(self.z80.a, 0x71)
        addr = 0xffff
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x8f)
        self._expectFlags(opc, 2, 8,
                          True, False, 0xf + 0x1 > 0xf, 0x71 + 0x8f > 0xff)
        self._regEq(self.z80.a, 0x00)

    def test_addAA(self):
        opc = 0x87
        self._validOpc(opc, self.z80.addAA, 0)
        self.z80.a.ld(0x47)
        self.z80.f.n.set()
        self._expectFlags(opc, 1, 4,
                          False, False, 0x7 + 0x7 > 0xf, 0x47 + 0x47 > 0xff)
        self._regEq(self.z80.a, 0x8e)
        self.z80.a.ld(0xff)
        self._expectFlags(opc, 1, 4,
                          False, False, 0xf + 0xf > 0xf, 0xff + 0xff > 0xff)
        self._regEq(self.z80.a, 0xfe)
        self.z80.a.ld(0x80)
        self._expectFlags(opc, 1, 4,
                          True, False, 0x0 + 0x0 > 0xf, 0x80 + 0x80 > 0xff)
        self._regEq(self.z80.a, 0x00)

    def test_adcAB(self):
        self._test_adcAR(0x88, self.z80.adcAB, self.z80.b)

    def test_adcAC(self):
        self._test_adcAR(0x89, self.z80.adcAC, self.z80.c)

    def test_adcAD(self):
        self._test_adcAR(0x8a, self.z80.adcAD, self.z80.d)

    def test_adcAE(self):
        self._test_adcAR(0x8b, self.z80.adcAE, self.z80.e)

    def test_adcAH(self):
        self._test_adcAR(0x8c, self.z80.adcAH, self.z80.h)

    def test_adcAL(self):
        self._test_adcAR(0x8d, self.z80.adcAL, self.z80.l)

    def test_adcAMemHL(self):
        opc = 0x8e
        self._validOpc(opc, self.z80.adcAMemHL, 0)
        self.z80.a.ld(0x73)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0xff)
        self.z80.f.n.set()
        self._expectFlags(opc, 2, 8,
                          False, False, 0x3 + 0xf > 0xf, True)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x01)
        self._expectFlags(opc, 2, 8,
                          False, False, 0x2 + 0x1 + 0x1 > 0xf, False)
        self._regEq(self.z80.a, 0x74)
        addr = 0xffff
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x8c)
        self._expectFlags(opc, 2, 8,
                          True, False, 0x4 + 0xc > 0xf, 0x74 + 0x8c > 0xff)
        self._regEq(self.z80.a, 0x00)

    def test_adcAA(self):
        opc = 0x8f
        self._validOpc(opc, self.z80.adcAA, 0)
        self.z80.a.ld(0x80)
        self._expectFlags(opc, 1, 4, True, False, 0x0 + 0x0 > 0xf, True)
        self._regEq(self.z80.a, 0x00)
        self.z80.f.n.set()
        self.z80.a.ld(0xff)
        self._expectFlags(opc, 1, 4, False, False, 0xf + 0x1 + 0x1 > 0xf, True)
        self._regEq(self.z80.a, 0xff)
        self.z80.a.ld(0x01)
        self._expectFlags(opc, 1, 4, False, False, 0x1 + 0x1 + 0x1 > 0xf, False)
        self._regEq(self.z80.a, 0x03)
        self.z80.a.ld(0x01)
        self._expectFlags(opc, 1, 4, False, False, 0x1 + 0x1 > 0xf, False)
        self._regEq(self.z80.a, 0x02)

    def test_subAB(self):
        self._test_subAR(0x90, self.z80.subAB, self.z80.b)

    def test_subAC(self):
        self._test_subAR(0x91, self.z80.subAC, self.z80.c)

    def test_subAD(self):
        self._test_subAR(0x92, self.z80.subAD, self.z80.d)

    def test_subAE(self):
        self._test_subAR(0x93, self.z80.subAE, self.z80.e)

    def test_subAH(self):
        self._test_subAR(0x94, self.z80.subAH, self.z80.h)

    def test_subAL(self):
        self._test_subAR(0x95, self.z80.subAL, self.z80.l)

    def test_subAMemHL(self):
        opc = 0x96
        self._validOpc(opc, self.z80.subAMemHL, 0)
        self.z80.a.ld(0x9c)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x2a)
        self.z80.f.n.reset()
        self._expectFlags(opc, 2, 8, False, True, 0xc < 0xa, 0x9c < 0x2a)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0xff)
        self._expectFlags(opc, 2, 8, False, True, 0x2 < 0xf, 0x72 < 0xff)
        self._regEq(self.z80.a, 0x73)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x73)
        self._expectFlags(opc, 2, 8, True, True, 0x3 < 0x3, 0x73 < 0x73)
        self._regEq(self.z80.a, 0x00)

    def test_subAA(self):
        opc = 0x97
        self._validOpc(opc, self.z80.subAA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.f.z.reset()
            self.z80.f.n.reset()
            self.z80.f.h.set()
            self.z80.f.c.set()
            self._expectFlags(opc, 1, 4, True, True, False, False)

    def test_sbcAB(self):
        self._test_sbcAR(0x98, self.z80.sbcAB, self.z80.b)

    def test_sbcAC(self):
        self._test_sbcAR(0x99, self.z80.sbcAC, self.z80.c)

    def test_sbcAD(self):
        self._test_sbcAR(0x9a, self.z80.sbcAD, self.z80.d)

    def test_sbcAE(self):
        self._test_sbcAR(0x9b, self.z80.sbcAE, self.z80.e)

    def test_sbcAH(self):
        self._test_sbcAR(0x9c, self.z80.sbcAH, self.z80.h)

    def test_sbcAL(self):
        self._test_sbcAR(0x9d, self.z80.sbcAL, self.z80.l)

    def test_sbcAMemHL(self):
        opc = 0x9e
        self._validOpc(opc, self.z80.sbcAMemHL, 0)
        self.z80.a.ld(0x0e)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x9c)
        self.z80.f.n.reset()
        self._expectFlags(opc, 2, 8, False, True, 0xe < 0xc, True)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x01)
        self._expectFlags(opc, 2, 8,
                          False, True, 0x2 < 0x1 + 0x1, False)
        self._regEq(self.z80.a, 0x70)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0x70)
        self._expectFlags(opc, 2, 8, True, True, 0x0 < 0x0, 0x70 < 0x70)
        self._regEq(self.z80.a, 0x00)

    def test_sbcAA(self):
        opc = 0x9f
        self._validOpc(opc, self.z80.sbcAA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.f.z.reset()
            self.z80.f.n.reset()
            self.z80.f.h.set()
            self.z80.f.c.reset()
            self._expectFlags(opc, 1, 4, True, True, False, False)
            self._regEq(self.z80.a, 0x00)
        self.z80.a.ld(0x00)
        self.z80.f.z.reset()
        self.z80.f.n.reset()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, False, True, True, True)
        self._regEq(self.z80.a, 0xff)
        self.z80.f.c.reset()
        self._expectFlags(opc, 1, 4, True, True, False, False)
        self._regEq(self.z80.a, 0x00)

    def test_andB(self):
        self._test_andR(0xa0, self.z80.andB, self.z80.b)

    def test_andC(self):
        self._test_andR(0xa1, self.z80.andC, self.z80.c)

    def test_andD(self):
        self._test_andR(0xa2, self.z80.andD, self.z80.d)

    def test_andE(self):
        self._test_andR(0xa3, self.z80.andE, self.z80.e)

    def test_andH(self):
        self._test_andR(0xa4, self.z80.andH, self.z80.h)

    def test_andL(self):
        self._test_andR(0xa5, self.z80.andL, self.z80.l)

    def test_andMemHL(self):
        opc = 0xa6
        self._validOpc(opc, self.z80.andMemHL, 0)
        self.z80.a.ld(0b0011)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, 2, 8, False, False, True, False)
        self._regEq(self.z80.a, 0b0001)
        self.assertEquals(self.mem.get8(addr), 0b0101)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, 2, 8, True, False, True, False)
        self._regEq(self.z80.a, 0)
        self.assertEquals(self.mem.get8(addr), 0)

    def test_andA(self):
        opc = 0xa7
        self._validOpc(opc, self.z80.andA, 0)
        self.z80.a.ld(0b01)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, False, False, True, False)
        self._regEq(self.z80.a, 0b01)
        self.z80.a.ld(0)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, True, False, True, False)
        self._regEq(self.z80.a, 0)

    def test_xorB(self):
        self._test_xorR(0xa8, self.z80.xorB, self.z80.b)

    def test_xorC(self):
        self._test_xorR(0xa9, self.z80.xorC, self.z80.c)

    def test_xorD(self):
        self._test_xorR(0xaa, self.z80.xorD, self.z80.d)

    def test_xorE(self):
        self._test_xorR(0xab, self.z80.xorE, self.z80.e)

    def test_xorH(self):
        self._test_xorR(0xac, self.z80.xorH, self.z80.h)

    def test_xorL(self):
        self._test_xorR(0xad, self.z80.xorL, self.z80.l)

    def test_xorMemHL(self):
        opc = 0xae
        self._validOpc(opc, self.z80.xorMemHL, 0)
        self.z80.a.ld(0b0011)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 2, 8, False, False, False, False)
        self._regEq(self.z80.a, 0b0110)
        self.assertEquals(self.mem.get8(addr), 0b0101)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        val = self.z80.a.val()
        self.mem.set8(addr, val)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 2, 8, True, False, False, False)
        self._regEq(self.z80.a, 0)
        self.assertEquals(self.mem.get8(addr), val)

    def test_xorA(self):
        opc = 0xaf
        self._validOpc(opc, self.z80.xorA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.f.z.reset()
            self.z80.f.n.set()
            self.z80.f.h.set()
            self.z80.f.c.set()
            self._expectFlags(opc, 1, 4, True, False, False, False)
            self._regEq(self.z80.a, 0)

    def test_orB(self):
        self._test_orR(0xb0, self.z80.orB, self.z80.b)

    def test_orC(self):
        self._test_orR(0xb1, self.z80.orC, self.z80.c)

    def test_orD(self):
        self._test_orR(0xb2, self.z80.orD, self.z80.d)

    def test_orE(self):
        self._test_orR(0xb3, self.z80.orE, self.z80.e)

    def test_orH(self):
        self._test_orR(0xb4, self.z80.orH, self.z80.h)

    def test_orL(self):
        self._test_orR(0xb5, self.z80.orL, self.z80.l)

    def test_orMemHL(self):
        opc = 0xb6
        self._validOpc(opc, self.z80.orMemHL, 0)
        self.z80.a.ld(0b0011)
        addr = 0xdead
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 2, 8, False, False, False, False)
        self._regEq(self.z80.a, 0b0111)
        self.assertEquals(self.mem.get8(addr), 0b0101)
        self.z80.a.ld(0)
        addr = 0xbeef
        self.z80.ldHLnn(addr >> 8, addr & 0xff)
        self.mem.set8(addr, 0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 2, 8, True, False, False, False)
        self._regEq(self.z80.a, 0)
        self.assertEquals(self.mem.get8(addr), 0)

    def test_orA(self):
        opc = 0xb7
        self._validOpc(opc, self.z80.orA, 0)
        self.z80.a.ld(0b0011)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, False, False, False, False)
        self._regEq(self.z80.a, 0b0011)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, True, False, False, False)
        self._regEq(self.z80.a, 0)

    def test_cpB(self):
        self._test_cpR(0xb8, self.z80.cpB, self.z80.b)

    def test_cpC(self):
        self._test_cpR(0xb9, self.z80.cpC, self.z80.c)

    def test_cpD(self):
        self._test_cpR(0xba, self.z80.cpD, self.z80.d)

    def test_cpE(self):
        self._test_cpR(0xbb, self.z80.cpE, self.z80.e)

    def test_cpH(self):
        self._test_cpR(0xbc, self.z80.cpH, self.z80.h)

    def test_cpL(self):
        self._test_cpR(0xbd, self.z80.cpL, self.z80.l)

    def test_cpMemHL(self):
        opc = 0xbe
        self._validOpc(opc, self.z80.cpMemHL, 0)
        confs = [(0x9c, 0x2a, 0xdead),
                 (0x72, 0xff, 0xbeef),
                 (0x73, 0x73, 0xffff)]
        for conf in confs:
            a, v, addr = conf
            self.z80.a.ld(a)
            self.z80.ldHLnn(addr >> 8, addr & 0xff)
            self.mem.set8(addr, v)
            self.z80.f.n.reset()
            self._expectFlags(opc, 2, 8,
                              a == v, True, (a & 0xf) < (v & 0xf), a < v)
            self._regEq(self.z80.a, a)

    def test_cpA(self):
        opc = 0xbf
        self._validOpc(opc, self.z80.cpA, 0)
        for a in range(0, self.NUM_TESTS):
            self.z80.a.ld(a)
            self.z80.f.n.reset()
            self._expectFlags(opc, 1, 4, True, True, False, False)
            self._regEq(self.z80.a, a)

    def test_retNZ(self):
        opc = 0xc0
        self._validOpc(opc, self.z80.retNZ, 0)
        self.z80.f.z.reset()
        self._test_retNZ(opc, 0xdead, 0xffff, 0xbeef, 0xbeef)
        self._test_retNZ(opc, 0xbeef, 0xffff, 0xdead, 0xdead)
        self.z80.f.z.set()
        self._test_retNZ(opc, 0xdead, 0xffff, 0xbeef, 0)
        self._test_retNZ(opc, 0xbeef, 0xffff, 0xdead, 0)

    def _test_retNZ(self, opc, sp, pcInit, pcVal, expected):
        self.mem.set8(sp + 1, pcVal >> 8)
        self.mem.set8(sp, pcVal & 0xff)
        self.z80.sp.ld(sp)
        self.z80.pc.ld(pcInit)
        self._flagsFixed(opc, 2, 8)
        if self.z80.f.z.val():
            self._regEq(self.z80.pc, pcInit)
            self._regEq(self.z80.sp, sp)
        else:
            self._regEq(self.z80.pc, pcVal)
            self._regEq(self.z80.sp, sp + 2)

    def test_popBC(self):
        opc = 0xc1
        self._validOpc(opc, self.z80.popBC, 0)
        self.z80.sp.ld(0xfffe)
        vals = [0xa5a5, 0x5a5a, 0xdead, 0xbeef]
        for val in vals:
            self._push16(val)
        vals.reverse()
        for val in vals:
            self._flagsFixed(opc, 3, 12)
            self._regEq(self.z80.b, val >> 8)
            self._regEq(self.z80.c, val & 0xff)

    def test_jpNZnn(self):
        opc = 0xc2
        self._validOpc(opc, self.z80.jpNZnn, 2)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            pc = self.z80.pc.val()
            self._flagsFixed(opc, 3, 12, i * 2, i * 4)
            if z:
                self._regEq(self.z80.pc, pc)
            else:
                self._regEq(self.z80.pc, ((i * 4) << 8) + (i * 2))

    def _push16(self, val):
        self._push8(val >> 8)
        self._push8(val & 0xff)

    def _push8(self, val):
        sp = self.z80.sp.val() - 1
        self.z80.sp.ld(sp)
        self.mem.set8(sp, val)

    def _validOpc(self, opc, func, argc):
        self.assertTrue(opc < len(self.z80.instr),
            "Opcode out of instruction range")
        func_, argc_ = self.z80.instr[opc]
        self.assertEquals(func, func_,
            "Opcode should be 0x%02x(%d)" % (opc, opc))
        self.assertEquals(argc, argc_,
            "Instruction should take %d args, got %d" % (argc, argc_))

    def _incOp8(self, opc, reg, inc, m_, t_, a=None, b=None):
        if inc == 0:
            raise ValueError("Can't increase register by 0")
        else:
            pos = inc > 0
        val = reg.val()
        self.z80.n = pos
        c = self.z80.f.c.val()
        self._timeOp(opc, m_, t_, a, b)
        self._flagEq(self.z80.f.z, reg.val() == 0)
        self._flagEq(self.z80.f.n, not pos)
        self._flagEq(self.z80.f.c, c)
        self._flagEq(self.z80.f.h, val & 0xf == 0xf if pos else val & 0xf == 0x0)

    def _flagsFixed(self, opc, m_, t_, a=None, b=None):
        """Flags are unaffected by running instruction opc with a and b"""
        f = self.z80.f
        self._expectFlags(opc, m_, t_, f.z.val(), f.n.val(), f.h.val(),
                          f.c.val(), a, b)

    def _timeOp(self, opc, m_, t_, a=None, b=None):
        m = self.z80.m
        t = self.z80.t
        self._runOp(opc, a, b)
        self.assertEqual(self.z80.m, m + m_)
        self.assertEqual(self.z80.t, t + t_)

    def _runOp(self, opc, a=None, b=None):
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

    def _flagEq(self, flag, val):
        self.assertEquals(flag.val(), val, "Flag %s is 0x%d, should be 0x%d" %
            (flag.name(), flag.val(), val))

    def _regEq(self, reg, val):
        self.assertEquals(reg.val(), val,
                "Register %s is 0x%02x(%d), should be 0x%02x(%d)"
                % (reg.name(), reg.val(), reg.val(), val, val))

    def _test_ldRR(self, opc, func, dstReg, srcReg):
        self._validOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            val = i * 2
            srcReg.ld(val)
            self._flagsFixed(opc, 1, 4)
            self._regEq(dstReg, val)

    def _test_ldRMemHL(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.h.ld(i * 4)
            self.z80.l.ld(i * 2)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            val = (i * 7) & 0xff
            self.mem.set8(addr, val)
            self._flagsFixed(opc, 2, 8)
            self._regEq(reg, val)

    def _test_ldMemHLR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            val = (i * 7) & 0xff
            self.z80.h.ld(val if reg == self.z80.h else i * 4)
            self.z80.l.ld(val if reg == self.z80.l else i * 2)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            reg.ld(val)
            self._flagsFixed(opc, 2, 8)
            self.assertEquals(self.mem.get8(addr), reg.val())

    def _test_addAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x2b)
        self.z80.f.n.set()
        reg.ld(0x47)
        self._expectFlags(opc, 1, 4,
                          False, False, 0xa + 0x7 > 0xf, 0x2a + 0x47 > 0xff)
        self._regEq(self.z80.a, 0x72)
        reg.ld(0xff)
        self._expectFlags(opc, 1, 4,
                          False, False, 0x2 + 0xf > 0xf, 0x72 + 0xff > 0xff)
        self._regEq(self.z80.a, 0x71)
        reg.ld(0x8f)
        self._expectFlags(opc, 1, 4,
                          True, False, 0xf + 0x1 > 0xf, 0x71 + 0x8f > 0xff)
        self._regEq(self.z80.a, 0x00)

    def _test_adcAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x73)
        self.z80.f.n.set()
        reg.ld(0xff)
        self._expectFlags(opc, 1, 4, False, False, 0x3 + 0xf > 0xf, True)
        self._regEq(self.z80.a, 0x72)
        reg.ld(0x01)
        self._expectFlags(opc, 1, 4,
                          False, False, 0x2 + 0x1 + 0x1 > 0xf, False)
        self._regEq(self.z80.a, 0x74)
        reg.ld(0x8c)
        self._expectFlags(opc, 1, 4,
                          True, False, 0x4 + 0xc > 0xf, 0x74 + 0x8c > 0xff)
        self._regEq(self.z80.a, 0x00)

    def _test_subAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x9c)
        self.z80.f.n.reset()
        reg.ld(0x2a)
        self._expectFlags(opc, 1, 4, False, True, 0xc < 0xa, 0x9c < 0x2a)
        self._regEq(self.z80.a, 0x72)
        reg.ld(0xff)
        self._expectFlags(opc, 1, 4, False, True, 0x2 < 0xf, 0x72 < 0xff)
        self._regEq(self.z80.a, 0x73)
        reg.ld(0x73)
        self._expectFlags(opc, 1, 4, True, True, 0x3 < 0x3, 0x73 < 0x73)
        self._regEq(self.z80.a, 0x00)

    def _test_sbcAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x9c)
        self.z80.f.n.reset()
        reg.ld(0xff)
        self._expectFlags(opc, 1, 4, False, True, 0xc < 0xf, True)
        self._regEq(self.z80.a, 0x9d)
        reg.ld(0x01)
        self._expectFlags(opc, 1, 4, False, True, 0xd < 0x1, False)
        self._regEq(self.z80.a, 0x9b)
        reg.ld(0x9b)
        self._expectFlags(opc, 1, 4, True, True, 0xb < 0xb, 0x9b < 0x9b)
        self._regEq(self.z80.a, 0x00)

    def _expectFlags(self, opc, m, t, z, n, h, c, a=None, b=None):
        self._timeOp(opc, m, t, a, b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, n)
        self._flagEq(self.z80.f.h, h)
        self._flagEq(self.z80.f.c, c)

    def _test_andR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0b0011)
        reg.ld(0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, False, False, True, False)
        self._regEq(self.z80.a, 0b0001)
        self._regEq(reg, 0b0101)
        reg.ld(0)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, True, False, True, False)
        self._regEq(self.z80.a, 0)
        self._regEq(reg, 0)

    def _test_xorR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0b0011)
        reg.ld(0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, False, False, False, False)
        self._regEq(self.z80.a, 0b0110)
        self._regEq(reg, 0b0101)
        val = self.z80.a.val()
        reg.ld(val)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, True, False, False, False)
        self._regEq(self.z80.a, 0)
        self._regEq(reg, val)

    def _test_orR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0b0011)
        reg.ld(0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, False, False, False, False)
        self._regEq(self.z80.a, 0b0111)
        self._regEq(reg, 0b0101)
        self.z80.a.ld(0)
        reg.ld(0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, 1, 4, True, False, False, False)
        self._regEq(self.z80.a, 0)
        self._regEq(reg, 0)

    def _test_cpR(self, opc, func, reg):
        for regVal in [(0x9c, 0x2a), (0x72, 0xff), (0x73, 0x73)]:
            a, v = regVal
            self.z80.a.ld(a)
            reg.ld(v)
            self.z80.f.n.reset()
            self._expectFlags(opc, 1, 4,
                              a == v, True, (a & 0xf) < (v & 0xf), a < v)
            self._regEq(self.z80.a, a)

    def tearDown(self):
        self.mem = None
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
