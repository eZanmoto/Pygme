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
                     ]

    def nop(self):
        """The CPU performs no operation during this machine cycle."""
        self.m += 1
        self.t += 4

    def ldBCnn(self, b, c):
        """Loads a byte into B and a byte into C."""
        self.b.ld(b)
        self.c.ld(c)
        self.m += 3
        self.t += 12

    def ldMemBCA(self):
        """Loads the contents of A into the memory address specified by BC."""
        self._mem.set8((self.b.val() << 8) + self.c.val(), self.a.val())
        self.m += 2
        self.t += 8

    def incBC(self):
        """Increments the contents of BC."""
        self.c.ld((self.c.val() + 1) & 0xff)
        if self.c.val() == 0:
            self.b.ld((self.b.val() + 1) & 0xff)
        self.m += 1
        self.t += 4

    def incB(self):
        """Increments the contents of B."""
        self.f.n.reset()
        self.f.h.setTo(self.b.val() & 0xf == 0xf)
        self.b.ld((self.b.val() + 1) & 0xff)
        self.chkZ(self.b)
        self.m += 1
        self.t += 4

    def decB(self):
        """Decrements the contents of B."""
        self.f.n.set()
        self.f.h.setTo(self.b.val() & 0xf != 0)
        self.b.ld((self.b.val() - 1) & 0xff)
        self.chkZ(self.b)
        self.m += 1
        self.t += 4

    def ldBn(self, b):
        """Loads a byte into B."""
        self.b.ld(b)
        self.m += 1
        self.t += 4

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
        if self.b.val() == 0 and self.c.val() == 0:
            self.b.ld(0xff)
            self.c.ld(0xff)
        elif self.c.val() == 0:
            self.b.ld((self.b.val() - 1) & 0xff)
            self.c.ld(0xff)
        else:
            self.c.ld((self.c.val() - 1) & 0xff)
        self.m += 1
        self.t += 4

    def incC(self):
        """Increments the contents of C."""
        self.f.n.reset()
        self.f.h.setTo(self.c.val() & 0xf == 0xf)
        self.c.ld((self.c.val() + 1) & 0xff)
        self.chkZ(self.c)
        self.m += 1
        self.t += 4

    def decC(self):
        """Decrements the contents of C."""
        self.f.n.set()
        self.f.h.setTo(self.c.val() & 0xf != 0)
        self.c.ld((self.c.val() - 1) & 0xff)
        self.chkZ(self.c)
        self.m += 1
        self.t += 4

    def ldCn(self, c):
        """Loads a byte into C."""
        self.c.ld(c)
        self.m += 1
        self.t += 4

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
        self.d.ld(d)
        self.e.ld(e)
        self.m += 3
        self.t += 12

    def ldMemDEA(self):
        """Loads the contents of A into the memory address specified by DE."""
        self._mem.set8((self.d.val() << 8) + self.e.val(), self.a.val())
        self.m += 2
        self.t += 8

    def incDE(self):
        """Increments the contents of DE."""
        self.e.ld((self.e.val() + 1) & 0xff)
        if self.e.val() == 0:
            self.d.ld((self.d.val() + 1) & 0xff)
        self.m += 1
        self.t += 4

    def incD(self):
        """Increments the contents of D."""
        self.f.n.reset()
        self.f.h.setTo(self.d.val() & 0xf == 0xf)
        self.d.ld((self.d.val() + 1) & 0xff)
        self.chkZ(self.d)
        self.m += 1
        self.t += 4

    def decD(self):
        """Decrements the contents of D."""
        self.f.n.set()
        self.f.h.setTo(self.d.val() & 0xf != 0)
        self.d.ld((self.d.val() - 1) & 0xff)
        self.chkZ(self.d)
        self.m += 1
        self.t += 4

    def ldDn(self, d):
        """Loads a byte into D."""
        self.d.ld(d)
        self.m += 1
        self.t += 4

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
        if self.d.val() == 0 and self.e.val() == 0:
            self.d.ld(0xff)
            self.e.ld(0xff)
        elif self.e.val() == 0:
            self.d.ld((self.d.val() - 1) & 0xff)
            self.e.ld(0xff)
        else:
            self.e.ld((self.e.val() - 1) & 0xff)
        self.m += 1
        self.t += 4

    def incE(self):
        """Increments the contents of E."""
        self.f.n.reset()
        self.f.h.setTo(self.e.val() & 0xf == 0xf)
        self.e.ld((self.e.val() + 1) & 0xff)
        self.chkZ(self.e)
        self.m += 1
        self.t += 4

    def chkZ(self, reg):
        self.f.z.setTo(reg.val() == 0)
