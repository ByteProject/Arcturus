"""Execute the assembled MSX1 probe end to end on a mini Z80 with a
TMS9918A write model, and verify VRAM. Same strict-interpreter approach
as the ZX3 probe's run_probe.py (exactly the opcodes the probe uses,
anything else raises), plus an io map: port $99 pairs latch VDP register
writes and VRAM write addresses, port $98 writes VRAM and
auto-increments, ports $A9/$AA model an idle keyboard. Execution pauses
at each `waitkey` ENTRY (the just-drawn image is complete), VRAM and the
VDP registers are captured, and waitkey is skipped by simulating its
ret. Two captures (mode 9, then mode 12), then stop.

Expected VRAM comes straight from the embedded pairs via arcimg's
read_arc: the raw pattern section at $0000, raw color section at $2000,
the identity name table at $1800, the sprite terminator at $1B00, zeros
everywhere else. Run this after every reassembly, BEFORE any emulator
pass; the emulator hand-off is about pixels, not loader bugs.
"""

import os
import sys
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
PROBE_BIN = os.path.join(_HERE, "probe.bin")
ORG = 0x9000
WAITKEY = 0x9081    # from the sjasmplus listing; re-derive if probe.asm
                    # gains or loses code before the waitkey routine

_spec = importlib.util.spec_from_file_location(
    "arcimg", os.path.join(_ROOT, "..", "tools", "arcimg.py"))
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)


def expected_vram(pair_path):
    vram = bytearray(0x4000)
    _head, secs = arcimg.read_arc(open(pair_path, "rb").read())
    for stype, _flags, raw in secs:
        base = {1: 0x0000, 3: 0x2000}[stype]
        vram[base:base + len(raw)] = raw
    for third in range(3):
        for n in range(256):
            vram[0x1800 + third * 256 + n] = n
    vram[0x1B00] = 208
    return bytes(vram)


EXPECTED_REGS = [0x02, 0xC0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x01]


