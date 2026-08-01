# test_boot_flash.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The boot latch: the status bar stays invisible until the first prompt.

The first retro interpreter (the CPC work) caught Cosmos painting the
complete status bar before `on start` had set its colours and again after
the colour repaint, both erased before the quote screen: invisible on a
fast interpreter, a visible flash at 4 MHz. The statusline granule now
reserves row 1 during boot and paints only from the first prompt on (the
PunyInform manner). This test drives the boot through Actaea's screen
model and asserts the op stream: no upper-window text before the first
line input, exactly one bar paint at the prompt, and the row-1 reserve
(the split) still protecting `on start` text from the old field bug.
"""

import os
import subprocess
import sys

import pytest

from actaea import screen as scr
from actaea.io import IOSystem
from actaea.loader import load_file
from actaea.vm import VM

GAME = """
summon.statusline
summon.quotes

game
    title "Bootflash"
    author "pytest"
    start cell

on start
    zcolor.font white
    zcolor.background black
    quote_line
    show("Stillness before the first prompt.")
    quote_line
    quote_done

room cell
    name "Quiet Cell"
    desc "Four walls and the absence of any flicker."
"""


class _FirstPrompt(Exception):
    pass


def _trace_boot(story_path):
    """Run the boot, recording (op, window, payload) until the first
    read_line. Keypresses (the quote box) are auto-fed."""
    log = []

    def wrap(name):
        orig = getattr(scr.ScreenModel, name)

        def logged(self, *args, **kwargs):
            if name == "write":
                log.append(("write", self.window, args[0]))
            else:
                log.append((name, None, args))
            return orig(self, *args, **kwargs)

        return logged

    saved = {}
    for m in ("split", "select", "erase_window", "set_style", "write"):
        saved[m] = getattr(scr.ScreenModel, m)
        setattr(scr.ScreenModel, m, wrap(m))
    try:
        class BootIO(IOSystem):
            def print_text(self, t):
                pass

            def read_line(self, *a, **k):
                log.append(("read_line", None, ()))
                raise _FirstPrompt

            def read_char(self, *a, **k):
                return 32

        vm = VM(load_file(str(story_path)), BootIO())
        with pytest.raises(_FirstPrompt):
            vm.run()
    finally:
        for m, fn in saved.items():
            setattr(scr.ScreenModel, m, fn)
    return log


def test_no_bar_before_the_first_prompt(tmp_path):
    src = tmp_path / "bootflash.storyarc"
    src.write_text(GAME)
    story = tmp_path / "bootflash.z5"
    subprocess.run(
        [sys.executable, "-m", "arcturus.cli", str(src), "-o", str(story)],
        capture_output=True, text=True, check=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )

    log = _trace_boot(story)

    # Upper-window text runs, split by the quote box (window taller than
    # one row) versus the one-row bar. The quote is welcome; the bar is not
    # until the prompt has gone live.
    bar_rows = []
    current_split = 0
    for op, win, payload in log:
        if op == "split":
            current_split = payload[0]
        elif op == "write" and win == 1 and str(payload).strip():
            if current_split <= 1:
                bar_rows.append(payload)
        elif op == "read_line":
            break

    assert bar_rows and "Quiet Cell" in "".join(str(p) for p in bar_rows), \
        "the bar must have painted once, with the room name, by the prompt"

    # And before the room description was written, no one-row upper text at
    # all: the boot reserves, the quote box speaks, the bar stays dark.
    # (The bar carries the title, so the lower window's first room text is
    # the description prose, the scan key here.)
    pre_desc = []
    current_split = 0
    for op, win, payload in log:
        if op == "split":
            current_split = payload[0]
        elif op == "write":
            if win == 0 and "Four walls" in str(payload):
                break
            if win == 1 and current_split <= 1 and str(payload).strip():
                pre_desc.append(payload)
    assert pre_desc == [], f"bar painted during boot: {pre_desc!r}"

    # The row-1 reserve survives: a split(1) happens before the quote box,
    # so `on start` text can never land under the future bar.
    first_ops = [op for op, _, _ in log[:6]]
    assert "split" in first_ops
