# test_on_other_enter.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""ENTER reaches a THING's `on other` catch-all (a field report: it never
did). `enter` is two things sharing one name: on a room it is the arrival
event the loop fires (which a catch-all must never answer), on a thing it
is the ENTER verb, an ordinary consumable action. The react generator's
specific-handler path always respected that split; the catch-all's skip
list did not, and skipped the enter action on every object."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

THING = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing pod in hall\n    name "escape pod"\n    words pod, escape\n'
    '    on other\n        say "CAUGHT."\n'
)

ROOM = (
    'game\n    title "R"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north den\n'
    'room den\n    name "Den"\n    desc "A den."\n    south hall\n'
    '    on other\n        say "ROOM CATCH-ALL."\n'
)

_STORY = {}


def _run(cmds, game):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_enter_reaches_a_things_catch_all():
    # ENTER and its idioms (SIT ON, GET IN) land in `on other` exactly like
    # any other verb tried on the thing.
    out = _run(["enter pod", "sit on pod", "get in pod"], THING)
    assert out.count("CAUGHT.") == 3
    assert "can't get inside" not in out


def test_a_rooms_arrival_never_hits_its_catch_all():
    # Walking into a room with only an `on other`: the arrival event stays
    # a life-cycle hook, so no ROOM CATCH-ALL fires and the room describes.
    out = _run(["north"], ROOM)
    at = out.rindex(">north")
    after = out[at:]
    assert "ROOM CATCH-ALL." not in after
    assert "Den" in after
