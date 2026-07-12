# test_within.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The `within` operator (a field request: Inform's IndirectlyContains):
`coin within player` is true anywhere in the tree, however nested, so a
coin in a purse in a bucket the player holds still counts as his. Total
like the direct tests (nothing within x is false), an ordinary Cosmos
walk underneath, and DCE'd from a game that never asks."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    'thing bucket of container in player\n    name "bucket"\n    words bucket\n'
    '    open\n'
    'thing purse of container in bucket\n    name "purse"\n    words purse\n'
    '    open\n'
    'thing coin in purse\n    name "coin"\n    words coin\n'
    'thing stone in yard\n    name "stone"\n    words stone\n'
    'verb "audit"\n    audit\n'
    'on audit\n'
    '    if coin within player\n'
    '        say "The coin is yours, however nested."\n'
    '    if coin within bucket\n'
    '        say "And within the bucket."\n'
    '    if not (coin within purse)\n'
    '        say "NEVER: it is directly in the purse."\n'
    '    if stone within player\n'
    '        say "NEVER: the stone lies in the yard."\n'
    '    if nothing within player\n'
    '        say "NEVER: nothing is nowhere."\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))), io).run(
            max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_within_walks_the_whole_tree():
    out = _run(["audit", "drop bucket", "audit"])
    # Before the drop: nested containment holds top to bottom.
    assert "The coin is yours, however nested." in out
    assert "And within the bucket." in out
    assert "NEVER" not in out
    # After dropping the bucket the coin leaves the player's tree but
    # stays within the bucket: exactly one of the two lines remains.
    assert out.count("And within the bucket.") == 2
    assert out.count("The coin is yours, however nested.") == 1
