# test_parse_command.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The B4.5d done-test: the Cosmos parser (parser.prelude + english.prelude)
resolves a typed line to an action and a noun, on Frotz."""

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
    'verb "take", "get"\n'
    '    take noun\n'
    'thing lamp in cave\n'
    '    name "brass lamp"\n'
    '    words brass, lamp, lantern\n'
    'thing coin in cave\n'
    '    name "gold coin"\n'
    '    words gold, coin\n'
    'room cave\n'
    '    name "Cave"\n'
)


def _parse_story():
    world = analyze(cosmos.combined_program(parse(GAME)))
    gmap = _globals_map(world)
    actions = _action_numbers(world)
    layout = build_layout(world, react_objects=_react_objects(world, actions))
    pool = StringPool()
    _main, routines, registry = build_routines(world, gmap, layout, pool)
    react = gen_react_routines(world, actions, registry)
    obj = layout.obj_number

    drive = a.Routine("__main__", nlocals=0)
    drive.op("store", a.Const(gmap["player"]), a.Const(obj["player"]))
    drive.op("store", a.Const(gmap["here"]), a.Const(obj["cave"]))
    drive.op("call_vs", a.RoutineRef("blk_parse"), store=a.Variable(a.STACK))
    drive.op("print", text="action: ")
    drive.op("print_num", a.Variable(a.STACK))
    drive.op("new_line")
    drive.op("print", text="noun: ")
    drive.op("print_obj", a.Variable(gmap["noun"]))
    drive.op("new_line")
    drive.op("rfalse")

    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vn", a.RoutineRef("__main__"))
    entry.op("quit")
    story = build_story(world, entry, [drive] + routines + react + [gen_schedule_tick(world, gmap)]
                       + gen_topic_helpers(layout), layout=layout, string_pool=pool)
    return story, actions


def test_parse_story_compiles():
    assert _parse_story()[0][0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
@pytest.mark.parametrize(
    "command,verb,noun_name",
    [
        ("take lamp", "take", "brass lamp"),
        ("get coin", "take", "gold coin"),
        ("take the brass lamp", "take", "brass lamp"),  # noise word + adjective
    ],
)
def test_parser_resolves_command(tmp_path, command, verb, noun_name):
    story, actions = _parse_story()
    path = tmp_path / "p.z5"
    path.write_bytes(story)
    out = subprocess.run(
        [_frotz(), "-p", str(path)], input=command + "\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert f"action: {actions[verb]}" in out
    assert f"noun: {noun_name}" in out
