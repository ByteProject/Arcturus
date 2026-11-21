# test_nested_intro.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""An intro inside a holder (docs/01 chapter 7; Stefan's ruling
2026-11-21): a thing on a supporter or in a container the player can see
into speaks its unexpired intro in the room description, after its
holder's paragraph, and the listings leave it out while the room is told
(the holder's contents, the scenery line, the tail "with ... on it").
EXAMINE still names it; once taken, it lists as any thing. A game whose
intros all start in rooms is byte-identical (any_nested_intro)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_build(src)), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def _after(out, cmd, n=1):
    return out.split(">" + cmd)[n].split(">")[0]


STUDY = (
    'game\n    title "T"\n    start study\n'
    'room study\n    name "Study"\n    desc "Books everywhere."\n'
    'thing desk of supporter in study\n    name "desk"\n    words desk\n    scenery\n'
    'thing key in desk\n    name "brass key"\n    words key, >brass\n'
    '    intro "A brass key glints on the desk."\n'
    'thing table of supporter in study\n    name "table"\n    words table\n'
    'thing letter in table\n    name "letter"\n    words letter\n'
    '    intro "A sealed letter waits on the table."\n'
    'thing chest of container in study\n    name "chest"\n    words chest\n'
    '    openable\n    scenery\n'
    'thing ring in chest\n    name "ring"\n    words ring\n'
    '    intro "A silver ring lies in the chest."\n'
    'thing coin in study\n    name "coin"\n    words coin\n'
)


def test_an_intro_on_scenery_speaks():
    look = _after(_run(STUDY, ["look"]), "look")
    assert "A brass key glints on the desk." in look


def test_an_intro_on_a_listed_holder_speaks_and_leaves_its_listing():
    look = _after(_run(STUDY, ["look"]), "look")
    assert "A sealed letter waits on the table." in look
    assert "You can see a table and a coin here." in look
    assert "letter)" not in look


def test_a_shut_chest_keeps_its_intro_until_opened():
    out = _run(STUDY, ["look", "open chest", "look"])
    assert "silver ring" not in _after(out, "look", 1)
    assert "A silver ring lies in the chest." in _after(out, "look", 2)


def test_examine_still_names_it():
    out = _run(STUDY, ["examine table"])
    assert "On the table you can see a letter." in out


def test_once_taken_it_lists_as_any_thing():
    out = _run(STUDY, ["take letter", "put letter on table", "look"])
    look = _after(out, "look")
    assert "sealed letter waits" not in look
    assert "a table (on which is a letter)" in look


def test_the_scenery_line_leaves_it_out():
    src = 'constant scenery_contents = true\n' + STUDY + (
        'thing pen in desk\n    name "pen"\n    words pen\n')
    look = _after(_run(src, ["look"]), "look")
    assert "On the desk you can see a pen." in look
    assert "A brass key glints on the desk." in look
    assert look.index("On the desk you can see a pen.") < look.index("A brass key")


def test_intros_all_in_rooms_cost_nothing():
    plain = (
        'game\n    title "T"\n    start study\n'
        'room study\n    name "Study"\n    desc "Books."\n'
        'thing key in study\n    name "key"\n    words key\n'
        '    intro "A key lies here."\n'
    )
    from arcturus import lower
    from arcturus.sema import analyze as _an
    world = _an(cosmos.combined_program(parse(plain)))
    assert lower._any_nested_intro(world) == 0
    world = _an(cosmos.combined_program(parse(STUDY)))
    assert lower._any_nested_intro(world) == 1
