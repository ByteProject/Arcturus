# test_arc_image.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arc_image (B11), the compiler and degradation half: a room's `arc_image <id>`
property holds a numeric resource id (the author's own number, or a constant
that folds to one), the room describer draws it behind a runtime
pictures-available guard, and the whole path folds away in a game with no
pictures. The id IS the resource slot, so there is no name manifest: an aware
interpreter loads <id>.png. The story stays a conformant z5 file: it runs
unchanged, text-only, on a standard interpreter (dfrotz would HALT if it decoded
the custom opcode, so a clean run proves the guard keeps it unreachable).
Rendering is Actaea's GUI, tested there."""

import os
import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

# 0xBE is the extended-opcode marker; 0x80 is draw_image's EXT number (in the
# 128-255 range the Standard reserves for private extensions). The pair is the
# opcode's on-disk signature, so its presence/absence in the story bytes is a
# direct check of the compile-time fold.
DRAW_IMAGE = b"\xbe\x80"

# Ids named by constants (the readable way authors write them): cellar is slot
# 1, forest is slot 2, so the interpreter loads 1.png and 2.png.
IMG = (
    'constant cellar = 1\n'
    'constant forest = 2\n'
    'game\n    title "Img"\n    author "T"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A bare hall."\n'
    '    arc_image cellar\n    north yard\n'
    'room yard\n    name "The Yard"\n    desc "Open sky."\n'
    '    arc_image forest\n    south hall\n'
    'thing coin in hall\n    name "coin"\n    words coin\n'
)

NO_IMG = (
    'game\n    title "Plain"\n    author "T"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A bare hall."\n    north yard\n'
    'room yard\n    name "The Yard"\n    desc "Open sky."\n    south hall\n'
)


