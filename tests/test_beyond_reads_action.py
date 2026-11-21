# test_beyond_reads_action.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`action` inside a property block the gates speak through (2026-11-21):
the reach gate runs before any handler, so a `beyond block` that words
its refusal by action must read THIS turn's action. Two holes closed:
the any_action_read fold never looked inside property blocks (a game
reading action only in a beyond block never recorded it), and the action
was published only by the dispatcher, after the gates (the block read
the previous turn's)."""

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


HALL = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A tall hall."\n'
    'thing chandelier in hall\n    name "chandelier"\n    words chandelier\n'
    '    fixed\n'
    '    beyond block\n'
    '        if action is take\n'
    '            say "A yard above your fingers."\n'
    '        else\n'
    '            say "Far too high."\n'
)

TAKE = "A yard above your fingers."
OTHER = "Far too high."


def test_a_beyond_block_alone_reads_the_action():
    out = _run(HALL, ["take chandelier", "push chandelier"])
    assert out.count(TAKE) == 1 and out.count(OTHER) == 1
    assert out.index(TAKE) < out.index(OTHER)


def test_the_gate_never_reads_the_last_turns_action():
    src = HALL + (
        'thing rug in hall\n    name "rug"\n    words rug\n'
        '    on other\n'
        '        if action is push\n'
        '            say "The rug bunches."\n'
        '        else\n'
        '            say "Nothing."\n'
    )
    out = _run(src, ["push rug", "take chandelier", "take rug",
                     "push chandelier"])
    parts = out.split(">take chandelier")[1]
    assert parts.split(">")[0].strip() == TAKE
    tail = out.split(">push chandelier")[1]
    assert tail.split(">")[0].strip() == OTHER
