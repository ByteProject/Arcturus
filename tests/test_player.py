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


def test_player_block_body_is_resolved_like_any_owner(tmp_path):
    # The field report (improvmonster): `if x is worn` inside a player.desc
    # block died in codegen with "unknown name 'worn'". The player is
    # seeded, not declared, and its augmentation bodies skipped sema's
    # resolution pass: no is-test resolution, and typos there escaped sema
    # entirely. They resolve like any owner's members now.
    import shutil
    import subprocess
    src = (
        'game\n    title "W"\n    start den\n'
        'room den\n    name "Den"\n    desc "Cosy."\n'
        'thing hat in player\n    name "hat"\n    wearable\n    worn\n'
        'player.desc block\n'
        '    show("A fine figure. ")\n'
        '    for each x in player\n'
        '        if x is worn\n'
        '            show("Wearing ${a x}")\n'
        '    say "."\n'
    )
    story_bytes = generate(analyze(cosmos.combined_program(parse(src))))
    frotz = shutil.which("dfrotz") or shutil.which("frotz")
    if frotz:
        story = tmp_path / "w.z5"
        story.write_bytes(story_bytes)
        out = subprocess.run(
            [frotz, "-p", "-w", "80", str(story)],
            input="x me\n", capture_output=True, text=True, timeout=15,
        ).stdout
        assert "Wearing a hat." in out
    # and a typo in a player block is now a sema error, not a codegen one
    from arcturus.errors import ArcError
    bad = src.replace("if x is worn", "if x is wornn")
    with pytest.raises(ArcError):
        analyze(cosmos.combined_program(parse(bad)))
