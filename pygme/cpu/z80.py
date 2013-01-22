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
        self.sp = reg16.Reg16("SP")
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
                      (self.addHLHL, 0),
                      (self.ldiAMemHL, 0),
                      (self.decHL, 0),
                      (self.incL, 0),
                      (self.decL, 0),
                      (self.ldLn, 1),
                      (self.cpl, 0),
                      (self.jrNCn, 1),
                      (self.ldSPnn, 2),
                      (self.lddMemHLA, 0),
                      (self.incSP, 0),
                     ]

    def nop(self):
        """The CPU performs no operation during this machine cycle."""
        self.m += 1
        self.t += 4

    def ldBCnn(self, b, c):
        """Loads a byte into B and a byte into C."""
        self._ldRRnn(self.b, b, self.c, c)

    def ldMemBCA(self):
        """Loads the contents of A into the memory address specified by BC."""
        self._ldMemRRA(self.b, self.c)

    def incBC(self):
        """Increments the contents of BC."""
        self._incRR(self.b, self.c)

    def incB(self):
        """Increments the contents of B."""
        self._incR(self.b)

    def decB(self):
        """Decrements the contents of B."""
        self._decR(self.b)

    def ldBn(self, b):
        """Loads a byte into B."""
        self._ldRn(self.b, b)

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
        self._addHLRR(self.b, self.c)

    def ldAMemBC(self):
        """Loads the contents of the memory address specified by BC into A."""
        self._ldAMemRR(self.b, self.c)

    def decBC(self):
        """Decrements the contents of BC."""
        self._decRR(self.b, self.c)

    def incC(self):
        """Increments the contents of C."""
        self._incR(self.c)

    def decC(self):
        """Decrements the contents of C."""
        self._decR(self.c)

    def ldCn(self, c):
        """Loads a byte into C."""
        self._ldRn(self.c, c)

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
        self._ldRRnn(self.d, d, self.e, e)

    def ldMemDEA(self):
        """Loads the contents of A into the memory address specified by DE."""
        self._ldMemRRA(self.d, self.e)

    def incDE(self):
        """Increments the contents of DE."""
        self._incRR(self.d, self.e)

    def incD(self):
        """Increments the contents of D."""
        self._incR(self.d)

    def decD(self):
        """Decrements the contents of D."""
        self._decR(self.d)

    def ldDn(self, d):
        """Loads a byte into D."""
        self._ldRn(self.d, d)

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
        self._addHLRR(self.d, self.e)

    def ldAMemDE(self):
        """Loads the contents of the memory address specified by DE into A."""
        self._ldAMemRR(self.d, self.e)

    def decDE(self):
        """Decrements the contents of DE."""
        self._decRR(self.d, self.e)

    def incE(self):
        """Increments the contents of E."""
        self._incR(self.e)

    def decE(self):
        """Decrements the contents of E."""
        self._decR(self.e)

    def ldEn(self, e):
        """Loads a byte into E."""
        self._ldRn(self.e, e)

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
        self._ldRRnn(self.h, h, self.l, l)

    def ldiMemHLA(self):
        """Loads A into the memory address in HL and increments HL."""
        self._ldMemRRA(self.h, self.l)
        self.incHL()
        self.m -= 1
        self.t -= 4

    def incHL(self):
        """Increments the contents of HL."""
        self._incRR(self.h, self.l)

    def incH(self):
        """Increments the contents of H."""
        self._incR(self.h)

    def decH(self):
        """Decrements the contents of H."""
        self._decR(self.h)

    def ldHn(self, h):
        """Loads a byte into H."""
        self._ldRn(self.h, h)

    def daa(self):
        raise NotImplementedError("'DAA' has not been implemented")

    def jrZn(self, n):
        """Decrements/increments PC by the signed 16-bit number n if Z is 1."""
        if self.f.z.val():
            self.jrn(n)
        else:
            self.m += 1
            self.t += 4

    def addHLHL(self):
        """Adds HL to HL and stores the result in HL."""
        self._addHLRR(self.h, self.l)

    def ldiAMemHL(self):
        """Loads byte at memory address in HL into A and increments HL."""
        self._ldAMemRR(self.h, self.l)
        self.incHL()
        self.m -= 1
        self.t -= 4

    def decHL(self):
        """Decrements the contents of HL."""
        self._decRR(self.h, self.l)

    def incL(self):
        """Increments the contents of L."""
        self._incR(self.l)

    def decL(self):
        """Decrements the contents of L."""
        self._decR(self.l)

    def ldLn(self, l):
        """Loads a byte into L."""
        self._ldRn(self.l, l)

    def cpl(self):
        """Complements the A register."""
        self.a.ld(0xff - self.a.val())
        self.f.n.set()
        self.f.h.set()
        self.m += 1
        self.t += 4

    def jrNCn(self, n):
        """Decrements/increments PC by the signed 16-bit number n if C is 0."""
        if self.f.c.val():
            self.m += 1
            self.t += 4
        else:
            self.jrn(n)

    def ldSPnn(self, h, l):
        """Loads a byte into S and a byte into P."""
        self.sp.ld((h << 8) + l)
        self.m += 3
        self.t += 12

    def lddMemHLA(self):
        """Loads A into the memory address in HL and decrements HL."""
        self._ldMemRRA(self.h, self.l)
        self.decHL()
        self.m -= 1
        self.t -= 4

    def incSP(self):
        """Increments the contents of SP."""
        self.sp.ld((self.sp.val() + 1) & 0xffff)
        self.m += 1
        self.t += 4

    def _ldRRnn(self, hiOrdReg, hiOrdVal, loOrdReg, loOrdVal):
        self._ldRn(hiOrdReg, hiOrdVal)
        self._ldRn(loOrdReg, loOrdVal)
        self.m += 1
        self.t += 4

    def _ldMemRRA(self, hiOrdReg, loOrdReg):
        self._mem.set8((hiOrdReg.val() << 8) + loOrdReg.val(), self.a.val())
        self.m += 2
        self.t += 8

    def _incRR(self, hiOrdReg, loOrdReg):
        loOrdReg.ld((loOrdReg.val() + 1) & 0xff)
        if loOrdReg.val() == 0:
            hiOrdReg.ld((hiOrdReg.val() + 1) & 0xff)
        self.m += 1
        self.t += 4

    def _incR(self, reg):
        self.f.n.reset()
        self.f.h.setTo(reg.val() & 0xf == 0xf)
        reg.ld((reg.val() + 1) & 0xff)
        self._chkZ(reg)
        self.m += 1
        self.t += 4

    def _decR(self, reg):
        self.f.n.set()
        self.f.h.setTo(reg.val() & 0xf != 0)
        reg.ld((reg.val() - 1) & 0xff)
        self._chkZ(reg)
        self.m += 1
        self.t += 4

    def _ldRn(self, reg, val):
        reg.ld(val)
        self.m += 1
        self.t += 4

    def _addHLRR(self, hiOrdReg, loOrdReg):
        hl = (self.h.val() << 8) + self.l.val()
        rr = (hiOrdReg.val() << 8) + loOrdReg.val()
        result = hl + rr
        self.h.ld((result >> 8) & 0xff)
        self.l.ld(result & 0xff)
        self.f.n.reset()
        self.f.h.setTo((hl & 0xfff) + (rr & 0xfff) > 0xfff)
        self.f.c.setTo(result > 0xffff)
        self.m += 3
        self.t += 12

    def _ldAMemRR(self, hiOrdReg, loOrdReg):
        self.a.ld(self._mem.get8((hiOrdReg.val() << 8) + loOrdReg.val()))
        self.m += 2
        self.t += 8

    def _decRR(self, hiOrdReg, lowOrdReg):
        if hiOrdReg.val() == 0 and lowOrdReg.val() == 0:
            hiOrdReg.ld(0xff)
            lowOrdReg.ld(0xff)
        elif lowOrdReg.val() == 0:
            hiOrdReg.ld((hiOrdReg.val() - 1) & 0xff)
            lowOrdReg.ld(0xff)
        else:
            lowOrdReg.ld((lowOrdReg.val() - 1) & 0xff)
        self.m += 1
        self.t += 4

    def _chkZ(self, reg):
        self.f.z.setTo(reg.val() == 0)
