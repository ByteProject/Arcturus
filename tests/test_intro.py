# test_intro.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The intro property (B5): an object shows its `intro` text in a room
description while it sits untouched in place, and reverts to the plain listing
once it has moved. A static object keeps its intro forever. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Intro Test"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A bare hall."\n'
    'thing torch in hall\n    name "guttering torch"\n    words guttering, torch\n'
    '    intro "A guttering torch is wedged into a wall bracket."\n'
    'thing statue in hall\n    name "marble statue"\n    words marble, statue\n'
    '    fixed\n    intro "A marble statue dominates the room."\n'
)


def test_intro_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_intro_until_moved_on_frotz(tmp_path):
    story = tmp_path / "i.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="take torch\ndrop torch\nlook\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    # Up front, both show their intro, not the plain listing.
    opening = out.split(">")[0]
    assert "A guttering torch is wedged into a wall bracket." in opening
    assert "You can see a guttering torch here." not in opening
    # After the torch has moved, the final look lists it plainly,
    final_look = out.rsplit("Down it goes.", 1)[1]
    assert "You can see a guttering torch here." in final_look
    # but the static statue keeps its intro.
    assert "A marble statue dominates the room." in final_look
