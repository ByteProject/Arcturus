# test_metaverbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The unrecognized-verb reply and the quit meta verb (B4 polish): an unknown
verb gets a reply instead of being ignored, and quit ends the session. Driven on
Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Meta Test"\n'
    '    start room1\n'
    'room room1\n'
    '    name "A Room"\n'
    '    desc "Nothing special."\n'
)


def test_metaverbs_compile():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_unknown_verb_and_quit_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="frobnicate\nquit\ny\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "That's not a verb I recognise." in out  # unknown verb gets a reply
    assert "Are you sure you want to quit?" in out  # quit asks for confirmation
    assert "Thanks for playing." in out  # confirmed quit says the farewell


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_quit_can_be_cancelled_on_frotz(tmp_path):
    story = tmp_path / "m2.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="quit\nn\nlook\n",  # decline, keep playing
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Are you sure you want to quit?" in out
    assert "Thanks for playing." not in out  # declined - no farewell
    assert out.count("A Room") >= 2  # still playing: look re-describes
