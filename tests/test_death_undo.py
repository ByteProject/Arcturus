# test_death_undo.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""UNDO at the death prompt (a field report: its absence "is going to be
VERY unpopular with players", and Infocom, Inform, and Puny all offer it).
The game-over prompt now names UNDO, and answering it takes back the fatal
command through the checkpoint every turn already takes, resuming play as
if it were never typed. Worded in all three languages."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start ledge\n'
    'room ledge\n    name "Ledge"\n    desc "The drop yawns north."\n'
    '    north drop\n'
    'room drop\n    name "Falling"\n    desc "Briefly."\n'
    '    on enter\n'
    '        say "You step into empty air."\n'
    '        finish "You have died."\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))), io).run(
            max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_undo_at_death_resumes_before_the_fatal_command():
    out = _run(["north", "undo", "look"])
    assert "You have died." in out
    assert "UNDO the last command" in out    # the prompt offers it
    assert "Taken back." in out              # the undo landed
    # Alive again: the ledge redescribes after the undo AND answers the look.
    assert out.count("The drop yawns north.") >= 3
