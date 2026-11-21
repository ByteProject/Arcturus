# test_within_loop_room_of.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`for each x within chest` and `room_of(x)` (improvmonster's request,
2026-11-13, with EdwardianDuck's room_of as the shape). The loop visits
every object for which `x within chest` holds, at any depth, in object
order, and a body that moves things cannot derail it. room_of answers the
room around a thing however deeply nested, a room answers for itself, and
an object offstage or backstage answers nothing; a story's own room_of
still overrides the library's."""

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
        pass  # script exhausted at the next prompt
    return io.text


WORLD = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'room attic\n    name "Attic"\n    desc "Dusty."\n'
    'thing chest of container in hall\n    name "chest"\n    words chest\n    open\n'
    'thing tray of supporter in chest\n    name "tray"\n    words tray\n'
    'thing cup in tray\n    name "cup"\n    words cup\n'
    'thing box of container in chest\n    name "box"\n    words box\n    openable\n'
    'thing pearl in box\n    name "pearl"\n    words pearl\n'
    'thing lamp in hall\n    name "lamp"\n    words lamp\n'
    'thing ghost\n    name "ghost"\n    words ghost\n'
    'thing echo in scope\n    name "echo"\n    words echo\n    scenery\n'
    'thing coin in player\n    name "coin"\n    words coin\n'
)


def test_the_loop_reaches_every_depth_shut_boxes_included():
    src = WORLD + (
        'verb "sweep"\n    sweep\n'
        'on sweep\n'
        '    for each x within chest\n'
        '        say "- ${x}"\n'
    )
    out = _run(src, ["sweep"])
    for name in ("tray", "cup", "box", "pearl"):
        assert f"- {name}" in out
    assert "- lamp" not in out and "- chest" not in out


def test_the_body_may_move_what_it_visits():
    src = WORLD + (
        'verb "empty"\n    empty\n'
        'on empty\n'
        '    for each x within chest\n'
        '        move x to hall\n'
        '    let n = 0\n'
        '    for each y within chest\n'
        '        change n to n + 1\n'
        '    say "Left in the chest: ${n}."\n'
    )
    out = _run(src, ["empty", "look"])
    assert "Left in the chest: 0." in out


def test_within_here_includes_the_player_and_what_they_carry():
    src = WORLD + (
        'verb "census"\n    census\n'
        'on census\n'
        '    for each x within here\n'
        '        say "- ${x}"\n'
    )
    out = _run(src, ["census"])
    assert "- coin" in out and "- lamp" in out and "- pearl" in out
    assert "- ghost" not in out and "- echo" not in out


def test_room_of_answers_the_room_around_anything():
    src = WORLD + (
        'verb "where"\n    where noun\n'
        'on where\n'
        '    let r = room_of(noun)\n'
        '    if r is nothing\n'
        '        say "${The noun} is nowhere."\n'
        '    else\n'
        '        say "${The noun} is in ${r}."\n'
        'verb "probe"\n    probe\n'
        'on probe\n'
        '    say "pearl: ${room_of(pearl)}; hall: ${room_of(hall)}; ghost: ${room_of(ghost)}; echo: ${room_of(echo)}."\n'
    )
    out = _run(src, ["where cup", "where coin", "probe"])
    assert "The cup is in Hall." in out
    assert "The coin is in Hall." in out
    # nothing prints as an empty name, the language's rule
    assert "pearl: Hall; hall: Hall; ghost: ; echo: ." in out


def test_a_storys_own_room_of_still_wins():
    src = WORLD + (
        'block room_of(obj)\n    return attic\n'
        'verb "where"\n    where noun\n'
        'on where\n    say "${room_of(noun)}"\n'
    )
    out = _run(src, ["where cup"])
    assert "Attic" in out


def test_debug_warp_to_something_offstage_refuses():
    src = 'summon.debug\n' + WORLD
    out = _run(src, ["warp ghost"])
    assert "That is nowhere in the world." in out
