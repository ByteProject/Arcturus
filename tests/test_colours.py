# test_colours.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Z-machine colours (docs/01 section 16): the zcolor statement, the coloured
say, the compile-time colour-name check, and the run-time degradation to plain
text on an interpreter without colour support."""

import shutil
import subprocess

import pytest

from arcturus import ast, cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "C"\n    start r\n'
    "on start\n"
    "    zcolor.font white\n"
    "    zcolor.background black\n"
    '    say "plain one"\n'
    '    say.yellow "the emphasized line"\n'
    '    say "plain two"\n'
    'room r\n    name "R"\n    desc "A room."\n'
)


def test_parse_shapes():
    prog = parse(GAME)
    handler = next(d for d in prog.decls if isinstance(d, ast.Handler))
    zc = [s for s in handler.body if isinstance(s, ast.ZColor)]
    assert [(s.target, s.colour) for s in zc] == [("font", "white"), ("background", "black")]
    says = [s for s in handler.body if isinstance(s, ast.Say)]
    assert [s.colour for s in says] == [None, "yellow", None]


def test_unknown_colour_is_a_parse_error():
    with pytest.raises(ArcError) as e:
        parse('game\n    title "C"\n    start r\non start\n    say.purple "x"\n')
    assert "unknown colour 'purple'" in str(e.value)
    with pytest.raises(ArcError) as e:
        parse('game\n    title "C"\n    start r\non start\n    zcolor.pen white\n')
    assert "not a zcolor target" in str(e.value)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_colours_degrade_to_plain_text_on_frotz(tmp_path):
    # dfrotz reports no colour support in the header, so every colour operation
    # is skipped at run time and the three lines print as plain text, in order.
    story = tmp_path / "c.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="quit\ny\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "plain one" in out
    assert "the emphasized line" in out
    assert "plain two" in out
