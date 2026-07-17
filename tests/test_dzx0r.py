# test_dzx0r.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""dzx0r_z80.asm, the ring decompressor, EXECUTED. The Z80 source is
assembled with sjasmplus (skipped when the assembler is absent; it is a
dev tool like pytest itself) and run on a deliberately tiny Z80 core that
implements exactly the opcodes the decoder uses and raises on anything
else. Every stream arcimg packs must decode byte-identically to
zx0_decompress through the 2K ring and the emit vector, on real corpus
sections and on the synthetic edges (offset exactly 2048, overlapping
runs, long literals, the repeat-offset path). This is the proof that the
probe hand-off to the emulator is about pixels, not decoder bugs."""

import glob
import importlib.util
import os
import shutil
import subprocess

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ARCIMG = os.path.join(_ROOT, "tools", "arcimg.py")
_spec = importlib.util.spec_from_file_location("arcimg_dzx0r", _ARCIMG)
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)

_SJASM = shutil.which("sjasmplus")

ORG = 0x8000          # scaffold + decoder
SRC = 0x4000          # compressed stream (16K of room)
OUT = 0x6000          # emit appends here (8K of room, band max is 7680)
RING = 0x9000         # 2K-aligned ring

EPTR = ORG + 7        # dw right after the 7 fixed bytes of ld/call/halt

_SCAFFOLD = f"""
        org ${ORG:04X}
start:  ld hl, ${SRC:04X}
        call dzx0r
        halt
eptr:   dw ${OUT:04X}
emit:   push hl
        ld hl, (eptr)
        ld (hl), a
        inc hl
        ld (eptr), hl
        pop hl
        ret
        include "{os.path.join(_ROOT, 'arc_image', 'probes', 'dzx0r_z80.asm')}"
        org ${RING:04X}
