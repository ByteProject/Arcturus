# mk_nex.py - wrap the assembled NXT probe into a standard .nex file
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.

"""Build probe.nex from probe.bin: the Next-native executable the NEXTZXOS
browser (and ZEsarUX's TBBlue, and CSpect, and real hardware from SD) loads
directly. Pure Python, stdlib only, the BuildTools doctrine.

The .nex V1.2 layout, the parts this probe needs: a 512-byte header
("Next", "V1.2", RAM wanted, bank count, SP, PC, the 112-byte
bank-presence table, and the minimum core version), then each present
16K bank in the canonical loader order. The probe is one bank: bank 0,
mapped at $C000 by the standard map, holding code and both embedded
pairs; PC $C000, SP $BFF0. Core 3.0.0 is required for the 320x256
Layer 2 mode, so older cores refuse loudly instead of showing garbage.

Run:  python3 mk_nex.py        (writes probe.nex beside probe.bin)
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ORG = 0xC000
SP = 0xBFF0


def _bank(data):
    assert len(data) <= 16384
    return data + bytes(16384 - len(data))


def build():
    code = open(os.path.join(HERE, "probe.bin"), "rb").read()
    banks = {                        # bank -> 16K content
        0: _bank(code),              # the loader, mapped at $C000
        1: _bank(open(os.path.join(HERE, "9.NXT"), "rb").read()),
        3: _bank(open(os.path.join(HERE, "12.NXT"), "rb").read()),
    }

    hdr = bytearray(512)
    hdr[0:4] = b"Next"
    hdr[4:8] = b"V1.2"
    hdr[8] = 0                      # RAM required: 768K
    hdr[9] = len(banks)             # banks to load
    hdr[10] = 0                     # no loading screen
    hdr[11] = 0                     # border black
    hdr[12] = SP & 0xFF             # SP, little-endian
    hdr[13] = SP >> 8
    hdr[14] = ORG & 0xFF            # PC: jump straight into the probe
    hdr[15] = ORG >> 8
    hdr[16] = 0                     # extra files: none
    hdr[17] = 0
    for b in banks:
        hdr[18 + b] = 1             # the bank-presence table
    hdr[135] = 3                    # core 3.0.0 minimum: the 320 mode
    hdr[136] = 0
    hdr[137] = 0

    # banks are stored in the loader's canonical order
    order = [b for b in (5, 2, 0, 1, 3, 4, 6, 7) if b in banks]
    out = os.path.join(HERE, "probe.nex")
    with open(out, "wb") as f:
        f.write(hdr)
        for b in order:
            f.write(banks[b])
    print(f"wrote {out} ({512 + 16384 * len(banks)} bytes: "
          f"header + banks {sorted(banks)})")


if __name__ == "__main__":
    build()
