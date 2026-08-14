# test_arcconvert.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""B12 R2, wave 1: the master-to-native converters (AMI, AST, DOS) over the
golden corpus (the 21 Rabenstein masters). The invariants:

- every conversion encodes to a .arc that round-trips exactly;
- DOS and AST reproduce these masters bit-exact (the art is ST-class and
  sits on the 3-bit and 6-bit gun grids); AMI differs only by the 4-bit gun
  snap, bounded per channel by half a 4-bit step;
- the ST text contract holds: entry 0 is the darkest color, entry 15 is a
  readable light ink, on every picture;
- a wrong-shaped PNG is refused with the band-shape message."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import arcimg  # noqa: E402

MASTERS = os.path.join(os.path.dirname(__file__), "..", "arc_image", "masters")
ALL = sorted((n for n in os.listdir(MASTERS) if n.endswith(".png")),
             key=lambda s: int(s.split(".")[0]))
# The full corpus check runs on a spread; the whole set is the CLI's job.
SAMPLE = [ALL[0], ALL[2], ALL[8], ALL[15], ALL[-1]]


def _err(rows, native):
    pal = native["palette"]
    worst = 0
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            p = pal[native["pixels"][y][x]]
            worst = max(worst, max(abs(a - b) for a, b in zip(c, p)))
    return worst


@pytest.mark.parametrize("name", SAMPLE)
def test_ast_and_dos_are_bit_exact_on_the_corpus(name):
    path = os.path.join(MASTERS, name)
    rows = arcimg._read_png(path)
    for tag in ("AST", "DOS"):
        _mode, native = arcimg.convert_master(path, tag)
        assert _err(rows, native) == 0, f"{tag} {name}"


@pytest.mark.parametrize("name", SAMPLE)
def test_ami_differs_only_by_the_gun_snap(name):
    path = os.path.join(MASTERS, name)
    rows = arcimg._read_png(path)
    _mode, native = arcimg.convert_master(path, "AMI")
    assert _err(rows, native) <= 9  # half a 4-bit step, rounded up


@pytest.mark.parametrize("name", SAMPLE)
def test_conversions_round_trip_through_the_container(name):
    path = os.path.join(MASTERS, name)
    iid = int(name.split(".")[0])
    for tag in ("AMI", "AST", "DOS"):
        mode, native = arcimg.convert_master(path, tag)
        blob = arcimg.encode_native(tag, mode, iid, native,
                                    codec=arcimg.CODEC_RLE)
        tag2, mode2, iid2, back = arcimg.decode_arc(blob)
        assert (tag2, mode2, iid2) == (tag, mode, iid)
        assert back == native


def test_the_st_text_contract():
    for name in ALL:
        _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "AST")
        pal = native["palette"]
        assert len(pal) == 16
        luma = lambda c: 2 * c[0] + 4 * c[1] + c[2]
        assert luma(pal[15]) >= 4 * 255, name          # a readable ink
        # Darkest paper, judged over the colours the picture actually uses:
        # an unused slot stays hardware black, and a picture too plain to
        # use them all (the dark room's flat grey) must not fail on slots
        # no pixel references.
        used = {idx for row in native["pixels"] for idx in row} | {0}
        assert luma(pal[0]) == min(luma(pal[i]) for i in used), name


def test_wrong_shape_is_refused(tmp_path):
    bad = tmp_path / "9.png"
    arcimg._write_png(str(bad), [[(1, 2, 3)] * 100 for _ in range(50)])
    with pytest.raises(ValueError, match="320x72 or 320x96"):
        arcimg.convert_master(str(bad), "AMI")


def test_unwaved_target_says_so():
    with pytest.raises(ValueError, match="wave order"):
        arcimg.convert_master(os.path.join(MASTERS, ALL[0]), "M65")


# -- the gradient path (the stresstest class) ---------------------------------

STRESS = os.path.join(os.path.dirname(__file__), "..", "arc_image",
                      "stresstest", "beach.png")


def test_flat_and_gradient_masters_are_told_apart():
    flat = arcimg._read_png(os.path.join(MASTERS, ALL[0]))
    assert not arcimg._gradient_class(flat)
    assert arcimg._gradient_class(arcimg._read_png(STRESS))


