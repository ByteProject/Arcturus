# test_dzx0r6502.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""dzx0r_6502.asm, the 6502 ring decompressor, EXECUTED. Assembled with
ACME from ~/FictionTools on the orb Debian machine (its intended home;
skipped when `orb` or acme is unreachable) and run on a deliberately tiny
6502 core that implements exactly the opcodes the decoder uses and raises
on anything else. The same battery as the Z80 twin: real corpus sections,
the offset-exactly-2048 edge, overlapping runs, long literals, tiny
inputs, all byte-identical to zx0_decompress through the 2K ring."""

import glob
import importlib.util
import os
import shutil
import subprocess

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ARCIMG = os.path.join(_ROOT, "tools", "arcimg.py")
_spec = importlib.util.spec_from_file_location("arcimg_dzx0r6502", _ARCIMG)
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)

_ORB = shutil.which("orb")

ORG = 0x8000          # scaffold + decoder
SRC = 0x4000          # compressed stream
OUT = 0x6000          # emit appends here
RING = 0x9000         # 2K-aligned ring
EPTR = 0x20           # scaffold zp: output cursor (2 cells)

_SCAFFOLD = f"""
!cpu 6510
* = ${ORG:04X}
start:  lda #<myemit
        sta zr_emit+1
        lda #>myemit
        sta zr_emit+2
        lda #${OUT >> 8:02X}
        sta ${EPTR + 1:02X}
        lda #0
        sta ${EPTR:02X}
        ldx #<${SRC:04X}
        lda #>${SRC:04X}
        jsr dzx0r
        brk
myemit: ldy #0
        sta (${EPTR:02X}),y
        inc ${EPTR:02X}
        bne +
        inc ${EPTR + 1:02X}
