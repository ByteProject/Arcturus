# test_loop.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The turn loop (B4.5e.1): banner, the opening event, the room description, the
prompt, and the look verb, driven on Frotz. Also guards the call-statement
discard, which must not underflow the stack."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Loop Test"\n'
    '    author "Tester"\n'
    '    start den\n'
    'on start\n'
    '    say "Welcome in."\n'
    'room den\n'
    '    name "The Den"\n'
    '    desc "A snug room with a low ceiling."\n'
    'thing cushion in den\n'
    '    name "red cushion"\n'
    '    words red, cushion\n'
)


def test_loop_game_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_turn_loop_runs_on_frotz(tmp_path):
    story = tmp_path / "loop.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="look\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Loop Test" in out  # the banner
    assert "Welcome in." in out  # on start fired
    assert "A snug room with a low ceiling." in out  # the room description
    assert "You can see a red cushion here." in out  # the contents listing
    assert out.count("The Den") >= 2  # described at start and again after look
    assert "underflow" not in out.lower()  # the discard does not corrupt the stack
