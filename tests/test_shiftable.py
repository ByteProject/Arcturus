# test_shiftable.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""PUSH THE CRATE NORTH (the verbs overhaul, phase 6; Stefan named the
attribute): a `shiftable` thing rolls through the exit with the player,
doors respected, the same arrival a walk gets. Anything else with a
direction answers that it will not shift; a bare push keeps the flat
default; a game with nothing shiftable folds the whole path away. PICK UP
lands beside it: an up-direction with a noun is the everyday take, never a
boarding, in both word orders."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "P"\n    start dock\n'
    'room dock\n    name "Dock"\n    desc "A dock."\n    north warehouse\n'
    'room warehouse\n    name "Warehouse"\n    desc "A warehouse."\n'
    '    south dock\n'
    'thing barrel in dock\n    name "tar barrel"\n    words barrel, tar\n'
    '    shiftable\n'
    'thing anvil in dock\n    name "anvil"\n    words anvil\n'
    'thing lamp in dock\n    name "brass lamp"\n    words lamp, brass\n'
)


def _run(cmds, src=GAME):
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


def test_a_shiftable_thing_travels_and_the_player_follows():
    out = _run(["push barrel north", "look"])
    assert "shove it along" in out
    assert "Warehouse" in out
    tail = out.split("Warehouse")[-1]
    assert "tar barrel" in tail


def test_an_unshiftable_thing_refuses_the_direction():
    out = _run(["push anvil north"])
    assert "not going anywhere that way" in out


def test_no_exit_refuses_like_a_walk():
    out = _run(["push barrel east"])
    assert "no exit" in out.lower()


def test_a_bare_push_keeps_the_flat_default():
    out = _run(["push barrel"])
    assert "holds firm" in out


def test_a_shut_door_blocks_the_shove():
    src = GAME.replace(
        "    north warehouse\n",
        "    north gate\n",
    ) + (
        'thing gate of door in dock\n    name "iron gate"\n    words gate, iron\n'
        '    spans dock, warehouse\n'
        '    open false\n'
    )
    out = _run(["push barrel north"], src=src)
    assert "shut" in out.lower() or "closed" in out.lower()


def test_pick_up_is_the_everyday_take():
    out = _run(["pick up the lamp", "i"])
    assert "Got it." in out
    assert "brass lamp" in out.split(">i")[-1]
    out = _run(["pick the lamp up"])
    assert "Got it." in out