+       rts
!source "{os.path.join(_ROOT, 'arc_image', 'probes', 'c64', 'dzx0r_6502.asm')}"
* = ${RING:04X}
zx0ring: !fill 2048, 0
"""


@pytest.fixture(scope="module")
def decoder_bin(tmp_path_factory):
    if not _ORB:
        pytest.skip("orb (OrbStack CLI) not available")
    d = tmp_path_factory.mktemp("dzx0r6502")
    asm = d / "t.asm"
    binf = d / "t.bin"
    asm.write_text(_SCAFFOLD)
    r = subprocess.run(
        ["orb", "-m", "debian", "bash", "-c",
         f"~/FictionTools/acme -f plain -o '{binf}' '{asm}'"],
        capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip(f"acme unreachable or failed: {r.stderr[:200]}")
    return binf.read_bytes()


class Halt(Exception):
    pass


def run_6502(code, stream):
    """A strict, tiny 6502: exactly the opcodes the decoder and scaffold
    use; anything else raises."""
    m = bytearray(0x10000)
    m[ORG:ORG + len(code)] = code
    m[SRC:SRC + len(stream)] = stream
    r = {"A": 0, "X": 0, "Y": 0, "SP": 0xFF, "PC": ORG, "C": 0, "Z": 0, "N": 0}
    steps = 0

    def fetch():
        b = m[r["PC"]]
        r["PC"] = (r["PC"] + 1) & 0xFFFF
        return b

    def fetch16():
        lo = fetch()
        return lo | (fetch() << 8)

    def push(v):
        m[0x100 + r["SP"]] = v & 0xFF
        r["SP"] = (r["SP"] - 1) & 0xFF

    def pop():
        r["SP"] = (r["SP"] + 1) & 0xFF
        return m[0x100 + r["SP"]]

    def setnz(v):
        r["Z"] = 1 if v == 0 else 0
        r["N"] = 1 if v & 0x80 else 0

    def zpiy(zp):
        base = m[zp] | (m[(zp + 1) & 0xFF] << 8)
        return (base + r["Y"]) & 0xFFFF

    while True:
        steps += 1
        if steps > 80_000_000:
            raise AssertionError("dzx0r_6502 did not halt (runaway)")
        op = fetch()
        if op == 0x00:                               # brk
            raise Halt(m)
        elif op == 0xA9: r["A"] = fetch(); setnz(r["A"])          # lda #
        elif op == 0xA5: r["A"] = m[fetch()]; setnz(r["A"])       # lda zp
        elif op == 0xB1: r["A"] = m[zpiy(fetch())]; setnz(r["A"]) # lda (zp),y
        elif op == 0x85: m[fetch()] = r["A"]                      # sta zp
        elif op == 0x91: m[zpiy(fetch())] = r["A"]                # sta (zp),y
        elif op == 0x8D: m[fetch16()] = r["A"]                    # sta abs
        elif op == 0xA2: r["X"] = fetch(); setnz(r["X"])          # ldx #
        elif op == 0xA0: r["Y"] = fetch(); setnz(r["Y"])          # ldy #
        elif op == 0x86: m[fetch()] = r["X"]                      # stx zp
        elif op == 0xE6:                                          # inc zp
            a = fetch(); m[a] = (m[a] + 1) & 0xFF; setnz(m[a])
        elif op == 0xC6:                                          # dec zp
            a = fetch(); m[a] = (m[a] - 1) & 0xFF; setnz(m[a])
        elif op == 0x06:                                          # asl zp
            a = fetch(); v = m[a] << 1
            r["C"] = 1 if v > 0xFF else 0
            m[a] = v & 0xFF; setnz(m[a])
        elif op == 0x2A:                                          # rol a
            v = (r["A"] << 1) | r["C"]
            r["C"] = 1 if v > 0xFF else 0
            r["A"] = v & 0xFF; setnz(r["A"])
        elif op == 0x26:                                          # rol zp
            a = fetch(); v = (m[a] << 1) | r["C"]
            r["C"] = 1 if v > 0xFF else 0
            m[a] = v & 0xFF; setnz(m[a])
        elif op == 0x66:                                          # ror zp
            a = fetch(); v = m[a] | (r["C"] << 8)
            r["C"] = v & 1
            m[a] = v >> 1; setnz(m[a])
        elif op == 0x29: r["A"] &= fetch(); setnz(r["A"])         # and #
        elif op == 0x09: r["A"] |= fetch(); setnz(r["A"])         # ora #
        elif op == 0x05: r["A"] |= m[fetch()]; setnz(r["A"])      # ora zp
        elif op == 0x65:                                          # adc zp
            v = r["A"] + m[fetch()] + r["C"]
            r["C"] = 1 if v > 0xFF else 0
            r["A"] = v & 0xFF; setnz(r["A"])
        elif op == 0x69:                                          # adc #
            v = r["A"] + fetch() + r["C"]
            r["C"] = 1 if v > 0xFF else 0
            r["A"] = v & 0xFF; setnz(r["A"])
        elif op == 0x18: r["C"] = 0                               # clc
        elif op == 0x38: r["C"] = 1                               # sec
        elif op == 0x48: push(r["A"])                             # pha
        elif op == 0x68: r["A"] = pop(); setnz(r["A"])            # pla
        elif op == 0x20:                                          # jsr
            a = fetch16()
            push((r["PC"] - 1) >> 8)
            push((r["PC"] - 1) & 0xFF)
            r["PC"] = a
        elif op == 0x60:                                          # rts
            lo = pop(); hi = pop()
            r["PC"] = ((hi << 8) | lo) + 1 & 0xFFFF
        elif op == 0x4C: r["PC"] = fetch16()                      # jmp abs
        elif op in (0xD0, 0xF0, 0xB0, 0x90, 0x10, 0x30):          # branches
            d = fetch()
            take = {0xD0: not r["Z"], 0xF0: r["Z"],
                    0xB0: r["C"], 0x90: not r["C"],
                    0x10: not r["N"], 0x30: r["N"]}[op]
            if take:
                r["PC"] = (r["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        else:
            raise AssertionError(f"unimplemented opcode {op:02X} at {r['PC'] - 1:04X}")


def ring_decode(code, stream):
    try:
        run_6502(code, stream)
    except Halt as h:
        m = h.args[0]
        end = m[EPTR] | (m[EPTR + 1] << 8)
        return bytes(m[OUT:end])
    raise AssertionError("decoder never halted")


def test_corpus_sections_decode_through_the_ring(decoder_bin):
    files = (sorted(glob.glob(os.path.join(_ROOT, "arc_image/c64/*.C64")))[:2]
             + sorted(glob.glob(os.path.join(_ROOT, "arc_image/probes/c64/*.C64"))))
    assert files
    checked = 0
    for p in files:
        with open(p, "rb") as f:
            blob = f.read()
        head, sections = arcimg.read_arc(blob)
        for stype, flags, raw in sections:
            if not raw or len(raw) > 0x2000:
                continue
            packed = arcimg.zx0_compress(raw)
            assert ring_decode(decoder_bin, packed) == raw, (
                f"{os.path.basename(p)} section type {stype} mismatched")
            checked += 1
    assert checked >= 8


def test_edge_offset_exactly_2048(decoder_bin):
    import random
    rnd = random.Random(21)
    block = bytes(rnd.randrange(256) for _ in range(300))
    raw = block + bytes(rnd.randrange(256) for _ in range(2048 - 300)) + block
    packed = arcimg.zx0_compress(raw)
    assert arcimg.zx0_decompress(packed) == raw
    assert ring_decode(decoder_bin, packed) == raw


def test_edge_overlap_and_long_literals(decoder_bin):
    import random
    rnd = random.Random(22)
    raw = (b"\x2A" * 700
           + bytes(rnd.randrange(256) for _ in range(600))
           + b"\x2A" * 100)
    packed = arcimg.zx0_compress(raw)
    assert ring_decode(decoder_bin, packed) == raw


def test_edge_tiny_inputs(decoder_bin):
    for raw in (b"A", b"AB", b"AAAA", bytes(range(64))):
        packed = arcimg.zx0_compress(raw)
        assert ring_decode(decoder_bin, packed) == raw
