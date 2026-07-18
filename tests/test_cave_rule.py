# test_cave_rule.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The cave rule (the modern darkness approach, analog to Inform 7; ruled
2026-07-18): in darkness the player can feel what they carry, so
INVENTORY works, but they cannot SEE detail, so EXAMINE (and READ, which
maps onto it) refuse without light. A game that wants stricter darkness
overrides inventory with a one-line free rule; the recipe is pinned here."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(game, cmds):
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


_DARK = (
    'game\n    title "T"\n    start cave\n'
    'room cave\n    name "Cave"\n    desc "A cave."\n    lit false\n'
    'thing lamp in player\n    name "lamp"\n    words lamp\n    lit false\n'
    '    desc "A dented lamp."\n'
    '    on switch_on\n        now self is lit\n        say "The lamp glows."\n'
    'thing coin in player\n    name "coin"\n    words coin\n'
    '    desc "A worn coin."\n'
)


def test_examine_and_read_refuse_in_the_dark():
    out = _run(_DARK, ["x coin", "read coin"])
    assert out.count("too dark") == 2
    assert "A worn coin." not in out


def test_inventory_works_in_the_dark():
    out = _run(_DARK, ["i"])
    assert "lamp" in out and "coin" in out
    assert "too dark" not in out


def test_light_restores_examine():
    out = _run(_DARK, ["turn on lamp", "x coin"])
    assert "The lamp glows." in out
    assert "A worn coin." in out


def test_strict_darkness_recipe_overrides_inventory():
    game = _DARK + (
        'on inventory when is_lit is false\n'
        '    say "It is far too dark to rummage through your belongings."\n'
        '    stop\n'
    )
    out = _run(game, ["i", "turn on lamp", "i"])
    assert "far too dark to rummage" in out
    assert "coin" in out.split("glows")[-1]   # lit inventory lists again
