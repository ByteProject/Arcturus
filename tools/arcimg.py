#!/usr/bin/env python3
# arcimg.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arcimg: the arc_image preparation tool.

An arc_image id is a resource slot: a room says `arc_image 8`, and an aware
interpreter loads picture 8. This tool turns an author's source art into the
numbered picture files that back those slots, and packs them for distribution.

Two picture shapes (docs/00, the graphics plan):

  infocom   320x72   9 rows, the upper third, the classic Arthur look
  daad      320x96   12 rows, the upper half, the Rabenstein look

Both are pixel-art dimensions that hold a whole number of 8-pixel text rows, so
the status bar sits flush beneath the band. On modern systems an interpreter
integer-scales the picture to the window (crisp for pixel art); the display is
integer-scaled either way, so pixel art is the medium that looks best.

Commands:

  arcimg pack SOURCES... -o story.blorb
      Pack the numbered PNGs found in the given files/directories into a
      Blorb (Pict N = arc_image id N, plus the ARCI declaration chunk).
      With --zblorb STORY the story rides inside as Exec 0: one file that
      carries the whole game, for Actaea, the Gargoyle family, and the
      proteus web builder alike. Stdlib only.

  arcimg prep SOURCE --id N --mode {infocom,daad} [-o DIR]
      Produce N.png sized to a mode. A PNG already at the exact mode size is
      just copied (stdlib). Any other source (a photo, a JPEG, a wrong size) is
      centre-cropped to the mode's aspect and resized, which needs Pillow; the
      tool offers to install it, guided, the first time it is needed.

  arcimg info SOURCE
      Report the size of a PNG, or list the pictures in a Blorb pack.

  arcimg convert SOURCES... --target TAG -o DIR [--preview DIR]
      The retro path (arc_image/reference/design.md): derive each master's native version for a
      target (AMI, AST, DOS, C64, ZX3, CPC, ...) as <id>.<TAG> .arc files.
      Pictures convert in parallel; outputs newer than their master, its
      .hint sidecar, and this tool are skipped make-style. A master may
      carry <id>.hint ({"salient": [[cx, cy, r], ...]}) naming bright discs
      (a moon, a sun) that must survive conversion visibly. The 16-bit
      targets pack LZSA2: Emmanuel Marty's lzsa tool is used when found
      ($ARCIMG_LZSA, then PATH) for the optimal parse, and the built-in
      pure-Python packer otherwise (~8% larger, no dependency ever).

  arcimg targets | arcimg render FILE -o PNG
      List the target ledger; render any .arc back to a PNG preview.

  arcimg scr SOURCE -o out.scr / arcimg unscr FILE --id N -o DIR
      The Spectrum polish loop. `scr` writes a ZX3 conversion (or converts
      a master on the spot) as a standard 6912-byte .scr: the band on top,
      a black bar below, so any editor gets the full 256x192 frame. The
      author fixes cells in SevenuP, img2spec, or any Spectrum tool, and
      `unscr` takes the file back: detects the band (9 or 12 rows; --mode
      overrides), strips the bar, lints (FLASH refused, content below the
      band reported), and writes <id>.ZX3 stamped HAND-AUTHORED (header
      byte 15 = 1). `convert` never overwrites a hand-authored file, with
      or without --force; delete it to reconvert from the master.

Pillow is an author-side convenience, never shipped to players: arcc and the
Actaea interpreter stay pure standard library. It is reached only to resize or
convert a source that is not already a mode-sized PNG.
"""

import argparse
import os
import re
import shutil
import struct
import sys
import zipfile
import zlib

__version__ = "1.35.0"

# The build fingerprint, in the manner of arcc and actaea: __version__ names the
# intended release, and __build__ is a short content hash the amalgamator bakes
# into build/arcimg so `arcimg --version` names the exact build. None here means
# the tool is running from source, not the standalone.
__build__ = None


def build_id() -> str:
    return __build__ or "source"


def _banner() -> str:
    """The identity block, matching the arcc and actaea family: three lines and
    no build id, so it stays clean leading every command; --version appends the
    build itself (version_text)."""
    return (
        f"arcimg v{__version__} - image processor and converter\n"
        "Part of Arcturus, programming language & compiler for the Infocom "
        "Z-machine\n"
        "Copyright (c) 2026, Stefan Vogt | "
        "https://github.com/ByteProject/Arcturus"
    )


def _version_text() -> str:
    """The banner plus the exact build, for `arcimg --version`."""
    return f"{_banner()}\nBuild {build_id()}"


# The picture modes: mode name -> (width, height) in pixels. Both are whole
# multiples of the 8-pixel text row (72 = 9 rows, 96 = 12 rows), which is what
# lets the status bar align flush under the band on every target.
MODES = {
    "infocom": (320, 72),   # 9 rows, upper third, the Arthur look
    "daad": (320, 96),      # 12 rows, upper half, the Rabenstein look
}

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_NUMBERED = re.compile(r"^(\d+)\.png$", re.IGNORECASE)


# -- small stdlib helpers (no Pillow) ------------------------------------------

def _numbered_id(name: str):
    """The id from a `<number>.png` filename, or None. The number is the
    resource slot, so 8.png is picture 8."""
    m = _NUMBERED.match(os.path.basename(name))
    return int(m.group(1)) if m else None


def _png_size_bytes(data: bytes):
    """(width, height) read straight from a PNG's IHDR header, or None if the
    bytes are not a PNG. No decode, no third-party library."""
    if len(data) < 24 or data[:8] != _PNG_SIG or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _png_size(path: str):
    """(width, height) of a PNG file, or None if it is not a readable PNG."""
    try:
        with open(path, "rb") as f:
            return _png_size_bytes(f.read(24))
    except OSError:
        return None


def _mode_of(dims):
    """The mode name whose dimensions match, or None."""
    for name, wh in MODES.items():
        if wh == dims:
            return name
    return None


def _modes_str():
    return ", ".join(f"{n} {w}x{h}" for n, (w, h) in MODES.items())


# -- Pillow, reached only when a source must be resized or converted -----------

def _ensure_pillow():
    """Return PIL.Image, installing Pillow first (with the author's consent) if
    it is missing. Pillow is needed only to resize or convert a source that is
    not already a mode-sized PNG; mode-sized PNGs never reach here."""
    try:
        from PIL import Image
        return Image
    except ImportError:
        pass

    print("arcimg: this step needs Pillow (the Python imaging library), which")
    print("        is not installed for this interpreter:")
    print(f"          {sys.executable}")
    try:
        answer = input("Install Pillow now with pip? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        print()
        print("arcimg: without Pillow this tool can only pack art that is")
        print("        already a PNG at a mode's exact size. Size your picture")
        print(f"        to one of: {_modes_str()}, then use `arcimg pack`.")
        raise SystemExit(2)

    import subprocess
    rc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "Pillow"]
    ).returncode
    if rc != 0:
        print("arcimg: pip could not install Pillow.", file=sys.stderr)
        raise SystemExit(2)
    try:
        from PIL import Image
        return Image
    except ImportError:
        print("arcimg: Pillow installed but could not be imported; try again "
              "in a fresh shell.", file=sys.stderr)
        raise SystemExit(2)


def _crop_to_ratio(img, tw: int, th: int):
    """Crop an image to the target aspect ratio (so a resize afterwards never
    squashes it), keeping as much of the picture as the ratio allows.

    Width trims are centred. Height trims anchor at the TOP (ruled
    2026-07-17): the two band modes think in interpreter lines, so the mode-9
    version of a mode-12 master is the SAME image ending at 72 rows, never a
    recomposition. A band-shaped master (already the target width) therefore
    passes through prep as an identity top-crop, pixel for pixel."""
    w, h = img.size
    target = tw / th
    cur = w / h
    if cur > target:                 # too wide: trim the sides, centred
        new_w = max(1, round(h * target))
        x = (w - new_w) // 2
        return img.crop((x, 0, x + new_w, h))
    if cur < target:                 # too tall: keep the top rows
        new_h = max(1, round(w / target))
        return img.crop((0, 0, w, new_h))
    return img


# ==============================================================================
# The .arc container, version 1 (arc_image/reference/design.md section 10): the retro image format.
# Big-endian throughout. One file per image id per target; arcimg is the only
# writer, the per-machine loaders are its readers, and render_arc() below is
# its round-trip unit test (encode, decode, render to PNG, compare).
# ==============================================================================

ARC_MAGIC = b"ARCI"
ARC_VERSION = 1

# Section types (arc_image/reference/design.md section 10).
SEC_BITMAP = 1     # the pixel data, in the target's native memory order
SEC_SCREEN = 2     # per-cell color-nibble matrix (C64 screen RAM, TED color)
SEC_COLOR = 3      # second per-cell matrix (C64 color RAM, TED luminance)
SEC_ATTR = 4       # one attribute byte per cell (Spectrum, VDC)
SEC_PALETTE = 5    # the palette, in native hardware encoding
SEC_LINETABLE = 6  # per-scanline register values (Atari 8-bit)
SEC_REGS = 7       # a handful of global hardware values


# ---- ZX0 (Einar Saukas's format, forward + inverted gamma: the v2 stream
# every published decompressor targets). Ported faithfully from the
# reference optimize.c/compress.c; the packer is OPTIMAL, not greedy, and
# byte-compatible with the reference tool. Ruled the .arc codec by Stefan
# (2026-07-08) after the corpus bake-off: within a few percent of Exomizer
# with the smallest decompressors in the business (~70 bytes of Z80).

_ZX0_MAX_OFFSET = 2048  # THE SPEC'D WINDOW (docs/08 part B; ruled 2026-07-17):
# every codec-1 stream arcimg packs carries no back-reference beyond 2048
# bytes, at ZERO measured cost on the corpus (byte-identical per-picture
# averages against the old 2176 quick window; 0-2% against the full 32640).
# The number is the CONTRACT that makes the ring decode architecture work:
# a decoder needs read access to only the last 2048 output bytes, one
# 2K-aligned ring in main RAM, so it can emit straight to screen memory
# (interleaved, port-addressed, or serial alike) with no staging band.
# Any published dzx0 also decodes these streams unchanged.


def _zx0_gamma_bits(value):
    bits = 1
    while value > 1:
        value >>= 1
        bits += 2
    return bits


class _Zx0Block:
    __slots__ = ("bits", "index", "offset", "chain")

    def __init__(self, bits, index, offset, chain):
        self.bits = bits
        self.index = index
        self.offset = offset
        self.chain = chain


def _zx0_optimize(data, offset_cap=None):
    """The optimal parse. offset_cap bounds every match offset (default: the
    quick-mode window). A SMALL cap (256) is the write-only-video mode: the
    stream stays standard ZX0, but a decoder then needs read access to only
    the last 256 output bytes, one page-aligned ring buffer in main RAM,
    which is what a machine whose video memory cannot be read back (a
    TRS-80's port-addressed graphics board, an Agon's serial VDP) wants."""
    if offset_cap is None:
        offset_cap = _ZX0_MAX_OFFSET
    n = len(data)
    max_offset = min(max(1, n - 1), offset_cap)
    last_literal = [None] * (max_offset + 1)
    last_match = [None] * (max_offset + 1)
    optimal = [None] * n
    match_length = [0] * (max_offset + 1)
    best_length = [0] * (n if n > 2 else 3)
    if n > 2:
        best_length[2] = 2
    last_match[1] = _Zx0Block(-1, -1, 1, None)
    for index in range(n):
        best_length_size = 2
        mo = min(max(index, 1), max_offset)
        for offset in range(1, mo + 1):
            if index != 0 and index >= offset and data[index] == data[index - offset]:
                ll = last_literal[offset]
                if ll is not None:
                    length = index - ll.index
                    bits = ll.bits + 1 + _zx0_gamma_bits(length)
                    lm = _Zx0Block(bits, index, offset, ll)
                    last_match[offset] = lm
                    if optimal[index] is None or optimal[index].bits > bits:
                        optimal[index] = lm
                match_length[offset] += 1
                if match_length[offset] > 1:
                    if best_length_size < match_length[offset]:
                        bits = (optimal[index - best_length[best_length_size]].bits
                                + _zx0_gamma_bits(best_length[best_length_size] - 1))
                        while best_length_size < match_length[offset]:
                            best_length_size += 1
                            bits2 = (optimal[index - best_length_size].bits
                                     + _zx0_gamma_bits(best_length_size - 1))
                            if bits2 <= bits:
                                best_length[best_length_size] = best_length_size
                                bits = bits2
                            else:
                                best_length[best_length_size] = \
                                    best_length[best_length_size - 1]
                    length = best_length[match_length[offset]]
                    bits = (optimal[index - length].bits + 8
                            + _zx0_gamma_bits((offset - 1) // 128 + 1)
                            + _zx0_gamma_bits(length - 1))
                    lm = last_match[offset]
                    if lm is None or lm.index != index or lm.bits > bits:
                        nb = _Zx0Block(bits, index, offset, optimal[index - length])
                        last_match[offset] = nb
                        if optimal[index] is None or optimal[index].bits > bits:
                            optimal[index] = nb
            else:
                match_length[offset] = 0
                lm = last_match[offset]
                if lm is not None:
                    length = index - lm.index
                    bits = lm.bits + 1 + _zx0_gamma_bits(length) + length * 8
                    nl = _Zx0Block(bits, index, 0, lm)
                    last_literal[offset] = nl
                    if optimal[index] is None or optimal[index].bits > bits:
                        optimal[index] = nl
    return optimal[n - 1]


def zx0_compress(data: bytes, offset_cap=None) -> bytes:
    """Optimal ZX0 (forward, inverted gamma). Empty input compresses to the
    bare end marker. offset_cap bounds the match window (see _zx0_optimize):
    the windowed mode for write-only video memory."""
    if not data:
        return b""  # ZX0 has no empty-stream form; the container convention
    out = bytearray()
    state = {"mask": 0, "bit_index": 0, "backtrack": True}

    def write_byte(v):
        out.append(v & 0xFF)

    def write_bit(v):
        if state["backtrack"]:
            if v:
                out[-1] |= 1
            state["backtrack"] = False
            return
        if not state["mask"]:
            state["mask"] = 128
            state["bit_index"] = len(out)
            write_byte(0)
        if v:
            out[state["bit_index"]] |= state["mask"]
        state["mask"] >>= 1

    def write_gamma(value, invert):
        i = 2
        while i <= value:
            i <<= 1
        i >>= 2
        while i:
            write_bit(0)
            bit = value & i
            write_bit((0 if bit else 1) if invert else (1 if bit else 0))
            i >>= 1
        write_bit(1)

    if data:
        # Un-reverse the optimal chain.
        optimal = _zx0_optimize(data, offset_cap)
        prev = None
        while optimal is not None:
            nxt = optimal.chain
            optimal.chain = prev
            prev = optimal
            optimal = nxt
        last_offset = 1
        pos = 0
        node = prev.chain
        prev_index = prev.index
        while node is not None:
            length = node.index - prev_index
            if node.offset == 0:
                write_bit(0)
                write_gamma(length, False)
                for _ in range(length):
                    write_byte(data[pos])
                    pos += 1
            elif node.offset == last_offset:
                write_bit(0)
                write_gamma(length, False)
                pos += length
            else:
                write_bit(1)
                write_gamma((node.offset - 1) // 128 + 1, True)
                write_byte((127 - (node.offset - 1) % 128) << 1)
                state["backtrack"] = True
                write_gamma(length - 1, False)
                pos += length
                last_offset = node.offset
            prev_index = node.index
            node = node.chain
    write_bit(1)
    write_gamma(256, True)
    return bytes(out)


def zx0_decompress(blob: bytes) -> bytes:
    """A verbatim port of the reference dzx0 (forward, inverted gamma): the
    mirror of every published ZX0 decoder, used by render/tests and as the
    executable specification for the per-CPU loaders in docs/08. The
    backtrack bit is the trick to know: after a new offset's LSB byte, the
    FIRST bit of the length gamma is that byte's bit 0."""
    if not blob:
        return b""  # the container's empty-section convention
    out = bytearray()
    pos = 0
    mask = 0
    bitv = 0
    back = False
    last_byte = 0
    last_offset = 1

    def read_byte():
        nonlocal pos, last_byte
        last_byte = blob[pos]
        pos += 1
        return last_byte

    def read_bit():
        nonlocal mask, bitv, back
        if back:
            back = False
            return last_byte & 1
        mask >>= 1
        if mask == 0:
            mask = 128
            bitv = read_byte()
        return 1 if bitv & mask else 0

    def gamma(inv):
        v = 1
        while not read_bit():
            v = (v << 1) | (read_bit() ^ inv)
        return v

    state = "lit"
    while True:
        if state == "lit":
            for _ in range(gamma(0)):
                out.append(read_byte())
            state = "new" if read_bit() else "last"
        elif state == "last":
            for _ in range(gamma(0)):
                out.append(out[-last_offset])
            state = "new" if read_bit() else "lit"
        else:
            v = gamma(1)
            if v == 256:
                return bytes(out)
            last_offset = v * 128 - (read_byte() >> 1)
            back = True
            for _ in range(gamma(0) + 1):
                out.append(out[-last_offset])
            state = "new" if read_bit() else "lit"


def rle_encode(data: bytes) -> bytes:
    """The shared RLE scheme: c<=0x7F copies c+1 literal bytes, c>=0x81
    repeats the next byte 257-c times (2..128), 0x80 ends the section. Runs
    shorter than 3 ship as literals (a 2-run costs the same and merges)."""
    out = bytearray()
    i, n = 0, len(data)
    lit = 0  # start of the pending literal stretch
    while i < n:
        # Measure the run at i.
        j = i + 1
        while j < n and data[j] == data[i] and j - i < 128:
            j += 1
        if j - i >= 3:
            # Flush pending literals, then the run.
            k = lit
            while k < i:
                take = min(128, i - k)
                out.append(take - 1)
                out += data[k:k + take]
                k += take
            out.append(257 - (j - i))
            out.append(data[i])
            i = j
            lit = i
        else:
            i = j
    k = lit
    while k < n:
        take = min(128, n - k)
        out.append(take - 1)
        out += data[k:k + take]
        k += take
    out.append(0x80)
    return bytes(out)


def rle_decode(data: bytes) -> bytes:
    """Inverse of rle_encode; stops at the 0x80 sentinel."""
    out = bytearray()
    i = 0
    while i < len(data):
        c = data[i]
        i += 1
        if c == 0x80:
            return bytes(out)
        if c < 0x80:
            out += data[i:i + c + 1]
            i += c + 1
        else:
            out += bytes([data[i]]) * (257 - c)
            i += 1
    raise ValueError("RLE stream ended without the 0x80 sentinel")


# -- LZSA2 (codec 2): the 16-bit targets' codec ---------------------------------
#
# Ruled 2026-07-08 (the codec bake-off addendum, arc_image/reference/design.md): the big-disk 16-bit
# targets (Amiga, ST, DOS) take LZSA2 instead of ZX0. Measured on the corpus:
# LZSA2 is ~5% larger than ZX0 (~300 bytes per picture) but packs 75x faster
# and decompresses faster on 68000/8086, and those machines have disk room to
# spare while a z5 story caps at 256K anyway. The 8-bit cell targets keep ZX0
# (best ratio, ~70-byte Z80 decoder) because their pictures are the ones that
# share a floppy with the story.
#
# Packing prefers Emmanuel Marty's `lzsa` tool when one is around, because
# its optimal parse beats any quick parse; without one, a pure-Python greedy
# packer below produces the same format about 8% larger (measured on the
# corpus), so arcimg never NEEDS an external binary (the BuildTools 4.0
# doctrine: Python only, no Linux dependency, every disk builder
# self-contained). The chain, ruled 2026-07-09:
#
#   $ARCIMG_LZSA (an explicit binary)  ->  `lzsa` on PATH  ->  built-in greedy
#
# Note the trade an author should know (documented in arc_image/reference/design.md): with the tool
# on PATH the assets pack ~8% smaller, but two machines only produce
# byte-identical assets when both have the same lzsa (or neither has one).
# Decompression is pure Python below, ported from BlockFormat_LZSA2.md, and
# doubles as the executable spec for the interpreter decoders (docs/08
# Part B). Every pack, from either packer, is round-tripped through that
# decoder before it is accepted.

def _find_lzsa():
    """The lzsa binary: $ARCIMG_LZSA, then PATH; None means the built-in
    greedy packer takes over. Never a remote machine, never an error."""
    env = os.environ.get("ARCIMG_LZSA")
    if env:
        return [env]
    path = shutil.which("lzsa")
    if path:
        return [path]
    return None


def lzsa2_compress(data: bytes) -> bytes:
    """Raw LZSA2 block: the external packer when one is found, the built-in
    greedy packer otherwise, both verified by lzsa2_decompress. The empty
    convention matches ZX0: empty in, empty out."""
    if not data:
        return b""
    cmd = _find_lzsa()
    if cmd is None:
        comp = _lzsa2_greedy(data)
    else:
        import subprocess
        import tempfile
        tmp = tempfile.mkdtemp(prefix="arcimg-lzsa-")
        try:
            src = os.path.join(tmp, "in.raw")
            dst = os.path.join(tmp, "out.lzsa2")
            with open(src, "wb") as f:
                f.write(data)
            r = subprocess.run(cmd + ["-f2", "-r", src, dst],
                               capture_output=True)
            if r.returncode != 0 or not os.path.exists(dst):
                raise RuntimeError(
                    f"lzsa failed: "
                    f"{r.stderr.decode(errors='replace').strip()}")
            with open(dst, "rb") as f:
                comp = f.read()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if lzsa2_decompress(comp) != data:
        raise RuntimeError("LZSA2 round-trip mismatch (packer bug?)")
    return comp


def _lzsa2_greedy(data: bytes) -> bytes:
    """The built-in LZSA2 packer: a greedy hash-chain parse with one step
    of lazy evaluation and rep-match awareness, emitting every mode of the
    raw block format. About 8% larger than the lzsa tool's optimal parse on
    the corpus, in seconds, deterministic, and dependency-free."""
    n = len(data)
    out = bytearray()
    pending = -1                         # index of the half-filled nibble byte

    def nibble(v):
        nonlocal pending
        if pending < 0:
            out.append((v & 0xF) << 4)
            pending = len(out) - 1
        else:
            out[pending] |= v & 0xF
            pending = -1

    def literals_extra(count):
        # the token carries 3; a nibble 0-14 adds; 15 -> a byte adds to 18;
        # byte 239 -> little-endian word, absolute.
        rest = count - 3
        if rest < 15:
            nibble(rest)
            return
        nibble(15)
        if count <= 255:                 # byte 0..237 (238/239 reserved)
            out.append(count - 18)
            return
        out.append(239)
        out.append(count & 0xFF)
        out.append(count >> 8)

    def match_extra(mlen):
        # the token carries 7 (+2 minmatch = 9); a nibble adds to 9;
        # 15 -> a byte adds to 24; byte 233 -> word absolute; 232 is EOD.
        rest = mlen - 9
        if rest < 15:
            nibble(rest)
            return
        nibble(15)
        if mlen <= 255 and mlen - 24 <= 231:
            out.append(mlen - 24)
            return
        out.append(233)
        out.append(mlen & 0xFF)
        out.append(mlen >> 8)

    def emit(lits_at, lits_n, d, mlen, last_d):
        # token XYZ|LL|MMM plus the trailing pieces, in stream order
        ll = lits_n if lits_n < 3 else 3
        mm = (mlen - 2) if (mlen - 2) < 7 else 7
        if d == last_d:
            xyz = 0b111
        elif d <= 32:
            xyz = 0b000 | ((~((-d) & 0x1F)) & 1)
        elif d <= 512:
            xyz = 0b010 | ((~(((-d) & 0x1FF) >> 8)) & 1)
        elif d <= 8704:
            xyz = 0b100 | ((~(((-(d - 512)) & 0x1FFF) >> 8)) & 1)
        else:
            xyz = 0b110
        out.append((xyz << 5) | (ll << 3) | mm)
        if lits_n >= 3:
            literals_extra(lits_n)
        out.extend(data[lits_at:lits_at + lits_n])
        if d != last_d:
            if d <= 32:
                nibble(((-d) & 0x1F) >> 1)
            elif d <= 512:
                out.append((-d) & 0xFF)
            elif d <= 8704:
                v = (-(d - 512)) & 0x1FFF
                nibble((v >> 9) & 0xF)
                out.append(v & 0xFF)
            else:
                v = (-d) & 0xFFFF
                out.append(v >> 8)
                out.append(v & 0xFF)
        if mlen - 2 >= 7:
            match_extra(mlen)

    head = {}
    prev = [0] * n
    CHAIN = 256

    def insert(i):
        if i + 2 < n:
            h = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2]
            prev[i] = head.get(h, -1)
            head[h] = i

    def offset_cost(d, last):
        # what an offset spends, in half-bytes (a nibble is 1)
        if d == last:
            return 0
        if d <= 32:
            return 1
        if d <= 512:
            return 2
        if d <= 8704:
            return 3
        return 4

    def find(i, last):
        # the best (gain, len, d) at i: gain in half-bytes saved against
        # spelling the same bytes as literals; a rep-match rides free
        best = (0, 0, 0)
        m = n - i
        if last and i >= last:
            l = 0
            while l < m and data[i + l] == data[i - last + l]:
                l += 1
            if l >= 2:
                g = 2 * l - 2 - (1 if l >= 9 else 0)
                if g > best[0]:
                    best = (g, l, last)
        if i + 2 < n:
            h = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2]
            j = head.get(h, -1)
            depth = 0
            while j >= 0 and depth < CHAIN:
                d = i - j
                if d > 0xFFFF:
                    break
                l = 0
                while l < m and data[j + l] == data[i + l]:
                    l += 1
                if l >= 2:
                    g = 2 * l - 2 - offset_cost(d, last)                         - (1 if l >= 9 else 0)
                    if g > best[0]:
                        best = (g, l, d)
                if l >= 512:
                    break
                j = prev[j]
                depth += 1
        return best

    i = 0
    lits_at = 0
    last_d = 0
    while i < n:
        gain, best_len, best_d = find(i, last_d)
        if best_len >= 2 and gain > 0:
            # the lazy step: a clearly better match one byte on defers this
            if i + 1 < n:
                g2, _l2, _d2 = find(i + 1, last_d)
                if g2 > gain + 2:
                    insert(i)
                    i += 1
                    continue
            emit(lits_at, i - lits_at, best_d, best_len, last_d)
            last_d = best_d
            stop = i + best_len
            while i < stop:
                insert(i)
                i += 1
            lits_at = i
        else:
            insert(i)
            i += 1

    # the EOD command: trailing literals, a 9-bit offset byte of zero
    # (ignored by decoders, the spec's shape), then the 232 marker
    lits_n = i - lits_at
    ll = lits_n if lits_n < 3 else 3
    out.append((0b010 << 5) | (ll << 3) | 7)
    if lits_n >= 3:
        literals_extra(lits_n)
    out.extend(data[lits_at:lits_at + lits_n])
    out.append(0)
    nibble(15)
    out.append(232)
    return bytes(out)


def lzsa2_decompress(blob: bytes) -> bytes:
    """Raw LZSA2 block decoder, a faithful port of BlockFormat_LZSA2.md.

    Token XYZ|LL|MMM. LL 0-2 direct, 3 extends by nibble (0-14 adds), nibble
    15 extends by byte (0-237 adds 18; 239 means a little-endian 16-bit
    absolute follows). MMM+2 is the match length, 7 extends the same way
    (byte adds 24; 233 means 16-bit absolute; 232 is EOD). Offsets decode by
    XYZ and are NEGATIVE (unexpressed high bits set to 1):
      00Z  5-bit: nibble is bits 1-4, NOT Z is bit 0
      01Z  9-bit: byte is bits 0-7, NOT Z is bit 8
      10Z 13-bit: nibble is bits 9-12, NOT Z is bit 8, byte is bits 0-7,
                  then subtract 512
      110 16-bit: byte is bits 8-15, then byte is bits 0-7
      111 repeat: the previous offset
    Nibbles come from a one-byte buffer, high half first."""
    if not blob:
        return b""
    out = bytearray()
    pos = 0
    nib_ready = False
    nib_store = 0
    offset = 0

    def byte():
        nonlocal pos
        v = blob[pos]
        pos += 1
        return v

    def nibble():
        nonlocal nib_ready, nib_store
        if nib_ready:
            nib_ready = False
            return nib_store & 0x0F
        nib_store = byte()
        nib_ready = True
        return nib_store >> 4

    while True:
        token = byte()
        # literals
        lits = (token >> 3) & 3
        if lits == 3:
            n = nibble()
            if n == 15:
                b = byte()
                lits = (byte() | (byte() << 8)) if b == 239 else 18 + b
            else:
                lits = 3 + n
        out += blob[pos:pos + lits]
        pos += lits
        # offset
        xyz = token >> 5
        if xyz < 2:                                  # 00Z: 5-bit
            offset = (nibble() << 1) | (~token >> 5 & 1) | ~0x1F
        elif xyz < 4:                                # 01Z: 9-bit
            offset = ((~token >> 5 & 1) << 8) | byte() | ~0x1FF
        elif xyz < 6:                                # 10Z: 13-bit
            offset = ((nibble() << 9) | ((~token >> 5 & 1) << 8) | byte()) \
                     | ~0x1FFF
            offset -= 512
        elif xyz == 6:                               # 110: 16-bit
            offset = ((byte() << 8) | byte()) - 0x10000
        # 111: repeat, offset unchanged
        # match length
        mlen = (token & 7) + 2
        if mlen == 9:
            n = nibble()
            if n == 15:
                b = byte()
                if b == 232:
                    return bytes(out)                # EOD marker
                mlen = (byte() | (byte() << 8)) if b == 233 else 24 + b
            else:
                mlen = 9 + n
        src = len(out) + offset
        if src < 0:
            raise ValueError("LZSA2 offset before start")
        for _ in range(mlen):
            out.append(out[src])
            src += 1


# Codecs (header byte 14): 0 = the RLE scheme above, 1 = ZX0 (the 8-bit cell
# targets and the default; every stream carries the 2048-byte window
# guarantee, see _ZX0_MAX_OFFSET above), 2 = LZSA2 (the 16-bit targets; see
# the ruling note above). A short-lived codec 3 ("ZX0W", a 256-byte window)
# was retired unreleased on 2026-07-17: the ruling folded its ring idea into
# codec 1 itself as the window guarantee, at zero ratio cost, so one codec
# per target chapter stands. Each target chapter in docs/08 mandates exactly
# one codec, so a real interpreter carries exactly one decoder.
CODEC_RLE = 0
CODEC_ZX0 = 1
CODEC_LZSA2 = 2

