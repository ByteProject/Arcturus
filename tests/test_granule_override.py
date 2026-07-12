# test_granule_override.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Most-specific-wins, the chain complete (a field report: overriding a
message failed when the action lives in extendedverbs.granule): a game
block overrides a granule block overrides a library block. Messages
(msg_*, line_*) are a granule's public skin and reskin silently, which
also unlocks message overrides in German and Spanish games (the language
packs are granules); capturing any OTHER granule block gets a teaching
note, since a silent collision with a granule's internal helper was the
reason the old rule forbade this outright."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

EXTENDED = (
    'game\n    title "T"\n    start shed\n'
    'summon.extendedverbs\n'
    'room shed\n    name "Shed"\n    desc "A shed."\n'
    'thing rock in shed\n    name "rock"\n    words rock\n'
    'block msg_rub()\n    say "The rock is not impressed by your rubbing."\n'
)

GERMAN = (
    'game\n    title "T"\n    start bau\n'
    'summon.language "german"\n'
    'room bau\n    name "Bau"\n    desc "Eine Kammer."\n'
    'thing stein in bau\n    name "Stein"\n    words stein\n'
    'block msg_taken()\n    say "Eingesteckt."\n'
)


def _run(cmds, game):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(game))))), io).run(
            max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_game_overrides_a_granule_message(capfd):
    out = _run(["rub rock"], EXTENDED)
    assert "The rock is not impressed by your rubbing." in out
    # A message reskin is the documented surface: no note.
    assert "replaces a summoned granule's block" not in capfd.readouterr().err


def test_game_overrides_a_language_pack_message():
    # The language packs are granules too; the old rule blocked EVERY
    # message override in a translated game.
    out = _run(["nimm stein"], GERMAN)
    assert "Eingesteckt." in out


def test_capturing_a_granule_internal_is_noted(capfd):
    src = (
        'game\n    title "T"\n    start r\n'
        'summon.debug\n'
        'room r\n    name "R"\n    desc "D."\n'
        # Collides with the debug granule's internal helper by accident.
        'block match_any()\n    return nothing\n'
    )
    generate(analyze(cosmos.combined_program(parse(src))))
    err = capfd.readouterr().err
    assert "block 'match_any' replaces a summoned granule's block" in err
