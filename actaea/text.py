# text.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The text engine (M5; Standard 1.1 section 3): Z-string decode, ZSCII to
Unicode both ways, and the dictionary-form word encoder.

A Z-string is a sequence of 16-bit words, three 5-bit z-characters each, the
top bit marking the final word. The z-characters speak through three
alphabets: A0 lowercase, A1 uppercase, A2 punctuation and digits. 0 is a
space; 1 to 3 pick an abbreviation (32 per bank, addressed through the table
the header names at 0x18, stored as WORD addresses, so doubled); 4 and 5
shift to A1/A2 for exactly one character; A2's char 6 opens a 10-bit ZSCII
escape spelled by the next two z-characters; A2's char 7 is a newline.

ZSCII is Actaea's wire format between the machine and the world: codes 32 to
126 match ASCII, 13 is newline, and 155 to 251 are the extra characters,
which default to the Standard 1.1 accent table below and can be replaced by
a custom Unicode translation table named in the header extension (word 3).
The alphabets themselves can be replaced too (header 0x34, 78 bytes, rows
A0/A1/A2 for z-characters 6 to 31; A2's 6 and 7 keep their fixed meanings).

Stefan's deseos.z5 conformance story exists exactly to prove the accented
path end to end ([[never-strip-accents]]: the games render Spanish and
German properly on the retro interpreters, and Actaea must match)."""

from .errors import ActaeaError

_A0 = "abcdefghijklmnopqrstuvwxyz"
_A1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# A2's first two entries (z-chars 6 and 7) are the escape and newline, fixed
# even under a custom alphabet table; the string covers z-chars 8..31.
_A2 = "0123456789.,!?_#'\"/\\-:()"

# The default extra characters, ZSCII 155..223 (Standard 1.1 table 1).
_DEFAULT_EXTRA = (
    "äöüÄÖÜß»«"  # ä ö ü Ä Ö Ü ß » «
    "ëïÿËÏ"                          # ë ï ÿ Ë Ï
    "áéíóúý"                    # á é í ó ú ý
    "ÁÉÍÓÚÝ"                    # Á É Í Ó Ú Ý
    "àèìòù"                          # à è ì ò ù
    "ÀÈÌÒÙ"                          # À È Ì Ò Ù
    "âêîôû"                          # â ê î ô û
    "ÂÊÎÔÛ"                          # Â Ê Î Ô Û
    "åÅøØ"                                # å Å ø Ø
    "ãñõÃÑÕ"                    # ã ñ õ Ã Ñ Õ
    "æÆçÇ"                                # æ Æ ç Ç
    "þðÞÐ"                                # þ ð Þ Ð
    "£œŒ¡¿"                          # £ œ Œ ¡ ¿
)


class TextError(ActaeaError):
    """A Z-string or ZSCII code no well-formed story produces."""


class TextEngine:
    """Decoding and encoding against one story's tables: its abbreviations,
    its custom alphabets if any, and its Unicode translation table if any."""

    def __init__(self, mem, header):
        self.mem = mem
        self.abbrev_table = header.abbreviations
        # The Unicode translation table first: a custom ALPHABET table below
        # may name extra characters, so the translation must already stand.
        # (Header extension word 3, S 3.8.5.4: a length byte, then that many
        # words of Unicode code points for ZSCII 155 upward. Absent, the
        # Standard's default table speaks.)
        self.extra = _DEFAULT_EXTRA
        if header.header_ext and self._ext_words(header) >= 3:
            uaddr = mem.word(header.header_ext + 2 * 3)
            if uaddr:
                n = mem.byte(uaddr)
                self.extra = "".join(
                    chr(mem.word(uaddr + 1 + 2 * i)) for i in range(n)
                )
        # Custom alphabet table: 78 bytes of ZSCII at the header 0x34 address;
        # rows for z-chars 6..31 of A0, A1, A2. Zero means the defaults.
        if header.alphabet:
            base = header.alphabet
            rows = []
            for r in range(3):
                row = "".join(
                    self.zscii_to_unicode(mem.byte(base + 26 * r + i))
                    for i in range(26)
                )
                rows.append(row)
            self.a0, self.a1 = rows[0], rows[1]
            # A2's z-chars 6 and 7 stay escape and newline (S 3.5.5.1); the
            # custom row only speaks for 8..31.
            self.a2 = rows[2][2:]
        else:
            self.a0, self.a1, self.a2 = _A0, _A1, _A2

    def _ext_words(self, header) -> int:
        return self.mem.word(header.header_ext)

    # -- ZSCII <-> Unicode ---------------------------------------------------------

    def zscii_to_unicode(self, code: int) -> str:
        """One ZSCII output code as text. 0 prints nothing (S 3.8.2.1); the
        extra range answers from the translation table; anything undefined
        is a fault, named, in the fizmo tradition."""
        if code == 0:
            return ""
        if code == 13:
            return "\n"
        if 32 <= code <= 126:
            return chr(code)
        if 155 <= code <= 251:
            i = code - 155
            if i < len(self.extra):
                return self.extra[i]
            raise TextError(f"ZSCII {code} beyond the translation table")
        raise TextError(f"ZSCII {code} is not an output code")

    def unicode_to_zscii(self, ch: str) -> int:
        """One character as a ZSCII code (for input and for encoding)."""
        o = ord(ch)
        if ch == "\n":
            return 13
        if 32 <= o <= 126:
            return o
        i = self.extra.find(ch)
        if i >= 0:
            return 155 + i
        raise TextError(f"no ZSCII code for {ch!r}")

    # -- decoding --------------------------------------------------------------------

    def decode(self, addr: int, _in_abbrev: bool = False):
        """The Z-string at addr: returns (text, address after the string)."""
        out: list = []
        alpha = 0          # current alphabet for the NEXT character only
        pending = None     # 10-bit escape state: None, "high", or the high bits
        zchars = []
        a = addr
        while True:
            w = self.mem.word(a)
            a += 2
            zchars.extend(((w >> 10) & 0x1F, (w >> 5) & 0x1F, w & 0x1F))
            if w & 0x8000:
                break
        i = 0
        while i < len(zchars):
            z = zchars[i]
            i += 1
            if pending == "high":
                pending = z
                continue
            if pending is not None:
                out.append(self.zscii_to_unicode((pending << 5) | z))
                pending = None
                alpha = 0  # the shift that opened the escape is spent
                continue
            if z == 0:
                out.append(" ")
                alpha = 0
            elif z in (1, 2, 3):
                if i >= len(zchars):
                    break  # an abbreviation marker cut off by the end: drop it
                if _in_abbrev:
                    raise TextError(
                        f"abbreviation inside an abbreviation at {addr:#07x} "
                        "(S 3.3 forbids nesting)"
                    )
                n = 32 * (z - 1) + zchars[i]
                i += 1
                # The table holds WORD addresses: double to a byte address.
                sa = self.mem.word(self.abbrev_table + 2 * n) * 2
                out.append(self.decode(sa, _in_abbrev=True)[0])
                alpha = 0
            elif z == 4:
                alpha = 1
            elif z == 5:
                alpha = 2
            else:
                if alpha == 2 and z == 6:
                    pending = "high"
                elif alpha == 2 and z == 7:
                    out.append("\n")
                else:
                    row = (self.a0, self.a1, self.a2)[alpha]
                    # Rows index from z-char 6 (A2's from 8, past its two
                    # fixed entries).
                    out.append(row[z - (8 if alpha == 2 else 6)])
                alpha = 0
        return "".join(out), a

    # -- encoding (the dictionary form) -------------------------------------------------

    def encode_word(self, word: str) -> bytes:
        """A typed word in the v4+ dictionary form: 9 z-characters packed
        into 3 words (6 bytes), lowercased, truncated, padded with 5s.
        Characters outside the alphabets spell themselves as 10-bit escapes,
        exactly as the compiler on the other side of the project encodes
        them."""
        zchars: list = []
        for ch in word.lower():
            if ch == " ":
                zchars.append(0)
                continue
            i = self.a0.find(ch)
            if i >= 0:
                zchars.append(6 + i)
                continue
            i = self.a2.find(ch)
            if i >= 0:
                zchars.append(5)
                zchars.append(8 + i)
                continue
            try:
                z = self.unicode_to_zscii(ch)
            except TextError:
                z = ord("?")
            zchars.extend((5, 6, (z >> 5) & 0x1F, z & 0x1F))
        zchars = zchars[:9]
        while len(zchars) < 9:
            zchars.append(5)
        out = bytearray()
        for i in range(0, 9, 3):
            w = (zchars[i] << 10) | (zchars[i + 1] << 5) | zchars[i + 2]
            if i == 6:
                w |= 0x8000
            out += bytes([(w >> 8) & 0xFF, w & 0xFF])
        return bytes(out)
