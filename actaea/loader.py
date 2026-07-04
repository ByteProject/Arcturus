# loader.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Story-file loading and the header map (Z-Machine Standard 1.1 section 11).

load() takes the raw bytes, validates them (a version-5 or version-8 story,
long enough to hold what its header claims), and returns a Story: the parsed
header plus the Memory the rest of the interpreter runs against. Everything
that later modules need to find (dictionary, object table, globals,
abbreviations) is resolved here once, so the header layout lives in exactly
one file."""

from dataclasses import dataclass

from .errors import StoryFormatError
from .memory import Memory

HEADER_SIZE = 0x40

# The two versions Actaea plays, with their packed-address multipliers and the
# scale of the header's file-length field (Standard 1.1 section 11.1.6).
_SCALES = {5: 4, 8: 8}


@dataclass
class Header:
    """The story-side header fields (the ones the game wrote; the fields an
    interpreter fills in, like screen size and standard revision, are set by
    the VM at start time, not parsed here)."""

    version: int
    release: int
    serial: str            # six ASCII characters, conventionally YYMMDD
    high_base: int         # base of high memory (byte address)
    initial_pc: int        # first instruction's byte address (not packed)
    dictionary: int
    objects: int           # object table
    globals_: int          # global variables table (240 words)
    static_base: int
    abbreviations: int
    file_length: int       # in bytes, unscaled from the header field
    checksum: int          # as stated in the header
    flags1: int
    flags2: int
    terminating: int       # terminating-characters table (0 if none)
    alphabet: int          # custom alphabet table (0 = the standard one)
    header_ext: int        # header extension table (0 if none)


@dataclass
class Story:
    header: Header
    memory: Memory

    def checksum_ok(self) -> bool:
        """Verify the header checksum: the bytes from 0x40 up to the stated
        file length, summed modulo 0x10000 (Standard 1.1 verify opcode). A
        zero stated checksum is accepted as 'not provided' (some ancient
        tools); anything else must match."""
        h = self.header
        if h.checksum == 0:
            return True
        data = self.memory.mem
        end = min(h.file_length, len(data))
        return sum(data[HEADER_SIZE:end]) & 0xFFFF == h.checksum


def load(data: bytes, name: str = "story") -> Story:
    """Parse and validate a story image. Raises StoryFormatError with a
    plain-language reason for anything Actaea does not play."""
    if len(data) < HEADER_SIZE:
        raise StoryFormatError(
            f"{name}: too short to be a story file "
            f"({len(data)} bytes; the header alone is {HEADER_SIZE})"
        )
    version = data[0]
    if version not in _SCALES:
        raise StoryFormatError(
            f"{name}: version {version} story; Actaea plays versions 5 and 8"
        )
    scale = _SCALES[version]

    def word(off: int) -> int:
        return (data[off] << 8) | data[off + 1]

    header = Header(
        version=version,
        flags1=data[0x01],
        release=word(0x02),
        high_base=word(0x04),
        initial_pc=word(0x06),
        dictionary=word(0x08),
        objects=word(0x0A),
        globals_=word(0x0C),
        static_base=word(0x0E),
        flags2=word(0x10),
        serial=data[0x12:0x18].decode("ascii", errors="replace"),
        abbreviations=word(0x18),
        # The header stores the length divided by the version's scale.
        file_length=word(0x1A) * scale,
        checksum=word(0x1C),
        terminating=word(0x2E),
        alphabet=word(0x34),
        header_ext=word(0x36),
    )

    # A header claiming more file than exists is corrupt; less is fine (files
    # are commonly padded out to a scale boundary past the stated length).
    if header.file_length > len(data):
        raise StoryFormatError(
            f"{name}: header says {header.file_length} bytes "
            f"but the file holds {len(data)}"
        )
    if not HEADER_SIZE <= header.static_base <= len(data):
        raise StoryFormatError(
            f"{name}: static memory base {header.static_base:#06x} "
            f"outside the file"
        )

    return Story(header, Memory(data, scale))


def load_file(path: str) -> Story:
    with open(path, "rb") as f:
        return load(f.read(), name=path)
