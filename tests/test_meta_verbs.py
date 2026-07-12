# test_meta_verbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`verb ... meta` (a field report from a Dialog port): the debug granule's
GONEAR fired an object's `on other` catch-all, running story code from a
testing verb. A meta verb's actions join the out-of-world band beside
score/save/quit: the dispatcher routes them straight to the free rules,
past every object and room handler, `on other` included. The debug
granule's five verbs are meta now, TRANSCRIPT joined the fixed band, and
the marker is open to authors (an ABOUT verb). A plain custom verb still
meets `on other`, as it should."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'summon.debug\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north attic\n'
    'room attic\n    name "Attic"\n    desc "Dust."\n    south hall\n'
    'thing idol in attic\n    name "jade idol"\n    words idol, jade\n'
    '    on other\n        say "TRAP! The idol reacts."\n        stop\n'
    'verb "about" meta\n    about\n'
    'verb "poke"\n    poke noun\n'
    'on about\n    say "A test game."\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_debug_verbs_skip_on_other():
    # GONEAR (warp) and PURLOIN (fetch) reach the idol without firing its
    # on other; the debug output appears instead.
    out = _run(["gonear idol", "purloin idol", "inspect idol", "transcript off"])
    assert "TRAP!" not in out
    assert "Attic" in out               # warp arrived
    assert "Fetched jade idol." in out  # fetch worked
    assert "jade idol" in out
    assert "No transcript is running." in out  # transcript is meta too


def test_author_meta_verb_skips_on_other():
    out = _run(["north", "about"])
    assert "A test game." in out
    assert "TRAP!" not in out


def test_plain_custom_verb_still_meets_on_other():
    out = _run(["north", "poke idol"])
    assert "TRAP! The idol reacts." in out
