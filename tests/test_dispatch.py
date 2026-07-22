# test_dispatch.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The B4.5b done-test: the Arcturus dispatcher (cosmos/dispatch.prelude) routes
an action to the noun's handler via the react property, on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import assembler as a
from arcturus import cosmos
from arcturus.codegen import (
    gen_topic_helpers,
    StringPool,
    _action_numbers,
    _globals_map,
    _react_objects,
    build_routines,
    build_story,
    gen_react_routines,
    gen_schedule_tick,
)
from arcturus.objects import build_layout
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'thing red in cave\n'
    '    name "red lever"\n'
    '    on pull\n'
    '        say "Red pulled."\n'
    'thing blue in cave\n'
    '    name "blue lever"\n'
    '    on pull\n'
    '        say "Blue pulled."\n'
    'room cave\n'
    '    name "Cave"\n'
)


def _dispatch_story(nouns):
    """Drive the Arcturus dispatcher: for each object name, set noun and call
    dispatch(pull)."""
    world = analyze(cosmos.combined_program(parse(GAME)))
    gmap = _globals_map(world)
    actions = _action_numbers(world)
    layout = build_layout(world, react_objects=_react_objects(world, actions))
    pool = StringPool()
    _main, routines, registry = build_routines(world, gmap, layout, pool)
    react = gen_react_routines(world, actions, registry)

    drive = a.Routine("__main__", nlocals=0)
    for objname in nouns:
        drive.op("store", a.Const(gmap["noun"]), a.Const(layout.obj_number[objname]))
        drive.op("call_vn", a.RoutineRef("blk_dispatch"), a.Const(actions["pull"]))
    drive.op("rfalse")

    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vn", a.RoutineRef("__main__"))
    entry.op("quit")
    return build_story(world, entry, [drive] + routines + react + [gen_schedule_tick(world, gmap)]
                       + gen_topic_helpers(layout), layout=layout, string_pool=pool)


def test_dispatch_story_compiles():
    assert _dispatch_story(["red"])[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_dispatcher_routes_to_noun_handler(tmp_path):
    story = tmp_path / "d.z5"
    story.write_bytes(_dispatch_story(["red", "blue"]))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    # The dispatcher read each noun's react routine and fired its own handler.
    assert "Red pulled." in out
    assert "Blue pulled." in out
