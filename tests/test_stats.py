# test_stats.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The --stats compile report: generate() fills a stats dict with what the story
uses of each Z-machine ceiling, and the CLI prints it as the ledger."""

import os

from arcturus import cli, cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def _world(name):
    with open(os.path.join(EXAMPLES, name), encoding="utf-8") as fh:
        return analyze(cosmos.combined_program(parse(fh.read(), name)))


def test_generate_fills_stats():
    stats = {}
    img = generate(_world("cloak-of-darkness.storyarc"), stats=stats)
    # The story numbers agree with the image itself.
    assert stats["story_bytes"] == len(img)
    assert stats["story_max"] == 256 * 1024  # z5
    assert stats["readable_bytes"] < stats["readable_max"] == 65536
    # Every ceilinged value sits within its ceiling.
    assert 0 < stats["attributes"] <= stats["attributes_max"] == 48
    assert 0 < stats["properties"] <= stats["properties_max"]
    assert 0 < stats["globals"] <= stats["globals_max"] == 240
    assert stats["abbrevs"] <= stats["abbrevs_max"] == 96
    # The open-ended counts are present and plausible.
    assert stats["objects"] > 0 and stats["routines"] > 0
    assert stats["verbs"] > 0 and stats["dict_words"] > stats["verbs"]
    assert stats["code_bytes"] + stats["string_bytes"] < stats["story_bytes"]


def test_z8_stats_scale():
    stats = {}
    generate(_world("cloak-of-darkness.storyarc"), version=8, stats=stats)
    assert stats["story_max"] == 512 * 1024


def test_cli_stats_flag(capsys, tmp_path):
    # --stats without -o compiles for the numbers and writes nothing.
    src = os.path.join(EXAMPLES, "brass-lantern.storyarc")
    assert cli.main([src, "--stats"]) == 0
    out = capsys.readouterr().out
    assert "compile statistics:" in out
    assert "attributes" in out and "/48" in out
    assert "not written" in out
    # With -o it writes the story AND prints the ledger.
    dest = str(tmp_path / "b.z5")
    assert cli.main([src, "-o", dest, "-s"]) == 0
    out = capsys.readouterr().out
    assert "wrote" in out and "compile statistics:" in out
    assert os.path.exists(dest)
