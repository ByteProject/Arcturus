# test_nautical.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The nautical granule (a field report: `direction aft` in a game refused,
because direction properties are the compiler's standard set): fore, aft,
port, and starboard are standard direction PROPERTIES now, so exits and
`on go fore` handlers compile in any game, and summon.nautical opts in the
player words (F and SB included). Unsummoned, the words are unknown and,
like every direction, the unused properties cost nothing (the untouched
ceilings)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start bridge\n'
    'summon.nautical\n'
    'room bridge\n    name "Bridge"\n    desc "Dials."\n    aft walkway\n'
    'room walkway\n    name "Walkway"\n    desc "Narrow."\n'
    '    fore bridge\n    port hold\n'
    'room hold\n    name "Hold"\n    desc "Dark shapes."\n    starboard walkway\n'
    'on go fore\n'
    '    if here is walkway\n'
    '        say "You duck the frame."\n'
    '    continue\n'
)

UNSUMMONED = (
    'game\n    title "T"\n    start bridge\n'
    'room bridge\n    name "Bridge"\n    desc "Dials."\n    aft walkway\n'
    'room walkway\n    name "Walkway"\n    desc "Narrow."\n    fore bridge\n'
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


def test_nautical_words_walk_the_ship():
    out = _run(["aft", "port", "sb", "f"])
    assert out.count("Walkway") == 2      # aft in, sb back
    assert "Hold" in out                  # port
    assert "You duck the frame." in out   # the on go fore handler
    assert out.count("Bridge") >= 2       # f walked fore after the handler


def test_unsummoned_properties_compile_but_words_are_unknown():
    # The exits compile without the granule; the player word does not exist,
    # so a bare "aft" is not a command at all (and certainly not a walk).
    out = _run(["aft"], game=UNSUMMONED)
    assert "Those words don't add up to anything." in out
    assert "Walkway" not in out