def run():
    code = open(PROBE_BIN, "rb").read()
    m = bytearray(0x10000)
    m[ORG:ORG + len(code)] = code
    vram = bytearray(0x4000)
    vdp = {"latch": None, "addr": 0, "regs": [0] * 8}
    reg = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "H": 0, "L": 0}
    st = {"PC": ORG, "SP": 0xFFF0, "Z": 0, "CF": 0, "steps": 0, "IX": 0}
    captures = []

    def io_out(port, val):
        if port == 0x98:
            vram[vdp["addr"]] = val
            vdp["addr"] = (vdp["addr"] + 1) & 0x3FFF
            vdp["latch"] = None
        elif port == 0x99:
            if vdp["latch"] is None:
                vdp["latch"] = val
            else:
                lo, hi = vdp["latch"], val
                vdp["latch"] = None
                if hi & 0x80:
                    vdp["regs"][hi & 0x07] = lo
                elif hi & 0x40:
                    vdp["addr"] = ((hi & 0x3F) << 8) | lo
                else:
                    vdp["addr"] = ((hi & 0x3F) << 8) | lo  # read setup
        elif port == 0xAA:
            pass                                    # row select, ignored
        else:
            raise AssertionError(f"out to unmodeled port {port:02X}")

    def io_in(port):
        if port == 0xA9:
            return 0xFF                             # all keys up
        if port == 0xAA:
            return 0x00
        raise AssertionError(f"in from unmodeled port {port:02X}")

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
        if st["PC"] == WAITKEY:
            captures.append((bytes(vram), list(vdp["regs"])))
            if len(captures) == 2:
                return captures
            st["PC"] = pop16()          # skip waitkey: simulate its ret
            continue
        st["steps"] += 1
        if st["steps"] > 60_000_000:
            raise AssertionError("probe did not reach waitkey (runaway)")
        op = fetch()
        if op == 0x76:
            raise AssertionError("unexpected halt")
        elif op == 0xF3:                            # di
            pass
        elif op == 0x31:                            # ld sp,nn
            st["SP"] = fetch16()
        elif op == 0xAF:                            # xor a
            reg["A"] = 0
            setzn(0)
            st["CF"] = 0
        elif op == 0xD3:                            # out (n),a
            io_out(fetch(), reg["A"])
        elif op == 0xDB:                            # in a,(n)
            reg["A"] = io_in(fetch())
        elif op == 0x2F:                            # cpl
            reg["A"] ^= 0xFF
        elif op == 0xC3:                            # jp nn
            st["PC"] = fetch16()
        elif op == 0xC0:                            # ret nz
            if not st["Z"]:
                st["PC"] = pop16()
        elif op == 0xFE:                            # cp n
            n = fetch()
            v = reg["A"] - n
            st["Z"] = 1 if (v & 0xFF) == 0 else 0
            st["CF"] = 1 if v < 0 else 0
        elif op == 0x06:                            # ld b,n
            reg["B"] = fetch()
        elif op == 0x16:                            # ld d,n
            reg["D"] = fetch()
        elif op == 0x1E:                            # ld e,n
            reg["E"] = fetch()
        elif op == 0x79:                            # ld a,c
            reg["A"] = reg["C"]
        elif op == 0x7B:                            # ld a,e
            reg["A"] = reg["E"]
        elif op == 0x7D:                            # ld a,l
            reg["A"] = reg["L"]
        elif op == 0x1C:                            # inc e
            reg["E"] = (reg["E"] + 1) & 0xFF
            setzn(reg["E"])
        elif op == 0x0D:                            # dec c
            reg["C"] = (reg["C"] - 1) & 0xFF
            setzn(reg["C"])
        elif op == 0xB2:                            # or d
            reg["A"] |= reg["D"]
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xB3:                            # or e
            reg["A"] |= reg["E"]
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xB7:                            # or a
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0x3C:                            # inc a
            reg["A"] = (reg["A"] + 1) & 0xFF
            setzn(reg["A"])
        elif op == 0x56:                            # ld d,(hl)
            reg["D"] = m[rr16("H", "L")]
        elif op == 0x5E:                            # ld e,(hl)
            reg["E"] = m[rr16("H", "L")]
        elif op == 0x6B:                            # ld l,e
            reg["L"] = reg["E"]
        elif op == 0x62:                            # ld h,d
            reg["H"] = reg["D"]
        elif op == 0x57:                            # ld d,a
            reg["D"] = reg["A"]
        elif op == 0x29:                            # add hl,hl
            v = rr16("H", "L") * 2
            st["CF"] = 1 if v > 0xFFFF else 0
            wr16("H", "L", v & 0xFFFF)
        elif op == 0x10:                            # djnz
            d = fetch()
            reg["B"] = (reg["B"] - 1) & 0xFF
            if reg["B"]:
                st["PC"] = (st["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        elif op == 0xDD:                            # IX prefix
            sub = fetch()
            if sub == 0xE5:                         # push ix
                push16(st["IX"])
            elif sub == 0xE1:                       # pop ix
                st["IX"] = pop16()
            elif sub in (0x7E, 0x5E, 0x46):         # ld a/e/b,(ix+d)
                d = fetch()
                v = m[(st["IX"] + (d - 256 if d > 127 else d)) & 0xFFFF]
                reg[{0x7E: "A", 0x5E: "E", 0x46: "B"}[sub]] = v
            else:
                raise AssertionError(f"unimplemented DD {sub:02X}")
        # ---- the shared tests/test_dzx0r.py core, verbatim -----------------
        elif op == 0x01:
            wr16("B", "C", fetch16())
        elif op == 0x11:
            wr16("D", "E", fetch16())
        elif op == 0x21:
            wr16("H", "L", fetch16())
        elif op == 0x2A:
            a = fetch16()
            wr16("H", "L", m[a] | (m[(a + 1) & 0xFFFF] << 8))
        elif op == 0x22:
            a = fetch16()
            m[a] = reg["L"]
            m[(a + 1) & 0xFFFF] = reg["H"]
        elif op == 0x0E:
            reg["C"] = fetch()
        elif op == 0x3E:
            reg["A"] = fetch()
        elif op == 0xD8:
            if st["CF"]:
                st["PC"] = pop16()
        elif op == 0xE6:
            reg["A"] &= fetch()
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xF6:
            reg["A"] |= fetch()
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xB1:
            reg["A"] |= reg["C"]
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0x87:
            v = reg["A"] << 1
            st["CF"] = 1 if v > 0xFF else 0
            reg["A"] = v & 0xFF
            setzn(reg["A"])
        elif op == 0x17:
            v = (reg["A"] << 1) | st["CF"]
            st["CF"] = 1 if v > 0xFF else 0
            reg["A"] = v & 0xFF
        elif op == 0x19:
            v = rr16("H", "L") + rr16("D", "E")
            st["CF"] = 1 if v > 0xFFFF else 0
            wr16("H", "L", v & 0xFFFF)
        elif op in (0x03, 0x13, 0x23):
            hi, lo = {0x03: ("B", "C"), 0x13: ("D", "E"),
                      0x23: ("H", "L")}[op]
            wr16(hi, lo, (rr16(hi, lo) + 1) & 0xFFFF)
        elif op == 0x0B:
            wr16("B", "C", (rr16("B", "C") - 1) & 0xFFFF)
        elif op == 0x0C:
            reg["C"] = (reg["C"] + 1) & 0xFF
            setzn(reg["C"])
        elif op == 0x7E:
            reg["A"] = m[rr16("H", "L")]
        elif op == 0x4E:
            reg["C"] = m[rr16("H", "L")]
        elif op == 0x77:
            m[rr16("H", "L")] = reg["A"]
        elif op == 0x12:
            m[rr16("D", "E")] = reg["A"]
        elif op == 0x78:
            reg["A"] = reg["B"]
        elif op == 0x7A:
            reg["A"] = reg["D"]
        elif op == 0x7C:
            reg["A"] = reg["H"]
        elif op == 0x41:
            reg["B"] = reg["C"]
        elif op == 0x67:
            reg["H"] = reg["A"]
        elif op in (0xC5, 0xD5, 0xE5):
            hi, lo = {0xC5: ("B", "C"), 0xD5: ("D", "E"),
                      0xE5: ("H", "L")}[op]
            push16(rr16(hi, lo))
        elif op == 0xF5:
            push16((reg["A"] << 8) | (st["Z"] << 6) | st["CF"])
        elif op in (0xC1, 0xD1, 0xE1):
            hi, lo = {0xC1: ("B", "C"), 0xD1: ("D", "E"),
                      0xE1: ("H", "L")}[op]
            wr16(hi, lo, pop16())
        elif op == 0xF1:
            v = pop16()
            reg["A"] = (v >> 8) & 0xFF
            st["Z"] = (v >> 6) & 1
            st["CF"] = v & 1
        elif op == 0xE3:
            v = pop16()
            push16(rr16("H", "L"))
            wr16("H", "L", v)
        elif op == 0xED:
            sub = fetch()
            if sub == 0xA0:                         # ldi
                m[rr16("D", "E")] = m[rr16("H", "L")]
                wr16("D", "E", (rr16("D", "E") + 1) & 0xFFFF)
                wr16("H", "L", (rr16("H", "L") + 1) & 0xFFFF)
                wr16("B", "C", (rr16("B", "C") - 1) & 0xFFFF)
            else:
                raise AssertionError(f"unimplemented ED {sub:02X}")
        elif op == 0x18:
            d = fetch()
            st["PC"] = (st["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        elif op in (0x20, 0x28, 0x30, 0x38):
            d = fetch()
            take = {0x20: not st["Z"], 0x28: st["Z"],
                    0x30: not st["CF"], 0x38: st["CF"]}[op]
            if take:
                st["PC"] = (st["PC"] + (d - 256 if d > 127 else d)) & 0xFFFF
        elif op == 0xCD:
            a = fetch16()
            push16(st["PC"])
            st["PC"] = a
        elif op == 0xD4:
            a = fetch16()
            if not st["CF"]:
                push16(st["PC"])
                st["PC"] = a
        elif op == 0xC9:
            st["PC"] = pop16()
        elif op == 0xC8:
            if st["Z"]:
                st["PC"] = pop16()
        elif op == 0xCB:
            sub = fetch()
            tgt = {0x10: "B", 0x11: "C", 0x18: "B", 0x19: "C"}.get(sub)
            if tgt is None:
                raise AssertionError(f"unimplemented CB {sub:02X}")
            if sub in (0x10, 0x11):
                v = (reg[tgt] << 1) | st["CF"]
                st["CF"] = 1 if v > 0xFF else 0
                reg[tgt] = v & 0xFF
            else:
                v = reg[tgt] | (st["CF"] << 8)
                st["CF"] = v & 1
                reg[tgt] = v >> 1
            setzn(reg[tgt])
        else:
            raise AssertionError(
                f"unimplemented opcode {op:02X} at {st['PC'] - 1:04X}")


def main():
    (v9, r9), (v12, r12) = run()
    ok = True
    for name, got, regs, pair in (
            ("mode 9", v9, r9, "9.MS1"),
            ("mode 12", v12, r12, "12.MS1")):
        exp = expected_vram(os.path.join(_HERE, pair))
        if regs != EXPECTED_REGS:
            print(f"{name}: VDP registers {regs} != {EXPECTED_REGS}")
            ok = False
        if got == exp:
            print(f"{name}: VRAM byte-exact "
                  f"({sum(1 for b in got if b)} nonzero bytes)")
        else:
            bad = [i for i in range(len(exp)) if got[i] != exp[i]]
            print(f"{name}: {len(bad)} MISMATCHED bytes, first at "
                  f"${bad[0]:04X} (got {got[bad[0]]:02X}, "
                  f"want {exp[bad[0]]:02X})")
            ok = False
    if not ok:
        raise SystemExit(1)
    print("full probe simulation: PASS")


if __name__ == "__main__":
    main()
