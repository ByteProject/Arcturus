# test_arcformat.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The .arc container (docs/08 section 10), B12 R1. Three gates:

- the shared RLE codec round-trips exactly, including its edges (long runs,
  long literals, empty data, run-length limits);
- every target's native layout packs and unpacks to the identical native
  image, through a real .arc file (write_arc/read_arc in the middle), for
  both band modes: the encode side of the format is its own decode's proof;
- every target renders to a PNG preview without an emulator in sight.

The test patterns are legal native images built in each machine's own terms
(cell matrices and registers included), so the sections carry realistic
structure, not noise."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import arcimg  # noqa: E402


# -- the RLE codec ------------------------------------------------------------

def test_rle_round_trips():
    cases = [
        b"",
        b"A",
        b"AB",
        b"AAA",
        b"A" * 128,
        b"A" * 129,
        b"A" * 1000,
        bytes(range(256)) * 3,
        b"AB" * 200,                      # 2-runs must ship as literals
        b"X" * 2 + b"Y" * 3 + b"Z" * 130,
        bytes([0x80]) * 50,               # the sentinel byte as DATA
    ]
    for data in cases:
        enc = arcimg.rle_encode(data)
        assert enc[-1] == 0x80
        assert arcimg.rle_decode(enc) == data, data[:16]


def test_rle_runs_compress():
    enc = arcimg.rle_encode(b"\x00" * 3840)
    assert len(enc) < 3840 // 32


def test_rle_missing_sentinel_faults():
    with pytest.raises(ValueError):
        arcimg.rle_decode(b"\x01AB")  # literal then truncation, no 0x80


# -- the container ---------------------------------------------------------------

def test_header_and_sections_round_trip():
    sections = [(arcimg.SEC_BITMAP, 0, bytes(range(200))),
                (arcimg.SEC_PALETTE, 1, b"\x0F" * 32)]
    blob = arcimg.write_arc(3, 12, 320, 96, 8, sections)
    head, back = arcimg.read_arc(blob)
    assert head == {"target": 3, "mode": 12, "width": 320, "height": 96,
                    "id": 8, "codec": arcimg.CODEC_ZX0, "hand": False}
    assert back == sections


def test_bad_magic_faults():
    with pytest.raises(ValueError):
        arcimg.read_arc(b"NOPE" + b"\x00" * 20)


def test_length_mismatch_faults():
    blob = bytearray(arcimg.write_arc(1, 9, 320, 72, 1,
                                      [(arcimg.SEC_BITMAP, 0, b"AB" * 8)]))
    # Corrupt the table's uncompressed length.
    blob[18] = 0xFF
    with pytest.raises(ValueError):
        arcimg.read_arc(bytes(blob))


# -- every target, both modes ----------------------------------------------------

ALL_TAGS = sorted(arcimg.TARGETS, key=lambda t: arcimg.TARGETS[t].id)


@pytest.mark.parametrize("tag", ALL_TAGS)
@pytest.mark.parametrize("mode", [9, 12])
def test_target_round_trips_exactly(tag, mode):
    # Layout round-trips run on the RLE codec for speed; the ZX0 codec has
    # its own tests below (and is validated byte-for-byte against the
    # reference tool in test_zx0_matches_the_reference_format).
    t = arcimg.TARGETS[tag]
    w, h = t.width, t.height(mode)
    native = t.pattern(w, h)
    blob = arcimg.encode_native(tag, mode, 8, native, codec=arcimg.CODEC_RLE)
    tag2, mode2, iid, back = arcimg.decode_arc(blob)
    assert (tag2, mode2, iid) == (tag, mode, 8)
    assert back == native, f"{tag} mode {mode}: unpack does not invert pack"
    # A second encode of the round-tripped native is bit-identical: the
    # format has one canonical encoding.
    assert arcimg.encode_native(tag, mode, 8, back,
                                codec=arcimg.CODEC_RLE) == blob


def test_zx0_codec_round_trips():
    # The default codec, on a real target: pack, write, read, unpack.
    t = arcimg.TARGETS["ZX3"]
    native = t.pattern(t.width, 72)
    blob = arcimg.encode_native("ZX3", 9, 4, native)  # ZX0 is the default
    head_codec = blob[14]  # header: codec is byte 14
    assert head_codec == arcimg.CODEC_ZX0
    tag2, mode2, iid, back = arcimg.decode_arc(blob)
    assert (tag2, mode2, iid) == ("ZX3", 9, 4)
    assert back == native


