# test_way_family.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The way family (docs/01 chapter 8): the room graph, queryable from author
code. way_between(a, b) answers adjacency as TOPOLOGY (doors read through to
their far side whatever their state); way_toward(a, b) answers the first step
of a shortest walk, doors passing only where door_bars allows and rooms only
where path_admits allows. Absence is always no_way (-1), never 0, which stays
honest north. The path scratch (__pathbuf__) exists only in a program that
calls way_toward; everything else folds away, and the size gate holds every
example byte-identical."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

# A five-room map with a branch, a lockable door, and a one-way drop:
#   plaza -n- arcade -n- attic;  plaza -e- alley -n-(oak door)- cellar;
#   attic -down-> alley (no way back up).
MAP = (
    'game\n    title "W"\n    start plaza\n'
    'room plaza\n    name "Plaza"\n    desc "A plaza."\n'
    '    north arcade\n    east alley\n'
    'room arcade\n    name "Arcade"\n    desc "An arcade."\n'
    '    south plaza\n    north attic\n'
    'room attic\n    name "Attic"\n    desc "An attic."\n'
    '    south arcade\n    down alley\n'
    'room alley\n    name "Alley"\n    desc "An alley."\n'
    '    west plaza\n    north oak_door\n'
    'room cellar\n    name "Cellar"\n    desc "A cellar."\n    south oak_door\n'
    'thing oak_door of door in alley\n    name "oak door"\n'
    '    words oak, door\n    desc "Solid oak."\n    spans cellar\n    openable\n'
    'verb "probe" meta\n    probe\n'
    'on probe\n'
    '    say "b1:${way_between(plaza, arcade)} '
    'b2:${way_between(plaza, attic)} '
    'b3:${way_between(alley, cellar)}"\n'
    '    say "t1:${way_toward(plaza, attic)} '
    't2:${way_toward(plaza, cellar)} '
    't3:${way_toward(plaza, plaza)}"\n'
    'verb "unbar" meta\n    unbar\n'
    'on unbar\n'
    '    now oak_door is open\n'
    '    say "t4:${way_toward(plaza, cellar)} '
    't5:${way_toward(attic, alley)} '
    't6:${way_toward(alley, attic)}"\n'
)

# The same map with the curtain override: the door never bars.
CURTAIN = MAP + (
    'block door_bars(d)\n    return 0\n'
    'verb "veil" meta\n    veil\n'
    'on veil\n    say "v1:${way_toward(plaza, cellar)}"\n'
)

_STORY = {}


def _run(cmds, game=MAP):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_way_between_is_topology():
    out = _run(["probe"])
    # north is index 0; the shut door still reads through on the MAP.
    assert "b1:0" in out
    assert "b2:-1" in out  # not adjacent: no_way, never 0
    assert "b3:0" in out


def test_way_toward_walks_and_the_shut_door_bars():
    out = _run(["probe"])
    assert "t1:0" in out    # first step north toward the attic
    assert "t2:-1" in out   # the only route passes the shut oak door
    assert "t3:-1" in out   # a to a is the caller's case: no_way


def test_open_door_routes_and_one_way_edges_hold():
    out = _run(["probe", "unbar"])
    assert "t4:2" in out    # east: two steps via the alley beat four overland
    assert "t5:9" in out    # the drop: down, one step
    assert "t6:3" in out    # no way back up the drop: west around, three steps


def test_door_bars_is_a_seam():
    out = _run(["veil"], game=CURTAIN)
    # The override lets the shut door pass: the curtain case.
    assert "v1:2" in out
