# test_handlers.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Handler and block compilation (B4.5a): every handler and block becomes a
routine. A block call and a driven handler call run on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import assembler as a
from arcturus.codegen import StringPool, _globals_map, build_routines, build_story, generate
from arcturus.objects import build_layout
from arcturus.parser import parse
from arcturus.sema import analyze


def test_all_handlers_and_blocks_become_routines():
    world = analyze(parse(
        'block dbl(n)\n'
        '    return n * 2\n'
        'thing gem\n'
        '    name "gem"\n'
        '    on examine\n'
        '        say "ok"\n'
        'room cave\n'
        '    name "Cave"\n'
        '    on enter\n'
        '        say "entered"\n'
    ))
    layout = build_layout(world)
    main, routines, registry = build_routines(world, _globals_map(world), layout, StringPool())
    names = {r.name for r in routines}
    assert "blk_dbl" in names
    # examine on gem and enter on cave each registered a handler routine.
    events = {tuple(h.events): nm for h, nm in registry}
    assert ("examine",) in events
    assert ("enter",) in events


# -- end to end on Frotz ---------------------------------------------------

BLOCK_SRC = (
    'game\n'
    '    title "Blocks"\n'
    '    serial "260627"\n'
    '    start r\n'
    '\n'
    'block double(n)\n'
    '    return n * 2\n'
    '\n'
    'on start\n'
    '    say "double 5 is:"\n'
    '    say double(5)\n'
    '\n'
    'room r\n'
    '    name "Room"\n'
)


def _driven_handler_story(src, event, owner):
    world = analyze(parse(src))
    gmap = _globals_map(world)
    layout = build_layout(world)
    pool = StringPool()
    main, routines, registry = build_routines(world, gmap, layout, pool)
    name = next(nm for h, nm in registry if event in h.events and h.owner == owner)
    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vn", a.RoutineRef(name))  # drive the handler directly
    entry.op("quit")
    return build_story(world, entry, [main] + routines, layout=layout, string_pool=pool)


HANDLER_SRC = (
    'thing gem\n'
    '    name "ruby gem"\n'
    '    on examine\n'
    '        say "It sparkles."\n'
    '        say self\n'
    'room cave\n'
    '    name "Cave"\n'
)


def test_block_call_compiles():
    data = generate(analyze(parse(BLOCK_SRC)))
    assert data[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_block_call_runs_on_frotz(tmp_path):
    story = tmp_path / "blk.z5"
    story.write_bytes(generate(analyze(parse(BLOCK_SRC))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "10" in out  # double(5)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_driven_handler_runs_on_frotz(tmp_path):
    story = tmp_path / "h.z5"
    story.write_bytes(_driven_handler_story(HANDLER_SRC, "examine", "gem"))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "It sparkles." in out
    assert "ruby gem" in out  # say self -> print_obj of the owning object
