# Copyright 2014 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import collections

from pygme.lcd.mode import LCDMode

class LCDController:

    SCREEN_WIDTH = 160
    SCREEN_HEIGHT = 144

    PALETTE = [0xddffddff, 0x446644ff, 0x99bb99ff, 0x002200ff]

    VRAM_START = 0x8000

    def __init__(self, mem, lcd):
        self._mem = mem
        self._lcd = lcd
        self._ticks = 0
        Mode = collections.namedtuple('Mode', ['duration', 'exit_func'])
        self._modes = {
            LCDMode.OAM_READ: Mode(80, self._exit_oam_read),
            LCDMode.VRAM_READ: Mode(172, self._exit_vram_read),
            LCDMode.HBLANK: Mode(204, self._exit_hblank),
            LCDMode.VBLANK: Mode(456, self._exit_vblank)
        }

    def update(self, ticks):
        self._ticks += ticks
        mode = self._modes[self._mem.getLCDMode()]
        if self._ticks >= mode.duration:
            self._ticks -= mode.duration
            self._mem.setLCDMode(mode.exit_func())

    def _exit_oam_read(self):
        if self._mem.getDisplayIsOn():
            self._draw_scanline()
        return LCDMode.VRAM_READ

    def _exit_vram_read(self):
        if self._mem.isHBLANKIntrEnabled():
            self._mem.setLCDCIntr()
        self._mem.setLY(self._mem.getLY() + 1)
        return LCDMode.HBLANK

    def _exit_hblank(self):
        if self._mem.getLY() == 144:
            self._mem.setVBLANKIntr()
            if self._mem.isVBLANKIntrEnabled():
                self._mem.setLCDCIntr()
            if not self._mem.getDisplayIsOn():
                self._lcd.fill(self.PALETTE[0b11])
            self._lcd.update()
            return LCDMode.VBLANK
        else:
            if self._mem.isOAMIntrEnabled():
                self._mem.setLCDCIntr()
            return LCDMode.OAM_READ

    def _exit_vblank(self):
        self._mem.setLY(self._mem.getLY() + 1)
        if self._mem.getLY() > 153:
            self._mem.setLY(0)
            return LCDMode.OAM_READ
        return LCDMode.VBLANK

    def _draw_scanline(self):
        if self._mem.getBgAndWinIsOn():
            self._draw_background()

    def _draw_background(self):
        y = (self._mem.getLY() + self._mem.getSCY()) & 0xFF
        map_line = 0x1800 + self._mem.getLCDCBackgroundYOffset() + ((y >> 3) << 5)
        for x in range(self.SCREEN_WIDTH):
            x_ = (x + self._mem.getSCX()) & 0xFF
            tile_bit = 7 - (x_ & 0b111)
            tile_no = self._mem.get8(self.VRAM_START + map_line + (x_ >> 3))
            if tile_no < 0x80:
                tile_no += self._mem.getLCDCBackgroundXOffset()
            pal_index = 0
            for i in xrange(2):
                pal_index = (pal_index << 1) + (
                    (self._mem.get8(self.VRAM_START + tile_no * 0x10 +
                                    (y & 0b111) * 2 + i) >> tile_bit) & 1
                )
            self._lcd.drawPixel(x, self._mem.getLY(),
                self.PALETTE[(self._mem.getBgPalette() >> pal_index * 2) & 0b11]
            )
