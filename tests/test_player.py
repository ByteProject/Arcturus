# test_player.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The player object (docs/01 section 5a): the language layer's standard
self-words, the game's additive player.words, and the plain or computed
player.desc."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "P"\n    start deck\n'
    "player.words olivia, lund\n"
    "player.desc block\n"
    '    say "Olivia Lund, exobiologist."\n'
    'room deck\n    name "Deck"\n    desc "The bridge."\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_player_words_and_computed_desc_on_frotz(tmp_path):
    # The standard self-words come from the language layer (me, myself, self,
    # yourself, you); player.words ADDS the game's own on top; player.desc as a
    # block computes the description. And take-self answers its own message,
    # not the animate refusal.
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="x me\nx myself\nx yourself\nx olivia\nx lund\ntake me\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("Olivia Lund, exobiologist.") == 5
    assert "You keep a firm grip on yourself." in out


NO_DESC = 'game\n    title "N"\n    start r\nroom r\n    name "R"\n    desc "A room."\n'


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_examine_self_default_on_frotz(tmp_path):
    # With no player.desc, examining yourself gets the dedicated default, not
    # the object fallback ("Nothing about yourself rewards a closer look.").
    story = tmp_path / "n.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(NO_DESC)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="x me\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "admire ourselves" in out
    assert "rewards a closer look" not in out
