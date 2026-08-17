# run_probe.py - headless pre-proof of the Apple II DHGR arc_image probe
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.

"""Execute the assembled AP2 probe end to end on the strict 6502 core
(the house manner: a common-6502 subset, anything else raises) under an
Apple II softswitch model, and prove everything the probe claims before
any emulator runs: both hi-res pages' bytes (through the line-address
scatter), the below-band clear, and the switch end-state (graphics,
hi-res, full screen, AN3 off, 80COL, 80STORE).

The model implements exactly what the probe touches: main and aux 64K,
with $2000-$3FFF banked by 80STORE+PAGE2 (the DHGR loader's whole
memory story), and the keyboard register pair. An unmodeled softswitch
is a failure, not an emulation.

Execution pauses at each `waitkey` ENTRY, the pages are compared
against the pair file's own decode (arcimg's decode_arc is the
oracle), and waitkey returns by simulated ret. Two captures, mode 9
then mode 12, then stop. Addresses come from probe.sym (acme -l).

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

PROBE_BIN = os.path.join(_HERE, "probe.bin")
PROBE_SYM = os.path.join(_HERE, "probe.sym")
ORG = 0x6000
CYCLE = ("9.AP2", "12.AP2")


def _sym(name):
    for line in open(PROBE_SYM):
        m = re.match(rf"\s*{name}\s*=\s*\$([0-9A-Fa-f]+)", line)
        if m:
            return int(m.group(1), 16)
    raise SystemExit(f"run_probe: no symbol '{name}' in probe.sym")


def _lineaddr(y):
    return 0x2000 + (y & 7) * 0x400 + ((y >> 3) & 7) * 0x80 + (y >> 6) * 0x28


class AppleII:
    """Main and aux RAM behind the softswitches the probe uses."""

    def __init__(self):
        self.main = bytearray(0x10000)
        self.aux = bytearray(0x10000)
        self.sw = set()

    def _bank(self, addr):
        if ("80STORE" in self.sw and "PAGE2" in self.sw
                and 0x2000 <= addr <= 0x3FFF):
            return self.aux
        return self.main

    def read(self, addr):
        if addr == 0xC000:
            return 0                      # no key pending
        if 0xC000 <= addr <= 0xC0FF:
            self._switch(addr)
            return 0
        return self._bank(addr)[addr]

    def write(self, addr, v):
        if 0xC000 <= addr <= 0xC0FF:
            self._switch(addr)
            return
        self._bank(addr)[addr] = v & 0xFF

    def _switch(self, addr):
        known = {
            0xC001: ("80STORE", True),
            0xC00D: ("80COL", True),
            0xC050: ("GR", True), 0xC051: ("GR", False),
            0xC052: ("FULL", True), 0xC053: ("FULL", False),
            0xC054: ("PAGE2", False), 0xC055: ("PAGE2", True),
            0xC057: ("HIRES", True), 0xC056: ("HIRES", False),
            0xC05E: ("AN3OFF", True), 0xC05F: ("AN3OFF", False),
            0xC010: ("STROBE", True),
        }
        if addr not in known:
            raise AssertionError(f"unmodeled softswitch ${addr:04X}")
        name, on = known[addr]
        if name == "STROBE":
            return
        if on:
            self.sw.add(name)
        else:
            self.sw.discard(name)


class _CpuView:
    """The core's flat `mem` interface over the banked machine, so the
    80STORE banking stays honest for every access the core makes."""

    def __init__(self, machine):
        self.m = machine

    def __getitem__(self, i):
        return self.m.read(i)

    def __setitem__(self, i, v):
        self.m.write(i, v)


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
        elif op == 0xBC: r["Y"] = setnz(rd((fetch16() + r["X"]) & 0xFFFF))
        elif op == 0xBE: r["X"] = setnz(rd((fetch16() + r["Y"]) & 0xFFFF))
        elif op == 0xB6: r["X"] = setnz(rd((fetch() + r["Y"]) & 0xFF))
        elif op == 0xB5: r["A"] = setnz(rd((fetch() + r["X"]) & 0xFF))
        elif op == 0x95: wr((fetch() + r["X"]) & 0xFF, r["A"])
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
    tup = arcimg.decode_arc(open(os.path.join(_HERE, pair), "rb").read())
    native = next(x for x in tup if isinstance(x, dict) and "w" in x)
    return native, len(native["aux"])


def run():
    m = AppleII()
    prg = open(PROBE_BIN, "rb").read()
    m.main[ORG:ORG + len(prg)] = prg
    mem = _CpuView(m)
    waitkey = _sym("waitkey")
    pc = _sym("start")
    for pair in CYCLE:
        r = run_cpu(mem, m, pc, waitkey)
        native, rows = expected(pair)

        want = {"80STORE", "80COL", "GR", "FULL", "HIRES", "AN3OFF"}
        assert want <= m.sw, f"switches missing: {want - m.sw}"

        for y in range(96):
            a = _lineaddr(y)
            if y < rows:
                assert m.aux[a:a + 40] == bytes(native["aux"][y]), \
                    f"{pair}: aux row {y}"
                assert m.main[a:a + 40] == bytes(native["main"][y]), \
                    f"{pair}: main row {y}"
            else:
                assert m.aux[a:a + 40] == bytes(40), f"aux row {y} not black"
                assert m.main[a:a + 40] == bytes(40), f"main row {y} not black"

        print(f"{pair}: OK ({rows} rows, both pages, switches clean)")

        sp = r["SP"]
        lo = m.main[0x100 + ((sp + 1) & 0xFF)]
        hi = m.main[0x100 + ((sp + 2) & 0xFF)]
        r["SP"] = (sp + 2) & 0xFF
        pc = ((hi << 8) | lo) + 1 & 0xFFFF


if __name__ == "__main__":
    run()
