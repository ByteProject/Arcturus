"""Execute the assembled ZX3 probe end to end on a mini Z80 and verify
the screen. The core is tests/test_dzx0r.py's strict interpreter extended
with exactly the opcodes the probe scaffold adds (di, out, ix loads,
ldir, djnz, cp, ...); anything else still raises. Instead of emulating
the keyboard, execution pauses at each `waitkey` ENTRY (the moment the
just-drawn image is complete on screen), the ULA region $4000-$5AFF is
captured, and waitkey is skipped by simulating its ret. One capture per
image in the review cycle, then stop.

Expected frames come straight from the pair files: a drawn pair must
leave behind exactly the scr projection of its own native (band on
top, black below), so decode_arc + scr_from_native is the oracle.
"""

import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
PROBE_BIN = os.path.join(_HERE, "probe.bin")
# The probe's review cycle: one pair file per waitkey stop, in the
# order probe.asm draws them (Stefan's four-picture ruling, 2026-08-13:
# his art 8 both modes, his art 14, then the b/w of both scenes).
# Regenerate probe.bin (sjasmplus probe.asm) whenever the pairs change,
# then run this BEFORE any emulator pass.
CYCLE = ("9.ZX3", "12.ZX3", "art14.ZX3", "bw8.ZX3", "bw14.ZX3")
ORG = 0x8000
WAITKEY = 0x8041    # from the sjasmplus listing; re-derive if probe.asm
                    # gains or loses code before the waitkey routine

_spec = importlib.util.spec_from_file_location(
    "arcimg", os.path.join(_ROOT, "..", "tools", "arcimg.py"))
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)


def expected_frame(pair):
    """The ULA region $4000-$5AFF a drawn pair must leave behind."""
    tup = arcimg.decode_arc(open(os.path.join(_HERE, pair), "rb").read())
    native = next(x for x in tup if isinstance(x, dict) and "w" in x)
    return arcimg.scr_from_native(native)[:0x1B00]


def run():
    code = open(PROBE_BIN, "rb").read()
    m = bytearray(0x10000)
    m[ORG:ORG + len(code)] = code
    reg = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "H": 0, "L": 0}
    st = {"PC": ORG, "SP": 0xFFF0, "Z": 0, "CF": 0, "steps": 0, "IX": 0}
    captures = []

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
            captures.append(bytes(m[0x4000:0x5B00]))
            if len(captures) == len(CYCLE):
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
            fetch()
        elif op == 0x2F:                            # cpl
            reg["A"] ^= 0xFF
        elif op == 0x36:                            # ld (hl),n
            m[rr16("H", "L")] = fetch()
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
        elif op == 0xBF:                            # cp a
            st["Z"], st["CF"] = 1, 0
        elif op == 0x32:                            # ld (nn),a
            m[fetch16()] = reg["A"]
        elif op == 0x3A:                            # ld a,(nn)
            reg["A"] = m[fetch16()]
        elif op == 0x06:                            # ld b,n
            reg["B"] = fetch()
        elif op == 0x16:                            # ld d,n
            reg["D"] = fetch()
        elif op == 0x26:                            # ld h,n
            reg["H"] = fetch()
        elif op == 0x2E:                            # ld l,n
            reg["L"] = fetch()
        elif op == 0x6B:                            # ld l,e
            reg["L"] = reg["E"]
        elif op == 0x62:                            # ld h,d
            reg["H"] = reg["D"]
        elif op == 0x6F:                            # ld l,a
            reg["L"] = reg["A"]
        elif op == 0x47:                            # ld b,a
            reg["B"] = reg["A"]
        elif op == 0x56:                            # ld d,(hl)
            reg["D"] = m[rr16("H", "L")]
        elif op == 0x5E:                            # ld e,(hl)
            reg["E"] = m[rr16("H", "L")]
        elif op == 0x29:                            # add hl,hl
            v = rr16("H", "L") * 2
            st["CF"] = 1 if v > 0xFFFF else 0
            wr16("H", "L", v & 0xFFFF)
        elif op == 0x90:                            # sub b
            v = reg["A"] - reg["B"]
            st["CF"] = 1 if v < 0 else 0
            reg["A"] = v & 0xFF
            setzn(reg["A"])
        elif op == 0xB7:                            # or a
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0xB5:                            # or l
            reg["A"] |= reg["L"]
            setzn(reg["A"])
            st["CF"] = 0
        elif op == 0x24:                            # inc h
            reg["H"] = (reg["H"] + 1) & 0xFF
            setzn(reg["H"])
        elif op == 0x3C:                            # inc a
            reg["A"] = (reg["A"] + 1) & 0xFF
            setzn(reg["A"])
        elif op == 0x3D:                            # dec a
            reg["A"] = (reg["A"] - 1) & 0xFF
            setzn(reg["A"])
        elif op == 0xC6:                            # add a,n
            v = reg["A"] + fetch()
            st["CF"] = 1 if v > 0xFF else 0
            reg["A"] = v & 0xFF
            setzn(reg["A"])
        elif op == 0x2B:                            # dec hl (no flags)
            wr16("H", "L", (rr16("H", "L") - 1) & 0xFFFF)
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
        # ---- everything below is tests/test_dzx0r.py's core, verbatim ----
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
        elif op == 0x57:
            reg["D"] = reg["A"]
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
            elif sub == 0xB0:                       # ldir
                while True:
                    m[rr16("D", "E")] = m[rr16("H", "L")]
                    wr16("D", "E", (rr16("D", "E") + 1) & 0xFFFF)
                    wr16("H", "L", (rr16("H", "L") + 1) & 0xFFFF)
                    bc = (rr16("B", "C") - 1) & 0xFFFF
                    wr16("B", "C", bc)
                    st["steps"] += 1
                    if bc == 0:
                        break
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
    frames = run()
    for pair, got in zip(CYCLE, frames):
        exp = expected_frame(pair)
        if got == exp:
            print(f"{pair}: screen byte-exact "
                  f"({sum(1 for b in got if b)} nonzero bytes)")
        else:
            bad = [i for i in range(len(exp)) if got[i] != exp[i]]
            print(f"{pair}: {len(bad)} MISMATCHED bytes, first at "
                  f"${0x4000 + bad[0]:04X} "
                  f"(got {got[bad[0]]:02X}, want {exp[bad[0]]:02X})")
            raise SystemExit(1)
    print("full probe simulation: PASS")


if __name__ == "__main__":
    main()
