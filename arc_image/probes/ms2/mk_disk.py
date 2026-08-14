"""Build the bootable MSX probe disk: wrap probe.bin (raw, org $B400)
into a BSAVE binary, write the Disk BASIC AUTOEXEC.BAS, and lay both
onto a 720K FAT12 .dsk image written directly by this script.

The FictionTools dsktool was the ruled builder (design.md section 6),
but its create path segfaults on the orb machine (2026-08-13), and the
reference repository is never modified from here; a 720K MSX floppy is
plain FAT12 with a known boot-sector convention, so this stages it
deterministically in ~80 lines instead, the same builder-is-the-
authority pattern as Haumea's mk_plus3.py.

Layout (MSX 720K, media $F9): 512-byte sectors, 2 per cluster, 1
reserved, two 3-sector FATs, 112 root entries (7 sectors), data from
sector 14. The boot sector carries the BPB and a RET at offset $1E,
where the MSX disk ROM calls into it: the disk declines to boot code,
Disk BASIC comes up and runs AUTOEXEC.BAS, which fences BASIC below
$8400 and BLOADs the probe with ,R. The probe loads LOW ($8400 up),
because the disk system owns the top of RAM (HIMEM near $DE79 on a
two-drive MSX2) and loading over its work area reboot-loops the
machine; the staging buffer lives above the code and is only written
after the probe has taken over. Timestamps are fixed so the image is
byte-reproducible.
"""

import os
import struct

_HERE = os.path.dirname(os.path.abspath(__file__))
ORG = 0x8400

SECTOR = 512
CLUSTER = 2 * SECTOR
FAT_SECTORS = 3
ROOT_ENTRIES = 112
DATA_START = 1 + 2 * FAT_SECTORS + ROOT_ENTRIES * 32 // SECTOR   # 14
TOTAL_SECTORS = 1440


def bsave_wrap(raw):
    end = ORG + len(raw) - 1
    return bytes([0xFE, ORG & 0xFF, ORG >> 8, end & 0xFF, end >> 8,
                  ORG & 0xFF, ORG >> 8]) + raw


def boot_sector():
    b = bytearray(SECTOR)
    b[0:3] = b"\xEB\xFE\x90"                  # jmp $-2 over the BPB
    b[3:11] = b"ARCPROBE"
    struct.pack_into("<HBHBHHBHHHHH", b, 11,
                     SECTOR,        # bytes per sector
                     2,             # sectors per cluster
                     1,             # reserved sectors
                     2,             # FAT copies
                     ROOT_ENTRIES,
                     TOTAL_SECTORS,
                     0xF9,          # media descriptor
                     FAT_SECTORS,
                     9,             # sectors per track
                     2,             # heads
                     0, 0)          # hidden sectors
    b[0x1E] = 0xC9                  # the MSX disk ROM calls here: ret,
                                    # "not a boot disk", Disk BASIC runs
    return bytes(b)


def build(files):
    """files: [(name83, payload)] in directory order."""
    img = bytearray(TOTAL_SECTORS * SECTOR)
    img[0:SECTOR] = boot_sector()
    fat = bytearray(FAT_SECTORS * SECTOR)
    fat[0:3] = b"\xF9\xFF\xFF"

    def set_fat(cluster, value):
        off = cluster + cluster // 2
        if cluster & 1:
            fat[off] = (fat[off] & 0x0F) | ((value << 4) & 0xF0)
            fat[off + 1] = (value >> 4) & 0xFF
        else:
            fat[off] = value & 0xFF
            fat[off + 1] = (fat[off + 1] & 0xF0) | ((value >> 8) & 0x0F)

    root = bytearray(ROOT_ENTRIES * 32)
    next_cluster = 2
    for i, (name, payload) in enumerate(files):
        base, _dot, ext = name.partition(".")
        first = next_cluster
        clusters = max(1, -(-len(payload) // CLUSTER))
        for k in range(clusters):
            c = first + k
            set_fat(c, 0xFFF if k == clusters - 1 else c + 1)
            at = (DATA_START + (c - 2) * 2) * SECTOR
            img[at:at + CLUSTER] = payload[k * CLUSTER:(k + 1) * CLUSTER] \
                .ljust(CLUSTER, b"\x00")[:CLUSTER]
        next_cluster = first + clusters
        e = i * 32
        root[e:e + 11] = (base.ljust(8) + ext.ljust(3)).encode("ascii")
        root[e + 11] = 0x20                            # archive
        struct.pack_into("<HHHL", root, e + 22,
                         0x0000, 0x5B0D,               # 2025-08-13, 00:00
                         first, len(payload))
    img[SECTOR:SECTOR + len(fat)] = fat
    img[SECTOR * 4:SECTOR * 4 + len(fat)] = fat        # second copy
    img[SECTOR * 7:SECTOR * 7 + len(root)] = root
    return bytes(img)


def main():
    raw = open(os.path.join(_HERE, "probe.bin"), "rb").read()
    probe = bsave_wrap(raw)
    autoexec = b'10 CLEAR 200,&H83FF\r\n20 BLOAD"PROBE.BIN",R\r\n\x1a'
    img = build([("AUTOEXEC.BAS", autoexec), ("PROBE.BIN", probe)])
    out = os.path.join(_HERE, "probe.dsk")
    with open(out, "wb") as f:
        f.write(img)
    end = ORG + len(raw) - 1
    print(f"probe.dsk ({len(img)} bytes, 720K FAT12): AUTOEXEC.BAS "
          f"({len(autoexec)}B) + PROBE.BIN ({len(probe)}B, "
          f"BSAVE ${ORG:04X}-${end:04X} exec ${ORG:04X})")


if __name__ == "__main__":
    main()
