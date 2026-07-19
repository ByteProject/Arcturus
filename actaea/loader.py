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
        file length, summed modulo 0x10000 (Standard 1.1 verify opcode).
        Summed over the story file AS STORED (the pristine image), never the
        live memory: the game has usually written all over dynamic memory by
        the time it calls verify, and the opcode asks about the FILE (CZECH
        test 404 exists to catch exactly this). A zero stated checksum is
        accepted as 'not provided' (some ancient tools); anything else must
        match."""
        h = self.header
        if h.checksum == 0:
            return True
        data = self.memory.initial
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


def is_blorb(data: bytes) -> bool:
    """A Blorb resource file: IFF FORM of type IFRS (the .zblorb/.blorb
    shapes arcimg packs and the Gargoyle family opens)."""
    return len(data) >= 12 and data[:4] == b"FORM" and data[8:12] == b"IFRS"


def blorb_resources(data: bytes):
    """The Blorb resource index as {(usage, number): (start, length)} where
    start addresses the chunk's PAYLOAD. Tolerant of anything beyond what
    Actaea consumes (Exec 0 and Pict N); a malformed index raises
    StoryFormatError with the reason."""
    if not is_blorb(data):
        raise StoryFormatError("not a Blorb file")
    if data[12:16] != b"RIdx":
        raise StoryFormatError("Blorb: the resource index is not first")
    def word32(off):
        return (data[off] << 24) | (data[off+1] << 16) | (data[off+2] << 8) | data[off+3]
    count = word32(20)
    out = {}
    for i in range(count):
        off = 24 + i * 12
        usage = data[off:off+4]
        number = word32(off + 4)
        start = word32(off + 8)
        if start + 8 > len(data):
            raise StoryFormatError("Blorb: resource offset beyond the file")
        length = word32(start + 4)
        out[(usage, number)] = (start + 8, length)
    return out


def blorb_story(data: bytes) -> bytes:
    """The embedded story (Exec 0, a ZCOD chunk) of a .zblorb."""
    res = blorb_resources(data)
    hit = res.get((b"Exec", 0))
    if hit is None:
        raise StoryFormatError(
            "this Blorb holds no story (no Exec 0 resource); it is a "
            "resource-only .blorb that accompanies a separate story file"
        )
    start, length = hit
    return data[start:start + length]


def blorb_picture(path: str, number: int):
    """Picture `number` (a Pict resource, PNG bytes) from a Blorb file, or
    None on any miss: absent resource, unreadable file, not a Blorb. The
    forgiving shape the picture band wants (a missing picture degrades to
    an empty band, never a crash)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        start, length = blorb_resources(data)[(b"Pict", number)]
        return data[start:start + length]
    except (OSError, KeyError, StoryFormatError):
        return None


def load_file(path: str) -> Story:
    with open(path, "rb") as f:
        data = f.read()
    if is_blorb(data):
        # A .zblorb: the story rides inside as Exec 0. Pictures stay in the
        # file; the front end reads them back out via blorb_picture.
        return load(blorb_story(data), name=path)
    return load(data, name=path)
