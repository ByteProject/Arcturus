# test_noun_missing.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A bare verb asks its question (a field report from a Dialog port): TAKE
with no noun used to answer "You see nothing of the sort here.", the same
line as naming a thing that is absent, though the situations are opposite.
Now the bare verb asks, echoing the verb as typed ("Take what?", "Nimm
was?", "¿Coge qué?"), while a named-but-absent thing keeps the honest
can't-see, and an unknown word keeps the typo line."""

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
    'room hall\n    name "Hall"\n    desc "A hall."\n    north attic\n'
    'room attic\n    name "Attic"\n    desc "Dust."\n    south hall\n'
    'thing broom in attic\n    name "broom"\n    words broom\n'
)

GERMAN = (
    'game\n    title "T"\n    start bau\n'
    'summon.language "german"\n'
    'room bau\n    name "Bau"\n    desc "Eine Kammer."\n'
)

SPANISH = (
    'game\n    title "T"\n    start sala\n'
    'summon.language "spanish"\n'
    'room sala\n    name "Sala"\n    desc "Una sala."\n'
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


def test_bare_verb_asks_with_the_verb_echoed():
    out = _run(["take", "examine", "open"])
    assert "Take what?" in out
    assert "Examine what?" in out
    assert "Open what?" in out
    assert "You see nothing of the sort here." not in out


def test_the_three_answers_stay_distinct():
    # Bare verb asks; a real thing that is elsewhere keeps the can't-see;
    # an unknown word keeps the typo line. Three situations, three answers.
    out = _run(["take", "take broom", "take zzzq"])
    assert "Take what?" in out
    assert "You see nothing of the sort here." in out
    assert 'doesn\'t know the word "zzzq"' in out


def test_german_asks_natively():
    out = _run(["nimm", "untersuche"], game=GERMAN)
    assert "Nimm was?" in out
    assert "Untersuche was?" in out


def test_spanish_asks_natively():
    out = _run(["coge", "examina"], game=SPANISH)
    assert "¿Coge qué?" in out
    assert "¿Examina qué?" in out


def test_say_way_speaks_the_direction_word():
    # The Charles request: print the direction in a custom message. `say
    # way` (and ${way}) speaks the canonical word, not the property number;
    # way 0 prints nothing.
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "Bare."\n    north loft\n'
        'room loft\n    name "Loft"\n    desc "Up."\n    south hall\n'
        'on go\n'
        '    say "You head ${way} with purpose."\n'
        '    continue\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["north", "south"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "You head north with purpose." in io.text
    assert "You head south with purpose." in io.text