_CODECS = {
    CODEC_RLE: (rle_encode, rle_decode),
    CODEC_ZX0: (zx0_compress, zx0_decompress),
    CODEC_LZSA2: (lzsa2_compress, lzsa2_decompress),
}


def write_arc(target_id, mode, width, height, image_id, sections,
              codec=CODEC_ZX0, hand=False) -> bytes:
    """Assemble a .arc file: header, section table, compressed section
    streams. `sections` is a list of (type, flags, raw_bytes). `hand`
    stamps header byte 15: 1 marks a hand-authored image (imported from
    an author's native edit), which `arcimg convert` will never
    overwrite; loaders ignore the byte either way."""
    pack = _CODECS[codec][0]
    out = bytearray()
    out += ARC_MAGIC
    out += bytes([ARC_VERSION, target_id, mode, len(sections)])
    out += struct.pack(">HHHBB", width, height, image_id, codec,
                       1 if hand else 0)
    streams = []
    for stype, flags, raw in sections:
        comp = pack(raw)
        out += struct.pack(">BBHH", stype, flags, len(raw), len(comp))
        streams.append(comp)
    for comp in streams:
        out += comp
    return bytes(out)


def read_arc(blob: bytes):
    """Parse a .arc file back into (header dict, [(type, flags, raw_bytes)]).
    Raises ValueError on anything malformed; a loader on real hardware does
    the same checks with cheaper manners."""
    if len(blob) < 16 or blob[:4] != ARC_MAGIC:
        raise ValueError("not a .arc file (bad magic)")
    version, target_id, mode, count = blob[4], blob[5], blob[6], blob[7]
    if version != ARC_VERSION:
        raise ValueError(f"unsupported .arc version {version}")
    width, height, image_id, codec, hand = struct.unpack(">HHHBB",
                                                         blob[8:16])
    if codec not in _CODECS:
        raise ValueError(f"unknown .arc codec {codec}")
    unpack = _CODECS[codec][1]
    head = {"target": target_id, "mode": mode, "width": width,
            "height": height, "id": image_id, "codec": codec,
            "hand": hand == 1}
    pos = 16
    table = []
    for _ in range(count):
        stype, flags, ulen, clen = struct.unpack(">BBHH", blob[pos:pos + 6])
        table.append((stype, flags, ulen, clen))
        pos += 6
    sections = []
    for stype, flags, ulen, clen in table:
        raw = unpack(blob[pos:pos + clen])
        if len(raw) != ulen:
            raise ValueError(
                f"section {stype}: {len(raw)} bytes, table says {ulen}")
        sections.append((stype, flags, raw))
        pos += clen
    return head, sections


# -- reference palettes (render-back; frozen per target in its wave) -----------

# C64: Colodore is the conversion and render palette (R0, reaffirmed
# 2026-07-13 after a one-day Pepto experiment: Pepto holds no teal and no
# hot pink, the vivid corpus read genuinely well on Colodore, and the
# real-hardware verdict belongs to the probe). Pepto ships as data, as
# Pixel Polizei carries it (m_c64mc.pde, WTFPL, Markku Reunanen).
_PEPTO = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x68, 0x37, 0x2B),
    (0x70, 0xA4, 0xB2), (0x6F, 0x3D, 0x86), (0x58, 0x8D, 0x43),
    (0x35, 0x28, 0x79), (0xB8, 0xC7, 0x6F), (0x6F, 0x4F, 0x25),
    (0x43, 0x39, 0x00), (0x9A, 0x67, 0x59), (0x44, 0x44, 0x44),
    (0x6C, 0x6C, 0x6C), (0x9A, 0xD2, 0x84), (0x6C, 0x5E, 0xB5),
    (0x95, 0x95, 0x95),
]

_COLODORE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]

# Spectrum: 8 base colors at two levels; bright black is black. Normal 0xD7.
def _zx_color(ink: int, bright: int):
    lvl = 0xFF if bright else 0xD7
    return ((lvl if ink & 2 else 0), (lvl if ink & 4 else 0),
            (lvl if ink & 1 else 0))

# MSX1: the canonical TMS9918A palette, entries 1..15 (0 is transparent).
_TMS9918 = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x3E, 0xB8, 0x49),
    (0x74, 0xD0, 0x7D), (0x59, 0x55, 0xE0), (0x80, 0x76, 0xF1),
    (0xB9, 0x5E, 0x51), (0x65, 0xDB, 0xEF), (0xDB, 0x65, 0x59),
    (0xFF, 0x89, 0x7D), (0xCC, 0xC3, 0x5E), (0xDE, 0xD0, 0x87),
    (0x3A, 0xA2, 0x41), (0xB7, 0x66, 0xB5), (0xCC, 0xCC, 0xCC),
    (0xFF, 0xFF, 0xFF),
]

# Plus/4 (TED): THE MEASURED PALETTE, SECOND ANCHORING (the staircase
# on xplus4, Stefan's screenshots, 2026-07-25 morning). The first
# measurement was one nibble off: hardware nibble 0 is BLACK AT EVERY
# LUMINANCE (the TED doc's own law), so its column was invisible
# against the black canvas and the grid anchored on nibble 1's greys.
# Stefan's observation broke the case: "the clouds resolve into black
# instead of white" needs no hue shift, it convicts the greys. True
# order, the documented one: 0 black, 1 the grey ladder, 2 red, 3
# cyan, ... 15 light green: 15 ladders x 8 plus black = the 121.
_TED_MEASURED = (
    ((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)),
    ((32, 32, 32), (48, 48, 48), (64, 64, 64), (80, 80, 80), (120, 120, 120), (144, 144, 144), (192, 192, 192), (255, 255, 255)),
    ((94, 7, 0), (110, 23, 16), (126, 39, 32), (142, 55, 48), (182, 95, 88), (206, 119, 112), (254, 167, 160), (255, 231, 224)),
    ((0, 57, 64), (0, 73, 80), (2, 89, 96), (18, 105, 112), (58, 145, 152), (82, 169, 176), (130, 217, 224), (194, 255, 255)),
    ((86, 0, 108), (102, 6, 124), (118, 22, 140), (134, 38, 156), (174, 78, 196), (198, 102, 220), (246, 150, 255), (255, 214, 255)),
    ((0, 74, 0), (0, 90, 0), (10, 106, 0), (26, 122, 4), (66, 162, 44), (90, 186, 68), (138, 234, 116), (202, 255, 180)),
    ((21, 10, 174), (37, 26, 190), (53, 42, 206), (69, 58, 222), (109, 98, 255), (133, 122, 255), (181, 170, 255), (245, 234, 255)),
    ((43, 54, 0), (59, 70, 0), (75, 86, 0), (91, 102, 0), (131, 142, 0), (155, 166, 2), (203, 214, 50), (255, 255, 114)),
    ((84, 22, 0), (100, 38, 0), (116, 54, 0), (132, 70, 0), (172, 110, 37), (196, 134, 61), (244, 182, 109), (255, 246, 173)),
    ((66, 38, 0), (82, 54, 0), (98, 70, 0), (114, 86, 0), (154, 126, 0), (178, 150, 22), (226, 198, 70), (255, 255, 134)),
    ((18, 67, 0), (34, 83, 0), (50, 99, 0), (66, 115, 0), (106, 155, 0), (130, 179, 4), (178, 227, 52), (242, 255, 116)),
    ((95, 0, 56), (111, 11, 72), (127, 27, 88), (143, 43, 104), (183, 83, 144), (207, 107, 168), (255, 155, 216), (255, 219, 255)),
    ((0, 69, 8), (0, 85, 24), (1, 101, 40), (17, 117, 56), (57, 157, 96), (81, 181, 120), (129, 229, 168), (193, 255, 232)),
    ((0, 26, 154), (14, 42, 170), (30, 58, 186), (46, 74, 202), (86, 114, 242), (110, 138, 255), (158, 186, 255), (222, 250, 255)),
    ((46, 0, 172), (62, 13, 188), (78, 29, 204), (94, 45, 220), (134, 85, 255), (158, 109, 255), (206, 157, 255), (255, 221, 255)),
    ((0, 74, 0), (11, 90, 0), (27, 106, 0), (43, 122, 0), (83, 162, 3), (107, 186, 27), (155, 234, 75), (219, 255, 139)),
)

def _ted_color(hue: int, luma: int):
    return _TED_MEASURED[hue & 15][luma & 7]

# Atari 8-bit (GTIA hue<<4|luma): the common NTSC approximation; the R4
# addendum freezes a table measured from the probe emulator. Saturation
# 0.21: enough chroma for a sunset orange. No constant suits every master
# (0.28 made the wheel neon, 0.13 washed it out), and it does not have to:
# soft master shades are defended by the chroma-dumping metric in the A8
# converter, the CPC lesson, not by desaturating the whole wheel.
def _gtia_color(hl: int):
    import math
    hue, luma = (hl >> 4) & 15, hl & 15
    y = 20 + luma * 15
    if hue == 0:
        c = max(0, min(255, y))
        return (c, c, c)
    # THE WHEEL MIRROR, proven on Altirra's metal by the A8 probe
    # (2026-07-24): GTIA's hue numbering runs the OPPOSITE way around
    # the colour circle from the original model here, mirrored about
    # hue 5. Four probe points confirmed it (gold rendered blue before
    # the fix; hue 5 is the fixed point). The mirror is a pure
    # permutation of the same fifteen angles, so the RGB set the
    # optimizer chooses from is unchanged: renders stay pixel-identical
    # to the approved corpus, only the native bytes re-encode.
    mirrored = (10 - hue) % 15
    angle = math.radians((mirrored - 1) * 24 - 58)
    u, v = 0.21 * math.cos(angle), 0.21 * math.sin(angle)
    r = y + 292 * v
    g = y - 100 * u - 149 * v
    b = y + 517 * u
    clamp = lambda cc: max(0, min(255, int(round(cc))))
    return (clamp(r), clamp(g), clamp(b))

# Apple II HGR: black, white, and the two artifact pairs.
_HGR = {
    "black": (0, 0, 0), "white": (255, 255, 255),
    "purple": (255, 68, 253), "green": (20, 245, 60),
    "blue": (20, 207, 253), "orange": (255, 106, 60),
}

# C128 VDC: 16 RGBI (bit0 intensity); color 12 is dark yellow, not brown.
def _vdc_color(idx: int):
    i = 0x55 if idx & 1 else 0
    base = lambda on: 0xAA if on else 0
    return (min(255, base(idx & 8) + i), min(255, base(idx & 4) + i),
            min(255, base(idx & 2) + i))

