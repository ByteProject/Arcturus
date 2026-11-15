# test_cycle_gate.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The tree never cycles, and the refusal comes before any handler
(improvmonster's report, 2026-11-10): a supporter kind's own `on put`
capacity check spoke first on PUT TRAY ON TRAY, and a handler that moved
the thing itself halted the interpreter. check_cycle now runs in the
turn loop beside the other gates, for put and insert, the thing itself
and anything it holds; perform() meets the same gate before it dispatches."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start kitchen\n'
    'room kitchen\n    name "Kitchen"\n    desc "Tiles."\n'
    'kind shelf of supporter\n'
    '    on put\n'
    '        if second.item_count >= 1\n'
    '            say "There is not enough room on ${the second}."\n'
    '            stop\n'
    '        continue\n'
    'kind cart of supporter\n'
    '    on put\n'
    '        move noun to second\n'
    '        say "Onto the cart."\n'
    'kind hamper of container\n'
    '    on insert\n'
    '        move noun to second\n'
    '        say "Into the hamper."\n'
    'thing tray of shelf in kitchen\n    name "tray"\n    words tray\n'
    'thing cup in kitchen\n    name "cup"\n    words cup\n'
    'thing wagon of cart in kitchen\n    name "wagon"\n    words wagon\n'
    'thing basket of hamper in kitchen\n    name "basket"\n    words basket\n    open\n'
    'thing box of hamper in kitchen\n    name "box"\n    words box\n    open\n'
    'verb "heave"\n    heave noun\n'
    'on heave\n'
    '    if perform("put", noun, noun) is false\n'
    '        say "(perform refused)"\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_a_capacity_handler_never_speaks_for_a_self_put():
    out = _run(["put cup on tray", "put tray on tray"])
    assert "You put the cup on the tray." in out
    assert "You can't put the tray on top of itself." in out
    assert "not enough room" not in out


def test_a_moving_handler_never_sees_a_self_put():
    out = _run(["put wagon on wagon", "put basket in basket", "look"])
    assert "You can't put the wagon on top of itself." in out
    assert "You can't put the basket inside itself." in out
    assert "Onto the cart." not in out and "Into the hamper." not in out
    assert "Kitchen" in out.split("look")[-1]  # the story still runs


def test_nested_holders_are_refused_too():
    out = _run(["put box in basket", "put basket in box",
                "put cup on wagon", "put wagon on cup"])
    assert "Into the hamper." in out
    assert "You can't put the basket inside itself." in out
    assert "Onto the cart." in out
    assert out.count("Onto the cart.") == 1


def test_perform_meets_the_same_gate():
    # the cup has only the library handler; the wagon's own handler moves
    out = _run(["heave cup", "heave wagon", "look"])
    assert "You can't put the cup inside itself." in out
    assert "You can't put the wagon on top of itself." in out
    assert out.count("(perform refused)") == 2
    assert "Onto the cart." not in out
    assert "Kitchen" in out.split("look")[-1]
