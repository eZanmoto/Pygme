# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class Z80:

    def __init__(self, mem):
        self.a = 0
        self.b = 0
        self.c = 0
        self.m = 0
        self.t = 0
        self._mem = mem
        self.instr = [(self.nop, 0),
                      (self.ldBCnn, 2),
                      (self.ldMemBCA, 0),
                      (self.incBC, 0),
                     ]

    def nop(self):
        """The CPU performs no operation during this machine cycle."""
        self.m += 1
        self.t += 4

    def ldBCnn(self, b, c):
        """Loads a byte into B and a byte into C."""
        if b < 0 or b > 0xff:
            raise ValueError("Value overflow for B: 0x%04x(%d)" % (b, b))
        if c < 0 or c > 0xff:
            raise ValueError("Value overflow for C: 0x%04x(%d)" % (c, c))
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
