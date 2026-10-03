# test_anywhere.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`anywhere` on a verb (docs/01 chapter 12): the parser binds a noun that
names a real thing not in scope, the declarative face of the
reach_unscoped seam (Charles Moore Jr.'s ask, 2026-09-26, Inform's scope
token). The handler owns validity; AGAIN replays the reach; a game
without the marker is byte-identical (the untouched ceilings)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "A"\n    start yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    north barn\n'
    'room barn\n    name "Barn"\n    desc "A barn."\n    south yard\n'
    'thing drover of character in barn\n    name "drover"\n    words drover, man\n'
    'thing hat in barn\n    name "hat"\n    words hat\n'
    'verb "follow"\n    anywhere\n    follow noun\n'
    'verb "shout"\n    anywhere\n    shout noun\n'
    'on follow\n'
    '    if noun in here\n        say "${The noun} is right here."\n        stop\n'
    '    say "You follow ${the noun}."\n'
    '    teleport(parent_of(noun))\n'
    'on shout\n    say "You shout at ${the noun}."\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_anywhere_binds_a_thing_out_of_scope():
    out = _run(["take hat", "shout drover", "follow drover", "follow drover"])
    assert "nothing of the sort" in out.split(">shout")[0]   # ordinary verbs refuse
    assert "You shout at the drover." in out
    assert "You follow the drover." in out
    assert "The drover is right here." in out


def test_again_replays_the_reach():
    out = _run(["shout drover", "again"])
    assert out.count("You shout at the drover.") == 2


def test_unknown_words_still_refuse():
    out = _run(["shout xyzzyplugh"])
    assert "doesn't know the word" in out
