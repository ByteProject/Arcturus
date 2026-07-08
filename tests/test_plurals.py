# test_plurals.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The plurals granule (summon.plurals): group words (`plural coins`)
and THEM. (Noun lists are core, tested in test_chaining.py.) Every swept
item is a full turn, the same rule as chaining and TAKE ALL."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    "summon.plurals\n"
    'game\n    title "P"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    "    south hall\n"
    'thing gold in hall\n    name "gold coin"\n    words gold, coin\n'
    "    plural coins\n"
    'thing silver in hall\n    name "silver coin"\n    words silver, coin\n'
    "    plural coins\n"
    'thing lamp in hall\n    name "brass lamp"\n    words lamp\n'
    'thing box in hall\n    name "wooden box"\n    words box\n'
    'verb "clock"\n    clock\n'
    "on clock\n"
    "    change meta_turn to 1\n"
    '    say "Turns: ${turns}."\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_group_word_sweeps(tmp_path):
    # "take coins" acts on every coin, one turn each; the lamp is untouched.
    out = _play(tmp_path, GAME, "take coins\nclock\ni\n")
    assert "gold coin: Got it." in out
    assert "silver coin: Got it." in out
    assert "brass lamp:" not in out
    assert "Turns: 2." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_them_replays_the_group(tmp_path):
    out = _play(tmp_path, GAME, "take coins\ndrop them\ni\n")
    assert "gold coin: Down it goes." in out
    assert "silver coin: Down it goes." in out
    assert "precisely nothing" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_list_and_chain_coexist(tmp_path):
    # A verb after the chain word still chains; a noun borrows. Both on one
    # line: the sweep runs, then the move.
    out = _play(tmp_path, GAME, "take coins and go north\n")
    assert "gold coin: Got it." in out
    assert "Yard" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_singular_word_still_asks(tmp_path):
    # "coin" is words-vocabulary on both coins, not a group word: the tie
    # still asks, and the answer still resolves.
    out = _play(tmp_path, GAME, "take coin\ngold\ni\n")
    assert "Which do you mean, the gold coin or the silver coin?" in out
    assert "gold coin" in out.rsplit("You're carrying:", 1)[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_group_word_with_one_left_binds_singular(tmp_path):
    # With one coin gone, "coins" matches a single object: no sweep, no ask,
    # the plain take.
    out = _play(tmp_path, GAME, "take gold coin\nn\ndrop gold coin\ns\ntake coins\ni\n")
    assert "silver coin" in out.rsplit("You're carrying:", 1)[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_them_with_no_group_is_honest(tmp_path):
    out = _play(tmp_path, GAME, "drop them\n")
    assert "You see nothing of the sort here." in out


NO_GRANULE = (
    'game\n    title "N"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp\n'
    'thing box in hall\n    name "wooden box"\n    words box\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_without_granule_group_words_are_unknown(tmp_path):
    # Unsummoned, a group word is not vocabulary: the word is named back,
    # which tells the player it is not a word this story uses. (Noun lists
    # are core and tested with chaining, not here.)
    out = _play(tmp_path, NO_GRANULE, "take coins\n")
    assert 'know the word "coins"' in out
