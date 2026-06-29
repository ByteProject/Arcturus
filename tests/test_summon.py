# test_summon.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The summon loader (B5.5a): a summoned .granule is parsed, its blocks are tagged
`granule` so they override a Cosmos library block of the same name, and an
unsummoned granule never enters the build. A missing granule is a clean error.
Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import ast, cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Summon"\n    start cell\n'
    'summon "custom.granule"\n'
    'room cell\n    name "The Cell"\n    desc "A bare cell."\n'
)

# A granule that reskins the standard jump message by redefining its block.
GRANULE = 'block msg_jump()\n    say "The granule jump wins."\n'


def _write_granule(tmp_path):
    (tmp_path / "custom.granule").write_text(GRANULE)
    return parse(GAME, "g.storyarc")


def test_summoned_granule_block_overrides_library(tmp_path):
    program = cosmos.combined_program(_write_granule(tmp_path), story_dir=str(tmp_path))
    # Exactly one msg_jump survives collection, and it is the granule's.
    world = analyze(program)
    jump = world.blocks["msg_jump"]
    assert jump.origin == "granule"


def test_unknown_feature_summon_is_an_error():
    program = parse('game\n    title "X"\n    start cell\nsummon bogusfeature\n'
                    'room cell\n    name "Cell"\n', "x.storyarc")
    with pytest.raises(ArcError):
        cosmos.combined_program(program)


def test_missing_granule_file_is_an_error(tmp_path):
    program = parse(GAME, "g.storyarc")  # summons custom.granule, but none on disk
    with pytest.raises(ArcError):
        cosmos.combined_program(program, story_dir=str(tmp_path))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_summoned_override_runs_on_frotz(tmp_path):
    program = cosmos.combined_program(_write_granule(tmp_path), story_dir=str(tmp_path))
    story = tmp_path / "s.z5"
    story.write_bytes(generate(analyze(program)))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="jump\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "The granule jump wins." in out  # the granule's message, not the default
