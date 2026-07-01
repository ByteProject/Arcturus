# test_functional.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Functional verbs with real state (B5): open/close and lock/unlock against the
openable and lockable attributes with a matching key, enter/exit a container,
insert into it, and give/show needing a living recipient. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Functional"\n    start vault\n'
    'room vault\n    name "The Vault"\n    desc "A small vault."\n'
    'thing chest of container in vault\n    name "iron chest"\n'
    '    words iron, chest\n    openable\n    lockable\n    locked\n    open false\n    unseal_with brasskey\n'
    'thing brasskey in vault\n    name "brass key"\n    words brass, key\n'
    'thing coin in vault\n    name "gold coin"\n    words gold, coin\n'
    'thing table of supporter in vault\n    name "stone table"\n    words stone, table\n'
    'thing guard of character in vault\n    name "burly guard"\n    words burly, guard\n'
)


def test_functional_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_functional_verbs_on_frotz(tmp_path):
    story = tmp_path / "f.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    script = (
        "open chest\n"  # locked -> refused
        "unlock chest with brass key\n"  # the right key
        "open chest\n"  # now opens
        "take coin\n"
        "give coin\n"  # no recipient: must not test_attr on object 0
        "give coin to guard\n"  # animate recipient refuses (coin in hand)
        "show coin to guard\n"
        "give coin to chest\n"  # not animate -> the only-animate nudge
        "insert coin in chest\n"  # into the open container
        "close chest\n"
        "lock chest with brass key\n"
        "exit\n"  # not inside anything
        "enter table\n"  # step onto the supporter
        "exit\n"  # and back down to the room
    )
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15,
    ).stdout
    assert "The iron chest is locked." in out  # open while locked
    assert "Unlocked." in out  # unlock with the right key
    assert "Open." in out  # then open
    assert "Done." in out  # insert / close steps confirm
    assert "Locked." in out  # relock
    assert "doesn't want" in out  # give to the guard (animate)
    assert "not really into that" in out  # show to the guard
    assert "therapy" in out  # give to a non-animate (the only-animate nudge)
    assert "To whom?" in out  # give with no recipient asks, does not crash
    assert "test_attr" not in out  # the object-0 attribute-test bug is gone
    assert "You aren't inside anything to leave." in out  # exit in the open


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_two_noun_binds_by_position_on_frotz(tmp_path):
    # The gift binds to the noun slot by position, never the recipient. Here the
    # coin has been seen and then sealed in the chest, so it is known but shut
    # away: "give coin to guard" matches the coin (not the guard), and the loop
    # answers "open it first" rather than running give against the guard.
    story = tmp_path / "f.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    script = (
        "unlock chest with brass key\n"
        "open chest\n"
        "take coin\n"
        "insert coin in chest\n"  # the coin is now in the chest (and seen)
        "close chest\n"  # shut away, but known
        "give coin to guard\n"  # binds the coin, not the guard
    )
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You'll have to open the iron chest first." in out  # the coin is shut away
    assert "doesn't want" not in out  # the guard was never treated as the noun
