# run_probe.py - headless pre-proof of the Spectrum Next arc_image probe
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.

"""Execute the assembled NXT probe end to end on Haumea's simz80 core
(Stefan's portable Z80 simulator, ../../../..//Haumea/tools/simz80.py,
used unmodified) under a small TBBlue port model, and verify everything
the probe claims before any emulator is asked: the Layer 2 bytes it
placed, the palette it wrote, and the register discipline (320 mode,
ULA off, the band clip, the MMU restore).

The TBBlue model implements exactly what the probe touches: the
NextReg select/data port pair ($243B/$253B) with the registers the
blueprint names (MMU slots $50-$57 as real paging over a 2MB physical
RAM, the two-write 9-bit palette protocol $40/$43/$44, the Layer 2
clip window $18 with its $1C index reset), and the Layer 2 visible bit
on port $123B. Anything else the probe would touch is a failure, not
an emulation.

Execution pauses at each `waitkey` ENTRY (the moment an image is
complete and revealed), the layer region is captured and compared
against the pair file's own decode (arcimg's decode_arc is the
oracle), and waitkey returns by simulated ret. Two captures, mode 9
then mode 12, then stop. The waitkey address comes from probe.sym
(sjasmplus --sym), never hand-derived.

Run:  python3 run_probe.py     (prints one verdict line per image)
"""

import importlib.util
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))  # the Arcturus repo


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


arcimg = _load("arcimg", os.path.join(_ROOT, "tools", "arcimg.py"))
_SIM = os.path.join(os.path.dirname(_ROOT), "Haumea", "tools", "simz80.py")
if not os.path.exists(_SIM):
    sys.exit("run_probe: Haumea's simz80.py not found at " + _SIM)
simz80 = _load("simz80", _SIM)

PROBE_BIN = os.path.join(_HERE, "probe.bin")
PROBE_SYM = os.path.join(_HERE, "probe.sym")
ORG = 0xC000
CYCLE = ("9.NXT", "12.NXT")     # probe.asm's review order
PAGE_SIZE = 8192
LAYER_PAGE = 16                 # NextReg $12 = 16K bank 8 -> 8K page 16


def _sym(name):
    """A label's address from the sjasmplus symbol file."""
    for line in open(PROBE_SYM):
        m = re.match(rf"{name}:?\s+(?:EQU\s+)?0x([0-9A-Fa-f]+)", line.strip(), re.I)
        if m:
            return int(m.group(1), 16) & 0xFFFF
    raise SystemExit(f"run_probe: no symbol '{name}' in probe.sym")


class TBBlue(simz80.Machine):
    """Haumea's Machine with the Next's paging and register ports."""

    def __init__(self):
        super().__init__()
        self.phys = bytearray(2 * 1024 * 1024)
        # The standard post-boot map the .nex loader leaves behind:
        # ROM, ROM, bank 5, bank 2, bank 0 (8K pages).
        self.pages = [0xFF, 0xFF, 10, 11, 4, 5, 0, 1]
        self.rom = bytearray(16384)          # never executed; reads as 0
        self.nextregs = {}
        self.sel = 0
        self.clip = []                        # the four $18 writes, in order
        self.pal_index = 0
        self.pal_phase = 0
        self.pal_first = 0
        self.palette = {}                     # index -> (byte1, bit9)
        self.visible = 0

    # ---- paged memory ----------------------------------------------------
    def _read(self, addr):
        page = self.pages[(addr >> 13) & 7]
        if page >= 0xFE:
            return self.rom[addr & 0x3FFF]
        return self.phys[page * PAGE_SIZE + (addr & 0x1FFF)]

    def _write(self, addr, val):
        page = self.pages[(addr >> 13) & 7]
        if page < 0xFE:
            self.phys[page * PAGE_SIZE + (addr & 0x1FFF)] = val & 0xFF

    def load_cpu(self, data, addr):
        for i, b in enumerate(data):
            self._write(addr + i, b)

    # ---- ports -----------------------------------------------------------
    def _io_out(self, port, val):
        port &= 0xFFFF
        val &= 0xFF
        if port == 0x243B:
            self.sel = val
        elif port == 0x253B:
            self._nextreg(self.sel, val)
        elif port == 0x123B:
            self.visible = val
        else:
            raise SystemExit(f"probe touched unmodeled port ${port:04X}")

    def _io_in(self, port):
        if (port & 0xFF) == 0xFE:
            return 0xFF                       # no key held
        raise SystemExit(f"probe read unmodeled port ${port & 0xFFFF:04X}")

    def _nextreg(self, reg, val):
        self.nextregs[reg] = val
        if 0x50 <= reg <= 0x57:
            self.pages[reg - 0x50] = val
        elif reg == 0x1C and val & 1:
            self.clip = []                    # Layer 2 clip index reset
        elif reg == 0x18:
            self.clip.append(val)
        elif reg == 0x40:
            self.pal_index = val
            self.pal_phase = 0
        elif reg == 0x44:
            if self.pal_phase == 0:
                self.pal_first = val
                self.pal_phase = 1
            else:
                self.palette[self.pal_index] = (self.pal_first, val & 1)
                self.pal_index = (self.pal_index + 1) & 0xFF
                self.pal_phase = 0


