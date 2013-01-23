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
                      (self.incMemHL, 0),
                      (self.decMemHL, 0),
                      (self.ldMemHLn, 1),
                      (self.scf, 0),
                      (self.jrCn, 1),
                      (self.addHLSP, 0),
                      (self.lddAMemHL, 0),
                      (self.decSP, 0),
                      (self.incA, 0),
                      (self.decA, 0),
                      (self.ldAn, 1),
                      (self.ccf, 0),
                      (self.ldBB, 0),
                      (self.ldBC, 0),
                      (self.ldBD, 0),
                      (self.ldBE, 0),
                      (self.ldBH, 0),
                      (self.ldBL, 0),
                      (self.ldBMemHL, 0),
                      (self.ldBA, 0),
                      (self.ldCB, 0),
                      (self.ldCC, 0),
                      (self.ldCD, 0),
                      (self.ldCE, 0),
                      (self.ldCH, 0),
                      (self.ldCL, 0),
                      (self.ldCMemHL, 0),
                      (self.ldCA, 0),
                      (self.ldDB, 0),
                      (self.ldDC, 0),
                      (self.ldDD, 0),
                      (self.ldDE, 0),
                      (self.ldDH, 0),
                      (self.ldDL, 0),
                      (self.ldDMemHL, 0),
                      (self.ldDA, 0),
                      (self.ldEB, 0),
                      (self.ldEC, 0),
                      (self.ldED, 0),
                      (self.ldEE, 0),
                      (self.ldEH, 0),
                      (self.ldEL, 0),
                      (self.ldEMemHL, 0),
                      (self.ldEA, 0),
                      (self.ldHB, 0),
                      (self.ldHC, 0),
                      (self.ldHD, 0),
                      (self.ldHE, 0),
                      (self.ldHH, 0),
                      (self.ldHL, 0),
                      (self.ldHMemHL, 0),
                      (self.ldHA, 0),
                      (self.ldLB, 0),
                      (self.ldLC, 0),
                      (self.ldLD, 0),
                      (self.ldLE, 0),
                      (self.ldLH, 0),
                      (self.ldLL, 0),
                      (self.ldLMemHL, 0),
                      (self.ldLA, 0),
                      (self.ldMemHLB, 0),
                      (self.ldMemHLC, 0),
                      (self.ldMemHLD, 0),
                      (self.ldMemHLE, 0),
                      (self.ldMemHLH, 0),
                      (self.ldMemHLL, 0),
                      (self.halt, 0),
                      (self.ldMemHLA, 0),
                      (self.ldAB, 0),
                      (self.ldAC, 0),
                      (self.ldAD, 0),
                      (self.ldAE, 0),
                      (self.ldAH, 0),
                      (self.ldAL, 0),
                      (self.ldAMemHL, 0),
                      (self.ldAA, 0),
                      (self.addAB, 0),
                      (self.addAC, 0),
                      (self.addAD, 0),
                      (self.addAE, 0),
                      (self.addAH, 0),
                      (self.addAL, 0),
                      (self.addAMemHL, 0),
                      (self.addAA, 0),
                      (self.adcAB, 0),
                      (self.adcAC, 0),
                      (self.adcAD, 0),
                      (self.adcAE, 0),
                      (self.adcAH, 0),
                      (self.adcAL, 0),
                      (self.adcAMemHL, 0),
                      (self.adcAA, 0),
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
        self._ldRMemHL(self.a)
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

    def incMemHL(self):
        """Increments the contents of the memory address specified by HL."""
        self.f.n.reset()
        addr = self._hl()
        val = self._mem.get8(addr)
        self._mem.set8(addr, (val + 1) & 0xff)
        self.f.h.setTo(val & 0xf  == 0xf)
        self.f.z.setTo(self._mem.get8(addr) == 0)
        self.m += 3
        self.t += 12

    def decMemHL(self):
        """Decrements the contents of the memory address specified by HL."""
        self.f.n.set()
        addr = self._hl()
        val = self._mem.get8(addr)
        self._mem.set8(addr, (val - 1) & 0xff)
        self.f.h.setTo(val & 0xf != 0)
        self.f.z.setTo(self._mem.get8(addr) == 0)
        self.m += 3
        self.t += 12

    def ldMemHLn(self, hl):
        """Loads a byte into the memory address specified by HL."""
        self._mem.set8(self._hl(), hl)
        self.m += 3
        self.t += 12

    def scf(self):
        """Sets the carry flag."""
        self.f.n.reset()
        self.f.h.reset()
        self.f.c.set()
        self.m += 1
        self.t += 4

    def jrCn(self, n):
        """Decrements/increments PC by the signed 16-bit number n if C is 1."""
        if self.f.c.val():
            self.jrn(n)
        else:
            self.m += 1
            self.t += 4

    def addHLSP(self):
        """Adds SP to HL and stores the result in HL."""
        hl = (self.h.val() << 8) + self.l.val()
        result = hl + self.sp.val()
        self.h.ld((result >> 8) & 0xff)
        self.l.ld(result & 0xff)
        self.f.n.reset()
        self.f.h.setTo((hl & 0xfff) + (self.sp.val() & 0xfff) > 0xfff)
        self.f.c.setTo(result > 0xffff)
        self.m += 3
        self.t += 12

    def lddAMemHL(self):
        """Loads the value at memory address in HL into A and decrements HL."""
        self._ldRMemHL(self.a)
        self.decHL()
        self.m -= 1
        self.t -= 4

    def decSP(self):
        """Decrements the contents of SP."""
        self.sp.ld((self.sp.val() - 1) & 0xffff)
        self.m += 1
        self.t += 4

    def incA(self):
        """Increments the contents of A."""
        self._incR(self.a)

    def decA(self):
        """Decrements the contents of A."""
        self._decR(self.a)

    def ldAn(self, a):
        """Loads a byte into A."""
        self._ldRn(self.a, a)

    def ccf(self):
        """Complements the C flag."""
        self.f.h.reset()
        self.f.n.reset()
        self.f.c.setTo(not self.f.c.val())
        self.m += 1
        self.t += 4

    def ldBB(self):
        """Loads the contents of B into B."""
        self._ldRR(self.b, self.b)

    def ldBC(self):
        """Loads the contents of C into B."""
        self._ldRR(self.b, self.c)

    def ldBD(self):
        """Loads the contents of D into B."""
        self._ldRR(self.b, self.d)

    def ldBE(self):
        """Loads the contents of E into B."""
        self._ldRR(self.b, self.e)

    def ldBH(self):
        """Loads the contents of H into B."""
        self._ldRR(self.b, self.h)

    def ldBL(self):
        """Loads the contents of L into B."""
        self._ldRR(self.b, self.l)

    def ldBMemHL(self):
        """Loads the value at memory address in HL into B."""
        self._ldRMemHL(self.b)

    def ldBA(self):
        """Loads the contents of A into B."""
        self._ldRR(self.b, self.a)

    def ldCB(self):
        """Loads the contents of B into C."""
        self._ldRR(self.c, self.b)

    def ldCC(self):
        """Loads the contents of C into C."""
        self._ldRR(self.c, self.c)

    def ldCD(self):
        """Loads the contents of D into C."""
        self._ldRR(self.c, self.d)

    def ldCE(self):
        """Loads the contents of E into C."""
        self._ldRR(self.c, self.e)

    def ldCH(self):
        """Loads the contents of H into C."""
        self._ldRR(self.c, self.h)

    def ldCL(self):
        """Loads the contents of L into C."""
        self._ldRR(self.c, self.l)

    def ldCMemHL(self):
        """Loads the value at memory address in HL into C."""
        self._ldRMemHL(self.c)

    def ldCA(self):
        """Loads the contents of A into C."""
        self._ldRR(self.c, self.a)

    def ldDB(self):
        """Loads the contents of B into D."""
        self._ldRR(self.d, self.b)

    def ldDC(self):
        """Loads the contents of C into D."""
        self._ldRR(self.d, self.c)

    def ldDD(self):
        """Loads the contents of D into D."""
        self._ldRR(self.d, self.d)

    def ldDE(self):
        """Loads the contents of E into D."""
        self._ldRR(self.d, self.e)

    def ldDH(self):
        """Loads the contents of H into D."""
        self._ldRR(self.d, self.h)

    def ldDL(self):
        """Loads the contents of L into D."""
        self._ldRR(self.d, self.l)

    def ldDMemHL(self):
        """Loads the value at memory address in HL into D."""
        self._ldRMemHL(self.d)

    def ldDA(self):
        """Loads the contents of A into D."""
        self._ldRR(self.d, self.a)

    def ldEB(self):
        """Loads the contents of B into E."""
        self._ldRR(self.e, self.b)

    def ldEC(self):
        """Loads the contents of C into E."""
        self._ldRR(self.e, self.c)

    def ldED(self):
        """Loads the contents of D into E."""
        self._ldRR(self.e, self.d)

    def ldEE(self):
        """Loads the contents of E into E."""
        self._ldRR(self.e, self.e)

    def ldEH(self):
        """Loads the contents of H into E."""
        self._ldRR(self.e, self.h)

    def ldEL(self):
        """Loads the contents of L into E."""
        self._ldRR(self.e, self.l)

    def ldEMemHL(self):
        """Loads the value at memory address in HL into E."""
        self._ldRMemHL(self.e)

    def ldEA(self):
        """Loads the contents of A into E."""
        self._ldRR(self.e, self.a)

    def ldHB(self):
        """Loads the contents of B into H."""
        self._ldRR(self.h, self.b)

    def ldHC(self):
        """Loads the contents of C into H."""
        self._ldRR(self.h, self.c)

    def ldHD(self):
        """Loads the contents of D into H."""
        self._ldRR(self.h, self.d)

    def ldHE(self):
        """Loads the contents of E into H."""
        self._ldRR(self.h, self.e)

    def ldHH(self):
        """Loads the contents of H into H."""
        self._ldRR(self.h, self.h)

    def ldHL(self):
        """Loads the contents of L into H."""
        self._ldRR(self.h, self.l)

    def ldHMemHL(self):
        """Loads the value at memory address in HL into H."""
        self._ldRMemHL(self.h)

    def ldHA(self):
        """Loads the contents of A into H."""
        self._ldRR(self.h, self.a)

    def ldLB(self):
        """Loads the contents of B into L."""
        self._ldRR(self.l, self.b)

    def ldLC(self):
        """Loads the contents of C into L."""
        self._ldRR(self.l, self.c)

    def ldLD(self):
        """Loads the contents of D into L."""
        self._ldRR(self.l, self.d)

    def ldLE(self):
        """Loads the contents of E into L."""
        self._ldRR(self.l, self.e)

    def ldLH(self):
        """Loads the contents of H into L."""
        self._ldRR(self.l, self.h)

    def ldLL(self):
        """Loads the contents of L into L."""
        self._ldRR(self.l, self.l)

    def ldLMemHL(self):
        """Loads the value at memory address in HL into L."""
        self._ldRMemHL(self.l)

    def ldLA(self):
        """Loads the contents of A into L."""
        self._ldRR(self.l, self.a)

    def ldMemHLB(self):
        """Loads B into the memory address in HL."""
        self._ldMemHLR(self.b)

    def ldMemHLC(self):
        """Loads C into the memory address in HL."""
        self._ldMemHLR(self.c)

    def ldMemHLD(self):
        """Loads D into the memory address in HL."""
        self._ldMemHLR(self.d)

    def ldMemHLE(self):
        """Loads E into the memory address in HL."""
        self._ldMemHLR(self.e)

    def ldMemHLH(self):
        """Loads H into the memory address in HL."""
        self._ldMemHLR(self.h)

    def ldMemHLL(self):
        """Loads L into the memory address in HL."""
        self._ldMemHLR(self.l)

    def halt(self):
        raise NotImplementedError("'HALT' has not been implemented")

    def ldMemHLA(self):
        """Loads A into the memory address in HL."""
        self._ldMemHLR(self.a)

    def ldAB(self):
        """Loads the contents of B into A."""
        self._ldRR(self.a, self.b)

    def ldAC(self):
        """Loads the contents of C into A."""
        self._ldRR(self.a, self.c)

    def ldAD(self):
        """Loads the contents of D into A."""
        self._ldRR(self.a, self.d)

    def ldAE(self):
        """Loads the contents of E into A."""
        self._ldRR(self.a, self.e)

    def ldAH(self):
        """Loads the contents of H into A."""
        self._ldRR(self.a, self.h)

    def ldAL(self):
        """Loads the contents of L into A."""
        self._ldRR(self.a, self.l)

    def ldAMemHL(self):
        """Loads the value at memory address in HL into A."""
        self._ldRMemHL(self.a)

    def ldAA(self):
        """Loads the contents of A into A."""
        self._ldRR(self.a, self.a)

    def addAB(self):
        """Adds A and B and stores the result in A."""
        self._addAR(self.b)

    def addAC(self):
        """Adds A and C and stores the result in A."""
        self._addAR(self.c)

    def addAD(self):
        """Adds A and D and stores the result in A."""
        self._addAR(self.d)

    def addAE(self):
        """Adds A and E and stores the result in A."""
        self._addAR(self.e)

    def addAH(self):
        """Adds A and H and stores the result in A."""
        self._addAR(self.h)

    def addAL(self):
        """Adds A and L and stores the result in A."""
        self._addAR(self.l)

    def addAMemHL(self):
        """Adds A and value stored at address in HL and stores result in A."""
        a = self.a.val()
        v = self._mem.get8(self._hl())
        self.f.n.reset()
        self.f.h.setTo((a & 0xf) + (v & 0xf) > 0xf)
        self.f.c.setTo(a + v > 0xff)
        self.a.ld((a + v) & 0xff)
        self._chkZ(self.a)
        self.m += 2
        self.t += 8

    def addAA(self):
        """Adds A, C and A and stores the result in A."""
        self._addAR(self.a)

    def adcAB(self):
        """Adds A, C and B and stores the result in A."""
        self._adcAR(self.b)

    def adcAC(self):
        """Adds A, C and C and stores the result in A."""
        self._adcAR(self.c)

    def adcAD(self):
        """Adds A, C and D and stores the result in A."""
        self._adcAR(self.d)

    def adcAE(self):
        """Adds A, C and E and stores the result in A."""
        self._adcAR(self.e)

    def adcAH(self):
        """Adds A, C and H and stores the result in A."""
        self._adcAR(self.h)

    def adcAL(self):
        """Adds A, C and L and stores the result in A."""
        self._adcAR(self.l)

    def adcAMemHL(self):
        """Adds A, C and value stored at address in HL, stores result in A."""
        a = self.a.val()
        v = self._mem.get8(self._hl())
        c = 1 if self.f.c.val() else 0
        self.f.n.reset()
        self.f.h.setTo((a & 0xf) + (v & 0xf) + c > 0xf)
        self.f.c.setTo(a + v + c > 0xff)
        self.a.ld((a + v + c) & 0xff)
        self._chkZ(self.a)
        self.m += 2
        self.t += 8

    def adcAA(self):
        """Adds A, C and A and stores the result in A."""
        self._adcAR(self.a)

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

    def _ldRR(self, dstReg, srcReg):
        self._ldRn(dstReg, srcReg.val())

    def _ldRMemHL(self, reg):
        self._ldRn(reg, self._mem.get8(self._hl()))
        self.m += 1
        self.t += 4

    def _ldMemHLR(self, reg):
        self._mem.set8(self._hl(), reg.val())
        self.m += 2
        self.t += 8

    def _addAR(self, reg):
        a = self.a.val()
        r = reg.val()
        self.f.n.reset()
        self.f.h.setTo((a & 0xf) + (r & 0xf) > 0xf)
        self.f.c.setTo(a + r > 0xff)
        self.a.ld((a + r) & 0xff)
        self._chkZ(self.a)
        self.m += 1
        self.t += 4

    def _adcAR(self, reg):
        a = self.a.val()
        r = reg.val()
        c = 1 if self.f.c.val() else 0
        self.f.n.reset()
        self.f.h.setTo((a & 0xf) + (r & 0xf) + c > 0xf)
        self.f.c.setTo(a + r + c > 0xff)
        self.a.ld((a + r + c) & 0xff)
        self._chkZ(self.a)
        self.m += 1
        self.t += 4

    def _chkZ(self, reg):
        self.f.z.setTo(reg.val() == 0)

    def _hl(self):
        return (self.h.val() << 8) + self.l.val()