def test_gradient_master_converts_and_round_trips():
    rows = arcimg._read_png(STRESS)
    for tag, budget in (("AMI", 32), ("AST", 16), ("DOS", 256)):
        native = arcimg._CONVERTERS[tag](rows)
        assert len(native["palette"]) == budget
        blob = arcimg.encode_native(tag, 12, 100, native,
                                    codec=arcimg.CODEC_RLE)
        _t, _m, _i, back = arcimg.decode_arc(blob)
        assert back == native, tag


def test_gradient_master_is_dithered_flat_art_is_not():
    rows = arcimg._read_png(STRESS)
    assert arcimg._dither_amount(rows, 16) > 0
    flat = arcimg._read_png(os.path.join(MASTERS, ALL[0]))
    assert arcimg._dither_amount(flat, 16) == 0


# -- wave 2: the cell class -----------------------------------------------------

@pytest.mark.parametrize("name", SAMPLE)
def test_cell_targets_convert_and_round_trip(name):
    path = os.path.join(MASTERS, name)
    iid = int(name.split(".")[0])
    for tag in ("C64", "ZX3", "CPC"):
        mode, native = arcimg.convert_master(path, tag)
        blob = arcimg.encode_native(tag, mode, iid, native,
                                    codec=arcimg.CODEC_RLE)
        tag2, mode2, iid2, back = arcimg.decode_arc(blob)
        assert (tag2, mode2, iid2) == (tag, mode, iid)
        assert back == native, tag


def test_c64_cells_respect_the_hardware():
    # Every 4x8 cell uses at most the background plus its three cell colors,
    # by construction: the pixel codes are 2-bit; the real check is that the
    # background register is one of the fixed 16 and the matrices are bytes.
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, ALL[0]), "C64")
    assert 0 <= native["regs"][0] <= 15
    assert all(0 <= b <= 255 for b in native["screen"])
    assert all(0 <= b <= 15 for b in native["color"])
    assert all(0 <= p <= 3 for row in native["pixels"] for p in row)


def test_zx3_attrs_are_legal():
    # Ink and paper share the bright level by construction; the attribute
    # byte never sets flash and always parses back to the palette.
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, ALL[0]), "ZX3")
    for attr in native["attrs"]:
        assert attr & 0x80 == 0  # no flash
    assert all(p in (0, 1) for row in native["pixels"] for p in row)


def test_cpc_inks_are_in_the_cube():
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, ALL[0]), "CPC")
    assert len(native["palette"]) == 16
    assert all(0 <= i <= 26 for i in native["palette"])


# THE CPC IS FROZEN (Stefan's ruling, 2026-07-23: "WE ARE NOT TOUCHING
# CPC AGAIN"). The corpus at arcimg 1.19.1 is his approved "genuinely
# perfect" build; these digests pin its exact output bytes on
# representative scenes. If ANY refactor of the shared pipeline
# (_reduce_master, _map_pixels_diffusion, _express, _convert_cpc)
# changes a digest, this test fails and the change must instead go
# into a target-private variant. That is the mechanism behind the
# ruling that expression policy is per target: the CPC keeps the exact
# path it was approved with.
_CPC_GOLDEN = {
    "2.png": "1524361bafdcfa78",
    "8.png": "bd676aa84d3b5c69",
    "10.png": "b81616567de04cd1",
    "12.png": "8c8aa3c1b9ede1d5",
}


