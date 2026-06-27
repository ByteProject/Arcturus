# test_storyfile.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Story-file assembler tests: header fields, length scaling, and checksum."""

from arcturus import storyfile


def word(data, off):
    return (data[off] << 8) | data[off + 1]


def test_version_byte():
    sf = storyfile.StoryFile(5)
    assert sf.mem[storyfile.H_VERSION] == 5


def test_set_word_and_byte():
    sf = storyfile.StoryFile(5)
    sf.set_word(storyfile.H_RELEASE, 0x1234)
    sf.set_byte(storyfile.H_FLAGS1, 0xAB)
    assert sf.mem[0x02] == 0x12 and sf.mem[0x03] == 0x34
    assert sf.mem[0x01] == 0xAB


def test_serial_is_six_bytes():
    sf = storyfile.StoryFile(5)
    sf.set_serial("260627")
    assert sf.mem[0x12:0x18] == b"260627"


def test_finalize_pads_and_checksums():
    sf = storyfile.StoryFile(5)
    sf.append(bytes([1, 2, 3, 4, 5]))  # 64 + 5 = 69, pads to 72 (multiple of 4)
    data = sf.finalize()
    assert len(data) % 4 == 0
    # length field is the real length divided by 4 (v5 scale).
    assert word(data, storyfile.H_LENGTH) == len(data) // 4
    # checksum is the sum of bytes from 0x40 to the end, mod 65536.
    assert word(data, storyfile.H_CHECKSUM) == sum(data[0x40:]) & 0xFFFF
