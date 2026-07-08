#!/usr/bin/env python3
# build_adf.py - assemble the Amiga probe and lay it onto a bootable ADF.
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
#
# The ADF is raw sectors, no filesystem: bootblock (sectors 0-1, DOS\0 magic
# and the Kickstart checksum) plus the payload from sector 2. Usage:
#
#   python3 build_adf.py [--vasm PATH]   -> probe.adf

import argparse
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADF_BYTES = 901120
SECTOR = 512


def run_vasm(vasm, src, out):
    r = subprocess.run([vasm, "-Fbin", "-o", out, src], cwd=HERE,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"vasm failed on {src}")


def checksum(block: bytes) -> int:
    """The Kickstart bootblock checksum: the 256 longwords sum, WITH the
    carry folded back in after every add, to $FFFFFFFF."""
    s = 0
    for i in range(0, 1024, 4):
        s += struct.unpack(">I", block[i:i + 4])[0]
        if s > 0xFFFFFFFF:
            s = (s & 0xFFFFFFFF) + 1
    return 0xFFFFFFFF - s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vasm",
                    default="/Users/stefan/Fiction/Eris/tools/bin/vasmm68k_mot")
    args = ap.parse_args()

    run_vasm(args.vasm, "payload.s", "payload.bin")
    with open(os.path.join(HERE, "payload.bin"), "rb") as f:
        payload = f.read()
    plen = (len(payload) + SECTOR - 1) // SECTOR * SECTOR

    run_vasm(args.vasm, "boot.s", "boot.bin")
    with open(os.path.join(HERE, "boot.bin"), "rb") as f:
        boot = bytearray(f.read())
    boot += bytes(1024 - len(boot))
    # Patch the payload length (the last longword of the code, label plen:
    # found as the final nonzero-adjacent slot; simplest is a marker scan).
    at = boot.rfind(b"\x00\x00\x00\x00", 12, len(boot.rstrip(b"\x00")) + 4)
    # plen sits at the end of the assembled code; locate it as the trailing
    # longword of the unpadded boot.bin.
    code_len = len(open(os.path.join(HERE, "boot.bin"), "rb").read())
    boot[code_len - 4:code_len] = struct.pack(">I", plen)
    # Checksum last (field at offset 4).
    boot[4:8] = b"\x00\x00\x00\x00"
    boot[4:8] = struct.pack(">I", checksum(bytes(boot)))

    adf = bytearray(ADF_BYTES)
    adf[0:1024] = boot
    adf[1024:1024 + len(payload)] = payload
    out = os.path.join(HERE, "probe.adf")
    with open(out, "wb") as f:
        f.write(adf)
    print(f"wrote probe.adf (payload {len(payload)} bytes, "
          f"read length {plen})")


if __name__ == "__main__":
    main()
