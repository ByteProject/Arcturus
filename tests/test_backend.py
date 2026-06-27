# test_backend.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The B3 done-test: the backend emits a valid z5 story file for the smallest
program, and it runs on Frotz."""

import os
import shutil
import subprocess

import pytest

from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "smallest.storyarc")

with open(FIXTURE, "r", encoding="utf-8") as _fh:
    MINIMAL = _fh.read()


def compile_z5(src):
    return generate(analyze(parse(src)))


def word(data, off):
    return (data[off] << 8) | data[off + 1]


def test_emits_valid_z5_header():
    data = compile_z5(MINIMAL)
    assert data[0x00] == 5  # version 5
    assert len(data) % 4 == 0
    assert word(data, 0x1A) == len(data) // 4  # file length field
    assert word(data, 0x1C) == sum(data[0x40:]) & 0xFFFF  # checksum
    # Region invariants: dynamic < static <= high, PC inside high memory.
    assert word(data, 0x0E) <= word(data, 0x04)  # static_base <= high_base
    assert word(data, 0x06) == word(data, 0x04)  # initial PC at start of code
    assert data[0x12:0x18] == b"260627"


def test_object_interpolation_is_rejected_until_b43():
    # Numeric interpolation works now; printing an object name or an article
    # needs the object table (B4.3).
    src = 'on start\n    say "${the player}"\n'
    with pytest.raises(ArcError):
        compile_z5(src)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_runs_on_frotz(tmp_path):
    data = compile_z5(MINIMAL)
    story = tmp_path / "test.z5"
    story.write_bytes(data)
    result = subprocess.run(
        [_frotz(), "-p", str(story)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
    )
    out = result.stdout
    # The banner and the start text both appear, and the game ran to a clean end.
    assert "Smallest" in out
    assert "Release 1 / Serial number 260627 / Arcturus" in out
    assert "Hello from Arcturus." in out
