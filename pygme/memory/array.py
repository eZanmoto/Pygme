# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class Array:

    def __init__(self, size):
        self._mem = [0 for _ in range(0, size)]

    def get8(self, addr):
        self._chkAddr(addr)
        return self._mem[addr]

    def set8(self, addr, val):
        self._chkAddr(addr)
        if val < 0 or val > 0xff:
            raise ValueError("Expected 8-bit value, got 0x%04x(%d)"
                % (val, val))
        self._mem[addr] = val

    def size(self):
        return len(self._mem)

    def _chkAddr(self, addr):
        if addr < 0 or addr >= self.size():
            raise IndexError( "Address (0x%x) is out of range [0x0-0x%x]"
                % (addr, self.size() - 1))