def _compile(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def test_image_id_is_the_authors_number():
    from arcturus import ast
    w = analyze(cosmos.combined_program(parse(IMG)))
    assert w.uses_images is True
    # The slot holds the id the author gave (through a constant), a plain number,
    # not a first-seen-assigned id and not a string address.
    hall = w.objects["hall"].props["arc_image"].values[0]
    yard = w.objects["yard"].props["arc_image"].values[0]
    assert isinstance(hall, ast.Number) and hall.value == 1
    assert isinstance(yard, ast.Number) and yard.value == 2
    assert w.properties["arc_image"].type == "number"


def test_image_id_accepts_a_bare_number():
    src = (
        'game\n    title "N"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x"\n    arc_image 8\n'
    )
    w = analyze(cosmos.combined_program(parse(src)))
    assert w.objects["hall"].props["arc_image"].values[0].value == 8
    assert w.uses_images is True


def test_a_string_image_is_a_clear_error():
    from arcturus.errors import ArcError
    src = (
        'game\n    title "Bad"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x"\n    arc_image "cellar"\n'
    )
    with pytest.raises(ArcError, match="picture id"):
        analyze(cosmos.combined_program(parse(src)))


def test_image_id_zero_is_rejected():
    from arcturus.errors import ArcError
    src = (
        'game\n    title "Bad"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x"\n    arc_image 0\n'
    )
    with pytest.raises(ArcError, match="1 or more"):
        analyze(cosmos.combined_program(parse(src)))


def test_pay_for_use_no_opcode_without_images():
    # A game with no arc_image carries no draw_image opcode at all: the whole
    # picture path folds out (any_images = 0) and DCE drops it.
    assert DRAW_IMAGE not in _compile(NO_IMG)
    # A game that uses arc_image does carry it (behind the guard).
    assert DRAW_IMAGE in _compile(IMG)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_conformant_z5_plays_text_only_on_frotz(tmp_path):
    story = tmp_path / "img.z5"
    story.write_bytes(_compile(IMG))
    out = subprocess.run(
        [_frotz(), "-p", "-w", "200", str(story)],
        input="look\nnorth\nlook\nsouth\nquit\ny\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    # It played the rooms and never faulted on the custom opcode (dfrotz would
    # print a fatal/illegal-opcode message and stop).
    assert "The Hall" in out and "The Yard" in out
    for bad in ("fatal", "illegal", "Illegal", "abort", "undefined opcode"):
        assert bad not in out


def test_runs_on_actaea_headless():
    # Actaea's headless front-end reports no picture support, so the guard skips
    # the draw and the story plays as pure text (the console/build-tools path).
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    io = CaptureIO(script=["look", "north", "look", "south", "quit", "y"])
    vm = VM(load(_compile(IMG)), io)
    vm.run(max_steps=2_000_000)
    assert "The Hall" in io.text and "The Yard" in io.text


def _run(io_cls, script):
    from actaea.loader import load
    from actaea.vm import VM
    io = io_cls(script=list(script))
    vm = VM(load(_compile(IMG)), io)
    vm.run(max_steps=2_000_000)
    return vm


def test_picture_requested_only_when_the_interpreter_can_show_it():
    # The whole capability gate, headless: a front-end that advertises picture
    # support (the header bit) makes the room draw its picture into the screen
    # model; one that does not never touches it. Same story, opposite outcome.
    from actaea.io import CaptureIO

    class PicIO(CaptureIO):
        supports_pictures = True

    # With pictures available: ending in the yard, its picture (forest = id 2)
    # is the one on screen; the mode is the game default, 9 (Infocom).
    assert _run(PicIO, ["north", "quit", "y"]).screen.image == (2, 9)
    # Back in the hall, its own picture (cellar = id 1).
    assert _run(PicIO, ["north", "south", "quit", "y"]).screen.image == (1, 9)
    # Without picture support, nothing is ever drawn.
    assert _run(CaptureIO, ["north", "quit", "y"]).screen.image is None


def test_arc_mode_flows_to_the_opcode():
    # The game's arc_mode reaches the interpreter in the draw_image mode operand,
    # so the band is sized from the mode and not the picture. `constant arc_mode
    # = 12` (DAAD) overrides the default 9 (Infocom).
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    class PicIO(CaptureIO):
        supports_pictures = True

    story = load(_compile("constant arc_mode = 12\n" + IMG))
    vm = VM(story, PicIO(script=["quit", "y"]))
    vm.run(max_steps=2_000_000)
    # Started in the hall (cellar = id 1), drawn in DAAD mode 12.
    assert vm.screen.image == (1, 12)


def test_arc_mode_must_be_a_valid_mode():
    from arcturus.errors import ArcError
    with pytest.raises(ArcError, match="arc_mode must be 9"):
        analyze(cosmos.combined_program(parse("constant arc_mode = 7\n" + IMG)))


def test_no_resource_sidecar_is_written(tmp_path):
    # The id is the resource slot, so the compiler writes NO manifest or pack
    # beside the story: pictures are delivered separately, as a --images
    # directory of numbered PNGs or an .arcres pack that arcimg builds.
    import sys
    src = tmp_path / "g.storyarc"
    src.write_text(IMG)
    story = tmp_path / "g.z5"
    subprocess.run(
        [sys.executable, "-m", "arcturus.cli", str(src), "-o", str(story)],
        capture_output=True, text=True, check=True,
    )
    assert story.exists()
    assert not (tmp_path / "g.arcres").exists()


def test_interpreter_resolves_dir_then_pack(tmp_path):
    # How a front-end finds the pictures: an explicit --images directory wins;
    # else a sibling .arcres pack; else the story's own directory.
    from actaea.__main__ import _resolve_images
    story = str(tmp_path / "g.z5")
    (tmp_path / "g.z5").write_bytes(b"x")
    # No pack, no --images: the story's own directory (the loose debug default).
    d, z = _resolve_images(story, None)
    assert d == os.path.dirname(os.path.abspath(story)) and z is None
    # A sibling .arcres pack is picked up when present.
    (tmp_path / "g.arcres").write_bytes(b"PK")
    d, z = _resolve_images(story, None)
    assert d is None and z == os.path.splitext(story)[0] + ".arcres"
    # An explicit --images directory always wins over the pack.
    d, z = _resolve_images(story, "/some/dir")
    assert d == "/some/dir" and z is None