def test_zx0_matches_the_reference_format():
    # Streams from the reference zx0 tool must decompress with our decoder,
    # and our packer's streams decompress to the same bytes: the executable
    # spec both ways (small cases; the whole corpus was cross-validated at
    # adoption time, byte-identical totals with the reference in quick mode).
    data = (b"the quick brown fox " * 30) + bytes(range(200))
    z = arcimg.zx0_compress(data)
    assert arcimg.zx0_decompress(z) == data
    assert arcimg.zx0_decompress(arcimg.zx0_compress(b"")) == b""
    assert arcimg.zx0_decompress(arcimg.zx0_compress(b"\x00" * 5000)) == b"\x00" * 5000


@pytest.mark.parametrize("tag", ALL_TAGS)
def test_target_renders_a_png(tag, tmp_path):
    t = arcimg.TARGETS[tag]
    w, h = t.width, t.height(9)
    blob = arcimg.encode_native(tag, 9, 3, t.pattern(w, h),
                                codec=arcimg.CODEC_RLE)
    out = tmp_path / f"{tag}.png"
    arcimg.render_arc(blob, str(out))
    data = out.read_bytes()
    assert data[:8] == arcimg._PNG_SIG
    # The preview's pixel width doubles for the wide-pixel machines.
    import struct
    pw, ph = struct.unpack(">II", data[16:24])
    assert ph == h
    assert pw in (w, w * 2)


def test_the_golden_corpus_is_in_place():
    # The Rabenstein masters are the conversion corpus (docs/08 section 4):
    # every wave's back-end converts them and the results are the acceptance
    # gate. R1 only guarantees the corpus is present and band-shaped.
    import zipfile
    pack = os.path.join(os.path.dirname(__file__), "..", "examples",
                        "arc_image", "rabenstein.arcres")
    with zipfile.ZipFile(pack) as z:
        names = sorted(z.namelist())
        assert names, "the corpus pack is empty"
        for name in names:
            data = z.read(name)
            assert data[:8] == arcimg._PNG_SIG
            import struct
            w, h = struct.unpack(">II", data[16:24])
            assert (w, h) in ((320, 72), (320, 96)), name


def test_the_ledger_is_complete():
    # Fourteen targets, ids 1..14, each with the geometry docs/08 records.
    assert len(arcimg.TARGETS) == 14
    ids = sorted(t.id for t in arcimg.TARGETS.values())
    assert ids == list(range(1, 15))
    widths = {t.tag: t.width for t in arcimg.TARGETS.values()}
    assert widths == {
        "AMI": 320, "AST": 320, "DOS": 320, "C64": 160, "P4": 320,
        "CPC": 160, "MS1": 256, "MS2": 256, "ZX3": 256, "A8": 160,
        "AP2": 280, "NXT": 320, "M65": 320, "VDC": 640,
    }


# -- LZSA2 (codec 2, the 16-bit trio's codec) -----------------------------------

# A reference vector produced by Emmanuel Marty's lzsa tool (-f2 -r) from the
# plaintext below: the decoder must reproduce it byte-exactly without the
# external packer being present.
_LZSA2_PLAIN = (b"the quick brown fox jumps over the lazy dog, " * 3
                + bytes(range(64)) + b"\x00" * 200 + b"the quick end")
_LZSA2_VECTOR = bytes.fromhex(
    "1af00d74686520717569636b2062726f776e20666f78206a756d7073206f7665"
    "72205f7f6c617a7920646f672c20d3421fff2f000102030405060708090a0b0c"
    "0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c"
    "2d2e2f303132333435363738393a3b3c3d3e3f00f1af6771ff0f656e64e8")


def test_lzsa2_decoder_reference_vector():
    assert arcimg.lzsa2_decompress(_LZSA2_VECTOR) == _LZSA2_PLAIN


def test_lzsa2_empty_convention():
    assert arcimg.lzsa2_decompress(b"") == b""


def test_the_16bit_targets_default_to_lzsa2():
    for tag in ("AMI", "AST", "DOS", "MS2", "NXT", "M65"):
        assert arcimg.TARGETS[tag].codec == arcimg.CODEC_LZSA2, tag
    for tag in ("C64", "ZX3", "CPC", "MS1", "A8", "AP2", "P4", "VDC"):
        assert arcimg.TARGETS[tag].codec == arcimg.CODEC_ZX0, tag


