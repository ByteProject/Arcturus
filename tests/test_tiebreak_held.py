# test_tiebreak_held.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The held tiebreak (a field request from a Dialog port): a noun-phrase
tie where exactly one candidate is in the player's hands is not an
ambiguity worth a question. EXAMINE MIRROR with one in hand and one on an
NPC means the held one, silently; TAKE MIRROR in the same room means the
one NOT held (taking wants the takeable one). A tie with no held side, or
two candidates on the wanted side, still asks."""

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
    'room parlor\n    name "Parlor"\n    desc "A parlor."\n'
    'thing pocket_mirror in player\n    name "silver mirror"\n'
    '    words mirror, silver\n    desc "Your own silver mirror."\n'
    'thing guard of character in parlor\n    name "guard"\n    words guard\n'
    'thing guard_mirror in guard\n    name "brass mirror"\n'
    '    words mirror, brass\n    desc "The guard\'s brass mirror."\n'
    '    component\n'
    'thing table_mirror in parlor\n    name "cracked mirror"\n'
    '    words mirror, cracked\n    desc "A cracked mirror."\n'
)

TWO_LOOSE = (
    'game\n    title "T"\n    start shed\n'
    'room shed\n    name "Shed"\n    desc "A shed."\n'
    'thing red_pail in shed\n    name "red pail"\n    words pail, red\n'
    'thing blue_pail in shed\n    name "blue pail"\n    words pail, blue\n'
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


def test_examine_prefers_the_held_one():
    # Three mirrors tie (held, the NPC's component, on the floor); exactly
    # one is in hand, so no question is asked and the held one answers.
    out = _run(["examine mirror"])
    assert "Your own silver mirror." in out
    assert "Which do you mean" not in out


def test_take_prefers_one_not_held_or_asks():
    # For TAKE the wanted side is not-held; two candidates sit there (the
    # guard's and the floor's), so the honest question still comes.
    out = _run(["take mirror"])
    assert "Which do you mean" in out


def test_drop_means_the_held_one():
    out = _run(["drop mirror", "look"])
    assert "Which do you mean" not in out
    assert "cracked mirror" in out  # the floor one still where it was
    assert "silver mirror" in out   # the held one, now dropped and listed


def test_a_tie_with_no_held_side_still_asks():
    out = _run(["examine pail"], game=TWO_LOOSE)
    assert "Which do you mean" in out
