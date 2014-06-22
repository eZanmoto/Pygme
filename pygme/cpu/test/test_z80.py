# Copyright 2014 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu.z80 import Z80

class MockMem:

    PC_OFFSET = 0x0100

    def __init__(self, opcodes):
        self._opcodes = opcodes
        self.last_write = None

    def get8(self, addr):
        return self._opcodes[addr - self.PC_OFFSET]

    def set8(self, addr, val):
        self.last_write = (addr, val)


class MockGPU:

    def update(self, ticks):
        pass


class TestZ80(unittest.TestCase):

    def test_WithDefaultCPU_NOP_DoesntChangeA(self):
        # Arrange
        cpu = Z80(MockMem([0x00]), MockGPU())
        a = cpu.a()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.a(), a)

    def test_WithDefaultCPU_LDBC0x00A5_Loads0xA5IntoB(self):
        # Arrange
        b = 0xA5
        cpu = Z80(MockMem([0x01, 0x00, b]), MockGPU())
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), b)

    def test_WithDefaultCPU_LDBC0xA500_Loads0xA5IntoC(self):
        # Arrange
        c = 0xA5
        cpu = Z80(MockMem([0x01, c, 0x00]), MockGPU())
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.c(), c)

    def test_WithDefaultCPU_LDBC0xA5A5_DoesntAffectFlags(self):
        self._test_Instr_DoesntAffectFlags([0x01, 0xA5, 0xA5])

    def _test_Instr_DoesntAffectFlags(self, mem):
        # Arrange
        cpu = Z80(MockMem(mem), MockGPU())
        z = cpu.zero()
        n = cpu.neg()
        h = cpu.half_carry()
        c = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.zero(), z)
        self.assertEquals(cpu.neg(), n)
        self.assertEquals(cpu.half_carry(), h)
        self.assertEquals(cpu.carry(), c)

    def test_WithDefaultCPU_LDMemBCA_LoadsAIntoMemBC(self):
        # Arrange
        mem = MockMem([0x02])
        cpu = Z80(mem, MockGPU())
        # Act
        cpu.step()
        # Assert
        self.assertEquals(((cpu.b() << 8) + cpu.c(), cpu.a()), mem.last_write)


if __name__ == '__main__':
    unittest.main()
