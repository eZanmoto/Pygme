# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu import z80
from pygme.memory import array


class TestZ80(unittest.TestCase):
    """
    Tests for Z80 class.

    When a parameter to a method is a function, the parameter name
    should ideally be suffixed with 'f'.

    MSB and LSB stand for most significant byte and least significant
    byte, respectively.

    r8 and r16 denote an 8-bit and a 16-bit register, respectively.
    """

    # The default number of times each test should be run
    NUM_TESTS = 10

    def setUp(self):
        self.mem = array.Array(1 << 16)
        self.z80 = z80.Z80(self.mem)

    def test_notInstrs(self):
        opcs = [0xcb,
                0xd3,
                0xdb,
                0xdd,
                0xe3,
                0xe4,
                0xeb,
                0xec,
                0xed,
                0xf2,
                0xf4,
                0xfc,
                0xfd,
                ]
        for opc in opcs:
            with self.assertRaises(RuntimeError):
                func, argc = self.z80.instr[opc]
                self.assertEquals(argc, 0)
                func()

    def test_nop(self):
        opc = 0x00
        self._validOpc(opc, self.z80.nop, 0)
        for _ in range(0, self.NUM_TESTS):
            self._flagsFixed(opc)

    def test_ldBCnn(self):
        self._test_ldr16nn(0x01, self.z80.ldBCnn,
                           self._r16valffromr8r8(self.z80.b, self.z80.c))

    def _r16valffromr8r8(self, hireg, loreg):
        """
        Create a function that gets the value of two 8-bit registers as a
        single integer.
        """
        return lambda: (hireg.val() << 8) + loreg.val()

    def _test_ldr16nn(self, opc, func, getf):
        self._validOpc(opc, func, 2)
        lsbmsbs = [(0x00, 0xff),
                   (0x01, 0xfe),
                   ]
        for lsbmsb in lsbmsbs:
            lsb, msb = lsbmsb
            self._flagsFixed(opc, lsb, msb)
            self.assertEquals(getf(), (msb << 8) + lsb)

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
            self._flagsFixed(opc)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())

    def test_incBC(self):
        opc = 0x03
        self._validOpc(opc, self.z80.incBC, 0)
        self._regEq(self.z80.b, 0)
        for i in range(0, 0x200):
            self._regEq(self.z80.c, i & 0xff)
            self._flagsFixed(opc)
        self._regEq(self.z80.b, 2)

    def test_incB(self):
        opc = 0x04
        self._validOpc(opc, self.z80.incB, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.b, 1)
            self._regEq(self.z80.b, i & 0xff)

    def test_decB(self):
        self._test_decr8(0x05, self.z80.decB, 0, self.z80.b)

    def _test_decr8(self, opc, func, argc, reg):
        self._validOpc(opc, func, argc)
        reg.ld(0x02)
        self._incOp8(opc, reg, -1)
        self._regEq(reg, 0x01)
        self._incOp8(opc, reg, -1)
        self._regEq(reg, 0x00)
        self._incOp8(opc, reg, -1)
        self._regEq(reg, 0xff)
        self._incOp8(opc, reg, -1)
        self._regEq(reg, 0xfe)

    def test_ldBn(self):
        opc = 0x06
        self._validOpc(opc, self.z80.ldBn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.b, i)

    def test_ldBn_maxValue(self):
        self.z80.ldBn(0xff)
        with self.assertRaises(ValueError):
            self.z80.ldBn(0x100)

    def test_ldBn_minValue(self):
        self.z80.ldBn(0)
        with self.assertRaises(ValueError):
            self.z80.ldBn(-1)

    def test_rlca(self):
        opc = 0x07
        self._validOpc(opc, self.z80.rlca, 0)
        self.z80.a.ld(1)
        for i in range(0, self.NUM_TESTS):
            self._regEq(self.z80.a, (1 << (i % 8)) & 0xff)
            c = (self.z80.a.val() >> 7) & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runOp(opc)
            self._flagEq(self.z80.f.z, self.z80.a.val() == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self.z80.f.c.reset()
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self._runOp(opc)
        self._flagEq(self.z80.f.z, True)

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
        self._runOp(opc)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.b.ld(0xff)
        self.z80.c.ld(0xff)
        self._runOp(opc)
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
            self._flagsFixed(opc)
            self._regEq(self.z80.a, val)

    def test_decBC(self):
        self._test_decr8r8(0x0b, self.z80.decBC, 0, self.z80.ldBCnn,
                           self.z80.b, self.z80.c)

    def _test_decr8r8(self, opc, func, argc, setr8r8f, hireg, loreg):
        setr16f = lambda v: setr8r8f(v & 0xff, v >> 8)
        getf = lambda: (hireg.val() << 8) + loreg.val()
        self._test_decr16(opc, func, argc, setr16f, getf)

    def _test_decr16(self, opc, func, argc, setf, getf):
        srctgts = [(0x0101, 0x0100),
                   (0x0100, 0x00ff),
                   (0x0002, 0x0001),
                   (0x0001, 0x0000),
                   (0x0000, 0xffff),
                   (0xffff, 0xfffe),
                   (0xff00, 0xfeff),
                   ]
        self._validOpc(opc, func, argc)
        for srctgt in srctgts:
            src, tgt = srctgt
            setf(src)
            self._flagsFixed(opc)
            self.assertEquals(tgt, getf())

    def test_incC(self):
        opc = 0x0c
        self._validOpc(opc, self.z80.incC, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.c, 1)
            self._regEq(self.z80.c, i & 0xff)

    def test_decC(self):
        self._test_decr8(0x0d, self.z80.decC, 0, self.z80.c)

    def test_ldCn(self):
        opc = 0x0e
        self._validOpc(opc, self.z80.ldCn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.c, i)

    def test_rrca(self):
        opc = 0x0f
        self._validOpc(opc, self.z80.rrca, 0)
        self.z80.a.ld(0x80)
        self.z80.f.n.set()
        self.z80.f.h.set()
        for i in range(0, self.NUM_TESTS):
            self._regEq(self.z80.a, (0x80 >> (i % 8)) & 0xff)
            c = self.z80.a.val() & 1
            self._runOp(opc)
            self._flagEq(self.z80.f.z, self.z80.a.val() == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self.z80.a.ld(1)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x80)
        self._flagEq(self.z80.f.c, True)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x40)
        self._flagEq(self.z80.f.c, False)
        self.z80.f.c.reset()
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self._runOp(opc)
        self._flagEq(self.z80.f.z, True)

    def test_stop(self):
        opc = 0x10
        self._validOpc(opc, self.z80.stop, 0)

    def test_ldDEnn(self):
        self._test_ldr16nn(0x11, self.z80.ldDEnn,
                           self._r16valffromr8r8(self.z80.d, self.z80.e))

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
            self._flagsFixed(opc)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())

    def test_incDE(self):
        opc = 0x13
        self._validOpc(opc, self.z80.incDE, 0)
        self._regEq(self.z80.d, 0)
        for i in range(0, 0x200):
            self._regEq(self.z80.e, i & 0xff)
            self._flagsFixed(opc)
        self._regEq(self.z80.d, 2)

    def test_incD(self):
        opc = 0x14
        self._validOpc(opc, self.z80.incD, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.d, 1)
            self._regEq(self.z80.d, i & 0xff)

    def test_decD(self):
        self._test_decr8(0x15, self.z80.decD, 0, self.z80.d)

    def test_ldDn(self):
        opc = 0x16
        self._validOpc(opc, self.z80.ldDn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.d, i)

    def test_rla(self):
        opc = 0x17
        self._validOpc(opc, self.z80.rla, 0)
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.a.ld(0x80)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, True)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x01)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x02)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)

    def test_jrn(self):
        opc = 0x18
        self._validOpc(opc, self.z80.jrn, 1)
        self._test_jrcn(opc, True)

    def test_addHLDE(self):
        opc = 0x19
        self._validOpc(opc, self.z80.addHLDE, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.d.ld(0x23)
        self.z80.e.ld(0x67)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._runOp(opc)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.d.ld(0xff)
        self.z80.e.ld(0xff)
        self._runOp(opc)
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
            self._flagsFixed(opc)
            self._regEq(self.z80.a, val)

    def test_decDE(self):
        self._test_decr8r8(0x1b, self.z80.decDE, 0, self.z80.ldDEnn,
                           self.z80.d, self.z80.e)

    def test_incE(self):
        opc = 0x1c
        self._validOpc(opc, self.z80.incE, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.e, 1)
            self._regEq(self.z80.e, i & 0xff)

    def test_decE(self):
        self._test_decr8(0x1d, self.z80.decE, 0, self.z80.e)

    def test_ldEn(self):
        opc = 0x1e
        self._validOpc(opc, self.z80.ldEn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.e, i)

    def test_rra(self):
        opc = 0x1f
        self._validOpc(opc, self.z80.rra, 0)
        self.z80.a.ld(0x02)
        self.z80.f.n.set()
        self.z80.f.h.set()
        self._runOp(opc)
        self._regEq(self.z80.a, 0x01)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, True)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x80)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x40)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)

    def test_jrNZn(self):
        opc = 0x20
        self._validOpc(opc, self.z80.jrNZn, 1)
        self.z80.f.z.set()
        self._test_jrcn(opc, False)
        self.z80.f.z.reset()
        self._test_jrcn(opc, True)

    def test_ldHLnn(self):
        self._test_ldr16nn(0x21, self.z80.ldHLnn,
                           self._r16valffromr8r8(self.z80.h, self.z80.l))

    def test_ldiMemHLA(self):
        opc = 0x22
        self._validOpc(opc, self.z80.ldiMemHLA, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.a.ld(i)
            self.z80.h.ld(i * 2)
            self.z80.l.ld(i * 4)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            self.assertEquals(self.mem.get8(addr), 0)
            self._flagsFixed(opc)
            self.assertEquals(self.mem.get8(addr), self.z80.a.val())
            self._regEq(self.z80.l, (i * 4 + 1) & 0xff)
            self._regEq(self.z80.h, (i * 2) + ((i * 4 + 1) >> 8))

    def test_incHL(self):
        opc = 0x23
        self._validOpc(opc, self.z80.incHL, 0)
        self._regEq(self.z80.h, 0)
        for i in range(0, 0x200):
            self._regEq(self.z80.l, i & 0xff)
            self._flagsFixed(opc)
        self._regEq(self.z80.h, 2)

    def test_incH(self):
        opc = 0x24
        self._validOpc(opc, self.z80.incH, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.h, 1)
            self._regEq(self.z80.h, i & 0xff)

    def test_decH(self):
        self._test_decr8(0x25, self.z80.decH, 0, self.z80.h)

    def test_ldHn(self):
        opc = 0x26
        self._validOpc(opc, self.z80.ldHn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.h, i)

    def test_daa(self):
        opc = 0x27
        self._validOpc(opc, self.z80.daa, 0)

    def test_jrZn(self):
        opc = 0x28
        self._validOpc(opc, self.z80.jrZn, 1)
        self.z80.f.z.set()
        self._test_jrcn(opc, True)
        self.z80.f.z.reset()
        self._test_jrcn(opc, False)

    def test_addHLHL(self):
        opc = 0x29
        self._validOpc(opc, self.z80.addHLHL, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x36)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._runOp(opc)
        self._regEq(self.z80.h, 0x26)
        self._regEq(self.z80.l, 0x6c)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x133 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1336 + 0x1336 > 0xffff)
        self.z80.h.ld(0xff)
        self.z80.l.ld(0xff)
        self._runOp(opc)
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
            self._flagsFixed(opc)
            self._regEq(self.z80.a, val)
            if i * 4 == 0xff:
                self._regEq(self.z80.h, i * 2 + 1)
                self._regEq(self.z80.l, 0)
            else:
                self._regEq(self.z80.h, i * 2)
                self._regEq(self.z80.l, i * 4 + 1)
        self.z80.h.ld(0x00)
        self.z80.l.ld(0xff)
        self._flagsFixed(opc)
        self._regEq(self.z80.h, 0x01)
        self._regEq(self.z80.l, 0x00)

    def test_decHL(self):
        self._test_decr8r8(0x2b, self.z80.decHL, 0, self.z80.ldHLnn,
                           self.z80.h, self.z80.l)

    def test_incL(self):
        opc = 0x2c
        self._validOpc(opc, self.z80.incL, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.l, 1)
            self._regEq(self.z80.l, i & 0xff)

    def test_decL(self):
        self._test_decr8(0x2d, self.z80.decL, 0, self.z80.l)

    def test_ldLn(self):
        opc = 0x2e
        self._validOpc(opc, self.z80.ldLn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.l, i)

    def test_cpl(self):
        opc = 0x2f
        self._validOpc(opc, self.z80.cpl, 0)
        z, c = (self.z80.f.z.val(), self.z80.f.c.val())
        self.z80.f.h.reset()
        self.z80.f.n.reset()
        self.z80.a.ld(0x00)
        self._runOp(opc)
        self._regEq(self.z80.a, 0xff)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x00)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)
        self.z80.a.ld(0x5a)
        self._runOp(opc)
        self._regEq(self.z80.a, 0xa5)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)
        self._runOp(opc)
        self._regEq(self.z80.a, 0x5a)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, c)

    def test_jrNCn(self):
        opc = 0x30
        self._validOpc(opc, self.z80.jrNCn, 1)
        self.z80.f.c.set()
        self._test_jrcn(opc, False)
        self.z80.f.c.reset()
        self._test_jrcn(opc, True)

    def test_ldSPnn(self):
        self._test_ldr16nn(0x31, self.z80.ldSPnn, self.z80.sp.val)

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
        self._flagsFixed(opc)
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
            self._flagsFixed(opc)

    def test_incMemHL(self):
        opc = 0x34
        self._validOpc(opc, self.z80.incMemHL, 0)
        for i in range(1, 0x200):
            self.z80.n = True
            c = self.z80.f.c.val()
            self._runOp(opc)
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
            self._runOp(opc)
            self._flagEq(self.z80.f.z, (i - 1) & 0xff == 0)
            self._flagEq(self.z80.f.n, True)
            self._flagEq(self.z80.f.c, c)
            self._flagEq(self.z80.f.h, i & 0xf == 0x0)

    def test_ldMemHLn(self):
        opc = 0x36
        self._validOpc(opc, self.z80.ldMemHLn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            self.assertEquals(self.mem.get8(addr), i)

    def test_scf(self):
        opc = 0x37
        self._validOpc(opc, self.z80.scf, 0)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.reset()
        self._runOp(opc)
        self._regEq(self.z80.f.z, z)
        self._regEq(self.z80.f.n, False)
        self._regEq(self.z80.f.h, False)
        self._regEq(self.z80.f.c, True)

    def test_jrCn(self):
        opc = 0x38
        self._validOpc(opc, self.z80.jrCn, 1)
        self.z80.f.c.set()
        self._test_jrcn(opc, True)
        self.z80.f.c.reset()
        self._test_jrcn(opc, False)

    def test_addHLSP(self):
        opc = 0x39
        self._validOpc(opc, self.z80.addHLSP, 0)
        self.z80.h.ld(0x13)
        self.z80.l.ld(0x34)
        self.z80.sp.ld(0x2367)
        z = self.z80.f.z.val()
        self.z80.f.n.set()
        self._runOp(opc)
        self._regEq(self.z80.h, 0x36)
        self._regEq(self.z80.l, 0x9b)
        self._flagEq(self.z80.f.z, z)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, 0x133 + 0x236 > 0xfff)
        self._flagEq(self.z80.f.c, 0x1334 + 0x2367 > 0xffff)
        self.z80.sp.ld(0xffff)
        self._runOp(opc)
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
        self._flagsFixed(opc)
        self._regEq(self.z80.a, self.mem.get8(param))
        self._regEq(hiReg, (value >> 8) & 0xff)
        self._regEq(loReg, value & 0xff)

    def test_decSP(self):
        self._test_decr16(0x3b, self.z80.decSP, 0, self.z80.sp.ld,
                          self.z80.sp.val)

    def test_incA(self):
        opc = 0x3c
        self._validOpc(opc, self.z80.incA, 0)
        for i in range(1, 0x200):
            self._incOp8(opc, self.z80.a, 1)
            self._regEq(self.z80.a, i & 0xff)

    def test_decA(self):
        self._test_decr8(0x3d, self.z80.decA, 0, self.z80.a)

    def test_ldAn(self):
        opc = 0x3e
        self._validOpc(opc, self.z80.ldAn, 1)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc, i)
            self._regEq(self.z80.a, i)

    def test_ccf(self):
        opc = 0x3f
        self._validOpc(opc, self.z80.ccf, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.f.z.setTo(i % 2 == 0)
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runOp(opc)
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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x47)
        self.z80.f.n.set()
        self._expectFlags(opc,
                          False, False, 0xa + 0x7 > 0xf, 0x2a + 0x47 > 0xff)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0xff)
        self._expectFlags(opc,
                          False, False, 0x2 + 0xf > 0xf, 0x72 + 0xff > 0xff)
        self._regEq(self.z80.a, 0x71)
        addr = 0xffff
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x8f)
        self._expectFlags(opc,
                          True, False, 0xf + 0x1 > 0xf, 0x71 + 0x8f > 0xff)
        self._regEq(self.z80.a, 0x00)

    def test_addAA(self):
        opc = 0x87
        self._validOpc(opc, self.z80.addAA, 0)
        self.z80.a.ld(0x47)
        self.z80.f.n.set()
        self._expectFlags(opc,
                          False, False, 0x7 + 0x7 > 0xf, 0x47 + 0x47 > 0xff)
        self._regEq(self.z80.a, 0x8e)
        self.z80.a.ld(0xff)
        self._expectFlags(opc,
                          False, False, 0xf + 0xf > 0xf, 0xff + 0xff > 0xff)
        self._regEq(self.z80.a, 0xfe)
        self.z80.a.ld(0x80)
        self._expectFlags(opc,
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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0xff)
        self.z80.f.n.set()
        self._expectFlags(opc,
                          False, False, 0x3 + 0xf > 0xf, True)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x01)
        self._expectFlags(opc,
                          False, False, 0x2 + 0x1 + 0x1 > 0xf, False)
        self._regEq(self.z80.a, 0x74)
        addr = 0xffff
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x8c)
        self._expectFlags(opc,
                          True, False, 0x4 + 0xc > 0xf, 0x74 + 0x8c > 0xff)
        self._regEq(self.z80.a, 0x00)

    def test_adcAA(self):
        opc = 0x8f
        self._validOpc(opc, self.z80.adcAA, 0)
        self.z80.a.ld(0x80)
        self._expectFlags(opc, True, False, 0x0 + 0x0 > 0xf, True)
        self._regEq(self.z80.a, 0x00)
        self.z80.f.n.set()
        self.z80.a.ld(0xff)
        self._expectFlags(opc, False, False, 0xf + 0x1 + 0x1 > 0xf, True)
        self._regEq(self.z80.a, 0xff)
        self.z80.a.ld(0x01)
        self._expectFlags(opc, False, False, 0x1 + 0x1 + 0x1 > 0xf,
                          False)
        self._regEq(self.z80.a, 0x03)
        self.z80.a.ld(0x01)
        self._expectFlags(opc, False, False, 0x1 + 0x1 > 0xf, False)
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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x2a)
        self.z80.f.n.reset()
        self._expectFlags(opc, False, True, 0xc < 0xa, 0x9c < 0x2a)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0xff)
        self._expectFlags(opc, False, True, 0x2 < 0xf, 0x72 < 0xff)
        self._regEq(self.z80.a, 0x73)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x73)
        self._expectFlags(opc, True, True, 0x3 < 0x3, 0x73 < 0x73)
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
            self._expectFlags(opc, True, True, False, False)

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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x9c)
        self.z80.f.n.reset()
        self._expectFlags(opc, False, True, 0xe < 0xc, True)
        self._regEq(self.z80.a, 0x72)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x01)
        self._expectFlags(opc,
                          False, True, 0x2 < 0x1 + 0x1, False)
        self._regEq(self.z80.a, 0x70)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0x70)
        self._expectFlags(opc, True, True, 0x0 < 0x0, 0x70 < 0x70)
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
            self._expectFlags(opc, True, True, False, False)
            self._regEq(self.z80.a, 0x00)
        self.z80.a.ld(0x00)
        self.z80.f.z.reset()
        self.z80.f.n.reset()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, False, True, True, True)
        self._regEq(self.z80.a, 0xff)
        self.z80.f.c.reset()
        self._expectFlags(opc, True, True, False, False)
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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, False, False, True, False)
        self._regEq(self.z80.a, 0b0001)
        self.assertEquals(self.mem.get8(addr), 0b0101)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, True, False)
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
        self._expectFlags(opc, False, False, True, False)
        self._regEq(self.z80.a, 0b01)
        self.z80.a.ld(0)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, True, False)
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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, False, False, False, False)
        self._regEq(self.z80.a, 0b0110)
        self.assertEquals(self.mem.get8(addr), 0b0101)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        val = self.z80.a.val()
        self.mem.set8(addr, val)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False)
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
            self._expectFlags(opc, True, False, False, False)
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
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0b0101)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, False, False, False, False)
        self._regEq(self.z80.a, 0b0111)
        self.assertEquals(self.mem.get8(addr), 0b0101)
        self.z80.a.ld(0)
        addr = 0xbeef
        self.z80.ldHLnn(addr & 0xff, addr >> 8)
        self.mem.set8(addr, 0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False)
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
        self._expectFlags(opc, False, False, False, False)
        self._regEq(self.z80.a, 0b0011)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False)
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
            self.z80.ldHLnn(addr & 0xff, addr >> 8)
            self.mem.set8(addr, v)
            self.z80.f.n.reset()
            self._expectFlags(opc,
                              a == v, True, (a & 0xf) < (v & 0xf), a < v)
            self._regEq(self.z80.a, a)

    def test_cpA(self):
        opc = 0xbf
        self._validOpc(opc, self.z80.cpA, 0)
        for a in range(0, self.NUM_TESTS):
            self.z80.a.ld(a)
            self.z80.f.n.reset()
            self._expectFlags(opc, True, True, False, False)
            self._regEq(self.z80.a, a)

    def test_retNZ(self):
        opc = 0xc0
        self._validOpc(opc, self.z80.retNZ, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            self.z80.pc.ld(i * 0x5a)
            self._test_retcnn(opc, not z)

    def test_popBC(self):
        self._test_popRR(0xc1, self.z80.popBC, self.z80.b, self.z80.c)

    def test_jpNZnn(self):
        opc = 0xc2
        self._validOpc(opc, self.z80.jpNZnn, 2)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            self._test_jpcnn(opc, not z, i * 2, i * 4)

    def test_jpnn(self):
        opc = 0xc3
        self._validOpc(opc, self.z80.jpnn, 2)
        for i in range(0, self.NUM_TESTS):
            self._test_jpcnn(opc, True, i * 2, i * 4)

    def test_callNZnn(self):
        opc = 0xc4
        self._validOpc(opc, self.z80.callNZnn, 2)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            self.z80.pc.ld(i * 0x5a)
            self._test_callcnn(opc, not z, i * 2, i * 4)

    def test_pushBC(self):
        self._test_pushRR(0xc5, self.z80.pushBC, self.z80.b, self.z80.c)

    def test_addAn(self):
        opc = 0xc6
        self._validOpc(opc, self.z80.addAn, 1)
        self.z80.a.ld(0x2b)
        self.z80.f.n.set()
        self._expectFlags(opc,
                          False, False, 0xa + 0x7 > 0xf, 0x2a + 0x47 > 0xff,
                          0x47)
        self._regEq(self.z80.a, 0x72)
        self._expectFlags(opc,
                          False, False, 0x2 + 0xf > 0xf, 0x72 + 0xff > 0xff,
                          0xff)
        self._regEq(self.z80.a, 0x71)
        self._expectFlags(opc,
                          True, False, 0xf + 0x1 > 0xf, 0x71 + 0x8f > 0xff,
                          0x8f)
        self._regEq(self.z80.a, 0x00)

    def test_rst0(self):
        self._test_rstn(0xc7, self.z80.rst0, 0)

    def test_retZ(self):
        opc = 0xc8
        self._validOpc(opc, self.z80.retZ, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            self.z80.pc.ld(i * 0x5a)
            self._test_retcnn(opc, z)

    def test_ret(self):
        opc = 0xc9
        self._validOpc(opc, self.z80.ret, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            self.z80.pc.ld(i * 0x5a)
            self._test_retcnn(opc, True)

    def test_jpZnn(self):
        opc = 0xca
        self._validOpc(opc, self.z80.jpZnn, 2)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            self._test_jpcnn(opc, z, i * 2, i * 4)

    def test_rlcB(self):
        self._test_rlcR(0x00, self.z80.rlcB, self.z80.b)

    def test_rlcC(self):
        self._test_rlcR(0x01, self.z80.rlcC, self.z80.c)

    def test_rlcD(self):
        self._test_rlcR(0x02, self.z80.rlcD, self.z80.d)

    def test_rlcE(self):
        self._test_rlcR(0x03, self.z80.rlcE, self.z80.e)

    def test_rlcH(self):
        self._test_rlcR(0x04, self.z80.rlcH, self.z80.h)

    def test_rlcL(self):
        self._test_rlcR(0x05, self.z80.rlcL, self.z80.l)

    def test_rlcMemHL(self):
        opc = 0x06
        self._validExtOpc(opc, self.z80.rlcMemHL, 0)
        self.z80.ldHLnn(0xbe, 0xef)
        self._setMemHL(1)
        for i in range(0, self.NUM_TESTS):
            self.assertEquals(self._getMemHL(), (1 << (i % 8)) & 0xff)
            c = (self._getMemHL() >> 7) & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, self._getMemHL() == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self.z80.f.c.reset()
        self._setMemHL(0)
        self.z80.f.z.reset()
        self._runExtOp(opc)
        self._flagEq(self.z80.f.z, True)

    def test_rlcA(self):
        self._test_rlcR(0x07, self.z80.rlcA, self.z80.a)

    def test_rrcB(self):
        self._test_rrcR(0x08, self.z80.rrcB, self.z80.b)

    def test_rrcC(self):
        self._test_rrcR(0x09, self.z80.rrcC, self.z80.c)

    def test_rrcD(self):
        self._test_rrcR(0x0a, self.z80.rrcD, self.z80.d)

    def test_rrcE(self):
        self._test_rrcR(0x0b, self.z80.rrcE, self.z80.e)

    def test_rrcH(self):
        self._test_rrcR(0x0c, self.z80.rrcH, self.z80.h)

    def test_rrcL(self):
        self._test_rrcR(0x0d, self.z80.rrcL, self.z80.l)

    def test_rrcMemHL(self):
        opc = 0x0e
        self._validExtOpc(opc, self.z80.rrcMemHL, 0)
        self._setMemHL(0x80)
        for i in range(0, self.NUM_TESTS):
            self.assertEquals(self._getMemHL(), (0x80 >> (i % 8)) & 0xff)
            c = self._getMemHL() & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, self._getMemHL() == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self._setMemHL(1)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x80)
        self._flagEq(self.z80.f.c, True)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x40)
        self._flagEq(self.z80.f.c, False)
        self.z80.f.c.reset()
        self._setMemHL(0)
        self.z80.f.z.reset()
        self._runExtOp(opc)
        self._flagEq(self.z80.f.z, True)

    def test_rrcA(self):
        self._test_rrcR(0x0f, self.z80.rrcA, self.z80.a)

    def test_rlB(self):
        self._test_rlR(0x10, self.z80.rlB, self.z80.b)

    def test_rlC(self):
        self._test_rlR(0x11, self.z80.rlC, self.z80.c)

    def test_rlD(self):
        self._test_rlR(0x12, self.z80.rlD, self.z80.d)

    def test_rlE(self):
        self._test_rlR(0x13, self.z80.rlE, self.z80.e)

    def test_rlH(self):
        self._test_rlR(0x14, self.z80.rlH, self.z80.h)

    def test_rlL(self):
        self._test_rlR(0x15, self.z80.rlL, self.z80.l)

    def test_rlMemHL(self):
        opc = 0x16
        self._validExtOpc(opc, self.z80.rlMemHL, 0)
        self.z80.f.n.set()
        self.z80.f.h.set()
        self._setMemHL(0x80)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, True)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x01)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x02)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)

    def test_rlA(self):
        self._test_rlR(0x17, self.z80.rlA, self.z80.a)

    def test_rrB(self):
        self._test_rrR(0x18, self.z80.rrB, self.z80.b)

    def test_rrC(self):
        self._test_rrR(0x19, self.z80.rrC, self.z80.c)

    def test_rrD(self):
        self._test_rrR(0x1a, self.z80.rrD, self.z80.d)

    def test_rrE(self):
        self._test_rrR(0x1b, self.z80.rrE, self.z80.e)

    def test_rrH(self):
        self._test_rrR(0x1c, self.z80.rrH, self.z80.h)

    def test_rrL(self):
        self._test_rrR(0x1d, self.z80.rrL, self.z80.l)

    def test_rrMemHL(self):
        opc = 0x1e
        self._validExtOpc(opc, self.z80.rrMemHL, 0)
        self._setMemHL(0x02)
        self.z80.f.n.set()
        self.z80.f.h.set()
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x01)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, True)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x80)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._runExtOp(opc)
        self.assertEquals(self._getMemHL(), 0x40)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)

    def test_rrA(self):
        self._test_rrR(0x1f, self.z80.rrA, self.z80.a)

    def test_slaB(self):
        self._test_slaR(0x20, self.z80.slaB, self.z80.b)

    def test_slaC(self):
        self._test_slaR(0x21, self.z80.slaC, self.z80.c)

    def test_slaD(self):
        self._test_slaR(0x22, self.z80.slaD, self.z80.d)

    def test_slaE(self):
        self._test_slaR(0x23, self.z80.slaE, self.z80.e)

    def test_slaH(self):
        self._test_slaR(0x24, self.z80.slaH, self.z80.h)

    def test_slaL(self):
        self._test_slaR(0x25, self.z80.slaL, self.z80.l)

    def test_slaMemHL(self):
        self._test_slan(0x26, self.z80.slaMemHL, "(HL)", 4, 16, self._getMemHL,
                        self._setMemHL)

    def test_slaA(self):
        self._test_slaR(0x27, self.z80.slaA, self.z80.a)

    def test_sraB(self):
        self._test_sraR(0x28, self.z80.sraB, self.z80.b)

    def test_sraC(self):
        self._test_sraR(0x29, self.z80.sraC, self.z80.c)

    def test_sraD(self):
        self._test_sraR(0x2a, self.z80.sraD, self.z80.d)

    def test_sraE(self):
        self._test_sraR(0x2b, self.z80.sraE, self.z80.e)

    def test_sraH(self):
        self._test_sraR(0x2c, self.z80.sraH, self.z80.h)

    def test_sraL(self):
        self._test_sraR(0x2d, self.z80.sraL, self.z80.l)

    def test_sraMemHL(self):
        self._test_sran(0x2e, self.z80.sraMemHL, "(HL)", 4, 16, self._getMemHL,
                        self._setMemHL)

    def test_sraA(self):
        self._test_sraR(0x2f, self.z80.sraA, self.z80.a)

    def test_swapB(self):
        self._test_swapR(0x30, self.z80.swapB, self.z80.b)

    def test_swapC(self):
        self._test_swapR(0x31, self.z80.swapC, self.z80.c)

    def test_swapD(self):
        self._test_swapR(0x32, self.z80.swapD, self.z80.d)

    def test_swapE(self):
        self._test_swapR(0x33, self.z80.swapE, self.z80.e)

    def test_swapH(self):
        self._test_swapR(0x34, self.z80.swapH, self.z80.h)

    def test_swapL(self):
        self._test_swapR(0x35, self.z80.swapL, self.z80.l)

    def test_swapMemHL(self):
        self._test_swapn(0x36, self.z80.swapMemHL, "(HL)", 4, 16,
                         self._getMemHL, self._setMemHL)

    def test_swapA(self):
        self._test_swapR(0x37, self.z80.swapA, self.z80.a)

    def test_srlB(self):
        self._test_srlR(0x38, self.z80.srlB, self.z80.b)

    def test_srlC(self):
        self._test_srlR(0x39, self.z80.srlC, self.z80.c)

    def test_srlD(self):
        self._test_srlR(0x3a, self.z80.srlD, self.z80.d)

    def test_srlE(self):
        self._test_srlR(0x3b, self.z80.srlE, self.z80.e)

    def test_srlH(self):
        self._test_srlR(0x3c, self.z80.srlH, self.z80.h)

    def test_srlL(self):
        self._test_srlR(0x3d, self.z80.srlL, self.z80.l)

    def test_srlMemHL(self):
        self._test_srln(0x3e, self.z80.srlMemHL, "(HL)", 4, 16, self._getMemHL,
                        self._setMemHL)

    def test_srlA(self):
        self._test_srlR(0x3f, self.z80.srlA, self.z80.a)

    def test_bit0B(self):
        self._test_bitBR(0x40, self.z80.bit0B, 0, self.z80.b)

    def test_bit0C(self):
        self._test_bitBR(0x41, self.z80.bit0C, 0, self.z80.c)

    def test_bit0D(self):
        self._test_bitBR(0x42, self.z80.bit0D, 0, self.z80.d)

    def test_bit0E(self):
        self._test_bitBR(0x43, self.z80.bit0E, 0, self.z80.e)

    def test_bit0H(self):
        self._test_bitBR(0x44, self.z80.bit0H, 0, self.z80.h)

    def test_bit0L(self):
        self._test_bitBR(0x45, self.z80.bit0L, 0, self.z80.l)

    def test_bit0MemHL(self):
        self._test_bitBn(0x46, self.z80.bit0MemHL, "(HL)", 4, 16, 0,
                         self._setMemHL)

    def test_bit0A(self):
        self._test_bitBR(0x47, self.z80.bit0A, 0, self.z80.a)

    def test_bit1B(self):
        self._test_bitBR(0x48, self.z80.bit1B, 1, self.z80.b)

    def test_bit1C(self):
        self._test_bitBR(0x49, self.z80.bit1C, 1, self.z80.c)

    def test_bit1D(self):
        self._test_bitBR(0x4a, self.z80.bit1D, 1, self.z80.d)

    def test_bit1E(self):
        self._test_bitBR(0x4b, self.z80.bit1E, 1, self.z80.e)

    def test_bit1H(self):
        self._test_bitBR(0x4c, self.z80.bit1H, 1, self.z80.h)

    def test_bit1L(self):
        self._test_bitBR(0x4d, self.z80.bit1L, 1, self.z80.l)

    def test_bit1MemHL(self):
        self._test_bitBn(0x4e, self.z80.bit1MemHL, "(HL)", 4, 16, 1,
                         self._setMemHL)

    def test_bit1A(self):
        self._test_bitBR(0x4f, self.z80.bit1A, 1, self.z80.a)

    def test_bit2B(self):
        self._test_bitBR(0x50, self.z80.bit2B, 2, self.z80.b)

    def test_bit2C(self):
        self._test_bitBR(0x51, self.z80.bit2C, 2, self.z80.c)

    def test_bit2D(self):
        self._test_bitBR(0x52, self.z80.bit2D, 2, self.z80.d)

    def test_bit2E(self):
        self._test_bitBR(0x53, self.z80.bit2E, 2, self.z80.e)

    def test_bit2H(self):
        self._test_bitBR(0x54, self.z80.bit2H, 2, self.z80.h)

    def test_bit2L(self):
        self._test_bitBR(0x55, self.z80.bit2L, 2, self.z80.l)

    def test_bit2MemHL(self):
        self._test_bitBn(0x56, self.z80.bit2MemHL, "(HL)", 4, 16, 2,
                         self._setMemHL)

    def test_bit2A(self):
        self._test_bitBR(0x57, self.z80.bit2A, 2, self.z80.a)

    def test_bit3B(self):
        self._test_bitBR(0x58, self.z80.bit3B, 3, self.z80.b)

    def test_bit3C(self):
        self._test_bitBR(0x59, self.z80.bit3C, 3, self.z80.c)

    def test_bit3D(self):
        self._test_bitBR(0x5a, self.z80.bit3D, 3, self.z80.d)

    def test_bit3E(self):
        self._test_bitBR(0x5b, self.z80.bit3E, 3, self.z80.e)

    def test_bit3H(self):
        self._test_bitBR(0x5c, self.z80.bit3H, 3, self.z80.h)

    def test_bit3L(self):
        self._test_bitBR(0x5d, self.z80.bit3L, 3, self.z80.l)

    def test_bit3MemHL(self):
        self._test_bitBn(0x5e, self.z80.bit3MemHL, "(HL)", 4, 16, 3,
                         self._setMemHL)

    def test_bit3A(self):
        self._test_bitBR(0x5f, self.z80.bit3A, 3, self.z80.a)

    def test_bit4B(self):
        self._test_bitBR(0x60, self.z80.bit4B, 4, self.z80.b)

    def test_bit4C(self):
        self._test_bitBR(0x61, self.z80.bit4C, 4, self.z80.c)

    def test_bit4D(self):
        self._test_bitBR(0x62, self.z80.bit4D, 4, self.z80.d)

    def test_bit4E(self):
        self._test_bitBR(0x63, self.z80.bit4E, 4, self.z80.e)

    def test_bit4H(self):
        self._test_bitBR(0x64, self.z80.bit4H, 4, self.z80.h)

    def test_bit4L(self):
        self._test_bitBR(0x65, self.z80.bit4L, 4, self.z80.l)

    def test_bit4MemHL(self):
        self._test_bitBn(0x66, self.z80.bit4MemHL, "(HL)", 4, 16, 4,
                         self._setMemHL)

    def test_bit4A(self):
        self._test_bitBR(0x67, self.z80.bit4A, 4, self.z80.a)

    def test_bit5B(self):
        self._test_bitBR(0x68, self.z80.bit5B, 5, self.z80.b)

    def test_bit5C(self):
        self._test_bitBR(0x69, self.z80.bit5C, 5, self.z80.c)

    def test_bit5D(self):
        self._test_bitBR(0x6a, self.z80.bit5D, 5, self.z80.d)

    def test_bit5E(self):
        self._test_bitBR(0x6b, self.z80.bit5E, 5, self.z80.e)

    def test_bit5H(self):
        self._test_bitBR(0x6c, self.z80.bit5H, 5, self.z80.h)

    def test_bit5L(self):
        self._test_bitBR(0x6d, self.z80.bit5L, 5, self.z80.l)

    def test_bit5MemHL(self):
        self._test_bitBn(0x6e, self.z80.bit5MemHL, "(HL)", 4, 16, 5,
                         self._setMemHL)

    def test_bit5A(self):
        self._test_bitBR(0x6f, self.z80.bit5A, 5, self.z80.a)

    def test_bit6B(self):
        self._test_bitBR(0x70, self.z80.bit6B, 6, self.z80.b)

    def test_bit6C(self):
        self._test_bitBR(0x71, self.z80.bit6C, 6, self.z80.c)

    def test_bit6D(self):
        self._test_bitBR(0x72, self.z80.bit6D, 6, self.z80.d)

    def test_bit6E(self):
        self._test_bitBR(0x73, self.z80.bit6E, 6, self.z80.e)

    def test_bit6H(self):
        self._test_bitBR(0x74, self.z80.bit6H, 6, self.z80.h)

    def test_bit6L(self):
        self._test_bitBR(0x75, self.z80.bit6L, 6, self.z80.l)

    def test_bit6MemHL(self):
        self._test_bitBn(0x76, self.z80.bit6MemHL, "(HL)", 4, 16, 6,
                         self._setMemHL)

    def test_bit6A(self):
        self._test_bitBR(0x77, self.z80.bit6A, 6, self.z80.a)

    def test_bit7B(self):
        self._test_bitBR(0x78, self.z80.bit7B, 7, self.z80.b)

    def test_bit7C(self):
        self._test_bitBR(0x79, self.z80.bit7C, 7, self.z80.c)

    def test_bit7D(self):
        self._test_bitBR(0x7a, self.z80.bit7D, 7, self.z80.d)

    def test_bit7E(self):
        self._test_bitBR(0x7b, self.z80.bit7E, 7, self.z80.e)

    def test_bit7H(self):
        self._test_bitBR(0x7c, self.z80.bit7H, 7, self.z80.h)

    def test_bit7L(self):
        self._test_bitBR(0x7d, self.z80.bit7L, 7, self.z80.l)

    def test_bit7MemHL(self):
        self._test_bitBn(0x7e, self.z80.bit7MemHL, "(HL)", 4, 16, 7,
                         self._setMemHL)

    def test_bit7A(self):
        self._test_bitBR(0x7f, self.z80.bit7A, 7, self.z80.a)

    def test_res0B(self):
        self._test_resBR(0x80, self.z80.res0B, 0, self.z80.b)

    def test_res0C(self):
        self._test_resBR(0x81, self.z80.res0C, 0, self.z80.c)

    def test_res0D(self):
        self._test_resBR(0x82, self.z80.res0D, 0, self.z80.d)

    def test_res0E(self):
        self._test_resBR(0x83, self.z80.res0E, 0, self.z80.e)

    def test_res0H(self):
        self._test_resBR(0x84, self.z80.res0H, 0, self.z80.h)

    def test_res0L(self):
        self._test_resBR(0x85, self.z80.res0L, 0, self.z80.l)

    def test_res0MemHL(self):
        self._test_resBn(0x86, self.z80.res0MemHL, "(HL)", 4, 16, 0,
                         self._setMemHL, self._getMemHL)

    def test_res0A(self):
        self._test_resBR(0x87, self.z80.res0A, 0, self.z80.a)

    def test_res1B(self):
        self._test_resBR(0x88, self.z80.res1B, 1, self.z80.b)

    def test_res1C(self):
        self._test_resBR(0x89, self.z80.res1C, 1, self.z80.c)

    def test_res1D(self):
        self._test_resBR(0x8a, self.z80.res1D, 1, self.z80.d)

    def test_res1E(self):
        self._test_resBR(0x8b, self.z80.res1E, 1, self.z80.e)

    def test_res1H(self):
        self._test_resBR(0x8c, self.z80.res1H, 1, self.z80.h)

    def test_res1L(self):
        self._test_resBR(0x8d, self.z80.res1L, 1, self.z80.l)

    def test_res1MemHL(self):
        self._test_resBn(0x8e, self.z80.res1MemHL, "(HL)", 4, 16, 1,
                         self._setMemHL, self._getMemHL)

    def test_res1A(self):
        self._test_resBR(0x8f, self.z80.res1A, 1, self.z80.a)

    def test_res2B(self):
        self._test_resBR(0x90, self.z80.res2B, 2, self.z80.b)

    def test_res2C(self):
        self._test_resBR(0x91, self.z80.res2C, 2, self.z80.c)

    def test_res2D(self):
        self._test_resBR(0x92, self.z80.res2D, 2, self.z80.d)

    def test_res2E(self):
        self._test_resBR(0x93, self.z80.res2E, 2, self.z80.e)

    def test_res2H(self):
        self._test_resBR(0x94, self.z80.res2H, 2, self.z80.h)

    def test_res2L(self):
        self._test_resBR(0x95, self.z80.res2L, 2, self.z80.l)

    def test_res2MemHL(self):
        self._test_resBn(0x96, self.z80.res2MemHL, "(HL)", 4, 16, 2,
                         self._setMemHL, self._getMemHL)

    def test_res2A(self):
        self._test_resBR(0x97, self.z80.res2A, 2, self.z80.a)

    def test_res3B(self):
        self._test_resBR(0x98, self.z80.res3B, 3, self.z80.b)

    def test_res3C(self):
        self._test_resBR(0x99, self.z80.res3C, 3, self.z80.c)

    def test_res3D(self):
        self._test_resBR(0x9a, self.z80.res3D, 3, self.z80.d)

    def test_res3E(self):
        self._test_resBR(0x9b, self.z80.res3E, 3, self.z80.e)

    def test_res3H(self):
        self._test_resBR(0x9c, self.z80.res3H, 3, self.z80.h)

    def test_res3L(self):
        self._test_resBR(0x9d, self.z80.res3L, 3, self.z80.l)

    def test_res3MemHL(self):
        self._test_resBn(0x9e, self.z80.res3MemHL, "(HL)", 4, 16, 3,
                         self._setMemHL, self._getMemHL)

    def test_res3A(self):
        self._test_resBR(0x9f, self.z80.res3A, 3, self.z80.a)

    def test_res4B(self):
        self._test_resBR(0xa0, self.z80.res4B, 4, self.z80.b)

    def test_res4C(self):
        self._test_resBR(0xa1, self.z80.res4C, 4, self.z80.c)

    def test_res4D(self):
        self._test_resBR(0xa2, self.z80.res4D, 4, self.z80.d)

    def test_res4E(self):
        self._test_resBR(0xa3, self.z80.res4E, 4, self.z80.e)

    def test_res4H(self):
        self._test_resBR(0xa4, self.z80.res4H, 4, self.z80.h)

    def test_res4L(self):
        self._test_resBR(0xa5, self.z80.res4L, 4, self.z80.l)

    def test_res4MemHL(self):
        self._test_resBn(0xa6, self.z80.res4MemHL, "(HL)", 4, 16, 4,
                         self._setMemHL, self._getMemHL)

    def test_res4A(self):
        self._test_resBR(0xa7, self.z80.res4A, 4, self.z80.a)

    def test_res5B(self):
        self._test_resBR(0xa8, self.z80.res5B, 5, self.z80.b)

    def test_res5C(self):
        self._test_resBR(0xa9, self.z80.res5C, 5, self.z80.c)

    def test_res5D(self):
        self._test_resBR(0xaa, self.z80.res5D, 5, self.z80.d)

    def test_res5E(self):
        self._test_resBR(0xab, self.z80.res5E, 5, self.z80.e)

    def test_res5H(self):
        self._test_resBR(0xac, self.z80.res5H, 5, self.z80.h)

    def test_res5L(self):
        self._test_resBR(0xad, self.z80.res5L, 5, self.z80.l)

    def test_res5MemHL(self):
        self._test_resBn(0xae, self.z80.res5MemHL, "(HL)", 4, 16, 5,
                         self._setMemHL, self._getMemHL)

    def test_res5A(self):
        self._test_resBR(0xaf, self.z80.res5A, 5, self.z80.a)

    def test_res6B(self):
        self._test_resBR(0xb0, self.z80.res6B, 6, self.z80.b)

    def test_res6C(self):
        self._test_resBR(0xb1, self.z80.res6C, 6, self.z80.c)

    def test_res6D(self):
        self._test_resBR(0xb2, self.z80.res6D, 6, self.z80.d)

    def test_res6E(self):
        self._test_resBR(0xb3, self.z80.res6E, 6, self.z80.e)

    def test_res6H(self):
        self._test_resBR(0xb4, self.z80.res6H, 6, self.z80.h)

    def test_res6L(self):
        self._test_resBR(0xb5, self.z80.res6L, 6, self.z80.l)

    def test_res6MemHL(self):
        self._test_resBn(0xb6, self.z80.res6MemHL, "(HL)", 4, 16, 6,
                         self._setMemHL, self._getMemHL)

    def test_res6A(self):
        self._test_resBR(0xb7, self.z80.res6A, 6, self.z80.a)

    def test_res7B(self):
        self._test_resBR(0xb8, self.z80.res7B, 7, self.z80.b)

    def test_res7C(self):
        self._test_resBR(0xb9, self.z80.res7C, 7, self.z80.c)

    def test_res7D(self):
        self._test_resBR(0xba, self.z80.res7D, 7, self.z80.d)

    def test_res7E(self):
        self._test_resBR(0xbb, self.z80.res7E, 7, self.z80.e)

    def test_res7H(self):
        self._test_resBR(0xbc, self.z80.res7H, 7, self.z80.h)

    def test_res7L(self):
        self._test_resBR(0xbd, self.z80.res7L, 7, self.z80.l)

    def test_res7MemHL(self):
        self._test_resBn(0xbe, self.z80.res7MemHL, "(HL)", 4, 16, 7,
                         self._setMemHL, self._getMemHL)

    def test_res7A(self):
        self._test_resBR(0xbf, self.z80.res7A, 7, self.z80.a)

    def test_set0B(self):
        self._test_setBR(0xc0, self.z80.set0B, 0, self.z80.b)

    def test_set0C(self):
        self._test_setBR(0xc1, self.z80.set0C, 0, self.z80.c)

    def test_set0D(self):
        self._test_setBR(0xc2, self.z80.set0D, 0, self.z80.d)

    def test_set0E(self):
        self._test_setBR(0xc3, self.z80.set0E, 0, self.z80.e)

    def test_set0H(self):
        self._test_setBR(0xc4, self.z80.set0H, 0, self.z80.h)

    def test_set0L(self):
        self._test_setBR(0xc5, self.z80.set0L, 0, self.z80.l)

    def test_set0MemHL(self):
        self._test_setBn(0xc6, self.z80.set0MemHL, "(HL)", 4, 16, 0,
                         self._setMemHL, self._getMemHL)

    def test_set0A(self):
        self._test_setBR(0xc7, self.z80.set0A, 0, self.z80.a)

    def test_set1B(self):
        self._test_setBR(0xc8, self.z80.set1B, 1, self.z80.b)

    def test_set1C(self):
        self._test_setBR(0xc9, self.z80.set1C, 1, self.z80.c)

    def test_set1D(self):
        self._test_setBR(0xca, self.z80.set1D, 1, self.z80.d)

    def test_set1E(self):
        self._test_setBR(0xcb, self.z80.set1E, 1, self.z80.e)

    def test_set1H(self):
        self._test_setBR(0xcc, self.z80.set1H, 1, self.z80.h)

    def test_set1L(self):
        self._test_setBR(0xcd, self.z80.set1L, 1, self.z80.l)

    def test_set1MemHL(self):
        self._test_setBn(0xce, self.z80.set1MemHL, "(HL)", 4, 16, 1,
                         self._setMemHL, self._getMemHL)

    def test_set1A(self):
        self._test_setBR(0xcf, self.z80.set1A, 1, self.z80.a)

    def test_set2B(self):
        self._test_setBR(0xd0, self.z80.set2B, 2, self.z80.b)

    def test_set2C(self):
        self._test_setBR(0xd1, self.z80.set2C, 2, self.z80.c)

    def test_set2D(self):
        self._test_setBR(0xd2, self.z80.set2D, 2, self.z80.d)

    def test_set2E(self):
        self._test_setBR(0xd3, self.z80.set2E, 2, self.z80.e)

    def test_set2H(self):
        self._test_setBR(0xd4, self.z80.set2H, 2, self.z80.h)

    def test_set2L(self):
        self._test_setBR(0xd5, self.z80.set2L, 2, self.z80.l)

    def test_set2MemHL(self):
        self._test_setBn(0xd6, self.z80.set2MemHL, "(HL)", 4, 16, 2,
                         self._setMemHL, self._getMemHL)

    def test_set2A(self):
        self._test_setBR(0xd7, self.z80.set2A, 2, self.z80.a)

    def test_set3B(self):
        self._test_setBR(0xd8, self.z80.set3B, 3, self.z80.b)

    def test_set3C(self):
        self._test_setBR(0xd9, self.z80.set3C, 3, self.z80.c)

    def test_set3D(self):
        self._test_setBR(0xda, self.z80.set3D, 3, self.z80.d)

    def test_set3E(self):
        self._test_setBR(0xdb, self.z80.set3E, 3, self.z80.e)

    def test_set3H(self):
        self._test_setBR(0xdc, self.z80.set3H, 3, self.z80.h)

    def test_set3L(self):
        self._test_setBR(0xdd, self.z80.set3L, 3, self.z80.l)

    def test_set3MemHL(self):
        self._test_setBn(0xde, self.z80.set3MemHL, "(HL)", 4, 16, 3,
                         self._setMemHL, self._getMemHL)

    def test_set3A(self):
        self._test_setBR(0xdf, self.z80.set3A, 3, self.z80.a)

    def test_set4B(self):
        self._test_setBR(0xe0, self.z80.set4B, 4, self.z80.b)

    def test_set4C(self):
        self._test_setBR(0xe1, self.z80.set4C, 4, self.z80.c)

    def test_set4D(self):
        self._test_setBR(0xe2, self.z80.set4D, 4, self.z80.d)

    def test_set4E(self):
        self._test_setBR(0xe3, self.z80.set4E, 4, self.z80.e)

    def test_set4H(self):
        self._test_setBR(0xe4, self.z80.set4H, 4, self.z80.h)

    def test_set4L(self):
        self._test_setBR(0xe5, self.z80.set4L, 4, self.z80.l)

    def test_set4MemHL(self):
        self._test_setBn(0xe6, self.z80.set4MemHL, "(HL)", 4, 16, 4,
                         self._setMemHL, self._getMemHL)

    def test_set4A(self):
        self._test_setBR(0xe7, self.z80.set4A, 4, self.z80.a)

    def test_set5B(self):
        self._test_setBR(0xe8, self.z80.set5B, 5, self.z80.b)

    def test_set5C(self):
        self._test_setBR(0xe9, self.z80.set5C, 5, self.z80.c)

    def test_set5D(self):
        self._test_setBR(0xea, self.z80.set5D, 5, self.z80.d)

    def test_set5E(self):
        self._test_setBR(0xeb, self.z80.set5E, 5, self.z80.e)

    def test_set5H(self):
        self._test_setBR(0xec, self.z80.set5H, 5, self.z80.h)

    def test_set5L(self):
        self._test_setBR(0xed, self.z80.set5L, 5, self.z80.l)

    def test_set5MemHL(self):
        self._test_setBn(0xee, self.z80.set5MemHL, "(HL)", 4, 16, 5,
                         self._setMemHL, self._getMemHL)

    def test_set5A(self):
        self._test_setBR(0xef, self.z80.set5A, 5, self.z80.a)

    def test_set6B(self):
        self._test_setBR(0xf0, self.z80.set6B, 6, self.z80.b)

    def test_set6C(self):
        self._test_setBR(0xf1, self.z80.set6C, 6, self.z80.c)

    def test_set6D(self):
        self._test_setBR(0xf2, self.z80.set6D, 6, self.z80.d)

    def test_set6E(self):
        self._test_setBR(0xf3, self.z80.set6E, 6, self.z80.e)

    def test_set6H(self):
        self._test_setBR(0xf4, self.z80.set6H, 6, self.z80.h)

    def test_set6L(self):
        self._test_setBR(0xf5, self.z80.set6L, 6, self.z80.l)

    def test_set6MemHL(self):
        self._test_setBn(0xf6, self.z80.set6MemHL, "(HL)", 4, 16, 6,
                         self._setMemHL, self._getMemHL)

    def test_set6A(self):
        self._test_setBR(0xf7, self.z80.set6A, 6, self.z80.a)

    def test_set7B(self):
        self._test_setBR(0xf8, self.z80.set7B, 7, self.z80.b)

    def test_set7C(self):
        self._test_setBR(0xf9, self.z80.set7C, 7, self.z80.c)

    def test_set7D(self):
        self._test_setBR(0xfa, self.z80.set7D, 7, self.z80.d)

    def test_set7E(self):
        self._test_setBR(0xfb, self.z80.set7E, 7, self.z80.e)

    def test_set7H(self):
        self._test_setBR(0xfc, self.z80.set7H, 7, self.z80.h)

    def test_set7L(self):
        self._test_setBR(0xfd, self.z80.set7L, 7, self.z80.l)

    def test_set7MemHL(self):
        self._test_setBn(0xfe, self.z80.set7MemHL, "(HL)", 4, 16, 7,
                         self._setMemHL, self._getMemHL)

    def test_set7A(self):
        self._test_setBR(0xff, self.z80.set7A, 7, self.z80.a)

    def test_callZnn(self):
        opc = 0xcc
        self._validOpc(opc, self.z80.callZnn, 2)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            z = i % 2 == 0
            self.z80.f.z.setTo(z)
            self.z80.pc.ld(i * 0x5a)
            self._test_callcnn(opc, z, i * 2, i * 4)

    def test_callnn(self):
        opc = 0xcd
        self._validOpc(opc, self.z80.callnn, 2)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            self.z80.pc.ld(i * 0x5a)
            self._test_callcnn(opc, True, i * 2, i * 4)

    def test_adcAn(self):
        opc = 0xce
        self._validOpc(opc, self.z80.adcAn, 1)
        self.z80.a.ld(0x73)
        self.z80.f.n.set()
        self._expectFlags(opc, False, False, 0x3 + 0xf > 0xf, True, 0xff)
        self._regEq(self.z80.a, 0x72)
        self._expectFlags(opc,
                          False, False, 0x2 + 0x1 + 0x1 > 0xf, False, 0x01)
        self._regEq(self.z80.a, 0x74)
        self._expectFlags(opc,
                          True, False, 0x4 + 0xc > 0xf, 0x74 + 0x8c > 0xff,
                          0x8c)
        self._regEq(self.z80.a, 0x00)

    def test_rst8(self):
        self._test_rstn(0xcf, self.z80.rst8, 8)

    def test_retNC(self):
        opc = 0xd0
        self._validOpc(opc, self.z80.retNC, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            c = i % 2 == 0
            self.z80.f.c.setTo(c)
            self.z80.pc.ld(i * 0x5a)
            self._test_retcnn(opc, not c)

    def test_popDE(self):
        self._test_popRR(0xd1, self.z80.popDE, self.z80.d, self.z80.e)

    def test_jpNCnn(self):
        opc = 0xd2
        self._validOpc(opc, self.z80.jpNCnn, 2)
        for i in range(0, self.NUM_TESTS):
            c = i % 2 == 0
            self.z80.f.c.setTo(c)
            self._test_jpcnn(opc, not c, i * 2, i * 4)

    def test_callNCnn(self):
        opc = 0xd4
        self._validOpc(opc, self.z80.callNCnn, 2)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            c = i % 2 == 0
            self.z80.f.c.setTo(c)
            self.z80.pc.ld(i * 0x5a)
            self._test_callcnn(opc, not c, i * 2, i * 4)

    def test_pushDE(self):
        self._test_pushRR(0xd5, self.z80.pushDE, self.z80.d, self.z80.e)

    def test_subAn(self):
        opc = 0xd6
        self._validOpc(opc, self.z80.subAn, 1)
        self.z80.a.ld(0x9c)
        self.z80.f.n.reset()
        self._expectFlags(opc, False, True, 0xc < 0xa, 0x9c < 0x2a, 0x2a)
        self.z80.f.n.reset()
        self._regEq(self.z80.a, 0x72)
        self._expectFlags(opc, False, True, 0x2 < 0xf, 0x72 < 0xff, 0xff)
        self.z80.f.n.reset()
        self._regEq(self.z80.a, 0x73)
        self._expectFlags(opc, True, True, 0x3 < 0x3, 0x73 < 0x73, 0x73)
        self._regEq(self.z80.a, 0x00)

    def test_rst10(self):
        self._test_rstn(0xd7, self.z80.rst10, 0x10)

    def test_retC(self):
        opc = 0xd8
        self._validOpc(opc, self.z80.retC, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            c = i % 2 == 0
            self.z80.f.c.setTo(c)
            self.z80.pc.ld(i * 0x5a)
            self._test_retcnn(opc, c)

    def test_reti(self):
        opc = 0xd9
        self._validOpc(opc, self.z80.reti, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            self.z80.pc.ld(i * 0x5a)
            self.z80.intsEnabled = i % 2 == 0
            self._test_retcnn(opc, True, True)
            self.assertTrue(self.z80.intsEnabled)

    def test_jpCnn(self):
        opc = 0xda
        self._validOpc(opc, self.z80.jpCnn, 2)
        for i in range(0, self.NUM_TESTS):
            c = i % 2 == 0
            self.z80.f.c.setTo(c)
            self._test_jpcnn(opc, c, i * 2, i * 4)

    def test_callCnn(self):
        opc = 0xdc
        self._validOpc(opc, self.z80.callCnn, 2)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            c = i % 2 == 0
            self.z80.f.c.setTo(c)
            self.z80.pc.ld(i * 0x5a)
            self._test_callcnn(opc, c, i * 2, i * 4)

    def test_sbcAn(self):
        opc = 0xde
        self._validOpc(opc, self.z80.sbcAn, 1)
        self.z80.a.ld(0x9c)
        self.z80.f.n.reset()
        self._expectFlags(opc, False, True, 0xc < 0xf, True, 0xff)
        self._regEq(self.z80.a, 0x9d)
        self._expectFlags(opc, False, True, 0xd < 0x1, False, 0x01)
        self._regEq(self.z80.a, 0x9b)
        self._expectFlags(opc, True, True, 0xb < 0xb, 0x9b < 0x9b, 0x9b)
        self._regEq(self.z80.a, 0x00)

    def test_rst18(self):
        self._test_rstn(0xdf, self.z80.rst18, 0x18)

    def test_ldhMemnA(self):
        opc = 0xe0
        self._validOpc(opc, self.z80.ldhMemnA, 1)
        for i in range(0, self.NUM_TESTS):
            n = (i * 0xa5) & 0xff
            v = (i * 0x5a) & 0xff
            self.z80.a.ld(v)
            self._flagsFixed(opc, n)
            self.assertEquals(self.mem.get8(0xff00 + n), v)

    def test_popHL(self):
        self._test_popRR(0xe1, self.z80.popHL, self.z80.h, self.z80.l)

    def test_ldhMemCA(self):
        opc = 0xe2
        self._validOpc(opc, self.z80.ldhMemCA, 0)
        for i in range(0, self.NUM_TESTS):
            n = (i * 0xa5) & 0xff
            v = (i * 0x5a) & 0xff
            self.z80.a.ld(v)
            self.z80.c.ld(n)
            self._flagsFixed(opc)
            self.assertEquals(self.mem.get8(0xff00 + n), v)

    def test_pushHL(self):
        self._test_pushRR(0xe5, self.z80.pushHL, self.z80.h, self.z80.l)

    def test_andn(self):
        opc = 0xe6
        self._validOpc(opc, self.z80.andn, 1)
        self.z80.a.ld(0b0011)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, False, False, True, False, 0b0101)
        self._regEq(self.z80.a, 0b0001)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, True, False, 0)
        self._regEq(self.z80.a, 0)

    def test_rst20(self):
        self._test_rstn(0xe7, self.z80.rst20, 0x20)

    def test_addSPn(self):
        opc = 0xe8
        self._validOpc(opc, self.z80.addSPn, 1)
        self.z80.sp.ld(0xbeef)
        self._flagsFixed(opc, 0x01)
        self._regEq(self.z80.sp, 0xbef0)
        self._flagsFixed(opc, 0xff)
        self._regEq(self.z80.sp, 0xbeef)

    def test_jpMemHL(self):
        opc = 0xe9
        self._validOpc(opc, self.z80.jpMemHL, 0)
        for i in range(0, self.NUM_TESTS):
            self._flagsFixed(opc)
            self._regEq(self.z80.pc, self._hl())

    def test_ldMemnnA(self):
        opc = 0xea
        self._validOpc(opc, self.z80.ldMemnnA, 2)
        for i in range(0, self.NUM_TESTS):
            msb = (i * 0xbe) & 0xff
            lsb = (i * 0xef) & 0xff
            v = (i * 0xa5) & 0xff
            self.z80.a.ld(v)
            self._flagsFixed(opc, lsb, msb)
            self.assertEquals(self.mem.get8((msb << 8) + lsb), v)

    def test_xorn(self):
        opc = 0xee
        self._validOpc(opc, self.z80.xorn, 1)
        self.z80.a.ld(0b0011)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, False, False, False, False, 0b0101)
        self._regEq(self.z80.a, 0b0110)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False, 0b0110)
        self._regEq(self.z80.a, 0)

    def test_rst28(self):
        self._test_rstn(0xef, self.z80.rst28, 0x28)

    def test_ldhAMemn(self):
        opc = 0xf0
        self._validOpc(opc, self.z80.ldhAMemn, 1)
        for i in range(0, self.NUM_TESTS):
            n = (i * 0xa5) & 0xff
            v = (i * 0x5a) & 0xff
            self.mem.set8(0xff00 + n, v)
            self._flagsFixed(opc, n)
            self._regEq(self.z80.a, v)

    def test_popAF(self):
        opc = 0xf1
        self._validOpc(opc, self.z80.popAF, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            a = (0xa5 * i) & 0xff
            f = (0xef * i) & 0xff
            self._push8(a)
            self._push8(f)
            self._runOp(opc)
            self._flagEq(self.z80.f.z, (f >> 7) & 1)
            self._flagEq(self.z80.f.n, (f >> 6) & 1)
            self._flagEq(self.z80.f.h, (f >> 5) & 1)
            self._flagEq(self.z80.f.c, (f >> 4) & 1)
            self._regEq(self.z80.a, a)

    def test_di(self):
        opc = 0xf3
        self._validOpc(opc, self.z80.di, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.intsEnabled = i % 2 == 0
            self._flagsFixed(opc)
            self.assertFalse(self.z80.intsEnabled)

    def test_pushAF(self):
        opc = 0xf5
        self._validOpc(opc, self.z80.pushAF, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            a = (0xa5 * i) & 0xff
            f = ((0x7 * i) & 0xf) << 4
            self._push8(a)
            self._push8(f)
            self.z80.f.z.setTo((f >> 7) & 1 == 1)
            self.z80.f.n.setTo((f >> 6) & 1 == 1)
            self.z80.f.h.setTo((f >> 5) & 1 == 1)
            self.z80.f.c.setTo((f >> 4) & 1 == 1)
            self.z80.a.ld(a)
            self._runOp(opc)
            self.assertEquals(self._pop8(), f)
            self.assertEquals(self._pop8(), a)

    def test_orn(self):
        opc = 0xf6
        self._validOpc(opc, self.z80.orn, 1)
        self.z80.a.ld(0b0011)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, False, False, False, False, 0b0101)
        self._regEq(self.z80.a, 0b0111)
        self.z80.a.ld(0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False, 0)
        self._regEq(self.z80.a, 0)

    def test_rst30(self):
        self._test_rstn(0xf7, self.z80.rst30, 0x30)

    def test_ldhlSPn(self):
        opc = 0xf8
        self._validOpc(opc, self.z80.ldhlSPn, 1)
        for i in range(0, self.NUM_TESTS):
            n = (0xa5 * i) & 0xff
            self.z80.sp.ld(0x8888)
            self.z80.f.z.set()
            self.z80.f.n.set()
            if n > 127:
                h = False
                c = False
            else:
                h = (0x8 + (n & 0xf)) > 0xf
                c = (0x88 + n) > 0xff
            self._expectFlags(opc, False, False, h, c, n)
            self._regEq(self.z80.sp, 0x8888 + self._sign(n))
        self.z80.sp.ld(0x0000)
        self._expectFlags(opc, False, False, False, False, 0xff)
        self._regEq(self.z80.sp, 0xffff)
        self.z80.sp.ld(0xffff)
        self._expectFlags(opc, False, False, True, True, 0x01)
        self._regEq(self.z80.sp, 0x0000)

    def test_ldSPHL(self):
        opc = 0xf9
        self._validOpc(opc, self.z80.ldSPHL, 0)
        for i in range(0, self.NUM_TESTS):
            n = (0xa5a5 * i) & 0xffff
            self.z80.sp.ld(0)
            self.z80.h.ld(n >> 8)
            self.z80.l.ld(n & 0xff)
            self._flagsFixed(opc)
            self._regEq(self.z80.sp, n)

    def test_ldAMemnn(self):
        opc = 0xfa
        self._validOpc(opc, self.z80.ldAMemnn, 2)
        for i in range(0, self.NUM_TESTS):
            n = (0xa5 * i) & 0xff
            addr = (0xbeef * i) & 0xffff
            self.mem.set8(addr, n)
            self.z80.a.ld(0)
            self._flagsFixed(opc, addr & 0xff, addr >> 8)
            self._regEq(self.z80.a, n)

    def test_ei(self):
        opc = 0xfb
        self._validOpc(opc, self.z80.ei, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.intsEnabled = i % 2 == 0
            self._flagsFixed(opc)
            self.assertTrue(self.z80.intsEnabled)

    def test_cpn(self):
        opc = 0xfe
        self._validOpc(opc, self.z80.cpn, 1)
        for regVal in [(0x9c, 0x2a), (0x72, 0xff), (0x73, 0x73)]:
            a, v = regVal
            self.z80.a.ld(a)
            self.z80.f.n.reset()
            self._expectFlags(opc,
                              a == v, True, (a & 0xf) < (v & 0xf), a < v, v)
            self._regEq(self.z80.a, a)

    def test_rst38(self):
        self._test_rstn(0xff, self.z80.rst38, 0x38)

    def _sign(self, n):
        if n > 127:
            n = (n & 127) - 128
        return n

    def _test_popRR(self, opc, func, loOrdReg, hiOrdReg):
        self._validOpc(opc, func, 0)
        self.z80.sp.ld(0xfffe)
        vals = [0xa5a5, 0x5a5a, 0xdead, 0xbeef]
        for val in vals:
            self._push16(val)
        vals.reverse()
        for val in vals:
            sp = self.z80.sp.val()
            self._flagsFixed(opc)
            self._regEq(self.z80.sp, sp + 2)
            self._regEq(loOrdReg, val >> 8)
            self._regEq(hiOrdReg, val & 0xff)

    def _test_pushRR(self, opc, func, loOrdReg, hiOrdReg):
        self._validOpc(opc, func, 0)
        self.z80.sp.ld(0xfffe)
        vals = [0xa5a5, 0x5a5a, 0xdead, 0xbeef]
        for val in vals:
            loOrdReg.ld(val >> 8)
            hiOrdReg.ld(val & 0xff)
            sp = self.z80.sp.val()
            self._flagsFixed(opc)
            self._regEq(self.z80.sp, sp - 2)
        vals.reverse()
        for val in vals:
            self.assertEquals(self._pop16(), val)

    def _test_resBR(self, opc, func, bitNum, reg):
        self._test_resBn(opc, func, reg.name(), 2, 8, bitNum, reg.ld, reg.val)

    def _test_resBn(self, opc, func, name, m, t, bitNum, setf, getf):
        self._validExtOpc(opc, func, 0)
        setf(0xff)
        self.z80.f.z.setTo(True)
        self.z80.f.n.setTo(True)
        self.z80.f.h.setTo(True)
        self.z80.f.c.setTo(True)
        self._runExtOp(opc)
        self.assertEquals(0xff ^ (1<<bitNum), getf())
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, True)
        setf(1 << bitNum)
        self.z80.f.z.setTo(False)
        self.z80.f.n.setTo(False)
        self.z80.f.h.setTo(False)
        self.z80.f.c.setTo(False)
        self._runExtOp(opc)
        self.assertEquals(0x00, getf())
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)

    def _test_setBR(self, opc, func, bitNum, reg):
        self._test_setBn(opc, func, reg.name(), 2, 8, bitNum, reg.ld, reg.val)

    def _test_setBn(self, opc, func, name, m, t, bitNum, setf, getf):
        self._validExtOpc(opc, func, 0)
        setf(0x00)
        self.z80.f.z.setTo(True)
        self.z80.f.n.setTo(True)
        self.z80.f.h.setTo(True)
        self.z80.f.c.setTo(True)
        self._runExtOp(opc)
        self.assertEquals(1 << bitNum, getf(), "got %d, should be %d" %
                          (getf(), 1 << bitNum))
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.n, True)
        self._flagEq(self.z80.f.h, True)
        self._flagEq(self.z80.f.c, True)
        setf(0xff ^ (1 << bitNum))
        self.z80.f.z.setTo(False)
        self.z80.f.n.setTo(False)
        self.z80.f.h.setTo(False)
        self.z80.f.c.setTo(False)
        self._runExtOp(opc)
        self.assertEquals(0xff, getf())
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)

    def _test_bitBR(self, opc, func, bitNum, reg):
        self._test_bitBn(opc, func, reg.name(), 2, 8, bitNum, reg.ld)

    def _test_bitBn(self, opc, func, name, m, t, bitNum, setf):
        self._validExtOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            val = (i * 0xa5) & 0xff
            setf(val)
            c = self.z80.f.c.val()
            self.z80.f.n.set()
            self.z80.f.h.reset()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, (val >> bitNum) & 1 == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, True)
            self._flagEq(self.z80.f.c, c)

    def _test_srlR(self, opc, func, reg):
        self._test_srln(opc, func, reg.name(), 2, 8, reg.val, reg.ld)

    def _test_srln(self, opc, func, name, m, t, getf, setf):
        self._validExtOpc(opc, func, 0)
        setf(0x80)
        for i in range(0, self.NUM_TESTS):
            val = (0x80 >> i) & 0xff
            self.assertEquals(getf(), val,
                              "%s is 0x%02x(%d), should be 0x%02x(%d)" %
                              (name, getf(), getf(), val, val))
            c = getf() & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, (0x80 >> (i + 1)) & 0xff == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)

    def _test_swapR(self, opc, func, reg):
        self._test_swapn(opc, func, reg.name(), 2, 8, reg.val, reg.ld)

    def _test_swapn(self, opc, func, name, m, t, getf, setf):
        self._validExtOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            hiOrdVal, loOrdVal = (i & 0xf, (i * 2) & 0xf)
            setf((hiOrdVal << 4) + loOrdVal)
            f = self.z80.f
            z, n, h, c = (f.z.val(), f.n.val(), f.h.val(), f.c.val())
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, z)
            self._flagEq(self.z80.f.n, n)
            self._flagEq(self.z80.f.h, h)
            self._flagEq(self.z80.f.c, c)
            expected = (loOrdVal << 4) + hiOrdVal
            self.assertEquals(getf(), expected,
                              "%s is 0x%02x(%d), should be 0x%02x(%d)" %
                              (name, getf(), getf(), expected, expected))

    def _test_slaR(self, opc, func, reg):
        self._test_slan(opc, func, reg.name(), 2, 8, reg.val, reg.ld)

    def _test_slan(self, opc, func, name, m, t, getf, setf):
        self._validExtOpc(opc, func, 0)
        setf(1)
        for i in range(0, self.NUM_TESTS):
            val = (1 << i) & 0xff
            self.assertEquals(getf(), val,
                              "%s is 0x%02x(%d), should be 0x%02x(%d)" %
                              (name, getf(), getf(), val, val))
            c = (getf() >> 7) & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, (1 << (i + 1)) & 0xff == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)

    def _test_sraR(self, opc, func, reg):
        self._test_sran(opc, func, reg.name(), 2, 8, reg.val, reg.ld)

    def _test_sran(self, opc, func, name, m, t, getf, setf):
        self._validExtOpc(opc, func, 0)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x80, 0xc0)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xc0, 0xe0)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xe0, 0xf0)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xf0, 0xf8)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xf8, 0xfc)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xfc, 0xfe)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xfe, 0xff)
        self._test_sranExec(opc, name, m, t, getf, setf, 0xff, 0xff)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x7f, 0x3f)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x3f, 0x1f)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x1f, 0x0f)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x0f, 0x07)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x07, 0x03)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x03, 0x01)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x01, 0x00)
        self._test_sranExec(opc, name, m, t, getf, setf, 0x00, 0x00)

    def _test_sranExec(self, opc, name, m, t, getf, setf, val, expected):
        setf(val)
        self.z80.f.n.set()
        self.z80.f.h.set()
        self._runExtOp(opc)
        self.assertEquals(getf(), expected,
                          "%s is 0x%02x(%d), should be 0x%02x(%d)" %
                          (name, getf(), getf(), expected, expected))
        self._flagEq(self.z80.f.z, expected == 0)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, val & 1)

    def _setMemHL(self, val):
        self.mem.set8(self._hl(), val)

    def _getMemHL(self):
        return self.mem.get8(self._hl())

    def _hl(self):
        return (self.z80.h.val() << 8) + self.z80.l.val()

    def _test_rlcR(self, opc, func, reg):
        self._validExtOpc(opc, func, 0)
        reg.ld(1)
        for i in range(0, self.NUM_TESTS):
            self._regEq(reg, (1 << (i % 8)) & 0xff)
            c = (reg.val() >> 7) & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, reg.val() == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        self.z80.f.c.reset()
        reg.ld(0)
        self.z80.f.z.reset()
        self._runExtOp(opc)
        self._flagEq(self.z80.f.z, True)

    def _test_rrcR(self, opc, func, reg):
        self._validExtOpc(opc, func, 0)
        reg.ld(0x80)
        for i in range(0, self.NUM_TESTS):
            self._regEq(reg, (0x80 >> (i % 8)) & 0xff)
            c = reg.val() & 1
            self.z80.f.n.set()
            self.z80.f.h.set()
            self._runExtOp(opc)
            self._flagEq(self.z80.f.z, reg.val() == 0)
            self._flagEq(self.z80.f.n, False)
            self._flagEq(self.z80.f.h, False)
            self._flagEq(self.z80.f.c, c)
        reg.ld(1)
        self._runExtOp(opc)
        self._regEq(reg, 0x80)
        self._flagEq(self.z80.f.c, True)
        self._runExtOp(opc)
        self._regEq(reg, 0x40)
        self._flagEq(self.z80.f.c, False)
        self.z80.f.c.reset()
        reg.ld(0)
        self.z80.f.z.reset()
        self._runExtOp(opc)
        self._flagEq(self.z80.f.z, True)

    def _test_rlR(self, opc, func, reg):
        self._validExtOpc(opc, func, 0)
        self.z80.f.n.set()
        self.z80.f.h.set()
        reg.ld(0x80)
        self._runExtOp(opc)
        self._regEq(reg, 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, True)
        self._runExtOp(opc)
        self._regEq(reg, 0x01)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)
        self._runExtOp(opc)
        self._regEq(reg, 0x02)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.c, False)

    def _test_rrR(self, opc, func, reg):
        self._validExtOpc(opc, func, 0)
        reg.ld(0x02)
        self.z80.f.n.set()
        self.z80.f.h.set()
        self._runExtOp(opc)
        self._regEq(reg, 0x01)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._runExtOp(opc)
        self._regEq(reg, 0x00)
        self._flagEq(self.z80.f.z, True)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, True)
        self._runExtOp(opc)
        self._regEq(reg, 0x80)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)
        self._runExtOp(opc)
        self._regEq(reg, 0x40)
        self._flagEq(self.z80.f.z, False)
        self._flagEq(self.z80.f.h, False)
        self._flagEq(self.z80.f.n, False)
        self._flagEq(self.z80.f.c, False)

    def _test_rstn(self, opc, func, n):
        self._validOpc(opc, func, 0)
        self.z80.sp.ld(0xfffe)
        for i in range(0, self.NUM_TESTS):
            pc = i * 0x5a
            self.z80.pc.ld(pc)
            self._flagsFixed(opc)
            self._regEq(self.z80.pc, n)
            self.assertEquals(self._pop16(), pc)

    def _test_callcnn(self, opc, cond, loOrdVal, hiOrdVal):
        pc = self.z80.pc.val()
        self._push8(0xa5)
        self._flagsFixed(opc, loOrdVal, hiOrdVal)
        self._push8(0x5a)
        self._regEq(self.z80.pc, ((hiOrdVal << 8) + loOrdVal) if cond else pc)
        self.assertEquals(self._pop8(), 0x5a)
        if cond:
            self.assertEquals(self._pop16(), pc)
        self.assertEquals(self._pop8(), 0xa5)

    def _test_retcnn(self, opc, cond, changesInts=False):
        pc = self.z80.pc.val()
        self._push8(0xa5)
        z = self.z80.f.z.val()
        self.z80.f.z.reset()
        self.z80.callNZnn(0xbe, 0xef)
        self.z80.f.z.setTo(z)
        if not changesInts:
            intsEn = self.z80.intsEnabled
        self._flagsFixed(opc)
        if cond:
            self._regEq(self.z80.pc, pc)
        else:
            self.assertEquals(self._pop16(), pc)
        self.assertEquals(self._pop8(), 0xa5)
        if not changesInts:
            self.assertEquals(intsEn, self.z80.intsEnabled)

    def _push16(self, val):
        self._push8(val >> 8)
        self._push8(val & 0xff)

    def _push8(self, val):
        sp = self.z80.sp.val() - 1
        self.z80.sp.ld(sp)
        self.mem.set8(sp, val)

    def _pop16(self):
        lo = self._pop8()
        hi = self._pop8()
        return (hi << 8) + lo

    def _pop8(self):
        sp = self.z80.sp.val()
        self.z80.sp.ld(sp + 1)
        return self.mem.get8(sp)

    def _validOpc(self, opc, func, argc):
        self._validInstrOpc(self.z80.instr, opc, func, argc)

    def _validExtOpc(self, opc, func, argc):
        self._validInstrOpc(self.z80.extInstr, opc, func, argc)

    def _validInstrOpc(self, instrs, opc, func, argc):
        self.assertTrue(opc < len(instrs), "Opcode out of instruction range")
        func_, argc_ = instrs[opc]
        self.assertEquals(func, func_,
                          "Opcode should be 0x%02x(%d)" % (opc, opc))
        self.assertEquals(argc, argc_,
                          "Instruction should take %d args, got %d" %
                          (argc, argc_))

    def _incOp8(self, opc, reg, inc, a=None, b=None):
        if inc == 0:
            raise ValueError("Can't increase register by 0")
        else:
            pos = inc > 0
        val = reg.val()
        self.z80.n = pos
        c = self.z80.f.c.val()
        self._runOp(opc, a, b)
        self._flagEq(self.z80.f.z, reg.val() == 0)
        self._flagEq(self.z80.f.n, not pos)
        self._flagEq(self.z80.f.c, c)
        self._flagEq(self.z80.f.h,
                     val & 0xf == 0xf if pos else val & 0xf == 0x0)

    def _flagsFixed(self, opc, a=None, b=None):
        """Flags are unaffected by running instruction opc with a and b"""
        f = self.z80.f
        self._expectFlags(opc, f.z.val(), f.n.val(), f.h.val(),
                          f.c.val(), a, b)

    def _runOp(self, opc, a=None, b=None):
        self._runAnyOp(self.z80.instr, opc, a, b)

    def _runExtOp(self, opc, a=None, b=None):
        self._runAnyOp(self.z80.extInstr, opc, a, b)

    def _runAnyOp(self, instrs, opc, a=None, b=None):
        op, n = instrs[opc]
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
                          "Register %s is 0x%02x(%d), should be 0x%02x(%d)" %
                          (reg.name(), reg.val(), reg.val(), val, val))

    def _test_ldRR(self, opc, func, dstReg, srcReg):
        self._validOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            val = i * 2
            srcReg.ld(val)
            self._flagsFixed(opc)
            self._regEq(dstReg, val)

    def _test_ldRMemHL(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            self.z80.h.ld(i * 4)
            self.z80.l.ld(i * 2)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            val = (i * 7) & 0xff
            self.mem.set8(addr, val)
            self._flagsFixed(opc)
            self._regEq(reg, val)

    def _test_ldMemHLR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        for i in range(0, self.NUM_TESTS):
            val = (i * 7) & 0xff
            self.z80.h.ld(val if reg == self.z80.h else i * 4)
            self.z80.l.ld(val if reg == self.z80.l else i * 2)
            addr = (self.z80.h.val() << 8) + self.z80.l.val()
            reg.ld(val)
            self._flagsFixed(opc)
            self.assertEquals(self.mem.get8(addr), reg.val())

    def _test_addAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x2b)
        self.z80.f.n.set()
        reg.ld(0x47)
        self._expectFlags(opc,
                          False, False, 0xa + 0x7 > 0xf, 0x2a + 0x47 > 0xff)
        self._regEq(self.z80.a, 0x72)
        reg.ld(0xff)
        self._expectFlags(opc,
                          False, False, 0x2 + 0xf > 0xf, 0x72 + 0xff > 0xff)
        self._regEq(self.z80.a, 0x71)
        reg.ld(0x8f)
        self._expectFlags(opc,
                          True, False, 0xf + 0x1 > 0xf, 0x71 + 0x8f > 0xff)
        self._regEq(self.z80.a, 0x00)

    def _test_adcAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x73)
        self.z80.f.n.set()
        reg.ld(0xff)
        self._expectFlags(opc, False, False, 0x3 + 0xf > 0xf, True)
        self._regEq(self.z80.a, 0x72)
        reg.ld(0x01)
        self._expectFlags(opc,
                          False, False, 0x2 + 0x1 + 0x1 > 0xf, False)
        self._regEq(self.z80.a, 0x74)
        reg.ld(0x8c)
        self._expectFlags(opc,
                          True, False, 0x4 + 0xc > 0xf, 0x74 + 0x8c > 0xff)
        self._regEq(self.z80.a, 0x00)

    def _test_subAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x9c)
        self.z80.f.n.reset()
        reg.ld(0x2a)
        self._expectFlags(opc, False, True, 0xc < 0xa, 0x9c < 0x2a)
        self._regEq(self.z80.a, 0x72)
        reg.ld(0xff)
        self._expectFlags(opc, False, True, 0x2 < 0xf, 0x72 < 0xff)
        self._regEq(self.z80.a, 0x73)
        reg.ld(0x73)
        self._expectFlags(opc, True, True, 0x3 < 0x3, 0x73 < 0x73)
        self._regEq(self.z80.a, 0x00)

    def _test_sbcAR(self, opc, func, reg):
        self._validOpc(opc, func, 0)
        self.z80.a.ld(0x9c)
        self.z80.f.n.reset()
        reg.ld(0xff)
        self._expectFlags(opc, False, True, 0xc < 0xf, True)
        self._regEq(self.z80.a, 0x9d)
        reg.ld(0x01)
        self._expectFlags(opc, False, True, 0xd < 0x1, False)
        self._regEq(self.z80.a, 0x9b)
        reg.ld(0x9b)
        self._expectFlags(opc, True, True, 0xb < 0xb, 0x9b < 0x9b)
        self._regEq(self.z80.a, 0x00)

    def _expectFlags(self, opc, z, n, h, c, a=None, b=None):
        self._runOp(opc, a, b)
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
        self._expectFlags(opc, False, False, True, False)
        self._regEq(self.z80.a, 0b0001)
        self._regEq(reg, 0b0101)
        reg.ld(0)
        self.z80.f.z.set()
        self.z80.f.n.set()
        self.z80.f.h.reset()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, True, False)
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
        self._expectFlags(opc, False, False, False, False)
        self._regEq(self.z80.a, 0b0110)
        self._regEq(reg, 0b0101)
        val = self.z80.a.val()
        reg.ld(val)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False)
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
        self._expectFlags(opc, False, False, False, False)
        self._regEq(self.z80.a, 0b0111)
        self._regEq(reg, 0b0101)
        self.z80.a.ld(0)
        reg.ld(0)
        self.z80.f.z.reset()
        self.z80.f.n.set()
        self.z80.f.h.set()
        self.z80.f.c.set()
        self._expectFlags(opc, True, False, False, False)
        self._regEq(self.z80.a, 0)
        self._regEq(reg, 0)

    def _test_cpR(self, opc, func, reg):
        for regVal in [(0x9c, 0x2a), (0x72, 0xff), (0x73, 0x73)]:
            a, v = regVal
            self.z80.a.ld(a)
            reg.ld(v)
            self.z80.f.n.reset()
            self._expectFlags(opc,
                              a == v, True, (a & 0xf) < (v & 0xf), a < v)
            self._regEq(self.z80.a, a)

    def _test_jrcn(self, opc, cond):
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 0)
        self._regEq(self.z80.pc, 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 1)
        self._regEq(self.z80.pc, 1 if cond else 0)
        self.z80.pc.ld(0)
        self._flagsFixed(opc, 127)
        self._regEq(self.z80.pc, 127 if cond else 0)
        self.z80.pc.ld(128)
        self._flagsFixed(opc, 128)
        self._regEq(self.z80.pc, 0 if cond else 128)
        self.z80.pc.ld(1)
        self._flagsFixed(opc, 255)
        self._regEq(self.z80.pc, 0 if cond else 1)

    def _test_jpcnn(self, opc, cond, hiOrdByte, loOrdByte):
        pc = self.z80.pc.val()
        self._flagsFixed(opc, loOrdByte, hiOrdByte)
        if cond:
            self._regEq(self.z80.pc, (hiOrdByte << 8) + loOrdByte)
        else:
            self._regEq(self.z80.pc, pc)

    def tearDown(self):
        self.mem = None
        self.z80 = None


if __name__ == '__main__':
    unittest.main()
