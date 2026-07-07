# test_spans_kind.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Spanning a room KIND (docs/01 section 5): `the_sun spans outside_room` puts
the object in scope in every room of that kind. Rooms are all known at compile
time, so the kind expands to its rooms in sema; the runtime spans table and
scope check are the same as for a list of named rooms. Also the marker kind: a
kind may be declared with no body, purely to tag its instances."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

# Two outside rooms (one the sun's tree home, one not) and an inside room. The
# marker kind outside_room has NO body: it exists only to tag its rooms.
GAME = (
    "game\n    title \"T\"\n    start meadow\n"
    "kind outside_room of room\n"
    "room meadow of outside_room\n    name \"Meadow\"\n    desc \"Grass.\"\n"
    "    lit\n    east hilltop\n    north cave\n"
    "room hilltop of outside_room\n    name \"Hilltop\"\n    desc \"A hill.\"\n"
    "    lit\n    west meadow\n"
    "room cave\n    name \"Cave\"\n    desc \"A hollow.\"\n    lit\n    south meadow\n"
    "thing the_sun\n    name \"sun\"\n    words sun\n    scenery\n"
    "    spans outside_room\n    desc \"It blazes overhead.\"\n"
)


def test_kind_span_expands_to_its_rooms():
    w = analyze(cosmos.combined_program(parse(GAME)))
    # The kind resolved to its rooms, in declaration order, deduplicated.
    assert w.objects["the_sun"].spans == ["meadow", "hilltop"]
    # A home-less spanning object is re-homed from the kind to the first room.
    assert w.objects["the_sun"].location == "meadow"


def _play(cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=cmds)
    try:
        VM(story, io).run(max_steps=5_000_000)
    except IndexError:
        pass  # script ran out at a prompt; io.text has what played
    return io.text


def _look_at_sun(cmds):
    out = _play(cmds + ["x sun"])
    at = out.rindex(">x sun")
    return out[at:at + 100].split("\n")[1]


def test_sun_in_scope_in_every_outside_room():
    # The sun's tree home (meadow) and another outside room (hilltop) both see it.
    assert _look_at_sun([]) == "It blazes overhead."
    assert _look_at_sun(["east"]) == "It blazes overhead."


def test_sun_not_in_scope_inside():
    # The cave is a plain room, not an outside_room: the sun is not in scope.
    assert "nothing of the sort" in _look_at_sun(["north"])


def test_marker_kind_needs_no_body():
    # The empty `kind outside_room of room` above compiled and ran; a marker kind
    # with no members is legal.
    w = analyze(cosmos.combined_program(parse(GAME)))
    assert "outside_room" in w.kinds


def test_subkind_rooms_are_included():
    # A room of a SUBKIND of the spanned kind counts: a beach is an outside_room.
    src = (
        "game\n    title \"T\"\n    start beach\n"
        "kind outside_room of room\n"
        "kind beach_room of outside_room\n"
        "room beach of beach_room\n    name \"Beach\"\n    desc \"Sand.\"\n    lit\n"
        "thing the_sun\n    name \"sun\"\n    words sun\n    scenery\n"
        "    spans outside_room\n    desc \"Bright.\"\n"
    )
    w = analyze(cosmos.combined_program(parse(src)))
    assert w.objects["the_sun"].spans == ["beach"]


def test_spanning_a_non_room_kind_is_an_error():
    src = (
        "game\n    title \"T\"\n    start r\n"
        "kind gadget of thing\n"
        "room r\n    name \"R\"\n    desc \"x\"\n"
        "thing widget of gadget in r\n    name \"w\"\n    words w\n"
        "thing beam in r\n    name \"beam\"\n    words beam\n    scenery\n"
        "    spans gadget\n"
    )
    with pytest.raises(ArcError, match="not a room kind"):
        analyze(cosmos.combined_program(parse(src)))


def test_spanning_a_kind_with_no_rooms_is_an_error():
    src = (
        "game\n    title \"T\"\n    start r\n"
        "kind outside_room of room\n"
        "room r\n    name \"R\"\n    desc \"x\"\n"
        "thing the_sun in r\n    name \"sun\"\n    words sun\n    scenery\n"
        "    spans outside_room\n"
    )
    with pytest.raises(ArcError, match="no rooms"):
        analyze(cosmos.combined_program(parse(src)))
