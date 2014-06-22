# Copyright 2014 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu.z80 import Z80

class MockMem:

    PC_OFFSET = 0x0100

    def __init__(self, opcodes):
        self._opcodes = opcodes

    def get8(self, addr):
        return self._opcodes[addr - self.PC_OFFSET]


class MockGPU:

    def update(self, ticks):
        pass


class TestZ80(unittest.TestCase):

    def test_WithDefaultCPU_NOP_DoesntChangeA(self):
        # Arrange
        cpu = Z80(MockMem([0x00]), MockGPU())
        a = cpu.a.val()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.a.val(), a)

    def test_WithDefaultCPU_LDBC0x00A5_Loads0xA5IntoB(self):
        # Arrange
        b = 0xA5
        cpu = Z80(MockMem([0x01, 0x00, b]), MockGPU())
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b.val(), b)

    def test_WithDefaultCPU_LDBC0xA500_Loads0xA5IntoC(self):
        # Arrange
        c = 0xA5
        cpu = Z80(MockMem([0x01, c, 0x00]), MockGPU())
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.c.val(), c)

    def test_WithDefaultCPU_LDBC0xA5A5_DoesntAffectFlags(self):
        self._test_Instr_DoesntAffectFlags([0x01, 0xa5, 0xA5])

    def _test_Instr_DoesntAffectFlags(self, mem):
        # Arrange
        cpu = Z80(MockMem(mem), MockGPU())
        z = cpu.f.z.val()
        n = cpu.f.n.val()
        h = cpu.f.h.val()
        c = cpu.f.c.val()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.f.z.val(), z)
        self.assertEquals(cpu.f.n.val(), n)
        self.assertEquals(cpu.f.h.val(), h)
        self.assertEquals(cpu.f.c.val(), c)


if __name__ == '__main__':
    unittest.main()
