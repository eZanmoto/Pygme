# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

OFFSET_FROM_RAM = 0x2000

START_ADDR = 0xe000
END_ADDR = 0xfdff


class EchoMem:
    """Handles reading and writing from echoed memory."""

    def __init__(self, mem):
        self._mem = mem

    def set8(self, addr, val):
        self._mem.set8(addr, val)

    def get8(self, addr):
        addr_ = addr
        if START_ADDR <= addr_ <= END_ADDR:
            addr_ -= OFFSET_FROM_RAM
        return self._mem.get8(addr_)
