# test_wake.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""WAKE in the extendedverbs granule (auraes's report, 2026-10-24: the verb
was missing from the extended set). WAKE alone or on yourself is the idle
report; on anyone or anything else it declines; a character's own
`on wake` makes waking real; a slice without the family leaves it out."""

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


GAME = (
    '{summon}\n'
    'game\n    title "G"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing greta of character in hall\n    name "Greta"\n    named\n    words greta\n    feminine\n'
    'thing guard of character in hall\n    name "guard"\n    words guard\n'
    '    on wake\n        say "The guard jolts upright."\n'
    'thing lamp in hall\n    name "lamp"\n    words lamp\n'
)

SELF = "You are as awake as you are going to get."


def test_every_wake_phrasing_answers():
    out = _run(GAME.format(summon="summon.extendedverbs"), [
        "wake", "wake up", "awake", "awaken", "wake me", "wake up myself",
        "wake greta", "wake greta up", "wake up greta", "awaken greta",
        "wake lamp", "wake up lamp", "wake guard", "wake guard up"])
    parts = out.split(">")[1:]
    for i in range(6):
        assert SELF in parts[i], (i, parts[i])
    for i in range(6, 10):
        assert "Greta doesn't need waking." in parts[i], (i, parts[i])
    for i in (10, 11):
        assert "The lamp doesn't need waking." in parts[i], (i, parts[i])
    for i in (12, 13):
        assert "The guard jolts upright." in parts[i], (i, parts[i])
        assert "need waking" not in parts[i]


def test_a_slice_without_wake_leaves_it_out():
    out = _run(GAME.replace('    on wake\n        say "The guard jolts upright."\n', '')
               .format(summon="summon.extendedverbs dig"), ["wake"])
    assert SELF not in out
