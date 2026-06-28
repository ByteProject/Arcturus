# test_cosmos.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Cosmos-compilation pipeline (B4.5b, piece 3): the bundled cosmos/*.prelude
sources are compiled together with the game, and the game can call into them."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def test_prelude_sources_present():
    srcs = cosmos.prelude_sources()
    assert "core.prelude" in srcs
    assert "block cosmos_ready" in srcs["core.prelude"]


def test_combined_program_prepends_cosmos():
    game = parse('on start\n    say "hi"\nroom r\n    name "r"\n')
    combined = cosmos.combined_program(game)
    # The combined program has more declarations than the game alone.
    assert len(combined.decls) > len(game.decls)


GAME = (
    'game\n'
    '    title "Cosmos"\n'
    '    serial "260627"\n'
    '    start r\n'
    'on start\n'
    '    say "ready:"\n'
    '    say cosmos_ready()\n'
    'room r\n'
    '    name "Room"\n'
)


def test_game_calling_cosmos_compiles():
    world = analyze(cosmos.combined_program(parse(GAME)))
    assert generate(world)[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_game_calls_cosmos_block_on_frotz(tmp_path):
    world = analyze(cosmos.combined_program(parse(GAME)))
    story = tmp_path / "c.z5"
    story.write_bytes(generate(world))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "ready:" in out and "1" in out  # cosmos_ready() returned 1
