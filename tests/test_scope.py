# test_scope.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Scope and light (B4.5c, done-test). A harness drives the Cosmos scope
predicates (cosmos/scope.prelude): a lit room vs a dark one, visibility of an
item on a supporter, and a held light source, on Frotz."""

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

WORLD = (
    'room lit_room\n'
    '    name "Lit Room"\n'
    '    lit true\n'
    'thing table of supporter in lit_room\n'
    '    name "table"\n'
    'thing book in table\n'
    '    name "book"\n'
    'thing rock in lit_room\n'
    '    name "rock"\n'
    'room dark_room\n'
    '    name "Dark Room"\n'
    '    lit false\n'  # rooms are lit by default; this one opts out
    'thing lamp in player\n'
    '    name "lamp"\n'
    '    lit false\n'
)


def _scope_story():
    world = analyze(cosmos.combined_program(parse(WORLD)))
    gmap = _globals_map(world)
    actions = _action_numbers(world)
    layout = build_layout(world, react_objects=_react_objects(world, actions))
    pool = StringPool()
    _main, routines, registry = build_routines(world, gmap, layout, pool)
    react = gen_react_routines(world, actions, registry)

    obj = layout.obj_number
    lit_attr = layout.attr_number["lit"]
    drive = a.Routine("__main__", nlocals=0)

    def setg(name, value):
        drive.op("store", a.Const(gmap[name]), a.Const(value))

    def report(label, routine, *args):
        drive.op("print", text=label)
        drive.op("call_vs", a.RoutineRef(routine), *[a.Const(x) for x in args],
                 store=a.Variable(a.STACK))
        drive.op("print_num", a.Variable(a.STACK))
        drive.op("new_line")

    setg("player", obj["player"])
    setg("here", obj["lit_room"])
    report("lit is_lit: ", "blk_is_lit")
    report("book visible: ", "blk_visible", obj["book"])  # on a supporter
    report("rock visible: ", "blk_visible", obj["rock"])
    setg("here", obj["dark_room"])
    report("dark is_lit: ", "blk_is_lit")
    report("rock visible in dark: ", "blk_visible", obj["rock"])
    drive.op("set_attr", a.Const(obj["lamp"]), a.Const(lit_attr))  # light the held lamp
    report("dark with lit lamp is_lit: ", "blk_is_lit")
    drive.op("rfalse")

    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vn", a.RoutineRef("__main__"))
    entry.op("quit")
    return build_story(world, entry, [drive] + routines + react + [gen_schedule_tick(world, gmap)]
                       + gen_topic_helpers(layout), layout=layout, string_pool=pool)


def test_scope_story_compiles():
    assert _scope_story()[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_scope_and_light_on_frotz(tmp_path):
    story = tmp_path / "scope.z5"
    story.write_bytes(_scope_story())
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "lit is_lit: 1" in out
    assert "book visible: 1" in out  # item on a supporter, in a lit room
    assert "rock visible: 1" in out
    assert "dark is_lit: 0" in out
    assert "rock visible in dark: 0" in out
    assert "dark with lit lamp is_lit: 1" in out  # held light source


def test_move_to_scope_seeds_the_backstage_room():
    # A field report: `move x to scope` failed with "unknown name 'scope'"
    # when nothing was declared `in scope`, because the backstage room was
    # seeded only by a placement. A move-to-scope now seeds it too, so an
    # object revealed into scope at run time (the frisk idiom) is reachable.
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\nsummon.extendedverbs\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing corpse in hall\n    name "corpse"\n    words corpse\n'
        '    on search\n'
        '        move locket to scope\n'
        '        say "You turn out a silver locket."\n'
        'thing locket in corpse\n    name "silver locket"\n    words locket\n'
    )
    world = analyze(cosmos.combined_program(parse(game)))
    assert "scope" in world.objects        # the move-to-scope seeded it
    story = generate(world)
    io = CaptureIO(script=["search corpse", "take locket"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "Got it." in io.text.split("take locket")[-1]  # reachable via scope


def test_no_scope_use_seeds_nothing():
    from arcturus.parser import parse
    from arcturus.sema import analyze
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing rock in hall\n    name "rock"\n    words rock\n'
    )
    world = analyze(cosmos.combined_program(parse(game)))
    assert "scope" not in world.objects     # no placement, no move: no backstage
