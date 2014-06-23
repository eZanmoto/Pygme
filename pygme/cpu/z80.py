# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

from functools import partial

from pygme import bits
from pygme.cpu import reg8, reg16, reg_flag


class Flags:

    def __init__(self):
        self.z = reg_flag.RegFlag("Z")
        self.n = reg_flag.RegFlag("N")
        self.c = reg_flag.RegFlag("C")
        self.h = reg_flag.RegFlag("H")


class Z80:
    """
    The Z80 class emulates a gameboy CPU.

    The class allows the execution of emulated instructions using its
    exported methods, and monitors the side-effects of these
    instructions on its registers.

    This implementation does not include clock registers.
    """

    LEFT = True
    RIGHT = not LEFT

    POSITIVE = True
    NEGATIVE = not POSITIVE

    WITH_CARRY = True
    WITHOUT_CARRY = not WITH_CARRY

    AND = 0
    OR = 1
    XOR = 2

    INDEX_INSTR_FUNC = 0
    INDEX_INSTR_TIME = 1
    INDEX_INSTR_ARGC = 2

    def __init__(self, mem, gpu):
        self._mem = mem
        self._gpu = gpu
        self._halted = False
        self._intsEnabled = False
        self._a = reg8.Reg8("A", 0x01)
        self._b = reg8.Reg8("B", 0x00)
        self._c = reg8.Reg8("C", 0x13)
        self._d = reg8.Reg8("D", 0x00)
        self._e = reg8.Reg8("E", 0xd8)
        self._h = reg8.Reg8("H", 0x01)
        self._l = reg8.Reg8("L", 0x4d)
        self.pc = reg16.Reg16("PC", 0x0100)
        self._sp = reg16.Reg16("SP", 0xfffe)
        self.f = Flags()
        self.f.z.set()
        self.f.n.reset()
        self.f.h.set()
        self.f.c.set()
        self._instr = [
            (self._nop, 0, 0),
            (partial(self._ldrrnn, self._b, self._c), 12, 2),
            (partial(self._ldmemrra, self._b, self._c), 8, 0),
            (partial(self._incrr, self._b, self._c), 8, 0),
            (partial(self._incr, self._b), 4, 0),
            (partial(self._decr, self._b), 4, 0),
            (partial(self._ldrn, self._b), 8, 1),
            (self.rlca, 4, 0),
            (self.ldMemnnSP, 20, 2),
            (self.addHLBC, 8, 0),
            (self.ldAMemBC, 8, 0),
            (self.decBC, 8, 0),
            (self.incC, 4, 0),
            (self.decC, 4, 0),
            (self.ldCn, 8, 1),
            (self.rrca, 4, 0),
            (self.stop, 4, 0),
            (self.ldDEnn, 12, 2),
            (self.ldMemDEA, 8, 0),
            (self.incDE, 8, 0),
            (self.incD, 4, 0),
            (self.decD, 4, 0),
            (self.ldDn, 8, 1),
            (self.rla, 4, 0),
            (self.jrn, 12, 1),
            (self.addHLDE, 8, 0),
            (self.ldAMemDE, 8, 0),
            (self.decDE, 8, 0),
            (self.incE, 4, 0),
            (self.decE, 4, 0),
            (self.ldEn, 8, 1),
            (self.rra, 4, 0),
            (self.jrNZn, 8, 1),
            (self.ldHLnn, 12, 2),
            (self.ldiMemHLA, 8, 0),
            (self.incHL, 8, 0),
            (self.incH, 4, 0),
            (self.decH, 4, 0),
            (self.ldHn, 8, 1),
            (self.daa, 4, 0),
            (self.jrZn, 8, 1),
            (self.addHLHL, 8, 0),
            (self.ldiAMemHL, 8, 0),
            (self.decHL, 8, 0),
            (self.incL, 4, 0),
            (self.decL, 4, 0),
            (self.ldLn, 8, 1),
            (self.cpl, 4, 0),
            (self.jrNCn, 8, 1),
            (self.ldSPnn, 12, 2),
            (self.lddMemHLA, 8, 0),
            (self.incSP, 8, 0),
            (self.incMemHL, 12, 0),
            (self.decMemHL, 12, 0),
            (self.ldMemHLn, 12, 1),
            (self.scf, 4, 0),
            (self.jrCn, 8, 1),
            (self.addHLSP, 8, 0),
            (self.lddAMemHL, 8, 0),
            (self.decSP, 8, 0),
            (self.incA, 4, 0),
            (self.decA, 4, 0),
            (self.ldAn, 8, 1),
            (self.ccf, 4, 0),
            (self.ldBB, 4, 0),
            (self.ldBC, 4, 0),
            (self.ldBD, 4, 0),
            (self.ldBE, 4, 0),
            (self.ldBH, 4, 0),
            (self.ldBL, 4, 0),
            (self.ldBMemHL, 8, 0),
            (self.ldBA, 4, 0),
            (self.ldCB, 4, 0),
            (self.ldCC, 4, 0),
            (self.ldCD, 4, 0),
            (self.ldCE, 4, 0),
            (self.ldCH, 4, 0),
            (self.ldCL, 4, 0),
            (self.ldCMemHL, 8, 0),
            (self.ldCA, 4, 0),
            (self.ldDB, 4, 0),
            (self.ldDC, 4, 0),
            (self.ldDD, 4, 0),
            (self.ldDE, 4, 0),
            (self.ldDH, 4, 0),
            (self.ldDL, 4, 0),
            (self.ldDMemHL, 8, 0),
            (self.ldDA, 4, 0),
            (self.ldEB, 4, 0),
            (self.ldEC, 4, 0),
            (self.ldED, 4, 0),
            (self.ldEE, 4, 0),
            (self.ldEH, 4, 0),
            (self.ldEL, 4, 0),
            (self.ldEMemHL, 8, 0),
            (self.ldEA, 4, 0),
            (self.ldHB, 4, 0),
            (self.ldHC, 4, 0),
            (self.ldHD, 4, 0),
            (self.ldHE, 4, 0),
            (self.ldHH, 4, 0),
            (self.ldHL, 4, 0),
            (self.ldHMemHL, 8, 0),
            (self.ldHA, 4, 0),
            (self.ldLB, 4, 0),
            (self.ldLC, 4, 0),
            (self.ldLD, 4, 0),
            (self.ldLE, 4, 0),
            (self.ldLH, 4, 0),
            (self.ldLL, 4, 0),
            (self.ldLMemHL, 8, 0),
            (self.ldLA, 4, 0),
            (self.ldMemHLB, 8, 0),
            (self.ldMemHLC, 8, 0),
            (self.ldMemHLD, 8, 0),
            (self.ldMemHLE, 8, 0),
            (self.ldMemHLH, 8, 0),
            (self.ldMemHLL, 8, 0),
            (self.halt, 4, 0),
            (self.ldMemHLA, 8, 0),
            (self.ldAB, 4, 0),
            (self.ldAC, 4, 0),
            (self.ldAD, 4, 0),
            (self.ldAE, 4, 0),
            (self.ldAH, 4, 0),
            (self.ldAL, 4, 0),
            (self.ldAMemHL, 8, 0),
            (self.ldAA, 0, 0),
            (self.addAB, 4, 0),
            (self.addAC, 4, 0),
            (self.addAD, 4, 0),
            (self.addAE, 4, 0),
            (self.addAH, 4, 0),
            (self.addAL, 4, 0),
            (self.addAMemHL, 8, 0),
            (self.addAA, 4, 0),
            (self.adcAB, 4, 0),
            (self.adcAC, 4, 0),
            (self.adcAD, 4, 0),
            (self.adcAE, 4, 0),
            (self.adcAH, 4, 0),
            (self.adcAL, 4, 0),
            (self.adcAMemHL, 8, 0),
            (self.adcAA, 4, 0),
            (self.subAB, 4, 0),
            (self.subAC, 4, 0),
            (self.subAD, 4, 0),
            (self.subAE, 4, 0),
            (self.subAH, 4, 0),
            (self.subAL, 4, 0),
            (self.subAMemHL, 8, 0),
            (self.subAA, 4, 0),
            (self.sbcAB, 4, 0),
            (self.sbcAC, 4, 0),
            (self.sbcAD, 4, 0),
            (self.sbcAE, 4, 0),
            (self.sbcAH, 4, 0),
            (self.sbcAL, 4, 0),
            (self.sbcAMemHL, 8, 0),
            (self.sbcAA, 4, 0),
            (self.andB, 4, 0),
            (self.andC, 4, 0),
            (self.andD, 4, 0),
            (self.andE, 4, 0),
            (self.andH, 4, 0),
            (self.andL, 4, 0),
            (self.andMemHL, 8, 0),
            (self.andA, 4, 0),
            (self.xorB, 4, 0),
            (self.xorC, 4, 0),
            (self.xorD, 4, 0),
            (self.xorE, 4, 0),
            (self.xorH, 4, 0),
            (self.xorL, 4, 0),
            (self.xorMemHL, 8, 0),
            (self.xorA, 4, 0),
            (self.orB, 4, 0),
            (self.orC, 4, 0),
            (self.orD, 4, 0),
            (self.orE, 4, 0),
            (self.orH, 4, 0),
            (self.orL, 4, 0),
            (self.orMemHL, 8, 0),
            (self.orA, 4, 0),
            (self.cpB, 4, 0),
            (self.cpC, 4, 0),
            (self.cpD, 4, 0),
            (self.cpE, 4, 0),
            (self.cpH, 4, 0),
            (self.cpL, 4, 0),
            (self.cpMemHL, 8, 0),
            (self.cpA, 4, 0),
            (self.retNZ, 8, 0),
            (self.popBC, 12, 0),
            (self.jpNZnn, 12, 2),
            (self.jpnn, 12, 2),
            (self.callNZnn, 12, 2),
            (self.pushBC, 16, 0),
            (self.addAn, 8, 1),
            (self.rst0, 32, 0),
            (self.retZ, 8, 0),
            (self.ret, 8, 0),
            (self.jpZnn, 12, 2),
            (self._notInstr(0xcb), 0, 0),
            (self.callZnn, 12, 2),
            (self.callnn, 12, 2),
            (self.adcAn, 4, 1),
            (self.rst8, 32, 0),
            (self.retNC, 8, 0),
            (self.popDE, 12, 0),
            (self.jpNCnn, 12, 2),
            (self._notInstr(0xd3), 0, 0),
            (self.callNCnn, 12, 2),
            (self.pushDE, 16, 0),
            (self.subAn, 8, 1),
            (self.rst10, 32, 0),
            (self.retC, 8, 0),
            (self.reti, 12, 0),
            (self.jpCnn, 12, 2),
            (self._notInstr(0xdb), 0, 0),
            (self.callCnn, 12, 2),
            (self._notInstr(0xdd), 0, 0),
            (self.sbcAn, 8, 1),
            (self.rst18, 32, 0),
            (self.ldhMemnA, 12, 1),
            (self.popHL, 12, 0),
            (self.ldhMemCA, 8, 0),
            (self._notInstr(0xe3), 0, 0),
            (self._notInstr(0xe4), 0, 0),
            (self.pushHL, 16, 0),
            (self.andn, 8, 1),
            (self.rst20, 32, 0),
            (self.addSPn, 16, 1),
            (self.jpMemHL, 4, 0),
            (self.ldMemnnA, 16, 2),
            (self._notInstr(0xeb), 0, 0),
            (self._notInstr(0xec), 0, 0),
            (self._notInstr(0xed), 0, 0),
            (self.xorn, 8, 1),
            (self.rst28, 32, 0),
            (self.ldhAMemn, 12, 1),
            (self.popAF, 12, 0),
            (self._notInstr(0xf2), 0, 0),
            (self.di, 4, 0),
            (self._notInstr(0xf4), 0, 0),
            (self.pushAF, 16, 0),
            (self.orn, 8, 1),
            (self.rst30, 32, 0),
            (self.ldhlSPn, 12, 1),
            (self.ldSPHL, 8, 0),
            (self.ldAMemnn, 16, 2),
            (self.ei, 4, 0),
            (self._notInstr(0xfc), 0, 0),
            (self._notInstr(0xfd), 0, 0),
            (self.cpn, 8, 1),
            (self.rst38, 32, 0),
        ]
        self._extInstr = map(lambda (op, cycles): (op, cycles, 0), [
            (self.rlcB, 8),
            (self.rlcC, 8),
            (self.rlcD, 8),
            (self.rlcE, 8),
            (self.rlcH, 8),
            (self.rlcL, 8),
            (self.rlcMemHL, 16),
            (self.rlcA, 8),
            (self.rrcB, 8),
            (self.rrcC, 8),
            (self.rrcD, 8),
            (self.rrcE, 8),
            (self.rrcH, 8),
            (self.rrcL, 8),
            (self.rrcMemHL, 16),
            (self.rrcA, 8),
            (self.rlB, 8),
            (self.rlC, 8),
            (self.rlD, 8),
            (self.rlE, 8),
            (self.rlH, 8),
            (self.rlL, 8),
            (self.rlMemHL, 16),
            (self.rlA, 8),
            (self.rrB, 8),
            (self.rrC, 8),
            (self.rrD, 8),
            (self.rrE, 8),
            (self.rrH, 8),
            (self.rrL, 8),
            (self.rrMemHL, 16),
            (self.rrA, 8),
            (self.slaB, 8),
            (self.slaC, 8),
            (self.slaD, 8),
            (self.slaE, 8),
            (self.slaH, 8),
            (self.slaL, 8),
            (self.slaMemHL, 16),
            (self.slaA, 8),
            (self.sraB, 8),
            (self.sraC, 8),
            (self.sraD, 8),
            (self.sraE, 8),
            (self.sraH, 8),
            (self.sraL, 8),
            (self.sraMemHL, 16),
            (self.sraA, 8),
            (self.swapB, 8),
            (self.swapC, 8),
            (self.swapD, 8),
            (self.swapE, 8),
            (self.swapH, 8),
            (self.swapL, 8),
            (self.swapMemHL, 8),
            (self.swapA, 8),
            (self.srlB, 8),
            (self.srlC, 8),
            (self.srlD, 8),
            (self.srlE, 8),
            (self.srlH, 8),
            (self.srlL, 8),
            (self.srlMemHL, 16),
            (self.srlA, 8),
            (self.bit0B, 8),
            (self.bit0C, 8),
            (self.bit0D, 8),
            (self.bit0E, 8),
            (self.bit0H, 8),
            (self.bit0L, 8),
            (self.bit0MemHL, 16),
            (self.bit0A, 8),
            (self.bit1B, 8),
            (self.bit1C, 8),
            (self.bit1D, 8),
            (self.bit1E, 8),
            (self.bit1H, 8),
            (self.bit1L, 8),
            (self.bit1MemHL, 16),
            (self.bit1A, 8),
            (self.bit2B, 8),
            (self.bit2C, 8),
            (self.bit2D, 8),
            (self.bit2E, 8),
            (self.bit2H, 8),
            (self.bit2L, 8),
            (self.bit2MemHL, 16),
            (self.bit2A, 8),
            (self.bit3B, 8),
            (self.bit3C, 8),
            (self.bit3D, 8),
            (self.bit3E, 8),
            (self.bit3H, 8),
            (self.bit3L, 8),
            (self.bit3MemHL, 16),
            (self.bit3A, 8),
            (self.bit4B, 8),
            (self.bit4C, 8),
            (self.bit4D, 8),
            (self.bit4E, 8),
            (self.bit4H, 8),
            (self.bit4L, 8),
            (self.bit4MemHL, 16),
            (self.bit4A, 8),
            (self.bit5B, 8),
            (self.bit5C, 8),
            (self.bit5D, 8),
            (self.bit5E, 8),
            (self.bit5H, 8),
            (self.bit5L, 8),
            (self.bit5MemHL, 16),
            (self.bit5A, 8),
            (self.bit6B, 8),
            (self.bit6C, 8),
            (self.bit6D, 8),
            (self.bit6E, 8),
            (self.bit6H, 8),
            (self.bit6L, 8),
            (self.bit6MemHL, 16),
            (self.bit6A, 8),
            (self.bit7B, 8),
            (self.bit7C, 8),
            (self.bit7D, 8),
            (self.bit7E, 8),
            (self.bit7H, 8),
            (self.bit7L, 8),
            (self.bit7MemHL, 16),
            (self.bit7A, 8),
            (self.res0B, 8),
            (self.res0C, 8),
            (self.res0D, 8),
            (self.res0E, 8),
            (self.res0H, 8),
            (self.res0L, 8),
            (self.res0MemHL, 16),
            (self.res0A, 8),
            (self.res1B, 8),
            (self.res1C, 8),
            (self.res1D, 8),
            (self.res1E, 8),
            (self.res1H, 8),
            (self.res1L, 8),
            (self.res1MemHL, 16),
            (self.res1A, 8),
            (self.res2B, 8),
            (self.res2C, 8),
            (self.res2D, 8),
            (self.res2E, 8),
            (self.res2H, 8),
            (self.res2L, 8),
            (self.res2MemHL, 16),
            (self.res2A, 8),
            (self.res3B, 8),
            (self.res3C, 8),
            (self.res3D, 8),
            (self.res3E, 8),
            (self.res3H, 8),
            (self.res3L, 8),
            (self.res3MemHL, 16),
            (self.res3A, 8),
            (self.res4B, 8),
            (self.res4C, 8),
            (self.res4D, 8),
            (self.res4E, 8),
            (self.res4H, 8),
            (self.res4L, 8),
            (self.res4MemHL, 16),
            (self.res4A, 8),
            (self.res5B, 8),
            (self.res5C, 8),
            (self.res5D, 8),
            (self.res5E, 8),
            (self.res5H, 8),
            (self.res5L, 8),
            (self.res5MemHL, 16),
            (self.res5A, 8),
            (self.res6B, 8),
            (self.res6C, 8),
            (self.res6D, 8),
            (self.res6E, 8),
            (self.res6H, 8),
            (self.res6L, 8),
            (self.res6MemHL, 16),
            (self.res6A, 8),
            (self.res7B, 8),
            (self.res7C, 8),
            (self.res7D, 8),
            (self.res7E, 8),
            (self.res7H, 8),
            (self.res7L, 8),
            (self.res7MemHL, 16),
            (self.res7A, 8),
            (self.set0B, 8),
            (self.set0C, 8),
            (self.set0D, 8),
            (self.set0E, 8),
            (self.set0H, 8),
            (self.set0L, 8),
            (self.set0MemHL, 16),
            (self.set0A, 8),
            (self.set1B, 8),
            (self.set1C, 8),
            (self.set1D, 8),
            (self.set1E, 8),
            (self.set1H, 8),
            (self.set1L, 8),
            (self.set1MemHL, 16),
            (self.set1A, 8),
            (self.set2B, 8),
            (self.set2C, 8),
            (self.set2D, 8),
            (self.set2E, 8),
            (self.set2H, 8),
            (self.set2L, 8),
            (self.set2MemHL, 16),
            (self.set2A, 8),
            (self.set3B, 8),
            (self.set3C, 8),
            (self.set3D, 8),
            (self.set3E, 8),
            (self.set3H, 8),
            (self.set3L, 8),
            (self.set3MemHL, 16),
            (self.set3A, 8),
            (self.set4B, 8),
            (self.set4C, 8),
            (self.set4D, 8),
            (self.set4E, 8),
            (self.set4H, 8),
            (self.set4L, 8),
            (self.set4MemHL, 16),
            (self.set4A, 8),
            (self.set5B, 8),
            (self.set5C, 8),
            (self.set5D, 8),
            (self.set5E, 8),
            (self.set5H, 8),
            (self.set5L, 8),
            (self.set5MemHL, 16),
            (self.set5A, 8),
            (self.set6B, 8),
            (self.set6C, 8),
            (self.set6D, 8),
            (self.set6E, 8),
            (self.set6H, 8),
            (self.set6L, 8),
            (self.set6MemHL, 16),
            (self.set6A, 8),
            (self.set7B, 8),
            (self.set7C, 8),
            (self.set7D, 8),
            (self.set7E, 8),
            (self.set7H, 8),
            (self.set7L, 8),
            (self.set7MemHL, 16),
            (self.set7A, 8),
        ])

    def a(self, val=None):
        return self._reg(self._a, val)

    def b(self, val=None):
        return self._reg(self._b, val)

    def _reg(self, r, val):
        if val is not None:
            r.ld(val)
        return r.val()

    def c(self):
        return self._c.val()

    def bc(self, val=None):
        return self._double_reg(self._b, self._c, val)

    def _double_reg(self, msr, lsr, val):
        if val is not None:
            msr.ld(val >> 8)
            lsr.ld(val & 0xff)
        return (msr.val() << 8) | lsr.val()

    def d(self):
        return self._d.val()

    def e(self):
        return self._e.val()

    def h(self):
        return self._h.val()

    def l(self):
        return self._l.val()

    def zero(self):
        return self.f.z.val()

    def neg(self):
        return self.f.n.val()

    def half_carry(self):
        return self.f.h.val()

    def carry(self):
        return self.f.c.val()

    def sp(self, val=None):
        return self._reg(self._sp, val)

    def step(self):
        opc = self._fetch()
        table = self._instr
        if opc == 0xCB:
            opc = self._fetch()
            table = self._extInstr
        op, cycles, argc = table[opc]
        args = []
        for _ in xrange(argc):
            args.append(self._fetch())
        op(*args)
        return cycles

    def _fetch(self):
        val = self._mem.get8(self.pc.val())
        self.pc.ld(self.pc.val() + 1)
        return val

    def _nop(self):
        """The CPU performs no operation during this machine cycle."""

    def _ldrrnn(self, msr, lsr, lsb, msb):
        """Load `msb` into `msr` and `lsb` into `lsr`."""
        lsr.ld(lsb)
        msr.ld(msb)

    def _ldmemrra(self, msr, lsr):
        """Load A into the memory address specified by `msr` and `lsr`."""
        self._mem.set8((msr.val() << 8) + lsr.val(), self._a.val())

    def _incrr(self, msr, lsr):
        """Increment the contents of the combined `msr` and `lsr` register."""
        lsr.ld((lsr.val() + 1) & 0xff)
        if lsr.val() == 0:
            msr.ld((msr.val() + 1) & 0xff)

    def _incr(self, r):
        """Increment the contents of `r`."""
        c = self.f.c.val()
        self._arithRn(r, 1, self.POSITIVE, self.WITHOUT_CARRY)
        self.f.c.setTo(c)

    def _decr(self, r):
        """Decrements the contents of `r`."""
        c = self.f.c.val()
        self._arithRn(r, 1, self.NEGATIVE, self.WITHOUT_CARRY)
        self.f.c.setTo(c)

    def _ldrn(self, r, n):
        """Load `n` into `r`."""
        r.ld(n)

    def rlca(self):
        """A is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rotA(self.LEFT, self.WITH_CARRY)

    def ldMemnnSP(self, lsb, msb):
        addr = bits.join(8, msb, lsb)
        sp = self.sp()
        self._mem.set8(addr, sp & 0xFF)
        self._mem.set8(addr + 1, sp >> 8)

    def addHLBC(self):
        """Adds BC to HL and stores the result in HL."""
        self._addHLRR(self._b, self._c)

    def ldAMemBC(self):
        """Loads the contents of the memory address specified by BC into A."""
        self._ldAMemRR(self._b, self._c)

    def decBC(self):
        """Decrements the contents of BC."""
        self._decRR(self._b, self._c)

    def incC(self):
        """Increments the contents of C."""
        self._incR(self._c)

    def decC(self):
        """Decrements the contents of C."""
        self._decR(self._c)

    def ldCn(self, c):
        """Loads a byte into C."""
        self._ldRn(self._c, c)

    def rrca(self):
        """A is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rotA(self.RIGHT, self.WITH_CARRY)

    def stop(self):
        raise NotImplementedError("'STOP' has not been implemented")

    def ldDEnn(self, lsb, msb):
        """Loads a byte into D and a byte into E."""
        self._ldRRnn(self._d, msb, self._e, lsb)

    def ldMemDEA(self):
        """Loads the contents of A into the memory address specified by DE."""
        self._ldMemRRA(self._d, self._e)

    def incDE(self):
        """Increments the contents of DE."""
        self._incRR(self._d, self._e)

    def incD(self):
        """Increments the contents of D."""
        self._incR(self._d)

    def decD(self):
        """Decrements the contents of D."""
        self._decR(self._d)

    def ldDn(self, d):
        """Loads a byte into D."""
        self._ldRn(self._d, d)

    def rla(self):
        """A is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rotA(self.LEFT, self.WITHOUT_CARRY)

    def jrn(self, n):
        """Decrements/increments the PC by the signed byte n."""
        self._jrcn(True, n)

    def addHLDE(self):
        """Adds DE to HL and stores the result in HL."""
        self._addHLRR(self._d, self._e)

    def ldAMemDE(self):
        """Loads the contents of the memory address specified by DE into A."""
        self._ldAMemRR(self._d, self._e)

    def decDE(self):
        """Decrements the contents of DE."""
        self._decRR(self._d, self._e)

    def incE(self):
        """Increments the contents of E."""
        self._incR(self._e)

    def decE(self):
        """Decrements the contents of E."""
        self._decR(self._e)

    def ldEn(self, e):
        """Loads a byte into E."""
        self._ldRn(self._e, e)

    def rra(self):
        """A is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rotA(self.RIGHT, self.WITHOUT_CARRY)

    def jrNZn(self, n):
        """Decrements/increments PC by the signed byte n if Z is reset."""
        self._jrcn(not self.f.z.val(), n)

    def ldHLnn(self, lsb, msb):
        """Loads a byte into H and a byte into L."""
        self._ldRRnn(self._h, msb, self._l, lsb)

    def ldiMemHLA(self):
        """Loads A into the memory address in HL and increments HL."""
        self._ldMemRRA(self._h, self._l)
        self.incHL()

    def incHL(self):
        """Increments the contents of HL."""
        self._incRR(self._h, self._l)

    def incH(self):
        """Increments the contents of H."""
        self._incR(self._h)

    def decH(self):
        """Decrements the contents of H."""
        self._decR(self._h)

    def ldHn(self, h):
        """Loads a byte into H."""
        self._ldRn(self._h, h)

    def daa(self):
        raise NotImplementedError("'DAA' has not been implemented")

    def jrZn(self, n):
        """Decrements/increments PC by the signed byte n if Z is set."""
        self._jrcn(self.f.z.val(), n)

    def addHLHL(self):
        """Adds HL to HL and stores the result in HL."""
        self._addHLRR(self._h, self._l)

    def ldiAMemHL(self):
        """Loads byte at memory address in HL into A and increments HL."""
        self._ldRMemHL(self._a)
        self.incHL()

    def decHL(self):
        """Decrements the contents of HL."""
        self._decRR(self._h, self._l)

    def incL(self):
        """Increments the contents of L."""
        self._incR(self._l)

    def decL(self):
        """Decrements the contents of L."""
        self._decR(self._l)

    def ldLn(self, l):
        """Loads a byte into L."""
        self._ldRn(self._l, l)

    def cpl(self):
        """Complements the A register."""
        self._a.ld(0xff - self._a.val())
        self.f.n.set()
        self.f.h.set()

    def jrNCn(self, n):
        """Decrements/increments PC by the signed byte n if C is reset."""
        self._jrcn(not self.f.c.val(), n)

    def ldSPnn(self, lsb, msb):
        """Loads a byte into S and a byte into P."""
        self._sp.ld((msb << 8) + lsb)

    def lddMemHLA(self):
        """Loads A into the memory address in HL and decrements HL."""
        self._ldMemRRA(self._h, self._l)
        self.decHL()

    def incSP(self):
        """Increments the contents of SP."""
        self._sp.ld((self._sp.val() + 1) & 0xffff)

    def incMemHL(self):
        """Increments the contents of the memory address specified by HL."""
        self.f.n.reset()
        addr = self._hl()
        val = self._mem.get8(addr)
        self._mem.set8(addr, (val + 1) & 0xff)
        self.f.h.setTo(val & 0xf == 0xf)
        self.f.z.setTo(self._mem.get8(addr) == 0)

    def decMemHL(self):
        """Decrements the contents of the memory address specified by HL."""
        self.f.n.set()
        addr = self._hl()
        val = self._mem.get8(addr)
        self._mem.set8(addr, (val - 1) & 0xff)
        self.f.h.setTo(val & 0xf == 0)
        self.f.z.setTo(self._mem.get8(addr) == 0)

    def ldMemHLn(self, hl):
        """Loads a byte into the memory address specified by HL."""
        self._mem.set8(self._hl(), hl)

    def scf(self):
        """Sets the carry flag."""
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.set()

    def jrCn(self, n):
        """Decrements/increments PC by the signed byte n if C is set."""
        self._jrcn(self.f.c.val(), n)

    def addHLSP(self):
        """Adds SP to HL and stores the result in HL."""
        hl = (self._h.val() << 8) + self._l.val()
        result = hl + self._sp.val()
        self._h.ld((result >> 8) & 0xff)
        self._l.ld(result & 0xff)
        self.f.n.reset()
        self.f.h.setTo((hl & 0xfff) + (self._sp.val() & 0xfff) > 0xfff)
        self.f.c.setTo(result > 0xffff)

    def lddAMemHL(self):
        """Loads the value at memory address in HL into A and decrements HL."""
        self._ldRMemHL(self._a)
        self.decHL()

    def decSP(self):
        """Decrements the contents of SP."""
        self._sp.ld((self._sp.val() - 1) & 0xffff)

    def incA(self):
        """Increments the contents of A."""
        self._incR(self._a)

    def decA(self):
        """Decrements the contents of A."""
        self._decR(self._a)

    def ldAn(self, a):
        """Loads a byte into A."""
        self._ldRn(self._a, a)

    def ccf(self):
        """Complements the C flag."""
        self.f.h.reset()
        self.f.n.reset()
        self.f.c.setTo(not self.f.c.val())

    def ldBB(self):
        """Loads the contents of B into B."""
        self._ldRR(self._b, self._b)

    def ldBC(self):
        """Loads the contents of C into B."""
        self._ldRR(self._b, self._c)

    def ldBD(self):
        """Loads the contents of D into B."""
        self._ldRR(self._b, self._d)

    def ldBE(self):
        """Loads the contents of E into B."""
        self._ldRR(self._b, self._e)

    def ldBH(self):
        """Loads the contents of H into B."""
        self._ldRR(self._b, self._h)

    def ldBL(self):
        """Loads the contents of L into B."""
        self._ldRR(self._b, self._l)

    def ldBMemHL(self):
        """Loads the value at memory address in HL into B."""
        self._ldRMemHL(self._b)

    def ldBA(self):
        """Loads the contents of A into B."""
        self._ldRR(self._b, self._a)

    def ldCB(self):
        """Loads the contents of B into C."""
        self._ldRR(self._c, self._b)

    def ldCC(self):
        """Loads the contents of C into C."""
        self._ldRR(self._c, self._c)

    def ldCD(self):
        """Loads the contents of D into C."""
        self._ldRR(self._c, self._d)

    def ldCE(self):
        """Loads the contents of E into C."""
        self._ldRR(self._c, self._e)

    def ldCH(self):
        """Loads the contents of H into C."""
        self._ldRR(self._c, self._h)

    def ldCL(self):
        """Loads the contents of L into C."""
        self._ldRR(self._c, self._l)

    def ldCMemHL(self):
        """Loads the value at memory address in HL into C."""
        self._ldRMemHL(self._c)

    def ldCA(self):
        """Loads the contents of A into C."""
        self._ldRR(self._c, self._a)

    def ldDB(self):
        """Loads the contents of B into D."""
        self._ldRR(self._d, self._b)

    def ldDC(self):
        """Loads the contents of C into D."""
        self._ldRR(self._d, self._c)

    def ldDD(self):
        """Loads the contents of D into D."""
        self._ldRR(self._d, self._d)

    def ldDE(self):
        """Loads the contents of E into D."""
        self._ldRR(self._d, self._e)

    def ldDH(self):
        """Loads the contents of H into D."""
        self._ldRR(self._d, self._h)

    def ldDL(self):
        """Loads the contents of L into D."""
        self._ldRR(self._d, self._l)

    def ldDMemHL(self):
        """Loads the value at memory address in HL into D."""
        self._ldRMemHL(self._d)

    def ldDA(self):
        """Loads the contents of A into D."""
        self._ldRR(self._d, self._a)

    def ldEB(self):
        """Loads the contents of B into E."""
        self._ldRR(self._e, self._b)

    def ldEC(self):
        """Loads the contents of C into E."""
        self._ldRR(self._e, self._c)

    def ldED(self):
        """Loads the contents of D into E."""
        self._ldRR(self._e, self._d)

    def ldEE(self):
        """Loads the contents of E into E."""
        self._ldRR(self._e, self._e)

    def ldEH(self):
        """Loads the contents of H into E."""
        self._ldRR(self._e, self._h)

    def ldEL(self):
        """Loads the contents of L into E."""
        self._ldRR(self._e, self._l)

    def ldEMemHL(self):
        """Loads the value at memory address in HL into E."""
        self._ldRMemHL(self._e)

    def ldEA(self):
        """Loads the contents of A into E."""
        self._ldRR(self._e, self._a)

    def ldHB(self):
        """Loads the contents of B into H."""
        self._ldRR(self._h, self._b)

    def ldHC(self):
        """Loads the contents of C into H."""
        self._ldRR(self._h, self._c)

    def ldHD(self):
        """Loads the contents of D into H."""
        self._ldRR(self._h, self._d)

    def ldHE(self):
        """Loads the contents of E into H."""
        self._ldRR(self._h, self._e)

    def ldHH(self):
        """Loads the contents of H into H."""
        self._ldRR(self._h, self._h)

    def ldHL(self):
        """Loads the contents of L into H."""
        self._ldRR(self._h, self._l)

    def ldHMemHL(self):
        """Loads the value at memory address in HL into H."""
        self._ldRMemHL(self._h)

    def ldHA(self):
        """Loads the contents of A into H."""
        self._ldRR(self._h, self._a)

    def ldLB(self):
        """Loads the contents of B into L."""
        self._ldRR(self._l, self._b)

    def ldLC(self):
        """Loads the contents of C into L."""
        self._ldRR(self._l, self._c)

    def ldLD(self):
        """Loads the contents of D into L."""
        self._ldRR(self._l, self._d)

    def ldLE(self):
        """Loads the contents of E into L."""
        self._ldRR(self._l, self._e)

    def ldLH(self):
        """Loads the contents of H into L."""
        self._ldRR(self._l, self._h)

    def ldLL(self):
        """Loads the contents of L into L."""
        self._ldRR(self._l, self._l)

    def ldLMemHL(self):
        """Loads the value at memory address in HL into L."""
        self._ldRMemHL(self._l)

    def ldLA(self):
        """Loads the contents of A into L."""
        self._ldRR(self._l, self._a)

    def ldMemHLB(self):
        """Loads B into the memory address in HL."""
        self._ldMemHLR(self._b)

    def ldMemHLC(self):
        """Loads C into the memory address in HL."""
        self._ldMemHLR(self._c)

    def ldMemHLD(self):
        """Loads D into the memory address in HL."""
        self._ldMemHLR(self._d)

    def ldMemHLE(self):
        """Loads E into the memory address in HL."""
        self._ldMemHLR(self._e)

    def ldMemHLH(self):
        """Loads H into the memory address in HL."""
        self._ldMemHLR(self._h)

    def ldMemHLL(self):
        """Loads L into the memory address in HL."""
        self._ldMemHLR(self._l)

    def halt(self):
        raise NotImplementedError("'HALT' has not been implemented")

    def ldMemHLA(self):
        """Loads A into the memory address in HL."""
        self._ldMemHLR(self._a)

    def ldAB(self):
        """Loads the contents of B into A."""
        self._ldRR(self._a, self._b)

    def ldAC(self):
        """Loads the contents of C into A."""
        self._ldRR(self._a, self._c)

    def ldAD(self):
        """Loads the contents of D into A."""
        self._ldRR(self._a, self._d)

    def ldAE(self):
        """Loads the contents of E into A."""
        self._ldRR(self._a, self._e)

    def ldAH(self):
        """Loads the contents of H into A."""
        self._ldRR(self._a, self._h)

    def ldAL(self):
        """Loads the contents of L into A."""
        self._ldRR(self._a, self._l)

    def ldAMemHL(self):
        """Loads the value at memory address in HL into A."""
        self._ldRMemHL(self._a)

    def ldAA(self):
        """Loads the contents of A into A."""
        self._ldRR(self._a, self._a)

    def addAB(self):
        """Adds A and B and stores the result in A."""
        self._addAR(self._b)

    def addAC(self):
        """Adds A and C and stores the result in A."""
        self._addAR(self._c)

    def addAD(self):
        """Adds A and D and stores the result in A."""
        self._addAR(self._d)

    def addAE(self):
        """Adds A and E and stores the result in A."""
        self._addAR(self._e)

    def addAH(self):
        """Adds A and H and stores the result in A."""
        self._addAR(self._h)

    def addAL(self):
        """Adds A and L and stores the result in A."""
        self._addAR(self._l)

    def addAMemHL(self):
        """Adds A and value stored at address in HL and stores result in A."""
        self.addAn(self._mem.get8(self._hl()))

    def addAA(self):
        """Adds A and A and stores the result in A."""
        self._addAR(self._a)

    def adcAB(self):
        """Adds A, Carry and B and stores the result in A."""
        self._adcAR(self._b)

    def adcAC(self):
        """Adds A, Carry and C and stores the result in A."""
        self._adcAR(self._c)

    def adcAD(self):
        """Adds A, Carry and D and stores the result in A."""
        self._adcAR(self._d)

    def adcAE(self):
        """Adds A, Carry and E and stores the result in A."""
        self._adcAR(self._e)

    def adcAH(self):
        """Adds A, Carry and H and stores the result in A."""
        self._adcAR(self._h)

    def adcAL(self):
        """Adds A, Carry and L and stores the result in A."""
        self._adcAR(self._l)

    def adcAMemHL(self):
        """Adds A, Carry and value at address in HL, stores result in A."""
        self._adcAn(self._mem.get8(self._hl()))

    def adcAA(self):
        """Adds A, Carry and A and stores the result in A."""
        self._adcAR(self._a)

    def subAB(self):
        """Subtracts B from A and stores the result in A."""
        self._subAR(self._b)

    def subAC(self):
        """Subtracts C from A and stores the result in A."""
        self._subAR(self._c)

    def subAD(self):
        """Subtracts D from A and stores the result in A."""
        self._subAR(self._d)

    def subAE(self):
        """Subtracts E from A and stores the result in A."""
        self._subAR(self._e)

    def subAH(self):
        """Subtracts H from A and stores the result in A."""
        self._subAR(self._h)

    def subAL(self):
        """Subtracts L from A and stores the result in A."""
        self._subAR(self._l)

    def subAMemHL(self):
        """Subtracts value at address in HL from A and stores result in A."""
        self._subAn(self._mem.get8(self._hl()))

    def subAA(self):
        """Subtracts A from A and stores the result in A."""
        self._subAR(self._a)

    def sbcAB(self):
        """Subtracts B + Carry from A and stores the result in A."""
        self._sbcAR(self._b)

    def sbcAC(self):
        """Subtracts C + Carry from A and stores the result in A."""
        self._sbcAR(self._c)

    def sbcAD(self):
        """Subtracts D + Carry from A and stores the result in A."""
        self._sbcAR(self._d)

    def sbcAE(self):
        """Subtracts E + Carry from A and stores the result in A."""
        self._sbcAR(self._e)

    def sbcAH(self):
        """Subtracts H + Carry from A and stores the result in A."""
        self._sbcAR(self._h)

    def sbcAL(self):
        """Subtracts L + Carry from A and stores the result in A."""
        self._sbcAR(self._l)

    def sbcAMemHL(self):
        """Subtracts value at address in HL + C from A, stores result in A."""
        self._sbcAn(self._mem.get8(self._hl()))

    def sbcAA(self):
        """Subtracts A + Carry from A and stores the result in A."""
        self._sbcAR(self._a)

    def andB(self):
        """Bitwise ANDs A and B and stores the result in A."""
        self._bitwiseR(self.AND, self._b)

    def andC(self):
        """Bitwise ANDs A and C and stores the result in A."""
        self._bitwiseR(self.AND, self._c)

    def andD(self):
        """Bitwise ANDs A and D and stores the result in A."""
        self._bitwiseR(self.AND, self._d)

    def andE(self):
        """Bitwise ANDs A and E and stores the result in A."""
        self._bitwiseR(self.AND, self._e)

    def andH(self):
        """Bitwise ANDs A and H and stores the result in A."""
        self._bitwiseR(self.AND, self._h)

    def andL(self):
        """Bitwise ANDs A and L and stores the result in A."""
        self._bitwiseR(self.AND, self._l)

    def andMemHL(self):
        """Bitwise ANDs A and value at address in HL and stores result in A."""
        self._bitwisen(self.AND, self._mem.get8(self._hl()))

    def andA(self):
        """Bitwise ANDs A and A and stores the result in A."""
        self._bitwiseR(self.AND, self._a)

    def xorB(self):
        """Bitwise XORs A and B and stores the result in A."""
        self._bitwiseR(self.XOR, self._b)

    def xorC(self):
        """Bitwise XORs A and C and stores the result in A."""
        self._bitwiseR(self.XOR, self._c)

    def xorD(self):
        """Bitwise XORs A and D and stores the result in A."""
        self._bitwiseR(self.XOR, self._d)

    def xorE(self):
        """Bitwise XORs A and E and stores the result in A."""
        self._bitwiseR(self.XOR, self._e)

    def xorH(self):
        """Bitwise XORs A and H and stores the result in A."""
        self._bitwiseR(self.XOR, self._h)

    def xorL(self):
        """Bitwise XORs A and L and stores the result in A."""
        self._bitwiseR(self.XOR, self._l)

    def xorMemHL(self):
        """Bitwise XORs A and value at address in HL and stores result in A."""
        self._bitwisen(self.XOR, self._mem.get8(self._hl()))

    def xorA(self):
        """Bitwise XORs A and A and stores the result in A."""
        self._bitwiseR(self.XOR, self._a)

    def orB(self):
        """Bitwise ORs A and B and stores the result in A."""
        self._bitwiseR(self.OR, self._b)

    def orC(self):
        """Bitwise ORs A and C and stores the result in A."""
        self._bitwiseR(self.OR, self._c)

    def orD(self):
        """Bitwise ORs A and D and stores the result in A."""
        self._bitwiseR(self.OR, self._d)

    def orE(self):
        """Bitwise ORs A and E and stores the result in A."""
        self._bitwiseR(self.OR, self._e)

    def orH(self):
        """Bitwise ORs A and H and stores the result in A."""
        self._bitwiseR(self.OR, self._h)

    def orL(self):
        """Bitwise ORs A and L and stores the result in A."""
        self._bitwiseR(self.OR, self._l)

    def orMemHL(self):
        """Bitwise ORs A and value at address in HL and stores result in A."""
        self._bitwisen(self.OR, self._mem.get8(self._hl()))

    def orA(self):
        """Bitwise ORs A and A and stores the result in A."""
        self._bitwiseR(self.OR, self._a)

    def cpB(self):
        """Updates the flags with the result of subtracting B from A."""
        self._cpR(self._b)

    def cpC(self):
        """Updates the flags with the result of subtracting C from A."""
        self._cpR(self._c)

    def cpD(self):
        """Updates the flags with the result of subtracting D from A."""
        self._cpR(self._d)

    def cpE(self):
        """Updates the flags with the result of subtracting E from A."""
        self._cpR(self._e)

    def cpH(self):
        """Updates the flags with the result of subtracting H from A."""
        self._cpR(self._h)

    def cpL(self):
        """Updates the flags with the result of subtracting L from A."""
        self._cpR(self._l)

    def cpMemHL(self):
        """Updates flags after subtracting value at address in HL from A."""
        self._cpn(self._mem.get8(self._hl()))

    def cpA(self):
        """Updates the flags with the result of subtracting A from A."""
        self._cpR(self._a)

    def retNZ(self):
        """Pops the top two bytes of the stack into the PC if Z is not set."""
        if not self.f.z.val():
            self.pc.ld(self._pop16())

    def popBC(self):
        """Pops the top two bytes of the stack into BC."""
        self._popRR(self._b, self._c)

    def jpNZnn(self, loOrdByte, hiOrdByte):
        """Loads little-endian word into PC if Z is not set."""
        self._jpcnn(not self.f.z.val(), loOrdByte, hiOrdByte)

    def jpnn(self, loOrdByte, hiOrdByte):
        """Loads little-endian word into PC."""
        self._jpcnn(True, loOrdByte, hiOrdByte)

    def callNZnn(self, lsb, msb):
        """Pushes PC and loads little-endian word into PC if Z is reset."""
        self._callcnn(not self.f.z.val(), lsb, msb)

    def pushBC(self):
        """Pushes the contents of BC onto the top of the stack."""
        self._pushRR(self._b, self._c)

    def addAn(self, n):
        """Adds A and n and stores the result in A."""
        self._arithAn(n, self.POSITIVE, self.WITHOUT_CARRY)

    def rst0(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0000."""
        self._rstn(0x0000)

    def retZ(self):
        """Pops the top two bytes of the stack into the PC if Z is set."""
        if self.f.z.val():
            self.pc.ld(self._pop16())

    def ret(self):
        """Pops the top two bytes of the stack into the PC."""
        self.pc.ld(self._pop16())

    def jpZnn(self, loOrdByte, hiOrdByte):
        """Loads little-endian word into PC if Z is set."""
        self._jpcnn(self.f.z.val(), loOrdByte, hiOrdByte)

    def rlcB(self):
        """B is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._b)

    def rlcC(self):
        """C is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._c)

    def rlcD(self):
        """D is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._d)

    def rlcE(self):
        """E is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._e)

    def rlcH(self):
        """H is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._h)

    def rlcL(self):
        """L is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._l)

    def rlcMemHL(self):
        """
        Value at address in HL is rotated left 1-bit position - bit 7 goes into
        Carry and bit 0.

        """
        r = self._getMemHL()
        c = (r >> 7) & 1
        self._setMemHL(((r << 1) & 0xff) | c)
        self.f.z.setTo(self._getMemHL() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(c == 1)

    def rlcA(self):
        """A is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        self._rlcR(self._a)

    def rrcB(self):
        """B is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._b)

    def rrcC(self):
        """C is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._c)

    def rrcD(self):
        """D is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._d)

    def rrcE(self):
        """E is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._e)

    def rrcH(self):
        """H is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._h)

    def rrcL(self):
        """L is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._l)

    def rrcMemHL(self):
        """
        Value at address in HL is rotated right 1-bit position - bit 0 goes
        into Carry and bit 7.

        """
        r = self._getMemHL()
        c = r & 1
        self._setMemHL(((r >> 1) & 0xff) | c << 7)
        self.f.z.setTo(self._getMemHL() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(c == 1)

    def rrcA(self):
        """A is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        self._rrcR(self._a)

    def rlB(self):
        """B is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._b)

    def rlC(self):
        """C is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._c)

    def rlD(self):
        """D is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._d)

    def rlE(self):
        """E is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._e)

    def rlH(self):
        """H is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._h)

    def rlL(self):
        """L is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._l)

    def rlMemHL(self):
        """
        Value at address in HL is rotated left 1-bit position - bit 7 goes into
        Carry and bit 0.

        """
        r = self._getMemHL()
        c = (r >> 7) & 1
        self._setMemHL(((r << 1) & 0xff) | (1 if self.f.c.val() else 0))
        self.f.z.setTo(self._getMemHL() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(c == 1)

    def rlA(self):
        """A is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        self._rlR(self._a)

    def rrB(self):
        """B is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._b)

    def rrC(self):
        """C is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._c)

    def rrD(self):
        """D is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._d)

    def rrE(self):
        """E is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._e)

    def rrH(self):
        """H is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._h)

    def rrL(self):
        """L is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._l)

    def rrMemHL(self):
        """
        Value at address in HL is rotated right 1-bit position - bit 0 goes
        into C and C goes into bit 7.

        """
        r = self._getMemHL()
        self._setMemHL(((r >> 1) & 0xff) | (1 if self.f.c.val() else 0) << 7)
        self.f.z.setTo(self._getMemHL() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(r & 1 == 1)

    def rrA(self):
        """A is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        self._rrR(self._a)

    def slaB(self):
        """B is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._b)

    def slaC(self):
        """C is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._c)

    def slaD(self):
        """D is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._d)

    def slaE(self):
        """E is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._e)

    def slaH(self):
        """H is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._h)

    def slaL(self):
        """L is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._l)

    def slaMemHL(self):
        """
        Value at address in HL is rotated left 1-bit position - bit 7 goes into
        Carry and 0 goes into bit 0.

        """
        self._slan(self._getMemHL, self._setMemHL)

    def slaA(self):
        """A is rotated left 1-bit position - bit 7 goes into Carry and 0 goes
        into bit 0."""
        self._slaR(self._a)

    def sraB(self):
        """B is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._b)

    def sraC(self):
        """C is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._c)

    def sraD(self):
        """D is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._d)

    def sraE(self):
        """E is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._e)

    def sraH(self):
        """H is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._h)

    def sraL(self):
        """L is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._l)

    def sraMemHL(self):
        """
        Value at address in HL is rotated right 1-bit position - bit 0 goes
        into Carry and bit 7 retains its value.

        """
        self._sran(self._getMemHL, self._setMemHL)

    def sraA(self):
        """A is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        retains its value."""
        self._sraR(self._a)

    def swapB(self):
        """Swaps the most significant and least significant nibbles of B."""
        self._swapR(self._b)

    def swapC(self):
        """Swaps the most significant and least significant nibbles of C."""
        self._swapR(self._c)

    def swapD(self):
        """Swaps the most significant and least significant nibbles of D."""
        self._swapR(self._d)

    def swapE(self):
        """Swaps the most significant and least significant nibbles of E."""
        self._swapR(self._e)

    def swapH(self):
        """Swaps the most significant and least significant nibbles of H."""
        self._swapR(self._h)

    def swapL(self):
        """Swaps the most significant and least significant nibbles of L."""
        self._swapR(self._l)

    def swapMemHL(self):
        """
        Swaps the most significant and least significant nibbles of the value
        at address in HL.

        """
        self._swapn(self._getMemHL, self._setMemHL)

    def swapA(self):
        """Swaps the most significant and least significant nibbles of A."""
        self._swapR(self._a)

    def srlB(self):
        """B is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._b)

    def srlC(self):
        """C is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._c)

    def srlD(self):
        """D is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._d)

    def srlE(self):
        """E is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._e)

    def srlH(self):
        """H is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._h)

    def srlL(self):
        """L is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._l)

    def srlMemHL(self):
        """
        Value at address in HL is rotated right 1-bit position - bit 0 goes
        into Carry and bit 7 is reset.

        """
        self._srln(self._getMemHL, self._setMemHL)

    def srlA(self):
        """A is rotated right 1-bit position - bit 0 goes into Carry and bit 7
        is reset."""
        self._srlR(self._a)

    def bit0B(self):
        """Sets flag Z if bit 0 of B is reset."""
        self._bitBR(0, self._b)

    def bit0C(self):
        """Sets flag Z if bit 0 of C is reset."""
        self._bitBR(0, self._c)

    def bit0D(self):
        """Sets flag Z if bit 0 of D is reset."""
        self._bitBR(0, self._d)

    def bit0E(self):
        """Sets flag Z if bit 0 of E is reset."""
        self._bitBR(0, self._e)

    def bit0H(self):
        """Sets flag Z if bit 0 of H is reset."""
        self._bitBR(0, self._h)

    def bit0L(self):
        """Sets flag Z if bit 0 of L is reset."""
        self._bitBR(0, self._l)

    def bit0MemHL(self):
        """Sets flag Z if bit 0 of value at address in HL is reset."""
        self._bitBn(0, self._getMemHL)

    def bit0A(self):
        """Sets flag Z if bit 0 of A is reset."""
        self._bitBR(0, self._a)

    def bit1B(self):
        """Sets flag Z if bit 1 of B is reset."""
        self._bitBR(1, self._b)

    def bit1C(self):
        """Sets flag Z if bit 1 of C is reset."""
        self._bitBR(1, self._c)

    def bit1D(self):
        """Sets flag Z if bit 1 of D is reset."""
        self._bitBR(1, self._d)

    def bit1E(self):
        """Sets flag Z if bit 1 of E is reset."""
        self._bitBR(1, self._e)

    def bit1H(self):
        """Sets flag Z if bit 1 of H is reset."""
        self._bitBR(1, self._h)

    def bit1L(self):
        """Sets flag Z if bit 1 of L is reset."""
        self._bitBR(1, self._l)

    def bit1MemHL(self):
        """Sets flag Z if bit 1 of value at address in HL is reset."""
        self._bitBn(1, self._getMemHL)

    def bit1A(self):
        """Sets flag Z if bit 1 of A is reset."""
        self._bitBR(1, self._a)

    def bit2B(self):
        """Sets flag Z if bit 2 of B is reset."""
        self._bitBR(2, self._b)

    def bit2C(self):
        """Sets flag Z if bit 2 of C is reset."""
        self._bitBR(2, self._c)

    def bit2D(self):
        """Sets flag Z if bit 2 of D is reset."""
        self._bitBR(2, self._d)

    def bit2E(self):
        """Sets flag Z if bit 2 of E is reset."""
        self._bitBR(2, self._e)

    def bit2H(self):
        """Sets flag Z if bit 2 of H is reset."""
        self._bitBR(2, self._h)

    def bit2L(self):
        """Sets flag Z if bit 2 of L is reset."""
        self._bitBR(2, self._l)

    def bit2MemHL(self):
        """Sets flag Z if bit 2 of value at address in HL is reset."""
        self._bitBn(2, self._getMemHL)

    def bit2A(self):
        """Sets flag Z if bit 2 of A is reset."""
        self._bitBR(2, self._a)

    def bit3B(self):
        """Sets flag Z if bit 3 of B is reset."""
        self._bitBR(3, self._b)

    def bit3C(self):
        """Sets flag Z if bit 3 of C is reset."""
        self._bitBR(3, self._c)

    def bit3D(self):
        """Sets flag Z if bit 3 of D is reset."""
        self._bitBR(3, self._d)

    def bit3E(self):
        """Sets flag Z if bit 3 of E is reset."""
        self._bitBR(3, self._e)

    def bit3H(self):
        """Sets flag Z if bit 3 of H is reset."""
        self._bitBR(3, self._h)

    def bit3L(self):
        """Sets flag Z if bit 3 of L is reset."""
        self._bitBR(3, self._l)

    def bit3MemHL(self):
        """Sets flag Z if bit 3 of value at address in HL is reset."""
        self._bitBn(3, self._getMemHL)

    def bit3A(self):
        """Sets flag Z if bit 3 of A is reset."""
        self._bitBR(3, self._a)

    def bit4B(self):
        """Sets flag Z if bit 4 of B is reset."""
        self._bitBR(4, self._b)

    def bit4C(self):
        """Sets flag Z if bit 4 of C is reset."""
        self._bitBR(4, self._c)

    def bit4D(self):
        """Sets flag Z if bit 4 of D is reset."""
        self._bitBR(4, self._d)

    def bit4E(self):
        """Sets flag Z if bit 4 of E is reset."""
        self._bitBR(4, self._e)

    def bit4H(self):
        """Sets flag Z if bit 4 of H is reset."""
        self._bitBR(4, self._h)

    def bit4L(self):
        """Sets flag Z if bit 4 of L is reset."""
        self._bitBR(4, self._l)

    def bit4MemHL(self):
        """Sets flag Z if bit 4 of value at address in HL is reset."""
        self._bitBn(4, self._getMemHL)

    def bit4A(self):
        """Sets flag Z if bit 4 of A is reset."""
        self._bitBR(4, self._a)

    def bit5B(self):
        """Sets flag Z if bit 5 of B is reset."""
        self._bitBR(5, self._b)

    def bit5C(self):
        """Sets flag Z if bit 5 of C is reset."""
        self._bitBR(5, self._c)

    def bit5D(self):
        """Sets flag Z if bit 5 of D is reset."""
        self._bitBR(5, self._d)

    def bit5E(self):
        """Sets flag Z if bit 5 of E is reset."""
        self._bitBR(5, self._e)

    def bit5H(self):
        """Sets flag Z if bit 5 of H is reset."""
        self._bitBR(5, self._h)

    def bit5L(self):
        """Sets flag Z if bit 5 of L is reset."""
        self._bitBR(5, self._l)

    def bit5MemHL(self):
        """Sets flag Z if bit 5 of value at address in HL is reset."""
        self._bitBn(5, self._getMemHL)

    def bit5A(self):
        """Sets flag Z if bit 5 of A is reset."""
        self._bitBR(5, self._a)

    def bit6B(self):
        """Sets flag Z if bit 6 of B is reset."""
        self._bitBR(6, self._b)

    def bit6C(self):
        """Sets flag Z if bit 6 of C is reset."""
        self._bitBR(6, self._c)

    def bit6D(self):
        """Sets flag Z if bit 6 of D is reset."""
        self._bitBR(6, self._d)

    def bit6E(self):
        """Sets flag Z if bit 6 of E is reset."""
        self._bitBR(6, self._e)

    def bit6H(self):
        """Sets flag Z if bit 6 of H is reset."""
        self._bitBR(6, self._h)

    def bit6L(self):
        """Sets flag Z if bit 6 of L is reset."""
        self._bitBR(6, self._l)

    def bit6MemHL(self):
        """Sets flag Z if bit 6 of value at address in HL is reset."""
        self._bitBn(6, self._getMemHL)

    def bit6A(self):
        """Sets flag Z if bit 6 of A is reset."""
        self._bitBR(6, self._a)

    def bit7B(self):
        """Sets flag Z if bit 7 of B is reset."""
        self._bitBR(7, self._b)

    def bit7C(self):
        """Sets flag Z if bit 7 of C is reset."""
        self._bitBR(7, self._c)

    def bit7D(self):
        """Sets flag Z if bit 7 of D is reset."""
        self._bitBR(7, self._d)

    def bit7E(self):
        """Sets flag Z if bit 7 of E is reset."""
        self._bitBR(7, self._e)

    def bit7H(self):
        """Sets flag Z if bit 7 of H is reset."""
        self._bitBR(7, self._h)

    def bit7L(self):
        """Sets flag Z if bit 7 of L is reset."""
        self._bitBR(7, self._l)

    def bit7MemHL(self):
        """Sets flag Z if bit 7 of value at address in HL is reset."""
        self._bitBn(7, self._getMemHL)

    def bit7A(self):
        """Sets flag Z if bit 7 of A is reset."""
        self._bitBR(7, self._a)

    def res0B(self):
        """Reset bit 0 of B."""
        self._resBR(0, self._b)

    def res0C(self):
        """Reset bit 0 of C."""
        self._resBR(0, self._c)

    def res0D(self):
        """Reset bit 0 of D."""
        self._resBR(0, self._d)

    def res0E(self):
        """Reset bit 0 of E."""
        self._resBR(0, self._e)

    def res0H(self):
        """Reset bit 0 of H."""
        self._resBR(0, self._h)

    def res0L(self):
        """Reset bit 0 of L."""
        self._resBR(0, self._l)

    def res0MemHL(self):
        """Reset bit 0 of value at address in HL."""
        self._resBn(0, self._getMemHL, self._setMemHL)

    def res0A(self):
        """Reset bit 0 of A."""
        self._resBR(0, self._a)

    def res1B(self):
        """Reset bit 1 of B."""
        self._resBR(1, self._b)

    def res1C(self):
        """Reset bit 1 of C."""
        self._resBR(1, self._c)

    def res1D(self):
        """Reset bit 1 of D."""
        self._resBR(1, self._d)

    def res1E(self):
        """Reset bit 1 of E."""
        self._resBR(1, self._e)

    def res1H(self):
        """Reset bit 1 of H."""
        self._resBR(1, self._h)

    def res1L(self):
        """Reset bit 1 of L."""
        self._resBR(1, self._l)

    def res1MemHL(self):
        """Reset bit 1 of value at address in HL."""
        self._resBn(1, self._getMemHL, self._setMemHL)

    def res1A(self):
        """Reset bit 1 of A."""
        self._resBR(1, self._a)

    def res2B(self):
        """Reset bit 2 of B."""
        self._resBR(2, self._b)

    def res2C(self):
        """Reset bit 2 of C."""
        self._resBR(2, self._c)

    def res2D(self):
        """Reset bit 2 of D."""
        self._resBR(2, self._d)

    def res2E(self):
        """Reset bit 2 of E."""
        self._resBR(2, self._e)

    def res2H(self):
        """Reset bit 2 of H."""
        self._resBR(2, self._h)

    def res2L(self):
        """Reset bit 2 of L."""
        self._resBR(2, self._l)

    def res2MemHL(self):
        """Reset bit 2 of value at address in HL."""
        self._resBn(2, self._getMemHL, self._setMemHL)

    def res2A(self):
        """Reset bit 2 of A."""
        self._resBR(2, self._a)

    def res3B(self):
        """Reset bit 3 of B."""
        self._resBR(3, self._b)

    def res3C(self):
        """Reset bit 3 of C."""
        self._resBR(3, self._c)

    def res3D(self):
        """Reset bit 3 of D."""
        self._resBR(3, self._d)

    def res3E(self):
        """Reset bit 3 of E."""
        self._resBR(3, self._e)

    def res3H(self):
        """Reset bit 3 of H."""
        self._resBR(3, self._h)

    def res3L(self):
        """Reset bit 3 of L."""
        self._resBR(3, self._l)

    def res3MemHL(self):
        """Reset bit 3 of value at address in HL."""
        self._resBn(3, self._getMemHL, self._setMemHL)

    def res3A(self):
        """Reset bit 3 of A."""
        self._resBR(3, self._a)

    def res4B(self):
        """Reset bit 4 of B."""
        self._resBR(4, self._b)

    def res4C(self):
        """Reset bit 4 of C."""
        self._resBR(4, self._c)

    def res4D(self):
        """Reset bit 4 of D."""
        self._resBR(4, self._d)

    def res4E(self):
        """Reset bit 4 of E."""
        self._resBR(4, self._e)

    def res4H(self):
        """Reset bit 4 of H."""
        self._resBR(4, self._h)

    def res4L(self):
        """Reset bit 4 of L."""
        self._resBR(4, self._l)

    def res4MemHL(self):
        """Reset bit 4 of value at address in HL."""
        self._resBn(4, self._getMemHL, self._setMemHL)

    def res4A(self):
        """Reset bit 4 of A."""
        self._resBR(4, self._a)

    def res5B(self):
        """Reset bit 5 of B."""
        self._resBR(5, self._b)

    def res5C(self):
        """Reset bit 5 of C."""
        self._resBR(5, self._c)

    def res5D(self):
        """Reset bit 5 of D."""
        self._resBR(5, self._d)

    def res5E(self):
        """Reset bit 5 of E."""
        self._resBR(5, self._e)

    def res5H(self):
        """Reset bit 5 of H."""
        self._resBR(5, self._h)

    def res5L(self):
        """Reset bit 5 of L."""
        self._resBR(5, self._l)

    def res5MemHL(self):
        """Reset bit 5 of value at address in HL."""
        self._resBn(5, self._getMemHL, self._setMemHL)

    def res5A(self):
        """Reset bit 5 of A."""
        self._resBR(5, self._a)

    def res6B(self):
        """Reset bit 6 of B."""
        self._resBR(6, self._b)

    def res6C(self):
        """Reset bit 6 of C."""
        self._resBR(6, self._c)

    def res6D(self):
        """Reset bit 6 of D."""
        self._resBR(6, self._d)

    def res6E(self):
        """Reset bit 6 of E."""
        self._resBR(6, self._e)

    def res6H(self):
        """Reset bit 6 of H."""
        self._resBR(6, self._h)

    def res6L(self):
        """Reset bit 6 of L."""
        self._resBR(6, self._l)

    def res6MemHL(self):
        """Reset bit 6 of value at address in HL."""
        self._resBn(6, self._getMemHL, self._setMemHL)

    def res6A(self):
        """Reset bit 6 of A."""
        self._resBR(6, self._a)

    def res7B(self):
        """Reset bit 7 of B."""
        self._resBR(7, self._b)

    def res7C(self):
        """Reset bit 7 of C."""
        self._resBR(7, self._c)

    def res7D(self):
        """Reset bit 7 of D."""
        self._resBR(7, self._d)

    def res7E(self):
        """Reset bit 7 of E."""
        self._resBR(7, self._e)

    def res7H(self):
        """Reset bit 7 of H."""
        self._resBR(7, self._h)

    def res7L(self):
        """Reset bit 7 of L."""
        self._resBR(7, self._l)

    def res7MemHL(self):
        """Reset bit 7 of value at address in HL."""
        self._resBn(7, self._getMemHL, self._setMemHL)

    def res7A(self):
        """Reset bit 7 of A."""
        self._resBR(7, self._a)

    def set0B(self):
        """Set bit 0 of B."""
        self._setBR(0, self._b)

    def set0C(self):
        """Set bit 0 of C."""
        self._setBR(0, self._c)

    def set0D(self):
        """Set bit 0 of D."""
        self._setBR(0, self._d)

    def set0E(self):
        """Set bit 0 of E."""
        self._setBR(0, self._e)

    def set0H(self):
        """Set bit 0 of H."""
        self._setBR(0, self._h)

    def set0L(self):
        """Set bit 0 of L."""
        self._setBR(0, self._l)

    def set0MemHL(self):
        """Set bit 0 of value at address in HL."""
        self._setBn(0, self._getMemHL, self._setMemHL)

    def set0A(self):
        """Set bit 0 of A."""
        self._setBR(0, self._a)

    def set1B(self):
        """Set bit 1 of B."""
        self._setBR(1, self._b)

    def set1C(self):
        """Set bit 1 of C."""
        self._setBR(1, self._c)

    def set1D(self):
        """Set bit 1 of D."""
        self._setBR(1, self._d)

    def set1E(self):
        """Set bit 1 of E."""
        self._setBR(1, self._e)

    def set1H(self):
        """Set bit 1 of H."""
        self._setBR(1, self._h)

    def set1L(self):
        """Set bit 1 of L."""
        self._setBR(1, self._l)

    def set1MemHL(self):
        """Set bit 1 of value at address in HL."""
        self._setBn(1, self._getMemHL, self._setMemHL)

    def set1A(self):
        """Set bit 1 of A."""
        self._setBR(1, self._a)

    def set2B(self):
        """Set bit 2 of B."""
        self._setBR(2, self._b)

    def set2C(self):
        """Set bit 2 of C."""
        self._setBR(2, self._c)

    def set2D(self):
        """Set bit 2 of D."""
        self._setBR(2, self._d)

    def set2E(self):
        """Set bit 2 of E."""
        self._setBR(2, self._e)

    def set2H(self):
        """Set bit 2 of H."""
        self._setBR(2, self._h)

    def set2L(self):
        """Set bit 2 of L."""
        self._setBR(2, self._l)

    def set2MemHL(self):
        """Set bit 2 of value at address in HL."""
        self._setBn(2, self._getMemHL, self._setMemHL)

    def set2A(self):
        """Set bit 2 of A."""
        self._setBR(2, self._a)

    def set3B(self):
        """Set bit 3 of B."""
        self._setBR(3, self._b)

    def set3C(self):
        """Set bit 3 of C."""
        self._setBR(3, self._c)

    def set3D(self):
        """Set bit 3 of D."""
        self._setBR(3, self._d)

    def set3E(self):
        """Set bit 3 of E."""
        self._setBR(3, self._e)

    def set3H(self):
        """Set bit 3 of H."""
        self._setBR(3, self._h)

    def set3L(self):
        """Set bit 3 of L."""
        self._setBR(3, self._l)

    def set3MemHL(self):
        """Set bit 3 of value at address in HL."""
        self._setBn(3, self._getMemHL, self._setMemHL)

    def set3A(self):
        """Set bit 3 of A."""
        self._setBR(3, self._a)

    def set4B(self):
        """Set bit 4 of B."""
        self._setBR(4, self._b)

    def set4C(self):
        """Set bit 4 of C."""
        self._setBR(4, self._c)

    def set4D(self):
        """Set bit 4 of D."""
        self._setBR(4, self._d)

    def set4E(self):
        """Set bit 4 of E."""
        self._setBR(4, self._e)

    def set4H(self):
        """Set bit 4 of H."""
        self._setBR(4, self._h)

    def set4L(self):
        """Set bit 4 of L."""
        self._setBR(4, self._l)

    def set4MemHL(self):
        """Set bit 4 of value at address in HL."""
        self._setBn(4, self._getMemHL, self._setMemHL)

    def set4A(self):
        """Set bit 4 of A."""
        self._setBR(4, self._a)

    def set5B(self):
        """Set bit 5 of B."""
        self._setBR(5, self._b)

    def set5C(self):
        """Set bit 5 of C."""
        self._setBR(5, self._c)

    def set5D(self):
        """Set bit 5 of D."""
        self._setBR(5, self._d)

    def set5E(self):
        """Set bit 5 of E."""
        self._setBR(5, self._e)

    def set5H(self):
        """Set bit 5 of H."""
        self._setBR(5, self._h)

    def set5L(self):
        """Set bit 5 of L."""
        self._setBR(5, self._l)

    def set5MemHL(self):
        """Set bit 5 of value at address in HL."""
        self._setBn(5, self._getMemHL, self._setMemHL)

    def set5A(self):
        """Set bit 5 of A."""
        self._setBR(5, self._a)

    def set6B(self):
        """Set bit 6 of B."""
        self._setBR(6, self._b)

    def set6C(self):
        """Set bit 6 of C."""
        self._setBR(6, self._c)

    def set6D(self):
        """Set bit 6 of D."""
        self._setBR(6, self._d)

    def set6E(self):
        """Set bit 6 of E."""
        self._setBR(6, self._e)

    def set6H(self):
        """Set bit 6 of H."""
        self._setBR(6, self._h)

    def set6L(self):
        """Set bit 6 of L."""
        self._setBR(6, self._l)

    def set6MemHL(self):
        """Set bit 6 of value at address in HL."""
        self._setBn(6, self._getMemHL, self._setMemHL)

    def set6A(self):
        """Set bit 6 of A."""
        self._setBR(6, self._a)

    def set7B(self):
        """Set bit 7 of B."""
        self._setBR(7, self._b)

    def set7C(self):
        """Set bit 7 of C."""
        self._setBR(7, self._c)

    def set7D(self):
        """Set bit 7 of D."""
        self._setBR(7, self._d)

    def set7E(self):
        """Set bit 7 of E."""
        self._setBR(7, self._e)

    def set7H(self):
        """Set bit 7 of H."""
        self._setBR(7, self._h)

    def set7L(self):
        """Set bit 7 of L."""
        self._setBR(7, self._l)

    def set7MemHL(self):
        """Set bit 7 of value at address in HL."""
        self._setBn(7, self._getMemHL, self._setMemHL)

    def set7A(self):
        """Set bit 7 of A."""
        self._setBR(7, self._a)

    def extErr(self):
        """Raises an exception, as method shouldn't be called."""
        raise RuntimeError("Opcode 0xCB is a prefix for an extended" +
                           " instruction and should not be called directly.")

    def callZnn(self, lsb, msb):
        """Pushes PC and loads little-endian word into PC if Z is set."""
        self._callcnn(self.f.z.val(), lsb, msb)

    def callnn(self, lsb, msb):
        """Pushes PC and loads little-endian word into PC."""
        self._callcnn(True, lsb, msb)

    def adcAn(self, n):
        """Adds A, Carry and a byte and stores the result in A."""
        self._adcAn(n)

    def rst8(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0008."""
        self._rstn(0x0008)

    def retNC(self):
        """Pops the top two bytes of the stack into the PC if C is not set."""
        if not self.f.c.val():
            self.pc.ld(self._pop16())

    def popDE(self):
        """Pops the top two bytes of the stack into DE."""
        self._popRR(self._d, self._e)

    def jpNCnn(self, lsb, msb):
        """Loads little-endian word into PC if C is not set."""
        self._jpcnn(not self.f.c.val(), lsb, msb)

    def callNCnn(self, lsb, msb):
        """Pushes PC and loads little-endian word into PC if C is reset."""
        self._callcnn(not self.f.c.val(), lsb, msb)

    def pushDE(self):
        """Pushes the contents of DE onto the top of the stack."""
        self._pushRR(self._d, self._e)

    def subAn(self, n):
        """Subtracts n from A and stores result in A."""
        self._subAn(n)

    def rst10(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0010."""
        self._rstn(0x0010)

    def retC(self):
        """Pops the top two bytes of the stack into the PC if C is set."""
        if self.f.c.val():
            self.pc.ld(self._pop16())

    def reti(self):
        """Pops two bytes off the stack into the PC and enables interrupts."""
        self.ret()
        self.ei()

    def jpCnn(self, lsb, msb):
        """Loads little-endian word into PC if C is set."""
        self._jpcnn(self.f.c.val(), lsb, msb)

    def callCnn(self, lsb, msb):
        """Pushes PC and loads little-endian word into PC if C is set."""
        self._callcnn(self.f.c.val(), lsb, msb)

    def sbcAn(self, n):
        """Subtracts a byte + Carry from A and stores the result in A."""
        self._sbcAn(n)

    def rst18(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0018."""
        self._rstn(0x0018)

    def ldhMemnA(self, n):
        """Loads A into the memory location 0xFF00 + n."""
        self._assertByte(n)
        self._mem.set8(0xff00 + n, self._a.val())

    def popHL(self):
        """Pops the top two bytes of the stack into HL."""
        self._popRR(self._h, self._l)

    def ldhMemCA(self):
        """Loads A into the memory location 0xFF00 + C."""
        self._mem.set8(0xff00 + self._c.val(), self._a.val())

    def pushHL(self):
        """Pushes the contents of HL onto the top of the stack."""
        self._pushRR(self._h, self._l)

    def andn(self, n):
        """Bitwise ANDs A and a byte and stores the result in A."""
        self._bitwisen(self.AND, n)

    def rst20(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0020."""
        self._rstn(0x0020)

    def addSPn(self, n):
        """Adds signed byte to SP and stores the result in SP."""
        self._assertByte(n)
        self._sp.ld(self._sp.val() + self._to2sComp(n))

    def jpMemHL(self):
        """Loads the value of HL into PC."""
        self._jpcnn(True, self._l.val(), self._h.val())

    def ldMemnnA(self, lsb, msb):
        """Loads A into the specified memory location."""
        self._mem.set8((msb << 8) + lsb, self._a.val())

    def xorn(self, n):
        """Bitwise XORs A and a byte and stores the result in A."""
        self._bitwisen(self.XOR, n)

    def rst28(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0028."""
        self._rstn(0x0028)

    def ldhAMemn(self, n):
        """Loads the value at the memory location 0xFF00 + n into A."""
        self._assertByte(n)
        self._a.ld(self._mem.get8(0xff00 + n))

    def popAF(self):
        """Pops top byte of stack into flags register and next byte into A."""
        f = self._pop8()
        self.f.z.setTo((f >> 7) & 1 == 1)
        self.f.n.setTo((f >> 6) & 1 == 1)
        self.f.h.setTo((f >> 5) & 1 == 1)
        self.f.c.setTo((f >> 4) & 1 == 1)
        self._a.ld(self._pop8())

    def di(self):
        """Disables interrupts."""
        self._intsEnabled = False

    def pushAF(self):
        """Pushes A onto the stack and then pushes the flags register."""
        self._push8(self._a.val())
        self._push8(((1 if self.f.z.val() else 0) << 7) |
                    ((1 if self.f.n.val() else 0) << 6) |
                    ((1 if self.f.h.val() else 0) << 5) |
                    ((1 if self.f.c.val() else 0) << 4))

    def orn(self, n):
        """Bitwise ORs A and a byte and stores the result in A."""
        self._bitwisen(self.OR, n)

    def rst30(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0030."""
        self._rstn(0x0030)

    def ldhlSPn(self, n):
        self._assertByte(n)
        sp = self._sp.val()
        self.f.z.reset()
        self.f.n.reset()
        if n > 127:
            self.f.h.reset()
            self.f.c.reset()
        else:
            self.f.h.setTo((sp & 0xf) + (n & 0xf) > 0xf)
            self.f.c.setTo((sp & 0xff) + n > 0xff)
        self._sp.ld((sp + self._to2sComp(n)) & 0xffff)

    def ldSPHL(self):
        self._sp.ld(self._hl())

    def ldAMemnn(self, lsb, msb):
        self._a.ld(self._mem.get8((msb << 8) + lsb))

    def ei(self):
        """Enables interrupts."""
        self._intsEnabled = True

    def cpn(self, n):
        """Updates the flags with the result of subtracting n from A."""
        self._cpn(n)

    def rst38(self):
        """Pushes the PC onto the top of the stack and jumps to 0x0038."""
        self._rstn(0x0038)

    def _notInstr(self, opc):
        def raiseEx(opc):
            raise RuntimeError("0x%02x is not a valid instruction opcode" %
                               opc)
        return lambda: raiseEx(opc)

    def _rstn(self, n):
        self._push16(self.pc.val())
        self.jpnn(n, 0)

    def _callcnn(self, cond, lsb, msb):
        if cond:
            self._push16(self.pc.val())
            self.jpnn(lsb, msb)

    def _resBR(self, bitNum, reg):
        self._resBn(bitNum, reg.val, reg.ld)

    def _resBn(self, bitNum, getf, setf):
        setf(getf() & (~ (1 << bitNum)))

    def _setBR(self, bitNum, reg):
        self._setBn(bitNum, reg.val, reg.ld)

    def _setBn(self, bitNum, getf, setf):
        setf(getf() | (1 << bitNum))

    def _bitBR(self, bitNum, reg):
        self._bitBn(bitNum, reg.val)

    def _bitBn(self, bitNum, getf):
        self.f.z.setTo((getf() >> bitNum) & 1 == 0)
        self.f.n.reset()
        self.f.h.set()

    def _srlR(self, reg):
        self._srln(reg.val, reg.ld)

    def _srln(self, getf, setf):
        v = getf()
        setf((v >> 1) & 0xff)
        self.f.z.setTo(getf() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(v & 1 == 1)

    def _swapR(self, reg):
        self._swapn(reg.val, reg.ld)

    def _swapn(self, getf, setf):
        setf(((getf() & 0xf) << 4) + ((getf() >> 4) & 0xf))

    def _slaR(self, reg):
        self._slan(reg.val, reg.ld)

    def _slan(self, getf, setf):
        v = getf()
        setf((v << 1) & 0xff)
        self.f.z.setTo(getf() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo((v >> 7) & 1 == 1)

    def _sraR(self, reg):
        self._sran(reg.val, reg.ld)

    def _sran(self, getf, setf):
        v = getf()
        setf(((v >> 1) & 0xff) | (v & 0x80))
        self.f.z.setTo(getf() == 0)  # NOTE Z is unaffected on Z80
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(v & 1 == 1)

    def _setMemHL(self, val):
        self._mem.set8(self._hl(), val)

    def _getMemHL(self):
        return self._mem.get8(self._hl())

    def _rlcR(self, reg):
        self._rotR(reg, self.LEFT, self.WITH_CARRY)

    def _rrcR(self, reg):
        self._rotR(reg, self.RIGHT, self.WITH_CARRY)

    def _rlR(self, reg):
        self._rotR(reg, self.LEFT, self.WITHOUT_CARRY)

    def _rrR(self, reg):
        self._rotR(reg, self.RIGHT, self.WITHOUT_CARRY)

    def _ldRRnn(self, hiOrdReg, hiOrdVal, loOrdReg, loOrdVal):
        self._ldRn(hiOrdReg, hiOrdVal)
        self._ldRn(loOrdReg, loOrdVal)

    def _ldMemRRA(self, hiOrdReg, loOrdReg):
        self._mem.set8((hiOrdReg.val() << 8) + loOrdReg.val(), self._a.val())

    def _incRR(self, hiOrdReg, loOrdReg):
        loOrdReg.ld((loOrdReg.val() + 1) & 0xff)
        if loOrdReg.val() == 0:
            hiOrdReg.ld((hiOrdReg.val() + 1) & 0xff)

    def _incR(self, reg):
        c = self.f.c.val()
        self._arithRn(reg, 1, True, False)
        self.f.c.setTo(c)

    def _decR(self, reg):
        c = self.f.c.val()
        self._arithRn(reg, 1, False, False)
        self.f.c.setTo(c)

    def _ldRn(self, reg, val):
        reg.ld(val)

    def _rotA(self, rotLeft, withCarry):
        self._rotR(self._a, rotLeft, withCarry)

    def _rotR(self, reg, rotLeft, withCarry):
        r = reg.val()
        c = (r >> 7) & 1 if rotLeft else r & 1
        orBit = c if withCarry else (1 if self.f.c.val() else 0)
        if not rotLeft:
            orBit <<= 7
        reg.ld(((r << 1 if rotLeft else r >> 1) & 0xff) | orBit)
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(c == 1)
        self._chkZ(reg)  # NOTE Z is unaffected on Z80

    def _addHLRR(self, hiOrdReg, loOrdReg):
        hl = (self._h.val() << 8) + self._l.val()
        rr = (hiOrdReg.val() << 8) + loOrdReg.val()
        result = hl + rr
        self._h.ld((result >> 8) & 0xff)
        self._l.ld(result & 0xff)
        self.f.n.reset()
        self.f.h.setTo((hl & 0xfff) + (rr & 0xfff) > 0xfff)
        self.f.c.setTo(result > 0xffff)

    def _ldAMemRR(self, hiOrdReg, loOrdReg):
        self._a.ld(self._mem.get8((hiOrdReg.val() << 8) + loOrdReg.val()))

    def _decRR(self, hiOrdReg, loOrdReg):
        loOrdReg.ld((loOrdReg.val() - 1) & 0xff)
        if loOrdReg.val() == 0xff:
            hiOrdReg.ld((hiOrdReg.val() - 1) & 0xff)

    def _ldRR(self, dstReg, srcReg):
        self._ldRn(dstReg, srcReg.val())

    def _ldRMemHL(self, reg):
        self._ldRn(reg, self._mem.get8(self._hl()))

    def _ldMemHLR(self, reg):
        self._mem.set8(self._hl(), reg.val())

    def _addAR(self, reg):
        self.addAn(reg.val())

    def _adcAR(self, reg):
        self._adcAn(reg.val())

    def _adcAn(self, val):
        self._arithAn(val, self.POSITIVE, self.WITH_CARRY)

    def _subAR(self, reg):
        self._subAn(reg.val())

    def _subAn(self, v):
        self._arithAn(v, self.NEGATIVE, self.WITHOUT_CARRY)

    def _sbcAR(self, reg):
        self._sbcAn(reg.val())

    def _sbcAn(self, v):
        self._arithAn(v, self.NEGATIVE, self.WITH_CARRY)

    def _arithAn(self, v, isPositive, withCarry):
        self._arithRn(self._a, v, isPositive, withCarry)

    def _arithRn(self, reg, v, isPositive, withCarry):
        self._assertByte(v)
        r = reg.val()
        c = 1 if withCarry and self.f.c.val() else 0
        if isPositive:
            r_ = r + v + c
            h_ = (r & 0xf) + (v & 0xf) + c
        else:
            r_ = r - v - c
            h_ = (r & 0xf) - (v & 0xf) - c
        self.f.n.setTo(not isPositive)
        self.f.h.setTo(h_ < 0x0 or h_ > 0xf)
        self.f.c.setTo(r_ < 0x00 or r_ > 0xff)
        reg.ld(r_ & 0xff)
        self._chkZ(reg)

    def _bitwiseR(self, op, reg):
        self._bitwisen(op, reg.val())

    def _bitwisen(self, op, val):
        self._assertByte(val)
        if op == self.AND:
            f = lambda a, b: a & b
        elif op == self.OR:
            f = lambda a, b: a | b
        elif op == self.XOR:
            f = lambda a, b: a ^ b
        self._a.ld(f(self._a.val(), val))
        self.f.n.reset()
        self.f.h.setTo(op == self.AND)
        self.f.c.reset()
        self._chkZ(self._a)

    def _cpR(self, reg):
        self._cpn(reg.val())

    def _cpn(self, val):
        a = self._a.val()
        self._subAn(val)
        self._a.ld(a)

    def _popRR(self, hiOrdReg, loOrdReg):
        v = self._pop16()
        hiOrdReg.ld(v >> 8)
        loOrdReg.ld(v & 0xff)

    def _pop16(self):
        lsb = self._pop8()
        msb = self._pop8()
        return (msb << 8) + lsb

    def _pop8(self):
        addr = self._sp.val()
        self._sp.ld(addr + 1)
        return self._mem.get8(addr)

    def _pushRR(self, hiOrdReg, loOrdReg):
        self._push16((hiOrdReg.val() << 8) + loOrdReg.val())

    def _push16(self, val):
        self._push8(val >> 8)
        self._push8(val & 0xff)

    def _push8(self, val):
        sp = self._sp.val() - 1
        self._mem.set8(sp, val)
        self._sp.ld(sp)

    def _jrcn(self, cond, n):
        self._assertByte(n)
        if cond:
            pc = self.pc.val() + self._to2sComp(n)
            self.pc.ld(pc & 0xffff)

    def _to2sComp(self, n):
        self._assertByte(n)
        if n > 127:
            n = (n & 127) - 128
        return n

    def _jpcnn(self, cond, loOrdByte, hiOrdByte):
        self._assertByte(loOrdByte)
        if cond:
            self.pc.ld((hiOrdByte << 8) + loOrdByte)

    def _assertByte(self, n):
        if n < 0 or n > 0xff:
            raise ValueError("Byte 0x%x(%d) must be 8-bit" % (n, n))

    def _chkZ(self, reg):
        self.f.z.setTo(reg.val() == 0)

    def _hl(self):
        return (self._h.val() << 8) + self._l.val()
