# test_enter_redirect.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`on enter` means two things that share one action name: on a ROOM it is the
arrival event (every hook fires, results ignored, fired by fire_enter after a
walk), on a THING it is the ENTER verb, an ordinary consumable action. Before
the fix a thing's `on enter` was compiled with the event semantics, so its
consume was thrown away and the default refusal leaked after it: a scenery
shack redirecting ENTER into a teleport printed its prose, moved the player,
and then added "You can't get inside the shack." (the field report)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hallway\n'
    'room hallway\n    name "Hallway"\n    desc "A hallway."\n'
    '    north shack\n'
    'thing facade in hallway\n'
    '    name "shack"\n'
    '    words shack, hovel\n'
    '    desc "A rundown shack."\n'
    '    scenery\n'
    '    on enter\n'
    '        say "You step through the doorway."\n'
    '        teleport(shack)\n'
    'room shack\n'
    '    name "Shack"\n'
    '    desc "Inside the shack."\n'
    '    south hallway\n'
    '    on enter\n'
    '        say "ARRIVAL HOOK."\n'
    'thing crate in hallway\n'
    '    name "crate"\n    words crate\n'
)


def _play(cmds):
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(story, io).run(max_steps=30_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_a_things_on_enter_consumes_the_action():
    # The redirect runs, the player moves, and NO default refusal follows.
    text = _play(["enter shack"])
    assert "You step through the doorway." in text
    assert "Inside the shack." in text
    assert "can't get inside" not in text


def test_the_rooms_arrival_hook_still_fires_on_walking():
    text = _play(["north"])
    assert "ARRIVAL HOOK." in text
    assert "Inside the shack." in text


def test_the_default_enter_refusal_still_works():
    # A thing with no handler keeps the honest refusal.
    text = _play(["enter crate"])
    assert "You can't get inside the crate." in text
