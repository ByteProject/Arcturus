# test_verb_trigger.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The bare-command ask and verb_trigger (the verbs overhaul, completed).

A CUSTOM verb with noun grammar used to answer a bare command with silence
and a consumed move while a standard verb asked; now the ask is central,
library-owned, and answers for every verb alike with the one honest line,
"The verb <word> requires you to be more specific.", echoing the verb AS
TYPED (full length, the player's own synonym). And the seam that carries
the typed word is author-facing: `verb_trigger` compares against a verb
word (`if verb_trigger is "roll"` inside an `on push`), so a handler can
branch on the phrasing rather than the action family."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    # The checkpoint's one-minute repro: a custom flag-model verb.
    'verb "wibble"\n    wib noun\n'
    # A long verb word: the echo must spell it whole from the text buffer
    # (the dictionary's nine-character cap must never show).
    'verb "disintegrate"\n    zap noun\n'
    # A custom TABLED verb (a literal before the slot tables it).
    'verb "peer"\n    peer_under under noun\n'
    # A custom verb with a DECLARED bare line: the author owns the bare
    # command, and the handler sees noun = nothing.
    'verb "hum"\n    hum\n    hum noun\n'
    'on hum\n'
    '    if noun is nothing\n        say "You hum vaguely."\n        stop\n'
    '    say "You hum at ${the noun}."\n'
    'thing trunk in hall\n    name "trunk"\n    words trunk\n'
    '    on wib\n        say "WIBBLED."\n'
    '    on push\n'
    '        if verb_trigger is "shove"\n'
    '            say "It ROLLS."\n'
    '            stop\n'
    '        say "It SLIDES."\n'
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


def test_bare_custom_verb_asks_like_a_standard_one():
    # The urgent half of the overhaul: silence is gone, the ask is central.
    out = _run(["wibble", "push", "wibble trunk"])
    assert "The verb wibble requires you to be more specific." in out
    assert "The verb push requires you to be more specific." in out
    assert "WIBBLED." in out


def test_the_echo_is_the_full_typed_word():
    # "disintegrate" is 12 characters; the dictionary truncates at nine, the
    # echo must not ("The verb disintegr..." was ruled a bug).
    out = _run(["disintegrate"])
    assert "The verb disintegrate requires you to be more specific." in out


def test_bare_tabled_custom_verb_asks_too():
    # PEER (and PEER UNDER with nothing after it) ride the positional table.
    out = _run(["peer", "peer under"])
    assert out.count("The verb peer requires you to be more specific.") == 2


def test_a_declared_bare_line_hands_the_bare_command_to_the_handler():
    out = _run(["hum", "hum trunk"])
    assert "You hum vaguely." in out
    assert "You hum at the trunk." in out
    assert "The verb hum requires" not in out


def test_verb_trigger_branches_on_the_typed_synonym():
    # PUSH and SHOVE reach the same action; verb_trigger tells them apart.
    out = _run(["push trunk", "shove trunk"])
    assert "It SLIDES." in out
    assert "It ROLLS." in out


def test_the_ask_costs_no_move_and_again_skips_it():
    # The ask is a meta refusal: AGAIN repeats the last REAL command, never
    # the refused bare one.
    out = _run(["push trunk", "shove", "again"])
    assert out.count("It SLIDES.") == 2
    assert out.count("It ROLLS.") == 0


def test_an_unknown_trigger_word_is_a_compile_error():
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing rock in hall\n    name "rock"\n    words rock\n'
        '    on push\n'
        '        if verb_trigger is "frobnicate"\n'
        '            say "?"\n'
    )
    with pytest.raises(ArcError):
        generate(analyze(cosmos.combined_program(parse(game))))
