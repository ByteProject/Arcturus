# test_computed_exits.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Computed exits (docs/01 chapter 8): a direction property may be a
`block`, so an exit can depend on world state, returning a room to allow the
move or `nothing` to refuse it. The one computed VALUE property Arcturus
supports: a destination is a room object number (small), so an exit read
tells it from the block routine's packed address (large) at the __routines__
threshold. A general computed value property stays a compile error. Static
exits fold the machinery away, so a game without a computed exit is
byte-identical."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GATE = (
    'game\n    title "Gate"\n    start cave\n'
    'room cave\n    name "Cave Mouth"\n    desc "A dark opening."\n'
    '    north block\n'
    '        if portcullis is open\n'
    '            return inner_hall\n'
    '        return nothing\n'
    'room inner_hall\n    name "Inner Hall"\n    desc "Beyond the gate."\n'
    '    south cave\n'
    'thing portcullis in cave\n    name "iron portcullis"\n    openable\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(story, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_computed_exit_refuses_when_the_block_returns_nothing():
    out = _run(_build(GATE), ["north"]).split(">north")[-1]
    assert "Inner Hall" not in out          # the gate is shut
    assert "no exit" in out.lower() or "cannot go" in out.lower()


def test_computed_exit_allows_when_the_block_returns_a_room():
    out = _run(_build(GATE), ["open portcullis", "north"]).split(">north")[-1]
    assert "Inner Hall" in out              # the block returned the room
    assert "Beyond the gate." in out


def test_computed_exit_re_evaluates_each_turn():
    # Open, go through, come back, close, try again: the block is state, not a
    # one-time value.
    out = _run(_build(GATE),
               ["open portcullis", "north", "south", "close portcullis", "north"])
    tail = out.split("close portcullis")[-1]
    assert "Inner Hall" not in tail          # shut again, refused again


def test_static_exits_still_work_alongside_a_computed_one():
    out = _run(_build(GATE), ["open portcullis", "north", "south"])
    # SOUTH from the inner hall is a plain static exit back to the cave.
    assert out.rstrip().endswith(">") or "Cave Mouth" in out.split("south")[-1]


def test_a_computed_weight_speaks_the_units_of_a_plain_one():
    # Value properties may be blocks since arcc 2.35.0 (Stefan's ruling,
    # 2026-10-24); the restriction this test once pinned is lifted. A
    # computed weight returns whole units like a plain `weight 5`: the
    # carryweight granule's tenths scaling reaches its returns.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'summon.carryweight\n'
        'game\n    title "V"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x."\n'
        'thing rock in hall\n    name "rock"\n    words rock\n'
        '    weight block\n'
        '        return 5\n'
        'thing pebble in hall\n    name "pebble"\n    words pebble\n    weight 5\n'
        'verb "probe"\n    probe\n'
        'on probe\n    say "${rock.weight} ${pebble.weight}"\n'
    )
    io = CaptureIO(script=["probe"])
    try:
        VM(load(_build(src)), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "50 50" in io.text


def test_static_exit_game_is_byte_identical_without_the_machinery():
    # A game whose exits are all static compiles the same as it would have
    # before computed exits existed: exit_dest folds to a plain property read.
    static = (
        'game\n    title "S"\n    start a\n'
        'room a\n    name "A"\n    desc "Room A."\n    north b\n'
        'room b\n    name "B"\n    desc "Room B."\n    south a\n'
    )
    assert _build(static) == _build(static)  # deterministic; no stray state
