# test_light_watch.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The light watch (a field report: LIGHT LANTERN in the dark answered only
the lantern's own line, leaving the player to type LOOK for the room they
could suddenly see). A turn that lifts darkness without moving describes
the room; a turn that kills the light says where that leaves you; walking
through a doorway keeps its single description (arrive already speaks, the
watch must not double it). Always-lit games carry none of it (any_dark)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "D"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "Bright."\n    north cell\n'
    'room cell\n    name "Cell"\n    desc "Bare walls."\n    lit false\n'
    '    south hall\n'
    'thing lamp in hall\n    name "lamp"\n    words lamp\n    switchable\n'
    '    lit false\n'
    '    on switch_on\n        now self is lit\n        say "Click."\n'
    '    on switch_off\n        now self is not lit\n        say "Clack."\n'
)

_STORY = {}


def _run(cmds):
    if "s" not in _STORY:
        _STORY["s"] = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY["s"]), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_light_lifting_darkness_describes_the_room():
    out = _run(["take lamp", "north", "turn on lamp"])
    at = out.rindex("Click.")
    assert "Bare walls." in out[at:]


def test_light_dying_reports_the_darkness():
    out = _run(["take lamp", "north", "turn on lamp", "turn off lamp"])
    at = out.rindex("Clack.")
    assert "Pitch black" in out[at:]


def test_doorways_keep_a_single_description():
    # Walking into the dark cell reports the darkness ONCE; walking back
    # into the lit hall describes it ONCE (arrive speaks, the watch stays
    # quiet on a move).
    out = _run(["take lamp", "north", "south"])
    at = out.index(">north")
    mid = out.index(">south")
    assert out[at:mid].count("Pitch black") == 1
    assert out[mid:].count("Bright.") == 1
