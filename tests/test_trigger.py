# test_trigger.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The trigger marker (docs/01 chapter 14): `words #crate, packing` marks a
word as what the thing IS. Among tied candidates, exactly one whose trigger
was typed wins silently; two or more typed triggers keep the question; zero
changes nothing. A tiebreaker, never a gag order, and it outranks the held
heuristic: declared intent beats a guess."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze


def _replies(src, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


# The shared-synonym shape: the chest generously answers to "crate" too, so
# OPEN CRATE ties two partial matches, the exact ask the marker kills.
GAME_SYN = (
    'game\n    title "T"\n    start cellar\n'
    'room cellar\n    name "Cellar"\n    desc "A cellar."\n'
    'thing crate in cellar\n    name "packing crate"\n'
    '    words #crate, packing\n'
    '    container\n    openable\n'
    '    on open\n        say "[CRATE]"\n        stop\n'
    'thing chest in cellar\n    name "oak chest"\n'
    '    words #chest, oak, crate\n'
    '    container\n    openable\n'
    '    on open\n        say "[CHEST]"\n        stop\n'
    'thing coin in cellar\n    name "gold coin"\n    words coin\n'
)


def test_typed_trigger_wins_the_tie():
    # OPEN CRATE: both score 1, both partial, and only the crate's trigger
    # was typed: the crate opens, no question asked.
    out = _replies(GAME_SYN, ["open crate"])
    assert "[CRATE]" in out
    assert "[CHEST]" not in out
    assert "Which do you mean" not in out


def test_trigger_outranks_the_held_tiebreak():
    # With the chest in hand, the held heuristic would settle OPEN CRATE on
    # the chest. The typed trigger is declared intent and wins first.
    out = _replies(GAME_SYN, ["take chest", "open crate"])
    assert "[CRATE]" in out
    assert "[CHEST]" not in out


def test_trigger_settles_the_second_slot_too():
    # PUT COIN IN CRATE: the second slot ties the same way; the trigger
    # settles it through the same matcher, and the coin lands in the crate.
    out = _replies(GAME_SYN, ["take coin", "put coin in crate", "open crate"])
    assert "Which do you mean" not in out
    assert "[CRATE]" in out


# The symmetric shape: no shared synonym, each with its own trigger, tied
# only when the player names both at once or neither distinctly.
GAME_TWO = (
    'game\n    title "U"\n    start cellar\n'
    'room cellar\n    name "Cellar"\n    desc "A cellar."\n'
    'thing crate in cellar\n    name "packing crate"\n'
    '    words #crate, packing, box\n'
    '    container\n    openable\n'
    '    on open\n        say "[CRATE]"\n        stop\n'
    'thing chest in cellar\n    name "oak chest"\n'
    '    words #chest, oak, box\n'
    '    container\n    openable\n'
    '    on open\n        say "[CHEST]"\n        stop\n'
)


def test_two_typed_triggers_still_ask():
    # OPEN CRATE CHEST names both triggers at once: a genuine question, and
    # the marker never gags it (Stefan's rule).
    out = _replies(GAME_TWO, ["open crate chest"])
    assert "Which do you mean" in out
    assert "[CRATE]" not in out
    assert "[CHEST]" not in out


def test_zero_typed_triggers_change_nothing():
    # OPEN BOX touches no trigger: the ordinary ask stands, and answering
    # still works.
    out = _replies(GAME_TWO, ["open box"])
    assert "Which do you mean" in out
    out = _replies(GAME_TWO, ["open box", "crate"])
    assert "[CRATE]" in out


GERMAN_SYN = (
    'summon.language "german"\n'
    'game\n    title "G"\n    start keller\n'
    'room keller\n    name "Keller"\n    desc "Ein Keller."\n'
    'thing kiste in keller\n    name "große Kiste"\n'
    '    words #kiste, gross, grosse\n    die\n'
    '    container\n    openable\n'
    '    on open\n        say "[KISTE]"\n        stop\n'
    'thing truhe in keller\n    name "Truhe aus Eiche"\n'
    '    words truhe, eiche, kiste\n    die\n'
    '    container\n    openable\n'
    '    on open\n        say "[TRUHE]"\n        stop\n'
)


def test_trigger_is_language_agnostic():
    # The marker lives in the agnostic skeleton: the German Kiste/Truhe
    # shape resolves the same way, no pack work.
    out = _replies(GERMAN_SYN, ["oeffne kiste"])
    assert "[KISTE]" in out
    assert "Was meinst du" not in out


def test_trigger_marker_is_words_only():
    # The # marker belongs to `words`; a plural list refuses it.
    src = (
        'game\n    title "P"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing coin in r\n    name "coin"\n    words coin\n    plural #coins\n'
    )
    with pytest.raises(ArcError):
        parse(src)