@pytest.mark.parametrize("name", sorted(_CPC_GOLDEN))
def test_cpc_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "CPC")
    t = arcimg.TARGETS["CPC"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _CPC_GOLDEN[name]


# The C64 derives from the frozen CPC (Stefan's ruling, 2026-07-24:
# "the derived route without any alteration was already it", the
# corpus "genuinely all good, we cracked it"). Same freeze mechanism:
# these digests pin the approved derivation.
_C64_GOLDEN = {
    "2.png": "9095c6ea9af758f0",
    "8.png": "d5c3a91195b1b947",
    "10.png": "5ff79aaf31d076bf",
    "12.png": "a2d9fb73b6d9e609",
}


@pytest.mark.parametrize("name", sorted(_C64_GOLDEN))
def test_c64_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "C64")
    t = arcimg.TARGETS["C64"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _C64_GOLDEN[name]


# The A8 converts direct from the master (Stefan's ruling and corpus
# approval, 2026-07-24: "nothing regressed. A8 is approved."). Same
# freeze mechanism as its siblings.
# Re-pinned 2026-07-24 (arcimg 1.25.0): the GTIA wheel mirror lands,
# proven on Altirra's metal by the A8 probe (gold rendered blue before
# it; hue 5 the fixed point). The mirror permutes the same fifteen hue
# angles, so the renders stayed pixel-identical to the approved corpus
# (preview PNGs byte-identical across the re-pin); only the native
# bytes re-encode for real hardware.
_A8_GOLDEN = {
    "2.png": "0388d0d5d8967397",
    "8.png": "176221ddbd350e66",
    "10.png": "8cce252fb7146a8f",
    "12.png": "2bfb5af3d3780013",
}


@pytest.mark.parametrize("name", sorted(_A8_GOLDEN))
def test_a8_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "A8")
    t = arcimg.TARGETS["A8"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _A8_GOLDEN[name]


# The Spectrum mono form as Stefan approved it (2026-08-13, "we keep
# this for Spectrum"): the C-banded pattern stipple, bright white on
# black. Color on this machine is the author's, via scr/unscr.
_ZX3_GOLDEN = {
    "2.png": "2b7cbeeff8a6a934",
    "8.png": "ecb0bb2e813e8bcf",
    "10.png": "5050b245178ddc6f",
    "12.png": "0ac51354694b2f8a",
}


@pytest.mark.parametrize("name", sorted(_ZX3_GOLDEN))
def test_zx3_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "ZX3")
    t = arcimg.TARGETS["ZX3"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _ZX3_GOLDEN[name]


# The MSX1 conversion as Stefan approved it (2026-08-12, the scoped
# third leg build): a golden proves the converter has not changed,
# never that it was right; his eye is the gate that froze these.
_MS1_GOLDEN = {
    "2.png": "643694142ea7ad10",
    "8.png": "3e6ee6e332ea3b78",
    "10.png": "d087caac7527f0b2",
    "12.png": "cbd215a159a537c1",
}


@pytest.mark.parametrize("name", sorted(_MS1_GOLDEN))
def test_ms1_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "MS1")
    t = arcimg.TARGETS["MS1"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _MS1_GOLDEN[name]


# -- wave 3: the Atari 8-bit per-line solver ------------------------------------

@pytest.mark.parametrize("name", SAMPLE)
def test_a8_converts_and_round_trips(name):
    path = os.path.join(MASTERS, name)
    iid = int(name.split(".")[0])
    mode, native = arcimg.convert_master(path, "A8")
    blob = arcimg.encode_native("A8", mode, iid, native,
                                codec=arcimg.CODEC_RLE)
    tag2, mode2, iid2, back = arcimg.decode_arc(blob)
    assert (tag2, mode2, iid2) == ("A8", mode, iid)
    assert back == native


def test_a8_respects_the_hardware():
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, ALL[0]), "A8")
    h = native["h"]
    assert len(native["lines"]) == 4 * h  # four registers per scanline
    # GTIA does not decode luminance bit 0: every table byte is even.
    assert all(b & 1 == 0 and 0 <= b <= 255 for b in native["lines"])
    assert all(0 <= p <= 3 for row in native["pixels"] for p in row)


def test_a8_registers_are_honest_gtia():
    # The A8 converts DIRECT from the master (Stefan's ruling and corpus
    # approval, 2026-07-24; the C64-inheritance doctrine is retired).
    # Every register byte is a real GTIA colour (even luminance bit,
    # GTIA does not decode bit 0), and the table holds one palette per
    # 8-line segment, replayed per line.
    for name in (ALL[0], "8.png"):
        _mode, native = arcimg.convert_master(os.path.join(MASTERS, name),
                                              "A8")
        assert all(b & 1 == 0 for b in native["lines"]), name
        lines = native["lines"]
        for y in range(native["h"]):
            seg = (y // 8) * 8
            assert lines[y * 4:(y + 1) * 4] == \
                lines[seg * 4:seg * 4 + 4], name


def test_a8_line_table_is_quiet():
    # The whole point of the solver: line palettes drawn from one stable
    # global set, held and role-assigned line to line, so flat regions emit
    # IDENTICAL table rows (no shimmer on screen, runs for ZX0). On the
    # corpus the table holds 21-29 distinct rows per 96 lines with about
    # 60 exact repeats; the bounds are loose thirds of that.
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, ALL[0]), "A8")
    h = native["h"]
    rows = [tuple(native["lines"][y * 4:(y + 1) * 4]) for y in range(h)]
    assert len(set(rows)) < h // 3
    assert sum(1 for y in range(1, h) if rows[y] == rows[y - 1]) > h // 3


