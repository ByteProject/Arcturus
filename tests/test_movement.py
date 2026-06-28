# test_movement.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Movement (B4.5e.2): the go verb, static exits, the can't-go default, and an
`on go <direction>` override (operand-pattern dispatch), driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Move Test"\n'
    '    start hall\n'
    'room hall\n'
    '    name "The Hall"\n'
    '    desc "A bare hall."\n'
    '    north study\n'
    '    on go south\n'
    '        say "The south door is locked."\n'
    '        stop\n'
    'room study\n'
    '    name "The Study"\n'
    '    desc "A book-lined study."\n'
    '    south hall\n'
)


def test_movement_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_movement_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    # north -> study; south -> back to hall; south -> the override; east -> no exit.
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="north\nsouth\nsouth\neast\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "The Study" in out  # walked north through a static exit
    assert "The south door is locked." in out  # on go south override fired
    assert "You can't go that way." in out  # east has no exit
    assert out.count("The Hall") >= 2  # started in the hall and walked back
