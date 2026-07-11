# test_appearance.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The appearance property: the paragraph an object ALWAYS owns in a room
description, replacing its listing line (Inform's describe, Dialog's
(appearance $)). Unlike intro it never expires with `moved`; a computed
block words it by state; hidden/concealed still suppress; a game with no
appearance anywhere keeps the original describe_room, byte-identical
(any_appearance, proven by the untouched ceilings)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "A"\n    start shop\n'
    'room shop\n    name "Shop"\n    desc "Dusty."\n'
    'thing keeper of character in shop\n    name "keeper"\n'
    '    scenery\n    angry false\n'
    '    appearance block\n'
    '        if keeper is angry\n'
    '            say "The keeper glowers at you."\n'
    '        else\n'
    '            say "The keeper is sweeping the floor."\n'
    'thing broom in shop\n    name "broom"\n'
    '    appearance "A worn broom leans against the wall."\n'
    'verb "anger"\n    anger\n'
    'on anger\n    now keeper is angry\n    say "Insulted."\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, cmds):
    return subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input=cmds, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_appearance_owns_the_paragraph_permanently(tmp_path):
    story = tmp_path / "a.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "take broom\ndrop broom\nlook\n")
    # after a take and a drop, the paragraph is still the appearance (the
    # intro rule would have expired with `moved`), and no listing line runs
    last = out.split("Down it goes.")[-1]
    assert "A worn broom leans against the wall." in last
    assert "You can see a broom here." not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_computed_appearance_follows_state(tmp_path):
    story = tmp_path / "a.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "anger\nlook\n")
    assert "The keeper is sweeping the floor." in out   # the opening description
    assert "The keeper glowers at you." in out          # after the state change
    assert "You can see the keeper here." not in out    # never the listing line
