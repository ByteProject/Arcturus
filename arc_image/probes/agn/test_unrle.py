"""The probe's RLE decoder, EXECUTED before it is trusted: the unrle
routine is assembled behind a scaffold whose RST $10 vector collects
emitted bytes into memory, run on Haumea's SimZ80 against the embedded
pairs' real streams, and compared byte-for-byte with arcimg's Python
rle_decode. The emit path in the real probe is the MOS VDU write; the
decode logic is identical either way.

Run: python3 test_unrle.py  (run after every probe.asm change)
"""

import importlib.util
import os
import re
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

ORG = 0x8000       # scaffold entry (the file is contiguous from 0)
SRC = 0x1000       # compressed stream (the mode-12 pair is ~27K)


def extract_unrle():
    src = open(os.path.join(_HERE, "probe.asm")).read()
    m = re.search(r"(unrle:.*?\.copy:.*?jr unrle\n)", src, re.S)
    assert m, "unrle routine not found"
    return m.group(1)


_SCAFFOLD = f"""
        MACRO VDU           ; the probe's emit macro, rebound to the
        out ($10), a        ; host collector port for the harness
        ENDM
        org $0000
        ds ${ORG:04X} - $, 0
start:  ld hl, ${SRC:04X}
        call unrle
        halt
{{unrle}}
"""


def build():
    with tempfile.TemporaryDirectory() as d:
        asm = os.path.join(d, "t.asm")
        binf = os.path.join(d, "t.bin")
        with open(asm, "w") as f:
            f.write(_SCAFFOLD.format(unrle=extract_unrle()))
        r = subprocess.run(["sjasmplus", "--nologo", asm, f"--raw={binf}"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return open(binf, "rb").read()


def z80_unrle(code, stream, expect_len):
    mem = bytearray(0x10000)
    mem[:len(code)] = code
    mem[SRC:SRC + len(stream)] = stream
    out = bytearray()
    cpu = simz80.Z80(read=lambda a: mem[a],
                     write=lambda a, v: mem.__setitem__(a, v),
                     io_out=lambda port, v: out.append(v))
    cpu.reset()
    cpu.pc = ORG
    cpu.sp = 0x7F00
    steps = 0
    while not cpu.halted:
        cpu.step()
        steps += 1
        if steps > 30_000_000:
            raise AssertionError("unrle did not halt")
    return bytes(out)


def main():
    code = build()
    total = 0
    for pair in ("9.AGN", "12.AGN"):
        blob = open(os.path.join(_HERE, pair), "rb").read()
        count = blob[7]
        off = 16 + count * 6
        for i in range(count):
            e = 16 + i * 6
            ulen = (blob[e + 2] << 8) | blob[e + 3]
            clen = (blob[e + 4] << 8) | blob[e + 5]
            comp = blob[off:off + clen]
            off += clen
            want = arcimg.rle_decode(comp)
            assert len(want) == ulen
            got = z80_unrle(code, comp, ulen)
            ok = got == want
            total += 1
            print(f"{pair} section {i}: {ulen} bytes "
                  f"{'byte-identical' if ok else 'MISMATCH'}")
            if not ok:
                raise SystemExit(1)
    print(f"unrle: {total} real streams decoded byte-identically "
          f"to the Python decoder")


if __name__ == "__main__":
    main()
