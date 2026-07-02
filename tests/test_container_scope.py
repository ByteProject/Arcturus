# test_container_scope.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Container scope, layer 1: the noun matcher recurses into what the player can
see into. An object inside an open (or `clear`) container, or on a supporter, is
referable; inside a closed opaque container it is not. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

HEAD = (
    'game\n    title "S"\n    start cell\n'
    'room cell\n    name "The Cell"\n    desc "A cell."\n'
    'thing tray of supporter in cell\n    name "tin tray"\n    words tin, tray\n'
    'thing key in tray\n    name "brass key"\n    words brass, key\n'
)


def _game(box_state):
    return (
        HEAD
        + 'thing box of container in cell\n    name "wooden box"\n'
        '    words wooden, box\n    openable\n    ' + box_state + '\n'
        'thing coin in box\n    name "gold coin"\n    words gold, coin\n'
    )


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_all_compile():
    for state in ("open", "open false", "open false\n    clear"):
        assert _build(_game(state))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _examine(story, word):
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine " + word + "\n", capture_output=True, text=True, timeout=15,
    ).stdout
    return out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_open_container_contents_in_scope(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(_game("open")))
    assert "rewards a closer look" in _examine(story, "coin")  # matched, in scope


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_closed_opaque_container_hides_contents(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(_game("open false")))
    assert "You see nothing of the sort here." in _examine(story, "coin")  # out of scope


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_clear_container_shows_contents_when_closed(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(_game("open false\n    clear")))
    assert "rewards a closer look" in _examine(story, "coin")  # see-through: in scope


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_supporter_contents_in_scope(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(_game("open false")))  # the box is closed; the tray isn't
    assert "rewards a closer look" in _examine(story, "key")  # on a supporter: in scope


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_closed_box_remembers_and_redirects(tmp_path):
    # The knowledge layer: a never-seen coin in a closed box is unknown; once seen
    # (by opening), a closed box still lists it, and acting on it asks to open the
    # box rather than denying it exists.
    story = tmp_path / "s.z5"
    story.write_bytes(_build(_game("open false")))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take coin\nopen box\nclose box\nlook\ntake coin\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You see nothing of the sort here." in out  # never seen: unknown
    assert "Inside you find a gold coin." in out  # opening reveals it
    # Closed, but remembered: the knowledge model lists the contents the player
    # has seen, and the closed-openable qualifier sits alongside it.
    assert "wooden box (closed) (contains a gold coin)" in out
    assert "You'll have to open the wooden box first." in out  # known but shut away
