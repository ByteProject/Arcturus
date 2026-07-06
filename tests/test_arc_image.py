# test_arc_image.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arc_image (B11), the compiler and degradation half: a room's `arc_image
"name"` property becomes a numeric resource id, the room describer draws it
behind a runtime pictures-available guard, and the whole path folds away in a
game with no pictures. The story stays a conformant z5 file: it runs unchanged,
text-only, on a standard interpreter (dfrotz would HALT if it decoded the
custom opcode, so a clean run proves the guard keeps it unreachable). Rendering
is Actaea's GUI, tested there."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

# 0xBE is the extended-opcode marker; 0x20 is draw_image's EXT number. The pair
# is the opcode's on-disk signature, so its presence/absence in the story bytes
# is a direct check of the compile-time fold.
DRAW_IMAGE = b"\xbe\x20"

IMG = (
    'game\n    title "Img"\n    author "T"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A bare hall."\n'
    '    arc_image "cellar"\n    north yard\n'
    'room yard\n    name "The Yard"\n    desc "Open sky."\n'
    '    arc_image "forest"\n    south hall\n'
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


def test_names_become_stable_ids():
    w = analyze(cosmos.combined_program(parse(IMG)))
    assert w.images == {"cellar": 1, "forest": 2}
    # The slot holds the id (a number), not a string address.
    from arcturus import ast
    val = w.objects["hall"].props["arc_image"].values[0]
    assert isinstance(val, ast.Number) and val.value == 1
    assert w.properties["arc_image"].type == "number"


def test_a_non_string_image_is_a_clear_error():
    from arcturus.errors import ArcError
    src = (
        'game\n    title "Bad"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x"\n    arc_image 7\n'
    )
    with pytest.raises(ArcError, match="picture name in quotes"):
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
