# test_plural_lines.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""auraes's report (2026-10-03): two lines lacked plural forms, and UNLOCK
on an unlocked, already-open chest spoke two contradicting lines."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_listen_to_a_plural_character_and_find_a_plural_thing():
    src = (
        'summon.extendedverbs\n'
        'summon.pathfinding\n'
        'game\n    title "P"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing twins of character in r\n    name "twins"\n    words twins\n'
        '    pluribus\n'
        'thing scissors in r\n    name "scissors"\n    words scissors\n'
        '    pluribus\n'
        'thing monk of character in r\n    name "monk"\n    words monk\n'
    )
    out = _run(src, ["listen to twins", "listen to monk", "find scissors"])
    assert "The twins are silent." in out
    assert "The monk is silent." in out
    assert "The scissors are right here." in out


def test_unlock_on_an_open_chest_speaks_once():
    src = (
        'game\n    title "U"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing chest of container in r\n    name "chest"\n    words chest\n'
        '    openable\n    open\n    lockable\n'
        'thing box of container in r\n    name "box"\n    words box\n'
        '    openable\n    open\n'
    )
    out = _run(src, ["unlock chest", "unlock box", "close chest", "unlock chest"])
    first = out.split(">unlock chest")[1].split(">")[0]
    assert "already open" in first and "skip the suspense" not in first
    second = out.split(">unlock box")[1].split(">")[0]
    assert "already open" in second and "needs unlocking" not in second
    third = out.split(">unlock chest")[2].split(">")[0]
    assert "skip the suspense and open it" in third     # shut and unlocked: opens
