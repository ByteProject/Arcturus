# test_foreach_move.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`for each` is move-safe for its own loop object (docs/01 section 8): the
next sibling is cached before the body runs, so emptying a container by
moving each child out cannot derail the walk. The field report: a bucket in
the player's hands, `for each x in self / move x to loc`, spun forever and
even swept the PLAYER into the iteration (the moved marble became the room's
first child, its sibling pointer aimed at the player, and the walk followed
it out of the bucket)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing bucket of container in player\n'
    '    name "bucket"\n    words bucket, pail\n    open\n'
    '    on empty self\n'
    '        let loc = parent_of(player)\n'
    '        for each x in self\n'
    '            show("OUT ${the x}. ")\n'
    '            move x to loc\n'
    '        say "You pour out the contents of the bucket."\n'
    'thing red_marble in bucket\n'
    '    name "red marble"\n    words red, marble\n'
    'thing blue_marble in bucket\n'
    '    name "blue marble"\n    words blue, marble\n'
    'verb "empty"\n'
    '    empty held\n'
)


def _play(cmds):
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(story, io).run(max_steps=5_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_emptying_a_container_terminates_and_moves_everything():
    text = _play(["empty bucket", "look"])
    assert "OUT the red marble." in text
    assert "OUT the blue marble." in text
    assert "You pour out the contents of the bucket." in text
    # The player was never swept into the bucket's iteration.
    assert "OUT yourself" not in text
    # Both marbles now lie in the hall.
    after = text[text.index(">look"):]
    assert "red marble" in after and "blue marble" in after


def test_emptying_twice_is_calm():
    text = _play(["empty bucket", "empty bucket"])
    assert text.count("You pour out the contents of the bucket.") == 2
    assert text.count("OUT") == 2  # nothing left the second time
