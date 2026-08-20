# test_pager_matches_tk.py
# part of Actaea, the Arcturus reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Pager computes what Tk would measure. OPT-IN: run it with

    ACTAEA_TK_PARITY=1 python3 -m pytest tests/actaea/unit/test_pager_matches_tk.py

The window's [MORE] has to stop where the widget actually wraps, so the
pager's arithmetic is checked against tkinter itself: the same text goes into
a real Text widget at the same width and the display lines are counted with
Tk's own `count(..., "displaylines")`. The window is created withdrawn and
destroyed again, so nothing appears on screen.

It is off by default because live Tk measurement is not reliable inside the
ordinary suite: with several parallel workers each driving withdrawn windows,
the layout measured now and then belongs to a moment that has passed, and a
different case fails each run. Run serially by hand and it is exact; that is
how the wrapping was verified when it was written (six cases, no mismatch),
and how to re-verify it after any change to the wrapping."""

import os

import pytest

from actaea.gui.pager import Pager

tk = pytest.importorskip("tkinter")

pytestmark = pytest.mark.skipif(
    not os.environ.get("ACTAEA_TK_PARITY"),
    reason="live Tk measurement: opt in with ACTAEA_TK_PARITY=1, run serially",
)


@pytest.fixture
def root():
    # One window per case, created and destroyed: a shared root under
    # parallel workers measured a stale layout now and then.
    try:
        r = tk.Tk()
    except tk.TclError as exc:            # no display: nothing to compare with
        pytest.skip("no display for tkinter: %s" % exc)
    r.withdraw()
    yield r
    r.destroy()


CASES = [
    ("abcde fghij klmno pqrst uvwxy zabcd\n", 20),
    ("The gatehouse arch is a black mouth in a blacker wall, and the "
     "portcullis teeth above it have not been raised in living memory.\n", 40),
    ("x" * 25 + "\n", 10),                                  # broken at the margin
    ("aaaa bbbbbbbb\n", 10),                                # moved whole, wrapped
    ("Short.\n\nAnother paragraph that runs on a good deal further than one "
     "line of forty columns can hold.\n", 40),              # blank lines count
    ("A short one.\n", 80),
]


@pytest.mark.parametrize("text,width", CASES)
def test_the_pager_counts_the_lines_tk_would_draw(root, text, width):
    from tkinter import font as tkfont

    widget = tk.Text(root, wrap="word", font=tkfont.nametofont("TkFixedFont"),
                     width=width, padx=0, pady=0, borderwidth=0,
                     highlightthickness=0)
    widget.pack()
    root.update()
    widget.insert("end-1c", text)
    root.update()
    measured = widget.count("1.0", "end-1c", "displaylines")
    if isinstance(measured, tuple):
        measured = measured[0]
    widget.destroy()

    pager = Pager()
    pager.feed(text, width=width, room=999)
    assert pager.lines == measured
