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
# The scored variant: `scoring` puts the score side back on the bar.
SCORED = 'game\n    title "SL"\n    start hall\n    scoring\nsummon.statusline\n' + ROOMS
WITHOUT = 'game\n    title "SL"\n    start hall\n' + ROOMS


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_with_and_without_compile():
    assert _build(WITH)[0x00] == 5
    assert _build(WITHOUT)[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, width):
    return subprocess.run(
        [_frotz(), "-p", "-w", str(width), str(story)],
        input="east\n", capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_statusline_scoreless_shows_only_moves(tmp_path):
    # A game that scores nothing gets no permanent "Score: 0": the bar
    # shows the move count alone (Stefan's ruling, 2026-07-04).
    story = tmp_path / "s.z5"
    story.write_bytes(_build(WITH))
    out = _run(story, 80)
    assert "Score:" not in out
    assert "The Hall" in out and "The Garden" in out  # the room shows in the bar
    assert "Moves: 1" in out  # the move count advances


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_statusline_full_on_a_wide_screen(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(SCORED))
    out = _run(story, 80)  # >= 54 columns: the full Score:/Moves: form
    assert "Score:" in out and "Moves:" in out
    assert "The Hall" in out and "The Garden" in out  # the room shows in the bar
    assert "Moves: 1" in out  # the move count advances


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_statusline_compact_on_a_narrow_screen(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(SCORED))
    out = _run(story, 40)  # a 40-column C64: the compact "Score: score/turns"
    assert "Score:" in out
    assert "5/1" in out  # the auto-scored garden paid on entry; one turn taken
    assert "Moves:" not in out  # the wide form is not used here


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_without_summon_has_no_bar_on_frotz(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(WITHOUT))
    assert "Score:" not in _run(story, 80)
