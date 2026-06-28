# test_foreach.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`for each x in <object>` over the tree (B4.5c.1): a get_child / get_sibling
loop, with the loop variable bound to an object."""

import shutil
import subprocess

import pytest

from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

SRC = (
    'game\n'
    '    title "ForEach"\n'
    '    serial "260627"\n'
    '    start cave\n'
    'thing lamp in cave\n'
    '    name "lamp"\n'
    'thing key in cave\n'
    '    name "key"\n'
    'thing coin in cave\n'
    '    name "coin"\n'
    'room cave\n'
    '    name "Cave"\n'
    'on start\n'
    '    let n = 0\n'
    '    for each x in cave\n'
    '        change n to n + 1\n'
    '        say x\n'
    '    say "count:"\n'
    '    say n\n'
)


def test_for_each_compiles():
    assert generate(analyze(parse(SRC)))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_for_each_walks_tree_children(tmp_path):
    story = tmp_path / "fe.z5"
    story.write_bytes(generate(analyze(parse(SRC))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    # Each child is named (object-typed loop var) and there are three of them.
    for word in ("lamp", "key", "coin"):
        assert word in out
    assert "count:" in out and "3" in out
