# test_clear_screen.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""clear_screen and the screen furniture (the field report: a game that
clears before its intro lost the first line under the status bar). The
erase unsplits, so the lowering re-runs the screen_ready seam right after
it, and only when a granule actually claimed the seam: a bar-less game
carries no call. The opcode encodings asserted here: erase_window -1 is
ED 3F FF FF, call_vn is F9."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

ERASE_ALL = b"\xED\x3F\xFF\xFF"


def _img(extra):
    game = (
        'game\n    title "T"\n    banner false\n    start hall\n'
        + extra +
        'room hall\n    name "Hall"\n    desc "H."\n'
        "on start\n"
        "    clear_screen\n"
        '    say "FIRST LINE."\n'
    )
    return generate(analyze(cosmos.combined_program(parse(game))))


def _call_follows(img):
    at = img.index(ERASE_ALL)
    # After the erase: the par-pending reset, then (with a claimed seam)
    # call_vn blk_screen_ready. A short window is plenty.
    return b"\xF9" in img[at + 4:at + 16]


def test_clear_screen_reraises_the_bar():
    assert _call_follows(_img("summon.statusline\n"))


def test_clear_screen_stays_bare_without_a_seam_owner():
    img = _img("")
    assert ERASE_ALL in img
    assert not _call_follows(img)
