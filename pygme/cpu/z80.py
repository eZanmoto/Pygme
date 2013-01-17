# Copyright 2013 Sean Kelleher. All rights reserved.

class Z80:

    def __init__(self):
        self.m = 0
        self.t = 0
        self.instr = [self.nop,
                     ]

    def nop(self):
        self.m += 1
        self.t += 4
