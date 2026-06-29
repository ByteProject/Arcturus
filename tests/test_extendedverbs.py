# test_extendedverbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The extendedverbs granule (B5.5b v1): the E-side verbs parse and speak their
defaults when summoned; search lists a container's contents; an object overrides
a default; ask addresses a living thing. Unsummoned, the verbs are unknown.
Driven on Frotz."""

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
    'thing guard of person in cell\n    name "burly guard"\n    words burly, guard\n'
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
        input="search chest\ndig\nthink\nrub pebble\nask guard about pebble\nrub guard\nfullscore\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You find gold coin." in out  # search lists the chest's contents
    assert "The ground keeps its secrets." in out  # an intransitive flavor verb (dig)
    assert "A fine idea. Nothing comes of it." in out  # think
    assert "You polish the grey pebble." in out  # rub default on an object
    assert "stays mum" in out  # ask a living thing (flavor)
    assert "The guard does not enjoy that." in out  # the guard's own on rub overrides
    assert "You have scored 0 of a possible 0" in out  # fullscore breakdown


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
