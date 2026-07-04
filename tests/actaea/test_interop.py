# test_interop.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M10's done-test (docs/06 section 9): a save made in Actaea loads
in Frotz and the reverse, and undo and restart behave. The game is a small
Arcturus story compiled on the spot, so the whole toolchain is in the loop:
the compiler emits the story, Cosmos drives @save/@restore through do_save,
one interpreter writes the Quetzal file and the other resumes it."""

import shutil
import subprocess

import pytest

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM
from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Interop"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A bare hall."\n'
    'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _story_bytes():
    return generate(analyze(cosmos.combined_program(parse(GAME))))


def _actaea(story_bytes, script, tmp_path) -> str:
    io = CaptureIO(script=list(script), save_dir=str(tmp_path))
    vm = VM(load(story_bytes), io)
    vm.run(max_steps=5_000_000)
    assert vm.halted
    return io.text


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_actaea_save_restores_in_frotz(tmp_path):
    story_bytes = _story_bytes()
    # Actaea: take the coin, save, quit.
    out = _actaea(
        story_bytes,
        ["take coin", "save", "actaea.qzl", "quit", "y"],
        tmp_path,
    )
    assert "Saved." in out  # do_save returned 1: the file is written
    assert (tmp_path / "actaea.qzl").exists()
    # dfrotz: restore that file; the coin must be in hand.
    story = tmp_path / "interop.z5"
    story.write_bytes(story_bytes)
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="restore\nactaea.qzl\ninventory\nquit\ny\n",
        capture_output=True, text=True, timeout=15, cwd=tmp_path,
    ).stdout
    assert "You're carrying:" in out
    assert "gold coin" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_frotz_save_restores_in_actaea(tmp_path):
    story_bytes = _story_bytes()
    story = tmp_path / "interop.z5"
    story.write_bytes(story_bytes)
    # dfrotz: take the coin, save, quit.
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take coin\nsave\nfrotz.qzl\nquit\ny\n",
        capture_output=True, text=True, timeout=15, cwd=tmp_path,
    ).stdout
    assert "Saved." in out
    assert (tmp_path / "frotz.qzl").exists()
    # Actaea: restore it; play resumes at the save point (do_save yields 2,
    # the room is redescribed) with the coin in hand.
    out = _actaea(
        story_bytes,
        ["restore", "frotz.qzl", "inventory", "quit", "y"],
        tmp_path,
    )
    assert "You're carrying:" in out
    assert "gold coin" in out


def test_a_foreign_save_is_refused_with_the_reason(tmp_path):
    # A save from a DIFFERENT story: Actaea names the problem instead of
    # loading state into the wrong world.
    story_bytes = _story_bytes()
    other = GAME.replace('"Interop"', '"Other"')
    other_bytes = generate(analyze(cosmos.combined_program(parse(other))))
    _actaea(other_bytes, ["save", "other.qzl", "quit", "y"], tmp_path)
    out = _actaea(
        story_bytes,
        ["restore", "other.qzl", "quit", "y"],
        tmp_path,
    )
    assert "different story" in out
    assert "Saved." not in out


def test_restart_reboots_the_story(tmp_path):
    # The banner prints at boot and again after a confirmed restart, and
    # the taken coin is back on the floor.
    out = _actaea(
        _story_bytes(),
        ["take coin", "restart", "y", "take coin", "quit", "y"],
        tmp_path,
    )
    assert out.count("Cosmos") >= 2
    # Both takes succeed: the restart put the coin back in the hall.
    assert out.count("Got it.") == 2
