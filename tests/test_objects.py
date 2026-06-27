# test_objects.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Object-table tests (B4.3): numbering, attribute bits, the tree, and an
object-operations program that runs on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import objects
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

WORLD_SRC = (
    'thing lamp in cave\n'
    '    name "brass lamp"\n'
    '    switchable\n'
    '    lit false\n'
    'thing box in cave\n'
    '    name "wooden box"\n'
    '    value 7\n'
    'room cave\n'
    '    name "The Cave"\n'
)


def layout_of(src):
    return objects.build_layout(analyze(parse(src)))


def test_object_numbering_starts_after_player():
    layout = layout_of(WORLD_SRC)
    # player is the standard object collected first, so it is object 1.
    assert layout.obj_number["player"] == 1
    assert set(layout.obj_number) == {"player", "lamp", "box", "cave"}


def test_attribute_and_property_numbering():
    layout = layout_of(WORLD_SRC)
    # Boolean properties become attributes; value properties become properties.
    assert "switchable" in layout.attr_number
    assert "lit" in layout.attr_number
    assert "value" in layout.prop_number
    assert "name" not in layout.prop_number  # name is the short name


def test_true_boolean_sets_attribute_bit():
    layout = layout_of(WORLD_SRC)
    num = layout.obj_number["lamp"]
    entry = 63 * 2 + (num - 1) * 14
    attr = layout.attr_number["switchable"]
    byte = layout.table[entry + attr // 8]
    assert byte & (0x80 >> (attr % 8))  # switchable is set on the lamp
    # lit is false, so its bit is clear.
    lit = layout.attr_number["lit"]
    assert not (layout.table[entry + lit // 8] & (0x80 >> (lit % 8)))


def test_tree_parent_from_location():
    layout = layout_of(WORLD_SRC)
    lamp = layout.obj_number["lamp"]
    cave = layout.obj_number["cave"]
    entry = 63 * 2 + (lamp - 1) * 14
    parent = (layout.table[entry + 6] << 8) | layout.table[entry + 7]
    assert parent == cave


# -- end to end on Frotz ---------------------------------------------------

OBJ = (
    'game\n'
    '    title "Objects"\n'
    '    serial "260627"\n'
    '    start cave\n'
    '\n'
    'room cave\n'
    '    name "The Cave"\n'
    '\n'
    'thing lamp in cave\n'
    '    name "brass lamp"\n'
    '    lit false\n'
    '\n'
    'thing box in cave\n'
    '    name "wooden box"\n'
    '    value 7\n'
    '\n'
    'on start\n'
    '    now lamp is lit\n'
    '    if lamp is lit\n'
    '        say "The lamp is lit."\n'
    '    say lamp\n'
    '    say box.value\n'
    '    move lamp to box\n'
    '    if box holds lamp\n'
    '        say "In the box."\n'
)


def test_object_demo_compiles():
    data = generate(analyze(parse(OBJ)))
    assert data[0x00] == 5
    assert ((data[0x1C] << 8) | data[0x1D]) == sum(data[0x40:]) & 0xFFFF


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_object_ops_run_on_frotz(tmp_path):
    story = tmp_path / "obj.z5"
    story.write_bytes(generate(analyze(parse(OBJ))))
    result = subprocess.run(
        [_frotz(), "-p", str(story)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
    )
    out = result.stdout
    assert "The lamp is lit." in out  # set_attr + test_attr
    assert "brass lamp" in out  # print_obj
    assert "7" in out  # get_prop
    assert "In the box." in out  # insert_obj + jin
