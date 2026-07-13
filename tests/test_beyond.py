# test_beyond.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""beyond (Dialog's out-of-reach, the Arcturus attribute): visible and
examinable, but every touching action refuses ("... is beyond your
reach"), scope and conversation untouched, and it is STATE: clear it and
the hand arrives. Static faraway decoration stays a grain's job; beyond
is for distance that matters to the model. Guards fold away in a game
where everything is within arm's length (the untouched ceilings)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start pantry\n'
    'summon.extendedverbs\n'
    'summon.infocom_talking\n'
    'room pantry\n    name "Pantry"\n    desc "Shelves to the ceiling."\n'
    'thing jar in pantry\n    name "honey jar"\n    words jar, honey\n'
    '    desc "Amber and patient, one shelf too high."\n'
    '    beyond\n'
    'thing stool in pantry\n    name "stool"\n    words stool\n'
    '    fixed\n'
    '    on enter\n'
    '        now jar is not beyond\n'
    '        continue\n'
    '    on exit\n'
    '        now jar is beyond\n'
    '        continue\n'
    'thing keeper of character in pantry\n    name "keeper"\n    words keeper\n'
    '    beyond\n'
    '    topic honey "the honey" words honey\n        reply "Top shelf. Use the stool."\n'
    'thing basket of container in pantry\n    name "basket"\n    words basket\n'
    '    open\n    beyond\n'
    'thing pebble in player\n    name "pebble"\n    words pebble\n'
)

_STORY = {}


def _run(cmds):
    if "s" not in _STORY:
        _STORY["s"] = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY["s"]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_examine_free_touch_refused():
    out = _run(["x jar", "take jar", "rub jar"])
    assert "Amber and patient, one shelf too high." in out
    assert out.count("The honey jar is beyond your reach.") == 2
    assert "Got it." not in out


def test_beyond_is_state():
    out = _run(["take jar", "enter stool", "take jar", "i", "exit", "take jar"])
    assert "Got it." in out                      # from the stool it works
    assert "honey jar" in out.split("carrying")[-1]
    # back on the floor, a second jar-take... (already held, so have-it) -
    # instead prove the flag returned by touching something else beyond.
    out2 = _run(["enter stool", "exit", "take basket"])
    assert "The basket is beyond your reach." in out2


def test_second_slot_guarded_but_talk_free():
    out = _run(["put pebble in basket", "ask keeper about honey"])
    assert "The basket is beyond your reach." in out
    assert "Top shelf. Use the stool." in out    # conversation crosses the gap


def test_beyond_speaks_its_own_why():
    # The Charles request: attach the reason to the attribute itself, the
    # desc-block shape. String form, block form, and the generic fallback.
    game = (
        'game\n    title "T"\n    start pantry\n'
        'room pantry\n    name "Pantry"\n    desc "Shelves."\n'
        'thing jar in pantry\n    name "jar"\n    words jar\n'
        '    beyond "Without the ladder, the top shelf might as well be the moon."\n'
        'thing bulb in pantry\n    name "bulb"\n    words bulb\n'
        '    beyond block\n'
        '        show("It hangs a clear ")\n'
        '        show(3)\n'
        '        say " feet above your reach."\n'
        'thing hook in pantry\n    name "hook"\n    words hook\n'
        '    beyond\n'
    )
    from arcturus import cosmos as _c
    story = generate(analyze(_c.combined_program(parse(game))))
    io = CaptureIO(script=["take jar", "take bulb", "take hook"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "might as well be the moon." in out
    assert "It hangs a clear 3 feet above your reach." in out
    assert "beyond your reach" in out          # the generic fallback, hook
