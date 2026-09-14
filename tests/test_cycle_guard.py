# test_cycle_guard.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The tree never cycles (a field report, 2026-09-14: a player inside a
portable container could TAKE it, pocketing their own enclosure; and PUT
X IN X corrupted the interpreter's object tree outright). Two guards, one
principle: take_probe's why 8 refuses taking anything that encloses the
player (foresight runs the real exits first and lets the take continue),
and the movers refuse a thing entering itself or anything it contains."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start attic\n'
    'room attic\n    name "Attic"\n    desc "Dust."\n'
    'thing hamper of container in attic\n    name "wicker hamper"\n'
    '    words wicker, hamper\n    openable\n    open\n'
    'thing box of container in hamper\n    name "tin box"\n'
    '    words tin, box\n    open\n'
    'thing stool of supporter in attic\n    name "stool"\n    words stool\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_taking_the_enclosure_refuses_on_and_in():
    out = _run(["enter hamper", "take hamper", "exit",
                "sit on stool", "take stool", "i"])
    assert "You would have to get out of the wicker hamper first." in out
    assert "You would have to get off the stool first." in out
    assert "You take" not in out  # nothing was ever pocketed
    assert "precisely nothing" in out  # the inventory stays empty


def test_nothing_enters_itself_or_its_own_contents():
    out = _run(["put hamper in hamper", "put hamper in box",
                "put stool on stool"])
    # self, transitive (the box sits inside the hamper), and the
    # supporter wording; the last one seats no player, so the cycle
    # gate speaks, not the perch.
    assert out.count("You can't put the wicker hamper inside itself.") == 2
    assert "You can't put the stool on top of itself." in out


def test_foresight_exits_first_and_the_repairs_stack():
    game = "summon.foresight\n" + GAME
    out = _run(["enter hamper", "close hamper", "take hamper", "i"], game)
    # perch repair, then the lid repair inside the real exit, one turn
    at = out.index(">take hamper")
    tail = out[at:]
    assert "(getting out of the wicker hamper first)" in tail
    assert "(opening the wicker hamper first)" in tail
    assert "You take the wicker hamper with you." in tail
    assert "a wicker hamper" in out.split("You're carrying:")[-1]
