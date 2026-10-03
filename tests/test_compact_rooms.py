# test_compact_rooms.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""constant compact_rooms = 1 (docs/01 chapter 13): the blank line above a
room title folds away (a line back on a 25-row screen, auraes's ask,
2026-09-21). Off by default and byte-identical then (the untouched
ceilings). Alongside: msg_done names what was put where."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

WORLD = (
    'room hall\n    name "Hall"\n    desc "Bare."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "Open."\n    south hall\n'
    'thing coin in hall\n    name "coin"\n    words coin\n'
    'thing box of container in hall\n    name "box"\n    words box\n    open\n'
    'thing altar of supporter in hall\n    name "altar"\n    words altar\n'
)


def _run(head, cmds):
    src = head + WORLD
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_default_keeps_the_blank_line_above_the_title():
    out = _run('game\n    title "C"\n    start hall\n', ["look", "north"])
    assert ">look\n\nHall\n" in out
    assert ">north\n\nYard\n" in out


def test_compact_rooms_drops_it():
    out = _run('constant compact_rooms = 1\ngame\n    title "C"\n    start hall\n',
               ["look", "north"])
    assert ">look\nHall\n" in out
    assert ">north\nYard\n" in out
    assert "\n\nHall" not in out.split(">look")[1].split(">north")[0]


def test_put_reports_name_the_thing_and_the_place():
    out = _run('game\n    title "C"\n    start hall\n',
               ["take coin", "put coin in box", "take coin", "put coin on altar"])
    assert "You put the coin in the box." in out
    assert "You put the coin on the altar." in out
    assert "Done." not in out


def test_switch_constants_take_true_and_false():
    # The language's own literals (Stefan's rule, 2026-10-03): a switch
    # written `constant compact_rooms = true` is on, `= false` is off, and
    # both fold exactly as the older numeric spelling did. The readers
    # used to accept a Number only, so `= true` compiled and did nothing.
    on = _run('constant compact_rooms = true\ngame\n    title "C"\n    start hall\n', ["look"])
    assert ">look\nHall\n" in on
    off = _run('constant compact_rooms = false\ngame\n    title "C"\n    start hall\n', ["look"])
    assert ">look\n\nHall\n" in off
