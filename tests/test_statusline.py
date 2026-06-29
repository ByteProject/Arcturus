# test_statusline.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The statusline granule (B5.5d): when summoned, a status bar is painted in the
upper window before each prompt, showing the room on the left and score/moves on
the right, updating every turn. Unsummoned, there is no bar. Driven on Frotz
(dumb-mode frotz reconstructs the upper window, so the content is checkable)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

ROOMS = (
    'room hall\n    name "The Hall"\n    desc "A long hall."\n    east garden\n'
    'room garden\n    name "The Garden"\n    desc "Grass."\n    west hall\n'
)
WITH = 'game\n    title "SL"\n    start hall\nsummon.statusline\n' + ROOMS
WITHOUT = 'game\n    title "SL"\n    start hall\n' + ROOMS


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_with_and_without_compile():
    assert _build(WITH)[0x00] == 5
    assert _build(WITHOUT)[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_statusline_paints_and_updates_on_frotz(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(WITH))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="east\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Score:" in out and "Moves:" in out  # the bar is painted
    assert "The Hall" in out and "The Garden" in out  # the room shows in the bar
    assert "Moves: 1" in out  # the move count advances after a turn


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_without_summon_has_no_bar_on_frotz(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(WITHOUT))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="east\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Score:" not in out
    assert "Moves:" not in out
