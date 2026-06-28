# test_paragraphs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Library-controlled paragraph breaks (B4 polish): the library inserts a blank
line between logical blocks - the opening text and the room, the description and
the contents, the contents and a daemon - so authors never place newlines. Driven
on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Para Test"\n'
    '    start den\n'
    'on start\n'
    '    say "Welcome in."\n'
    'room den\n'
    '    name "The Den"\n'
    '    desc "A snug room."\n'
    '    on each_turn\n'
    '        say "A clock ticks."\n'
    'thing cushion in den\n'
    '    name "red cushion"\n'
    '    words red, cushion\n'
)


def test_paragraphs_compile():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_paragraph_breaks_on_frotz(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="look\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    # A blank line separates the opening text from the room name,
    assert "Welcome in.\n\nThe Den" in out
    # the description from the contents,
    assert "A snug room.\n\nYou can see red cushion here." in out
    # and the contents from the each_turn daemon.
    assert "here.\n\nA clock ticks." in out
