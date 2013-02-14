# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.memory import array, echomem

class TestEchoMem(unittest.TestCase):
    """Tests for EchoMem class."""

    def setUp(self):
        self._mem = echomem.EchoMem(array.Array(1 << 16))

    def test_set8_inMainRAM_isCopiedToEcho(self):
        for addr in [echomem.START_ADDR, echomem.END_ADDR]:
            addr -= echomem.OFFSET_FROM_RAM
            for val in [0x00, 0x5a, 0xa5, 0xff]:
                self._mem.set8(addr, val)
                self._expect8(addr, val)
                self._expect8(addr + echomem.OFFSET_FROM_RAM, val)

    def test_set8_inEcho_isCopiedToMainRAM(self):
        for addr in [echomem.START_ADDR, echomem.END_ADDR]:
            for val in [0x00, 0x5a, 0xa5, 0xff]:
                self._mem.set8(addr, val)
                self._expect8(addr, val)
                self._expect8(addr - echomem.OFFSET_FROM_RAM, val)

    def _expect8(self, addr, v):
        b = self._mem.get8(addr)
        self.assertEquals(b, v, "Expected 0x%02x(%d), got 0x%02x(%d) at 0x%x"
            % (v, v, b, b, addr))

    def tearDown(self):
        self._mem = None


if __name__ == '__main__':
    unittest.main()
