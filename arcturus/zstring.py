# zstring.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""ZSCII text encoding for Z-machine version 5.

Text is packed as 5-bit Z-characters, three to a 16-bit word, the top bit of
the final word marking the end of the string (Z-machine standard 1.1, section
3). Three alphabets carry the characters: A0 lowercase, A1 uppercase, A2
punctuation. In version 5 the shift characters 4 and 5 shift the next single
character into A1 and A2 respectively; there is no shift lock. A character in
no alphabet is written with the A2 escape (Z-char 6) followed by its 10-bit
ZSCII value in two halves.

Abbreviation compression (the Z-chars 1 to 3) is the B6 size lever (docs/00
section 5). An abbreviation reference is two Z-characters: a shift (1, 2, or 3,
selecting the bank) followed by an index 0..31, so the three banks address 96
abbreviations, matching the table the header points at (storyfile.H_ABBREV). The
table and the abbreviation strings are laid out by codegen; this module decides,
at encode time, where a reference is cheaper than the literal text.

The active set is module state, installed once per compile with
set_abbreviations(), because encode() is called from many places (the assembler
encodes inline print text as routines are built, codegen encodes the packed
strings) and threading the set through every call site would be invasive. The
default is empty, so the driven backend tests, which never install a set, encode
literally exactly as before. The abbreviation strings themselves, and dictionary
words, must never contain a reference (the standard forbids nesting), so those
call sites pass abbrevs=[] for a literal encode.
"""

from __future__ import annotations

# A2 holds digits and punctuation at Z-char positions 8..31 (positions 6 and 7
# are the escape and newline, handled specially).
_A2_PUNCT = "0123456789.,!?_#'\"/\\-:()"
assert len(_A2_PUNCT) == 24  # fills Z-chars 8..31

# The abbreviation set in force for the current compilation. _ACTIVE is the
# author-facing order (index k is abbreviation k); _MATCHERS is the same set
# sorted longest-first as (text, bank, offset) so encode() greedily prefers the
# longest match. _HARVEST, when a list, records every string encode() sees, so a
# dry-run compile can pool the program's text for the optimizer (--make-
# abbreviations).
_ACTIVE: list[str] = []
_MATCHERS: list[tuple[str, int, int]] = []
_HARVEST: list[str] | None = None
ABBREV_MAX = 96  # three banks of 32 (Z-chars 1..3 then an index 0..31)


def set_abbreviations(abbrevs) -> None:
    """Install the abbreviation set encode() uses for this compile (at most 96
    strings; their order is the abbreviation index). Pass [] to disable."""
    global _ACTIVE, _MATCHERS
    _ACTIVE = list(abbrevs)[:ABBREV_MAX]
    _MATCHERS = _build_matchers(_ACTIVE)


def active_abbreviations() -> list[str]:
    """The installed set, in index order (what codegen lays out as the table)."""
    return list(_ACTIVE)


def _build_matchers(abbrevs) -> list[tuple[str, int, int]]:
    matchers = []
    for i, s in enumerate(abbrevs):
        if s:
            matchers.append((s, i // 32 + 1, i % 32))
    matchers.sort(key=lambda m: len(m[0]), reverse=True)  # longest match wins
    return matchers


def begin_harvest() -> None:
    """Start recording every string passed to encode() (a dry-run pass that pools
    the program's text without changing the bytes emitted)."""
    global _HARVEST
    _HARVEST = []


def end_harvest() -> list[str]:
    """Stop recording and return the strings seen since begin_harvest()."""
    global _HARVEST
    out = _HARVEST or []
    _HARVEST = None
    return out


def _char_to_zchars(c: str) -> list[int]:
    if c == " ":
        return [0]
    if "a" <= c <= "z":
        return [ord(c) - ord("a") + 6]
    if "A" <= c <= "Z":
        return [4, ord(c) - ord("A") + 6]
    if c == "\n":
        return [5, 7]
    idx = _A2_PUNCT.find(c)
    if idx >= 0:
        return [5, idx + 8]
    # Anything else: the A2 escape and a 10-bit ZSCII code (its byte value for
    # ZSCII 32..1023; non-representable characters fall back to '?').
    z = ord(c)
    if z > 0x3FF:
        z = ord("?")
    return [5, 6, (z >> 5) & 0x1F, z & 0x1F]


def _text_to_zchars(text: str, matchers: list[tuple[str, int, int]]) -> list[int]:
    """Walk the text left to right, emitting an abbreviation reference (the two
    Z-chars shift+index) wherever the longest installed abbreviation is a prefix
    of the remaining text, and the literal Z-chars otherwise."""
    zchars: list[int] = []
    i = 0
    n = len(text)
    while i < n:
        hit = None
        if matchers:
            for s, bank, offset in matchers:
                if text.startswith(s, i):
                    hit = (s, bank, offset)
                    break
        if hit is not None:
            s, bank, offset = hit
            zchars.append(bank)
            zchars.append(offset)
            i += len(s)
        else:
            zchars.extend(_char_to_zchars(text[i]))
            i += 1
    return zchars


def encode(text: str, abbrevs=None) -> bytes:
    """Encode a string as a packed Z-string, including the end-of-string bit.
    By default the module's installed abbreviation set is applied; pass abbrevs=[]
    for a literal encode (the abbreviation strings themselves and any other text
    that must hold no reference) or an explicit list to use a one-off set."""
    if _HARVEST is not None:
        _HARVEST.append(text)
    matchers = _MATCHERS if abbrevs is None else _build_matchers(abbrevs)
    zchars = _text_to_zchars(text, matchers)
    # Pad with shift-5 (a harmless trailing shift) to a multiple of three.
    while len(zchars) % 3 != 0:
        zchars.append(5)
    if not zchars:
        zchars = [5, 5, 5]

    out = bytearray()
    for i in range(0, len(zchars), 3):
        word = (zchars[i] << 10) | (zchars[i + 1] << 5) | zchars[i + 2]
        out.append((word >> 8) & 0xFF)
        out.append(word & 0xFF)
    # Set the end bit on the final word's high byte.
    out[-2] |= 0x80
    return bytes(out)


def encode_dict_word(word: str) -> bytes:
    """Encode a word as a fixed 6-byte dictionary entry (Z-machine standard 1.1,
    section 13). In version 5 a dictionary word is exactly nine Z-characters
    packed into three words (six bytes); longer words are truncated, so words
    sharing a nine-Z-character prefix collide. The text is lowercased by the
    caller; padding uses Z-char 5 and the end bit is set on the final word."""
    zchars: list[int] = []
    for c in word:
        zchars.extend(_char_to_zchars(c))
    zchars = zchars[:9]
    while len(zchars) < 9:
        zchars.append(5)
    out = bytearray()
    for i in range(0, 9, 3):
        w = (zchars[i] << 10) | (zchars[i + 1] << 5) | zchars[i + 2]
        out.append((w >> 8) & 0xFF)
        out.append(w & 0xFF)
    out[-2] |= 0x80  # end-of-string bit on the third (final) word
    return bytes(out)


def decode(data: bytes, abbrevs=None) -> str:
    """Decode a packed Z-string. Used by the tests to round-trip encode().
    Handles the v5 single shifts, the A2 escape, newline, and space. An
    abbreviation reference (Z-char 1..3 then an index) expands from `abbrevs` when
    given (index 32*(bank-1)+next); without it the reference yields nothing."""
    zchars: list[int] = []
    i = 0
    while i + 1 < len(data):
        word = (data[i] << 8) | data[i + 1]
        i += 2
        zchars.append((word >> 10) & 0x1F)
        zchars.append((word >> 5) & 0x1F)
        zchars.append(word & 0x1F)
        if word & 0x8000:
            break

    out: list[str] = []
    n = len(zchars)
    j = 0
    shift = None  # None (A0), "A1", or "A2", applying to the next alphabet char
    while j < n:
        z = zchars[j]
        j += 1
        if z == 0:
            out.append(" ")
            shift = None
        elif z in (1, 2, 3):
            # An abbreviation reference: the next Z-char is the index within bank z.
            if j < n:
                idx = 32 * (z - 1) + zchars[j]
                j += 1
                if abbrevs is not None and idx < len(abbrevs):
                    out.append(abbrevs[idx])
            shift = None
        elif z == 4:
            shift = "A1"
        elif z == 5:
            shift = "A2"
        elif z == 6 and shift == "A2":
            if j + 1 < n:
                out.append(chr((zchars[j] << 5) | zchars[j + 1]))
            j += 2
            shift = None
        elif z == 7 and shift == "A2":
            out.append("\n")
            shift = None
        else:
            if shift == "A1":
                out.append(chr(z - 6 + ord("A")))
            elif shift == "A2":
                out.append(_A2_PUNCT[z - 8])
            else:
                out.append(chr(z - 6 + ord("a")))
            shift = None
    return "".join(out)
