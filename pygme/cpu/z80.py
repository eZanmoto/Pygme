# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class Z80:

    def __init__(self):
        self.b = 0
        self.c = 0
        self.m = 0
        self.t = 0
        self.instr = [(self.nop,0),
                      (self.ldBCnn,2),
                     ]

    def nop(self):
        """The CPU performs no operation during this machine cycle."""
        self.m += 1
        self.t += 4

    def ldBCnn(self, n, m):
        """Loads a byte into B and a byte into C."""
        if n < 0 or n >= 0xff:
            raise ValueError
        if m < 0 or m >= 0xff:
            raise ValueError
        self.b = n
        self.c = m
        self.m += 2
        self.t += 10
