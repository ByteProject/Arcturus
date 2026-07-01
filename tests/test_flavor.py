# test_flavor.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Sensory and flavor verbs (B5), and the animate model: jump/wait/smell/push and
friends speak their defaults, talk distinguishes a living thing from an object
(the therapy line), and a person is animate via the person kind. Driven on
Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Flavor"\n    start cell\n'
    'room cell\n    name "The Cell"\n    desc "A bare cell."\n'
    'thing guard of character in cell\n    name "burly guard"\n    words burly, guard\n'
    'thing rock in cell\n    name "grey rock"\n    words grey, rock\n    fixed\n'
)


def test_flavor_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_flavor_and_animate_on_frotz(tmp_path):
    story = tmp_path / "f.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="jump\nwait\nsmell rock\npush rock\ntalk to guard\ntalk to rock\nattack guard\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You hop on the spot." in out  # jump
    assert "Time slips by." in out  # wait
    assert "The grey rock smells about as you'd expect." in out  # smell, with the noun
    assert "The grey rock holds firm." in out  # push default
    assert "The burly guard doesn't seem up for a conversation." in out  # talk to a person
    assert "talking to objects" in out  # talk to an object -> the animate guard
    assert "Hitting things rarely helps" in out  # attack default
