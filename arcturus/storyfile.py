# storyfile.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Assembly of a Z-machine version 5 story file.

A story file is a header (64 bytes) followed by dynamic memory (writable:
globals and the object table), static memory (read-only: abbreviations and the
dictionary), and high memory (code and strings). This builds the byte image,
sets the header fields, and finalizes the file length and checksum (Z-machine
standard 1.1, section 11).
"""

from __future__ import annotations

# Header field offsets (Z-machine standard 1.1, section 11).
H_VERSION = 0x00
H_FLAGS1 = 0x01
H_RELEASE = 0x02
H_HIGH_BASE = 0x04
H_INITIAL_PC = 0x06
H_DICTIONARY = 0x08
H_OBJECTS = 0x0A
H_GLOBALS = 0x0C
H_STATIC_BASE = 0x0E
H_FLAGS2 = 0x10
H_SERIAL = 0x12
H_ABBREV = 0x18
H_LENGTH = 0x1A
H_CHECKSUM = 0x1C

HEADER_SIZE = 64

# Fixed memory layout shared by codegen and the lowering. The header is 64 bytes
# and the 240 globals 480, so the input buffers sit at known addresses: the text
# buffer is [max-length, current-length, chars...]; the parse buffer is
# [max-words, count, (dict-addr, length, position) x max-words].
GLOBALS_BYTES = 240 * 2
TEXT_BUFFER_ADDR = HEADER_SIZE + GLOBALS_BYTES  # 544
TEXT_BUFFER_MAX = 60
TEXT_BUFFER_BYTES = 2 + TEXT_BUFFER_MAX
PARSE_BUFFER_ADDR = TEXT_BUFFER_ADDR + TEXT_BUFFER_BYTES  # 606
PARSE_BUFFER_MAX = 12
PARSE_BUFFER_BYTES = 2 + PARSE_BUFFER_MAX * 4
# A backup of the parse buffer, kept so "oops" can patch the previous command's
# offending word and re-resolve it without re-reading the line.
OOPS_PARSE_ADDR = PARSE_BUFFER_ADDR + PARSE_BUFFER_BYTES  # 656
OOPS_PARSE_BYTES = PARSE_BUFFER_BYTES
# A backup of the text buffer, kept so the disambiguation ask ("Which do you
# mean, ...?") can read the player's answer through the one shared text buffer
# and then weave it back into the saved command (docs/02 section 8).
ASK_TEXT_ADDR = OOPS_PARSE_ADDR + OOPS_PARSE_BYTES  # 706
ASK_TEXT_BYTES = TEXT_BUFFER_BYTES

# File-length scale by version: the stored length is the real length divided by
# this (section 11.1.6).
_LENGTH_SCALE = {1: 2, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8, 8: 8}


class StoryFile:
    def __init__(self, version: int = 5) -> None:
        self.version = version
        self.mem = bytearray(HEADER_SIZE)
        self.set_byte(H_VERSION, version)

    # -- placement ---------------------------------------------------------

    def append(self, data: bytes) -> int:
        """Append a region and return its start address."""
        addr = len(self.mem)
        self.mem += data
        return addr

    def here(self) -> int:
        return len(self.mem)

    # -- field setters -----------------------------------------------------

    def set_byte(self, off: int, value: int) -> None:
        self.mem[off] = value & 0xFF

    def set_word(self, off: int, value: int) -> None:
        self.mem[off] = (value >> 8) & 0xFF
        self.mem[off + 1] = value & 0xFF

    def set_bytes(self, off: int, data: bytes) -> None:
        self.mem[off : off + len(data)] = data

    def set_serial(self, serial: str) -> None:
        s = (serial + "      ")[:6].encode("ascii", "replace")
        self.set_bytes(H_SERIAL, s)

    # -- finalize ----------------------------------------------------------

    def finalize(self) -> bytes:
        scale = _LENGTH_SCALE[self.version]
        while len(self.mem) % scale != 0:
            self.mem.append(0)
        length = len(self.mem)
        self.set_word(H_LENGTH, length // scale)
        checksum = sum(self.mem[HEADER_SIZE:length]) & 0xFFFF
        self.set_word(H_CHECKSUM, checksum)
        return bytes(self.mem)
