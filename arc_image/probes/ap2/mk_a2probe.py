# mk_a2probe.py - lay the Apple II probe onto a bootable 140K .dsk
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.

"""Build probe.dsk: qboot in track 0, the assembled probe from track 1,
nothing else. Pure Python, stdlib only, deterministic output (identical
inputs give an identical image), the BuildTools doctrine.

PROBE FURNITURE, NOT A GAME PIPELINE. This lays ONE binary behind ONE
bootloader so the blueprint can be verified on real hardware and in
AppleWin; shipping games on Apple II disks is the interpreter's own
business, in BuildTools, later and elsewhere (the B12 boundary). The
name says so: never mk_dsk/mk_disk, which are taken by the real
game-disk tools.

THE TWO ORDERS. A .dsk file stores each track's sixteen sectors in DOS
3.3 LOGICAL order, while the disk itself presents them in PHYSICAL
order and qboot reads physically (consecutive physical sectors land in
consecutive pages). The translation is Ferrie's own xlatsec table from
DOS33L.S, physical index to DOS logical sector:

    0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15

so the bytes for physical sector p of track t sit at file offset
(t * 16 + XLAT[p]) * 256.

TRACK 0 IS THE LOADER'S. The Disk II ROM reads physical sector 0 into
$0800 and runs it; that first page of qboot then reads its own two
remaining pages ($BE00, $BF00) through the ROM's read routine, and
they live on physical sectors 2 and 4 (the classic 2:1 spacing that
gives the routine time to re-arm; Ferrie's source names them by their
DOS logical numbers, $0E and $0D, which is what XLAT maps them to).
The probe payload therefore starts at track 1, physical sector 0, and
runs on physically, track by track; qboot seeks.

Run:  python3 mk_a2probe.py      (writes probe.dsk beside probe.bin)
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKS, SECTORS, SECSIZE = 35, 16, 256

# physical sector -> DOS 3.3 logical sector (Ferrie's xlatsec)
XLAT = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]

# where qboot's three pages live, physically, in track 0
QBOOT_SECTORS = [0, 2, 4]
PAYLOAD_TRACK = 1                 # matches firsttrk in qboot.s
PAYLOAD_SECTOR = 0                # matches firstsec


def _put(img, track, phys, page):
    """One 256-byte page at physical sector `phys` of `track`."""
    assert len(page) == SECSIZE
    off = (track * SECTORS + XLAT[phys]) * SECSIZE
    img[off:off + SECSIZE] = page


def build():
    qboot = open(os.path.join(HERE, "qboot.bin"), "rb").read()
    probe = open(os.path.join(HERE, "probe.bin"), "rb").read()
    img = bytearray(TRACKS * SECTORS * SECSIZE)

    # the loader: its pages in the order the assembler emitted them
    qpages = [qboot[i:i + SECSIZE].ljust(SECSIZE, b"\x00")
              for i in range(0, len(qboot), SECSIZE)]
    assert len(qpages) == len(QBOOT_SECTORS), \
        f"qboot is {len(qpages)} pages, the layout knows {len(QBOOT_SECTORS)}"
    for phys, page in zip(QBOOT_SECTORS, qpages):
        _put(img, 0, phys, page)

    # the payload, physically consecutive from track 1
    pages = [probe[i:i + SECSIZE].ljust(SECSIZE, b"\x00")
             for i in range(0, len(probe), SECSIZE)]
    n = PAYLOAD_TRACK * SECTORS + PAYLOAD_SECTOR
    assert n + len(pages) <= TRACKS * SECTORS, "the probe outgrew the disk"
    for i, page in enumerate(pages):
        _put(img, (n + i) // SECTORS, (n + i) % SECTORS, page)

    out = os.path.join(HERE, "probe.dsk")
    with open(out, "wb") as f:
        f.write(img)
    print(f"wrote {out} ({len(img)} bytes: qboot on track 0, "
          f"{len(pages)} sectors of probe from track {PAYLOAD_TRACK})")
    print(f"qboot.s must say: sectors = {len(pages)}, firsttrk = "
          f"{PAYLOAD_TRACK}, firstsec = {PAYLOAD_SECTOR}")


if __name__ == "__main__":
    build()
