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

Abbreviation compression (the Z-chars 1 to 3) is a size-pass lever and is not
used here; this module emits literal text only.
"""

from __future__ import annotations

# A2 holds digits and punctuation at Z-char positions 8..31 (positions 6 and 7
# are the escape and newline, handled specially).
_A2_PUNCT = "0123456789.,!?_#'\"/\\-:()"
assert len(_A2_PUNCT) == 24  # fills Z-chars 8..31


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


def encode(text: str) -> bytes:
    """Encode a string as a packed Z-string, including the end-of-string bit."""
    zchars: list[int] = []
    for c in text:
        zchars.extend(_char_to_zchars(c))
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


def decode(data: bytes) -> str:
    """Decode a packed Z-string. Used by the tests to round-trip encode().
    Handles the v5 single shifts, the A2 escape, newline, and space; it does
    not expand abbreviations, which encode() never emits."""
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
            shift = None  # an abbreviation reference; encode() never emits these
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