# -- the salient hint (the moon ruling, arc_image/reference/design.md) --------------------------------

def _disc_master(tmp_path):
    """A synthetic night scene: dark teal sky, darker ground band, and a
    pale disc that no fixed palette separates from the sky by hue alone."""
    rows = []
    for y in range(96):
        row = []
        for x in range(320):
            if y > 64:
                row.append((20, 30, 20))
            else:
                row.append((0, 120, 120))
            if (x - 160) ** 2 + (y - 32) ** 2 <= 14 * 14:
                row[-1] = (0, 160, 220)
        rows.append(row)
    p = tmp_path / "3.png"
    arcimg._write_png(str(p), rows)
    (tmp_path / "3.hint").write_text('{"salient": [[160, 32, 14]]}\n')
    return str(p)


def _disc_separation(rendered):
    """Mean colour inside the fixture disc vs its surrounding ring."""
    inside, ring = [], []
    for y, row in enumerate(rendered):
        for x, c in enumerate(row):
            d2 = (x - 160) ** 2 + (y - 32) ** 2
            if d2 <= 100:
                inside.append(c)
            elif 400 <= d2 <= 784:
                ring.append(c)
    mean = lambda px: tuple(sum(c[k] for c in px) / len(px)
                            for k in range(3))
    return arcimg._dist(mean(inside), mean(ring))


def test_zx3_ignores_the_hint_and_keeps_a_bright_disc(tmp_path):
    # The derivation round (2026-08-12): the ZX3 derives from MSX1 and
    # obeys Stefan's sidecar rule, the hint is an author's last resort,
    # never consulted by our conversions. Byte-equality with and without
    # the sidecar is the contract now.
    path = _disc_master(tmp_path)
    _mode, with_hint = arcimg.convert_master(path, "ZX3")
    os.remove(os.path.splitext(path)[0] + ".hint")
    _mode, without = arcimg.convert_master(path, "ZX3")
    assert with_hint == without
    # And salience must still be earned from the picture itself: a
    # GENUINELY bright disc (the corpus moon's class, above the moon
    # rule's luma bar) promotes to white with no hint anywhere. The dim
    # teal disc of _disc_master is a KNOWN open case on the TMS-derived
    # path, the same-hue luminance-contrast class as picture 7's two
    # blues; it merges with its sky and this test does not pretend
    # otherwise.
    rows = []
    for y in range(96):
        row = []
        for x in range(320):
            row.append((20, 30, 20) if y > 64 else (0, 120, 120))
            if (x - 160) ** 2 + (y - 32) ** 2 <= 14 * 14:
                row[-1] = (200, 255, 255)
        rows.append(row)
    bright = tmp_path / "9.png"
    arcimg._write_png(str(bright), rows)
    _mode, native = arcimg.convert_master(str(bright), "ZX3")
    rendered = arcimg.TARGETS["ZX3"].render(native, native["w"],
                                            native["h"])
    whites = sum(1 for row in rendered for c in row
                 if c[0] > 200 and c[1] > 200 and c[2] > 200)
    assert whites > 100


def test_c64_disc_survives_without_a_hint(tmp_path):
    # The diffusion doctrine (Stefan's reboot, 2026-07-23): the C64 does
    # not consult the hint sidecar; salience lives in the intermediate
    # (_protect_extremes guarantees the brightest cluster an entry). The
    # invariant is DISTINCTNESS, not forced white: the disc must render
    # apart from its sky. Measured separation on the fixture is ~85000
    # _dist units; the floor leaves a wide margin.
    path = _disc_master(tmp_path)
    _mode, native = arcimg.convert_master(path, "C64")
    rendered = arcimg.TARGETS["C64"].render(native, native["w"],
                                            native["h"])
    assert _disc_separation(rendered) > 20000


def test_a8_ignores_a_hand_c64(tmp_path):
    # Retired doctrine, pinned in the negative: the A8 converts direct
    # from the master (2026-07-24) and a hand-authored .C64 no longer
    # shapes it; the job accepts the argument for compatibility and
    # produces the same bytes as the plain conversion.
    path = os.path.join(MASTERS, ALL[0])
    mode, c64 = arcimg.convert_master(path, "C64")
    hand = tmp_path / f"{ALL[0].split('.')[0]}.C64"
    hand.write_bytes(arcimg.encode_native("C64", mode, 0, c64, hand=True))
    dest = tmp_path / "0.A8"
    res = arcimg._convert_job((0, path, "A8", str(dest), None, None,
                               str(hand)))
    assert not isinstance(res, str), res
    _t, _m, _i, native = arcimg.decode_arc(dest.read_bytes())
    _mode2, direct = arcimg.convert_master(path, "A8")
    assert native == direct


