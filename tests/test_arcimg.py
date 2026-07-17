# test_arcimg.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arcimg, the arc_image preparation tool: the stdlib paths, which are the ones
a pixel artist actually uses (Pillow is only reached to resize or convert a
non-mode source, and is not asserted here). Covers packing numbered PNGs into an
.arcres pack that the interpreter can read, the prep fast-path that copies an
already-sized PNG with no Pillow, and info reporting."""

import importlib.util
import os
import struct
import zlib
import zipfile

import pytest

# Load tools/arcimg.py directly: tools/ is a script directory, not a package.
_ARCIMG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "arcimg.py"
)
_spec = importlib.util.spec_from_file_location("arcimg", _ARCIMG)
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)


def _make_png(path, w, h, rgb=(10, 20, 30)):
    """A tiny solid-colour PNG, no third-party libraries."""
    raw = bytearray()
    row = bytes(rgb) * w
    for _ in range(h):
        raw.append(0)
        raw += row

    def chunk(tag, data):
        c = tag + data
        return (struct.pack(">I", len(data)) + c
                + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def test_png_size_reads_the_header():
    # The stdlib size read, the basis for validation and the prep fast-path.
    assert arcimg._png_size_bytes(b"not a png") is None
    p = "x.png"
    # Round-trips a real header through a temp file below; here just the bytes.
    data = bytearray(b"\x89PNG\r\n\x1a\n")
    data += struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 320, 96)
    assert arcimg._png_size_bytes(bytes(data)) == (320, 96)


def test_numbered_id():
    assert arcimg._numbered_id("8.png") == 8
    assert arcimg._numbered_id("/a/b/12.PNG") == 12
    assert arcimg._numbered_id("cellar.png") is None
    assert arcimg._numbered_id("8.gif") is None


def test_pack_zips_numbered_pngs(tmp_path):
    # A directory of numbered PNGs packs into an .arcres the interpreter reads.
    imgs = tmp_path / "images"
    imgs.mkdir()
    _make_png(imgs / "1.png", 320, 96)
    _make_png(imgs / "2.png", 320, 72)
    _make_png(imgs / "notes.txt.png", 320, 96)  # not numbered: ignored below
    (imgs / "readme.txt").write_text("ignore me")
    pack = tmp_path / "game.arcres"

    rc = arcimg.main(["pack", str(imgs), "-o", str(pack)])
    assert rc == 0
    assert zipfile.is_zipfile(pack)
    with zipfile.ZipFile(pack) as z:
        names = sorted(z.namelist())
    assert names == ["1.png", "2.png"]  # numbered only, keyed by id


def test_pack_round_trips_into_the_interpreter(tmp_path):
    # The pack the interpreter side reads: <id>.png entries loadable by id.
    imgs = tmp_path / "images"
    imgs.mkdir()
    _make_png(imgs / "5.png", 320, 96, (1, 2, 3))
    pack = tmp_path / "g.arcres"
    arcimg.main(["pack", str(imgs), "-o", str(pack)])
    with zipfile.ZipFile(pack) as z:
        data = z.read("5.png")
    assert arcimg._png_size_bytes(data) == (320, 96)


def test_pack_rejects_a_non_png(tmp_path):
    bad = tmp_path / "3.png"
    bad.write_bytes(b"this is not a png")
    rc = arcimg.main(["pack", str(bad), "-o", str(tmp_path / "out.arcres")])
    assert rc == 2
    assert not (tmp_path / "out.arcres").exists()


def test_prep_fast_path_copies_a_mode_sized_png(tmp_path):
    # A PNG already at the exact mode size is numbered and copied, no Pillow.
    src = tmp_path / "opening.png"
    _make_png(src, 320, 96)
    out = tmp_path / "out"
    rc = arcimg.main(["prep", str(src), "--id", "8", "--mode", "daad",
                      "-o", str(out)])
    assert rc == 0
    assert arcimg._png_size(str(out / "8.png")) == (320, 96)


def test_prep_infocom_mode_size(tmp_path):
    src = tmp_path / "s.png"
    _make_png(src, 320, 72)
    out = tmp_path / "o"
    arcimg.main(["prep", str(src), "--id", "1", "--mode", "infocom", "-o", str(out)])
    assert arcimg._png_size(str(out / "1.png")) == (320, 72)


def test_info_lists_a_pack(tmp_path, capsys):
    imgs = tmp_path / "i"
    imgs.mkdir()
    _make_png(imgs / "1.png", 320, 96)
    _make_png(imgs / "2.png", 320, 72)
    pack = tmp_path / "g.arcres"
    arcimg.main(["pack", str(imgs), "-o", str(pack)])
    capsys.readouterr()  # clear the pack output
    rc = arcimg.main(["info", str(pack)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "2 pictures" in out
    assert "daad" in out and "infocom" in out


def test_crop_to_ratio_is_pure_geometry():
    # No Pillow needed for the geometry: a stub with a .size and .crop() proves
    # the centre-crop math (too-wide trims the sides to the target aspect).
    class Stub:
        def __init__(self, size):
            self.size = size
            self.cropped = None

        def crop(self, box):
            self.cropped = box
            return self

    wide = Stub((640, 96))          # 20:3, wider than daad's 10:3
    arcimg._crop_to_ratio(wide, 320, 96)
    # target 10:3 -> keep height 96, width 320, centred: x from (640-320)/2.
    assert wide.cropped == (160, 0, 480, 96)


# -- ZX0W (codec 3): the write-only-video window ------------------------------

def _ring_decompress(blob, window=256):
    """The real zx0_decompress, re-plumbed the way a write-only-video machine
    must run it: output goes to a screen the decoder never reads, and every
    back-reference is served from a ring holding only the last `window`
    output bytes. Asserts no offset exceeds the ring: the proof that one
    page of RAM suffices to decode a ZX0W stream."""
    screen = bytearray()
    ring = bytearray(window)
    wpos = 0
    pos = 0
    mask = 0
    bitv = 0
    back = False
    last_byte = 0
    last_offset = 1

    def read_byte():
        nonlocal pos, last_byte
        last_byte = blob[pos]
        pos += 1
        return last_byte

    def read_bit():
        nonlocal mask, bitv, back
        if back:
            back = False
            return last_byte & 1
        mask >>= 1
        if mask == 0:
            mask = 128
            bitv = read_byte()
        return 1 if bitv & mask else 0

    def gamma(inv):
        v = 1
        while not read_bit():
            v = (v << 1) | (read_bit() ^ inv)
        return v

    def emit(b):
        nonlocal wpos
        screen.append(b)          # the write-only screen
        ring[wpos % window] = b   # the one readable page
        wpos += 1

    def emit_ref():
        assert last_offset <= window, (
            f"offset {last_offset} exceeds the {window}-byte ring")
        emit(ring[(wpos - last_offset) % window])

    state = "lit"
    while True:
        if state == "lit":
            for _ in range(gamma(0)):
                emit(read_byte())
            state = "new" if read_bit() else "last"
        elif state == "last":
            for _ in range(gamma(0)):
                emit_ref()
            state = "new" if read_bit() else "lit"
        else:
            v = gamma(1)
            if v == 256:
                return bytes(screen)
            last_offset = v * 128 - (read_byte() >> 1)
            back = True
            for _ in range(gamma(0) + 1):
                emit_ref()
            state = "new" if read_bit() else "lit"


def test_zx0w_round_trips_and_fits_the_ring():
    import random
    rnd = random.Random(7)
    # Bitmap-like data: strong row correlation at pitch 80 (a TRS-80 band).
    pitch, rows = 80, 24
    data = bytearray(rnd.randrange(256) for _ in range(pitch))
    for r in range(1, rows):
        row = bytearray(data[(r - 1) * pitch:r * pitch])
        for _ in range(8):  # sparse changes per row
            row[rnd.randrange(pitch)] = rnd.randrange(256)
        data += row
    raw = bytes(data)
    packed = arcimg.zx0w_compress(raw)
    # 1. The bitstream IS zx0: the standard decoder reads it unchanged.
    assert arcimg.zx0_decompress(packed) == raw
    # 2. A ring decoder with only 256 readable bytes reproduces it too.
    assert _ring_decompress(packed, 256) == raw


def test_plain_zx0_can_exceed_the_ring():
    # The counter-proof: data whose only matches sit far apart compresses
    # with big offsets under plain ZX0, and the ring decoder refuses it.
    block = bytes(range(256)) + bytes(range(255, -1, -1))
    raw = block + b"\x00" * 700 + block
    packed = arcimg.zx0_compress(raw)
    assert arcimg.zx0_decompress(packed) == raw
    try:
        _ring_decompress(packed, 256)
    except AssertionError:
        pass  # expected: an offset beyond the ring
    else:
        raise AssertionError("plain zx0 unexpectedly fit the 256 ring")


def test_zx0w_is_a_registered_codec():
    raw = bytes(range(256)) * 4
    blob = arcimg.write_arc(1, 0, 64, 16, 5, [(1, 0, raw)],
                            codec=arcimg.CODEC_ZX0W)
    head, sections = arcimg.read_arc(blob)
    assert head["codec"] == arcimg.CODEC_ZX0W
    assert sections[0][2] == raw