zx0ring: ds 2048
"""


@pytest.fixture(scope="module")
def decoder_bin(tmp_path_factory):
    if not _SJASM:
        pytest.skip("sjasmplus not installed")
    d = tmp_path_factory.mktemp("dzx0r")
    asm = d / "t.asm"
    binf = d / "t.bin"
    asm.write_text(_SCAFFOLD)
    r = subprocess.run([_SJASM, "--nologo", str(asm), f"--raw={binf}"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return binf.read_bytes()


class Z80Halt(Exception):
    pass


def run_dzx0r(code, stream):
    """A strict, tiny Z80: exactly the opcodes dzx0r and the scaffold use.
    Anything else raises, so a decoder edit that grows the opcode set
    fails loudly here instead of misbehaving silently."""
    m = bytearray(0x10000)
    m[ORG:ORG + len(code)] = code
    m[SRC:SRC + len(stream)] = stream
    reg = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "H": 0, "L": 0}
    st = {"PC": ORG, "SP": 0xFFF0, "Z": 0, "CF": 0, "steps": 0}

    def rr16(hi, lo):
        return (reg[hi] << 8) | reg[lo]

    def wr16(hi, lo, v):
        reg[hi] = (v >> 8) & 0xFF
        reg[lo] = v & 0xFF

    def fetch():
        b = m[st["PC"]]
        st["PC"] = (st["PC"] + 1) & 0xFFFF
        return b

    def fetch16():
        lo = fetch()
        return lo | (fetch() << 8)

    def push16(v):
        st["SP"] = (st["SP"] - 2) & 0xFFFF
        m[st["SP"]] = v & 0xFF
        m[(st["SP"] + 1) & 0xFFFF] = (v >> 8) & 0xFF

    def pop16():
        v = m[st["SP"]] | (m[(st["SP"] + 1) & 0xFFFF] << 8)
        st["SP"] = (st["SP"] + 2) & 0xFFFF
        return v

    def setzn(v):
        st["Z"] = 1 if v == 0 else 0

    while True:
        st["steps"] += 1
        if st["steps"] > 60_000_000:
            raise AssertionError("dzx0r did not halt (runaway decode)")
        op = fetch()
        if op == 0x76:                              # halt
            raise Z80Halt(m)
        elif op == 0x01:                            # ld bc,nn
            wr16("B", "C", fetch16())
        elif op == 0x11:                            # ld de,nn
            wr16("D", "E", fetch16())
        elif op == 0x21:                            # ld hl,nn
            wr16("H", "L", fetch16())
        elif op == 0x2A:                            # ld hl,(nn)
            a = fetch16()
            wr16("H", "L", m[a] | (m[(a + 1) & 0xFFFF] << 8))
        elif op == 0x22:                            # ld (nn),hl
            a = fetch16()
            m[a] = reg["L"]
            m[(a + 1) & 0xFFFF] = reg["H"]
        elif op == 0x0E:                            # ld c,n
            reg["C"] = fetch()
        elif op == 0x3E:                            # ld a,n
            reg["A"] = fetch()
        elif op == 0xD8:                            # ret c
            if st["CF"]:
                st["PC"] = pop16()
        elif op == 0xE6:                            # and n
            reg["A"] &= fetch()
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xF6:                            # or n
            reg["A"] |= fetch()
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xB1:                            # or c
            reg["A"] |= reg["C"]
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0x87:                            # add a,a
            v = reg["A"] << 1
            st["CF"] = 1 if v > 0xFF else 0
            reg["A"] = v & 0xFF
            setzn(reg["A"])
        elif op == 0x17:                            # rla (through carry)
            v = (reg["A"] << 1) | st["CF"]
            st["CF"] = 1 if v > 0xFF else 0
            reg["A"] = v & 0xFF                     # rla leaves Z alone
        elif op == 0x19:                            # add hl,de (C only)
            v = rr16("H", "L") + rr16("D", "E")
            st["CF"] = 1 if v > 0xFFFF else 0
            wr16("H", "L", v & 0xFFFF)
        elif op in (0x03, 0x13, 0x23):              # inc bc/de/hl (no flags)
            hi, lo = {0x03: ("B", "C"), 0x13: ("D", "E"),
                      0x23: ("H", "L")}[op]
            wr16(hi, lo, (rr16(hi, lo) + 1) & 0xFFFF)
        elif op == 0x0B:                            # dec bc (no flags)
            wr16("B", "C", (rr16("B", "C") - 1) & 0xFFFF)
        elif op == 0x0C:                            # inc c (Z, keeps C flag)
            reg["C"] = (reg["C"] + 1) & 0xFF
            setzn(reg["C"])
        elif op == 0x7E:                            # ld a,(hl)
            reg["A"] = m[rr16("H", "L")]
        elif op == 0x4E:                            # ld c,(hl)
            reg["C"] = m[rr16("H", "L")]
        elif op == 0x77:                            # ld (hl),a
            m[rr16("H", "L")] = reg["A"]
        elif op == 0x12:                            # ld (de),a
            m[rr16("D", "E")] = reg["A"]
        elif op == 0x78:                            # ld a,b
            reg["A"] = reg["B"]
        elif op == 0x7A:                            # ld a,d
            reg["A"] = reg["D"]
        elif op == 0x7C:                            # ld a,h
            reg["A"] = reg["H"]
        elif op == 0x41:                            # ld b,c
            reg["B"] = reg["C"]
        elif op == 0x57:                            # ld d,a
            reg["D"] = reg["A"]
        elif op == 0x67:                            # ld h,a
            reg["H"] = reg["A"]
        elif op in (0xC5, 0xD5, 0xE5):              # push bc/de/hl
            hi, lo = {0xC5: ("B", "C"), 0xD5: ("D", "E"),
                      0xE5: ("H", "L")}[op]
            push16(rr16(hi, lo))
        elif op == 0xF5:                            # push af
            push16((reg["A"] << 8) | (st["Z"] << 6) | st["CF"])
        elif op in (0xC1, 0xD1, 0xE1):              # pop bc/de/hl
            hi, lo = {0xC1: ("B", "C"), 0xD1: ("D", "E"),
                      0xE1: ("H", "L")}[op]
            wr16(hi, lo, pop16())
        elif op == 0xF1:                            # pop af
            v = pop16()
            reg["A"] = (v >> 8) & 0xFF
            st["Z"] = (v >> 6) & 1
            st["CF"] = v & 1
        elif op == 0xE3:                            # ex (sp),hl
            v = pop16()
            push16(rr16("H", "L"))
            wr16("H", "L", v)
        elif op == 0x18:                            # jr
            d = fetch()
            st["PC"] = (st["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        elif op in (0x20, 0x28, 0x30, 0x38):        # jr nz/z/nc/c
            d = fetch()
            take = {0x20: not st["Z"], 0x28: st["Z"],
                    0x30: not st["CF"], 0x38: st["CF"]}[op]
            if take:
                st["PC"] = (st["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        elif op == 0xCD:                            # call
            a = fetch16()
            push16(st["PC"])
            st["PC"] = a
        elif op == 0xD4:                            # call nc
            a = fetch16()
            if not st["CF"]:
                push16(st["PC"])
                st["PC"] = a
        elif op == 0xC9:                            # ret
            st["PC"] = pop16()
        elif op == 0xC8:                            # ret z
            if st["Z"]:
                st["PC"] = pop16()
        elif op == 0xCB:                            # rotate group
            sub = fetch()
            tgt = {0x10: "B", 0x11: "C", 0x18: "B", 0x19: "C"}.get(sub)
            if tgt is None:
                raise AssertionError(f"unimplemented CB {sub:02X}")
            if sub in (0x10, 0x11):                 # rl r (through carry)
                v = (reg[tgt] << 1) | st["CF"]
                st["CF"] = 1 if v > 0xFF else 0
                reg[tgt] = v & 0xFF
            else:                                   # rr r (through carry)
                v = reg[tgt] | (st["CF"] << 8)
                st["CF"] = v & 1
                reg[tgt] = v >> 1
            setzn(reg[tgt])
        else:
            raise AssertionError(
                f"unimplemented opcode {op:02X} at {st['PC'] - 1:04X}")


def ring_decode(code, stream):
    """Run the assembled decoder on the mini core, return the emitted bytes."""
    try:
        run_dzx0r(code, stream)
    except Z80Halt as h:
        m = h.args[0]
        end = m[EPTR] | (m[EPTR + 1] << 8)
        return bytes(m[OUT:end])
    raise AssertionError("decoder never halted")


def test_corpus_sections_decode_through_the_ring(decoder_bin):
    files = (sorted(glob.glob(os.path.join(_ROOT, "arc_image/cpc/*.CPC")))[:2]
             + sorted(glob.glob(os.path.join(_ROOT, "arc_image/c64/*.C64")))[:2]
             + sorted(glob.glob(os.path.join(_ROOT, "arc_image/zx3/*.ZX3")))[:2])
    assert files, "no corpus files found"
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
    assert checked >= 6


def test_edge_offset_exactly_2048(decoder_bin):
    import random
    rnd = random.Random(11)
    block = bytes(rnd.randrange(256) for _ in range(300))
    raw = block + bytes(rnd.randrange(256) for _ in range(2048 - 300)) + block
    packed = arcimg.zx0_compress(raw)
    assert arcimg.zx0_decompress(packed) == raw
    assert ring_decode(decoder_bin, packed) == raw


def test_edge_overlapping_run_and_long_literals(decoder_bin):
    import random
    rnd = random.Random(12)
    raw = (b"\x7F" * 700                      # run fill: offset 1, len 699
           + bytes(rnd.randrange(256) for _ in range(600))  # long literals
           + b"\x7F" * 100)                   # repeat-offset path again
    packed = arcimg.zx0_compress(raw)
    assert arcimg.zx0_decompress(packed) == raw
    assert ring_decode(decoder_bin, packed) == raw


def test_edge_tiny_inputs(decoder_bin):
    for raw in (b"A", b"AB", b"AAAA", bytes(range(64))):
        packed = arcimg.zx0_compress(raw)
        assert ring_decode(decoder_bin, packed) == raw
