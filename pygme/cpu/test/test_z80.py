# Copyright 2014 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.cpu.z80 import Z80

class MockMem:

    PC_OFFSET = 0x0100

    def __init__(self, opcodes):
        self._bytes = {}
        for i in xrange(len(opcodes)):
            self._bytes[self.PC_OFFSET+i] = opcodes[i]

    def get8(self, addr):
        return self._bytes[addr]

    def set8(self, addr, val):
        self._bytes[addr] = val


class MockGPU:

    def update(self, ticks):
        pass


class TestZ80(unittest.TestCase):

    def test_WithDefaultCPU_NOP_DoesntChangeA(self):
        # Arrange
        cpu = Z80(MockMem([0x00]), MockGPU())
        a = cpu.a()
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.a(), a)
        self.assertFlagsEqual(cpu, f)

    def _flags(self, cpu):
        return (cpu.zero(), cpu.neg(), cpu.half_carry(), cpu.carry())

    def assertFlagsEqual(self, cpu, f=None, z=0, n=0, h=0, c=0):
        if f:
            z, n, h, c = f
        self.assertEquals(cpu.zero(), z)
        self.assertEquals(cpu.neg(), n)
        self.assertEquals(cpu.half_carry(), h)
        self.assertEquals(cpu.carry(), c)

    def test_WithDefaultCPU_LDBC0x00A5_Loads0xA5IntoB(self):
        # Arrange
        b = 0xA5
        cpu = Z80(MockMem([0x01, 0x00, b]), MockGPU())
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), b)
        self.assertFlagsEqual(cpu, f)

    def test_WithDefaultCPU_LDBC0xA500_Loads0xA5IntoC(self):
        # Arrange
        c = 0xA5
        cpu = Z80(MockMem([0x01, c, 0x00]), MockGPU())
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.c(), c)
        self.assertFlagsEqual(cpu, f)

    def test_WithDefaultCPU_LDMemBCA_LoadsAIntoMemBC(self):
        # Arrange
        mem = MockMem([0x02])
        cpu = Z80(mem, MockGPU())
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(mem._bytes[cpu.bc()], cpu.a())
        self.assertFlagsEqual(cpu, f)

    def test_With0x0000InBC_AfterIncBC_0x0001InBC(self):
        # Arrange
        mem = MockMem([0x03])
        cpu = Z80(mem, MockGPU())
        cpu.bc(0x0000)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.bc(), 0x0001)
        self.assertFlagsEqual(cpu, f)

    def test_With0x00ffInBC_AfterIncBC_0x0100InBC(self):
        # Arrange
        mem = MockMem([0x03])
        cpu = Z80(mem, MockGPU())
        cpu.bc(0x00ff)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.bc(), 0x0100)
        self.assertFlagsEqual(cpu, f)

    def test_With0xffffInBC_AfterIncBC_0x0000InBC(self):
        # Arrange
        mem = MockMem([0x03])
        cpu = Z80(mem, MockGPU())
        cpu.bc(0xffff)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.bc(), 0x0000)
        self.assertFlagsEqual(cpu, f)

    def test_With0x00InB_AfterIncB(self):
        # Arrange
        mem = MockMem([0x04])
        cpu = Z80(mem, MockGPU())
        cpu.b(0x00)
        carry = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0x01)
        self.assertFlagsEqual(cpu, z=0, n=0, h=0, c=carry)

    def test_With0x0FInB_AfterIncB(self):
        # Arrange
        mem = MockMem([0x04])
        cpu = Z80(mem, MockGPU())
        cpu.b(0x0F)
        carry = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0x10)
        self.assertFlagsEqual(cpu, z=0, n=0, h=1, c=carry)

    def test_With0xFFInB_AfterIncB(self):
        # Arrange
        mem = MockMem([0x04])
        cpu = Z80(mem, MockGPU())
        cpu.b(0xFF)
        carry = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0x00)
        self.assertFlagsEqual(cpu, z=1, n=0, h=1, c=carry)

    def test_With0x00InB_AfterDecB(self):
        # Arrange
        mem = MockMem([0x05])
        cpu = Z80(mem, MockGPU())
        cpu.b(0x00)
        carry = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0xFF)
        self.assertFlagsEqual(cpu, z=0, n=1, h=1, c=carry)

    def test_With0x01InB_AfterDecB(self):
        # Arrange
        mem = MockMem([0x05])
        cpu = Z80(mem, MockGPU())
        cpu.b(0x01)
        carry = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0x00)
        self.assertFlagsEqual(cpu, z=1, n=1, h=0, c=carry)

    def test_With0x10InB_AfterDecB(self):
        # Arrange
        mem = MockMem([0x05])
        cpu = Z80(mem, MockGPU())
        cpu.b(0x10)
        carry = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0x0F)
        self.assertFlagsEqual(cpu, z=0, n=1, h=1, c=carry)

    def test_With0x00InB_AfterLDB0xA5_BIs0xA5(self):
        # Arrange
        cpu = Z80(MockMem([0x06, 0xA5]), MockGPU())
        cpu.b(0x00)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.b(), 0xA5)
        self.assertFlagsEqual(cpu, f)

    def test_WhenAIs0x85AndCarryIs0_AfterRLCA_AIs0x0A(self):
        # Arrange
        cpu = Z80(MockMem([0x07]), MockGPU())
        cpu.a(0x85)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.a(), 0x0B)
        self.assertFlagsEqual(cpu, z=0, n=0, h=0, c=1)

    def test_WhenSPIs0xFFF8_AfterLDMem0xC100SP_Mem0xC100Contains0xFFF8(self):
        # Arrange
        mem = MockMem([0x08, 0x00, 0xC1])
        cpu = Z80(mem, MockGPU())
        cpu.sp(0xFFF8)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(mem._bytes[0xC100], 0xF8)
        self.assertEquals(mem._bytes[0xC100], 0xF8)
        self.assertFlagsEqual(cpu, f)

    def test_WhenHLIs0x8A23AndBCIs0x0605_AfterADDHLBC_HLContains0x9028(self):
        # Arrange
        cpu = Z80(MockMem([0x09]), MockGPU())
        cpu.hl(0x8A23)
        cpu.bc(0x0605)
        z = cpu.zero()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.hl(), 0x9028)
        self.assertFlagsEqual(cpu, z=z, n=0, h=1, c=0)

    def test_IfMemBCIs0x2F_AfterLDAMemBC_AContains0x2F(self):
        # Arrange
        mem = MockMem([0x0A])
        cpu = Z80(mem, MockGPU())
        cpu.bc(0x1C00)
        mem.set8(cpu.bc(), 0x2F)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.a(), 0x2F)
        self.assertFlagsEqual(cpu, f)

    def test_IfBCIs0x235F_AfterDecBC_BCContains0x235E(self):
        # Arrange
        cpu = Z80(MockMem([0x0B]), MockGPU())
        cpu.bc(0x235F)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.bc(), 0x235E)
        self.assertFlagsEqual(cpu, f)

    def test_IfCIs0xFF_AfterINCC_CIs0x00(self):
        # Arrange
        cpu = Z80(MockMem([0x0C]), MockGPU())
        cpu.c(0xFF)
        c = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.c(), 0x00)
        self.assertFlagsEqual(cpu, z=1, n=0, h=1, c=c)

    def test_IfCIs0x01_AfterDECC_CIs0x00(self):
        # Arrange
        cpu = Z80(MockMem([0x0D]), MockGPU())
        cpu.c(0x01)
        c = cpu.carry()
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.c(), 0x00)
        self.assertFlagsEqual(cpu, z=1, n=1, h=0, c=c)

    def test_IfCIs0x00_AfterLDC0x24_CIs0x24(self):
        # Arrange
        cpu = Z80(MockMem([0x0E, 0x24]), MockGPU())
        cpu.c(0x00)
        f = self._flags(cpu)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.c(), 0x24)
        self.assertFlagsEqual(cpu, f)

    def test_IfAIs0x3BAndCarryIs0_AfterRRCA_AIs0x9D(self):
        # Arrange
        cpu = Z80(MockMem([0x0F]), MockGPU())
        cpu.a(0x3B)
        cpu.carry(0)
        # Act
        cpu.step()
        # Assert
        self.assertEquals(cpu.a(), 0x9D)
        self.assertFlagsEqual(cpu, z=0, n=0, h=0, c=1)


if __name__ == '__main__':
    unittest.main()
