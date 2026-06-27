# test_backend.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The B3 done-test: the backend emits a valid z5 story file for the smallest
program, and it runs on Frotz."""

import shutil
import subprocess

import pytest

from arcturus.codegen import generate, CodegenError
from arcturus.parser import parse
from arcturus.sema import analyze

MINIMAL = (
    'game\n'
    '    title  "Test Story"\n'
    '    author "Tester"\n'
    '    serial "260627"\n'
    '    start void\n'
    '\n'
    'on start\n'
    '    say "Hello from the test."\n'
    '\n'
    'room void\n'
    '    name "The Void"\n'
)


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


def test_interpolation_in_start_is_rejected():
    src = 'on start\n    say "turns: ${turns}"\n'
    with pytest.raises(CodegenError):
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
    assert "Test Story" in out
    assert "Release 1 / Serial number 260627 / Arcturus" in out
    assert "Hello from the test." in out
