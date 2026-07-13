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


def test_cli_verbose_by_default_quiet_on_request(capsys, tmp_path):
    # A compile is verbose by default: the banner shows and the statistics
    # ledger follows the result line. -q silences both for scripts.
    src = os.path.join(EXAMPLES, "brass-lantern.storyarc")
    dest = str(tmp_path / "b.z5")
    assert cli.main([src, "-o", dest]) == 0
    out = capsys.readouterr().out
    assert "Arcturus -- [ arcc" in out  # the banner, on every invocation
    assert "wrote" in out and "compile statistics:" in out
    assert "attributes" in out and "/48" in out  # the ledger names attributes (not "flags": that is a distinct feature)
    assert os.path.exists(dest)
    assert cli.main([src, "-o", dest, "-q"]) == 0
    out = capsys.readouterr().out
    assert "wrote" in out
    assert "compile statistics:" not in out and "Arcturus -- [" not in out


def test_stats_separate_attributes_from_kinds():
    # The honest budget (the Charles wall): the ledger shows genuine object
    # attributes against the 48 ceiling and the kind count separately (with
    # the spill), so a kind is never mistaken for an attribute ceiling.
    from arcturus import cosmos
    from arcturus.parser import parse
    from arcturus.sema import analyze
    lines = ['game', '    title "T"', '    start hall']
    for i in range(60):
        lines.append(f'kind k{i} of thing')
    lines += ['room hall', '    name "Hall"', '    desc "D."']
    for i in range(60):
        lines += [f'thing o{i} of k{i} in hall', f'    name "obj{i}"',
                  f'    words obj{i}']
    lines += ['verb "probe"', '    probe noun', 'on probe']
    for i in range(60):
        lines += [f'    if noun is k{i}', f'        say "m{i}"']
    game = '\n'.join(lines) + '\n'
    stats = {}
    generate(analyze(cosmos.combined_program(parse(game))), stats=stats)
    assert stats["attributes"] < 48                 # genuine attributes under the ceiling
    assert stats["kinds_backed"] > 0                # some kinds keep test_attr
    assert stats["kinds_spilled"] > 0               # the rest spilled, still working
    line = cli._stats_report(stats, 5)
    assert "attributes" in line and "kinds" in line  # both, named honestly
    assert "spilled to catalogs" in line            # the author sees the spill
