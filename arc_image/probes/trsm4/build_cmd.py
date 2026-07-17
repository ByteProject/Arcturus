#!/usr/bin/env python3
# build_cmd.py - wrap a raw binary into a TRS-80 DOS /CMD load module.
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
#
# The CMD format: type-1 records carry object code (length byte counts the
# two address bytes plus the data, mod 256), a type-2 record transfers
# control. Pure Python, the build_sna.py manner.

import sys

def build(src, dst, org, entry=None):
    data = open(src, "rb").read()
    out = bytearray()
    pos = 0
    addr = org
    while pos < len(data):
        chunk = data[pos:pos + 254]
        out += bytes((0x01, (len(chunk) + 2) & 0xFF, addr & 0xFF, addr >> 8))
        out += chunk
        addr += len(chunk)
        pos += len(chunk)
    e = entry if entry is not None else org
    out += bytes((0x02, 0x02, e & 0xFF, e >> 8))
    open(dst, "wb").write(bytes(out))
    print(f"wrote {dst} ({len(out)} bytes, org ${org:04X}, entry ${e:04X})")

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    org = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x3000
    build(src, dst, org)