def expected(pair):
    """(pixels, palette-pairs, height) from the pair file itself."""
    tup = arcimg.decode_arc(open(os.path.join(_HERE, pair), "rb").read())
    native = next(x for x in tup if isinstance(x, dict) and "w" in x)
    pal = []
    for r, g, b in native["palette"]:
        r3, g3, b3 = r >> 5, g >> 5, b >> 5
        pal.append(((r3 << 5) | (g3 << 2) | (b3 >> 1), b3 & 1))
    return native["pixels"], pal, len(native["pixels"])


def run():
    m = TBBlue()
    m.load_cpu(open(PROBE_BIN, "rb").read(), ORG)
    # the pairs ride their own banks, as the .nex lays them out:
    # 9.NXT in 16K bank 1 (8K pages 2,3), 12.NXT in bank 3 (pages 6,7)
    for pair, page in (("9.NXT", 2), ("12.NXT", 6)):
        data = open(os.path.join(_HERE, pair), "rb").read()
        m.phys[page * PAGE_SIZE: page * PAGE_SIZE + len(data)] = data
    waitkey = _sym("waitkey")
    pc = ORG
    for pair in CYCLE:
        m.run(start=pc, max_steps=200_000_000, stop_pc=waitkey)
        assert m.cpu.pc == waitkey, f"probe never reached waitkey for {pair}"
        pixels, pal, h = expected(pair)

        # the register discipline
        assert m.nextregs.get(0x70) == 0x10, "not the 320x256 mode"
        assert m.nextregs.get(0x68) == 0x80, "ULA not switched off"
        assert m.nextregs.get(0x12) == 8, "layer bank not stated"
        assert m.clip == [0, 159, 0, h - 1], f"clip {m.clip} != band {h}"
        assert m.visible & 2, "Layer 2 not visible at the reveal"
        assert m.pages[7] == 1, "MMU slot 7 not restored after the blit"

        # the layer bytes: column-major x*256+y from 8K page 16
        base = LAYER_PAGE * PAGE_SIZE
        for x in range(320):
            col = m.phys[base + x * 256: base + x * 256 + h]
            want = bytes(pixels[y][x] for y in range(h))
            assert col == want, f"{pair}: column {x} differs"

        # the palette, all 256 entries through the two-write protocol
        for i, want in enumerate(pal):
            assert m.palette.get(i) == want, f"{pair}: palette entry {i}"

        print(f"{pair}: OK (mode band {h}, 320 columns, 256 palette entries)")

        # ret out of waitkey and continue the cycle
        sp = m.cpu.sp
        pc = m._read(sp) | (m._read(sp + 1) << 8)
        m.cpu.sp = (sp + 2) & 0xFFFF


if __name__ == "__main__":
    run()
