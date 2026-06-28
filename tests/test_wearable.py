# test_wearable.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Wearing and removing (B4 polish): wear refuses a second time, inventory tags a
worn item, and disrobe/remove takes it off. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Wear Test"\n'
    '    start hall\n'
    'room hall\n'
    '    name "The Hall"\n'
    '    desc "A hall."\n'
    'thing scarf in player\n'
    '    name "wool scarf"\n'
    '    words wool, scarf\n'
    '    wearable\n'
)


def test_wearable_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_wear_remove_on_frotz(tmp_path):
    story = tmp_path / "w.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="wear scarf\ni\nwear scarf\ndisrobe scarf\ni\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You put it on." in out  # first wear
    assert "wool scarf (worn)" in out  # inventory tags the worn item
    assert "You're already wearing that." in out  # second wear refused
    assert "You take it off." in out  # disrobe removes it
    # after removal, inventory shows it without the worn tag
    tail = out.rsplit("You take it off.", 1)[1]
    assert "wool scarf" in tail and "wool scarf (worn)" not in tail
