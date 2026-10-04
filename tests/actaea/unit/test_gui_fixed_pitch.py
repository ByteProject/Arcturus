# test_gui_fixed_pitch.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The GUI's fixed-pitch decision (auraes's report, 2026-09-28: Inform's
font off ignored). Three doors, all the Standard's: the FIXED text style,
Flags 2 bit 1 set by the game at run time, and font 4 chosen with
set_font. Tested on the method alone, no window: the GUI test that opens
one runs elsewhere, once."""

from types import SimpleNamespace

from actaea.gui.app import ActaeaApp as App
from actaea.screen import FIXED, ROMAN


class _Mem:
    def __init__(self, flags2):
        self._f = flags2

    def word(self, addr):
        assert addr == 0x10
        return self._f


def _stand_in(flags2=0, font=1):
    return SimpleNamespace(vm=SimpleNamespace(mem=_Mem(flags2), font=font))


def test_three_doors_to_fixed_pitch():
    f = App._fixed_now
    assert f(_stand_in(), ROMAN) is False
    assert f(_stand_in(), FIXED) is True                      # the style bit
    assert f(_stand_in(flags2=0x2), ROMAN) is True            # Flags 2 bit 1 (font off)
    assert f(_stand_in(flags2=0x1), ROMAN) is False           # bit 0 is transcription
    assert f(_stand_in(font=4), ROMAN) is True                # set_font 4
    assert f(_stand_in(font=1), ROMAN) is False
