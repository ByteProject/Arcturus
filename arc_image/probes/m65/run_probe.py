# run_probe.py - headless pre-proof of the MEGA65 arc_image probe
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.

"""Execute the assembled M65 probe end to end on a strict 6502 core (the
house manner: a common-6502 subset, anything outside it raises) under a
VIC-IV register model, and verify everything the probe claims before any
emulator runs: the full-colour character set it decoded, the formulaic
screen matrix, the palette register pages, the colour-RAM zeroing, and
the register discipline (the knock, legacy-before-precise under HOTREG,
CHR16 and full-colour bits, the row reveal).

The VIC-IV model implements exactly what the probe touches, at their
documented addresses (mega65-core iomap): the $D02F knock, the legacy
$D020/$D021/$D031 writes, HOTREG at $D05D, $D054's CHR16/FCLR bits,
LINESTEP, SCRNPTR, CHARPTR, DISPROWS at $D07B, the palette pages
$D100-$D3FF (nibble-swapped bytes stored verbatim, as the .arc carries
them), the CRAM2K window at $D030 with colour RAM behind $D800-$DFFF,
and the $D610 typing buffer. An unmodeled I/O touch is a failure.

Execution pauses at each `waitkey` ENTRY (the moment an image is
complete and revealed), the state is compared against the pair file's
own decode (arcimg's decode_arc is the oracle), and waitkey returns by
simulated ret. Two captures, mode 9 then mode 12, then stop. The
waitkey address comes from probe.sym (acme -l), never hand-derived.

Run:  python3 run_probe.py     (prints one verdict line per image)
"""

import importlib.util
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))

_spec = importlib.util.spec_from_file_location(
    "arcimg", os.path.join(_ROOT, "tools", "arcimg.py"))
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)

PROBE_PRG = os.path.join(_HERE, "probe.prg")
PROBE_SYM = os.path.join(_HERE, "probe.sym")
CYCLE = ("9.M65", "12.M65")
CHARS = 0x1640
SCREEN = 0x8E40


def _sym(name):
    for line in open(PROBE_SYM):
        m = re.match(rf"\s*{name}\s*=\s*\$([0-9A-Fa-f]+)", line)
        if m:
            return int(m.group(1), 16)
    raise SystemExit(f"run_probe: no symbol '{name}' in probe.sym")


