# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

from pygme.cpu import reg8, reg16, reg_flag

class Flags:

    def __init__(self):
        self.z = reg_flag.RegFlag("Z")
        self.n = reg_flag.RegFlag("N")
        self.c = reg_flag.RegFlag("C")
        self.h = reg_flag.RegFlag("H")

# Instructions that update flags:
#     LDHL SP, n
#     ADD  A, n
#     ADC  A, n
#     SUB  A, n
#     SBC  A, n
#     AND  A, n
#     OR   A, n
#     XOR  A, n
#     CP   A, n
#     INC  n
#     DEC  n
#     ADD  HL, n
#     ADD  SP, n
#     SWAP n
#     DAA
#     CPL
#     CFF
#     SCF
#     RLCA
#     RLA
#     RRCA
#     RRA
#     RLC  n
#     RL   n
#     RRC  n
#     RR   n
#     SLA  n
#     SRA  n
#     SRL  n
#     BIT  b, r
#     JP   cc, nn
class Z80:

    def __init__(self, mem):
        self.a = reg8.Reg8("A")
        self.b = reg8.Reg8("B")
        self.c = reg8.Reg8("C")
        self.d = reg8.Reg8("D")
        self.e = reg8.Reg8("E")
        self.h = reg8.Reg8("H")
        self.l = reg8.Reg8("L")
        self.pc = reg16.Reg16("PC")
        self.m = 0
        self.t = 0
        self.f = Flags()
        self._mem = mem
        self.instr = [(self.nop, 0),
                      (self.ldBCnn, 2),
                      (self.ldMemBCA, 0),
                      (self.incBC, 0),
                      (self.incB, 0),
                      (self.decB, 0),
                      (self.ldBn, 1),
                      (self.rlcA, 0),
                      (self.ldMemnnSP, 2),
                      (self.addHLBC, 0),
                      (self.ldAMemBC, 0),
                      (self.decBC, 0),
                      (self.incC, 0),
                      (self.decC, 0),
                      (self.ldCn, 1),
                      (self.rrcA, 0),
                      (self.stop, 0),
                      (self.ldDEnn, 2),
                      (self.ldMemDEA, 0),
                      (self.incDE, 0),
                      (self.incD, 0),
                      (self.decD, 0),
                      (self.ldDn, 1),
                      (self.rlA, 0),
                      (self.jrn, 1),
                      (self.addHLDE, 0),
                      (self.ldAMemDE, 0),
                      (self.decDE, 0),
                      (self.incE, 0),
                      (self.decE, 0),
                      (self.ldEn, 1),
                      (self.rrA, 0),
                      (self.jrNZn, 1),
                      (self.ldHLnn, 2),
                      (self.ldiMemHLA, 0),
                      (self.incHL, 0),
                      (self.incH, 0),
                      (self.decH, 0),
                      (self.ldHn, 1),
                      (self.daa, 0),
                      (self.jrZn, 1),
                     ]

    def nop(self):
        """The CPU performs no operation during this machine cycle."""
        self.m += 1
        self.t += 4

    def ldBCnn(self, b, c):
        """Loads a byte into B and a byte into C."""
        self._ld16(self.b, b, self.c, c)

    def ldMemBCA(self):
        """Loads the contents of A into the memory address specified by BC."""
        self._ldMemRA(self.b, self.c)

    def incBC(self):
        """Increments the contents of BC."""
        self._inc16(self.b, self.c)

    def incB(self):
        """Increments the contents of B."""
        self._inc8(self.b)

    def decB(self):
        """Decrements the contents of B."""
        self._dec8(self.b)

    def ldBn(self, b):
        """Loads a byte into B."""
        self._ld8(self.b, b)

    def rlcA(self):
        """A is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        bit7 = (self.a.val() >> 7) & 1
        self.a.ld(((self.a.val() << 1) & 0xff) | bit7)
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(bit7)
        self.m += 1
        self.t += 4

    def ldMemnnSP(self, n, m):
        raise NotImplementedError("'LD (nn), SP' has not been implemented")

    def addHLBC(self):
        """Adds BC to HL and stores the result in HL."""
        hl = (self.h.val() << 8) + self.l.val()
        bc = (self.b.val() << 8) + self.c.val()
        result = hl + bc
        self.h.ld((result >> 8) & 0xff)
        self.l.ld(result & 0xff)
        self.f.n.reset()
        self.f.h.setTo((hl & 0xfff) + (bc & 0xfff) > 0xfff)
        self.f.c.setTo(result > 0xffff)
        self.m += 3
        self.t += 12

    def ldAMemBC(self):
        """Loads the contents of the memory address specified by BC into A."""
        self.a.ld(self._mem.get8((self.b.val() << 8) + self.c.val()))
        self.m += 2
        self.t += 8

    def decBC(self):
        """Decrements the contents of BC."""
        self._dec16(self.b, self.c)

    def incC(self):
        """Increments the contents of C."""
        self._inc8(self.c)

    def decC(self):
        """Decrements the contents of C."""
        self._dec8(self.c)

    def ldCn(self, c):
        """Loads a byte into C."""
        self._ld8(self.c, c)

    def rrcA(self):
        """A is rotated right 1-bit position - bit 0 goes into C and bit 7."""
        bit0 = self.a.val() & 1
        self.a.ld(((self.a.val() >> 1) & 0xff) | (bit0 << 7))
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(bit0)
        self.m += 1
        self.t += 4

    def stop(self):
        raise NotImplementedError("'STOP' has not been implemented")

    def ldDEnn(self, d, e):
        """Loads a byte into D and a byte into E."""
        self._ld16(self.d, d, self.e, e)

    def ldMemDEA(self):
        """Loads the contents of A into the memory address specified by DE."""
        self._ldMemRA(self.d, self.e)

    def incDE(self):
        """Increments the contents of DE."""
        self._inc16(self.d, self.e)

    def incD(self):
        """Increments the contents of D."""
        self._inc8(self.d)

    def decD(self):
        """Decrements the contents of D."""
        self._dec8(self.d)

    def ldDn(self, d):
        """Loads a byte into D."""
        self._ld8(self.d, d)

    def rlA(self):
        """A is rotated left 1-bit position - bit 7 goes into C and C goes into
        bit 0."""
        bit7 = (self.a.val() >> 7) & 1
        self.a.ld(((self.a.val() << 1) & 0xff) | self.f.c.val())
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(bit7)
        self.m += 1
        self.t += 4

    def jrn(self, n):
        """Decrements/increments the PC by the signed 16-bit number n."""
        pc = self.pc.val()
        pc = (pc + n) - 126
        self.pc.ld(pc & 0xffff)
        self.m += 1
        self.t += 4

    def addHLDE(self):
        """Adds DE to HL and stores the result in HL."""
        hl = (self.h.val() << 8) + self.l.val()
        de = (self.d.val() << 8) + self.e.val()
        result = hl + de
        self.h.ld((result >> 8) & 0xff)
        self.l.ld(result & 0xff)
        self.f.n.reset()
        self.f.h.setTo((hl & 0xfff) + (de & 0xfff) > 0xfff)
        self.f.c.setTo(result > 0xffff)
        self.m += 3
        self.t += 12

    def ldAMemDE(self):
        """Loads the contents of the memory address specified by DE into A."""
        self.a.ld(self._mem.get8((self.d.val() << 8) + self.e.val()))
        self.m += 2
        self.t += 8

    def decDE(self):
        """Decrements the contents of DE."""
        self._dec16(self.d, self.e)

    def incE(self):
        """Increments the contents of E."""
        self._inc8(self.e)

    def decE(self):
        """Decrements the contents of E."""
        self._dec8(self.e)

    def ldEn(self, e):
        """Loads a byte into E."""
        self._ld8(self.e, e)

    def rrA(self):
        """A is rotated right 1-bit position - bit 0 goes into C and C goes
        into bit 7."""
        bit0 = self.a.val() & 1
        self.a.ld(((self.a.val() >> 1) & 0xff) | (self.f.c.val() << 7))
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.setTo(bit0)
        self.m += 1
        self.t += 4

    def jrNZn(self, n):
        """Decrements/increments PC by the signed 16-bit number n if Z is 0."""
        if self.f.z.val():
            self.m += 1
            self.t += 4
        else:
            self.jrn(n)

    def ldHLnn(self, h, l):
        """Loads a byte into H and a byte into L."""
        self._ld16(self.h, h, self.l, l)

    def ldiMemHLA(self):
        """Loads A into the memory address in HL and increments HL."""
        self._ldMemRA(self.h, self.l)
        self.incHL()
        self.m -= 1
        self.t -= 4

    def incHL(self):
        """Increments the contents of HL."""
        self._inc16(self.h, self.l)

    def incH(self):
        """Increments the contents of H."""
        self._inc8(self.h)

    def decH(self):
        """Decrements the contents of H."""
        self._dec8(self.h)

    def ldHn(self, h):
        """Loads a byte into H."""
        self._ld8(self.h, h)

    def daa(self):
        raise NotImplementedError("'DAA' has not been implemented")

    def jrZn(self, n):
        """Decrements/increments PC by the signed 16-bit number n if Z is 1."""
        if self.f.z.val():
            self.jrn(n)
        else:
            self.m += 1
            self.t += 4

    def _ld8(self, reg, val):
        reg.ld(val)
        self.m += 1
        self.t += 4

    def _ld16(self, hiOrdReg, hiOrdVal, loOrdReg, loOrdVal):
        self._ld8(hiOrdReg, hiOrdVal)
        self._ld8(loOrdReg, loOrdVal)
        self.m += 1
        self.t += 4

    def _inc8(self, reg):
        self.f.n.reset()
        self.f.h.setTo(reg.val() & 0xf == 0xf)
        reg.ld((reg.val() + 1) & 0xff)
        self._chkZ(reg)
        self.m += 1
        self.t += 4

    def _dec8(self, reg):
        self.f.n.set()
        self.f.h.setTo(reg.val() & 0xf != 0)
        reg.ld((reg.val() - 1) & 0xff)
        self._chkZ(reg)
        self.m += 1
        self.t += 4

    def _inc16(self, highOrdReg, lowOrdReg):
        lowOrdReg.ld((lowOrdReg.val() + 1) & 0xff)
        if lowOrdReg.val() == 0:
            highOrdReg.ld((highOrdReg.val() + 1) & 0xff)
        self.m += 1
        self.t += 4

    def _dec16(self, highOrdReg, lowOrdReg):
        if highOrdReg.val() == 0 and lowOrdReg.val() == 0:
            highOrdReg.ld(0xff)
            lowOrdReg.ld(0xff)
        elif lowOrdReg.val() == 0:
            highOrdReg.ld((highOrdReg.val() - 1) & 0xff)
            lowOrdReg.ld(0xff)
        else:
            lowOrdReg.ld((lowOrdReg.val() - 1) & 0xff)
        self.m += 1
        self.t += 4

    def _ldMemRA(self, highOrdReg, lowOrdReg):
        self._mem.set8((highOrdReg.val() << 8) + lowOrdReg.val(), self.a.val())
        self.m += 2
        self.t += 8

    def _chkZ(self, reg):
        self.f.z.setTo(reg.val() == 0)
