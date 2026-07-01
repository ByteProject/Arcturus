# test_directions.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Direction words live in the language layer as `direction` declarations, so a
language pack localizes them. They parse into world.directions and drive
movement; a custom word walks its direction on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def test_direction_decl_populates_world():
    src = 'direction north "norte", "n"\ndirection in "in"\n'
    world = analyze(parse(src))
    assert world.directions["norte"] == "north"
    assert world.directions["n"] == "north"
    assert world.directions["in"] == "in"  # a keyword works as the property


def test_unknown_direction_is_rejected():
    from arcturus.errors import ArcError
    with pytest.raises(ArcError):
        analyze(parse('direction sideways "sideways"\n'))


GAME = (
    'game\n    title "N"\n    start plaza\n'
    'room plaza\n    name "Plaza"\n    desc "A plaza."\n    north mercado\n'
    'room mercado\n    name "Mercado"\n    desc "A market."\n    south plaza\n'
    'direction north "norte", "n"\ndirection south "sur", "s"\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_custom_direction_word_walks_on_frotz(tmp_path):
    story = tmp_path / "n.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="norte\nsur\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Mercado" in out  # norte moved north
    assert out.count("Plaza") >= 2  # sur moved back