def test_a8_disc_survives(tmp_path):
    # Direct doctrine: no hint, the moon rule gives the strip's
    # brightest cluster a hard register, and the disc renders apart
    # from its sky (measured ~15900 on the fixture; disc and sky are
    # cyan cousins and the GTIA gamut compresses them, so the floor
    # sits at 10000).
    path = _disc_master(tmp_path)
    _mode, native = arcimg.convert_master(path, "A8")
    rendered = arcimg.TARGETS["A8"].render(native, native["w"],
                                           native["h"])
    assert _disc_separation(rendered) > 10000


def test_no_hint_no_change(tmp_path):
    # The same master without its sidecar must not sprout white pixels.
    path = _disc_master(tmp_path)
    os.remove(str(tmp_path / "3.hint"))
    _mode, native = arcimg.convert_master(path, "C64")
    rendered = arcimg.TARGETS["C64"].render(native, native["w"], native["h"])
    whites = sum(1 for row in rendered for c in row
                 if c[0] > 200 and c[1] > 200 and c[2] > 200)
    assert whites == 0


def test_zx3_attrs_are_hardware_legal():
    # Every attribute byte: ink and paper 0..7, and the pair must be
    # honest about the shared bright bit by construction (bit 6 only).
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, "8.png"),
                                          "ZX3")
    for attr in native["attrs"]:
        assert attr & 0x80 == 0          # no flash
        ink, paper = attr & 7, (attr >> 3) & 7
        assert 0 <= ink <= 7 and 0 <= paper <= 7


# --- Plus/4 (P4): multicolour, a child of the frozen CPC -------------------

# The P4 corpus frozen 2026-07-25, third pin, the hardware-true one
# (arcimg 1.28.0): the re-anchored TED table (nibble 0 is black at
# every luminance; the first staircase measured one column off because
# black is invisible on black) and the crossed luminance nibble the
# conventions probe proved on xplus4. Renders 20/21 pixel-identical to
# the approved corpus (image 19: 16 pixels); the probe then verified
# mode 9, mode 12, and picture 12 pixel-exact on the emulator.
_P4_GOLDEN = {
    "2.png": "7d6ea70f0856afa0",
    "8.png": "28ce3d245b713a56",
    "10.png": "30f017e0c7e1bc8e",
    "12.png": "230ee10b9db47e97",
}