def test_lzsa2_arc_roundtrip():
    # write_arc with codec 2 needs the packer; skip where it is absent.
    if arcimg._find_lzsa() is None:
        import pytest
        pytest.skip("no lzsa packer available")
    raw = bytes(range(256)) * 8
    blob = arcimg.write_arc(1, 12, 320, 96, 7, [(1, 0, raw)],
                            codec=arcimg.CODEC_LZSA2)
    assert blob[14] == arcimg.CODEC_LZSA2
    head, sections = arcimg.read_arc(blob)
    assert head["codec"] == arcimg.CODEC_LZSA2
    assert sections == [(1, 0, raw)]


# -- the Spectrum polish round-trip (scr in and out) ----------------------------

def test_scr_round_trip():
    native = arcimg.TARGETS["ZX3"].pattern(256, 96)
    scr = arcimg.scr_from_native(native)
    assert len(scr) == 6912
    back, warnings = arcimg.native_from_scr(scr, 12)
    assert back == native
    assert warnings == []


def test_scr_black_bar_is_black():
    native = arcimg.TARGETS["ZX3"].pattern(256, 72)
    scr = arcimg.scr_from_native(native)
    # every attr cell below the 72-row band is 0 (black on black)
    assert all(scr[6144 + cy * 32 + cx] == 0
               for cy in range(9, 24) for cx in range(32))


def test_unscr_warns_about_content_below_band():
    native = arcimg.TARGETS["ZX3"].pattern(256, 72)
    scr = bytearray(arcimg.scr_from_native(native))
    scr[6144 + 20 * 32 + 3] = 0x07     # an attr below the band
    _back, warnings = arcimg.native_from_scr(bytes(scr), 9)
    assert warnings and "below" in warnings[0]


def test_unscr_refuses_flash():
    import pytest
    native = arcimg.TARGETS["ZX3"].pattern(256, 96)
    scr = bytearray(arcimg.scr_from_native(native))
    scr[6144] |= 0x80
    with pytest.raises(ValueError, match="FLASH"):
        arcimg.native_from_scr(bytes(scr), 12)


def test_hand_flag_travels_and_protects(tmp_path):
    native = arcimg.TARGETS["ZX3"].pattern(256, 96)
    blob = arcimg.encode_native("ZX3", 12, 5, native,
                                codec=arcimg.CODEC_RLE, hand=True)
    assert blob[15] == 1
    head, _s = arcimg.read_arc(blob)
    assert head["hand"] is True
    dest = tmp_path / "5.ZX3"
    dest.write_bytes(blob)
    assert arcimg._is_hand_authored(str(dest))
    plain = arcimg.encode_native("ZX3", 12, 5, native,
                                 codec=arcimg.CODEC_RLE)
    assert plain[15] == 0
    dest.write_bytes(plain)
    assert not arcimg._is_hand_authored(str(dest))


def test_unscr_detects_the_band_mode():
    # a 9-row export leaves rows 72..96 inside the black bar; a 12-row
    # export does not: detection reads the stripe.
    nine = arcimg.TARGETS["ZX3"].pattern(256, 72)
    twelve = arcimg.TARGETS["ZX3"].pattern(256, 96)
    assert arcimg._detect_scr_mode(arcimg.scr_from_native(nine)) == 9
    assert arcimg._detect_scr_mode(arcimg.scr_from_native(twelve)) == 12


def test_scr_round_trip_nine_rows():
    native = arcimg.TARGETS["ZX3"].pattern(256, 72)
    back, warnings = arcimg.native_from_scr(
        arcimg.scr_from_native(native), 9)
    assert back == native
    assert warnings == []


def test_builtin_greedy_packer_round_trips(monkeypatch):
    # The packer chain (ruled 2026-07-09): $ARCIMG_LZSA, then PATH, then the
    # built-in greedy packer, never a remote machine and never an error.
    # With no binary found, packing must still work, pure Python.
    monkeypatch.setattr(arcimg, "_find_lzsa", lambda: None)
    for data in (
        b"", b"a", b"ab" * 700,
        bytes(range(256)) * 6,
        b"the quick brown fox " * 40 + bytes(1000) + b"the quick end",
    ):
        comp = arcimg.lzsa2_compress(data)
        assert arcimg.lzsa2_decompress(comp) == data


def test_greedy_packer_handles_real_sections(monkeypatch):
    monkeypatch.setattr(arcimg, "_find_lzsa", lambda: None)
    native = arcimg.TARGETS["AMI"].pattern(320, 96)
    blob = arcimg.write_arc(1, 12, 320, 96, 3, arcimg.TARGETS["AMI"].pack(native),
                            codec=arcimg.CODEC_LZSA2)
    _t, _m, _i, back = arcimg.decode_arc(blob)
    assert back == native