class VicIV:
    """The register model; raises on anything the blueprint never names."""

    def __init__(self):
        self.regs = {}
        self.knock = []
        self.pal = [bytearray(256), bytearray(256), bytearray(256)]
        # boots STALE, as the metal showed ($02 wall-to-wall): only a
        # real fill may clean it
        self.colram = bytearray(b"\x02" * 2048)
        self.d030 = 0
        self.dma = {}
        self.mem = None                   # wired by the runner

    @property
    def cram2k(self):
        return self.d030 & 1

    def write(self, addr, v):
        if addr == 0xD02F:
            self.knock.append(v)
        elif addr == 0xD030:
            self.d030 = v
        elif addr in (0xD701, 0xD702):
            self.dma[addr] = v
        elif addr == 0xD705:
            self._dma_enhanced((self.dma.get(0xD702, 0) << 16)
                               | (self.dma.get(0xD701, 0) << 8) | v)
        elif 0xD100 <= addr <= 0xD3FF:
            self.pal[(addr - 0xD100) >> 8][addr & 0xFF] = v
        elif 0xD800 <= addr <= 0xDBFF:
            self.colram[addr - 0xD800] = v
        elif 0xDC00 <= addr <= 0xDFFF:
            assert self.cram2k, "second-K colour write without CRAM2K"
            self.colram[1024 + addr - 0xDC00] = v
        elif addr in (0xD020, 0xD021, 0xD031, 0xD054, 0xD058, 0xD059,
                      0xD011, 0xD05D, 0xD05E, 0xD060, 0xD061, 0xD062, 0xD063, 0xD064, 0xD065,
                      0xD068, 0xD069, 0xD06A, 0xD07B, 0xD610):
            self.regs[addr] = v
        else:
            raise AssertionError(f"unmodeled I/O write ${addr:04X}")

    def _dma_enhanced(self, list_addr):
        """Execute the one job shape the probe uses: an option list
        (dst megabyte, format), then an F018A FILL. Anything else is
        a failure, not an emulation."""
        m = self.mem
        p = list_addr & 0xFFFF            # bank 0 lists only
        dst_mb = 0
        while True:
            opt = m[p]; p += 1
            if opt == 0x00:
                break
            elif opt == 0x81:
                dst_mb = m[p]; p += 1
            elif opt == 0x0A:
                pass                      # F018A format
            else:
                raise AssertionError(f"unmodeled DMA option ${opt:02X}")
        cmd = m[p]
        count = m[p + 1] | (m[p + 2] << 8)
        fill = m[p + 3]
        dst = m[p + 6] | (m[p + 7] << 8) | ((m[p + 8] & 0x0F) << 16)
        assert cmd & 3 == 3, "not a FILL job"
        assert dst_mb == 0xFF and dst == 0x80000, \
            f"fill aimed at ${dst_mb:02X}:{dst:05X}, not colour RAM"
        self.colram[:count] = bytes([fill]) * count

    def read(self, addr):
        if addr == 0xD610:
            return 0                     # no key held
        if addr == 0xD030:
            return self.d030
        if addr in (0xD011, 0xD031, 0xD05D):
            return self.regs.get(addr, 0)
        if addr in self.regs:
            return self.regs[addr]
        raise AssertionError(f"unmodeled I/O read ${addr:04X}")


