# test_string_constants.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""String constants (a field request from a PunyInform port): a `constant`
holding a string stands for its text anywhere text stands, so one wording
is shared between a desc and a say (the reported case: `desc DESC_OFFICE`
used to type the property as object and collide program-wide). Identical
text is laid out once in the story file, whether it repeats through a
constant or by hand; interpolation inside a constant works in say/show and
is noted (and dropped, as it always was) in a plain property string."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start office\n'
    'constant MOTTO = "Measure twice, ship once."\n'
    'constant GREETING = "It is turn ${turns}, and all is well."\n'
    'room office\n    name "Office"\n    desc MOTTO\n'
    'thing plaque in office\n    name "brass plaque"\n    words plaque\n'
    '    desc MOTTO\n    fixed\n'
    'verb "recite"\n    recite\n'
    'on recite\n    say MOTTO\n    say GREETING\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(cmds, game=GAME):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_build(game)), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_constant_serves_desc_and_say():
    out = _run(["look", "x plaque", "recite", "z", "recite"])
    # The room desc, the thing desc, and the say all speak the one wording.
    assert out.count("Measure twice, ship once.") >= 3
    # In say, the constant's interpolation runs (turn count advances).
    assert "It is turn 2, and all is well." in out
    assert "It is turn 4, and all is well." in out


def test_identical_text_is_stored_once():
    long = "A" + "n enormously long piece of shared prose, going on" * 3 + "."
    shared = (
        'game\n    title "T"\n    start r\n'
        f'constant PROSE = "{long}"\n'
        'room r\n    name "R"\n    desc PROSE\n'
        'thing a in r\n    name "a"\n    desc PROSE\n'
        'thing b in r\n    name "b"\n    desc PROSE\n'
    )
    solo = (
        'game\n    title "T"\n    start r\n'
        f'room r\n    name "R"\n    desc "{long}"\n'
        'thing a in r\n    name "a"\n    desc "x"\n'
        'thing b in r\n    name "b"\n    desc "y"\n'
    )
    # Three shares must cost no more than one copy plus two tiny descs.
    assert len(_build(shared)) <= len(_build(solo))


def test_interpolation_in_plain_property_string_is_noted(capfd):
    src = (
        'game\n    title "T"\n    start r\n'
        'room r\n    name "R"\n    desc "It is ${turns} turns past nine."\n'
    )
    _build(src)
    err = capfd.readouterr().err
    assert "interpolation in a plain property string is dropped" in err
    assert "desc block" in err


def test_number_constant_seeds_a_property():
    # A number constant stands for its number in a property seed too
    # (a field report, 2026-09-13: the slot typed as object, collided
    # program-wide, and a KIND default emitted 0). The kind default, an
    # instance override, and a runtime change through the constant all
    # read back as the numbers they name.
    game = (
        'game\n    title "T"\n    start cellar\n'
        'constant shine_dim = 50\n'
        'constant shine_bright = 200\n'
        'kind cave of room\n    shine shine_dim\n'
        'room cellar of cave\n    name "Cellar"\n    desc "Stone."\n'
        'room attic of cave\n    name "Attic"\n    desc "Dust."\n'
        '    shine 75\n'
        'on start\n'
        '    say "cellar ${cellar.shine} attic ${attic.shine}"\n'
        '    change attic.shine to shine_bright\n'
        '    say "attic now ${attic.shine}"\n'
    )
    out = _run(["quit", "y"], game)
    assert "cellar 50 attic 75" in out
    assert "attic now 200" in out
