# test_takeall.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The takeall granule (summon.takeall): TAKE ALL, DROP ALL, TAKE ALL FROM.
Every swept item is a full turn of its own (a deliberate departure from
Inform's one-turn ALL), undo takes back the whole sweep (one typed command),
and an empty or nonsensical ALL refuses, so a chained line stops."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    "summon.takeall\n"
    'game\n    title "A"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp\n'
    'thing box of container in hall\n    name "wooden box"\n    words box\n'
    "    openable\n    open false\n"
    'thing coin in box\n    name "gold coin"\n    words coin\n'
    'thing statue in hall\n    name "stone statue"\n    words statue\n'
    "    fixed\n"
    'thing hat in hall\n    name "felt hat"\n    words hat\n    wearable\n'
    'verb "clock"\n    clock\n'
    "on clock\n"
    "    change meta_turn to 1\n"
    '    say "Turns: ${turns}."\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "a.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_take_all_sweeps_and_counts_turns(tmp_path):
    # Three takeables (lamp, closed box, hat); the fixed statue is skipped
    # silently. Each item is a full turn: the counter moves per item.
    out = _play(tmp_path, GAME, "take all\nclock\ni\n")
    assert "brass lamp: Got it." in out
    assert "wooden box: Got it." in out
    assert "felt hat: Got it." in out
    assert "stone statue:" not in out  # the fixed statue is never attempted
    assert "Turns: 3." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_drop_all_keeps_worn(tmp_path):
    out = _play(tmp_path, GAME, "take all\nwear hat\ndrop all\ni\n")
    assert "brass lamp: Down it goes." in out
    assert "felt hat: Down it goes." not in out
    assert "(worn)" in out.rsplit("You're carrying:", 1)[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_take_all_from_container(tmp_path):
    # A shut source refuses honestly; open, its contents sweep out.
    out = _play(
        tmp_path, GAME,
        "take all from box\nopen box\ntake all from box\ni\n",
    )
    assert "The wooden box is shut." in out
    assert "gold coin: Got it." in out
    assert "gold coin" in out.rsplit("You're carrying:", 1)[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_all_with_other_verb_refuses(tmp_path):
    out = _play(tmp_path, GAME, "eat all\n")
    assert "One thing at a time." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_empty_sweep_refuses_and_stops_chain(tmp_path):
    # Second TAKE ALL finds nothing: it refuses, so the chained move dies.
    out = _play(tmp_path, GAME, "take all\ntake all and go north\nlook\n")
    assert "There's nothing here worth taking." in out
    assert "Yard" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_undo_takes_back_the_whole_sweep(tmp_path):
    # The sweep is one typed command: one undo rewinds all of it.
    out = _play(tmp_path, GAME, "take all\nundo\ni\n")
    assert "Taken back." in out
    assert "precisely nothing" in out.rsplit(">", 3)[1] or \
        "precisely nothing" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_take_all_then_chain_continues(tmp_path):
    # A successful sweep is not a refusal: the chained move still runs.
    out = _play(tmp_path, GAME, "take all and go north\n")
    assert "brass lamp: Got it." in out
    assert "Yard" in out


NO_GRANULE = (
    'game\n    title "N"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_without_granule_all_is_an_unknown_word(tmp_path):
    # Unsummoned, "all" is not in the dictionary and the hooks fold away:
    # the command falls into the ordinary can't-see refusal.
    out = _play(tmp_path, NO_GRANULE, "take all\n")
    assert "You see nothing of the sort here." in out
