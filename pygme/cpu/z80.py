# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class Flags:

    def __init__(self):
        self.z = False
        self.n = False
        self.c = False
        self.h = False

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
        self.a = 0
        self.b = 0
        self.c = 0
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
                     ]

    def nop(self):
        """The CPU performs no operation during this machine cycle."""
        self.m += 1
        self.t += 4

    def ldBCnn(self, b, c):
        """Loads a byte into B and a byte into C."""
        self.chkRegByte("B", b)
        self.chkRegByte("C", c)
        self.b = b
        self.c = c
        self.m += 3
        self.t += 12

    def ldMemBCA(self):
        """Loads the contents of A into the memory address specified by BC."""
        self._mem.set8((self.b << 8) + self.c, self.a)
        self.m += 2
        self.t += 8

    def incBC(self):
        """Increments the contents of BC."""
        self.c = (self.c + 1) & 0xff
        if self.c == 0:
            self.b = (self.b + 1) & 0xff
        self.m += 1
        self.t += 4

    def incB(self):
        """Increments the contents of B."""
        self.f.n = False
        self.f.h = self.b & 0xf == 0xf
        self.b = (self.b + 1) & 0xff
        self.chkZ(self.b)
        self.m += 1
        self.t += 4

    def decB(self):
        """Decrements the contents of B."""
        self.f.n = True
        self.f.h = self.b & 0xf != 0
        self.b = (self.b - 1) & 0xff
        self.chkZ(self.b)
        self.m += 1
        self.t += 4

    def ldBn(self, b):
        """Loads a byte into B."""
        self.chkRegByte("B", b)
        self.b = b
        self.m += 1
        self.t += 4

    def rlcA(self):
        """A is rotated left 1-bit position - bit 7 goes into C and bit 0."""
        bit7 = (self.a >> 7) & 1
        self.a = ((self.a << 1) & 0xff) | bit7
        self.chkZ(self.a)
        self.f.n = False
        self.f.h = False
        self.f.c = bit7
        self.m += 1
        self.t += 4

    def ldMemnnSP(self, n, m):
        raise NotImplementedError("'LD (nn), SP has not been implemented")

    def chkRegByte(self, r, b):
        if b < 0 or b > 0xff:
            raise ValueError("Value overflow for %s: 0x%x(%d)" % (r, b, b))

    def chkZ(self, v):
        self.f.z = v == 0
