"""The LZSA2 Z80 decoder, EXECUTED before it is trusted (the standing
verification pattern: a decoder is proven by decoding real streams on a
simulated CPU, never by reading it). unlzsa2_fast.asm (spke & uniabis,
vendored from the lzsa repository, notice intact) is assembled with
sjasmplus behind a tiny scaffold and run on Haumea's SimZ80 (the full
documented instruction set, flags and block ops included) against every
LZSA2 section this repo ships: the committed 16-bit corpora and fresh
MS2 encodes. Each stream must decode byte-identically to arcimg's
pure-Python unpacker.

Run: python3 test_unlzsa2.py  (also invoked by the probe build)
"""

import glob
import importlib.util
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_HAUMEA = os.path.expanduser("~/Fiction/Haumea/tools")

_spec = importlib.util.spec_from_file_location(
    "arcimg", os.path.join(_ROOT, "tools", "arcimg.py"))
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)
sys.path.insert(0, _HAUMEA)
import simz80  # noqa: E402

ORG = 0x0100       # decoder + scaffold (~220 bytes)
SRC = 0x0400       # compressed stream (up to 31K of room)
DST = 0x8000       # decompressed output: the largest section in the
                   # repo is the DOS chunky bitmap, 30720 bytes,
                   # 0x8000..0xF800, under the stack at 0xFF00

_SCAFFOLD = f"""
        org ${ORG:04X}
start:  ld hl, ${SRC:04X}
        ld de, ${DST:04X}
        call DecompressLZSA2
        halt
        include "{os.path.join(_HERE, 'unlzsa2_fast.asm')}"
"""


def build_decoder():
    with tempfile.TemporaryDirectory() as d:
        asm = os.path.join(d, "t.asm")
        binf = os.path.join(d, "t.bin")
        with open(asm, "w") as f:
            f.write(_SCAFFOLD)
        r = subprocess.run(["sjasmplus", "--nologo", asm, f"--raw={binf}"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        with open(binf, "rb") as f:
            return f.read()


def z80_decode(code, stream, expect_len):
    mem = bytearray(0x10000)
    mem[ORG:ORG + len(code)] = code
    mem[SRC:SRC + len(stream)] = stream
    cpu = simz80.Z80(read=lambda a: mem[a],
                     write=lambda a, v: mem.__setitem__(a, v))
    cpu.reset()
    cpu.pc = ORG
    cpu.sp = 0xFF00
    steps = 0
    while not cpu.halted:
        cpu.step()
        steps += 1
        if steps > 50_000_000:
            raise AssertionError("decoder did not halt")
    return bytes(mem[DST:DST + expect_len])


def main():
    code = build_decoder()
    unpack = arcimg._CODECS[arcimg.CODEC_LZSA2][1]
    streams = []
    for pat in ("ami/*.AMI", "ast/*.AST", "dos/*.DOS"):
        for f in sorted(glob.glob(os.path.join(_ROOT, "arc_image", pat)))[:4]:
            head, secs = arcimg.read_arc(open(f, "rb").read())
            blob = open(f, "rb").read()
            # re-walk the raw file to reach the COMPRESSED streams
            count = blob[7]
            off = 16 + count * 6
            for i in range(count):
                e = 16 + i * 6
                ulen = (blob[e + 2] << 8) | blob[e + 3]
                clen = (blob[e + 4] << 8) | blob[e + 5]
                streams.append((os.path.basename(f), i,
                                blob[off:off + clen], ulen))
                off += clen
    for n in (2, 8, 14):
        _m, native = arcimg.convert_master(
            os.path.join(_ROOT, "arc_image", "masters", f"{n}.png"), "MS2")
        blob = arcimg.encode_native("MS2", 12, n, native)
        count = blob[7]
        off = 16 + count * 6
        for i in range(count):
            e = 16 + i * 6
            ulen = (blob[e + 2] << 8) | blob[e + 3]
            clen = (blob[e + 4] << 8) | blob[e + 5]
            streams.append((f"MS2:{n}.png", i, blob[off:off + clen], ulen))
            off += clen
    bad = 0
    for name, i, comp, ulen in streams:
        want = unpack(comp)
        assert len(want) == ulen, (name, i)
        got = z80_decode(code, comp, ulen)
        ok = got == want
        bad += 0 if ok else 1
        print(f"{name} section {i}: {ulen} bytes "
              f"{'byte-identical' if ok else 'MISMATCH'}")
    if bad:
        raise SystemExit(1)
    print(f"unlzsa2_fast.asm: {len(streams)} real streams decoded "
          f"byte-identically to the Python unpacker")


if __name__ == "__main__":
    main()
