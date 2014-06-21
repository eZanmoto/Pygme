# Copyright 2014 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.lcd.driver import lcdc as lcdc
from pygme.lcd.mode import LCDMode


class MockIOMemory:

    def __init__(self, mode=LCDMode.HBLANK, ly=0, oam_intr_enabled=False,
                 hblank_intr_enabled=False, vblank_intr_enabled=False,
                 lcdc_intr_enabled=False, lcd_is_on=False):
        self._mode = mode
        self._ly = ly
        self._oam_intr_enabled = oam_intr_enabled
        self._hblank_intr_enabled = hblank_intr_enabled
        self._vblank_intr_enabled = vblank_intr_enabled
        self.lcdc_intr_enabled = lcdc_intr_enabled
        self.vblank_intr_enabled = vblank_intr_enabled
        self._lcd_is_on = lcd_is_on

    def setLY(self, ly):
        self._ly = ly

    def getLY(self):
        return self._ly

    def getLCDMode(self):
        return self._mode

    def setLCDMode(self, mode):
        self._mode = mode

    def isHBLANKIntrEnabled(self):
        return self._hblank_intr_enabled

    def isVBLANKIntrEnabled(self):
        return self._vblank_intr_enabled

    def isOAMIntrEnabled(self):
        return self._oam_intr_enabled

    def setLCDCIntr(self):
        self.lcdc_intr_enabled = True

    def setVBLANKIntr(self):
        self.vblank_intr_enabled

    def getDisplayIsOn(self):
        return self._lcd_is_on

    def getBgAndWinIsOn(self):
        return True

    def getSCY(self):
        return 0

    def getSCX(self):
        return 0

    def getLCDCBackgroundYOffset(self):
        return 0

    def getLCDCBackgroundXOffset(self):
        return 0

    def get8(self, addr):
        return 0

    def getBgPalette(self):
        return 0


class MockLCD:

    def __init__(self):
        self.drawn_pixels = []

    def fill(self, colour):
        pass

    def update(self):
        pass

    def drawPixel(self, x, y, colour):
        self.drawn_pixels.append((x, y))


class TestLCDC(unittest.TestCase):

    def test_WhenInOAM_After79ticks_LCDInOAMMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.OAM_READ)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(79):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.OAM_READ)

    def test_WhenInOAM_After80ticks_LCDEntersVRAMMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.OAM_READ)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(80):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.VRAM_READ)

    def test_WhenLCDIsOff_IfLCDEntersVRAMMode_ScanlineIsNotDrawn(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.OAM_READ, lcd_is_on=False)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(80):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.VRAM_READ)

    def test_WhenLCDIsOn_IfLCDEntersVRAMMode_ScanlineIsDrawn(self):
        # Arrange
        y = 0
        lcd = MockLCD()
        driver = lcdc.LCDController(MockIOMemory(mode=LCDMode.OAM_READ,
                                                 ly=y,
                                                 lcd_is_on=True), lcd)
        # Act
        for i in xrange(80):
            driver.update(1)
        # Assert
        self.assertTrue(all((x, y) in lcd.drawn_pixels for x in xrange(160)))

    def test_WhenInVRAM_After171ticks_LCDInVRAMMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VRAM_READ)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(171):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.VRAM_READ)

    def test_WhenInVRAM_After172ticks_LCDEntersHBLANKMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VRAM_READ)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(172):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.HBLANK)

    def test_WhenHBLANKIntrEnabled_IfLCDEntersHBLANKMode_LCDCIntrIsSet(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VRAM_READ, hblank_intr_enabled=True,
                           lcdc_intr_enabled=False)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(172):
            driver.update(1)
        # Assert
        self.assertTrue(mem.lcdc_intr_enabled)

    def test_WhenHBLANKIntrDisabled_IfLCDEntersHBLANKMode_LCDCIntrIsUnchanged(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VRAM_READ, hblank_intr_enabled=False,
                           lcdc_intr_enabled=False)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(172):
            driver.update(1)
        # Assert
        self.assertFalse(mem.lcdc_intr_enabled)

    def test_WhenLYIs0_IfLCDEntersHBLANKMode_LCDCIs1(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VRAM_READ, ly=0)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(172):
            driver.update(1)
        # Assert
        self.assertEqual(mem.getLY(), 1)

    def test_WhenInHBLANK_After203ticks_LCDInHBLANKMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VRAM_READ)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(203):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.HBLANK)

    def test_WhenInHBLANKAndLYIs0_After204ticks_LCDEntersOAMMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.HBLANK, ly=0)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(204):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.OAM_READ)

    def test_WhenOAMIntrEnabled_IfLCDEntersOAMMode_LCDCIntrIsSet(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.HBLANK, ly=0, oam_intr_enabled=True,
                           lcdc_intr_enabled=False)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(204):
            driver.update(1)
        # Assert
        self.assertTrue(mem.lcdc_intr_enabled)

    def test_WhenOAMIntrDisabled_IfLCDEntersOAMMode_LCDCIntrIsUnchanged(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.HBLANK, ly=0, oam_intr_enabled=False,
                           lcdc_intr_enabled=False)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(204):
            driver.update(1)
        # Assert
        self.assertFalse(mem.lcdc_intr_enabled)

    def test_WhenInHBLANKAndLYIs143_After204ticks_LCDEntersOAMMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.HBLANK, ly=143)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(204):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.OAM_READ)

    def test_WhenInHBLANKAndLYIs144_After204ticks_LCDEntersVBLANKMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.HBLANK, ly=144)
        driver = lcdc.LCDController(mem, MockLCD())
        # Act
        for i in xrange(204):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.VBLANK)

    def test_WhenInVBLANK_After4559ticks_LCDInVBLANKMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VBLANK, ly=144)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(4559):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.VBLANK)

    def test_WhenInVBLANK_After4560ticks_LCDEntersOAMMode(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VBLANK, ly=144)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(4560):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLCDMode(), LCDMode.OAM_READ)

    def test_WhenInVBLANK_After4560ticks_LYIs0(self):
        # Arrange
        mem = MockIOMemory(mode=LCDMode.VBLANK, ly=144)
        driver = lcdc.LCDController(mem, None)
        # Act
        for i in xrange(4560):
            driver.update(1)
        # Assert
        self.assertEquals(mem.getLY(), 0)
