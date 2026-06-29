# test_verbose_exits.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The verbose_exits granule (B5.5c): when summoned, a blocked direction lists the
room's live exits instead of the plain refusal; unsummoned, the default reply is
untouched and the backing routines are never emitted. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

# A hall with two exits (north and east), so a blocked south lists both.
HALL = (
    'room hall\n    name "The Hall"\n    desc "A long hall."\n'
    '    north library\n    east garden\n'
    'room library\n    name "The Library"\n    desc "Books."\n'
    'room garden\n    name "The Garden"\n    desc "Grass."\n'
)
WITH = 'game\n    title "VE"\n    start hall\nsummon.verbose_exits\n' + HALL
WITHOUT = 'game\n    title "VE"\n    start hall\n' + HALL


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_with_and_without_compile():
    assert _build(WITH)[0x00] == 5
    assert _build(WITHOUT)[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_verbose_exits_lists_exits_on_frotz(tmp_path):
    story = tmp_path / "v.z5"
    story.write_bytes(_build(WITH))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="south\n", capture_output=True, text=True, timeout=15,  # south is blocked
    ).stdout
    assert "You can only go north or east from here." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_without_summon_keeps_default_on_frotz(tmp_path):
    story = tmp_path / "v.z5"
    story.write_bytes(_build(WITHOUT))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="south\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "There's no exit in that direction." in out  # the unchanged default
    assert "You can only go" not in out
