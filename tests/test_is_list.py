# test_is_list.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The is-list (a field habit from Inform6): `if way is aft or north`
distributes to `way is aft or way is north`, and the negated form to
NEITHER (`way is not aft and way is not north`). Only a bare compile-time
value distributes; before this sugar such an operand was an always-true
constant, never working code, so no legal program changes meaning: a flag
or global as an operand keeps being the condition it always was, and a
bare value with no comparison to its left still gets the teaching note."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hub\n'
    'flag alarm\n'
    'room hub\n    name "Hub"\n    desc "Doors everywhere."\n'
    '    north a\n    south b\n    east c\n'
    'room a\n    name "A"\n    desc "A."\n    south hub\n'
    'room b\n    name "B"\n    desc "B."\n    north hub\n'
    'room c\n    name "C"\n    desc "C."\n    west hub\n'
    'verb "ring"\n    ring\n'
    'on ring\n    change alarm to true\n    say "Rung."\n'
    'on go\n'
    '    if way is north or south\n'
    '        say "AXIS"\n'
    '    if way is not north or south or east\n'
    '        say "ELSEWHERE"\n'
    '    if way is east or alarm\n'
    '        say "MIX"\n'
    '    continue\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))), io).run(
            max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_is_list_distributes():
    out = _run(["north", "south"])
    assert out.count("AXIS") == 2
    assert "ELSEWHERE" not in out
    assert "MIX" not in out


def test_negated_is_list_means_neither():
    out = _run(["east", "west"])
    # east: not in the neither-list; west: in it.
    assert out.count("ELSEWHERE") == 1
    assert out.count("MIX") == 1     # east fired the mix's comparison side


def test_flag_operand_keeps_its_meaning():
    out = _run(["ring", "north"])
    # With the alarm flag true, the mix fires even off the east axis.
    assert "MIX" in out


def test_undistributable_bare_value_still_notes(capfd):
    src = ('game\n    title "T"\n    start r\n'
           'room r\n    name "R"\n    desc "D."\n'
           'thing key in r\n    name "key"\n    words key\n'
           'thing box in r\n    name "box"\n    words box\n'
           'on go\n    if noun or key\n        say "x"\n    continue\n')
    generate(analyze(cosmos.combined_program(parse(src))))
    err = capfd.readouterr().err
    assert "stands alone in an 'or' condition" in err