@pytest.mark.parametrize("name", sorted(_P4_GOLDEN))
def test_p4_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "P4")
    t = arcimg.TARGETS["P4"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _P4_GOLDEN[name]


def test_p4_converts_and_round_trips():
    # TED MULTICOLOUR (Stefan's rulings: hires abandoned 2026-07-23;
    # the family derives downhill from the frozen CPC, 2026-07-24).
    # The contract: 160 fat pixels, 2-bit codes, per 4x8 cell two
    # private colours plus the two global registers, byte-exact
    # round-trip through pack/unpack, and every rendered pixel a legal
    # TED colour.
    import arcimg
    rows = arcimg._read_png(os.path.join(MASTERS, "8.png"))
    native = arcimg._convert_p4(rows)
    h = native["h"]
    assert native["w"] == 160 and h in (72, 96)
    cells = (160 // 4) * (h // 8)
    assert len(native["screen"]) == cells
    assert len(native["color"]) == cells
    assert len(native["regs"]) == 2
    assert all(0 <= p <= 3 for row in native["pixels"] for p in row)
    t = arcimg.TARGETS["P4"]
    sections = t.pack(native)
    back = t.unpack([(ty, fl, bytes(pl)) for ty, fl, pl in sections], 160, h)
    assert back["pixels"] == native["pixels"]
    assert back["screen"] == native["screen"]
    assert back["color"] == native["color"]
    assert back["regs"] == native["regs"]
    rendered = t.render(native, 160, h)
    assert len(rendered) == h and len(rendered[0]) == 320  # 2:1 doubled


def test_p4_rides_the_ring_codec():
    import arcimg
    assert arcimg.TARGETS["P4"].codec == arcimg.CODEC_ZX0


# --- slice9: the mode-9 slice must shrink every plane ----------------------

def test_slice9_slices_every_plane_and_keeps_the_hand_stamp(tmp_path):
    # The ZX3 probe rebuild (2026-08-13) caught two slice9 defects at
    # once: it only knew the C64 family's planes, so a ZX3 slice kept
    # all 384 mode-12 attribute bytes (three rows of colour decoding
    # below the band, into the interpreter's text area) and an MS1
    # native (pattern/colors, no "pixels" key) crashed it outright; and
    # it dropped header byte 15, so a slice of hand art lost its
    # convert-will-never-overwrite protection.
    import argparse
    for tag in ("ZX3", "MS1"):
        _mode, native = arcimg.convert_master(os.path.join(MASTERS, "8.png"),
                                              tag)
        src = tmp_path / f"12.{tag}"
        src.write_bytes(arcimg.encode_native(tag, 12, 12, native, hand=True))
        out = tmp_path / f"9.{tag}"
        ns = argparse.Namespace(source=str(src), id=9, out=str(out))
        assert arcimg.cmd_slice9(ns) in (0, None)
        blob = out.read_bytes()
        head, secs = arcimg.read_arc(blob)
        assert head["hand"] is True, f"{tag}: the hand stamp was dropped"
        if tag == "ZX3":
            attrs = next(raw for t, _f, raw in secs if t == 4)
            assert len(attrs) == (256 // 8) * (72 // 8)
        t = arcimg.TARGETS[tag]
        tup = arcimg.decode_arc(blob)
        sliced = next(x for x in tup if isinstance(x, dict) and "w" in x)
        full = t.render(native, native["w"], native["h"])
        top = t.render(sliced, sliced["w"], sliced["h"])
        assert top == full[:len(top)], f"{tag}: the slice is not the top rows"


# --- MS2 (MSX2): Screen 5, the quantize class through the MSX window -------

_MS2_GOLDEN = {
    "2.png": "df1a005de6a95877",
    "8.png": "e6c5f6b82e636412",
    "10.png": "2cd6dd59208ba367",
    "12.png": "538fe0c4483f8d73",
}


@pytest.mark.parametrize("name", sorted(_MS2_GOLDEN))
def test_ms2_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "MS2")
    t = arcimg.TARGETS["MS2"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _MS2_GOLDEN[name]


def test_ms2_respects_the_st_text_contract():
    # 16 of 512, 3:3:3: the ST's constraint set exactly, so the same
    # guarantee: entry 0 darkest (the text paper), the last entry a
    # readable light ink, every channel on the 3-bit gun grid.
    def luma(c):
        return 2 * c[0] + 4 * c[1] + c[2]
    for n in ("2.png", "8.png"):
        _m, native = arcimg.convert_master(os.path.join(MASTERS, n), "MS2")
        pal = native["palette"]
        assert len(pal) == 16
        assert all(luma(pal[0]) <= luma(c) for c in pal[1:])
        assert luma(pal[-1]) >= 4 * 255
        legal = {round(v * 255 / 7) for v in range(8)}
        assert all(ch in legal for c in pal for ch in c)


# --- AGN (Agon Light): mode 3, the fixed RGBA2222 cube ---------------------

_AGN_GOLDEN = {
    "2.png": "0263e0cfb032ca6b",
    "8.png": "4768aa3a68c75308",
    "10.png": "784a530904c0bad1",
    "12.png": "3725c9b644d8dfc7",
}


@pytest.mark.parametrize("name", sorted(_AGN_GOLDEN))
def test_agn_output_is_frozen(name):
    import hashlib
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, name), "AGN")
    t = arcimg.TARGETS["AGN"]
    blob = b"".join(bytes(pl) for _ty, _fl, pl in t.pack(native))
    assert hashlib.sha256(blob).hexdigest()[:16] == _AGN_GOLDEN[name]


def test_agn_bytes_are_opaque_cube_members():
    # every pixel byte: alpha %11 (opaque) and channels on the 2-bit
    # cube; width doubled from the 320 master, pairs identical never
    # averaged (the C64 width rule, inverted)
    _mode, native = arcimg.convert_master(os.path.join(MASTERS, "8.png"),
                                          "AGN")
    assert native["w"] == 640
    for row in native["pixels"]:
        for p in row:
            assert (p & 0xC0) == 0xC0
    assert arcimg.TARGETS["AGN"].codec == arcimg.CODEC_RLE
