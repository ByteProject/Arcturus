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


def test_teleport_lands_inside_an_enterable_in_one_turn():
    # teleport(dest) with a container or supporter destination (Charles
    # Moore Jr.'s request, 2026-09-11): the player lands inside it, here
    # becomes its room, and the arrival runs once, no gap turn. A closed
    # lid does not refuse: teleport is the author's word.
    from arcturus import cosmos as _c
    from arcturus.codegen import generate as _g
    from arcturus.parser import parse as _p
    from arcturus.sema import analyze as _a
    from actaea.loader import load as _l
    from actaea.vm import VM as _VM
    game = (
        'game\n    title "W"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'room vault\n    name "Vault"\n    desc "A vault."\n'
        'thing crate of container in vault\n    name "pine crate"\n'
        '    words crate\n    openable\n    open false\n'
        'thing bench of supporter in vault\n    name "bench"\n    words bench\n'
        'verb "warpbox"\n    warpbox\n'
        'on warpbox\n    teleport(crate)\n'
        'verb "warpbench"\n    warpbench\n'
        'on warpbench\n    teleport(bench)\n'
    )
    io = CaptureIO(script=["warpbox", "exit", "warpbench", "quit", "y"])
    try:
        _VM(_l(_g(_a(_c.combined_program(_p(game))))), io).run(
            max_steps=30_000_000)
    except IndexError:
        pass
    assert "Vault (in the pine crate)" in io.text
    assert "You get out of the pine crate." in io.text
    assert "Vault (on the bench)" in io.text
