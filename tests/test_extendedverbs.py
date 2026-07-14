# test_extendedverbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The extendedverbs granule (B5.5b v1): the E-side verbs parse and speak their
defaults when summoned; SEARCH works on any object with a neutral default the
author overrides per object (a real search reveals by making something
reachable); an object overrides a default; ask addresses a living thing.
Unsummoned, the verbs are unknown. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

ROOMS = (
    'room cell\n    name "The Cell"\n    desc "A bare cell."\n'
    'thing chest of container in cell\n    name "iron chest"\n    words iron, chest\n    open\n'
    'thing coin in chest\n    name "gold coin"\n    words gold, coin\n'
    'thing pebble in cell\n    name "grey pebble"\n    words grey, pebble\n'
    'thing guard of character in cell\n    name "burly guard"\n    words burly, guard\n'
)
# The guard's `on rub` override is only valid when extendedverbs defines `rub`.
GUARD_OVERRIDE = '    on rub\n        say "The guard does not enjoy that."\n'
WITH = 'game\n    title "EV"\n    start cell\nsummon.extendedverbs\n' + ROOMS + GUARD_OVERRIDE
WITHOUT = 'game\n    title "EV"\n    start cell\n' + ROOMS


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_with_and_without_compile():
    assert _build(WITH)[0x00] == 5
    assert _build(WITHOUT)[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_extended_verbs_on_frotz(tmp_path):
    story = tmp_path / "e.z5"
    story.write_bytes(_build(WITH))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="search chest\ndig\nthink\nrub pebble\nask guard about pebble\nrub guard\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "nothing new to see here" in out  # search's cheeky neutral default
    assert "The ground keeps its secrets." in out  # an intransitive flavor verb (dig)
    assert "A fine idea. Nothing comes of it." in out  # think
    assert "You give the grey pebble a thorough buffing." in out  # rub default on an object
    # With no conversation granule, asking IS talking: the shared brush-off
    # (the richer flat defaults exist only in infocom_talking games).
    assert "doesn't seem up for a conversation" in out
    assert "The guard does not enjoy that." in out  # the guard's own on rub overrides


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_unsummoned_verbs_are_unknown_on_frotz(tmp_path):
    story = tmp_path / "e.z5"
    story.write_bytes(_build(WITHOUT))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="dig\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "keeps its secrets" not in out  # the dig verb is not in the build
    assert "don't add up" in out  # the standard unknown-verb reply


def test_search_works_on_any_object():
    # SEARCH's shape (a field report via Charles Moore Jr.: it only worked on
    # containers/supporters, not NPCs). Now any object is searchable: a
    # neutral default everywhere, the Schroedinger flavor for a shut
    # container, and an `on search` override for a real search. The override
    # reveals things by making them REACHABLE (moving a hidden key into the
    # room), not by naming what the player cannot touch.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\nsummon.extendedverbs\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing statue in hall\n    name "statue"\n    words statue\n'
        'thing box of container in hall\n    name "shut box"\n    words shut, box\n'
        'thing guard of character in hall\n    name "guard"\n    words guard\n'
        '    on search\n'
        '        move key to here\n'
        '        say "You frisk the guard and turn out a brass key."\n'
        'thing key in guard\n    name "brass key"\n    words key, brass\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["search statue", "search box",
                           "frisk guard", "take key"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "nothing new to see here" in out       # a plain object: neutral default
    assert "Schroedinger" in out                  # a shut container
    assert "turn out a brass key" in out           # the override reveals
    assert "Got it." in out.split("take key")[-1]  # the key is now reachable and taken
