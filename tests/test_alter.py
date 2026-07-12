# test_alter.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""alter (a field request: default mechanics, your wording): a handler
speaks the action's report itself, one line (`alter "..."`) or an indented
body for composed wording, then continues; the default runs its full
mechanics and its success line stays silent. A plain say + continue keeps
today's stacking (the flavor idiom survives), refusals never honor the
mark, and a game that never alters compiles byte-identical (the untouched
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
    'game\n    title "T"\n    start shrine\n'
    'summon.extendedverbs\n'
    'room shrine\n    name "Shrine"\n    desc "A shrine."\n'
    'thing idol in shrine\n    name "jade idol"\n    words idol, jade\n'
    '    on take\n'
    '        alter "The idol comes free with a reluctance you can feel."\n'
    '        continue\n'
    '    on drop\n'
    '        alter\n'
    '            show("You set the idol down")\n'
    '            if here is shrine\n'
    '                show(", and the shrine seems to sigh")\n'
    '            say "."\n'
    '        continue\n'
    '    on rub\n'
    '        alter "The jade warms under your palm."\n'
    '        continue\n'
    'thing altar of supporter in shrine\n    name "altar"\n    words altar\n'
    '    fixed\n'
    '    on take\n'
    '        alter "You heave at the altar."\n'
    '        continue\n'
    'thing candle in shrine\n    name "candle"\n    words candle\n'
    '    on take\n'
    '        say "Wax flakes under your fingers."\n'
    '        continue\n'
)

_STORY = {}


def _run(cmds):
    if "s" not in _STORY:
        _STORY["s"] = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY["s"]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_alter_speaks_and_mechanics_run():
    out = _run(["take idol", "i", "drop idol"])
    assert "The idol comes free with a reluctance you can feel." in out
    assert "Got it." not in out                      # the default stayed silent
    assert "jade idol" in out                        # ...but the take HAPPENED
    assert "You set the idol down, and the shrine seems to sigh." in out
    assert "Down it goes." not in out                # block form suppressed too


def test_refusals_never_honor_the_mark():
    out = _run(["take altar"])
    assert "You heave at the altar." in out
    assert "stays exactly where it is." in out       # the refusal still speaks
    assert "altar" not in _run(["take altar", "i"]).split("carrying")[-1]


def test_plain_say_still_stacks():
    out = _run(["take candle"])
    assert "Wax flakes under your fingers." in out
    assert "Got it." in out                          # the flavor idiom survives


def test_alter_covers_a_granule_default():
    out = _run(["take idol", "rub idol"])
    assert "The jade warms under your palm." in out
    assert "Rubbing" not in out and "polish" not in out


def test_the_mark_lives_one_action():
    out = _run(["take idol", "drop idol", "take candle"])
    assert "Got it." in out                          # candle's default back
