# test_put_gate.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Put and insert refuse what a take refuses (auraes's couch, 2026-09-08):
both handlers move a noun the player does not hold, the floor-to-container
shortcut, so they must ask take_probe first; a fixed couch, scenery, or a
character never rides into a chest, and the refusal speaks in the take's
exact words (one guard chain, the take_probe discipline). A held thing
skips the probe, and a takeable floor thing still moves in one command."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _play(src, script):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(script) + ["quit", "y"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io, seed=7).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


GAME = (
    'game\n    title "Parlor"\n    author "T"\n    start parlor\n'
    'room parlor\n    name "Parlor"\n    desc "A parlor."\n'
    'thing couch in parlor\n    name "red couch"\n    words couch\n'
    '    fixed\n'
    'thing wallpaper in parlor\n    name "wallpaper"\n    words wallpaper\n'
    '    scenery\n'
    'thing vlad of character in parlor\n    name "Vlad"\n    words vlad\n'
    'thing coin in parlor\n    name "coin"\n    words coin\n'
    'thing pebble in player\n    name "pebble"\n    words pebble\n'
    'thing chest of container in parlor\n    name "chest"\n    words chest\n'
    '    open\n'
    'thing table of supporter in parlor\n    name "table"\n    words table\n'
)


def test_fixed_never_rides_into_a_container():
    out = _play(GAME, ["insert couch in chest", "look"])
    assert "stays exactly where it is" in out
    assert "contains a red couch" not in out


def test_fixed_never_rides_onto_a_supporter():
    out = _play(GAME, ["put couch on table"])
    assert "stays exactly where it is" in out


def test_scenery_and_characters_refuse_in_the_takes_words():
    out = _play(GAME, ["put wallpaper in chest", "insert vlad in chest"])
    assert "Just some scenery" in out
    assert "other ideas" in out


def test_the_floor_shortcut_and_the_held_case_still_move():
    # A takeable floor thing still moves in one command (no implicit-take
    # ceremony), and a held thing skips the probe entirely.
    out = _play(GAME, ["put coin in chest", "put pebble on table", "look"])
    assert "contains a coin" in out
    assert "is a pebble" in out
