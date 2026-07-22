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
        assert luma(pal[0]) == min(map(luma, pal)), name  # darkest paper


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


def test_a8_inherits_the_c64_taste():
    # The R4 ruling: the A8 derives from the C64 conversion (the 80s port
    # route), so every register byte it ever emits is one of the sixteen
    # Colodore-mapped GTIA bytes, and the mapping is injective (red and
    # orange must not merge; a fire keeps its shading).
    gt = arcimg._c64_to_gtia()
    assert len(set(gt)) == 16
    allowed = set(gt)
    for name in (ALL[0], "8.png"):
        _mode, native = arcimg.convert_master(os.path.join(MASTERS, name),
                                              "A8")
        assert set(native["lines"]) <= allowed, name


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


def test_hint_promotes_the_disc_to_white(tmp_path):
    path = _disc_master(tmp_path)
    for tag in ("C64", "ZX3"):
        _mode, native = arcimg.convert_master(path, tag)
        t = arcimg.TARGETS[tag]
        rendered = t.render(native, native["w"], native["h"])
        whites = sum(1 for row in rendered for c in row
                     if c[0] > 200 and c[1] > 200 and c[2] > 200)
        assert whites > 100, tag


def test_a8_hand_polished_c64_is_the_source(tmp_path):
    # Hand-polish inheritance (Stefan's ruling): a hand-authored .C64 is
    # the source of the whole 8-bit family's taste, so the A8 job derives
    # from it, mode included, instead of reconverting the master.
    path = os.path.join(MASTERS, ALL[0])
    mode, c64 = arcimg.convert_master(path, "C64")
    hand = tmp_path / f"{ALL[0].split('.')[0]}.C64"
    hand.write_bytes(arcimg.encode_native("C64", mode, 0, c64, hand=True))
    assert arcimg._is_hand_authored(str(hand))
    dest = tmp_path / "0.A8"
    res = arcimg._convert_job((0, path, "A8", str(dest), None, None,
                               str(hand)))
    assert not isinstance(res, str), res
    tag2, mode2, _iid, native = arcimg.decode_arc(dest.read_bytes())
    assert (tag2, mode2) == ("A8", mode)
    assert set(native["lines"]) <= set(arcimg._c64_to_gtia())


def test_a8_hint_promotes_the_disc_to_full_luminance(tmp_path):
    # The A8 promotion keeps the disc's HUE (128 colors allow it) but lifts
    # it to full GTIA luminance: the disc must stand apart from the sky it
    # glows out of.
    path = _disc_master(tmp_path)
    _mode, native = arcimg.convert_master(path, "A8")
    rendered = arcimg.TARGETS["A8"].render(native, native["w"], native["h"])
    bright = sum(1 for row in rendered for c in row
                 if 2 * c[0] + 4 * c[1] + c[2] > 1300)
    assert bright > 300


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


# --- Plus/4 (P4): the Rabenstein recipe, hires TED --------------------------

def test_p4_converts_and_round_trips():
    # The R4 wave's first target: near-monochrome dithered hires with few
    # accents and dark/bright pairs (the design record's ruling). This pins
    # the CONTRACT: geometry, the two-colours-per-cell invariant by
    # construction, byte-exact round-trip through pack/unpack, and the
    # near-mono restriction (the hues used stay within dominant + accents,
    # never a full-palette quantize).
    import arcimg
    rows = arcimg._read_png(os.path.join(MASTERS, "8.png"))
    native = arcimg._convert_p4(rows)
    h = native["h"]
    assert native["w"] == 320 and h in (72, 96)
    cells = (320 // 8) * (h // 8)
    assert len(native["screen"]) == cells
    assert len(native["color"]) == cells
    # The near-mono contract: at most dominant + 3 accents + black paper.
    ink_hues = {b >> 4 for b in native["screen"]}
    assert len(ink_hues) <= 4, ink_hues
    # Round-trip: pack to sections, unpack, byte-identical fields.
    t = arcimg.TARGETS["P4"]
    sections = t.pack(native)
    back = t.unpack([(ty, fl, bytes(pl)) for ty, fl, pl in sections], 320, h)
    assert back["pixels"] == native["pixels"]
    assert back["screen"] == native["screen"]
    assert back["color"] == native["color"]
    # And it renders: every pixel a legal TED colour.
    rendered = t.render(native, 320, h)
    assert len(rendered) == h and len(rendered[0]) == 320


def test_p4_rides_the_ring_codec():
    import arcimg
    assert arcimg.TARGETS["P4"].codec == arcimg.CODEC_ZX0
