"""Execute the assembled MSX2 probe end to end and verify VRAM and the
palette. The CPU is Haumea's SimZ80 (the full documented instruction
set: the vendored LZSA2 decoder needs real flags and block ops), the io
map a V9938 write model: port $99 latch pairs set registers and VRAM
addresses (17-bit, R#14 the bank), port $98 writes VRAM and
auto-increments, port $9A writes palette entries through the R#16
pointer, ports $A9/$AA an idle keyboard. Execution pauses at each
`waitkey` ENTRY, the screen state is captured, waitkey is skipped by a
simulated ret; one capture per image (mode 9, then mode 12), then stop.

Expected: the band region of VRAM ($0000-$2FFF; clrband zeroes it
before each draw) equals the pair's raw bitmap section zero-padded, the
palette RAM equals the raw palette section, the display is enabled
(R#1 = $40) at every stop. Run after every reassembly, BEFORE any
emulator pass; the emulator hand-off is about pixels, not loader bugs.
"""

import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_HAUMEA = os.path.expanduser("~/Fiction/Haumea/tools")
PROBE_BIN = os.path.join(_HERE, "probe.bin")
CYCLE = ("9.MS2", "12.MS2")
ORG = 0x8400
WAITKEY = 0x8494    # from the sjasmplus listing; re-derive if probe.asm
                    # gains or loses code before the waitkey routine

_spec = importlib.util.spec_from_file_location(
    "arcimg", os.path.join(_ROOT, "tools", "arcimg.py"))
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)
sys.path.insert(0, _HAUMEA)
import simz80  # noqa: E402


def raw_sections(pair):
    blob = open(os.path.join(_HERE, pair), "rb").read()
    _head, secs = arcimg.read_arc(blob)
    return {t: raw for t, _f, raw in secs}


def run():
    code = open(PROBE_BIN, "rb").read()
    mem = bytearray(0x10000)
    mem[ORG:ORG + len(code)] = code
    vram = bytearray(0x20000)
    pal = bytearray(32)
    vdp = {"latch": None, "addr": 0, "bank": 0, "regs": [0] * 47,
           "palptr": 0}

    def io_out(port, val):
        port &= 0xFF
        if port == 0x98:
            a = (vdp["bank"] << 14) | vdp["addr"]
            vram[a & 0x1FFFF] = val
            vdp["addr"] += 1
            if vdp["addr"] == 0x4000:
                # the real V9938 increments R#14 ITSELF on a 16K
                # crossing; a later address setup that does not rewrite
                # R#14 inherits the bumped bank (measured on openMSX
                # after the first build painted into invisible VRAM)
                vdp["addr"] = 0
                vdp["bank"] = (vdp["bank"] + 1) & 7
                vdp["regs"][14] = vdp["bank"]
            vdp["latch"] = None
        elif port == 0x99:
            if vdp["latch"] is None:
                vdp["latch"] = val
            else:
                lo, hi = vdp["latch"], val
                vdp["latch"] = None
                if hi & 0x80:
                    r = hi & 0x3F
                    vdp["regs"][r] = lo
                    if r == 14:
                        vdp["bank"] = lo & 7
                    if r == 16:
                        vdp["palptr"] = (lo & 15) * 2
                else:
                    # an address setup reloads A16-A14 from R#14; only
                    # the running auto-increment carries across banks
                    vdp["addr"] = ((hi & 0x3F) << 8) | lo
                    vdp["bank"] = vdp["regs"][14] & 7
        elif port == 0x9A:
            pal[vdp["palptr"]] = val
            vdp["palptr"] = (vdp["palptr"] + 1) % 32
        elif port == 0xAA:
            pass
        else:
            raise AssertionError(f"out to unmodeled port {port:02X}")

    def io_in(port):
        port &= 0xFF
        if port == 0xA9:
            return 0xFF                             # all keys up
        if port == 0xAA:
            return 0x00
        raise AssertionError(f"in from unmodeled port {port:02X}")

    cpu = simz80.Z80(read=lambda a: mem[a],
                     write=lambda a, v: mem.__setitem__(a, v),
                     io_in=io_in, io_out=io_out)
    cpu.reset()
    cpu.pc = ORG
    cpu.sp = 0xFF00
    captures = []
    steps = 0
    while True:
        if cpu.pc == WAITKEY:
            captures.append((bytes(vram[:0x3000]), bytes(pal),
                             vdp["regs"][1]))
            if len(captures) == len(CYCLE):
                return captures
            # skip waitkey: simulate its ret
            cpu.pc = mem[cpu.sp] | (mem[cpu.sp + 1] << 8)
            cpu.sp = (cpu.sp + 2) & 0xFFFF
            continue
        cpu.step()
        steps += 1
        if steps > 100_000_000:
            raise AssertionError("probe did not reach waitkey (runaway)")


def main():
    frames = run()
    ok = True
    for pair, (band, got_pal, r1) in zip(CYCLE, frames):
        secs = raw_sections(pair)
        exp_band = secs[1] + bytes(0x3000 - len(secs[1]))
        exp_pal = secs[5]
        if r1 != 0x40:
            print(f"{pair}: display register R#1 is {r1:02X}, want 40")
            ok = False
        if got_pal != exp_pal:
            print(f"{pair}: palette MISMATCH")
            ok = False
        if band == exp_band:
            print(f"{pair}: VRAM band + palette byte-exact "
                  f"({sum(1 for b in band if b)} nonzero bytes)")
        else:
            bad = [i for i in range(0x3000) if band[i] != exp_band[i]]
            print(f"{pair}: {len(bad)} MISMATCHED bytes, first at "
                  f"${bad[0]:04X} (got {band[bad[0]]:02X}, "
                  f"want {exp_band[bad[0]]:02X})")
            ok = False
    if not ok:
        raise SystemExit(1)
    print("full probe simulation: PASS")


if __name__ == "__main__":
    main()
