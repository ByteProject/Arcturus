# test_react.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""react routines and the react property (B4.5b, piece 2). A hand-driven harness
reads an object's react property and calls it (the call-by-address the Cosmos
dispatcher will use), checking the right handler fires and stop/continue codes."""

import shutil
import subprocess

import pytest

from arcturus import assembler as a
from arcturus.codegen import (
    StringPool,
    _action_numbers,
    _globals_map,
    _react_objects,
    build_routines,
    build_story,
    gen_react_routines,
)
from arcturus.objects import REACT_PROP, build_layout
from arcturus.parser import parse
from arcturus.sema import analyze

LEVER = (
    'thing lever in cave\n'
    '    name "lever"\n'
    '    pulled false\n'
    '    on pull\n'
    '        if lever is pulled\n'
    '            say "It will not give again."\n'
    '            stop\n'
    '        now lever is pulled\n'
    '        say "The lever grinds down."\n'
    'room cave\n'
    '    name "Cave"\n'
)


def test_lever_has_a_react_routine_and_property():
    world = analyze(parse(LEVER))
    actions = _action_numbers(world)
    assert "lever" in _react_objects(world, actions)
    layout = build_layout(world, react_objects=_react_objects(world, actions))
    _m, routines, registry = build_routines(world, _globals_map(world), layout, StringPool())
    react = gen_react_routines(world, actions, registry)
    assert any(r.name == "react_lever" for r in react)


def _harness(src, calls):
    """Build a story whose main routine drives the react mechanism: for each
    (object, action) it sets noun, reads object.react, calls it, and prints the
    returned dispatch code."""
    world = analyze(parse(src))
    gmap = _globals_map(world)
    actions = _action_numbers(world)
    layout = build_layout(world, react_objects=_react_objects(world, actions))
    pool = StringPool()
    _main, routines, registry = build_routines(world, gmap, layout, pool)
    react = gen_react_routines(world, actions, registry)

    drive = a.Routine("__main__", nlocals=1)
    for objname, action in calls:
        onum = layout.obj_number[objname]
        drive.op("store", a.Const(gmap["noun"]), a.Const(onum))  # noun = object
        drive.op("get_prop", a.Const(onum), a.Const(REACT_PROP), store=a.Variable(1))
        drive.op("call_vs", a.Variable(1), a.Const(actions[action]), store=a.Variable(a.STACK))
        drive.op("print", text="result: ")
        drive.op("print_num", a.Variable(a.STACK))
        drive.op("new_line")
    drive.op("rfalse")

    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vn", a.RoutineRef("__main__"))
    entry.op("quit")
    return build_story(world, entry, [drive] + routines + react, layout=layout, string_pool=pool)


def test_harness_compiles():
    data = _harness(LEVER, [("lever", "pull")])
    assert data[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_dispatch_fires_handler_and_honors_stop(tmp_path):
    # pull once (runs the body, returns handled), pull again (the guard takes the
    # stop path, still handled), examine (no handler, returns not-handled).
    story = tmp_path / "react.z5"
    story.write_bytes(_harness(LEVER, [("lever", "pull"), ("lever", "pull"), ("lever", "examine")]))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "The lever grinds down." in out  # first pull ran the body
    assert "It will not give again." in out  # second pull hit the stop guard
    # dispatch codes: handled, handled, not-handled.
    assert "result: 1" in out and "result: 0" in out
