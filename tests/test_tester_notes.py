# test_tester_notes.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Tester's notes (docs/01 chapter 14; improvmonster's request, 2026-10-21):
a line that opens with `*` is a comment for the author in a playtest
transcript. It is answered "Noted." and never parsed: no turn passes, no
parser error clutters the transcript, and AGAIN repeats the last real
command."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "N"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south hall\n'
    'verb "turncount"\n    turncount meta\n'
    'on turncount\n    say "turns: ${turns}"\n'
)


def _run(cmds, src=GAME):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_a_star_line_is_noted_and_costs_nothing():
    out = _run(["north", "* the yard needs more", "*typo", "again", "turncount"])
    notes = out.split(">* the yard needs more")[1].split(">")[0]
    assert "Noted." in notes and "add up" not in notes
    assert "Noted." in out.split(">*typo")[1].split(">")[0]
    assert "no exit" in out.split(">again")[1].split(">")[0].lower()   # AGAIN is the NORTH
    assert "turns: 2" in out.split(">turncount")[1]


def test_the_packs_word_the_answer():
    de = _run(["* notiz"], 'summon.language "german"\n' + GAME)
    assert "Notiert." in de
    es = _run(["* nota"], 'summon.language "spanish"\n' + GAME)
    assert "Anotado." in es
