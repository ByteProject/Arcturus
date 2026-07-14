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
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

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


# A computed appearance that OPTS OUT (prints nothing, e.g. while the player
# rides the object) must leave no blank line behind it. The reported bug: the
# paragraph break was flushed before the block ran, so a silent block still
# emitted the break. Run on the bundled VM so it needs no external interpreter.
OPT_OUT = (
    'game\n    title "O"\n    start dune\n'
    'room dune\n    name "Dune"\n    desc "Heat over the sand."\n'
    'thing camel in dune\n    name "camel"\n    supporter\n'
    '    appearance block\n'
    '        if player is in self\n'
    '            return true\n'
    '        else\n'
    '            say "A bored camel chews his cud here."\n'
    'thing shell in dune\n    name "shell"\n'
)


def _vm_run(story, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_silent_appearance_leaves_no_blank_line():
    story = _build(OPT_OUT)
    # Off the camel: desc, one blank, the appearance, one blank, the shell.
    out = _vm_run(story, ["look"]).split(">look")[-1]
    assert "chews his cud" in out
    assert "Heat over the sand.\n\nA bored camel" in out
    assert "\n\n\n" not in out
    # On the camel: the appearance opts out, so NO orphan blank line sits where
    # its paragraph would have been. The bug produced "sand.\n\n\nYou can see".
    out = _vm_run(story, ["enter camel", "look"]).split(">look")[-1]
    assert "chews his cud" not in out
    assert "Heat over the sand.\n\nYou can see" in out
    assert "\n\n\n" not in out
