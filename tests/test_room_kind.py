# test_room_kind.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""An instance of a room kind IS a room, however it was declared (a field
report from a Dialog port): `thing parlor of lounge`, with lounge a kind
OF ROOM, used to stay a thing by keyword, so spanning it was refused as
"not a room". The keyword is a reading aid; the kind chain is the truth:
such an instance now joins the room table, takes exits, serves as the
start room, and accepts spans."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start parlor\n'
    'kind lounge of room\n'
    '    desc "A comfortable room of the house."\n'
    # The reported shape: declared with `thing`, roomness by inheritance.
    'thing parlor of lounge\n    name "Parlor"\n    south study\n'
    'room study\n    name "Study"\n    desc "Shelves."\n    north parlor\n'
    'thing piano of supporter in parlor\n    name "piano"\n    words piano\n'
    '    fixed\n'
    # The span that triggered the report: spanning the kind-declared room.
    'thing river in study\n    name "river"\n    words river\n'
    '    desc "It runs the length of the house, somehow."\n'
    '    fixed\n    spans parlor\n'
)


def _run(cmds):
    story = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_room_kind_instance_is_a_room_everywhere():
    # Start room, kind-inherited desc, exits both ways, and the span.
    out = _run(["examine river", "south", "north", "examine river"])
    assert "Parlor" in out
    assert "A comfortable room of the house." in out  # the kind's desc
    assert "Shelves." in out                          # walked south
    assert out.count("It runs the length of the house") == 2  # span holds
