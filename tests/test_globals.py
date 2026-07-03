# test_globals.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The declaration trio (docs/01 section 4): `flag` (boolean state, starts
false, only ever true/false), `counter` (a number with ++ and --, starts 0),
and `global` (the general drawer: numbers, object references, and strings,
which hold their packed address and print as text)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "G"\n    start r\n'
    "flag lamp_lit\n"
    "flag doomed = true\n"
    "counter pushes\n"
    "counter lives = 3\n"
    'global motto = "Per aspera ad astra."\n'
    "global favorite = lamp\n"
    'room r\n    name "R"\n    desc "A room."\n'
    'thing lamp in r\n    name "lamp"\n    words lamp\n'
    'verb "probe"\n    probe\n'
    "on probe\n"
    "    pushes++\n"
    "    pushes++\n"
    "    lives--\n"
    "    change lamp_lit to true\n"
    '    say "p ${pushes} l ${lives} lit ${lamp_lit} doomed ${doomed}"\n'
    '    say "${motto}"\n'
    '    say "fav: ${the favorite}"\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "g.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_trio_end_to_end(tmp_path):
    out = _play(tmp_path, GAME, "probe\n")
    assert "p 2 l 2 lit 1 doomed 1" in out
    assert "Per aspera ad astra." in out
    assert "fav: the lamp" in out


def test_flag_rejects_numbers():
    src = GAME.replace("    change lamp_lit to true\n", "    change lamp_lit to 3\n")
    with pytest.raises(ArcError, match="takes true or false"):
        analyze(cosmos.combined_program(parse(src)))


def test_bump_needs_a_counter():
    src = GAME.replace("    pushes++\n    pushes++\n", "    doomed++\n")
    with pytest.raises(ArcError, match="needs a counter"):
        analyze(cosmos.combined_program(parse(src)))


def test_flag_initializer_must_be_boolean():
    src = GAME.replace("flag doomed = true", "flag doomed = 7")
    with pytest.raises(ArcError, match="starts true or false"):
        analyze(cosmos.combined_program(parse(src)))


def test_counter_initializer_must_be_number():
    src = GAME.replace("counter lives = 3", "counter lives = true")
    with pytest.raises(ArcError, match="starts at a number"):
        analyze(cosmos.combined_program(parse(src)))
