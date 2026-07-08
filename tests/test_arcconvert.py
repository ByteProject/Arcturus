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
ALL = sorted(os.listdir(MASTERS), key=lambda s: int(s.split(".")[0]))
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
        blob = arcimg.encode_native(tag, mode, iid, native)
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
        blob = arcimg.encode_native(tag, 12, 100, native)
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
        blob = arcimg.encode_native(tag, mode, iid, native)
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
