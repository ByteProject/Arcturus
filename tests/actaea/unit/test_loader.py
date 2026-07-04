# test_loader.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M1: the loader and memory model. Real stories come from the
Arcturus compiler itself (built in-process, so the tests need no checked-in
binaries) and from the conformance directory when present; rejection paths
use synthetic images."""

import os

import pytest

from actaea.errors import MemoryFault, StoryFormatError
from actaea.loader import HEADER_SIZE, load, load_file
from actaea.memory import from_signed, to_signed

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

CONFORMANCE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "actaea", "conformance"
)

GAME = (
    'game\n    title "Loader Probe"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A hall."\n'
)


def _build(version=5) -> bytes:
    return generate(analyze(cosmos.combined_program(parse(GAME))), version=version)


def test_loads_an_arcturus_z5():
    data = _build(5)
    story = load(data)
    h = story.header
    assert h.version == 5
    assert story.memory.scale == 4
    assert h.file_length <= len(data)
    assert story.checksum_ok()
    # The header's regions must be ordered and in range.
    assert HEADER_SIZE <= h.static_base <= h.high_base <= len(data)
    assert h.initial_pc >= h.high_base
    assert len(h.serial) == 6 and h.serial.isdigit()


def test_loads_an_arcturus_z8():
    story = load(load_z8 := _build(8))
    assert story.header.version == 8
    assert story.memory.scale == 8
    assert story.header.file_length <= len(load_z8)
    assert story.checksum_ok()


def test_rejects_wrong_versions():
    data = bytearray(_build(5))
    for wrong in (0, 3, 4, 6, 7, 9):
        data[0] = wrong
        with pytest.raises(StoryFormatError) as e:
            load(bytes(data))
        assert "versions 5 and 8" in str(e.value)


def test_rejects_a_truncated_file():
    with pytest.raises(StoryFormatError) as e:
        load(b"\x05too short")
    assert "too short" in str(e.value)


def test_rejects_a_lying_length_field():
    data = bytearray(_build(5))
    data[0x1A] = 0xFF  # claim ~256K in a file a fraction of that size
    data[0x1B] = 0xFF
    with pytest.raises(StoryFormatError) as e:
        load(bytes(data))
    assert "holds" in str(e.value)


def test_checksum_mismatch_is_detected():
    data = bytearray(_build(5))
    # Flip one byte past the header: verify must fail, loading must not.
    data[HEADER_SIZE + 1] ^= 0xFF
    story = load(bytes(data))
    assert not story.checksum_ok()


def test_memory_regions_and_write_barrier():
    story = load(_build(5))
    m = story.memory
    # Dynamic memory reads and writes; the pristine copy survives for reset.
    first = m.byte(HEADER_SIZE)
    m.set_byte(HEADER_SIZE, (first + 1) & 0xFF)
    assert m.byte(HEADER_SIZE) != first
    m.reset()
    assert m.byte(HEADER_SIZE) == first
    # Static memory reads but never writes.
    assert m.byte(m.static_base) >= 0
    with pytest.raises(MemoryFault):
        m.set_byte(m.static_base, 1)
    # A word write straddling the barrier is a fault too.
    with pytest.raises(MemoryFault):
        m.set_word(m.static_base - 1, 0x1234)
    # Reads past the story end fault instead of wrapping.
    with pytest.raises(MemoryFault):
        m.byte(len(m.mem))
    with pytest.raises(MemoryFault):
        m.word(len(m.mem) - 1)


def test_packed_address_resolution():
    z5 = load(_build(5))
    z8 = load(_build(8))
    # The initial PC sits in high memory; a routine packed near it must
    # unpack with the version's multiplier, and the 0x8000 sign line must
    # mean nothing here: packed addresses are unsigned (the 2026-07-04 rule).
    assert z5.memory.unpack(0x8000) == 0x20000
    assert z8.memory.unpack(0x8000) == 0x40000
    assert z5.memory.unpack(1) == 4
    assert z8.memory.unpack(1) == 8


def test_signedness_helpers_are_the_one_conversion():
    assert to_signed(0x0000) == 0
    assert to_signed(0x7FFF) == 32767
    assert to_signed(0x8000) == -32768
    assert to_signed(0xFFFF) == -1
    assert from_signed(-1) == 0xFFFF
    assert from_signed(-32768) == 0x8000
    assert from_signed(70000) == 70000 & 0xFFFF
    # Round trips both ways across the sign line.
    for w in (0, 1, 0x7FFF, 0x8000, 0x8001, 0xFFFF):
        assert from_signed(to_signed(w)) == w


@pytest.mark.skipif(
    not os.path.exists(os.path.join(CONFORMANCE, "czech.z5")),
    reason="conformance stories not present (kept out of the public repo)",
)
def test_loads_czech():
    story = load_file(os.path.join(CONFORMANCE, "czech.z5"))
    assert story.header.version == 5
    assert story.checksum_ok()


@pytest.mark.skipif(
    not os.path.exists(os.path.join(CONFORMANCE, "Jigsaw.z8")),
    reason="conformance stories not present (kept out of the public repo)",
)
def test_loads_a_real_z8():
    story = load_file(os.path.join(CONFORMANCE, "Jigsaw.z8"))
    assert story.header.version == 8
    assert story.memory.scale == 8
    assert story.checksum_ok()
