# test_statusline_seat.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The status bar seats its row once and repaints it after (2026-08-20, from
two interpreter authors working on arc_image hosts: the bar re-issued its
split_window on every paint, once per turn forever, which is visible work on a
memory-mapped 8-bit screen).

The split is establishment, not painting. It belongs after something took the
row away: the conversations menu's taller window, the quote box, a full-screen
erase (which always comes back through screen_ready), or a restore that may
have reset the screen. Everything that can take it away says so through the
bar_unseated seam in loop.prelude, empty and free in a game with no bar.

These tests read the story's op stream rather than the screen, because that is
where the defect lived: the picture on a conformant interpreter was always
right, and the waste was invisible until someone counted the opcodes."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

ROOMS = (
    'room hall\n    name "The Hall"\n    desc "A long hall."\n    east garden\n'
    'room garden\n    name "The Garden"\n    desc "Grass."\n    west hall\n'
)
BAR = 'game\n    title "SL"\n    start hall\nsummon.statusline\n' + ROOMS
NO_BAR = 'game\n    title "SL"\n    start hall\n' + ROOMS


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _trace(story, cmds, pictures=False, save_dir=None):
    """Play `cmds` and return the screen-op stream as a list of events:
    "split(n)" for each split_window, "paint" for each completed bar paint
    (the upper window being left again), and "read" per input."""
    events = []
    ops = VM._ops
    keep = {k: ops[k] for k in ("split_window", "set_window", "read")}

    def split(self, ins):
        r = keep["split_window"](self, ins)
        # Read the height from the screen model, never from the operands: the
        # quote box passes its operand on the stack, and reading it here would
        # pop the value out from under the real handler.
        events.append("split(%d)" % self.screen.rows)
        return r

    def set_window(self, ins):
        was = self.screen.window
        r = keep["set_window"](self, ins)
        if was == 1 and self.screen.window == 0:
            events.append("paint")
        return r

    def read(self, ins):
        events.append("read")
        return keep["read"](self, ins)

    ops["split_window"], ops["set_window"], ops["read"] = split, set_window, read
    try:
        io = CaptureIO(script=list(cmds) + ["quit", "y"],
                       save_dir=str(save_dir) if save_dir else None)
        vm = VM(load(story), io)
        if pictures:
            # Claim picture support the way an arc_image host does: Flags 1,
            # bit 1, which is what Cosmos's pictures_available reads.
            vm.mem.set_byte(1, vm.mem.byte(1) | 2)
        try:
            vm.run(max_steps=20_000_000)
        except SystemExit:
            pass
    finally:
        ops.update(keep)
    return events


def _turns(events):
    """The event stream cut into turns at each input read; the head is boot."""
    out, cur = [], []
    for e in events:
        if e == "read":
            out.append(cur)
            cur = []
        else:
            cur.append(e)
    out.append(cur)
    return out


def test_the_bar_seats_its_row_once_and_repaints_after():
    boot, *turns = _turns(_trace(_build(BAR), ["east", "west", "look", "wait"]))
    # Boot establishes the row, once.
    assert boot.count("split(1)") == 1
    assert boot.count("paint") == 1
    # Every turn after that repaints without re-establishing anything.
    for turn in turns[:4]:
        assert "split(1)" not in turn, turn
        assert turn.count("paint") == 1, turn


def test_a_game_without_the_bar_never_splits():
    # The seam is empty and the calls emit nothing: no upper window is ever
    # created in a game that does not summon the granule.
    events = _trace(_build(NO_BAR), ["east", "look"])
    assert not [e for e in events if e.startswith("split")]
    assert "paint" not in events


MENU = (
    'game\n    title "M"\n    start tent\nsummon.statusline\nsummon.conversations\n'
    'room tent\n    name "A Tent"\n    desc "Canvas and candle smoke."\n'
    'thing esme of character in tent\n    name "Madame Esme"\n    named\n'
    '    words esme, madame\n'
    '    topic fortune "your fortune"\n'
    '        you "What do you see for me?"\n'
    '        reply "A long road."\n'
)


def test_the_menu_gives_the_row_back():
    # The menu takes the whole upper window (a taller split) and closing it
    # unsplits to nothing, so the next paint has to reserve row 1 again. The
    # menu reads keys rather than lines ("q" leaves it), so the whole visit
    # and the re-seat after it belong to the TALK turn.
    boot, talk, after = _turns(
        _trace(_build(MENU), ["talk to esme", "q", "look"]))[:3]
    splits = [e for e in talk if e.startswith("split")]
    assert "split(0)" in splits            # the menu closed the upper window
    assert splits[splits.index("split(0)") + 1] == "split(1)"   # bar re-seated
    assert talk[-1] == "paint"             # and painted, in that order
    # The turn after it is back to repaint-only.
    assert "split(1)" not in after, after


BOX = (
    'game\n    title "Q"\n    start pad\n    banner false\n'
    'summon.quotes\nsummon.statusline\n'
    'on start\n    quote(1, 12)\n    quote_line\n    show("Ad astra.")\n'
    '    quote_done\n'
    'room pad\n    name "The Pad"\n    desc "Concrete and steam."\n'
)


def test_the_quote_box_gives_the_row_back():
    # The box owns the upper window, and a full-screen erase closes it. The
    # bar is told nothing about the row quote_done puts back, so the first
    # paint after the box reserves it once more: one spare split in a rare
    # path, and no way for a box to leave the bar holding a row it lost.
    boot, first, second = _turns(
        _trace(_build(BOX), ["", "look", "wait"]))[:3]
    assert "split(1)" in boot
    assert boot.index("split(1)") < boot.index("paint")
    # The ordinary turns after it are back to repaint-only.
    assert "split(1)" not in first, first
    assert first.count("paint") == 1


def test_a_restore_reseats_the_row(tmp_path):
    # The restored memory remembers a screen the interpreter may have reset
    # under it. Whatever the save believed about the row, the first paint
    # after a restore reserves it again.
    story = _build(BAR)
    events = _trace(story, ["save", "g.qzl", "east", "restore", "g.qzl", "look"],
                    save_dir=tmp_path)
    # Segments: boot, SAVE, EAST, RESTORE, LOOK (the filename answers are read
    # through the interpreter's own prompt, not the read opcode, so they do
    # not start a segment of their own).
    turns = _turns(events)
    restore_turn = turns[3]
    assert "split(1)" in restore_turn, restore_turn
    assert restore_turn.index("split(1)") < restore_turn.index("paint")


IMAGES = (
    'game\n    title "I"\n    start hall\nconstant arc_mode = 12\n'
    'summon.statusline\n'
    'room hall\n    arc_image 8\n    name "The Hall"\n    desc "A long hall."\n'
    '    east garden\n'
    'room garden\n    arc_image 1\n    name "The Garden"\n    desc "Grass."\n'
    '    west hall\n'
)


def test_a_quiet_turn_costs_no_split_on_a_picture_interpreter():
    # The arc_image path re-seats the bar after the band moves (Stefan's rule:
    # the bar settles after the band), so a turn that changes the picture still
    # splits, and that one is deliberate. A turn that changes nothing must not:
    # that was the waste the interpreter authors saw on every single turn.
    turns = _turns(_trace(_build(IMAGES), ["east", "look", "wait"],
                          pictures=True))
    moved, quiet, still = turns[1], turns[2], turns[3]
    assert "split(1)" in moved                  # the band moved: re-seat
    assert "split(1)" not in quiet, quiet       # nothing moved: no split
    assert "split(1)" not in still, still
    assert quiet.count("paint") == 1
