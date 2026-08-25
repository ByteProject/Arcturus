# test_boarding_matrix.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The complete boarding-and-leaving idiom matrix, pinned after the field
report that EXIT ENGINE and LEAVE ENGINE answered "You lost me after that."
(the exit verb never declared the noun line its own handler documented).
Every phrasing of getting in and out of an enterable is here, so the next
gap in this family fails a test instead of reaching an adopter."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start station\n'
    'room station\n    name "Station"\n    desc "A platform."\n'
    'thing engine of container in station\n'
    '    name "engine"\n    words engine, locomotive\n'
    '    open\n    scenery\n'
    'thing bench of supporter in station\n'
    '    name "bench"\n    words bench\n    scenery\n'
)

IN_PHRASES = ["enter engine", "get in engine", "get into engine",
              "go in engine", "board engine"]
OUT_PHRASES = ["exit", "leave", "exit engine", "leave engine",
               "get out", "get out of engine", "stand"]
ON_PHRASES = ["sit on bench", "get on bench", "stand on bench",
              "enter bench"]
OFF_PHRASES = ["get off bench", "stand", "exit", "leave", "exit bench"]

_STORY = {}


def _run(cmds):
    if "s" not in _STORY:
        _STORY["s"] = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY["s"]), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


@pytest.mark.parametrize("enter", IN_PHRASES)
@pytest.mark.parametrize("leave", OUT_PHRASES)
def test_every_way_in_matches_every_way_out(enter, leave):
    out = _run([enter, leave])
    assert "get in" in out or "get into" in out or "engine" in out
    at = out.index(">" + leave)
    tail = out[at:]
    assert "lost me" not in tail, (enter, leave, tail)
    assert "You get out of the engine." in tail or "get off" in tail, (
        enter, leave, tail)


@pytest.mark.parametrize("on", ON_PHRASES)
@pytest.mark.parametrize("off", OFF_PHRASES)
def test_every_way_on_matches_every_way_off(on, off):
    out = _run([on, off])
    at = out.index(">" + off)
    tail = out[at:]
    assert "lost me" not in tail, (on, off, tail)
    assert ("get off" in tail or "get out" in tail
            or "get up" in tail), (on, off, tail)
