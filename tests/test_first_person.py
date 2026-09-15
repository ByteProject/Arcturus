# test_first_person.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""First-person narration (alos's game, chartered 2026-09-15): `constant
first_person = 1` and the English layer speaks as I. Every person branch
is a static-if on any_firstperson, so a second-person game is
byte-identical (the untouched ceilings are the standing proof, and the
explicit compile check here); the system voice (parser clarifications,
meta prompts, bracketed notices) stays second person by design. English
only, by ruling."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start cabin\n'
    'constant first_person = 1\n'
    'summon.extendedverbs\n'
    'room cabin\n    name "Cabin"\n    desc "Snug."\n'
    'thing lamp in cabin\n    name "brass lamp"\n    words brass, lamp\n'
    'thing stool of supporter in cabin\n    name "stool"\n    words stool\n'
    '    fixed\n'
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


def test_the_narration_speaks_as_i():
    out = _run(["take lamp", "i", "take lamp", "sit on stool", "stand",
                "take me", "jump", "polish lamp"])
    assert "I can see a brass lamp and a stool here." in out
    assert "I take the brass lamp with me." in out
    assert "I'm carrying:" in out
    assert "I already have the brass lamp." in out
    assert "I sit down on the stool." in out
    assert "I get up from the stool." in out
    assert "I keep a firm grip on myself." in out
    assert "I hop on the spot." in out
    assert "judge me in silence." in out
    # no second-person narration leaks
    assert "You take" not in out and "You can see" not in out


def test_the_system_voice_stays_second_person():
    out = _run(["take", "score", "quit", "y"])
    # the parser's ask and the meta verbs address the PLAYER, not the
    # narrator, in both narrations
    assert "The verb take requires you to be more specific." in out
    assert "Are you sure you want to quit?" in out


def test_second_person_is_byte_identical():
    base = (
        'game\n    title "T"\n    start cabin\n'
        'room cabin\n    name "Cabin"\n    desc "Snug."\n'
        'thing lamp in cabin\n    name "brass lamp"\n    words brass, lamp\n'
    )
    with_const = base.replace("    start cabin\n",
                              "    start cabin\nconstant first_person = 0\n")
    a = generate(analyze(cosmos.combined_program(parse(base))))
    b = generate(analyze(cosmos.combined_program(parse(with_const))))
    assert a == b
