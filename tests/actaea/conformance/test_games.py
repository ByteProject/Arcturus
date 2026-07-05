# test_games.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M11: real games as integration checks (docs/06 section 11), z5
and z8, headless. Each boots and plays a few turns without a fault; the
assertions pin text the game genuinely prints, so a silently wrong machine
cannot pass by not crashing. Two of these earned their place the hard way:
Anchorhead reads below an array at boot (16-bit wraparound in the table
opcodes) and Jigsaw asks for the children of 'nothing' (object 0 answers 0,
never a fault). The story files are third-party and stay local; the tests
skip where they are absent."""

import os

import pytest

from actaea.io import CaptureIO
from actaea.loader import load_file
from actaea.vm import VM

CONFORMANCE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "actaea", "conformance"
)


def _play(name, script, steps=100_000_000):
    path = os.path.join(CONFORMANCE, name)
    if not os.path.exists(path):
        pytest.skip("conformance stories not present (kept out of the public repo)")
    vm = VM(load_file(path), CaptureIO(script=list(script)))
    try:
        vm.run(max_steps=steps)
    except IndexError:
        pass  # script exhausted: whatever printed is the evidence
    return vm.io.text


def test_ghosts_of_blackwood_manor_z5():
    out = _play("ghosts.z5", [""] * 4 + ["look", "inventory"])
    assert "Writer's block" in out


def test_deseos_z5_speaks_spanish_with_accents():
    out = _play("deseos.z5", ["no", "", "mirar"])
    # The Spanish machine-translation path in full: accented output decoded
    # from the story's own alphabet and Unicode tables.
    assert "¿Quieres color?" in out


def test_calypso_z5():
    out = _play("calypso.z5", [""] * 4 + ["look"])
    assert "CALYPSO" in out


def test_anchorhead_z8():
    out = _play("anchor.z8", [""] * 8 + ["look", "x house"])
    assert "A N C H O R H E A D" in out
    assert "November, 1997." in out


def test_jigsaw_z8():
    out = _play("Jigsaw.z8", [""] * 8 + ["look"])
    assert "Welcome to JIGSAW" in out
    assert "Century Park" in out