def run_cpu(mem, io, start, stop_pc):
    """A strict common-6502 subset; anything else raises."""
    r = {"A": 0, "X": 0, "Y": 0, "SP": 0xFF, "PC": start,
         "C": 0, "Z": 0, "N": 0, "V": 0}

    def rd(a):
        return io.read(a) if 0xD000 <= a <= 0xDFFF else mem[a]

    def wr(a, v):
        if 0xD000 <= a <= 0xDFFF:
            io.write(a, v & 0xFF)
        else:
            mem[a] = v & 0xFF

    def fetch():
        b = mem[r["PC"]]
        r["PC"] = (r["PC"] + 1) & 0xFFFF
        return b

    def fetch16():
        lo = fetch()
        return lo | (fetch() << 8)

    def push(v):
        mem[0x100 + r["SP"]] = v & 0xFF
        r["SP"] = (r["SP"] - 1) & 0xFF

    def pop():
        r["SP"] = (r["SP"] + 1) & 0xFF
        return mem[0x100 + r["SP"]]

    def setnz(v):
        r["Z"] = 1 if v == 0 else 0
        r["N"] = 1 if v & 0x80 else 0
        return v

    def zpiy(zp):
        return ((mem[zp] | (mem[(zp + 1) & 0xFF] << 8)) + r["Y"]) & 0xFFFF

    def adc(v):
        s = r["A"] + v + r["C"]
        r["V"] = 1 if (~(r["A"] ^ v) & (r["A"] ^ s)) & 0x80 else 0
        r["C"] = 1 if s > 0xFF else 0
        r["A"] = setnz(s & 0xFF)

    def sbc(v):
        adc(v ^ 0xFF)

    def cmp_(reg, v):
        d = (r[reg] - v) & 0x1FF
        r["C"] = 1 if r[reg] >= v else 0
        setnz((r[reg] - v) & 0xFF)

    steps = 0
    while True:
        steps += 1
        if steps > 400_000_000:
            raise AssertionError("probe did not reach waitkey (runaway)")
        if r["PC"] == stop_pc:
            return r
        op = fetch()
        # loads
        if op == 0xA9: setnz(0) ; r["A"] = setnz(fetch())
        elif op == 0xA5: r["A"] = setnz(rd(fetch()))
        elif op == 0xAD: r["A"] = setnz(rd(fetch16()))
        elif op == 0xBD: r["A"] = setnz(rd((fetch16() + r["X"]) & 0xFFFF))
        elif op == 0xB9: r["A"] = setnz(rd((fetch16() + r["Y"]) & 0xFFFF))
        elif op == 0xB1: r["A"] = setnz(rd(zpiy(fetch())))
        elif op == 0xA2: r["X"] = setnz(fetch())
        elif op == 0xA6: r["X"] = setnz(rd(fetch()))
        elif op == 0xAE: r["X"] = setnz(rd(fetch16()))
        elif op == 0xA0: r["Y"] = setnz(fetch())
        elif op == 0xA4: r["Y"] = setnz(rd(fetch()))
        elif op == 0xAC: r["Y"] = setnz(rd(fetch16()))
        # stores
        elif op == 0x85: wr(fetch(), r["A"])
        elif op == 0x8D: wr(fetch16(), r["A"])
        elif op == 0x9D: wr((fetch16() + r["X"]) & 0xFFFF, r["A"])
        elif op == 0x99: wr((fetch16() + r["Y"]) & 0xFFFF, r["A"])
        elif op == 0x91: wr(zpiy(fetch()), r["A"])
        elif op == 0x86: wr(fetch(), r["X"])
        elif op == 0x8E: wr(fetch16(), r["X"])
        elif op == 0x84: wr(fetch(), r["Y"])
        elif op == 0x8C: wr(fetch16(), r["Y"])
        # transfers, stack
        elif op == 0xAA: r["X"] = setnz(r["A"])
        elif op == 0xA8: r["Y"] = setnz(r["A"])
        elif op == 0x8A: r["A"] = setnz(r["X"])
        elif op == 0x98: r["A"] = setnz(r["Y"])
        elif op == 0x48: push(r["A"])
        elif op == 0x68: r["A"] = setnz(pop())
        # arithmetic, logic
        elif op == 0x69: adc(fetch())
        elif op == 0x65: adc(rd(fetch()))
        elif op == 0x6D: adc(rd(fetch16()))
        elif op == 0xE9: sbc(fetch())
        elif op == 0xE5: sbc(rd(fetch()))
        elif op == 0x29: r["A"] = setnz(r["A"] & fetch())
        elif op == 0x25: r["A"] = setnz(r["A"] & rd(fetch()))
        elif op == 0x2D: r["A"] = setnz(r["A"] & rd(fetch16()))
        elif op == 0x09: r["A"] = setnz(r["A"] | fetch())
        elif op == 0x05: r["A"] = setnz(r["A"] | rd(fetch()))
        elif op == 0x0D: r["A"] = setnz(r["A"] | rd(fetch16()))
        elif op == 0x49: r["A"] = setnz(r["A"] ^ fetch())
        elif op == 0x45: r["A"] = setnz(r["A"] ^ rd(fetch()))
        # compares
        elif op == 0xC9: cmp_("A", fetch())
        elif op == 0xC5: cmp_("A", rd(fetch()))
        elif op == 0xCD: cmp_("A", rd(fetch16()))
        elif op == 0xE0: cmp_("X", fetch())
        elif op == 0xE4: cmp_("X", rd(fetch()))
        elif op == 0xC0: cmp_("Y", fetch())
        elif op == 0xC4: cmp_("Y", rd(fetch()))
        # inc/dec
        elif op == 0xE6: a = fetch(); wr(a, setnz((rd(a) + 1) & 0xFF))
        elif op == 0xEE: a = fetch16(); wr(a, setnz((rd(a) + 1) & 0xFF))
        elif op == 0xC6: a = fetch(); wr(a, setnz((rd(a) - 1) & 0xFF))
        elif op == 0xCE: a = fetch16(); wr(a, setnz((rd(a) - 1) & 0xFF))
        elif op == 0xE8: r["X"] = setnz((r["X"] + 1) & 0xFF)
        elif op == 0xC8: r["Y"] = setnz((r["Y"] + 1) & 0xFF)
        elif op == 0xCA: r["X"] = setnz((r["X"] - 1) & 0xFF)
        elif op == 0x88: r["Y"] = setnz((r["Y"] - 1) & 0xFF)
        # shifts
        elif op == 0x0A:
            r["C"] = 1 if r["A"] & 0x80 else 0
            r["A"] = setnz((r["A"] << 1) & 0xFF)
        elif op == 0x06:
            a = fetch(); v = rd(a)
            r["C"] = 1 if v & 0x80 else 0
            wr(a, setnz((v << 1) & 0xFF))
        elif op == 0x4A:
            r["C"] = r["A"] & 1
            r["A"] = setnz(r["A"] >> 1)
        elif op == 0x46:
            a = fetch(); v = rd(a)
            r["C"] = v & 1
            wr(a, setnz(v >> 1))
        elif op == 0x2A:
            v = (r["A"] << 1) | r["C"]
            r["C"] = 1 if v > 0xFF else 0
            r["A"] = setnz(v & 0xFF)
        elif op == 0x26:
            a = fetch(); v = (rd(a) << 1) | r["C"]
            r["C"] = 1 if v > 0xFF else 0
            wr(a, setnz(v & 0xFF))
        elif op == 0x6A:
            v = r["A"] | (r["C"] << 8)
            r["C"] = v & 1
            r["A"] = setnz(v >> 1)
        elif op == 0x66:
            a = fetch(); v = rd(a) | (r["C"] << 8)
            r["C"] = v & 1
            wr(a, setnz(v >> 1))
        # flags, misc
        elif op == 0x18: r["C"] = 0
        elif op == 0x38: r["C"] = 1
        elif op == 0x78: pass                                    # sei
        elif op == 0x08:                                         # php
            push((r["N"] << 7) | (r["V"] << 6) | 0x30
                 | (r["Z"] << 1) | r["C"])
        elif op == 0x28:                                         # plp
            v = pop()
            r["N"], r["V"] = (v >> 7) & 1, (v >> 6) & 1
            r["Z"], r["C"] = (v >> 1) & 1, v & 1
        elif op == 0x2C:                                         # bit abs
            v = rd(fetch16())
            r["Z"] = 1 if (v & r["A"]) == 0 else 0
            r["N"] = 1 if v & 0x80 else 0
            r["V"] = 1 if v & 0x40 else 0
        # flow
        elif op == 0x20:
            a = fetch16()
            push((r["PC"] - 1) >> 8)
            push((r["PC"] - 1) & 0xFF)
            r["PC"] = a
        elif op == 0x60:
            lo = pop(); hi = pop()
            r["PC"] = (((hi << 8) | lo) + 1) & 0xFFFF
        elif op == 0x4C: r["PC"] = fetch16()
        elif op in (0xD0, 0xF0, 0xB0, 0x90, 0x10, 0x30, 0x50, 0x70):
            d = fetch()
            take = {0xD0: not r["Z"], 0xF0: r["Z"],
                    0xB0: r["C"], 0x90: not r["C"],
                    0x10: not r["N"], 0x30: r["N"],
                    0x50: not r["V"], 0x70: r["V"]}[op]
            if take:
                r["PC"] = (r["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        else:
            raise AssertionError(f"unimplemented opcode {op:02X} at {r['PC'] - 1:04X}")


def expected(pair):
    """(charset bytes, palette pages, char rows) from the pair itself."""
    tup = arcimg.decode_arc(open(os.path.join(_HERE, pair), "rb").read())
    native = next(x for x in tup if isinstance(x, dict) and "w" in x)
    px, h = native["pixels"], len(native["pixels"])
    chars = bytearray()
    for cy in range(h // 8):
        for cx in range(40):
            for line in range(8):
                for i in range(8):
                    chars.append(px[cy * 8 + line][cx * 8 + i])
    swap = lambda v: ((v & 15) << 4) | (v >> 4)
    pages = [bytearray(255) for _ in range(3)]
    for i, (rr, gg, bb) in enumerate(native["palette"]):
        pages[0][i] = swap(rr)
        pages[1][i] = swap(gg)
        pages[2][i] = swap(bb)
    return chars, pages, h // 8


def run():
    prg = open(PROBE_PRG, "rb").read()
    load = prg[0] | (prg[1] << 8)
    mem = bytearray(0x10000)
    mem[load:load + len(prg) - 2] = prg[2:]
    io = VicIV()
    io.mem = mem
    waitkey = _sym("waitkey")
    pc = _sym("boot")   # the stub entry: relocation first
    for pair in CYCLE:
        r = run_cpu(mem, io, pc, waitkey)
        chars, pages, rows = expected(pair)

        # the register discipline
        assert io.knock[:2] == [0x45, 0x54], "the knock never happened"
        assert io.regs.get(0xD054) == 0x47, "VFAST|CHR16|FCLR not set"
        assert io.regs.get(0xD05E) == 40, "CHRCOUNT not the 40-wide band"
        assert io.regs.get(0xD064) == 0 and io.regs.get(0xD065) == 0, \
            "COLPTR not pinned to the zeroed colour RAM"
        assert io.regs.get(0xD058) == 80 and io.regs.get(0xD059) == 0
        assert io.regs.get(0xD060) == SCREEN & 0xFF
        assert io.regs.get(0xD061) == SCREEN >> 8
        assert io.regs.get(0xD068) == CHARS & 0xFF
        assert io.regs.get(0xD069) == CHARS >> 8
        assert io.regs.get(0xD05D, 0) & 0x80 == 0, "HOTREG still hot"
        assert io.regs.get(0xD07B) == rows, "DISPROWS is not the band"
        assert io.regs.get(0xD020) == 0xFF and io.regs.get(0xD021) == 0xFF
        assert io.pal[0][255] == 0 and io.pal[1][255] == 0 \
            and io.pal[2][255] == 0, "entry 255 not black"

        # the character set, byte for byte
        got = mem[CHARS:CHARS + len(chars)]
        assert got == chars, f"{pair}: charset differs"

        # the formulaic screen matrix: absolute char numbers from CHARS/64
        # inside the band, the all-black char in every cell after it
        base = CHARS // 64
        blank = 0x9280 // 64
        for n in range(520):
            lo, hi = mem[SCREEN + n * 2], mem[SCREEN + n * 2 + 1]
            want = base + n if n < rows * 40 else blank
            assert lo | (hi << 8) == want, f"screen entry {n}"
        assert mem[0x9280:0x9280 + 64] == b"\xff" * 64, "no blank char"
        assert io.regs.get(0xD011, 0) & 0x10, "display not enabled at reveal"
        # the C65 ROM overlays are off
        assert io.d030 & 0b10111000 == 0, "ROM overlays still mapped"

        # the palette pages
        for p in range(3):
            assert io.pal[p][:255] == pages[p], f"{pair}: palette page {p}"

        # colour RAM: the band's 960 pairs, zeroed
        assert io.colram[:1920] == bytes(1920), "colour RAM not zeroed"

        print(f"{pair}: OK ({rows} char rows, charset {len(chars)} bytes, "
              f"palette pages verified)")

        # ret out of waitkey and continue
        sp = r["SP"]
        lo = mem[0x100 + ((sp + 1) & 0xFF)]
        hi = mem[0x100 + ((sp + 2) & 0xFF)]
        r["SP"] = (sp + 2) & 0xFF
        pc = ((hi << 8) | lo) + 1 & 0xFFFF


if __name__ == "__main__":
    run()
