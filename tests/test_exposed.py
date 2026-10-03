# test_exposed.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""exposed (docs/01 chapter 3): a character's belongings stay private by
design (Charles Moore Jr.'s report, 2026-09-26, expecting Inform's
everything-in-scope); the visible ones are declared per item. In scope
while the holder is, examinable, named by EXAMINE on the character, and
TAKE refuses in the holder's name. Games exposing nothing are
byte-identical (the untouched ceilings)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "X"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing testy of character in hall\n    name "Testy"\n    named\n'
    '    desc "He likes to travel."\n    words testy\n'
    'thing passport in testy\n    name "passport"\n    desc "Stamped."\n'
    '    words passport\n    exposed\n'
    'thing hat in testy\n    name "felt hat"\n    words hat\n'
    '    wearable\n    worn\n    exposed\n'
    'thing wallet in testy\n    name "wallet"\n    words wallet\n'
)


def _run(cmds, src=GAME):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_exposed_belongings_are_seen_named_and_kept():
    out = _run(["examine testy", "examine passport", "take passport",
                "take hat", "examine wallet", "take wallet", "inventory"])
    assert "Testy is wearing a felt hat and carrying a passport." in out
    assert "Stamped." in out
    assert "Testy is holding it." in out
    assert "Testy is wearing it." in out
    assert "nothing of the sort" in out.split(">examine wallet")[1]   # private stays private
    assert "passport" not in out.split(">inventory")[1]


def test_examine_line_reads_each_half_alone():
    held_only = GAME.replace("    wearable\n    worn\n    exposed\n", "")
    assert "Testy is carrying a passport." in _run(["examine testy"], held_only)
    worn_only = GAME.replace('    words passport\n    exposed\n', '    words passport\n')
    assert "Testy is wearing a felt hat." in _run(["examine testy"], worn_only)


def test_exposed_leaves_scope_with_its_holder():
    src = GAME.replace('    desc "A hall."\n', '    desc "A hall."\n    north yard\n') + (
        'room yard\n    name "Yard"\n    desc "Open."\n    south hall\n'
    )
    out = _run(["north", "examine passport"], src)
    assert "nothing of the sort" in out.split(">examine passport")[1]
