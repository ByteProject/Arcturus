# test_bodyless_instance.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""An instance of a kind may leave its body out (EdwardianDuck's request,
2026-11-01): everything, name included, comes from the kind. An object
without a kind still needs a body, and the error says why."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _compile(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_compile(src)), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


GAME = (
    'game\n    title "G"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north nook1\n'
    'kind nook of room\n    name "Nook"\n    desc "A small nook."\n'
    'kind crate of thing\n    name block\n        show("crate")\n'
    '    words crate\n    desc "A wooden crate."\n'
    'thing c1 of crate in hall\n'
    'room nook1 of nook\n'
    'thing c2 of crate in nook1\n'
)


def test_a_bodyless_instance_takes_everything_from_its_kind():
    out = _run(GAME, ["x crate", "take crate", "i", "north", "x crate"])
    parts = out.split(">")[1:]
    assert "A wooden crate." in parts[0]
    assert "You take the crate with you." in parts[1]
    assert "a crate" in parts[2]
    assert "A small nook." in parts[3]                 # the bodyless room
    assert "Which do you mean" in parts[4] or "A wooden crate." in parts[4]


def test_the_last_declaration_may_be_bodyless():
    _compile(GAME + 'thing c3 of crate in hall')         # no trailing newline


def test_an_object_without_a_kind_still_needs_a_body():
    with pytest.raises(ArcError, match="'c3' needs an indented body"):
        _compile(GAME + 'thing c3 in hall\n')