# CPC: 27 hardware colors as an r*9+g*3+b index, levels 0/128/255. The
# loader maps the index to its gate-array value with a 27-byte table (the
# wave-2 addendum).
def _cpc_color(idx: int):
    lv = (0, 0x80, 0xFF)
    return (lv[(idx // 9) % 3], lv[(idx // 3) % 3], lv[idx % 3])


# -- a minimal PNG reader (stdlib; band-sized masters need no Pillow) -----------

def _read_png(path: str):
    """Read a PNG into rows of (r, g, b). Handles the shapes masters arrive
    in: 8-bit truecolor (with or without alpha), palette, and grayscale, all
    five filters, non-interlaced. Anything else raises ValueError and the
    caller may fall back to Pillow."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != _PNG_SIG:
        raise ValueError(f"{path}: not a PNG")
    pos = 8
    w = h = None
    bitdepth = ctype = None
    palette = None
    idat = bytearray()
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if tag == b"IHDR":
            w, h, bitdepth, ctype, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", body)
            if bitdepth != 8 or interlace != 0:
                raise ValueError(f"{path}: only 8-bit non-interlaced PNGs")
            if ctype not in (0, 2, 3, 6):
                raise ValueError(f"{path}: unsupported PNG color type {ctype}")
        elif tag == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))
    channels = {0: 1, 2: 3, 3: 1, 6: 4}[ctype]
    stride = w * channels
    rows = []
    prev = bytearray(stride)
    p = 0
    for _y in range(h):
        f0 = raw[p]
        row = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f0 == 1:  # Sub
            for i in range(channels, stride):
                row[i] = (row[i] + row[i - channels]) & 0xFF
        elif f0 == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif f0 == 3:  # Average
            for i in range(stride):
                a = row[i - channels] if i >= channels else 0
                row[i] = (row[i] + (a + prev[i]) // 2) & 0xFF
        elif f0 == 4:  # Paeth
            for i in range(stride):
                a = row[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                q = a + b - c
                pa, pb, pc = abs(q - a), abs(q - b), abs(q - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pred) & 0xFF
        prev = row
        if ctype == 2:
            rows.append([tuple(row[i:i + 3]) for i in range(0, stride, 3)])
        elif ctype == 6:
            rows.append([tuple(row[i:i + 3]) for i in range(0, stride, 4)])
        elif ctype == 3:
            rows.append([palette[v] for v in row])
        else:  # grayscale
            rows.append([(v, v, v) for v in row])
    return rows


# -- the quantizer (Wave 1: the palette targets) ---------------------------------

def _median_cut(rows, n):
    """Median-cut the image's distinct colors down to at most n
    representatives, weighted by pixel count. Painted masters carry few
    distinct colors, so this is exact (a pass-through) whenever the master
    already fits the budget."""
    hist = {}
    for row in rows:
        for c in row:
            hist[c] = hist.get(c, 0) + 1
    colors = list(hist.items())
    if len(colors) <= n:
        return [c for c, _cnt in colors]
    boxes = [colors]
    while len(boxes) < n:
        # Split the box with the largest weighted spread.
        best, best_spread, best_axis = None, -1, 0
        for bi, box in enumerate(boxes):
            if len(box) < 2:
                continue
            for axis in range(3):
                vals = [c[axis] for c, _ in box]
                spread = max(vals) - min(vals)
                if spread > best_spread:
                    best, best_spread, best_axis = bi, spread, axis
        if best is None:
            break
        box = boxes.pop(best)
        box.sort(key=lambda e: e[0][best_axis])
        total = sum(cnt for _c, cnt in box)
        acc, cut = 0, len(box) // 2
        for i, (_c, cnt) in enumerate(box):
            acc += cnt
            if acc * 2 >= total:
                cut = max(1, min(len(box) - 1, i + 1))
                break
        boxes.append(box[:cut])
        boxes.append(box[cut:])
    out = []
    for box in boxes:
        total = sum(cnt for _c, cnt in box)
        r = round(sum(c[0] * cnt for c, cnt in box) / total)
        g = round(sum(c[1] * cnt for c, cnt in box) / total)
        b = round(sum(c[2] * cnt for c, cnt in box) / total)
        out.append((r, g, b))
    return out


def _dist(a, b):
    """Perceptually weighted squared distance (green counts most)."""
    return (2 * (a[0] - b[0]) ** 2 + 4 * (a[1] - b[1]) ** 2
            + 3 * (a[2] - b[2]) ** 2)


def _nearest(c, palette, lo=0, hi=None, metric=None):
    dist = metric or _dist
    best, bi = None, lo
    for i in range(lo, hi if hi is not None else len(palette)):
        d = dist(c, palette[i])
        if best is None or d < best:
            best, bi = d, i
    return bi


def _kmeans_polish(rows, palette, iterations=4):
    """A few Lloyd iterations over the image's color histogram: colors vote
    for their nearest palette entry, entries move to their voters' centroid.
    Median-cut splits by spatial extent and starves small, perceptually loud
    regions (a sunset's sun); the polish gives them their entry back. Flat
    art is unaffected: when the palette already matches the histogram, no
    entry moves and the loop exits on the first pass."""
    hist = {}
    for row in rows:
        for c in row:
            hist[c] = hist.get(c, 0) + 1
    pal = list(palette)
    for _ in range(iterations):
        sums = [[0, 0, 0, 0] for _ in pal]
        for c, cnt in hist.items():
            s = sums[_nearest(c, pal)]
            s[0] += c[0] * cnt
            s[1] += c[1] * cnt
            s[2] += c[2] * cnt
            s[3] += cnt
        moved = False
        for i, s in enumerate(sums):
            if s[3] == 0:
                continue
            nc = (round(s[0] / s[3]), round(s[1] / s[3]), round(s[2] / s[3]))
            if nc != pal[i]:
                pal[i] = nc
                moved = True
        if not moved:
            break
    return pal


# Bayer 8x8, for the gradient masters. Ordered (never error diffusion) on
# purpose: it is spatially stable, it will not bleed across the cell hardware
# of the later waves, and RLE survives it far better (arc_image/reference/design.md section 4).
# 8x8 rather than 4x4 by Stefan's eye on the stresstest beach: the 4x4
# matrix's threshold geometry draws little 2x2 crosses in smooth regions;
# the 8x8 tile spreads the thresholds and the clusters dissolve into grain.
_BAYER8 = (
    (0, 32, 8, 40, 2, 34, 10, 42),
    (48, 16, 56, 24, 50, 18, 58, 26),
    (12, 44, 4, 36, 14, 46, 6, 38),
    (60, 28, 52, 20, 62, 30, 54, 22),
    (3, 35, 11, 43, 1, 33, 9, 41),
    (51, 19, 59, 27, 49, 17, 57, 25),
    (15, 47, 7, 39, 13, 45, 5, 37),
    (63, 31, 55, 23, 61, 29, 53, 21),
)


def _map_pixels(rows, palette, dither, lo=0, hi=None, metric=None):
    """Master pixels to palette indices, with optional low-amplitude ordered
    dithering: the zero-centred Bayer threshold is added to the channels
    before the nearest-color lookup (the classic arbitrary-palette ordered
    dither). `dither` is the amplitude in 8-bit channel units; 0 is off.
    `metric` overrides the distance (the Spectrum's saturation-aware one)."""
    out = []
    for y, row in enumerate(rows):
        orow = []
        for x, c in enumerate(row):
            if dither:
                t = (_BAYER8[y & 7][x & 7] / 63.0 - 0.5) * 2 * dither
                c = (min(255, max(0, round(c[0] + t))),
                     min(255, max(0, round(c[1] + t))),
                     min(255, max(0, round(c[2] + t))))
            orow.append(_nearest(c, palette, lo, hi, metric))
        out.append(orow)
    return out


def _protect_extremes(rows, palette, snap):
    """Salience protection: the image's brightest color cluster must exist
    in the palette (the swallowed sun/moon lesson: median cut and k-means
    both starve small, perceptually loud regions). If the brightest pixels
    have no near palette entry, the least-used entry is replaced."""
    brightest = max((c for row in rows for c in row),
                    key=lambda c: 2 * c[0] + 4 * c[1] + c[2])
    target = snap(brightest)
    if any(_dist(target, p) < 900 for p in palette):
        return palette
    # Replace the least-used entry with the protected color.
    counts = [0] * len(palette)
    for row in rows:
        for c in row:
            counts[_nearest(c, palette)] += 1
    victim = counts.index(min(counts))
    out = list(palette)
    out[victim] = target
    return out


def _gradient_class(rows):
    """Is this master gradient art (thousands of blended colors) rather than
    flat pixel art? Decides the dithering default: flat art is never dithered
    (its conversion is exact already); gradient art gets the banding softened."""
    seen = set()
    for row in rows:
        for c in row:
            seen.add(c)
            if len(seen) > 256:
                return True
    return False


def _snap4(c):
    return tuple(round(v * 15 / 255) * 17 for v in c)


def _snap3(c):
    return tuple(round(round(v * 7 / 255) * 255 / 7) for v in c)


def _snap6(c):
    return tuple(round(round(v * 63 / 255) * 255 / 63) for v in c)


def _dedupe(palette):
    seen, out = set(), []
    for c in palette:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# Wave 1 conversion back-ends: master rows (320x72/96 RGB) -> native dict.
# The rules from arc_image/reference/design.md: build the palette (median cut, then the k-means
# polish so small loud regions keep their entry), snap it to the target's gun
# depth BEFORE mapping pixels, then map. Flat pixel-art masters convert
# without dithering (exactly, whenever they fit the budget); gradient-class
# masters get a low-amplitude ordered dither scaled to the palette budget.

def _build_palette(rows, n, snap):
    pal = _median_cut(rows, n)
    if _gradient_class(rows):
        pal = _kmeans_polish(rows, pal)
    return _dedupe([snap(c) for c in pal])


def _dither_amount(rows, budget):
    """The ordered-dither amplitude: 0 for flat art, gentle for gradient art,
    stronger the smaller the palette budget. Tuned on the stresstest pair
    with Stefan (less is more: the pattern must stay subtler than the art's
    own texture, and large smooth areas show it first)."""
    if not _gradient_class(rows):
        return 0
    return {16: 8, 32: 5}.get(budget, 3)


def _convert_ami(rows, salient=None):
    # The same text contract as the ST (docs/08): the palette is luminance
    # sorted, entry 0 the darkest (COLOR00: the flat area below the band and
    # the interpreter's text paper, STABLE across pictures instead of a
    # random art color; a probe caught the background flipping brown to
    # pink between two beaches), entry 31 a guaranteed-readable light ink.
    w, h = len(rows[0]), len(rows)
    def luma(c):
        return 2 * c[0] + 4 * c[1] + c[2]
    pal = _build_palette(rows, 32, _snap4)
    pal.sort(key=luma)
    if luma(pal[-1]) < 4 * 255:  # no usable ink: trade one slot for white
        pal = _build_palette(rows, 31, _snap4)
        pal.sort(key=luma)
        pal.append((255, 255, 255))
    palette = pal + [(0, 0, 0)] * (32 - len(pal))
    if len(pal) < 32:
        palette = pal[:-1] + [(0, 0, 0)] * (32 - len(pal)) + [pal[-1]]
    pixels = _map_pixels(rows, palette, _dither_amount(rows, 32))
    return {"w": w, "h": h, "pixels": pixels, "palette": palette}


def _convert_ast(rows, salient=None):
    # The ST text contract (arc_image/reference/design.md, ruling 7's guarantee clause): entry 0 is
    # the darkest color (the text paper) and entry 15 the lightest (the text
    # ink), SHARED with the art rather than reserved, so a 16-color master
    # (the ST-class common denominator) converts without losing a color. The
    # converter guarantees the ink is readable: only when the art has no
    # light color at all does it give up one slot for white.
    w, h = len(rows[0]), len(rows)
    def luma(c):
        return 2 * c[0] + 4 * c[1] + c[2]
    pal = _build_palette(rows, 16, _snap3)
    pal.sort(key=luma)
    if luma(pal[-1]) < 4 * 255:  # no usable ink: trade one slot for white
        pal = _build_palette(rows, 15, _snap3)
        pal.sort(key=luma)
        pal.append((255, 255, 255))
    palette = pal + [(0, 0, 0)] * (16 - len(pal))
    if len(pal) < 16:
        palette = pal[:-1] + [(0, 0, 0)] * (16 - len(pal)) + [pal[-1]]
    pixels = _map_pixels(rows, palette, _dither_amount(rows, 16))
    return {"w": w, "h": h, "pixels": pixels, "palette": palette}


def _convert_dos(rows, salient=None):
    # Indices 0..15 stay the interpreter's (a standard text palette); the art
    # palette begins at 16. At 240 art entries no dithering is ever needed.
    w, h = len(rows[0]), len(rows)
    art = _build_palette(rows, 240, _snap6)
    base = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
            (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
            (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
            (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
    palette = [_snap6(c) for c in base] + art
    palette += [(0, 0, 0)] * (256 - len(palette))
    pixels = [[i + 16 for i in row] for row in _map_pixels(rows, art, 0)]
    return {"w": w, "h": h, "pixels": pixels, "palette": palette}


# ---- wave 2: the cell class (C64, ZX Spectrum +3) and the CPC ------------------

def _halve_width(rows):
    """320 -> 160 for the wide-pixel machines: an exact 2:1 average."""
    out = []
    for row in rows:
        out.append([tuple((a + b) // 2 for a, b in zip(row[x], row[x + 1]))
                    for x in range(0, len(row), 2)])
    return out


def _crop_width(rows, w, anchor="center"):
    """Crop the 320-wide master to a narrower band (the arc_image/reference/design.md
    geometry policy: crop, do not squeeze). Anchor "center" is the wave-2
    default (the Spectrum); "left" pins the crop to the top-left corner
    (Stefan's MSX1 ruling, 2026-08-11: the retained geometry sits better
    with the attribute grid when the origin is honest)."""
    x0 = 0 if anchor == "left" else (len(rows[0]) - w) // 2
    return [row[x0:x0 + w] for row in rows]


def _bayer_at(x, y, amount):
    return (_BAYER8[y & 7][x & 7] / 63.0 - 0.5) * 2 * amount


def _collapse_pairs(idx):
    """320-wide palette indices to 160: pairs collapse by agreement,
    disagreement resolved by global frequency. Never an average: averaging
    manufactures blend colors no palette holds (the grey-sky lesson: the
    invented 27-cube middleman greyed every soft purple; Polizei maps the
    master STRAIGHT to each machine's palette, and so do we now)."""
    freq = {}
    for row in idx:
        for i in row:
            freq[i] = freq.get(i, 0) + 1
    out = []
    for row in idx:
        half = []
        for x in range(0, len(row), 2):
            a, b = row[x], row[x + 1]
            half.append(a if a == b or freq.get(a, 0) >= freq.get(b, 0)
                        else b)
        out.append(half)
    return out


def _forced_cells(salient):
    """The halved cells a hint forces (both master pixels salient)."""
    if not salient:
        return frozenset()
    cells = {}
    for x, y in salient:
        cells[(x // 2, y)] = cells.get((x // 2, y), 0) + 1
    return frozenset(k for k, n in cells.items() if n == 2)


def _force_disc(idx, salient, value):
    """The moon ruling at halved width: a cell takes the disc's color only
    when BOTH master pixels are salient (either-pixel forcing erased the
    treeline in front of the moon, the A8 lesson)."""
    cells = {}
    for x, y in salient:
        cells[(x // 2, y)] = cells.get((x // 2, y), 0) + 1
    for (hx, y), n in cells.items():
        if n == 2:
            idx[y][hx] = value


# The spice (Stefan's ruling, twice: "a little", "only on spots", the
# R3 CPC wording made doctrine: replace color flat, SPRINKLE AT SEAMS).
# A pixel dithers only where BOTH hold: the master is locally SMOOTH
# there (a gradient band, not detail or texture), and the master sits
# genuinely between the two candidate colors (t in the 0.3..0.5
# midband, the exact strip where flat mapping hard-switches sides;
# 0.40 after Stefan's second too-much verdict).
# Everything else maps flat, so the dither draws the seam between two
# color bands, where the purple of the clouds meets the pink, and
# appears nowhere else.
_SPICE_MIN = 600
_SPICE_BAND = 0.40
_SMOOTH = 900  # neighbour distance below which the master counts as smooth


def _seam_mask(refs):
    """Where is the master locally smooth (gradient, not detail)? True
    where the right and down neighbours sit close in color."""
    h, w = len(refs), len(refs[0])
    mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r = refs[y][x + 1] if x + 1 < w else refs[y][x]
            d = refs[y + 1][x] if y + 1 < h else refs[y][x]
            mask[y][x] = (_dist(refs[y][x], r) < _SMOOTH
                          and _dist(refs[y][x], d) < _SMOOTH)
    return mask


def _spice(M, argb, x, y, smooth=True):
    """The final in-cell mapping with the artist's dither: flat nearest
    everywhere, except at a smooth seam where the master sits midway
    between the two nearest allowed colors. Returns the code into argb."""
    d = [_dist(M, a) for a in argb]
    i1 = min(range(len(argb)), key=lambda i: d[i])
    if not smooth or len(argb) < 2 or d[i1] < _SPICE_MIN:
        return i1
    i2 = min((i for i in range(len(argb)) if i != i1),
             key=lambda i: d[i])
    t = d[i1] / (d[i1] + d[i2])  # 0 (pure i1) .. 0.5 (halfway)
    if t < _SPICE_BAND:
        return i1  # clearly one side of the seam: flat
    return i2 if _BAYER8[y & 7][x & 7] / 64.0 < t else i1


# THE AUTHORED CPC -> COLODORE FALLBACK TABLE (Stefan's ruling, 2026-08-10).
# Arithmetic makes bad calls between these two palettes: the CPC's cube is
# saturated primaries, Colodore is muted, so plain nearest-distance sent
# CPC Green to Colodore Brown (picture 8's sky) and bumped Bright Yellow
# off Yellow (picture 1's window lights turned white). The artist states
# the intent instead; the tool only obeys. Each CPC ink lists its homes in
# order of preference, so an ink whose first home is already claimed by a
# more-used ink falls to the alternative its author chose, never to
# whatever the metric liked next. Keyed by the ink's RGB, since the CPC
# firmware's ink numbering and this file's cube order differ.
_C = {"Black": 0, "White": 1, "Red": 2, "Cyan": 3, "Purple": 4, "Green": 5,
      "Blue": 6, "Yellow": 7, "Orange": 8, "Brown": 9, "Light Red": 10,
      "Dark Grey": 11, "Grey": 12, "Light Green": 13, "Light Blue": 14,
      "Light Grey": 15}
_CPC_TO_COLODORE = {
    # STEFAN'S AUTHORED ROWS (2026-08-10). Only these inks are ruled; any
    # ink without a row keeps the automatic nearest match untouched. A
    # second home is where the ink goes when the first is already claimed
    # by another ink in that picture, which is how his conditional notes
    # express themselves ("Cyan if blue and bright blue are also used").
    # THE BLUES KEEP THEIR DISTANCE (Stefan, 2026-08-11): where two blue
    # tones stand side by side on the CPC, both Colodore blues should be
    # in play rather than collapsing to one. Each blue therefore lists
    # the other blue as a last resort, so a picture with several of them
    # spreads across Blue and Light Blue instead of flattening.
    (0x00, 0x00, 0x80): ("Blue", "Light Blue"),        # Blue
    (0x00, 0x00, 0xFF): ("Light Blue", "Blue"),        # Bright Blue
    (0x00, 0x80, 0xFF): ("Light Blue", "Cyan", "Blue"),  # Sky Blue
    (0xFF, 0x80, 0x00): ("Light Red",),                # Orange
    (0xFF, 0x00, 0xFF): ("Purple", "Light Red"),       # Bright Magenta
    (0x00, 0x80, 0x00): ("Green",),                    # Green
    (0x00, 0x80, 0x80): ("Green", "Cyan"),             # Cyan (teal)
    (0x00, 0xFF, 0x80): ("Cyan",),                     # Sea Green
    (0x00, 0xFF, 0x00): ("Light Green",),              # Bright Green
    (0x80, 0xFF, 0x00): ("Light Green",),              # Lime
    (0x80, 0x80, 0x00): ("Light Red",),                # Yellow (olive)
    (0xFF, 0xFF, 0x00): ("Yellow",),                   # Bright Yellow
    (0xFF, 0xFF, 0x80): ("Yellow",),                   # Pastel Yellow
    # Pastel Magenta lands on blank White automatically, which drained the
    # warm glow out of picture 2's church windows; Orange first, Light Red
    # where Orange is already claimed. (Two companion rows, Pink to Light
    # Red and Pastel Cyan to Light Green, were tried the same day and
    # REVERTED: they fixed their own regions but cost more elsewhere,
    # Stefan's verdict "the older one was genuinely better when all
    # colours worked together".)
    (0xFF, 0x80, 0xFF): ("Orange", "Light Red"),       # Pastel Magenta
}


def _inks_to_colodore(inks_rgb, usage):
    """THE ONE COLOUR DECISION OF THE FAMILY (Stefan's ruling, 2026-08-11:
    identify each CPC ink and map it 1:1 to the closest Colodore colour,
    his authored table ruling where it speaks). The C64 renders the result
    directly; the Plus/4 renders the SAME result on the TED's finer
    ladder. Computing it once is the point: when each machine resolved its
    own preferences the two drifted apart (picture 8's sky went green on
    the C64 and teal on the Plus/4), because a home taken in one palette
    is free in the other."""
    order = sorted(range(len(inks_rgb)), key=lambda i: -usage.get(i, 0))
    to_c64 = [0] * len(inks_rgb)
    taken = set()
    for i in order:
        prefs = [_C[n] for n in _CPC_TO_COLODORE.get(inks_rgb[i], ())]
        pick = next((k for k in prefs if k not in taken), None)
        if pick is None and prefs:
            # Every home this ink is allowed is already claimed, so it
            # COLLAPSES onto its first choice and shares it. The table
            # names those collapses on purpose (the cyan family, the two
            # blues, the yellows). Falling to the nearest unused colour
            # instead is what produced the cascade that cost picture 1
            # its window lights: sky blue took cyan, pastel cyan took
            # light green, pastel green took yellow, and the lights
            # ended up white.
            pick = prefs[0]
        elif pick is None:
            ranked = sorted(range(16),
                            key=lambda k: _dist(inks_rgb[i], _COLODORE[k]))
            pick = next((k for k in ranked if k not in taken), ranked[0])
        taken.add(pick)
        to_c64[i] = pick
    def _lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    _blues = (_C["Blue"], _C["Light Blue"])
    holders = [i for i in range(len(inks_rgb))
               if usage.get(i, 0) > 0 and to_c64[i] in _blues]
    targets = sorted({to_c64[i] for i in holders},
                     key=lambda k: _lum(_COLODORE[k]))
    if len(holders) == len(targets) > 1:
        holders.sort(key=lambda i: _lum(inks_rgb[i]))
        for i, k in zip(holders, targets):
            to_c64[i] = k
    return to_c64


def _c64_from_cpc(cpc):
    """THE C64 DERIVES FROM THE FROZEN CPC (Stefan's ruling, 2026-07-24:
    "the derived route without any alteration was already it"; the whole
    from-CPC corpus judged genuinely all good, "we cracked it"). The
    frozen, golden-pinned CPC conversion is the family's reduction; the
    C64 adds exactly two things: each CPC ink claims its own Colodore
    colour (injective, usage-ordered, plain metric; a hue-preference
    variant was tried the same day and withdrawn, it broke approved
    scenes, the record is in PROGRESS), and the multicolour cell solve.
    This is Stefan's own Photoshop cascade, ST to CPC to C64, made
    permanent machinery; the A8 keeps deriving from the C64 below."""
    pixels, pal = cpc["pixels"], cpc["palette"]
    h, w = cpc["h"], cpc["w"]
    inks_rgb = [_cpc_color(p % 27) for p in pal]
    usage = {}
    for row in pixels:
        for i in row:
            usage[i] = usage.get(i, 0) + 1
    order = sorted(range(len(inks_rgb)), key=lambda i: -usage.get(i, 0))
    to_c64 = _inks_to_colodore(inks_rgb, usage)
    grid = [[to_c64[pixels[y][x]] for x in range(w)] for y in range(h)]
    # the Polizei background vote among clashing cells
    clash = {}
    for cy in range(h // 8):
        for cx in range(w // 4):
            seen = {}
            for yy in range(8):
                for xx in range(4):
                    c = grid[cy * 8 + yy][cx * 4 + xx]
                    seen[c] = seen.get(c, 0) + 1
            if len(seen) > 4:
                for c, n in seen.items():
                    clash[c] = clash.get(c, 0) + n
    if clash:
        bg = max(clash, key=clash.get)
    else:
        allc = {}
        for row in grid:
            for c in row:
                allc[c] = allc.get(c, 0) + 1
        bg = max(allc, key=allc.get)
    pixels_out = [[0] * w for _ in range(h)]
    screen = []
    color = []
    for cy in range(h // 8):
        for cx in range(w // 4):
            hist = {}
            for yy in range(8):
                for xx in range(4):
                    c = grid[cy * 8 + yy][cx * 4 + xx]
                    if c != bg:
                        hist[c] = hist.get(c, 0) + 1
            freec = sorted(hist, key=hist.get, reverse=True)[:3]
            allowed = [bg] + freec
            for yy in range(8):
                for xx in range(4):
                    c = grid[cy * 8 + yy][cx * 4 + xx]
                    if c not in allowed:
                        c = min(allowed, key=lambda k: _dist(
                            _COLODORE[c], _COLODORE[k]))
                    pixels_out[cy * 8 + yy][cx * 4 + xx] = allowed.index(c)
            freec += [bg] * (3 - len(freec))
            screen.append((freec[0] << 4) | freec[1])
            color.append(freec[2])
    return {"w": w, "h": h, "pixels": pixels_out, "screen": screen,
            "color": color, "regs": [bg]}


def _convert_c64(rows, salient=None):
    # The C64 is a child of the frozen CPC: convert to the CPC first
    # (frozen, golden-pinned, Stefan's "genuinely perfect"), derive from
    # that. One reduction, expressed down the family, exactly as his
    # 80s ports derived from each other.
    return _c64_from_cpc(_convert_cpc(rows, salient))


def _dist_luma(a, b, w=20):
    """Luminance-dominant distance: dark things match dark first, colored
    second (Stefan's "think darker and brighter"). w=20 tuned by eye on the
    corpus; the cell solvers run on this, because attribute hardware
    punishes a wrong brightness far harder than a wrong hue (the moon must
    survive the sky's cell)."""
    ya = 2 * a[0] + 4 * a[1] + a[2]
    yb = 2 * b[0] + 4 * b[1] + b[2]
    return (w * (ya - yb) ** 2 // 49
            + (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


# The 15 real Spectrum colors: 0..7 the basic levels (black first), 8..14
# the bright levels of ink 1..7 (bright black is black). Index i decodes to
# (ink, bright) = (i, 0) below 8, (i - 7, 1) from 8 up.
_ZX15 = [_zx_color(i, 0) for i in range(8)] + \
        [_zx_color(i, 1) for i in range(1, 8)]



# The Spectrum's quiet mode: 1 renders the ruled near-monochrome
# philosophy (dominant ink on the black canvas per cell, accents only
# where a second color owns at least _ZX_ACCENT of the cell's 64
# pixels); 0 keeps every cell's own best pair. REJECTED at 1 (Stefan,
# 2026-08-12, "horrible": the accent bar eats thin colored lines, a
# 2px timber brace can never own 20 of a cell's 64 pixels, and the
# real complaint behind "too loud" was never saturation, it was FLAT
# cells, no paper used for shading; the cure is his authored mapping
# table plus a fg/bg mix where TMS siblings collide, not fewer inks).
_ZX_QUIET = 0
_ZX_ACCENT = 20

def _dist_zx15(a, b):
    # The Spectrum match: luminance-dominant plus a SATURATION term. The
    # palette is all full-blast primaries, and a dark muted brown or mauve
    # must land on the calm options (black, the darker hues) instead of a
    # screaming red of similar plain distance. The pipeline around this
    # metric is the plain Polizei one (no pre-curves, no vote biases); the
    # metric alone carries the taste.
    sa = max(a) - min(a)
    sb = max(b) - min(b)
    return _dist_luma(a, b, 20) + 3 * (sa - sb) ** 2


# Which Spectrum conversion route runs. "canopus" is the SHIPPED path
# (Stefan's ruling, 2026-08-13): due to the machine's attribute
# restrictions the automated conversion is deliberately a reasonable
# black-and-white artwork, the C-banded pattern stipple in bright white
# over black; every color route built in the 2026-08-12 session failed
# his eye against his own hand-authored art, and the color path on
# this machine is the AUTHOR'S, via the scr/unscr polish loop (hand
# art is stamped and never overwritten). The "derived" color route was
# deleted on his order after a final render; "rabenstein" and
# "inkline" stay as documented experimental dials.
# The inkline route's tone bar: a melted region fills white at or
# above this luminance, black below.
_ZXI_TONE = 100.0

# A same-fill boundary earns its ink line only when the two regions'
# tones differ by at least this much; 0 inks every boundary.
_ZXI_EDGE = 0.0

# The Rabenstein route's ink bar: a master pixel speaks (renders as
# ink) when any channel reaches this; below it, the black canvas.
_ZXR_INK = 64

# A cell vote below this margin is thin and may adopt its neighbours'
# ink (region coherence); a pixel below this fraction of its cell's lit
# tone is a shadow stroke and falls to black.
_ZXR_FIRM = 0.5
_ZXR_SHADOW = 0.45

# How many hue families the whole picture may spend (basic and bright
# of one hue count as one family; the moon's white is earned, never
# budgeted). 0 lifts the budget.
_ZXR_BUDGET = 4

# The Canopus texture engine: "stipple" (Stefan's keeper), "bayer"
# (decent, lattice artifacts), "atkinson" (rejected on review).
_ZXC_TEXTURE = "stipple"

# Band edges: 0 keeps the fixed classic edges, 1 adapts them to each
# picture's tonal quartiles ON A LEASH (Stefan's keeper, 2026-08-12,
# "C is a keeper", after the A/B/C round: raw adaptation destroyed
# picture 9, the leash holds each edge inside a window around the
# classic values). Fine adjustment expected.
_ZXC_ADAPT = 1

# The Canopus tone curve: middle steepness, and the solid floors where
# white stays white and shadow stays black.
_ZXC_GAIN = 1.4
_ZXC_WHITE = 0.90
_ZXC_BLACK = 0.10

_ZX3_ROUTE = "canopus"


def _convert_zx3(rows, salient=None):
    return _ZX3_ROUTES[_ZX3_ROUTE](rows, salient)


def _convert_zx3_canopus(rows, salient=None):
    """THE CANOPUS ROUTE (Stefan, 2026-08-12): the Spectrum drawn the
    way the machine was actually drawn on. Step one, THIS function: the
    FORM, black-and-white with dithering, derived straight from the
    master at the ruled window, because the master holds the most pixel
    density and the Spectrum's bitmap is per-pixel free; only color is
    celled, so a mono canvas pays no attribute tax anywhere. The recipe
    is the TRS-80 Model 4's, luminance, percentile contrast stretch,
    ordered Bayer at full resolution, the whole quality budget in the
    halftone. Step two, LATER and separately: color washes over chosen
    regions through the attributes, exactly the historical Spectrum
    manner, form first, color painted over it."""
    rows = [row[_MS1_CROP_X:_MS1_CROP_X + 256] for row in rows]
    w, h = len(rows[0]), len(rows)
    # (An MSX1-sourced tone field was tried and wiped on Stefan's test,
    # 2026-08-12: TMS owns no dark colors, so the MSX1 render arrives
    # tonally lifted and the mono form loses its blacks. The master is
    # the source.)
    lumas = [[(299 * r + 587 * g + 114 * b) / 255000.0 for r, g, b in row]
             for row in rows]
    flat = sorted(v for row in lumas for v in row)
    lo = flat[len(flat) * 2 // 100]
    hi = flat[len(flat) * 98 // 100]
    span = (hi - lo) or 1.0
    pixels = [[0] * w for _ in range(h)]
    # THE TEXTURE ENGINE (Stefan's visual ruling over seven candidates,
    # 2026-08-12): PATTERN STIPPLE is the keeper, "am absolut
    # schoensten, kommt am aehnlichsten an ZX Spectrum Art heran", the
    # hand-artist's five deliberate levels; BAYER stays selectable,
    # decent but with the lattice artifacts he named; ATKINSON stays as
    # a dial value, rejected on review. All textures run under one law:
    # solid white at and above the white floor, solid black at and
    # below the black ceiling, texture only between. THE MOON RULE
    # rides above all of them (his stipple review: picture 8's moon
    # fell into its halo's band and vanished; the brightest fat blob
    # outranks its band and renders solid white).
    field = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v = (lumas[y][x] - lo) / span
            field[y][x] = (v - 0.5) * _ZXC_GAIN + 0.5

    # The stipple's band edges, computed up front (the halo demotion
    # below needs to know where SOLID truly begins: the top band, not
    # only the white floor).
    if _ZXC_ADAPT:
        # ADAPTATION ON A LEASH (Stefan's split verdict, 2026-08-12:
        # raw quantiles made picture 14 stunning and destroyed picture
        # 9, whose dark-clustered mid-band collapsed all four edges to
        # 0.11 so the bedsheet flattened into solid white). Each edge
        # follows its picture's quantile only INSIDE a window around
        # the classic value: balanced pictures keep their tailored
        # edges, skewed ones are held near the classic stipple.
        mid = sorted(field[y][x] for y in range(h) for x in range(w)
                     if _ZXC_BLACK < field[y][x] < _ZXC_WHITE)
        if mid:
            q = (mid[len(mid) // 8], mid[len(mid) // 4],
                 mid[len(mid) // 2], mid[(3 * len(mid)) // 4])
            windows = ((0.10, 0.25), (0.22, 0.40),
                       (0.45, 0.65), (0.68, 0.86))
            t0, t1, t2, t3 = (max(lo_, min(hi_, v))
                              for v, (lo_, hi_) in zip(q, windows))
        else:
            t0, t1, t2, t3 = 0.15, 0.30, 0.55, 0.80
    else:
        t0, t1, t2, t3 = 0.15, 0.30, 0.55, 0.80

    bright = max((c for row in rows for c in row),
                 key=lambda c: 0.299*c[0] + 0.587*c[1] + 0.114*c[2])
    bset = set()
    if 0.299*bright[0] + 0.587*bright[1] + 0.114*bright[2] >= 150.0:
        cand = {(x, y) for y in range(h) for x in range(w)
                if _dist(rows[y][x], bright) < 1600}
        seen = set()
        for start_ in cand:
            if start_ in seen:
                continue
            blob, queue = {start_}, [start_]
            while queue:
                qx, qy = queue.pop()
                for nx, ny in ((qx+1, qy), (qx-1, qy),
                               (qx, qy+1), (qx, qy-1)):
                    if (nx, ny) in cand and (nx, ny) not in blob:
                        blob.add((nx, ny))
                        queue.append((nx, ny))
            seen |= blob
            xs = [q[0] for q in blob]
            ys = [q[1] for q in blob]
            if (len(blob) >= 24 and max(xs) - min(xs) >= 6
                    and max(ys) - min(ys) >= 6):
                core = {(qx, qy) for qx, qy in blob
                        if {(qx+1, qy), (qx-1, qy),
                            (qx, qy+1), (qx, qy-1)} <= blob}
                bset |= {(qx, qy) for qx, qy in blob
                         if (qx, qy) in core
                         or ({(qx+1, qy), (qx-1, qy), (qx, qy+1),
                              (qx, qy-1)} & core)}

    # A GLOW YIELDS TO ITS SOURCE (the eggless separation): pixels
    # within reach of the moon blob may not claim the solid white
    # floor; they render one level down, and the disc alone stays
    # absolute. No rings, no outlines, nothing global.
    if bset:
        # The halo is the WHOLE connected solid-white mass around the
        # disc (a six-pixel reach still drowned it): flood from the
        # blob through every floor-white neighbour and demote the lot.
        solid_gate = t3 if _ZXC_TEXTURE == "stipple" else _ZXC_WHITE
        halo, frontier = set(), set(bset)
        while frontier:
            nxt = set()
            for x, y in frontier:
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if 0 <= nx < w and 0 <= ny < h \
                            and (nx, ny) not in bset \
                            and (nx, ny) not in halo \
                            and field[ny][nx] >= solid_gate:
                        halo.add((nx, ny))
                        nxt.add((nx, ny))
            frontier = nxt
        demote = (t2 + t3) / 2 if _ZXC_TEXTURE == "stipple" \
            else _ZXC_WHITE - 0.001
        for x, y in halo:
            field[y][x] = min(field[y][x], demote)

    if _ZXC_TEXTURE == "atkinson":
        buf = [row[:] for row in field]
        for y in range(h):
            for x in range(w):
                src = field[y][x]
                if src >= _ZXC_WHITE:
                    pixels[y][x] = 1
                    continue
                if src <= _ZXC_BLACK:
                    pixels[y][x] = 0
                    continue
                out = 1 if buf[y][x] >= 0.5 else 0
                pixels[y][x] = out
                err = (buf[y][x] - out) / 8.0
                for dx, dy in ((1, 0), (2, 0), (-1, 1), (0, 1), (1, 1),
                               (0, 2)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h \
                            and _ZXC_BLACK < field[ny][nx] < _ZXC_WHITE:
                        buf[ny][nx] += err
    elif _ZXC_TEXTURE == "bayer":
        for y in range(h):
            for x in range(w):
                v = field[y][x]
                if v >= _ZXC_WHITE:
                    pixels[y][x] = 1
                elif v <= _ZXC_BLACK:
                    pixels[y][x] = 0
                else:
                    thr = (_BAYER8[y & 7][x & 7] + 0.5) / 64.0
                    pixels[y][x] = 1 if v > thr else 0
    else:                              # "stipple", the keeper
        P25 = {(0, 0)}
        P50 = {(0, 0), (1, 1)}
        P75 = {(0, 0), (1, 1), (0, 1)}
        # ADAPTIVE BAND EDGES (Stefan's detail complaint: fixed edges
        # lose structures whose tones cluster inside one band): the
        # five levels stay five, but their edges sit at the QUARTILES
        # of this picture's own mid-band tones, hoisted above.
        for y in range(h):
            for x in range(w):
                v = field[y][x]
                if v >= _ZXC_WHITE:
                    pixels[y][x] = 1
                elif v <= _ZXC_BLACK:
                    pixels[y][x] = 0
                else:
                    q = (x & 1, y & 1)
                    if v < t1:
                        pixels[y][x] = 1 if q in P25 and v >= t0 else 0
                    elif v < t2:
                        pixels[y][x] = 1 if q in P50 else 0
                    elif v < t3:
                        pixels[y][x] = 1 if q in P75 else 0
                    else:
                        pixels[y][x] = 1
    for x, y in bset:
        pixels[y][x] = 1               # the moon outranks its band
    # (A one-pixel dark rim around the blob was tried here and reverted
    # the same hour, Stefan: it egged picture 1's moon and outlined
    # every fat bright blob. The disc separates from its halo through
    # the adaptive bands instead: the halo lands one level below solid
    # on its own.)

    # Every cell: BRIGHT white ink over the black canvas (Stefan,
    # 2026-08-12: "all WHITE in WHITE, not dark white"; the dither's
    # color belongs on the vibrant tier, and black paper takes the
    # bright bit for free). The wash step retints per region, staying
    # on the bright plane.
    attrs = [0x47] * ((w // 8) * (h // 8))
    return {"w": w, "h": h, "pixels": pixels, "attrs": attrs}


def _convert_zx3_rabenstein(rows, salient=None):
    """THE RABENSTEIN ROUTE (Stefan's manner, measured off his own
    hand-painted Spectrum picture 8 and built to its grammar,
    2026-08-12): black is the paper virtually everywhere (62 percent of
    his picture is black; 83 percent of its cells are one ink over
    black), the shading is the master's OWN stroke texture (his ink
    continues into its neighbour 66 percent horizontally, clustered
    branch-work, never Bayer, which is why synthetic halftone offends
    his eye), color is a wash per region with the bright bit carrying
    depth, and accents are tiny and deliberate (two red pixels of eyes;
    one white moon). Historically he derived these from the hires
    Plus/4 by reducing colors in the same style; the master corpus
    descends from that school, so the master's pixels carry the stroke
    texture 1:1 at this window and the route simply keeps them: a pixel
    is INK where the master speaks (any channel above the bar), BLACK
    where it is quiet, and the cell's ink is the snap of its dominant
    speaking color, over black paper always. Black paper leaves the
    bright bit free per cell, the machine's one gift, so tiers mix
    freely as depth exactly as in his art."""
    rows = [row[_MS1_CROP_X:_MS1_CROP_X + 256] for row in rows]
    w, h = len(rows[0]), len(rows)
    cells_x, cells_y = w // 8, h // 8
    pixels = [[0] * w for _ in range(h)]
    ink_mask = [[max(c) >= _ZXR_INK for c in row] for row in rows]

    def lum(c):
        return 2 * c[0] + 4 * c[1] + c[2]

    # Pass 1: each cell votes its ink (the dominant speaking color,
    # snapped through the Spectrum's own metric) and remembers how
    # decisive the vote was.
    inks = [[None] * cells_x for _ in range(cells_y)]
    margin = [[1.0] * cells_x for _ in range(cells_y)]
    domlum = [[0.0] * cells_x for _ in range(cells_y)]
    for cy in range(cells_y):
        for cx in range(cells_x):
            votes = {}
            for yy in range(8):
                for xx in range(8):
                    x, y = cx * 8 + xx, cy * 8 + yy
                    if ink_mask[y][x]:
                        k = min(range(1, 15),
                                key=lambda k: _dist_zx15(rows[y][x],
                                                         _ZX15[k]))
                        votes[k] = votes.get(k, 0) + 1
            if not votes:
                continue
            ranked = sorted(votes, key=votes.get, reverse=True)
            inks[cy][cx] = ranked[0]
            total = sum(votes.values())
            second = votes[ranked[1]] if len(ranked) > 1 else 0
            margin[cy][cx] = (votes[ranked[0]] - second) / total
            best = max(((rows[cy*8+yy][cx*8+xx])
                        for yy in range(8) for xx in range(8)
                        if ink_mask[cy*8+yy][cx*8+xx]), key=lum)
            domlum[cy][cx] = float(lum(best))
    # Pass 1.5: THE GLOBAL INK BUDGET (Stefan's economy, measured off
    # his hand art, 2026-08-12: the Village is FOUR families, blue as
    # the world, cyan as the light, white for moon and snow, over the
    # black canvas). The picture's hue families are ranked by how much
    # ink they carry; the budget keeps the top few, and every cell
    # whose ink lost its family remaps to the nearest kept ink through
    # the Spectrum's own metric, tier following luminance. Basic and
    # bright of one hue are ONE family, both tiers stay available: the
    # two blues as depth is his grammar, not two spends. The moon rule
    # overrides later regardless, an earned accent never budgeted.
    if _ZXR_BUDGET:
        fam_w = {}
        for cy in range(cells_y):
            for cx in range(cells_x):
                k = inks[cy][cx]
                if k is not None:
                    f = k if k < 8 else k - 7
                    fam_w[f] = fam_w.get(f, 0) + 1
        kept = set(sorted(fam_w, key=fam_w.get, reverse=True)
                   [:_ZXR_BUDGET])
        allowed = [k for k in range(1, 15)
                   if (k if k < 8 else k - 7) in kept]
        for cy in range(cells_y):
            for cx in range(cells_x):
                k = inks[cy][cx]
                if k is None:
                    continue
                f = k if k < 8 else k - 7
                if f not in kept:
                    inks[cy][cx] = min(
                        allowed, key=lambda a: _dist_zx15(_ZX15[k],
                                                          _ZX15[a]))

    # Pass 2: REGION COHERENCE (his art holds one hue per region; a
    # master gradient flipped neighbouring cells' votes and the sky
    # checkered). A cell whose vote was thin adopts the ink most of its
    # neighbours settled on. Two sweeps settle it.
    for _sweep in range(2):
        for cy in range(cells_y):
            for cx in range(cells_x):
                if inks[cy][cx] is None or margin[cy][cx] > _ZXR_FIRM:
                    continue
                nb = {}
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < cells_y and 0 <= nx < cells_x \
                            and inks[ny][nx] is not None:
                        nb[inks[ny][nx]] = nb.get(inks[ny][nx], 0) + 1
                if nb:
                    top = max(nb, key=nb.get)
                    if nb[top] >= 3:
                        inks[cy][cx] = top
    # THE MOON RULE, third appearance (the MSX's earned salience, his
    # own art's grammar: the moon is BrWhite, the picture's one glow):
    # the brightest fat contiguous blob renders as bright white ink,
    # solid.
    bright = max((c for row in rows for c in row), key=lum)
    bset = set()
    if lum(bright) >= 1071:            # 150 luma on the 2-4-1 scale
        cand = {(x, y) for y in range(h) for x in range(w)
                if _dist(rows[y][x], bright) < 1600}
        seen = set()
        for start in cand:
            if start in seen:
                continue
            blob, queue = {start}, [start]
            while queue:
                px_, py_ = queue.pop()
                for nx, ny in ((px_+1, py_), (px_-1, py_),
                               (px_, py_+1), (px_, py_-1)):
                    if (nx, ny) in cand and (nx, ny) not in blob:
                        blob.add((nx, ny))
                        queue.append((nx, ny))
            seen |= blob
            xs = [q[0] for q in blob]
            ys = [q[1] for q in blob]
            if (len(blob) >= 24 and max(xs) - min(xs) >= 6
                    and max(ys) - min(ys) >= 6):
                core = {(qx, qy) for qx, qy in blob
                        if {(qx+1, qy), (qx-1, qy),
                            (qx, qy+1), (qx, qy-1)} <= blob}
                bset |= {(qx, qy) for qx, qy in blob
                         if (qx, qy) in core
                         or ({(qx+1, qy), (qx-1, qy), (qx, qy+1),
                              (qx, qy-1)} & core)}

    # Pass 3: emit. The stroke texture is the master's own (ink where
    # the master speaks), with THE RELATIVE SHADOW RULE for density:
    # a pixel well below its cell's lit tone is a shadow stroke and
    # falls to black, which is how his art shades WITHIN a region.
    attrs = []
    for cy in range(cells_y):
        for cx in range(cells_x):
            ink = inks[cy][cx]
            if ink is None:
                attrs.append(0x07)
                continue
            moon_here = any((cx * 8 + xx, cy * 8 + yy) in bset
                            for yy in range(8) for xx in range(8))
            bar = domlum[cy][cx] * _ZXR_SHADOW
            if moon_here:
                # His moon cells are disc-on-black: bright white ink,
                # and the blob is the ONLY ink (painting the cell's
                # glow pixels white too slabbed the sky).
                ink = 14
                for yy in range(8):
                    for xx in range(8):
                        x, y = cx * 8 + xx, cy * 8 + yy
                        pixels[y][x] = 1 if (x, y) in bset else 0
            else:
                for yy in range(8):
                    for xx in range(8):
                        x, y = cx * 8 + xx, cy * 8 + yy
                        pixels[y][x] = 1 if (ink_mask[y][x]
                                             and lum(rows[y][x]) >= bar) \
                            else 0
            ink_n = ink if ink < 8 else ink - 7
            attrs.append(ink_n | (0x40 if ink >= 8 else 0))
    return {"w": w, "h": h, "pixels": pixels, "attrs": attrs}


def _convert_zx3_inkline(rows, salient=None):
    """THE INKLINE ROUTE (Stefan, 2026-08-12: "black and white art,
    like a black and white comic"). A comic is ink lines and committed
    fills, never halftone, and the masters make both EXACT: they are
    palette art, so a region boundary is a precise color change. The
    master's one-pixel dither melts into solid regions under a mode
    filter, each region commits to black or white by its tone, and an
    ink line is drawn only where two regions of the SAME fill meet (a
    white line between two blacks, a black line between two whites);
    a black-white boundary is its own line. Mono pays zero attribute
    tax: the Spectrum's whole clash disease vanishes."""
    rows = [row[_MS1_CROP_X:_MS1_CROP_X + 256] for row in rows]
    w, h = len(rows[0]), len(rows)

    def lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    # Melt the dither: two passes of a 3x3 mode filter over the exact
    # master colors turn pixel-interleave into the region it paints.
    grid = [list(r) for r in rows]
    for _pass in range(2):
        nxt = [list(r) for r in grid]
        for y in range(h):
            for x in range(w):
                cnt = {}
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx_ = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx_ < w:
                            c = grid[ny][nx_]
                            cnt[c] = cnt.get(c, 0) + 1
                nxt[y][x] = max(cnt, key=cnt.get)
        grid = nxt

    # Fills: a region is white when its color's tone clears the bar.
    fill = [[1 if lum(grid[y][x]) >= _ZXI_TONE else 0 for x in range(w)]
            for y in range(h)]
    pixels = [[fill[y][x] for x in range(w)] for y in range(h)]
    # Ink lines where same-fill regions of different color meet.
    for y in range(h):
        for x in range(w):
            for dy, dx in ((0, 1), (1, 0)):
                ny, nx_ = y + dy, x + dx
                if ny >= h or nx_ >= w:
                    continue
                if grid[y][x] != grid[ny][nx_] \
                        and fill[y][x] == fill[ny][nx_] \
                        and abs(lum(grid[y][x])
                                - lum(grid[ny][nx_])) >= _ZXI_EDGE:
                    # The line hierarchy: near-tones share a region's
                    # silence, a line is earned by real contrast.
                    pixels[y][x] = 1 - fill[y][x]
                    break
    attrs = [0x07] * ((w // 8) * (h // 8))
    return {"w": w, "h": h, "pixels": pixels, "attrs": attrs}


_ZX3_ROUTES = {"canopus": _convert_zx3_canopus,
               "rabenstein": _convert_zx3_rabenstein,
               "inkline": _convert_zx3_inkline}


def _cpc_from_c64(c64, refs=None, skip=frozenset()):
    """The CPC FROM THE C64 CONVERSION (Stefan's base ruling): same
    160-wide 2:1 geometry, the C64's pixels and dither verbatim, every
    Colodore color recolored to its nearest cube ink. GREYS are re-read
    through the master DIRECTLY IN CUBE SPACE, not through Colodore's
    sixteen: the C64 dithers grey against color as a Colodore idiom, and
    re-reading both halves through Colodore collapsed the weave flat
    (Stefan's question, where did the dither go); the cube's own
    in-between shades keep the shimmer alive as navy against blue. The
    grey-axis ban rides along: a chromatic master pixel never lands on
    mid-grey or white."""
    lv = (0, 0x80, 0xFF)
    cube = [(lv[r], lv[g], lv[b])
            for r in range(3) for g in range(3) for b in range(3)]

    def dist_cpc(a, b):
        sa = max(a) - min(a)
        sb = max(b) - min(b)
        if sa >= 32 and sb == 0 and b != (0, 0, 0):
            return 1 << 30
        return _dist(a, b) + 4 * max(0, sa - sb) * sa

    to_cube = [_nearest(_COLODORE[c], cube) for c in range(16)]
    cidx = _c64_indices(c64)
    h, w = len(cidx), len(cidx[0])
    raw = [[0] * w for _ in range(h)]
    memo = {}
    for y in range(h):
        for x in range(w):
            c = cidx[y][x]
            col = _COLODORE[c]
            k = to_cube[c]
            if (refs is not None and (x, y) not in skip
                    and max(col) - min(col) < 32):
                M = refs[y][x]
                if max(M) - min(M) >= 32:
                    if M not in memo:
                        memo[M] = _nearest(M, cube, metric=dist_cpc)
                    k = memo[M]
            raw[y][x] = k
    # Ink budget: the sixteen most frequent cube colors; stragglers to
    # their nearest kept ink (the Polizei recipe, unchanged).
    freq = {}
    for row in raw:
        for k in row:
            freq[k] = freq.get(k, 0) + 1
    inks = sorted(freq, key=freq.get, reverse=True)[:16]
    order = {k: i for i, k in enumerate(inks)}
    stray = {}
    pixels = []
    for row in raw:
        out = []
        for k in row:
            if k in order:
                out.append(order[k])
            else:
                if k not in stray:
                    stray[k] = order[min(
                        inks, key=lambda q: _dist(cube[k], cube[q]))]
                out.append(stray[k])
        pixels.append(out)
    pal = list(inks)
    while len(pal) < 16:
        pal.append(0)  # unused slots; a duplicate ink is legal hardware
    return {"w": w, "h": h, "pixels": pixels, "palette": pal,
            "regs": [0]}


def _convert_cpc(rows, salient=None):
    # THE FIRST EXPRESSION OF THE SHARED INTERMEDIATE (Stefan's ruling,
    # 2026-07-23, reversing the old C64-first derivation): CPC mode 0 is
    # the one 8-bit target with no cell constraint, sixteen free inks
    # per pixel, so it renders the reduction pure: what his eye approves
    # here is the family's shared look, and every machine after adds
    # exactly one new variable, its own constraint. Salience is handled
    # by the intermediate itself (_protect_extremes); the hint sidecar
    # is not consulted.
    # Pairs collapse by agreement, NEVER an average (the Polizei doctrine;
    # plain averaging was isolated 2026-08-10 and disqualified: its
    # mid-tone smears escape the dark sanctuary and the ground dots
    # return). An agreeing pair blends; a disagreeing pair keeps its
    # BRIGHTER member, which is what puts the bedpost back on its wall
    # (Stefan's ruling, 2026-08-10: "the bedpost fix is still the best").
    #
    # THE TRUSS CHAPTER, closed with it. Picture 1's half-timbered walls
    # carry a lattice of ONE-PIXEL vertical posts at 320, sub-Nyquist for
    # a 160-wide target: any pairwise rule must drop either the post or
    # the wall between two posts. Eleven rules were built and scored
    # against it (continuity, ground-decides at three margins, rarity at
    # five, rarity-with-continuity at four, plain averaging); the ones
    # that held the lattice cost bright highlights everywhere else, and
    # Stefan judged the highlights worth more. PROGRESS holds the full
    # scoreboard. Do not reopen without him.
    half = []
    for row in rows:
        out_row = []
        for x in range(0, len(row), 2):
            a, b = row[x], row[x + 1]
            if _dist(a, b) <= 2400:
                out_row.append(tuple((p + q) // 2 for p, q in zip(a, b)))
            else:
                out_row.append(a if sum(a) >= sum(b) else b)
        half.append(out_row)
    h, w = len(half), len(half[0])
    lv = (0, 0x80, 0xFF)
    cube = [(lv[r], lv[g], lv[b])
            for r in range(3) for g in range(3) for b in range(3)]
    free, idx = _reduce_master(half, 16)
    expr = _express(free, _usage_order(idx, len(free)), cube)
    # ink slots: distinct cube colours in usage order, stragglers merge
    inks = []
    slot = {}
    for i in _usage_order(idx, len(free)):
        k = expr[i]
        if k not in slot:
            if len(inks) < 16:
                slot[k] = len(inks)
                inks.append(k)
            else:
                slot[k] = slot[min(
                    slot, key=lambda q: _dist(cube[k], cube[q]))]
    pixels = [[slot[expr[idx[y][x]]] for x in range(w)] for y in range(h)]
    pal = list(inks)
    while len(pal) < 16:
        pal.append(0)  # unused slots; a duplicate ink is legal hardware
    return {"w": w, "h": h, "pixels": pixels, "palette": pal,
            "regs": [0]}


# The 128 colors an Atari color register can hold apart: 16 hues x 8
# luminances. GTIA does not decode luminance bit 0, so only even values
# exist; the byte is hue<<4 | luma, written to the register verbatim.
_GTIA128 = [(hue << 4) | (luma << 1) for hue in range(16) for luma in range(8)]
_GTIA_RGB = [_gtia_color(v) for v in _GTIA128]


# Colodore to GTIA, computed against the current wheel (a future measured
# wheel shifts the whole mapping with it); the frozen table is printed in
# the C.7 chapter for Stefan's ruling, the Colodore way. INJECTIVE: two
# C64 colors never share a GTIA byte (plain nearest merged red and orange
# into one, and a fire would lose its shading), so the best matches claim
# their bytes first and a collision takes its next-best unused one.
def _c64_to_gtia():
    order = sorted(range(16), key=lambda i: min(
        _dist(_COLODORE[i], g) for g in _GTIA_RGB))
    out = [0] * 16
    taken = set()
    for i in order:
        ranked = sorted(range(len(_GTIA_RGB)),
                        key=lambda k: _dist(_COLODORE[i], _GTIA_RGB[k]))
        for k in ranked:
            if _GTIA128[k] not in taken:
                out[i] = _GTIA128[k]
                taken.add(_GTIA128[k])
                break
    return out


# The split penalty for the A8 block solver, in _dist units per pixel of
# one line: a palette change between 8-line blocks must save at least one
# line's worth of visibly wrong pixels, or the blocks share a set.
_A8_HOLD = 8000


def _c64_indices(c64):
    """A C64 native as a per-pixel Colodore index image: 0-3 codes resolved
    through the background register, the screen nibbles, and color RAM."""
    w, h = c64["w"], c64["h"]
    bg = c64["regs"][0]
    cells_x = w // 4
    out = []
    for y in range(h):
        row = []
        base = (y // 8) * cells_x
        for x in range(w):
            code = c64["pixels"][y][x]
            if code == 0:
                row.append(bg)
            else:
                cell = base + x // 4
                s = c64["screen"][cell]
                row.append((s >> 4) & 15 if code == 1 else
                           s & 15 if code == 2 else
                           c64["color"][cell] & 15)
        out.append(row)
    return out


def _degrey(cidx, refs, skip=frozenset()):
    """The C64's grey ramp is a Colodore idiom: soft greys that its muted
    palette absorbs (Stefan's observation). A sibling machine re-reads
    every grey C64 pixel through the MASTER: if the master is chromatic
    there (the sea's blue shimmer, the rock's brown), the pixel becomes
    the nearest CHROMATIC Colodore index instead, and only true neutrals
    stay grey. The inherited dither pattern is untouched, only its color
    reading changes; without this the CPC ran full of harsh cube grey
    and the A8 elected grey to whole line-registers (the grey bar)."""
    chroma = [c for c in range(16)
              if max(_COLODORE[c]) - min(_COLODORE[c]) >= 32]
    out = []
    memo = {}
    for y, row in enumerate(cidx):
        orow = []
        for x, c in enumerate(row):
            col = _COLODORE[c]
            # A salient-forced pixel is exempt: the disc's white is
            # deliberately brighter than the master (the promotion
            # ruling), and re-reading it through the master undoes it.
            if (x, y) not in skip and max(col) - min(col) < 32:
                M = refs[y][x]
                if max(M) - min(M) >= 32:
                    key = (c, M)
                    if key not in memo:
                        memo[key] = min(
                            chroma,
                            key=lambda k: _dist(M, _COLODORE[k]))
                    c = memo[key]
            orow.append(c)
        out.append(orow)
    return out


def _a8_from_c64(c64, refs=None, skip=frozenset()):
    """The A8 solve FROM THE C64 CONVERSION, not from the master (Stefan's
    R4 ruling, the way the 80s actually ported): the C64's cell solver has
    already made every taste decision, the geometry is pixel-identical
    (160 wide, 2:1), Colodore's sixteen map near one-to-one onto GTIA's
    wheel, and the input's own 8-line cell rhythm becomes the segment
    grid, so palette changes land where the art itself changes instead of
    chopping a cliff mid-object (four rounds of master-based solving said
    so). The cost, accepted: the A8 shows C64 art on Atari rather than
    exploiting the full 128-color wheel; per-hue luma refinement is staged
    behind Stefan's judgment of the plain mapping. Masters stay the only
    author-facing input; this is plumbing, and a hand-polished .C64 flows
    through it to the whole family (the inheritance ruling)."""
    w, h = c64["w"], c64["h"]
    cidx = _c64_indices(c64)
    if refs is not None:
        cidx = _degrey(cidx, refs, skip)
    gt = _c64_to_gtia()
    grgb = [_gtia_color(b) for b in gt]

    # Pick and remap on the dumping metric (the CPC lesson, one level
    # deeper): by plain distance the night sky's blue is closer to dark
    # grey than to black, and a segment that dropped blue turned the sky
    # grey. A saturated color keeps its family: it costs extra to serve
    # it with a grey register.
    def dd(a, b):
        sa = max(grgb[a]) - min(grgb[a])
        sb = max(grgb[b]) - min(grgb[b])
        # Symmetric: losing chroma costs (a dusk purple must not grey),
        # and GAINING it costs too (the dropped cliff-grey was remapping
        # to sea-blue, which was numerically nearest and free of penalty;
        # grey rock goes to black, never to blue: Stefan's stones).
        return (_dist(grgb[a], grgb[b]) + 3 * max(0, sa - sb) * sa
                + 3 * max(0, sb - sa) * sb)

    dmat = [[dd(a, b) for b in range(16)] for a in range(16)]

    # Per-block histograms: the block is the C64's 8-line cell row.
    nb = (h + 7) // 8
    hists = []
    for b in range(nb):
        hist = [0] * 16
        for y in range(b * 8, min(h, b * 8 + 8)):
            for c in cidx[y]:
                hist[c] += 1
        hists.append(hist)

    def seg_cost(hist, picks):
        return sum(hist[c] * min(dmat[c][a] for a in picks)
                   for c in range(16) if hist[c])

    lum = lambda c: 2 * grgb[c][0] + 4 * grgb[c][1] + grgb[c][2]

    def seg_pick(hist):
        """A range's four colors: greedy error minimization, then the
        defenses, INSIDE the pick so the segment optimizer prices them
        (they ran after the boundaries were fixed once, and the DP
        merged the sun band into the cliff band without knowing the sun
        would evict the cliff's brown: Stefan's color split). Bright
        star and dark anchor claim registers; a defense's victim is a
        neutral before it is ever a chromatic."""
        picks = []
        pool = [c for c in range(16) if hist[c]]
        while pool and len(picks) < 4:
            best, bc = None, None
            for cand in pool:
                total = 0
                for c in range(16):
                    cnt = hist[c]
                    if cnt:
                        d = dmat[c][cand]
                        for a in picks:
                            if dmat[c][a] < d:
                                d = dmat[c][a]
                        total += cnt * d
                if bc is None or total < bc:
                    best, bc = cand, total
            picks.append(best)
            pool.remove(best)
        if not picks:
            picks = [0]
        while len(picks) < 4:
            picks.append(picks[-1])

        present = [c for c in range(16) if hist[c] >= 8]
        protected = set()

        def force_in(star):
            def without(v):
                trial = [star if p == v else p for p in picks]
                return seg_cost(hist, trial)
            victims = set(picks) - protected
            neutrals = {v for v in victims
                        if max(grgb[v]) - min(grgb[v]) < 32}
            pool2 = neutrals if neutrals else victims
            victim = min(pool2, key=without)
            return [star if p == victim else p for p in picks]

        if present:
            star = max(present, key=lum)
            if star not in picks and lum(star) - max(
                    lum(p) for p in picks) > 150:
                picks = force_in(star)
            if star in picks:
                protected.add(star)
            dark = min(present, key=lum)
            if dark not in picks and min(
                    lum(p) for p in picks) - lum(dark) > 150:
                picks = force_in(dark)
        return picks

    # Segments over BLOCKS by dynamic programming, as before but on the
    # cell-row grid: a boundary exists only where it saves more error
    # than the penalty, and it can only land where the C64 art itself
    # changes.
    lam = w * _A8_HOLD
    best = [0] + [None] * nb
    cut = [0] * (nb + 1)
    memo = {}
    for j in range(nb):
        bj, bi = None, 0
        for i in range(j + 1):
            if best[i] is None:
                continue
            key = (i, j)
            if key not in memo:
                merged = [0] * 16
                for b in range(i, j + 1):
                    for c in range(16):
                        merged[c] += hists[b][c]
                memo[key] = seg_cost(merged, seg_pick(merged))
            total = best[i] + memo[key] + lam
            if bj is None or total < bj:
                bj, bi = total, i
        best[j + 1] = bj
        cut[j + 1] = bi
    bounds = []
    j = nb
    while j > 0:
        bounds.append((cut[j], j - 1))
        j = cut[j]
    bounds.reverse()

    from itertools import permutations
    pixels, lines = [], []
    prev = None
    for i, j in bounds:
        merged = [0] * 16
        for b in range(i, j + 1):
            for c in range(16):
                merged[c] += hists[b][c]
        picks = seg_pick(merged)  # defenses included, the DP saw them
        if prev is None:
            regs = sorted(set(picks), key=lambda p: -merged[p])
            while len(regs) < 4:
                regs.append(regs[-1])
        else:
            regs = min(
                (list(perm) for perm in permutations(picks)),
                key=lambda perm: sum(
                    0 if perm[k] == prev[k] else dmat[perm[k]][prev[k]]
                    for k in range(4)))
        prev = regs
        # Dropped colors remap FLAT to their nearest register: an A8-level
        # dither layer was tried and retired (it speckled the cliff stones;
        # Stefan's verdict). The A8 inherits the C64's seam dither through
        # the pixels themselves, and that is the only spice it carries.
        remap = [min(range(4), key=lambda k: dmat[c][regs[k]])
                 for c in range(16)]
        for y in range(i * 8, min(h, (j + 1) * 8)):
            lines += [gt[r] for r in regs]
            pixels.append([remap[c] for c in cidx[y]])
    return {"w": w, "h": h, "pixels": pixels, "lines": lines}


# THE PROTECTION BAR (Stefan's direction B, 2026-08-11). A colour cluster
# had to hold 120 pixels of a 1280-pixel strip, 9.4 percent, before the
# election was priced for losing it, while the darkest anchor was defended
# from 40 pixels, 3.1 percent, and at double weight. Black was cheap to
# protect and shadow expensive, which is the asymmetry behind his "too
# much black and a lot is flattening": measured over the corpus, a third
# of all strips elected four registers but painted only three, and the
# wasted one was usually the shadow rung.
_A8_MASS = 120

# How many of the strip's own colours stand as candidates, and how much
# of the strip they must account for before the pipeline believes it is
# looking at palette art rather than a photograph. Set _A8_EXACT to 0 to
# go back to clustering unconditionally.
_A8_EXACT = 8
_A8_EXACT_COVER = 0.90

# What a chromatic colour pays to be housed by a neutral of the same
# brightness. 1 is no loyalty at all, which is what the election's main
# error term used to have.
_A8_TINT = 3

# And what a neutral pays to be housed by a chromatic register of the
# same brightness. 0 is the old one-way rule.
_A8_TINT_BOTH = 3

# Whether a strip may hold only one hard bright member (see the white
# canvas in _a8_seg_analysis). 0 restores the July behaviour of two.
_A8_ONE_BRIGHT = 1

# Whether the moon rule decrees its register (1, July) or merely pays a
# heavy price for losing it (0, with this weight).
_A8_MOON_HARD = 1
_A8_MOON_WEIGHT = 8

# The darkest anchor's own bar, and the weight it carries once it clears
# it. This is the other half of the asymmetry: the anchor is defended
# from 40 pixels at DOUBLE weight while every other cluster needs 120 at
# single, so the strip pays three times more to lose its black than to
# lose its shadow.
_A8_DMASS = 40
_A8_DWEIGHT = 2

# THE GUARD. A register may only serve a pixel within this much luma and
# this much chroma of the source. July's 40 and 70 keep a dark purple
# dithering toward purple and black, never blue, which was right; but
# measured over the corpus they leave 74 to 91 percent of all pixels with
# exactly ONE legal register, so error diffusion has no partner to flip
# to and whole regions render poster-flat with no halftone at all. That
# is the "flattening way too much". Widening the luma bound is what lets
# the diffusion mix a lighter and a darker register into a colour the
# four-entry palette cannot name.
_A8_GUARD_L = 40.0
_A8_GUARD_C = 70.0

# How far the guard may travel from the source to follow the error the
# diffusion has actually accumulated, per channel. THE LOGIC ERROR THIS
# REPAIRS (found 2026-08-11 on Stefan's reading, "this looks more like a
# logic error than anything else"): the guard was recomputed from the
# UNTOUCHED source for every pixel, so in a region where only one
# register is legal the candidate set never changed however much error
# piled up. The error could not be discharged and simply compounded:
# measured, it reached 9531 on a 0-255 scale in picture 6, with 94
# percent of the picture carrying more than a full channel of it, and
# since the accumulated colour is clamped to 0-255 before the cost is
# computed, those regions were choosing against a pinned black or white
# rather than a colour. Following the error instead lets a flat zone
# spend a second register the band already holds, which is Stefan's own
# proposal ("paint what is missing there in one of the darker colours
# that is already accepted by the band"), and it fires only where error
# has actually built up, so an isolated highlight like picture 8's moon
# keeps its own register. REJECTED BY STEFAN 2026-08-11 ("the diffusion
# repair doesn't look good, it creates artifacts that shouldn't be there,
# dots everywhere, look at the ceiling in the picture of the chapel"):
# discharging the error does scatter it, and on a smooth ceiling that
# reads as dirt. Left as a dial at 0, where the guard stays centred on
# the source exactly as in July. The divergence it was built to repair is
# real but harmless in the picture; the election was the actual fault.
_A8_DRIFT = 0.0

# How far the diffusion buffer may depart from the source before it is
# held, per channel. A flat region that cannot discharge has NO fixed
# point: Floyd-Steinberg conserves the error, so it is handed on forever
# and grows without bound, which is how picture 6 reached 9531. Holding
# the buffer makes the runaway impossible by construction and keeps the
# accumulated colour a real colour instead of a pinned black or white.
# Set to 0 (or None) for the unbounded July buffer, which is where it
# sits: it is only meaningful beside _A8_DRIFT, and that is off.
_A8_ECLAMP = 0.0

# What share of a strip a register must actually paint to keep its slot.
# The moon rule forces the brightest cluster in from ten pixels out of
# 1280 and the optimizer may not price it away; in picture 18 that bought
# a luma-230 register in four separate strips which the pixel stage then
# never used once, a quarter of the palette spent on nothing. A register
# painting less than this is retired and the strip elects again without
# it. Set to 0 to restore the July behaviour.
_A8_MINUSE = 0.004

# The same bar for a register the strip did not choose but inherited
# from its neighbour, which has to pay for itself at a real share of the
# strip or go back.
_A8_INHERIT = 0.08


def _a8_seg_analysis(rows):
    """One strip's colour truth for the A8 (APPROVED by Stefan's corpus
    verdict, 2026-07-24, after the day's whole arc): six candidate
    centroids with masses; the protections the optimizer may not trade
    away (the darkest anchor, the big clusters); THE MOON RULE (the
    brightest cluster is a hard member, never priced); and the two
    CANVASES: a strip whose shadow tenth is truly dark carries black,
    a strip whose bright tenth is truly bright carries white."""
    # THE STRIP'S OWN COLOURS, NOT AVERAGES OF THEM (2026-08-11, the
    # fourth appearance of the identity doctrine and the worst of them).
    # A six-way k-means over palette art invents colours: in picture 6's
    # ceiling strip the two largest colours are pure black (620 pixels)
    # and a vivid blue (0, 0, 162) (283 pixels), and the clustering merged
    # them into (0, 0, 51), a colour that exists nowhere in the picture.
    # The election then protected the average, snapped the average, and
    # elected a palette with no blue in it at all, so the whole ceiling
    # rendered black. No amount of guard or diffusion tuning can repair
    # that, because the band never held the colour. These masters carry
    # at most sixteen colours in a whole picture, so the strip's own
    # colours ARE the candidate set, with their exact masses. Clustering
    # stays for a genuinely continuous master: if the leading colours do
    # not account for most of the strip, this is not palette art.
    cnt = {}
    for row in rows:
        for c in row:
            cnt[c] = cnt.get(c, 0) + 1
    npx_all = sum(cnt.values())
    top = sorted(cnt.items(), key=lambda kv: -kv[1])[:_A8_EXACT]
    if _A8_EXACT and sum(n for _, n in top) >= _A8_EXACT_COVER * npx_all:
        cents = [c for c, _ in top]
        mass = [n for _, n in top]
    else:
        cents = _kmeans_polish(rows, _median_cut(rows, 6))
        mass = [0] * len(cents)
        for row in rows:
            for c in row:
                i = min(range(len(cents)), key=lambda k: _dist(c, cents[k]))
                mass[i] += 1
    bright = max((c for row in rows for c in row),
                 key=lambda c: 2 * c[0] + 4 * c[1] + c[2])
    npx = sum(len(row) for row in rows)
    scale = npx / 1280.0          # the thresholds below were tuned on 8 rows
    bmass = sum(1 for row in rows for c in row if _dist(c, bright) < 1600)
    protected = []
    forced = bright if bmass >= max(2, 10 * scale) else None
    # THE MOON, PRICED RATHER THAN DECREED (dial). The rule fires on 81
    # percent of all strips, so "the brightest cluster is a hard member"
    # is not a rule about moons, it is a standing tax of one register in
    # four. Where the highlight is genuinely at risk the price defends it
    # anyway; where it is 6 percent of the strip and the darks are 60,
    # the picture should win.
    if forced is not None and not _A8_MOON_HARD:
        protected.append((forced, bmass * _A8_MOON_WEIGHT))
        forced = None
    dark = min((c for row in rows for c in row),
               key=lambda c: 2 * c[0] + 4 * c[1] + c[2])
    dmass = sum(1 for row in rows for c in row if _dist(c, dark) < 1600)
    if dmass >= max(5, _A8_DMASS * scale):
        protected.append((dark, dmass * _A8_DWEIGHT))
    lums = sorted(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                  for row in rows for c in row)
    # THE FORCED BLACK CANVAS IS GONE (Stefan, 2026-08-11: "this reaches
    # too much to black"). Any strip whose shadow tenth was dark used to
    # spend one of its four precious colours on pure black, which pulled
    # the corpus to 37 percent black against the masters' 31; without it
    # the A8 sits at 30, its art's own weight. Black still wins a slot
    # wherever the strip's own colours elect it, which is most of the
    # time; it is no longer imposed. (The darkest anchor keeps its double
    # protection: measured the same day, it costs nothing.)
    force_black = False
    force_white = lums[(9 * len(lums)) // 10] > 215.0
    # ONE HARD BRIGHT MEMBER, NOT TWO (2026-08-11). The moon rule and the
    # white canvas are separate tests and both can fire on the same strip,
    # each claiming a slot the optimizer may not price away. In picture
    # 1's house band that spent two of four registers on 11 percent of the
    # pixels (a pale cyan highlight and white), leaving ONE register for
    # black, dark blue and bright blue together, 73 percent of the strip
    # collapsed into a single colour: the blue mass with no timber in it.
    # The white canvas stays in the pool and can still win on price; it
    # just stops outranking the picture.
    if _A8_ONE_BRIGHT and forced is not None:
        force_white = False
    for i, c in enumerate(cents):
        if mass[i] >= max(15, _A8_MASS * scale):
            protected.append((tuple(c), mass[i]))
    return cents, protected, forced, force_black, force_white


def _a8_hist(strip):
    """A strip as (colours, counts, per-block counts). These masters are
    palette art: at most sixteen distinct colours in a whole picture and
    a median of eleven per strip. Scoring a combination against the
    histogram is therefore EXACT (integer arithmetic throughout, so the
    result is identical to walking every pixel) and about a hundred times
    cheaper, which is what makes a candidate pool bigger than six
    affordable."""
    idx, cols, counts, blocks = {}, [], [], []
    for row in strip:
        n = len(row)
        for x, c in enumerate(row):
            i = idx.get(c)
            if i is None:
                i = idx[c] = len(cols)
                cols.append(c)
                counts.append(0)
                blocks.append([0] * 8)
            counts[i] += 1
            blocks[i][x * 8 // n] += 1
    return cols, counts, blocks


def _a8_home_cost(col, home):
    """What it costs this strip colour to live on that register. ONE
    definition, used by the whole election (the identity doctrine: the
    protection term already knew a chromatic colour is not housed by a
    grey of equal brightness, but the main error term did not, so the
    main term, being the larger, decided the palette on brightness alone
    and every strip bought a luminance ladder instead of the picture's
    colours: picture 6 elected black, dark red, olive and pale yellow for
    a strip whose ceiling is blue)."""
    d = _dist_luma(col, home)
    cs, hs = max(col) - min(col), max(home) - min(home)
    if cs >= 18 and hs < 18:
        d *= _A8_TINT
    elif cs < 18 and hs >= 18 and _A8_TINT_BOTH:
        # AND THE OTHER WAY (Stefan, 2026-08-11: "lots of blue areas but
        # they are still missing the details"). The rule only ever ran in
        # one direction, so a neutral was housed on a saturated register
        # for free: picture 2's barn is 178 pixels of pure black against
        # 81 of dark blue, and the whole region painted itself blue
        # because black sat on the blue for nothing. Grey is not blue, and
        # blue is not grey; the doctrine is symmetric or it is not a
        # doctrine.
        d *= _A8_TINT_BOTH
    return d


def _a8_seam(hist, combo_rgb, prev_rgb):
    """The visible join with the strip above. A band is not "a strip
    changed its palette", it is ONE COLOUR FAMILY being painted one
    colour up there and a different colour down here, across a straight
    horizontal edge, in front of however many pixels sit on that family.
    So price exactly that: per family, how far the register this palette
    gives it lies from the register the strip above gave it, weighted by
    its mass.

    The gate is what makes this different from a flat continuity price
    (Stefan, 2026-08-11: a flat price "saturates some images with a
    single colour", picture 10 losing its green ground to the sky's
    palette). A family the strip above did NOT hold properly has no join
    to preserve, so it costs nothing here and this strip is free to buy
    it a colour of its own. Continuity binds what is shared and lets go
    of what is new."""
    cols, counts, _ = hist
    seam = 0
    for i, c in enumerate(cols):
        b = min(prev_rgb, key=lambda k: _a8_home_cost(c, k))
        a = min(combo_rgb, key=lambda k: _a8_home_cost(c, k))
        if a == b:
            continue
        # The gate is RELATIVE: the family is new here, and so has no
        # join to keep, only when this palette can house it far better
        # than the strip above ever could. An absolute radius does not
        # work, since almost every family sits further from its register
        # than that and the seam then costs nothing at all.
        if _a8_home_cost(c, b) > 2 * _a8_home_cost(c, a) + _A8_HOUSED:
            continue
        seam += counts[i] * _dist_luma(a, b)
    return seam


def _a8_combo_score(hist, combo_rgb, protected):
    """Region-balanced, protection-priced, luminance-dominant: the total
    error, plus the worst 20-column block (a palette may not sacrifice
    one side of the row to the other), plus a heavy price for any
    protected cluster left without a home."""
    cols, counts, cblocks = hist
    total = 0
    blocks = [0] * 8
    for i, c in enumerate(cols):
        e = min(_a8_home_cost(c, k) for k in combo_rgb)
        total += e * counts[i]
        cb = cblocks[i]
        for b in range(8):
            if cb[b]:
                blocks[b] += e * cb[b]
    score = total + 4 * max(blocks)
    for col, weight in protected:
        best = min(combo_rgb, key=lambda k: _dist_luma(col, k))
        d = _a8_home_cost(col, best)
        # TINT LOYALTY in the housing test (the fourth appearance of
        # the grey-axis lesson, 2026-07-24): a chromatic cluster is NOT
        # housed by a grey of equal brightness. Without this the
        # beach's blue sea sat 3832 "close" to grey under the luma
        # metric, inside the 4000 home radius, and the water greyed;
        # the same blindness was the corpus-wide missing-details bug
        # Stefan called out three times.
        if max(col) - min(col) >= 18 and max(best) - min(best) < 18:
            d *= 3
        if d > 4000:
            score += d * weight // 4
    return score


def _a8_snap(c):
    """Tint-loyal snap into the GTIA wheel (calibrated on the beach
    master, 2026-07-24: cliffs measure warm at spread 24, true neutrals
    9-13, so the boundary sits at 18). A source with a real tint may
    only snap to a chromatic entry on its own side of the wheel: warm
    stays warm, cool stays cool, and only true neutrals may be grey.
    Stefan's calling: the master's cliffs are sand-warm brown, never
    grey, and my thresholds at 30 were blind to soft chroma."""
    spread = max(c) - min(c)
    if spread < 18:
        return min(range(len(_GTIA_RGB)),
                   key=lambda k: _dist(c, _GTIA_RGB[k]))
    warm = c[0] > c[2]
    cands = [k for k in range(len(_GTIA_RGB))
             if (_GTIA128[k] >> 4) != 0
             and ((_GTIA_RGB[k][0] > _GTIA_RGB[k][2]) == warm)]
    return min(cands, key=lambda k: _dist(c, _GTIA_RGB[k]))


# How strongly an A8 segment prefers a colour its neighbour above already
# uses, as a PERCENTAGE of that strip's own error per differing register:
# 0 lets every strip choose freely and the picture bands; higher binds the
# strips together. (_A8_SHARE, an absolute figure in _dist units, was the
# first attempt at this and was never wired to anything; it is gone.)
_A8_CONT = 25

# How much worse than its own best palette a strip will accept in order
# to keep its neighbour's registers, as a percentage. This is the same
# idea as _A8_CONT expressed as a TOLERANCE rather than a price, which is
# the difference between "follow your neighbour unless it hurts" and
# "pay to differ": only the first leaves a strip free to buy a colour the
# rest of the picture does not have. 0 turns it off.
_A8_TOL = 0

# How heavily a visible join with the strip above is priced, as a
# percentage of its own measure (see _a8_seam), and how close a register
# must sit to a colour family to count as having painted it up there.
_A8_SEAM = 0
_A8_HOUSED = 4000

# Whether the strips are solved as a chain (0) or in two passes against
# their neighbours' independent choices (1). See _convert_a8.
_A8_TWOPASS = 0

# Whether a strip may answer with fewer than four colours to keep a join
# clean (see the election). 0 forces a full four every time.
_A8_FEWER = 0

# Whether the join is priced on the colours a strip BRINGS IN (1) or on
# the ones it fails to keep (0). See the election for why they differ.
_A8_PRICE_NEW = 0

# What a hue betrayal costs when a strip must substitute a colour it has
# How much a hue betrayal MULTIPLIES the cost when a segment must
# substitute a colour it has no room for, per turn of the wheel: enough
# that a purple ground prefers another purple, not so much that every
# unmatched hue flees to black.
_A8_HUE = 6.0

# How far a disagreeing pair leans toward its brighter member in the A8's
# halving: 0.5 is the plain average this converter used until now, 1.0 is
# the CPC trunk's full bedpost fix.
_A8_PAIR = 1.0

# Whether the kept member of a disagreeing pair is the one that departs
# further from the ground either side of it (1), or simply the brighter
# one (0, the CPC's rule, which has no dark features to lose).
_A8_PAIR_EXTREME = 1

# What share of the pixels sitting on a grey canvas must themselves be
# tinted before the canvas may take their tint. 0 restores the old
# mean-only test, which a warm minority could carry.
_A8_CANVAS_SHARE = 0.5

# Above this luminance a canvas is a white and keeps its neutrality. 255
# lets even white take a tint, which is what the code did before.
_A8_CANVAS_WHITE = 200.0


def _a8_choose(sx, cc, prgb, plum):
    """Which of a strip's four registers this pixel takes. ONE decision,
    called from two places (the identity doctrine's lesson from the
    Plus/4: a second site that re-derives the same answer will drift from
    it). `sx` is the source colour, which sets the guard; `cc` is what the
    diffusion has accumulated, which settles the choice. The pixel loop
    passes both; the usage probe that retires a dead register passes the
    source twice, since no error has flowed yet.

    Returns (register, guarded). `guarded` is False when nothing passed
    the guard at all and the pixel simply took its nearest: July's code
    diffused no error out of such a pixel, and that is kept."""
    # The guard is centred on WHAT IS LEFT TO RENDER, the source plus the
    # error the diffusion has carried into this pixel, bounded by
    # _A8_ECLAMP so it can follow the error without chasing a runaway.
    # Centring it on the bare source is what made flat regions inescapable
    # (see _A8_DRIFT above). The window itself is unchanged, and the hue
    # loyalty below still judges against the SOURCE, so following the
    # error can open a darker or lighter neighbour but never re-hue.
    gx = tuple(min(sx[k] + _A8_DRIFT, max(sx[k] - _A8_DRIFT, cc[k]))
               for k in range(3))
    src_l = 0.299 * gx[0] + 0.587 * gx[1] + 0.114 * gx[2]
    su, sv = gx[2] - src_l, gx[0] - src_l
    cands = []
    for i2 in range(4):
        if abs(plum[i2] - src_l) > _A8_GUARD_L:
            continue
        p2 = prgb[i2]
        pu, pv = p2[2] - plum[i2], p2[0] - plum[i2]
        if abs(pu - su) > _A8_GUARD_C or abs(pv - sv) > _A8_GUARD_C:
            continue
        cands.append(i2)
    if not cands:
        cands = [i2 for i2 in range(4)
                 if abs(plum[i2] - src_l) <= _A8_GUARD_L]
    if not cands:
        return min(range(4), key=lambda k: _dist(sx, prgb[k])), False

    # HUE LOYALTY IN THE SUBSTITUTION (Stefan, 2026-08-11, applied to the
    # master-inheritance converter): the strip's four colours cannot serve
    # every hue, and when one must stand in for another the replacement
    # has to stay in the source's own family. Plain distance re-hued whole
    # bands ("a stripe of dominant red, dominant blue"); the chroma window
    # above only bounds the tint, it does not stop a saturated pixel
    # landing on a saturated stranger.
    def cost(k):
        # The hue penalty MULTIPLIES the distance, it does not add a wall
        # (Stefan, 2026-08-11: "this reaches too much to black"). An
        # additive wall only punished saturated strangers, so black, being
        # neutral, escaped it entirely and became the cheapest escape
        # whenever no hue matched. Scaling keeps luminance in the contest:
        # a wrong hue costs proportionally, and a black that is far in
        # brightness stays expensive on its own account.
        d = _dist(cc, prgb[k])
        ws = max(sx) - min(sx)
        ps = max(prgb[k]) - min(prgb[k])
        if ws >= 40 and ps >= 40:
            hs, hp = _hue_turn(sx), _hue_turn(prgb[k])
            if hs is not None and hp is not None:
                dh = abs(hs - hp)
                dh = min(dh, 1.0 - dh)
                if dh > 0.15:
                    d *= 1.0 + _A8_HUE * dh
        return d

    return min(cands, key=cost), True


def _a8_usage(strip, pal4):
    """How many pixels each of the four registers would actually paint,
    diffusion aside. A register that paints (almost) none of them is a
    quarter of the strip's palette bought for nothing."""
    plum = [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in pal4]
    use = [0, 0, 0, 0]
    for row in strip:
        for c in row:
            use[_a8_choose(c, c, pal4, plum)[0]] += 1
    return use


def _hue_turn(c):
    """The colour's hue as a fraction of the wheel, or None for a neutral."""
    mx, mn = max(c), min(c)
    if mx == mn:
        return None
    r, g, b = c
    if mx == r:
        hh = (g - b) / (mx - mn)
    elif mx == g:
        hh = 2.0 + (b - r) / (mx - mn)
    else:
        hh = 4.0 + (r - g) / (mx - mn)
    return (hh % 6.0) / 6.0


def _convert_a8(rows, salient=None):
    # THE A8 CONVERTS DIRECT FROM THE MASTER, as the per-line-palette
    # machine it is (Stefan's ruling and corpus approval, 2026-07-24;
    # every derivation route failed his eye first: C64 heritage, flat
    # base, and the Plus/4 both ways). Each 8-line segment picks its own
    # four GTIA colours from its own strip of the master; continuity
    # between neighbours is a price, never a law (the line table replays
    # all four registers); guarded diffusion flows across the band with
    # tint loyalty (the chroma window: dark purple dithers toward purple
    # and black, never blue) and a tighter deadzone in the dark, so
    # blanket folds texture instead of flattening. A gentle lift (12
    # percent at black, fading to nothing at white) carries his "force
    # luminance slightly more". Salience emerges from the moon rule;
    # the hint sidecar is not consulted.
    from itertools import combinations

    def lift(c):
        y = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        f = 1.0 + 0.12 * (1.0 - y / 255.0)
        return tuple(min(255, round(v * f)) for v in c)

    # THE BEDPOST FIX, HERE TOO (Stefan, 2026-08-11). This converter
    # halved the master by plain averaging, the very line the CPC trunk
    # gave up: an averaged pair smears a one-pixel vertical into a
    # half-tone that quantises away, and the A8 lost its thin bright
    # structures the same way the CPC lost the bedpost. Pairs collapse by
    # agreement instead; a disagreeing pair keeps its brighter member.
    half = []
    for row in rows:
        out_row = []
        for x in range(0, len(row), 2):
            a, b = row[x], row[x + 1]
            if _dist(a, b) <= 2400:
                out_row.append(lift(tuple((p + q) // 2
                                          for p, q in zip(a, b))))
            else:
                # The fix at ADJUSTABLE STRENGTH (Stefan, 2026-08-11:
                # "not that much"). The CPC takes the brighter member
                # whole; here the pair leans toward it by _A8_PAIR, so
                # 0.5 is the old averaging and 1.0 is the CPC's full
                # force. A threshold dial was tried first and did
                # nothing: these pairs sit far beyond any threshold.
                br, dk = (a, b) if sum(a) >= sum(b) else (b, a)
                if _A8_PAIR_EXTREME:
                    # KEEP THE FEATURE, NOT THE BRIGHTER (2026-08-11).
                    # Always taking the brighter member saves a bright
                    # line on a dark ground and destroys a DARK line on a
                    # bright one, which is the same loss the fix exists
                    # to prevent, mirrored: measured over the corpus,
                    # going from the plain average to the full rule
                    # raised thin bright lines from 78.8 to 92.0 percent
                    # and dropped thin dark lines from 83.9 to 68.6, and
                    # it is why picture 2's chapel windows lose their
                    # mullions. So judge each member against the ground
                    # either side of the pair and keep whichever departs
                    # from it further; on a dark ground that is still the
                    # brighter one, and the fix behaves as before.
                    ground = [row[k] for k in (x - 1, x + 2)
                              if 0 <= k < len(row)]
                    if ground:
                        g = sum(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                                for c in ground) / len(ground)
                        la = 0.299 * a[0] + 0.587 * a[1] + 0.114 * a[2]
                        lb = 0.299 * b[0] + 0.587 * b[1] + 0.114 * b[2]
                        br, dk = ((a, b) if abs(la - g) >= abs(lb - g)
                                  else (b, a))
                w = _A8_PAIR
                out_row.append(lift(tuple(
                    round(br[k] * w + dk[k] * (1.0 - w)) for k in range(3))))
        half.append(out_row)
    h, w = len(half), len(half[0])

    snap = _a8_snap

    # A palette per EIGHT lines. Electing one per scanline was tried
    # 2026-08-11 (the format carries four registers per line, so the
    # capacity is there) and REVERTED the same hour: neighbouring lines
    # elected independently and locked into full-width stripes running
    # through the picture, while the flat regions stayed flat. The
    # capacity is real but it needs an election that reasons about the
    # picture, not one line at a time.
    def elect_strip(strip, neighbours):
        """This strip's four registers. `neighbours` is a list of the
        palettes it must join with, and it is the whole difference
        between banding and a picture drowned in one colour: pass the
        strip above as it was ELECTED IN TURN and a decision walks the
        length of the picture (Stefan, 2026-08-11: picture 10 "is
        basically only blue now, there used to be at least a green
        ground"); pass what the neighbours chose ON THEIR OWN, above and
        below, and every strip is pulled toward a fixed reference that
        cannot propagate. The seam is priced, never forbidden."""
        cents, protected, forced, f_black, f_white = _a8_seg_analysis(strip)
        must = snap(forced) if forced is not None else None
        fresh = []
        for c in cents:
            k = snap(c)
            if k not in fresh:
                fresh.append(k)
        for col, _wt in protected:
            k = snap(col)
            if k not in fresh:
                fresh.append(k)

        hist = _a8_hist(strip)
        prev = neighbours[0] if neighbours else None

        def elect(banned, prev=prev, hist=hist, fresh=fresh, must=must,
                  protected=protected, f_black=f_black, f_white=f_white):
            pool = list(fresh)
            for nb in neighbours:
                pool = list(dict.fromkeys(nb + pool))
            live = [k for k in pool if k not in banned]
            # A ban may never leave the strip with too little to choose
            # from: capacity is the whole point of retiring a register.
            if len(live) >= 4:
                pool = live
            m = None if must in banned else must
            if m is not None and m not in pool:
                pool.append(m)
            if f_black and 0 not in pool:
                pool.append(0)
            if f_white and 7 not in pool and 7 not in banned:
                pool.append(7)
            # FEWER COLOURS IS A LEGAL ANSWER (Stefan, 2026-08-11: "is
            # there a way in these regions to fall back into less
            # colours?"). A band is a colour appearing in one strip and
            # not the next, so a strip that can only serve three of its
            # neighbour's four registers should be free to take just
            # those three and leave a slot doubled, rather than fill it
            # with something new that will show as a seam. Sizes below
            # four are offered to the election and it takes them when the
            # join is worth more than the colour.
            sizes = [min(4, len(pool))]
            if _A8_FEWER and neighbours:
                sizes += [n for n in (3, 2) if n < len(pool)]
            best, bd, near = None, None, []
            for hard in (True, False):   # drop the canvases before failing
                for combo in (c for n in sizes for c in combinations(pool, n)):
                    if hard:
                        if m is not None and m not in combo:
                            continue
                        if f_black and 0 not in combo:
                            continue
                        if f_white and 7 not in combo and 7 not in banned:
                            continue
                    sc = _a8_combo_score(hist, [_GTIA_RGB[k] for k in combo],
                                         protected)
                    near.append((sc, combo))
                    crgb = [_GTIA_RGB[k] for k in combo]
                    for nb in neighbours:
                        # The price is on the colours this strip BRINGS
                        # IN, not on the ones it fails to keep. Those are
                        # not the same thing, and only the first lets a
                        # strip answer with fewer colours: charging for
                        # what is dropped makes "three of yours" cost
                        # exactly what "three of yours plus one of mine"
                        # costs, so the extra colour is always taken and
                        # always seams. (The flat 250000 this replaced
                        # was under one percent of a score that runs to
                        # tens of millions, so strips elected as if they
                        # were separate pictures.)
                        diff = (len(set(combo) - set(nb)) if _A8_PRICE_NEW
                                else 4 - len(set(combo) & set(nb)))
                        sc += diff * 250000 + diff * sc * _A8_CONT // 100
                        if _A8_SEAM:
                            sc += _A8_SEAM * _a8_seam(
                                hist, crgb,
                                [_GTIA_RGB[k] for k in nb]) // 100
                    if bd is None or sc < bd:
                        best, bd = list(combo), sc
                if best is not None:
                    break
            # CONTINUITY WHERE IT IS NEARLY FREE (Stefan, 2026-08-11: a
            # flat price per changed register "saturates some images with
            # a single colour", picture 10's green ground turning blue
            # because the sky's palette walked all the way down the
            # picture). A price cannot tell a strip that is merely
            # undecided from one that genuinely needs a colour its
            # neighbour does not have. So: find what the strip would
            # choose alone, then among every palette within _A8_TOL
            # percent of that, take the one holding most of the
            # neighbour's registers. A strip with nothing at stake falls
            # into line; a strip with a green ground keeps its green.
            if near and prev is not None and _A8_TOL:
                b0 = min(sc for sc, _ in near)
                cap = b0 + abs(b0) * _A8_TOL // 100
                best = list(min(
                    ((sc, c) for sc, c in near if sc <= cap),
                    key=lambda t: (-len(set(t[1]) & set(prev)), t[0]))[1])
            # A short palette doubles a register it already holds; it
            # must never be padded with black, which would smuggle in the
            # very extra colour the short answer was avoiding.
            while len(best) < 4:
                best.append(best[0] if best else 0)
            # THE CANVAS TAKES ITS USERS' TINT (Stefan's proposal,
            # 2026-07-24, after four gate rounds proved the pixel stage was
            # the wrong place: the Kopie build was right everywhere except
            # its grey canvas). For each mid-grey register, gather the strip
            # pixels that would land on it; if they are mostly tinted one
            # way, the register BECOMES their tint-loyal colour: a sea
            # canvas turns light blue, near-neutrals sit on it comfortably,
            # and no pixel gate exists to speckle a sky. True black and
            # bright white canvases stay; chromatic entries stay.
            pal4 = [_GTIA_RGB[k] for k in best]
            for slot in range(4):
                e = pal4[slot]
                el = 0.299 * e[0] + 0.587 * e[1] + 0.114 * e[2]
                # A bright white canvas stays white, which is what this
                # pass always said it did ("true black and bright white
                # canvases stay") and never actually checked: only black
                # was guarded. Picture 15 is what that cost. Its white
                # register serves about 175 white pixels and about 100
                # pink ones in three strips running; in the middle one
                # the pink is a shade heavier, the canvas turns pink, and
                # a mountain that occupies a corner of the picture paints
                # a band across its whole width while the strips above
                # and below stay white. Stefan, 2026-08-11: "the mountain
                # part that would be in this colour is genuinely small
                # and for that it paints over the whole row, that feels
                # off, disproportional".
                if (max(e) - min(e) >= 18 or el < 30.0
                        or el > _A8_CANVAS_WHITE):
                    continue
                users = []
                for srow in strip:
                    for c in srow:
                        if min(range(4), key=lambda k: _dist(c, pal4[k])) \
                                == slot:
                            users.append(c)
                if len(users) < 80:
                    continue
                n = len(users)
                # THE MAJORITY DECIDES, NOT THE MEAN (Stefan, 2026-08-11:
                # "a skin coloured bar going through, which only harms
                # the picture... the whole picture would be way better
                # off if this pink area is just painted with the rest of
                # the surrounding colours"). A mean can be pulled warm by
                # a minority while most of the users are plain grey, and
                # then the register turns and paints the grey salmon: in
                # picture 10's strip 2, 280 grey pixels lost their canvas
                # to 74 olive and red ones, and the result was a
                # full-width bar of skin tone through a stone wall. A
                # canvas may only take a tint that most of the pixels on
                # it actually have.
                tinted = sum(1 for c in users if max(c) - min(c) >= 18)
                if tinted < _A8_CANVAS_SHARE * n:
                    continue
                mc = tuple(sum(c[k] for c in users) / n for k in range(3))
                ml2 = 0.299 * mc[0] + 0.587 * mc[1] + 0.114 * mc[2]
                mmag = ((mc[2] - ml2) ** 2 + (mc[0] - ml2) ** 2) ** 0.5
                if mmag < 12.0:
                    continue
                k2 = _a8_snap(tuple(round(v) for v in mc))
                if k2 not in best:
                    best[slot] = k2
                    pal4[slot] = _GTIA_RGB[k2]
            return best

        # USE IT OR LOSE IT (Stefan's direction B, 2026-08-11). A strip
        # gets four registers and a third of the corpus painted only
        # three of them, because the moon rule forces the brightest
        # cluster in from ten pixels and the optimizer may not price it
        # away. Elect, ask the pixel stage what it would actually paint,
        # and retire anything it refuses; the slot goes back into the
        # pool and the strip elects again. Two rounds at most: this is a
        # cleanup pass, not a search.
        # A register the strip took from its neighbour has to EARN its
        # quarter of the palette, and a much higher bar than one the
        # strip chose for itself (Stefan, 2026-08-11: "some images are
        # now saturated too much with a single colour... picture 10 is
        # basically only blue now, there used to be at least a green
        # ground"). The join price is right to make a strip follow its
        # neighbour; it is wrong when the strip has no use for what it
        # inherits, and that is how a sky palette walks down into a
        # field. Applying the same bar to the strip's own choices was
        # tried and was too blunt: picture 16's green room turned salmon.
        own = set(fresh)
        inherited = set()
        for nb in neighbours:
            inherited |= set(nb)
        inherited -= own

        banned = set()
        best = elect(banned)
        for _round in range(2):
            if _A8_MINUSE <= 0:
                break
            use = _a8_usage(strip, [_GTIA_RGB[k] for k in best])
            n_use = sum(use)
            floors = [n_use * (_A8_INHERIT if best[k] in inherited
                               else _A8_MINUSE) for k in range(4)]
            dead = {best[k] for k in range(4) if use[k] < floors[k]}
            dead -= set(best[k] for k in range(4) if use[k] >= floors[k])
            if not dead or dead <= banned:
                break
            banned |= dead
            best = elect(banned)
        return best

    strips = [half[s * 8:(s + 1) * 8] for s in range(h // 8)]
    if _A8_TWOPASS:
        # Pass one: every strip elects alone. Pass two: each strip joins
        # with what its neighbours chose ALONE, above and below, so no
        # decision can walk the length of the picture. MEASURED WORSE
        # (2026-08-11) and left here as a dial: pulled toward two
        # references that disagree with each other, a strip lands on a
        # compromise matching neither, and the joins came out worse than
        # the plain chain (churn 256 against 127). The idea is right and
        # the arbitration is wrong; it wants the whole picture solved at
        # once, not each strip against its neighbours.
        alone = [elect_strip(st, []) for st in strips]
        palettes = [
            elect_strip(st, [n for n in (alone[i - 1] if i else None,
                                         alone[i + 1] if i + 1 < len(strips)
                                         else None) if n is not None])
            for i, st in enumerate(strips)]
    else:
        palettes = []
        prev = None
        for st in strips:
            prev = elect_strip(st, [prev] if prev is not None else [])
            palettes.append(prev)

    buf = [[[float(v) for v in c] for c in row] for row in half]
    codes = [[0] * w for _ in range(h)]
    for y in range(h):
        prgb = [_GTIA_RGB[k] for k in palettes[y // 8]]
        plum = [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in prgb]
        serp = y & 1
        xs = range(w - 1, -1, -1) if serp else range(w)
        step = -1 if serp else 1
        for x in xs:
            c = buf[y][x]
            cc = (min(255.0, max(0.0, c[0])),
                  min(255.0, max(0.0, c[1])),
                  min(255.0, max(0.0, c[2])))
            sx = half[y][x]
            src_l = 0.299 * sx[0] + 0.587 * sx[1] + 0.114 * sx[2]
            i, guarded = _a8_choose(sx, cc, prgb, plum)
            codes[y][x] = i
            if not guarded:
                continue
            dz = 300.0 if src_l < 60.0 else 900.0
            if _dist(sx, prgb[i]) < dz:
                continue
            pr, pg, pb = prgb[i]
            er, eg, eb = c[0] - pr, c[1] - pg, c[2] - pb
            for dx, dy, wt in ((step, 0, 7), (-step, 1, 3),
                               (0, 1, 5), (step, 1, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    t = buf[ny][nx]
                    t[0] += er * wt / 16.0
                    t[1] += eg * wt / 16.0
                    t[2] += eb * wt / 16.0
                    if _A8_ECLAMP:
                        # Hold the buffer near its own source: without
                        # this the error is conserved and handed on
                        # forever (see _A8_ECLAMP above).
                        n_sx = half[ny][nx]
                        for k in range(3):
                            t[k] = min(n_sx[k] + _A8_ECLAMP,
                                       max(n_sx[k] - _A8_ECLAMP, t[k]))

    lines = []
    for y in range(h):
        lines += [_GTIA128[k] for k in palettes[y // 8]]
    return {"w": w, "h": h, "pixels": codes, "lines": lines}

# Where the MSX1's 256-wide window sits in the 320-wide master, in
# pixels off the left edge, always a multiple of 8 so the attribute
# grid meets the master's own columns. 0 was the first round's pure
# top-left anchor; 24 is Stefan's call (2026-08-12): a third of the
# discard off the left (exactly three attribute columns), the rest off
# the right. 32 would be the centre crop, rejected.
_MS1_CROP_X = 24

# How strongly an octet prefers the pair its upstairs neighbour chose,
# as a percentage discount on that pair's score. 0 turns it off, and 0
# is where it stays: tried at 10 and 20 on 2026-08-12 against the
# row-oscillation stripes, and Stefan rejected it, new issues, no help
# where it was aimed. The stripes are the one-row color cell speaking;
# whoever reopens this needs a mechanism that understands the picture,
# not a bribe between neighbouring rows.
_MS1_VCONT = 0



def _convert_ms1(rows, salient=None):
    """MSX1 Screen 2, the gentlest of the cell class: 256 wide from the
    master by the TOP-LEFT crop (Stefan's ruling, 2026-08-11: one master
    pixel stays one native pixel, and the retained geometry sits better
    with the attribute grid when the origin is honest; wave 2's centre
    crop stays the Spectrum's). Two colors per 8x1 octet from the fixed
    fifteen (index 0 is transparent and never written). The octet is
    small enough for an EXACT solve: all 105 legal pairs are scored
    against the SOURCE pixels, so nothing here clusters, averages, or
    improvises (the identity doctrine, proved eight ways in the retro
    quality round; the exact solve is what a cell class looks like when
    the cell is only eight pixels). The hint sidecar is NOT consulted
    (Stefan's rule, 2026-08-12: the sidecar is an author's last resort
    for a weird picture, never this tool's crutch; arcimg brings its
    best results out of the box). Salience is the A8's MOON RULE, read
    from the picture itself: the brightest source cluster renders
    white, because TMS holds ONE cyan, so a moon disc and its halo
    would otherwise snap to the same entry and the disc dissolve into
    its own glow; GTIA's eight lumas per hue let the A8 keep that
    contrast for free, this palette cannot. Truly dark source pixels
    keep their darkness (the CPC's dark sanctuary carried over: below
    the luma bar, with every channel quiet, only black may serve;
    everything TMS owns besides black sits above luma 100, and without
    the sanctuary the crypt's mortar lifts into pastel. A SATURATED
    dark, picture 8's deep blue forest, is a color speaking, not
    darkness, and stays exempt). The background nibble takes the
    octet's MAJORITY color, so pattern bytes lean toward zero and the
    ZX0 stream stays cheap."""
    rows = [row[_MS1_CROP_X:_MS1_CROP_X + 256] for row in rows]
    w, h = len(rows[0]), len(rows)
    tiles_x = w // 8
    pattern = [[0] * tiles_x for _ in range(h)]
    colors = [[0] * tiles_x for _ in range(h)]
    pairs = [(a, b) for a in range(1, 16) for b in range(1, a)]
    white_pairs = [(a, b) for a, b in pairs if a == 15 or b == 15]

    def lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    # The moon rule's census: the brightest cluster, IF the picture has
    # a genuinely bright one (a dark hallway's brightest pixel is not a
    # moon, hence the luma bar). The cluster's COLOR is not enough: a
    # master's brightest ink paints the moon AND every glint and lit
    # tree rim, and forcing the color wholesale turned picture 8 into
    # white speckle. A moon is a large CONTIGUOUS patch of that ink, so
    # only fat connected blobs are forced: area for a real disc, both
    # bounding sides for fatness (a rim is long and thin, a disc is
    # round).
    bright = max((c for row in rows for c in row), key=lum)
    bset = set()
    if lum(bright) >= 150.0:
        cand = {(x, y) for y in range(h) for x in range(w)
                if _dist(rows[y][x], bright) < 1600}
        seen = set()
        for start in cand:
            if start in seen:
                continue
            blob, queue = {start}, [start]
            while queue:
                cx, cy = queue.pop()
                for nx, ny in ((cx + 1, cy), (cx - 1, cy),
                               (cx, cy + 1), (cx, cy - 1)):
                    if (nx, ny) in cand and (nx, ny) not in blob:
                        blob.add((nx, ny))
                        queue.append((nx, ny))
            seen |= blob
            xs = [p[0] for p in blob]
            ys = [p[1] for p in blob]
            if (len(blob) >= 24 and max(xs) - min(xs) >= 6
                    and max(ys) - min(ys) >= 6):
                # An OPENING before the blob is believed (picture 1's
                # moon grew streaks: the disc's ink continues into thin
                # connected glow trails, and contiguity alone follows
                # them out of the disc). Erode one step, dilate back
                # inside the blob: the fat disc survives, every tendril
                # one or two pixels thin does not.
                core = {(px, py) for px, py in blob
                        if {(px + 1, py), (px - 1, py),
                            (px, py + 1), (px, py - 1)} <= blob}
                bset |= {(px, py) for px, py in blob
                         if (px, py) in core
                         or ({(px + 1, py), (px - 1, py), (px, py + 1),
                              (px, py - 1)} & core)}

    def tms_dist(c, k):
        # HUE LOYALTY, the A8's proportional lesson carried over: TMS
        # has no olive, so plain distance sent the crypt's gold walls to
        # dark green, luma-right and hue-wrong, the exact betrayal the
        # quality round priced out. The penalty MULTIPLIES (an additive
        # wall lets black, being neutral, escape it and everything flees
        # to black).
        d = _dist(c, _TMS9918[k])
        ws = max(c) - min(c)
        p = _TMS9918[k]
        ps = max(p) - min(p)
        if ws >= 40 and ps >= 40:
            hs, hp = _hue_turn(c), _hue_turn(p)
            if hs is not None and hp is not None:
                dh = abs(hs - hp)
                dh = min(dh, 1.0 - dh)
                if dh > 0.15:
                    d *= 1.0 + _A8_HUE * dh
        elif ws < 18 and ps >= 40:
            # AND THE OTHER WAY (the A8's lesson, resurfacing on picture
            # 10's grey wall: a neutral source paid nothing to be housed
            # by a chromatic entry, so neighbouring octets each bought a
            # different cheap hue and the stone turned patchwork). Grey
            # is not blue; the doctrine is symmetric or it is nothing.
            d *= 3
        elif (ws >= 40 and ps < 18 and lum(c) >= 30.0
                and lum(p) < lum(c) - 24.0):
            # THE THIRD LEG, the one the A8 always had and this
            # converter lacked (found 2026-08-12 on picture 2's timber):
            # a chromatic color pays to be housed by a neutral THAT IS
            # SUBSTANTIALLY DARKER, black eating lit color. The timber's
            # dark red sits NEARER to black than to any TMS red, so no
            # pair logic downstream could ever save the line; the metric
            # itself had to stop giving black away free. Two guards
            # bound the rule to its disease: the luminance floor lets
            # picture 8's navy forest (luma 17) keep falling to black,
            # whose lie about it is small, so its blue-on-black texture
            # stays; and the darker-home test keeps the penalty OFF the
            # bright neutrals, so a lavender cloud rim still rounds up
            # into white as the master's art expects (Stefan's corpus
            # review: the first cut penalized all neutrals and drew rim
            # lines around picture 10's clouds and a stripe on 12's
            # statue).
            d *= 3
        return d

    # (Two whole architectures were tried here on 2026-08-12 and
    # reverted the same day on Stefan's eye. First octet-local repairs:
    # a census-gated sanctuary and ordered halftone, which read as
    # moth-eaten holes. Then a picture-global ink map, the C64 recolour
    # mechanics computed, with an exact pair solve over present inks:
    # it fixed the dotted timber measurably, 6.5 to 89 percent, and
    # improved many pictures, but flattened others; three-ink octets
    # lose their highlight minority under any consistent rule, and his
    # verdict was to keep THIS build, the reviewed one, whose per-octet
    # freedom reads livelier even where it is locally inconsistent.
    # Of that round's artifacts, 2's dotted timber was later fixed by
    # the third tint-loyalty leg (6.5 to 95.5 percent) and the rest
    # were RULED CLOSED as super minor by Stefan on 2026-08-13: no
    # further machinery. Whoever reopens any of this should read the
    # 2026-08-12 session record first.)
    SANCT = 10 ** 12
    prev_pair = [None] * tiles_x
    for y in range(h):
        row = rows[y]
        for tx in range(tiles_x):
            octet = row[tx * 8:(tx + 1) * 8]
            moon = [(tx * 8 + i, y) in bset for i in range(8)]
            d = []
            for i, c in enumerate(octet):
                px = [tms_dist(c, k) for k in range(16)]
                if moon[i]:
                    px = [SANCT] * 15 + [px[15]]
                elif lum(c) < 40.0 and max(c) < 90:
                    px = [px[0], px[1]] + [v * 6 for v in px[2:]]
                d.append(px)
            best, bd = None, None
            for a, b in (white_pairs if any(moon) else pairs):
                e = 0
                for px in d:
                    da, db = px[a], px[b]
                    e += da if da <= db else db
                # VERTICAL CONTINUITY AS A SMALL PRICE (Stefan's stripe
                # report, 2026-08-12: the color cell is ONE ROW tall, so
                # a mottled trunk elected a different pair every row and
                # flat-filled it, horizontal stripes almost periodic;
                # the third leg exposed what uniform black had hidden).
                # The A8's proven idea at octet scale: a near-tie aligns
                # with the octet above, a decisive content change still
                # wins. The discount is multiplicative and small, so it
                # never overrides a real difference, it only settles
                # coin flips the same way twice.
                if prev_pair[tx] is not None and {a, b} == prev_pair[tx]:
                    e -= e * _MS1_VCONT // 100
                if bd is None or e < bd:
                    best, bd = (a, b), e
            a, b = best
            prev_pair[tx] = {a, b}
            take_a = [px[a] <= px[b] for px in d]
            na = sum(take_a)
            fg, bg = (b, a) if na * 2 >= len(octet) else (a, b)
            byte = 0
            for i, ta in enumerate(take_a):
                if (ta and fg == a) or (not ta and fg == b):
                    byte |= 0x80 >> i
            pattern[y][tx] = byte
            colors[y][tx] = (fg << 4) | bg
    return {"w": w, "h": h, "pattern": pattern, "colors": colors}


def _convert_agn(rows, salient=None):
    """Master to Agon Light mode 3 (640x240, the fixed 64-color RGBA2222
    cube): 2x horizontal first (mode 3 pixels are half as wide as tall,
    the Model 4's aspect logic, and the dither grid doubles with it),
    then the nearest-color map over the full cube with the standard
    gentle ordered dither. No palette to solve: the cube is the
    hardware, and every master color is at most half a 2-bit step from
    a native one."""
    wide = [[c for c in row for _ in (0, 1)] for row in rows]
    w, h = len(wide[0]), len(wide)
    cube = [(r * 85, g * 85, b * 85)
            for r in range(4) for g in range(4) for b in range(4)]
    idx = _map_pixels(wide, cube, _dither_amount(wide, 64))
    pixels = [[_agn_byte(*cube[i]) for i in row] for row in idx]
    return {"w": w, "h": h, "pixels": pixels}


def _convert_ms2(rows, salient=None):
    """MSX2 Screen 5: 256 wide by the MSX window (the MS1 crop, columns
    24..279 of the master, so both MSX machines frame the same scene),
    free pixels, 16 simultaneous colors from the V9938's 512. The
    quantize class verbatim (approved in wave 1): median-cut to 16,
    palette snapped to the 3-bit guns BEFORE mapping, and the ST text
    contract, whose constraint set (16 of 512, 3:3:3) this machine
    shares exactly: entry 0 the darkest color (the text paper below the
    band), the last entry a guaranteed-readable light ink."""
    rows = [row[_MS1_CROP_X:_MS1_CROP_X + 256] for row in rows]
    w, h = len(rows[0]), len(rows)
    def luma(c):
        return 2 * c[0] + 4 * c[1] + c[2]
    pal = _build_palette(rows, 16, _snap3)
    pal.sort(key=luma)
    if luma(pal[-1]) < 4 * 255:  # no usable ink: trade one slot for white
        pal = _build_palette(rows, 15, _snap3)
        pal.sort(key=luma)
        pal.append((255, 255, 255))
    palette = pal + [(0, 0, 0)] * (16 - len(pal))
    if len(pal) < 16:
        palette = pal[:-1] + [(0, 0, 0)] * (16 - len(pal)) + [pal[-1]]
    pixels = _map_pixels(rows, palette, _dither_amount(rows, 16))
    return {"w": w, "h": h, "pixels": pixels, "palette": palette}


def _convert_trsm4(rows, salient=None):
    """Master to TRS-80 Model 4 mono: luminance, 2x horizontal (the hi-res
    board's 640x240 pixels are half as wide as tall, so the doubling both
    restores the aspect and doubles the dither grid), ordered dither at
    the full 640 resolution: the whole quality budget of a monochrome
    target is its halftone."""
    h = len(rows)
    lumas = [[(299 * r + 587 * g + 114 * b) / 255000.0 for r, g, b in row]
             for row in rows]
    # Contrast stretch before the halftone: a mono image lives on its
    # tonal range, and a master that never quite reaches black or white
    # would dither to gray mush. Percentile-anchored so single outlier
    # pixels cannot flatten the whole picture.
    flat = sorted(v for row in lumas for v in row)
    lo = flat[len(flat) * 2 // 100]
    hi = flat[len(flat) * 98 // 100]
    span = (hi - lo) or 1.0
    pixels = []
    for y in range(h):
        row = []
        for mx in range(320):
            luma = min(1.0, max(0.0, (lumas[y][mx] - lo) / span))
            for sub in range(2):
                x = mx * 2 + sub
                t = (_BAYER8[y & 7][x & 7] + 0.5) / 64.0
                row.append(1 if luma > t else 0)
        pixels.append(row)
    return {"w": 640, "h": h, "pixels": pixels}



def _map_pixels_diffusion(rows, palette):
    """Master pixels to palette indices by Floyd-Steinberg error diffusion,
    serpentine scan. THE PHOTOSHOP MANNER (Stefan's reboot ruling,
    2026-07-23, studied on his own Ghosts of Blackwood Manor cascade,
    Amiga -> ST -> CPC -> C64, machine-generated and untouched by hand):
    one small palette for the whole image and diffusion everywhere. On
    smooth gradients this lays the sparse, evenly drifting dots of his
    reference skies; where the palette matches the paint it goes honestly
    flat; and it never draws the Bayer crosses he ruled out. Ordered
    dithering stays available to the other targets (_map_pixels); this
    mapper is the diffusion counterpart.

    Three guards, all Stefan's catches, all firefly diseases of plain
    Floyd-Steinberg, plus one fail-safe. (A locally-gated variant was
    tried 2026-07-23 and withdrawn the same hour: it wrecked scenes the
    global guards had carried to his jackpot verdict. The record stands
    in PROGRESS; the guards are global, as the jackpot corpus proves.)
    - the luminance window: no entry beyond 40 luma of the source;
    - the chroma window: no entry whose tint pulls against the source
      (same-family blends stay legal);
    - the deadzone: a source already close to its colour drops the
      residual, so near-flat fields stay flat while true transitions
      dither fully;
    - the fail-safe: a pixel with NO compatible entry picks by SOURCE,
      never the error-laden accumulator, and drops the residual (the
      magenta flicker of corpus 2).
    """
    h, w = len(rows), len(rows[0])
    plum = [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in palette]
    slum = [[0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in row]
            for row in rows]
    buf = [[[float(v) for v in c] for c in row] for row in rows]
    idx = [[0] * w for _ in range(h)]
    for y in range(h):
        serp = y & 1
        xs = range(w - 1, -1, -1) if serp else range(w)
        step = -1 if serp else 1
        for x in xs:
            c = buf[y][x]
            cc = (min(255.0, max(0.0, c[0])),
                  min(255.0, max(0.0, c[1])),
                  min(255.0, max(0.0, c[2])))
            s = rows[y][x]
            src_l = slum[y][x]
            su, sv = s[2] - src_l, s[0] - src_l
            cands = []
            for i2 in range(len(palette)):
                if abs(plum[i2] - src_l) > 40.0:
                    continue
                p2 = palette[i2]
                pu, pv = p2[2] - plum[i2], p2[0] - plum[i2]
                if abs(pu - su) > 70.0 or abs(pv - sv) > 70.0:
                    continue
                cands.append(i2)
            if not cands:
                cands = [i2 for i2 in range(len(palette))
                         if abs(plum[i2] - src_l) <= 40.0]
                if not cands:
                    cands = range(len(palette))
                idx[y][x] = min(cands, key=lambda k: _dist(s, palette[k]))
                continue
            if src_l < 48.0:
                # THE DARK SANCTUARY (the CPC beach round, Stefan's
                # verdicts 2026-08-09/10, FINAL: "flat and safe"). In
                # darkness the mapper goes flat and literal, the 8-bit
                # school's way: only entries that are THEMSELVES dark may
                # fire (no bright or loud tint is ever planted into a
                # shadow), picked luminance-first by the SOURCE, and no
                # error crosses the boundary in either direction. A
                # chroma-split variant that let colored darkness keep the
                # diffusion detail was tried 2026-08-10 and REVERTED the
                # same day: it re-created the artifacts. Lit regions keep
                # the global guards and the jackpot diffusion untouched.
                dark = [k for k in range(len(palette))
                        if plum[k] <= src_l + 24.0]
                if not dark:
                    dark = [min(range(len(palette)), key=lambda k: plum[k])]
                idx[y][x] = min(
                    dark, key=lambda k: _dist_luma(s, palette[k], 20))
                continue
            i = min(cands, key=lambda k: _dist(cc, palette[k]))
            idx[y][x] = i
            if _dist(s, palette[i]) < 900:
                continue
            pr, pg, pb = palette[i]
            er, eg, eb = c[0] - pr, c[1] - pg, c[2] - pb
            for dx, dy, wt in ((step, 0, 7), (-step, 1, 3),
                               (0, 1, 5), (step, 1, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    t = buf[ny][nx]
                    t[0] += er * wt / 16.0
                    t[1] += eg * wt / 16.0
                    t[2] += eb * wt / 16.0
    # A boundary weave (a two-colour shadow dissolve at big-block edges)
    # was designed, gated, and REMOVED on Stefan's ruling, 2026-08-10:
    # flat-and-safe darkness is the final look. The record lives in
    # PROGRESS; do not re-add a weave without his explicit reopening.
    return idx


def _reduce_master(rows, n):
    """THE SHARED REDUCTION INTERMEDIATE (Stefan's ruling, 2026-07-23):
    one adaptive free-space palette and one diffused index map per
    picture, computed once; every retro target EXPRESSES this same
    intermediate in its own colours and then solves its own constraint.
    One gamut hop per machine, never two, and every port is visibly a
    sibling: the family coherence of his own Photoshop cascade (Amiga ->
    ST -> CPC -> C64) without the generational loss of chaining files."""
    # The palette is adaptive, never seeded: exact-paint seeding was
    # tried (2026-07-23) and starved the gradients of their in-between
    # slots; church windows flattened, water lost its shimmer, and the
    # detail Stefan prizes died. The jackpot corpus rode this build.
    free = _kmeans_polish(rows, _median_cut(rows, n))
    free = _protect_extremes(rows, free, lambda c: c)
    return free, _map_pixels_diffusion(rows, free)


def _express(free, usage_order, machine, merge_far=2.5):
    """Express free palette entries in a machine palette, one to one
    while a close colour is available. When forcing distinctness would
    push an entry far from its free colour (two violets fighting over
    one machine violet, two sun-golds over one yellow-white), it MERGES
    into the taken entry instead of inventing a loud hue the source
    never had. The metric carries THE GREY-AXIS RULE, the old CPC
    recipe's wisdom relearned on the beach's water: a chromatic entry
    never lands on mid-grey or white (black stays legal, darkness is
    achromatic), and losing saturation costs, so a light-blue shimmer
    expresses as the machine's nearest BLUE, not its grey."""
    def _exp_dist(f, m):
        sf = max(f) - min(f)
        sm = max(m) - min(m)
        if sf >= 32 and sm == 0 and m != (0, 0, 0):
            return 1 << 30
        # KNOB 3 (the CPC beach round, 2026-08-09): a quiet dark entry
        # stays quiet. The green ground dots were a dark teal (luma 36)
        # expressed to the cube's pure green (luma 75): plain distance
        # liked the hue and ignored the shout. Below the floor no entry
        # may lift its luminance past 24, and the landing among the quiet
        # options is ranked luminance-first, or the clamped entries crowd
        # the cube's one dark chromatic corner (the first iteration's
        # dark-red flood).
        lf = 0.299 * f[0] + 0.587 * f[1] + 0.114 * f[2]
        lm = 0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]
        if lf < 56.0:
            if lm - lf > 24.0:
                return 1 << 29
            return _dist_luma(f, m, 20) + 4 * max(0, sf - sm) * sf
        return _dist(f, m) + 4 * max(0, sf - sm) * sf

    expr = [None] * len(free)
    taken = set()
    for i in usage_order:
        ranked = sorted(range(len(machine)),
                        key=lambda k: _exp_dist(free[i], machine[k]))
        best = ranked[0]
        pick = next((k for k in ranked if k not in taken), best)
        if _exp_dist(free[i], machine[pick]) > merge_far * max(
                1, _exp_dist(free[i], machine[best])):
            pick = best
        taken.add(pick)
        expr[i] = pick
    return expr


def _usage_order(idx, n):
    usage = {}
    for row in idx:
        for i in row:
            usage[i] = usage.get(i, 0) + 1
    return sorted(range(n), key=lambda i: -usage.get(i, 0))


def _p4_from_cpc(cpc):
    """THE PLUS/4 DERIVES FROM THE FROZEN CPC, IN MULTICOLOUR, JUDGED IN
    THE MEASURED PALETTE (Stefan's approval, 2026-07-25, "Finally."):
    TED multicolour, 160 fat pixels, per 4x8 cell TWO private colours
    plus TWO clash-voted global registers, everything from the TED's
    own 128 (the grey ladder included: hardware truth). Each CPC ink
    claims its own TED colour, injective and usage-ordered. The cell
    solve is the night's earned machinery:

    - SEED-AND-GROW free election: a cell whose frequency pair is
      demonstrably bankrupt (optimal error under 0.55 of it, gain over
      4000) seeds an upgrade that grows to neighbours at a relaxed
      threshold (0.85 / 1500), so a jewel (image 8's pond reflection)
      upgrades as one organic region instead of a lone square;
    - COHERENCE RELAXATION elsewhere: a cell adopts a pair two or more
      neighbours use when it costs at most 12 percent more, so smooth
      regions (the moon dome) share pairs and dither flows across cell
      borders instead of cutting rectangles."""
    from itertools import combinations
    pixels, pal = cpc["pixels"], cpc["palette"]
    h, w = cpc["h"], cpc["w"]
    inks_rgb = [_cpc_color(p % 27) for p in pal]
    ted_rgb = []
    ted_hl = []
    for hue in range(16):
        for lu in range(8):
            ted_rgb.append(_ted_color(hue, lu))
            ted_hl.append((hue, lu))
    cells_x, cells_y = w // 4, h // 8
    usage = {}
    for row in pixels:
        for i in row:
            usage[i] = usage.get(i, 0) + 1
    order = sorted(range(len(inks_rgb)), key=lambda i: -usage.get(i, 0))
    to_ted = [0] * len(inks_rgb)
    taken = set()
    # THE PLUS/4 RENDERS THE FAMILY'S COLOUR DECISION (Stefan, 2026-08-11):
    # the assignment is made ONCE in Colodore space by _inks_to_colodore,
    # table and all, and the TED simply reproduces each chosen Colodore
    # colour on its own finer ladder. Distinct Colodore choices stay
    # distinct here; where two inks collapsed onto one Colodore colour the
    # TED separates them onto neighbouring rungs, which it can afford.
    to_col = _inks_to_colodore(inks_rgb, usage)
    for i in order:
        target = _COLODORE[to_col[i]]
        ranked = sorted(range(len(ted_rgb)),
                        key=lambda k: _dist(target, ted_rgb[k]))
        pick = next((k for k in ranked if k not in taken), ranked[0])
        taken.add(pick)
        to_ted[i] = pick
    grid = [[to_ted[pixels[y][x]] for x in range(w)] for y in range(h)]

    # the two global registers: the Polizei clash vote elects both,
    # in measured space (a register byte means what the hardware shows)
    def _clash_vote(exclude):
        hist = {}
        for cy in range(cells_y):
            for cx in range(cells_x):
                seen = {}
                for yy in range(8):
                    for xx in range(4):
                        c = grid[cy * 8 + yy][cx * 4 + xx]
                        seen[c] = seen.get(c, 0) + 1
                if len([k for k in seen if k not in exclude]) > 2:
                    for k, n in seen.items():
                        if k not in exclude:
                            hist[k] = hist.get(k, 0) + n
        return max(hist, key=hist.get) if hist else None
    bg = _clash_vote(set())
    if bg is None:
        allc = {}
        for row in grid:
            for c in row:
                allc[c] = allc.get(c, 0) + 1
        bg = max(allc, key=allc.get)
    aux = _clash_vote({bg})
    if aux is None:
        aux = bg
    bg_rgb, aux_rgb = ted_rgb[bg], ted_rgb[aux]

    cells = []
    for cy in range(cells_y):
        for cx in range(cells_x):
            idxs = [pixels[cy * 8 + yy][cx * 4 + xx]
                    for yy in range(8) for xx in range(4)]
            # THE CELL SOLVE JUDGES AGAINST THE FAMILY'S DECISION, not the
            # raw CPC ink (Stefan's catch, 2026-08-11). Measuring against
            # the ink let every upgraded cell re-derive its own answer in
            # TED space and discard the Colodore choice: picture 8's green
            # sky came back teal, picture 1's grey fog came back violet.
            # The intended colour is what the cell must reproduce.
            src_px = [_COLODORE[to_col[i]] for i in idxs]
            cnt = {}
            for i in idxs:
                cnt[to_ted[i]] = cnt.get(to_ted[i], 0) + 1
            freq = [k for k, _n in sorted(cnt.items(),
                                          key=lambda kv: -kv[1])
                    if ted_rgb[k] != bg_rgb and ted_rgb[k] != aux_rgb][:2]
            while len(freq) < 2:
                freq.append(freq[0] if freq else 0)
            cells.append({"src": src_px, "pair": tuple(sorted(freq))})

    def cell_err(i, pair):
        quad = [bg_rgb, aux_rgb, ted_rgb[pair[0]], ted_rgb[pair[1]]]
        return sum(min(_dist(c, q) for q in quad) for c in cells[i]["src"])

    for i, c in enumerate(cells):
        c["e_freq"] = cell_err(i, c["pair"])
        pool = []
        for s in set(c["src"]):
            rk = sorted(range(len(ted_rgb)),
                        key=lambda k: _dist(s, ted_rgb[k]))
            for k in rk[:3]:
                if k not in pool:
                    pool.append(k)
        best, bd = c["pair"], c["e_freq"]
        for a, b in combinations(pool, 2):
            e = cell_err(i, (a, b))
            if e < bd:
                best, bd = tuple(sorted((a, b))), e
        c["opt"], c["e_opt"] = best, bd

    up = [c["e_opt"] < 0.55 * c["e_freq"] and
          c["e_freq"] - c["e_opt"] > 4000 for c in cells]
    changed = True
    while changed:
        changed = False
        for i, c in enumerate(cells):
            if up[i]:
                continue
            cy, cx = divmod(i, cells_x)
            neigh = [(cy + dy) * cells_x + (cx + dx)
                     for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))
                     if 0 <= cy + dy < cells_y and 0 <= cx + dx < cells_x]
            if any(up[nb] for nb in neigh) and \
                    c["e_opt"] < 0.85 * c["e_freq"] and \
                    c["e_freq"] - c["e_opt"] > 1500:
                up[i] = True
                changed = True
    for i, c in enumerate(cells):
        if up[i]:
            c["pair"] = c["opt"]

    sweeps = 0
    moved = 1
    while moved and sweeps < 6:
        moved = 0
        sweeps += 1
        for i, c in enumerate(cells):
            if up[i]:
                continue
            cy, cx = divmod(i, cells_x)
            neigh = [(cy + dy) * cells_x + (cx + dx)
                     for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))
                     if 0 <= cy + dy < cells_y and 0 <= cx + dx < cells_x]
            npairs = {}
            for nb in neigh:
                pr = cells[nb]["pair"]
                npairs[pr] = npairs.get(pr, 0) + 1
            cur_e = cell_err(i, c["pair"])
            for pr, votes in sorted(npairs.items(), key=lambda kv: -kv[1]):
                if pr == c["pair"] or votes < 2:
                    continue
                if cell_err(i, pr) <= cur_e * 1.12:
                    c["pair"] = pr
                    moved += 1
                    break

    pixels_out = [[0] * w for _ in range(h)]
    screen = []
    color = []
    for i, c in enumerate(cells):
        cy, cx = divmod(i, cells_x)
        a, b = c["pair"]
        quad = [bg_rgb, ted_rgb[a], ted_rgb[b], aux_rgb]
        for i2, s in enumerate(c["src"]):
            yy, xx = divmod(i2, 4)
            pixels_out[cy * 8 + yy][cx * 4 + xx] = min(
                range(4), key=lambda q: _dist(s, quad[q]))
        ha, la = ted_hl[a]
        hb, lb = ted_hl[b]
        screen.append((ha << 4) | hb)
        # the luminance byte is CROSSED on the metal (the conventions
        # quadrant probe, 2026-07-25): %01 reads the LOW luma nibble,
        # %10 the HIGH, while hues read straight
        color.append((lb << 4) | la)
    bh, bl = ted_hl[bg]
    ah, al = ted_hl[aux]
    return {"w": w, "h": h, "pixels": pixels_out, "screen": screen,
            "color": color, "regs": [(bh << 4) | bl, (ah << 4) | al]}


def _convert_p4(rows, salient=None):
    # The Plus/4 is a child of the frozen CPC, like the C64: one family
    # reduction, expressed downhill. The hires diffusion build that
    # seeded the pipeline lives in git history.
    return _p4_from_cpc(_convert_cpc(rows, salient))


_CONVERTERS = {"AMI": _convert_ami, "AST": _convert_ast, "DOS": _convert_dos,
               "C64": _convert_c64, "ZX3": _convert_zx3, "CPC": _convert_cpc,
               "P4": _convert_p4,
               "A8": _convert_a8, "TRSM4": _convert_trsm4,
               "MS1": _convert_ms1, "MS2": _convert_ms2, "AGN": _convert_agn}


# -- the Spectrum polish round-trip (.scr in and out) ---------------------------
#
# The ZX framing (Stefan's ruling, 2026-07-08): the conversions are strong
# starting points, and depending on the image an author may want to polish
# a few cells by hand. So arcimg speaks the editors' language: `arcimg scr`
# writes a conversion as a standard 6912-byte .scr (the band at the top, a
# black bar below to keep the full 256x192 frame every editor expects), the
# author polishes it in SevenuP, img2spec, or any Spectrum tool, and
# `arcimg unscr` takes the fixed file back, strips the bar, and returns it
# to the portfolio as a hand-authored .arc that `arcimg convert` will never
# overwrite (header byte 15).

def _scr_bitmap_offset(y, xb):
    """The ULA's screen interleave: y to its bitmap row address."""
    return ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | xb


def scr_from_native(native) -> bytes:
    """A ZX3 native dict as a full 6912-byte .scr: band at top, black bar
    below (paper black, ink black, bitmap clear)."""
    w, h = native["w"], native["h"]
    out = bytearray(6912)
    for y in range(h):
        for xb in range(w // 8):
            b = 0
            for bit in range(8):
                b = (b << 1) | native["pixels"][y][xb * 8 + bit]
            out[_scr_bitmap_offset(y, xb)] = b
    for cy in range(h // 8):
        for cx in range(w // 8):
            out[6144 + cy * 32 + cx] = native["attrs"][cy * (w // 8) + cx]
    return bytes(out)


def native_from_scr(data: bytes, mode: int):
    """The top band of a .scr back into a ZX3 native dict, with the lint
    warnings an import deserves: content below the band is dropped (and
    said so), FLASH attributes are refused (the band never flashes)."""
    if len(data) != 6912:
        raise ValueError(f"a .scr is 6912 bytes, this is {len(data)}")
    w, h = 256, mode * 8
    pixels = [[0] * w for _ in range(h)]
    for y in range(h):
        for xb in range(w // 8):
            b = data[_scr_bitmap_offset(y, xb)]
            for bit in range(8):
                pixels[y][xb * 8 + bit] = (b >> (7 - bit)) & 1
    attrs = []
    warnings = []
    for cy in range(h // 8):
        for cx in range(32):
            a = data[6144 + cy * 32 + cx]
            if a & 0x80:
                raise ValueError(
                    f"cell ({cx},{cy}) sets FLASH; the band never flashes")
            attrs.append(a)
    below = False
    for y in range(h, 192):
        for xb in range(32):
            if data[_scr_bitmap_offset(y, xb)]:
                below = True
    if any(data[6144 + cy * 32 + cx]
           for cy in range(h // 8, 24) for cx in range(32)):
        below = True
    if below:
        warnings.append(f"content below the {h}-row band was dropped")
    return {"w": w, "h": h, "pixels": pixels, "attrs": attrs}, warnings


def _read_hint(path: str):
    """The optional author sidecar beside a master: 8.png may have 8.hint,
    a small JSON file. {"salient": [[cx, cy, r], ...]} marks the bright
    objects that must stay visible after conversion (a moon, a sun), as
    discs in master pixel coordinates. Seconds of author work, and every
    target benefits at once; detection was tried and is not reliable on
    pixel art (clouds share the moon's colors, trees occlude its shape),
    so the author states the intent and the tool honors it."""
    hint = os.path.splitext(path)[0] + ".hint"
    if not os.path.exists(hint):
        return None
    import json
    with open(hint) as f:
        data = json.load(f)
    discs = data.get("salient")
    return [tuple(int(v) for v in d) for d in discs] if discs else None


def _salient_pixels(rows, discs):
    """The set of (x, y) the hint protects: within each disc, the pixels of
    its bright side. An occluder in front (trees before the moon) is darker
    and stays untouched; a fully visible disc (the sun) is taken whole."""
    h, w = len(rows), len(rows[0])
    out = set()
    for cx, cy, r in discs:
        lums = []
        for y in range(max(0, cy - r), min(h, cy + r + 1)):
            for x in range(max(0, cx - r), min(w, cx + r + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    c = rows[y][x]
                    lums.append((2 * c[0] + 4 * c[1] + c[2], x, y))
        if not lums:
            continue
        lums.sort()
        half = len(lums) // 2
        dark = sum(l for l, _x, _y in lums[:half]) / max(1, half)
        bright = sum(l for l, _x, _y in lums[half:]) / (len(lums) - half)
        if bright - dark < 200:      # uniform disc: all of it is the object
            out.update((x, y) for _l, x, y in lums)
            continue
        # Occluded disc: the author's circle is the shape's truth, so only
        # clear occluders (trees in front, near the dark cluster) are
        # excluded; the low cut keeps the artist's own rim-dither inside
        # the disc so the shape stays round instead of notched. CONNECTED
        # from the crown: only the bright region reachable from the disc's
        # topmost bright row is the object. A low moon's circle reaches
        # below the treeline, and bright ground pixels there (path glints,
        # water) are NOT the moon; without this they mirror a second
        # half-disc into the foreground.
        cut = dark + (bright - dark) * 0.35
        bright_set = {(x, y) for l, x, y in lums if l >= cut}
        if not bright_set:
            continue
        top_y = min(y for _x, y in bright_set)
        frontier = [(x, y) for x, y in bright_set if y <= top_y + 1]
        seen = set(frontier)
        while frontier:
            x, y = frontier.pop()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in bright_set and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    frontier.append((nx, ny))
        out.update(seen)
    return out


def convert_master(path: str, tag: str):
    """A band-shaped master PNG into (mode, native dict) for a target."""
    rows = _read_png(path)
    w, h = len(rows[0]), len(rows)
    if (w, h) not in ((320, 72), (320, 96)):
        raise ValueError(
            f"{path}: a master is 320x72 or 320x96, this is {w}x{h}")
    if tag not in _CONVERTERS:
        raise ValueError(
            f"no converter for target {tag} yet (wave order, arc_image/reference/design.md); "
            f"available: {', '.join(sorted(_CONVERTERS))}")
    discs = _read_hint(path)
    salient = _salient_pixels(rows, discs) if discs else None
    return (9 if h == 72 else 12), _CONVERTERS[tag](rows, salient)


# -- a minimal PNG writer (stdlib; render-back needs no Pillow) -----------------

def _write_png(path: str, rows) -> None:
    """Write RGB rows (each a list of (r,g,b)) as a PNG. Filter 0 per row."""
    h = len(rows)
    w = len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for r, g, b in row:
            raw += bytes((r, g, b))
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
    with open(path, "wb") as f:
        f.write(_PNG_SIG)
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


# -- per-target layout packers and renderers -----------------------------------
#
# Each target packs a NATIVE image (a dict whose shape is the machine's own:
# indexed pixels plus the cell matrices and registers it needs) into its .arc
# sections, unpacks them back, and renders the native image to RGB rows for
# the PNG preview. pack/unpack are exact inverses; the tests hold them to it.
# The pixel index conventions match the payload layout notes in arc_image/reference/design.md s.10.

def _planar_rows(pixels, w, h, planes):
    """Amiga-style row-interleaved bitplanes: per row, one 40-byte (w/8) row
    per plane, plane 0 first. Bit 7 is the leftmost pixel."""
    out = bytearray()
    span = w // 8
    for y in range(h):
        row = pixels[y]
        for p in range(planes):
            for bx in range(span):
                byte = 0
                for bit in range(8):
                    if (row[bx * 8 + bit] >> p) & 1:
                        byte |= 0x80 >> bit
                out.append(byte)
    return bytes(out)


def _unplanar_rows(data, w, h, planes):
    span = w // 8
    pixels = [[0] * w for _ in range(h)]
    pos = 0
    for y in range(h):
        for p in range(planes):
            for bx in range(span):
                byte = data[pos]
                pos += 1
                for bit in range(8):
                    if byte & (0x80 >> bit):
                        pixels[y][bx * 8 + bit] |= 1 << p
    return pixels


def _st_words(pixels, w, h):
    """The ST's fixed interleave: per 16-pixel group, 4 consecutive plane
    words. Bit 15 is the leftmost pixel of the group."""
    out = bytearray()
    for y in range(h):
        row = pixels[y]
        for gx in range(0, w, 16):
            for p in range(4):
                word = 0
                for bit in range(16):
                    if (row[gx + bit] >> p) & 1:
                        word |= 0x8000 >> bit
                out += struct.pack(">H", word)
    return bytes(out)


def _un_st_words(data, w, h):
    pixels = [[0] * w for _ in range(h)]
    pos = 0
    for y in range(h):
        for gx in range(0, w, 16):
            for p in range(4):
                (word,) = struct.unpack(">H", data[pos:pos + 2])
                pos += 2
                for bit in range(16):
                    if word & (0x8000 >> bit):
                        pixels[y][gx + bit] |= 1 << p
    return pixels


def _cells_bitmap(pixels, w, h, bits):
    """C64-family cell-ordered bitmap: per 8px-tall cell row, per cell, the
    cell's 8 line bytes. `bits` is 1 (hires: 8 pixels) or 2 (multicolor: 4)."""
    per_byte = 8 // bits
    out = bytearray()
    cells_x = w // per_byte
    for cy in range(h // 8):
        for cx in range(cells_x):
            for line in range(8):
                row = pixels[cy * 8 + line]
                byte = 0
                for i in range(per_byte):
                    byte = (byte << bits) | row[cx * per_byte + i]
                out.append(byte)
    return bytes(out)


def _un_cells_bitmap(data, w, h, bits):
    per_byte = 8 // bits
    mask = (1 << bits) - 1
    pixels = [[0] * w for _ in range(h)]
    cells_x = w // per_byte
    pos = 0
    for cy in range(h // 8):
        for cx in range(cells_x):
            for line in range(8):
                byte = data[pos]
                pos += 1
                for i in range(per_byte):
                    shift = bits * (per_byte - 1 - i)
                    pixels[cy * 8 + line][cx * per_byte + i] = (byte >> shift) & mask
    return pixels


def _pack_1bpp(pixels, w, h):
    """Plain 1bpp rows, bit 7 leftmost (VDC, and the Spectrum's row form
    before the interleave reorders whole rows)."""
    out = bytearray()
    for y in range(h):
        for bx in range(w // 8):
            byte = 0
            for bit in range(8):
                if pixels[y][bx * 8 + bit]:
                    byte |= 0x80 >> bit
            out.append(byte)
    return bytes(out)


def _unpack_1bpp(data, w, h):
    pixels = [[0] * w for _ in range(h)]
    span = w // 8
    for y in range(h):
        for bx in range(span):
            byte = data[y * span + bx]
            for bit in range(8):
                pixels[y][bx * 8 + bit] = 1 if byte & (0x80 >> bit) else 0
    return pixels


def _zx_row_order(h):
    """Band rows in ascending ULA screen address: address bits are
    T T LLL RRR (third, line-in-char, char-row), so order by
    (third, line-in-char, char-row)."""
    return sorted(range(h), key=lambda y: (y >> 6, y & 7, (y >> 3) & 7))


def _cpc_row_order(h):
    """Band rows in ascending screen-block address: the eight 0x800
    sub-blocks each hold every 8th line, so order by (line mod 8, line div 8)."""
    return sorted(range(h), key=lambda y: (y & 7, y >> 3))


def _cpc_mode0_byte(pa, pb):
    """The Mode 0 pixel-bit shuffle (CPCWiki): byte bits 7,5,3,1 carry pixel
    A's bits 0,2,1,3 and bits 6,4,2,0 carry pixel B's. Verified against the
    firmware tables; the wave-2 probe re-proves it on hardware layout."""
    return (((pa & 1) << 7) | ((pb & 1) << 6)
            | (((pa >> 2) & 1) << 5) | (((pb >> 2) & 1) << 4)
            | (((pa >> 1) & 1) << 3) | (((pb >> 1) & 1) << 2)
            | (((pa >> 3) & 1) << 1) | ((pb >> 3) & 1))


def _cpc_mode0_unbyte(byte):
    pa = (((byte >> 7) & 1) | (((byte >> 3) & 1) << 1)
          | (((byte >> 5) & 1) << 2) | (((byte >> 1) & 1) << 3))
    pb = (((byte >> 6) & 1) | (((byte >> 2) & 1) << 1)
          | (((byte >> 4) & 1) << 2) | ((byte & 1) << 3))
    return pa, pb


# The target registry. Geometry is (width per mode is fixed; height = mode*8
# except where the target's pixel shape differs, and it never does: every
# machine's band is mode*8 of ITS OWN pixels; only the WIDTH varies).

TARGETS = {}


class Target:
    def __init__(self, tid, tag, width, pack, unpack, render, pattern,
                 codec=CODEC_ZX0):
        self.id = tid
        self.tag = tag
        self.width = width
        self.pack = pack        # native dict -> [(type, flags, bytes)]
        self.unpack = unpack    # (sections, w, h) -> native dict
        self.render = render    # (native, w, h) -> RGB rows
        self.pattern = pattern  # (w, h) -> native dict (a legal test image)
        self.codec = codec      # the codec this target's chapter mandates

    def height(self, mode):
        return mode * 8


# The 16-bit big-disk targets take LZSA2, everything else ZX0 (the codec
# ruling; the note above lzsa2_compress has the measured trade).
_LZSA2_TAGS = {"AMI", "AST", "DOS", "M65", "MS2", "NXT"}
_RLE_TAGS = {"AGN"}    # Shawn Sijnstra's ruling for the Agon: RLE keeps
                       # the eZ80 loader's memory management trivial, and
                       # the SD card does not count bytes


def _target(tid, tag, width):
    def deco(cls):
        codec = (CODEC_RLE if tag in _RLE_TAGS else
                 CODEC_LZSA2 if tag in _LZSA2_TAGS else CODEC_ZX0)
        TARGETS[tag] = Target(tid, tag, width, cls.pack, cls.unpack,
                              cls.render, cls.pattern, codec)
        return cls
    return deco


def _sections_by_type(sections):
    return {stype: raw for stype, _flags, raw in sections}


# ---- AMI: 5 bitplanes row-interleaved + $0RGB palette -------------------------

@_target(1, "AMI", 320)
class _Ami:
    @staticmethod
    def pack(native):
        pal = bytearray()
        for r, g, b in native["palette"]:
            pal += struct.pack(">H", ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4))
        return [(SEC_BITMAP, 0, _planar_rows(native["pixels"], native["w"], native["h"], 5)),
                (SEC_PALETTE, 0, bytes(pal))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        pal = []
        raw = s[SEC_PALETTE]
        for i in range(0, len(raw), 2):
            (word,) = struct.unpack(">H", raw[i:i + 2])
            pal.append((((word >> 8) & 15) * 17, ((word >> 4) & 15) * 17,
                        (word & 15) * 17))
        return {"w": w, "h": h, "pixels": _unplanar_rows(s[SEC_BITMAP], w, h, 5),
                "palette": pal}

    @staticmethod
    def render(native, w, h):
        pal = native["palette"]
        return [[pal[p] for p in row] for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        # Palette entries are 4-bit fixed points (multiples of 17), the
        # values the hardware can show: the snap rule, obeyed at the source.
        pal = [((i % 16) * 17, (15 - i % 16) * 17, ((i * 3) % 16) * 17)
               for i in range(32)]
        pixels = [[((x // 10) + (y // 8) * 3) % 32 for x in range(w)]
                  for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}


# ---- AST: ST word-interleaved 4 planes + 3-bit palette -------------------------

@_target(2, "AST", 320)
class _Ast:
    @staticmethod
    def pack(native):
        pal = bytearray()
        for r, g, b in native["palette"]:
            pal += struct.pack(">H", ((r >> 5) << 8) | ((g >> 5) << 4) | (b >> 5))
        return [(SEC_BITMAP, 0, _st_words(native["pixels"], native["w"], native["h"])),
                (SEC_PALETTE, 0, bytes(pal))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        pal = []
        raw = s[SEC_PALETTE]
        for i in range(0, len(raw), 2):
            (word,) = struct.unpack(">H", raw[i:i + 2])
            c3 = lambda v: round(v * 255 / 7)
            pal.append((c3((word >> 8) & 7), c3((word >> 4) & 7), c3(word & 7)))
        return {"w": w, "h": h, "pixels": _un_st_words(s[SEC_BITMAP], w, h),
                "palette": pal}

    @staticmethod
    def render(native, w, h):
        pal = native["palette"]
        return [[pal[p] for p in row] for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        pal = [(round((i & 7) * 255 / 7), round((7 - (i & 7)) * 255 / 7),
                round(((i * 3) & 7) * 255 / 7)) for i in range(16)]
        pixels = [[((x // 20) + (y // 16)) % 16 for x in range(w)]
                  for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}


# ---- DOS: chunky mode 13h + 6-bit DAC palette ---------------------------------

@_target(3, "DOS", 320)
class _Dos:
    @staticmethod
    def pack(native):
        pal = bytearray()
        for r, g, b in native["palette"]:
            pal += bytes((r >> 2, g >> 2, b >> 2))
        flat = bytearray()
        for row in native["pixels"]:
            flat += bytes(row)
        return [(SEC_BITMAP, 0, bytes(flat)), (SEC_PALETTE, 0, bytes(pal))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        raw = s[SEC_PALETTE]
        c6 = lambda v: round(v * 255 / 63)
        pal = [(c6(raw[i]), c6(raw[i + 1]), c6(raw[i + 2]))
               for i in range(0, len(raw), 3)]
        bm = s[SEC_BITMAP]
        pixels = [list(bm[y * w:(y + 1) * w]) for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}

    @staticmethod
    def render(native, w, h):
        pal = native["palette"]
        return [[pal[p] for p in row] for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        # 6-bit DAC fixed points, per the snap rule.
        c6 = lambda v: round((v % 64) * 255 / 63)
        pal = [(c6(i * 5), c6(i * 3), c6(255 - i)) for i in range(256)]
        pixels = [[(x + y * 2) % 256 for x in range(w)] for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}


# ---- C64: multicolor bitmap + screen + color RAM + background -----------------

@_target(4, "C64", 160)
class _C64:
    @staticmethod
    def pack(native):
        return [(SEC_BITMAP, 0, _cells_bitmap(native["pixels"], native["w"], native["h"], 2)),
                (SEC_SCREEN, 0, bytes(native["screen"])),
                (SEC_COLOR, 0, bytes(native["color"])),
                (SEC_REGS, 0, bytes(native["regs"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        return {"w": w, "h": h,
                "pixels": _un_cells_bitmap(s[SEC_BITMAP], w, h, 2),
                "screen": list(s[SEC_SCREEN]), "color": list(s[SEC_COLOR]),
                "regs": list(s[SEC_REGS])}

    @staticmethod
    def render(native, w, h):
        cells_x = w // 4
        bg = native["regs"][0] & 15
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                cell = (y // 8) * cells_x + (x // 4)
                code = native["pixels"][y][x]
                if code == 0:
                    c = bg
                elif code == 1:
                    c = (native["screen"][cell] >> 4) & 15
                elif code == 2:
                    c = native["screen"][cell] & 15
                else:
                    c = native["color"][cell] & 15
                rgb = _COLODORE[c]
                row.append(rgb)
                row.append(rgb)  # 2:1 wide pixels render doubled
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        cells_x, cells_y = w // 4, h // 8
        pixels = [[(x // 1 + y) % 4 for x in range(w)] for y in range(h)]
        screen = [((c * 7) % 256) & 0xFF for c in range(cells_x * cells_y)]
        color = [(c * 3) % 16 for c in range(cells_x * cells_y)]
        return {"w": w, "h": h, "pixels": pixels, "screen": screen,
                "color": color, "regs": [6]}


# ---- P4: TED hires + color matrix + luminance matrix --------------------------

@_target(5, "P4", 160)
class _P4:
    # TED MULTICOLOUR (Stefan's ruling: hires abandoned 2026-07-23).
    # 160 fat pixels, 2-bit codes per pixel: %00 the background register,
    # %01/%10 the cell's two private colours (hue matrix high/low nibble,
    # luminance matrix likewise), %11 the second global register. The two
    # register bytes travel as (hue << 4) | luma each.
    @staticmethod
    def pack(native):
        return [(SEC_BITMAP, 0, _cells_bitmap(native["pixels"], native["w"], native["h"], 2)),
                (SEC_SCREEN, 0, bytes(native["screen"])),
                (SEC_COLOR, 0, bytes(native["color"])),
                (SEC_REGS, 0, bytes(native["regs"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        return {"w": w, "h": h,
                "pixels": _un_cells_bitmap(s[SEC_BITMAP], w, h, 2),
                "screen": list(s[SEC_SCREEN]), "color": list(s[SEC_COLOR]),
                "regs": list(s[SEC_REGS])}

    @staticmethod
    def render(native, w, h):
        cells_x = w // 4

        def reg_rgb(b):
            hue, luma = (b >> 4) & 15, b & 7
            return _ted_color(hue, luma)

        bg = reg_rgb(native["regs"][0])
        aux = reg_rgb(native["regs"][1])
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                cell = (y // 8) * cells_x + (x // 4)
                code = native["pixels"][y][x]
                if code == 0:
                    rgb = bg
                elif code == 3:
                    rgb = aux
                else:
                    hues = native["screen"][cell]
                    lumas = native["color"][cell]
                    if code == 1:
                        hue, luma = (hues >> 4) & 15, lumas & 7
                    else:
                        hue, luma = hues & 15, (lumas >> 4) & 7
                    rgb = _ted_color(hue, luma)
                row.append(rgb)
                row.append(rgb)  # 2:1 wide pixels render doubled
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        cells_x, cells_y = w // 4, h // 8
        pixels = [[(x + y) % 4 for x in range(w)] for y in range(h)]
        screen = [((c % 15) + 1) << 4 | ((c * 5) % 15 + 1)
                  for c in range(cells_x * cells_y)]
        color = [((c % 8) << 4) | (7 - c % 8) for c in range(cells_x * cells_y)]
        return {"w": w, "h": h, "pixels": pixels, "screen": screen,
                "color": color, "regs": [(1 << 4) | 3, (5 << 4) | 6]}


# ---- CPC: Mode 0 with the bit shuffle, sub-block row order --------------------

@_target(6, "CPC", 160)
class _Cpc:
    @staticmethod
    def pack(native):
        w, h = native["w"], native["h"]
        out = bytearray()
        for y in _cpc_row_order(h):
            row = native["pixels"][y]
            for x in range(0, w, 2):
                out.append(_cpc_mode0_byte(row[x], row[x + 1]))
        return [(SEC_BITMAP, 0, bytes(out)),
                (SEC_PALETTE, 0, bytes(native["palette"])),
                (SEC_REGS, 0, bytes(native["regs"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        pixels = [[0] * w for _ in range(h)]
        pos = 0
        bm = s[SEC_BITMAP]
        for y in _cpc_row_order(h):
            for x in range(0, w, 2):
                pa, pb = _cpc_mode0_unbyte(bm[pos])
                pos += 1
                pixels[y][x], pixels[y][x + 1] = pa, pb
        return {"w": w, "h": h, "pixels": pixels,
                "palette": list(s[SEC_PALETTE]), "regs": list(s[SEC_REGS])}

    @staticmethod
    def render(native, w, h):
        inks = native["palette"]
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                rgb = _cpc_color(inks[native["pixels"][y][x]] % 27)
                row.append(rgb)
                row.append(rgb)  # 2:1 wide pixels
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        pixels = [[(x // 10 + y // 8) % 16 for x in range(w)] for y in range(h)]
        palette = [(i * 5 + 2) % 27 for i in range(16)]
        return {"w": w, "h": h, "pixels": pixels, "palette": palette,
                "regs": [0]}


# ---- MS1: Screen 2 pattern + color tables, tile order --------------------------

@_target(7, "MS1", 256)
class _Ms1:
    @staticmethod
    def pack(native):
        w, h = native["w"], native["h"]
        tiles_x = w // 8
        pat = bytearray()
        col = bytearray()
        for ty in range(h // 8):
            for tx in range(tiles_x):
                for line in range(8):
                    pat.append(native["pattern"][ty * 8 + line][tx])
                    col.append(native["colors"][ty * 8 + line][tx])
        return [(SEC_BITMAP, 0, bytes(pat)), (SEC_COLOR, 0, bytes(col))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        tiles_x = w // 8
        pattern = [[0] * tiles_x for _ in range(h)]
        colors = [[0] * tiles_x for _ in range(h)]
        pos = 0
        pat, col = s[SEC_BITMAP], s[SEC_COLOR]
        for ty in range(h // 8):
            for tx in range(tiles_x):
                for line in range(8):
                    pattern[ty * 8 + line][tx] = pat[pos]
                    colors[ty * 8 + line][tx] = col[pos]
                    pos += 1
        return {"w": w, "h": h, "pattern": pattern, "colors": colors}

    @staticmethod
    def render(native, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                byte = native["pattern"][y][x // 8]
                cbyte = native["colors"][y][x // 8]
                on = byte & (0x80 >> (x % 8))
                idx = (cbyte >> 4) if on else (cbyte & 15)
                row.append(_TMS9918[idx if idx else 1])
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        tiles_x = w // 8
        pattern = [[(0xF0 if (y // 4) % 2 else 0x3C) for _tx in range(tiles_x)]
                   for y in range(h)]
        colors = [[(((y // 8 + tx) % 15 + 1) << 4) | ((tx * 3) % 15 + 1)
                   for tx in range(tiles_x)] for y in range(h)]
        return {"w": w, "h": h, "pattern": pattern, "colors": colors}


# ---- MS2: Screen 5 nibble-packed + V9938 palette ------------------------------

@_target(8, "MS2", 256)
class _Ms2:
    @staticmethod
    def pack(native):
        out = bytearray()
        for row in native["pixels"]:
            for x in range(0, len(row), 2):
                out.append((row[x] << 4) | row[x + 1])
        pal = bytearray()
        for r, g, b in native["palette"]:
            pal.append(((r >> 5) << 4) | (b >> 5))
            pal.append(g >> 5)
        return [(SEC_BITMAP, 0, bytes(out)), (SEC_PALETTE, 0, bytes(pal))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        bm = s[SEC_BITMAP]
        pixels = []
        span = w // 2
        for y in range(h):
            row = []
            for i in range(span):
                byte = bm[y * span + i]
                row.append(byte >> 4)
                row.append(byte & 15)
            pixels.append(row)
        raw = s[SEC_PALETTE]
        c3 = lambda v: round(v * 255 / 7)
        pal = [(c3((raw[i] >> 4) & 7), c3(raw[i + 1] & 7), c3(raw[i] & 7))
               for i in range(0, len(raw), 2)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}

    @staticmethod
    def render(native, w, h):
        pal = native["palette"]
        return [[pal[p] for p in row] for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        pal = [(round((i & 7) * 255 / 7), round(((i * 5) & 7) * 255 / 7),
                round((7 - (i & 7)) * 255 / 7)) for i in range(16)]
        pixels = [[(x // 16 + y // 8) % 16 for x in range(w)] for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}


# ---- ZX3: interleaved-thirds bitmap + attributes ------------------------------

@_target(9, "ZX3", 256)
class _Zx3:
    @staticmethod
    def pack(native):
        w, h = native["w"], native["h"]
        linear = _pack_1bpp(native["pixels"], w, h)
        span = w // 8
        out = bytearray()
        for y in _zx_row_order(h):
            out += linear[y * span:(y + 1) * span]
        return [(SEC_BITMAP, 0, bytes(out)),
                (SEC_ATTR, 0, bytes(native["attrs"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        span = w // 8
        linear = bytearray(span * h)
        bm = s[SEC_BITMAP]
        for i, y in enumerate(_zx_row_order(h)):
            linear[y * span:(y + 1) * span] = bm[i * span:(i + 1) * span]
        return {"w": w, "h": h, "pixels": _unpack_1bpp(bytes(linear), w, h),
                "attrs": list(s[SEC_ATTR])}

    @staticmethod
    def render(native, w, h):
        cells_x = w // 8
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                attr = native["attrs"][(y // 8) * cells_x + (x // 8)]
                bright = (attr >> 6) & 1
                ink, paper = attr & 7, (attr >> 3) & 7
                on = native["pixels"][y][x]
                row.append(_zx_color(ink if on else paper, bright))
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        cells_x = w // 8
        pixels = [[1 if ((x ^ y) & 4) else 0 for x in range(w)]
                  for y in range(h)]
        attrs = [((c % 8) | (((c * 3) % 8) << 3) | (0x40 if c % 2 else 0))
                 for c in range(cells_x * (h // 8))]
        return {"w": w, "h": h, "pixels": pixels, "attrs": attrs}


# ---- A8: ANTIC mode E + per-line color registers ------------------------------

@_target(10, "A8", 160)
class _A8:
    @staticmethod
    def pack(native):
        out = bytearray()
        for row in native["pixels"]:
            for x in range(0, len(row), 4):
                out.append((row[x] << 6) | (row[x + 1] << 4)
                           | (row[x + 2] << 2) | row[x + 3])
        return [(SEC_BITMAP, 0, bytes(out)),
                (SEC_LINETABLE, 0, bytes(native["lines"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        bm = s[SEC_BITMAP]
        span = w // 4
        pixels = []
        for y in range(h):
            row = []
            for i in range(span):
                byte = bm[y * span + i]
                row += [(byte >> 6) & 3, (byte >> 4) & 3, (byte >> 2) & 3,
                        byte & 3]
            pixels.append(row)
        return {"w": w, "h": h, "pixels": pixels,
                "lines": list(s[SEC_LINETABLE])}

    @staticmethod
    def render(native, w, h):
        rows = []
        for y in range(h):
            regs = native["lines"][y * 4:(y + 1) * 4]
            row = []
            for x in range(w):
                rgb = _gtia_color(regs[native["pixels"][y][x]])
                row.append(rgb)
                row.append(rgb)  # 2:1 wide pixels
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        pixels = [[(x // 8 + y // 8) % 4 for x in range(w)] for y in range(h)]
        lines = []
        for y in range(h):
            lines += [((y // 8) % 16) << 4 | 2, ((y // 4) % 16) << 4 | 6,
                      ((y // 2) % 16) << 4 | 10, (y % 16) << 4 | 14]
        return {"w": w, "h": h, "pixels": pixels, "lines": lines}


# ---- AP2: HGR bytes in display row order --------------------------------------

@_target(11, "AP2", 280)
class _Ap2:
    @staticmethod
    def pack(native):
        out = bytearray()
        for y in range(native["h"]):
            for bx in range(native["w"] // 7):
                byte = native["hibits"][y][bx] << 7
                for i in range(7):
                    if native["pixels"][y][bx * 7 + i]:
                        byte |= 1 << i
                out.append(byte)
        return [(SEC_BITMAP, 0, bytes(out))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        bm = s[SEC_BITMAP]
        span = w // 7
        pixels = [[0] * w for _ in range(h)]
        hibits = [[0] * span for _ in range(h)]
        for y in range(h):
            for bx in range(span):
                byte = bm[y * span + bx]
                hibits[y][bx] = (byte >> 7) & 1
                for i in range(7):
                    pixels[y][bx * 7 + i] = (byte >> i) & 1
        return {"w": w, "h": h, "pixels": pixels, "hibits": hibits}

    @staticmethod
    def render(native, w, h):
        # A simplified HGR preview: lit pixels take the group's artifact
        # pair by column parity, adjacent lit pixels read white. The wave-4
        # addendum brings the NTSC-modeled version.
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                if not native["pixels"][y][x]:
                    row.append(_HGR["black"])
                    continue
                left = x > 0 and native["pixels"][y][x - 1]
                right = x < w - 1 and native["pixels"][y][x + 1]
                if left or right:
                    row.append(_HGR["white"])
                    continue
                pair = native["hibits"][y][x // 7]
                if x % 2 == 0:
                    row.append(_HGR["blue"] if pair else _HGR["purple"])
                else:
                    row.append(_HGR["orange"] if pair else _HGR["green"])
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        pixels = [[1 if (x + y) % 4 == 0 else 0 for x in range(w)]
                  for y in range(h)]
        hibits = [[(bx + y // 8) % 2 for bx in range(w // 7)]
                  for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "hibits": hibits}


# ---- NXT: Layer 2 column-major + 9-bit palette ---------------------------------

@_target(12, "NXT", 320)
class _Nxt:
    @staticmethod
    def pack(native):
        w, h = native["w"], native["h"]
        out = bytearray()
        for x in range(w):
            for y in range(h):
                out.append(native["pixels"][y][x])
        pal = bytearray()
        for r, g, b in native["palette"]:
            r3, g3, b3 = r >> 5, g >> 5, b >> 5
            pal.append((r3 << 5) | (g3 << 2) | (b3 >> 1))
            pal.append(b3 & 1)
        return [(SEC_BITMAP, 0, bytes(out)), (SEC_PALETTE, 0, bytes(pal))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        bm = s[SEC_BITMAP]
        pixels = [[0] * w for _ in range(h)]
        pos = 0
        for x in range(w):
            for y in range(h):
                pixels[y][x] = bm[pos]
                pos += 1
        raw = s[SEC_PALETTE]
        c3 = lambda v: round(v * 255 / 7)
        pal = []
        for i in range(0, len(raw), 2):
            b0, b1 = raw[i], raw[i + 1]
            pal.append((c3(b0 >> 5), c3((b0 >> 2) & 7),
                        c3(((b0 & 3) << 1) | (b1 & 1))))
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}

    @staticmethod
    def render(native, w, h):
        pal = native["palette"]
        return [[pal[p] for p in row] for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        pal = [(round(((i >> 5) & 7) * 255 / 7),
                round(((i >> 2) & 7) * 255 / 7),
                round((i & 3) * 2 * 255 / 7)) for i in range(256)]
        pixels = [[(x + y) % 256 for x in range(w)] for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}


# ---- M65: FCM chars + nibble-swapped palette -----------------------------------

@_target(13, "M65", 320)
class _M65:
    @staticmethod
    def pack(native):
        w, h = native["w"], native["h"]
        out = bytearray()
        for cy in range(h // 8):
            for cx in range(w // 8):
                for line in range(8):
                    for i in range(8):
                        out.append(native["pixels"][cy * 8 + line][cx * 8 + i])
        swap = lambda v: ((v & 15) << 4) | (v >> 4)
        pal = bytearray()
        for r, g, b in native["palette"]:
            pal += bytes((swap(r), swap(g), swap(b)))
        return [(SEC_BITMAP, 0, bytes(out)), (SEC_PALETTE, 0, bytes(pal))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        bm = s[SEC_BITMAP]
        pixels = [[0] * w for _ in range(h)]
        pos = 0
        for cy in range(h // 8):
            for cx in range(w // 8):
                for line in range(8):
                    for i in range(8):
                        pixels[cy * 8 + line][cx * 8 + i] = bm[pos]
                        pos += 1
        swap = lambda v: ((v & 15) << 4) | (v >> 4)
        raw = s[SEC_PALETTE]
        pal = [(swap(raw[i]), swap(raw[i + 1]), swap(raw[i + 2]))
               for i in range(0, len(raw), 3)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}

    @staticmethod
    def render(native, w, h):
        pal = native["palette"]
        return [[pal[p if p < len(pal) else 0] for p in row]
                for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        pal = [((i * 2) & 0xFF, (255 - i) & 0xFF, (i * 5) & 0xFF)
               for i in range(255)]
        pixels = [[(x * 2 + y) % 255 for x in range(w)] for y in range(h)]
        return {"w": w, "h": h, "pixels": pixels, "palette": pal}


# ---- VDC: 1bpp 640-wide + fg/bg attributes -------------------------------------

@_target(14, "VDC", 640)
class _Vdc:
    @staticmethod
    def pack(native):
        return [(SEC_BITMAP, 0, _pack_1bpp(native["pixels"], native["w"], native["h"])),
                (SEC_ATTR, 0, bytes(native["attrs"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        return {"w": w, "h": h, "pixels": _unpack_1bpp(s[SEC_BITMAP], w, h),
                "attrs": list(s[SEC_ATTR])}

    @staticmethod
    def render(native, w, h):
        cells_x = w // 8
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                attr = native["attrs"][(y // 8) * cells_x + (x // 8)]
                on = native["pixels"][y][x]
                row.append(_vdc_color((attr >> 4) & 15 if on else attr & 15))
            rows.append(row)
        return rows

    @staticmethod
    def pattern(w, h):
        cells_x = w // 8
        pixels = [[1 if ((x // 2) ^ y) & 2 else 0 for x in range(w)]
                  for y in range(h)]
        attrs = [((c % 16) << 4) | ((c * 5) % 16)
                 for c in range(cells_x * (h // 8))]
        return {"w": w, "h": h, "pixels": pixels, "attrs": attrs}


def encode_native(tag: str, mode: int, image_id: int, native,
                  codec=None, hand=False) -> bytes:
    """A native image (the target's own dict shape) into .arc bytes. The
    codec defaults to the target's own (LZSA2 on the 16-bit trio, ZX0
    elsewhere); pass one explicitly to override. `hand` marks the file
    hand-authored (see write_arc)."""
    t = TARGETS[tag]
    return write_arc(t.id, mode, native["w"], native["h"], image_id,
                     t.pack(native), t.codec if codec is None else codec,
                     hand)


# ---- TRSM4: the TRS-80 Model 4 hi-res board, 1bpp monochrome ------------------
#
# The first target whose INTERPRETER lives outside the family (Shawn
# Sijnstra's Model 4 engine; ruled 2026-07-17: the target itself is
# first-class arc_image regardless). One section: the bitmap, 80 bytes a
# row, bit 7 leftmost (Shawn's spec: 132 lights x....x..), decoded by the
# ring model like every codec-1 target.

@_target(15, "TRSM4", 640)
class _Trsm4:
    @staticmethod
    def pack(native):
        return [(SEC_BITMAP, 0,
                 _pack_1bpp(native["pixels"], native["w"], native["h"]))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        return {"w": w, "h": h, "pixels": _unpack_1bpp(s[SEC_BITMAP], w, h)}

    @staticmethod
    def render(native, w, h):
        on, off = (232, 232, 232), (16, 16, 16)
        return [[on if native["pixels"][y][x] else off for x in range(w)]
                for y in range(h)]

    @staticmethod
    def pattern(w, h):
        return {"w": w, "h": h,
                "pixels": [[1 if ((x ^ y) & 8) else 0 for x in range(w)]
                           for y in range(h)]}


# ---- AGN: Agon Light, VDP mode 3 RGBA2222 -------------------------------------
# Shawn Sijnstra's target (his Canopus interpreter family): 640x240 mode 3,
# the full fixed 64-color cube, one byte per pixel in the VDP's RGBA2222
# order (bits 1-0 R, 3-2 G, 5-4 B, 7-6 alpha; the band ships alpha %11,
# opaque). No palette section: the cube is the hardware. Rows are raw and
# continuous, top to bottom: the loader streams them to the serial VDP
# unframed, and dimensions travel in the display command, not the data.

def _agn_byte(r, g, b):
    return 0xC0 | ((b // 85) << 4) | ((g // 85) << 2) | (r // 85)


@_target(16, "AGN", 640)
class _Agn:
    @staticmethod
    def pack(native):
        out = bytearray()
        for row in native["pixels"]:
            out += bytes(row)
        return [(SEC_BITMAP, 0, bytes(out))]

    @staticmethod
    def unpack(sections, w, h):
        s = _sections_by_type(sections)
        bm = s[SEC_BITMAP]
        return {"w": w, "h": h,
                "pixels": [list(bm[y * w:(y + 1) * w]) for y in range(h)]}

    @staticmethod
    def render(native, w, h):
        return [[((p & 3) * 85, ((p >> 2) & 3) * 85, ((p >> 4) & 3) * 85)
                 for p in row] for row in native["pixels"]]

    @staticmethod
    def pattern(w, h):
        return {"w": w, "h": h,
                "pixels": [[_agn_byte((x // 10) % 4 * 85, (y // 8) % 4 * 85,
                                      ((x + y) // 12) % 4 * 85)
                            for x in range(w)] for y in range(h)]}


def decode_arc(blob: bytes):
    """.arc bytes back into (tag, mode, image id, native dict)."""
    head, sections = read_arc(blob)
    by_id = {t.id: t for t in TARGETS.values()}
    t = by_id.get(head["target"])
    if t is None:
        raise ValueError(f"unknown target id {head['target']}")
    native = t.unpack(sections, head["width"], head["height"])
    return t.tag, head["mode"], head["id"], native


def render_arc(blob: bytes, out_png: str) -> None:
    """Render a .arc to a PNG preview through the target's reference
    palette: the format's own round-trip test, and the author's no-emulator
    preview."""
    tag, _mode, _iid, native = decode_arc(blob)
    t = TARGETS[tag]
    _write_png(out_png, t.render(native, native["w"], native["h"]))


# -- commands ------------------------------------------------------------------

def cmd_prep(args) -> int:
    w, h = MODES[args.mode]
    out_dir = args.out or "."
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, f"{args.id}.png")

    # Fast path: art already a PNG at the exact mode size is just numbered and
    # copied. This is the pixel artist's whole workflow, and it needs no Pillow.
    if _png_size(args.source) == (w, h):
        shutil.copyfile(args.source, dest)
        print(f"arcimg: {args.source} is already {w}x{h} ({args.mode}); "
              f"wrote {dest}")
        return 0

    # Anything else (a photo, a JPEG, a wrong-sized PNG): crop to the mode's
    # aspect and resize to it. This is where Pillow is needed.
    Image = _ensure_pillow()
    try:
        img = Image.open(args.source).convert("RGB")
    except (OSError, ValueError) as exc:
        print(f"arcimg: cannot read {args.source}: {exc}", file=sys.stderr)
        return 2
    img = _crop_to_ratio(img, w, h)
    img = img.resize((w, h), Image.LANCZOS)
    img.save(dest, "PNG")
    print(f"arcimg: wrote {dest} ({w}x{h}, {args.mode} mode)")
    return 0


def _collect_numbered(sources):
    """Map id -> path for every <number>.png in the given files and directories.
    A later source with the same id wins, so a specific file can override a
    directory listed before it."""
    entries = {}
    for src in sources:
        if os.path.isdir(src):
            for name in sorted(os.listdir(src)):
                iid = _numbered_id(name)
                if iid is not None:
                    entries[iid] = os.path.join(src, name)
        elif os.path.isfile(src):
            iid = _numbered_id(src)
            if iid is None:
                print(f"arcimg: skipping {src}: not a <number>.png file",
                      file=sys.stderr)
            else:
                entries[iid] = src
        else:
            print(f"arcimg: skipping {src}: no such file or directory",
                  file=sys.stderr)
    return entries


def _mode_aspect(dims) -> bool:
    """True when width:height matches a band mode's aspect at ANY scale:
    320x72 is 40:9 (mode 9) and 320x96 is 10:3 (mode 12). High-resolution
    masters are welcome (interpreters scale; 320 is the reference
    resolution, not a ceiling), as long as the shape is a band shape."""
    w, h = dims
    return w * 9 == h * 40 or w * 3 == h * 10


# The arc_image declaration chunk carried by every Blorb arcimg writes
# (docs/08). Chris Spiegel's request, ruled mandatory: an interpreter reads
# it before running a byte and knows up front whether to reserve a picture
# band, and its ABSENCE is meaningful (this Blorb promises no arc_image
# graphics). Two bytes: the extension version, and the band mode (9 or 12,
# or 0 when the art declares none, in which case the opcode operand governs
# as always).
ARCI_CHUNK = b"ARCI"
ARCI_VERSION = 1


def _declared_mode(entries: dict) -> int:
    """The band mode to declare in the ARCI chunk: the first picture whose
    shape matches a standard mode. 0 when none does, meaning "not declared,
    read the opcode operand" (Part A keeps the operand authoritative, so a
    game that ever mixed modes still renders correctly)."""
    for iid in sorted(entries):
        name = _mode_of(_png_size(entries[iid]))
        if name is not None:
            return MODES[name][1] // 8  # the band in text rows: 9 or 12
    return 0


def build_blorb(entries: dict, story_path=None) -> bytes:
    """A Blorb (IFF FORM/IFRS) holding the numbered pictures as 'Pict'
    resources, resource number = the arc_image id, each a 'PNG ' chunk with
    the master bytes verbatim. With story_path, the story rides along as
    Exec 0 in a 'ZCOD' chunk: the .zblorb shape Gargoyle-family
    interpreters open directly. Blorb has no filenames inside; resources
    ARE numbers, which is exactly the arc_image model, so draw_image id N
    maps to Pict N with no translation anywhere.

    Every Blorb written here carries the ARCI declaration chunk (above),
    which is mandatory by ruling: a Blorb without it makes no arc_image
    promise."""
    chunks = []  # (chunk type, payload, usage, resource number)
    if story_path is not None:
        with open(story_path, "rb") as fh:
            chunks.append((b"ZCOD", fh.read(), b"Exec", 0))
    for iid in sorted(entries):
        with open(entries[iid], "rb") as fh:
            chunks.append((b"PNG ", fh.read(), b"Pict", iid))
    n = len(chunks)
    ridx_len = 4 + n * 12
    # The declaration chunk sits between the index and the resources. Its
    # whole size counts into the resource offsets below: RIdx entries are
    # ABSOLUTE file positions, so anything inserted ahead of the resources
    # must be in this sum or every pointer is silently wrong.
    arci = ARCI_CHUNK + struct.pack(">I", 2) + bytes(
        (ARCI_VERSION, _declared_mode(entries)))
    # Offsets are absolute file positions of each resource chunk's type
    # field: the 12-byte FORM header, the RIdx chunk (8 + payload, padded to
    # even), the ARCI chunk, then the resources in file order.
    pos = 12 + 8 + ridx_len + (ridx_len & 1) + len(arci)
    index = bytearray(struct.pack(">I", n))
    body = bytearray()
    for ctype, data, usage, num in chunks:
        index += usage + struct.pack(">II", num, pos)
        body += ctype + struct.pack(">I", len(data)) + data
        if len(data) & 1:
            body += b"\0"
        pos += 8 + len(data) + (len(data) & 1)
    inner = (b"IFRS" + b"RIdx" + struct.pack(">I", ridx_len) + bytes(index)
             + (b"\0" if ridx_len & 1 else b"") + arci + bytes(body))
    return b"FORM" + struct.pack(">I", len(inner)) + inner


def cmd_pack(args) -> int:
    entries = _collect_numbered(args.sources)
    if not entries:
        print("arcimg: no <number>.png files to pack", file=sys.stderr)
        return 2

    # Validate every entry is a real PNG. Any size at a band mode's aspect
    # ratio is fine (high-resolution masters scale on the interpreter side);
    # a shape that matches no mode gets a note (allowed, usually a mistake).
    for iid in sorted(entries):
        dims = _png_size(entries[iid])
        if dims is None:
            print(f"arcimg: {entries[iid]} is not a valid PNG", file=sys.stderr)
            return 2
        if _mode_of(dims) is None and not _mode_aspect(dims):
            print(f"arcimg: note: {os.path.basename(entries[iid])} is "
                  f"{dims[0]}x{dims[1]}, neither a standard mode size "
                  f"({_modes_str()}) nor a band aspect (40:9 or 10:3)")

    # The .arcres zip was retired (Stefan's ruling, 2026-07-31): the Blorb
    # is the one pack, readable by Actaea, the Gargoyle family, and the
    # proteus web builder alike. Refuse the old extension loudly instead
    # of writing a Blorb under a lying name.
    if args.out.lower().endswith(".arcres"):
        print("arcimg: the .arcres format was retired; pack writes a Blorb "
              "(use -o <name>.blorb, or --zblorb STORY -o <name>.zblorb)",
              file=sys.stderr)
        return 2

    zstory = getattr(args, "zblorb", None)
    if zstory is None and args.out.lower().endswith(".zblorb"):
        print("arcimg: a .zblorb embeds the story, so the story file is "
              "required: arcimg pack ... --zblorb STORY -o "
              f"{os.path.basename(args.out)}", file=sys.stderr)
        return 2
    if zstory is not None:
        if not os.path.isfile(zstory):
            print(f"arcimg: no story file {zstory}", file=sys.stderr)
            return 2
        with open(zstory, "rb") as fh:
            v = fh.read(1)
        if not v or v[0] not in (5, 8):
            print(f"arcimg: {zstory} is not a z5/z8 story file",
                  file=sys.stderr)
            return 2
    try:
        with open(args.out, "wb") as fh:
            fh.write(build_blorb(entries, zstory))
    except OSError as exc:
        print(f"arcimg: cannot write {args.out}: {exc}", file=sys.stderr)
        return 2
    ids = ", ".join(str(i) for i in sorted(entries))
    kind = "zblorb (story + pictures)" if zstory else "blorb (pictures)"
    print(f"arcimg: wrote {args.out}, {kind}: {ids}")
    return 0


def _blorb_pictures(path):
    """Read a Blorb pack: ({id: png_bytes}, has_story, arci_mode) or None
    when the file is not a Blorb. The mirror of build_blorb, kept beside
    it so the two never drift."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 12 or data[:4] != b"FORM" or data[8:12] != b"IFRS":
        return None
    pictures, has_story, arci_mode = {}, False, None
    ridx = {}
    pos = 12
    while pos + 8 <= len(data):
        fourcc = data[pos:pos + 4]
        (length,) = struct.unpack(">I", data[pos + 4:pos + 8])
        payload = data[pos + 8:pos + 8 + length]
        if fourcc == b"RIdx":
            (count,) = struct.unpack(">I", payload[0:4])
            for i in range(count):
                usage, number, offset = struct.unpack(
                    ">4sII", payload[4 + 12 * i:16 + 12 * i])
                ridx[offset] = (usage, number)
        elif fourcc == b"ARCI" and length >= 2:
            arci_mode = payload[1]
        usage_num = ridx.get(pos)
        if usage_num:
            usage, number = usage_num
            if usage == b"Pict":
                pictures[number] = payload
            elif usage == b"Exec":
                has_story = True
        pos += 8 + length + (length & 1)
    return pictures, has_story, arci_mode


def cmd_info(args) -> int:
    src = args.source
    blorb = None
    if os.path.isfile(src):
        blorb = _blorb_pictures(src)
    if blorb is not None:
        pictures, has_story, arci_mode = blorb
        kind = "zblorb (story + pictures)" if has_story else "blorb (pictures)"
        mode_tag = f", mode {arci_mode}" if arci_mode else ""
        print(f"{src}: {kind}, {len(pictures)} pictures{mode_tag}")
        for iid in sorted(pictures):
            dims = _png_size_bytes(pictures[iid])
            shape = f"{dims[0]}x{dims[1]}" if dims else "?"
            mode = _mode_of(dims) if dims else None
            tag = f" ({mode} mode)" if mode else ""
            print(f"  {iid:>4}  {shape}{tag}")
        return 0

    dims = _png_size(src)
    if dims is None:
        print(f"arcimg: {src} is not a PNG or a Blorb pack", file=sys.stderr)
        return 2
    mode = _mode_of(dims)
    tag = f" ({mode} mode)" if mode else " (not a standard mode size)"
    print(f"{src}: {dims[0]}x{dims[1]}{tag}")
    return 0


_CODEC_NAMES = {"rle": CODEC_RLE, "zx0": CODEC_ZX0, "lzsa2": CODEC_LZSA2}


def _is_hand_authored(dest):
    """Header byte 15 of an existing .arc: 1 means an author's own native
    edit came back through `arcimg unscr` and conversion must not touch it."""
    if not os.path.exists(dest):
        return False
    with open(dest, "rb") as f:
        head = f.read(16)
    return len(head) == 16 and head[:4] == ARC_MAGIC and head[15] == 1


def _native_filename(iid: int, tag: str) -> str:
    """The on-disk name of a native conversion. Every target ships
    <id>.<TAG> except the TRS-80 Model 4: TRSDOS caps a suffix at three
    characters and a filename must begin with a letter (Shawn
    Sijnstra's report, 2026-07-25), so the Model 4 ships ARC<id>.TR4.
    The .arc header id stays authoritative either way (part B), so no
    interpreter or packer logic changes with the name."""
    if tag == "TRSM4":
        return f"ARC{iid}.TR4"
    return f"{iid}.{tag}"


def _convert_stale(master, dest, preview):
    """make-style currency: the output stands if it is newer than the
    master, its hint sidecar (if any), and this tool itself."""
    outs = [dest] + ([preview] if preview else [])
    if not all(os.path.exists(o) for o in outs):
        return True
    deps = [master, os.path.abspath(__file__)]
    hint = os.path.splitext(master)[0] + ".hint"
    if os.path.exists(hint):
        deps.append(hint)
    newest_dep = max(os.path.getmtime(d) for d in deps)
    return min(os.path.getmtime(o) for o in outs) < newest_dep


def _convert_job(job):
    """One picture, start to finish; module-level so worker processes can
    reach it. Returns (iid, dest, size, mode) or an error string."""
    iid, path, tag, dest, preview, codec, c64src = job
    try:
        # c64src is accepted for call compatibility and ignored: the A8
        # converts DIRECT from the master (Stefan's ruling and corpus
        # approval, 2026-07-24); the hand-polish loop for the A8 is a
        # hand-authored .A8, like every other target.
        mode, native = convert_master(path, tag)
        blob = encode_native(tag, mode, iid, native, codec)
    except (ValueError, RuntimeError) as exc:
        return f"{path}: {exc}"
    with open(dest, "wb") as f:
        f.write(blob)
    if preview:
        render_arc(blob, preview)
    return (iid, dest, len(blob), mode)


def cmd_convert(args) -> int:
    tag = args.target.upper()
    entries = _collect_numbered(args.sources)
    if not entries:
        print("arcimg: no <number>.png masters to convert", file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)
    if args.preview:
        os.makedirs(args.preview, exist_ok=True)
    codec = _CODEC_NAMES[args.codec] if args.codec else None
    jobs = []
    skipped = 0
    for iid in sorted(entries):
        dest = os.path.join(args.out, _native_filename(iid, tag))
        preview = os.path.join(args.preview, f"{iid}-{tag}.png") \
            if args.preview else None
        if _is_hand_authored(dest):
            # An author's own edit (arcimg unscr) always wins; even --force
            # respects it. Delete the file to reconvert from the master.
            print(f"arcimg: {dest} is hand-authored, keeping it")
            skipped += 1
            continue
        if not args.force and not _convert_stale(entries[iid], dest, preview):
            skipped += 1
            continue
        c64src = None
        if tag == "A8":
            # Hand-polish inheritance (Stefan's ruling): when the author's
            # own .C64 edit exists, it is the source of the 8-bit family's
            # taste and the A8 derives from it; one polish pass, every
            # sibling benefits. Default location: the c64 directory beside
            # this target's output directory (the portfolio layout).
            c64dir = args.c64 or os.path.join(
                os.path.dirname(os.path.abspath(args.out)), "c64")
            cand = os.path.join(c64dir, f"{iid}.C64")
            if _is_hand_authored(cand):
                c64src = cand
                print(f"arcimg: {dest} inherits the hand-authored {cand}")
        jobs.append((iid, entries[iid], tag, dest, preview, codec, c64src))
    if len(jobs) > 1 and not args.serial:
        # The packers dominate the wall clock (ZX0's optimal parse above
        # all); pictures are independent, so they convert in parallel.
        import multiprocessing
        with multiprocessing.Pool() as pool:
            results = pool.map(_convert_job, jobs)
    else:
        results = [_convert_job(j) for j in jobs]
    total = 0
    for res in results:
        if isinstance(res, str):
            print(f"arcimg: {res}", file=sys.stderr)
            return 2
        _iid, dest, size, mode = res
        total += size
        print(f"arcimg: wrote {dest} ({size} bytes, mode {mode})")
    note = f", {skipped} current (skipped)" if skipped else ""
    print(f"arcimg: {len(jobs)} pictures, {total} bytes total{note}")
    return 0


def cmd_scr(args) -> int:
    src = args.source
    if src.lower().endswith(".png"):
        try:
            _mode, native = convert_master(src, "ZX3")
        except ValueError as exc:
            print(f"arcimg: {exc}", file=sys.stderr)
            return 2
    else:
        with open(src, "rb") as f:
            blob = f.read()
        try:
            tag, _mode, _iid, native = decode_arc(blob)
        except ValueError as exc:
            print(f"arcimg: {exc}", file=sys.stderr)
            return 2
        if tag != "ZX3":
            print(f"arcimg: {src} is a {tag} image, scr wants ZX3",
                  file=sys.stderr)
            return 2
    with open(args.out, "wb") as f:
        f.write(scr_from_native(native))
    print(f"arcimg: wrote {args.out} (6912 bytes, {native['h']}-row band, "
          f"black bar below)")
    return 0


def _detect_scr_mode(data: bytes) -> int:
    """Which band does this .scr carry? A 9-row export's rows 72..96 are
    part of the black bar (bitmap clear, attrs 0), so if that stripe is
    empty the band is 9 rows, otherwise 12. --mode overrides, for the
    rare hand image whose rows 72..96 are genuinely all black-on-black."""
    for y in range(72, 96):
        for xb in range(32):
            if data[_scr_bitmap_offset(y, xb)]:
                return 12
    if any(data[6144 + cy * 32 + cx] for cy in range(9, 12)
           for cx in range(32)):
        return 12
    return 9


def cmd_unscr(args) -> int:
    with open(args.source, "rb") as f:
        data = f.read()
    if len(data) != 6912:
        print(f"arcimg: a .scr is 6912 bytes, this is {len(data)}",
              file=sys.stderr)
        return 2
    mode = args.mode
    if mode is None:
        mode = _detect_scr_mode(data)
        print(f"arcimg: detected a {mode * 8}-row band (mode {mode}); "
              f"pass --mode to override")
    try:
        native, warnings = native_from_scr(data, mode)
    except ValueError as exc:
        print(f"arcimg: {exc}", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"arcimg: note: {warning}")
    os.makedirs(args.out, exist_ok=True)
    blob = encode_native("ZX3", mode, args.id, native, hand=True)
    dest = os.path.join(args.out, f"{args.id}.ZX3")
    with open(dest, "wb") as f:
        f.write(blob)
    print(f"arcimg: wrote {dest} ({len(blob)} bytes, hand-authored: "
          f"convert will keep it)")
    if args.preview:
        os.makedirs(args.preview, exist_ok=True)
        p = os.path.join(args.preview, f"{args.id}-ZX3.png")
        render_arc(blob, p)
        print(f"arcimg: wrote {p}")
    return 0


def cmd_targets(args) -> int:
    print("retro targets (arc_image/reference/design.md; conversion back-ends land per wave):")
    for tag in sorted(TARGETS, key=lambda t: TARGETS[t].id):
        t = TARGETS[tag]
        print(f"  {t.id:>3}  {t.tag:<4} {t.width}x72 / {t.width}x96")
    return 0


def cmd_slice9(args) -> int:
    """Mode 9 as the TOP SLICE of a mode-12 native: same bytes for every
    shared row BY CONSTRUCTION (Stefan's ruling, 2026-07-25: a mode 9
    that is a different version of the picture is a quality issue; the
    P4 probe measured its independently-converted test pair electing
    the same globals in opposite roles and brighter cell pairs). No
    second conversion happens, so nothing can diverge."""
    blob = open(args.source, "rb").read()
    head, _secs = read_arc(blob)
    if head["mode"] != 12:
        print("arcimg: slice9 wants a mode-12 .arc", file=sys.stderr)
        return 2
    tag = next(t.tag for t in TARGETS.values() if t.id == head["target"])
    t = TARGETS[tag]
    tup = decode_arc(blob)
    native = next(x for x in tup if isinstance(x, dict) and "w" in x)
    h9 = (head["height"] * 9 + 5) // 12   # 96 -> 72, 200-row family safe
    out = dict(native)
    out["h"] = h9
    # Every per-row and per-cell plane a target keeps must shrink with the
    # band, or the slice smuggles mode-12 bytes below row 72 (the ZX3 probe
    # caught exactly that: 96 leftover attribute bytes decoded into the
    # interpreter's text rows). Non-plane keys (palette, regs) carry over.
    for plane in ("pixels", "pattern", "colors", "hibits"):
        if plane in native:                 # one entry per pixel row
            out[plane] = [row[:] for row in native[plane][:h9]]
    if "screen" in native:                  # C64 family: per 4x8 cell
        cells = (native["w"] // 4) * (h9 // 8)
        out["screen"] = list(native["screen"][:cells])
        out["color"] = list(native["color"][:cells])
    if "attrs" in native:                   # Spectrum: per 8x8 cell
        out["attrs"] = list(native["attrs"][:(native["w"] // 8) * (h9 // 8)])
    if "lines" in native:
        out["lines"] = list(native["lines"][:h9 * 4])
    blob9 = write_arc(head["target"], 9, head["width"], h9,
                      args.id if args.id is not None else head["id"],
                      t.pack(out), codec=head["codec"], hand=head["hand"])
    open(args.out, "wb").write(blob9)
    print(f"arcimg: wrote {args.out} (mode 9 slice of {args.source})")
    return 0


def cmd_render(args) -> int:
    try:
        with open(args.source, "rb") as f:
            blob = f.read()
        render_arc(blob, args.out)
    except (OSError, ValueError) as exc:
        print(f"arcimg: {exc}", file=sys.stderr)
        return 2
    print(f"arcimg: rendered {args.source} to {args.out}")
    return 0


class _Version(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(_version_text() + "\n")
        parser.exit()


class _Parser(argparse.ArgumentParser):
    """An ArgumentParser whose help leads with the banner, so `-h` (and each
    subcommand's `-h`) shows the identity block the way every other invocation
    does. Subparsers inherit this class, so `arcimg pack -h` gets it too."""

    def format_help(self) -> str:
        # A trailing blank line too, so help ends with the same whitespace before
        # the prompt that command output does.
        return f"{_banner()}\n\n{super().format_help()}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(
        prog="arcimg",
        description="Prepare and pack arc_image pictures for Arcturus stories.",
    )
    ap.add_argument("--version", action=_Version, nargs=0,
                    help="show the version banner and exit")
    sub = ap.add_subparsers(dest="command")

    p_pack = sub.add_parser(
        "pack", help="pack numbered PNGs into a Blorb")
    p_pack.add_argument("sources", nargs="+",
                        help="directories and/or <number>.png files")
    p_pack.add_argument("-o", "--out", required=True,
                        help="the pack to write (.blorb, or .zblorb with "
                        "--zblorb)")
    p_pack.add_argument("--zblorb", metavar="STORY",
                        help="embed STORY (.z5/.z8) as Exec 0 beside the "
                        "pictures: one file that carries the whole game")
    p_pack.set_defaults(func=cmd_pack)

    p_prep = sub.add_parser(
        "prep", help="size a source image to a mode and number it")
    p_prep.add_argument("source", help="the source image (PNG, or any format "
                        "Pillow reads)")
    p_prep.add_argument("--id", type=int, required=True,
                        help="the picture id (the resource slot); output is "
                        "<id>.png")
    p_prep.add_argument("--mode", choices=sorted(MODES), default="daad",
                        help="the picture shape (default: daad)")
    p_prep.add_argument("-o", "--out", help="output directory (default: .)")
    p_prep.set_defaults(func=cmd_prep)

    p_info = sub.add_parser(
        "info", help="report a PNG's size or list a pack's pictures")
    p_info.add_argument("source", help="a PNG file or a Blorb pack")
    p_info.set_defaults(func=cmd_info)

    p_targets = sub.add_parser(
        "targets", help="list the retro targets (arc_image/reference/design.md)")
    p_targets.set_defaults(func=cmd_targets)

    p_conv = sub.add_parser(
        "convert", help="convert band-shaped masters to a retro target",
        epilog="A master with a bright celestial disc (a moon, a sun) may "
               "carry a hint sidecar beside it, 8.hint next to 8.png, one "
               "line of JSON: {\"salient\": [[cx, cy, r]]} naming the disc "
               "in pixel coordinates. Every target then keeps the disc "
               "visible on palettes that would otherwise lose it.")
    p_conv.add_argument("sources", nargs="+",
                        help="directories and/or <number>.png masters")
    p_conv.add_argument("--target", required=True,
                        help="the target tag (AMI, AST, DOS, ...)")
    p_conv.add_argument("-o", "--out", required=True,
                        help="output directory for the <id>.<TAG> files")
    p_conv.add_argument("--preview",
                        help="also render each result to PNG in this directory")
    p_conv.add_argument("--codec", choices=sorted(_CODEC_NAMES),
                        help="override the target's codec (default: LZSA2 on "
                             "the 16-bit trio, ZX0 elsewhere)")
    p_conv.add_argument("--c64",
                        help="directory holding <id>.C64 files; a "
                             "hand-authored one becomes the A8's source "
                             "(default: the c64 directory beside --out)")
    p_conv.add_argument("--force", action="store_true",
                        help="reconvert even when outputs are current")
    p_conv.add_argument("--serial", action="store_true",
                        help="convert one picture at a time (no worker pool)")
    p_conv.set_defaults(func=cmd_convert)

    p_slice = sub.add_parser(
        "slice9", help="derive a mode-9 .arc as the top slice of a "
                       "mode-12 .arc (same picture, same bytes for "
                       "every shared row)")
    p_slice.add_argument("source", help="a mode-12 .arc file")
    p_slice.add_argument("--id", type=int, default=None,
                         help="picture id for the slice (default: keep)")
    p_slice.add_argument("-o", "--out", required=True,
                         help="the mode-9 .arc to write")
    p_slice.set_defaults(func=cmd_slice9)

    p_render = sub.add_parser(
        "render", help="render a .arc image to a PNG preview")
    p_render.add_argument("source", help="a .arc file")
    p_render.add_argument("-o", "--out", required=True,
                          help="the PNG to write")
    p_render.set_defaults(func=cmd_render)

    p_scr = sub.add_parser(
        "scr", help="write a Spectrum conversion as a standard .scr for "
                    "hand polish (band on top, black bar below)")
    p_scr.add_argument("source",
                       help="a <id>.ZX3 file, or a master PNG to convert")
    p_scr.add_argument("-o", "--out", required=True,
                       help="the .scr to write (6912 bytes)")
    p_scr.set_defaults(func=cmd_scr)

    p_unscr = sub.add_parser(
        "unscr", help="take a polished .scr back: strip the black bar and "
                      "return it to the portfolio as <id>.ZX3 "
                      "(hand-authored; convert will never overwrite it)")
    p_unscr.add_argument("source", help="the polished .scr")
    p_unscr.add_argument("--id", type=int, required=True,
                         help="the image id it belongs to")
    p_unscr.add_argument("--mode", type=int, choices=(9, 12),
                         help="band mode; detected from the file when "
                              "omitted (the black bar gives it away)")
    p_unscr.add_argument("-o", "--out", required=True,
                         help="output directory (the zx3 portfolio dir)")
    p_unscr.add_argument("--preview",
                         help="also render the result to PNG here")
    p_unscr.set_defaults(func=cmd_unscr)
    return ap


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Every invocation leads with the header, the way arcc and actaea do; no
    # command shows the banner and a usage hint.
    if args.command is None:
        print(_banner())
        print("\nType 'arcimg -h' for help.   Commands: pack, prep, info\n")
        return 0
    print(_banner() + "\n")
    rc = args.func(args)
    print()  # a blank line between the output and the prompt
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
