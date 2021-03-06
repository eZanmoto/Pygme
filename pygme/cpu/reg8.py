# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.


class Reg8:

    def __init__(self, name, val):
        self._name = name
        self.ld(val)

    def name(self):
        return self._name

    def val(self):
        return self._val

    def ld(self, n):
        if n < 0 or n > 0xff:
            raise ValueError("Cannot assign 0x%x(%d) to 8-bit register '%s'" %
                             (n, n, self.name()))
        self._val = n
