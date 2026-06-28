# test_grains.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Scenery grains (B4.5e.5): a grain word answers the verbs it names with its
response, and any other action on it gets the scenery default. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Grain Test"\n'
    '    start gallery\n'
    'room gallery\n'
    '    name "The Gallery"\n'
    '    desc "A long gallery."\n'
    '    grains\n'
    '        examine "painting" or "portrait" say "A faded portrait of a duke."\n'
)


def test_grain_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_grain_on_frotz(tmp_path):
    story = tmp_path / "g.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine painting\ntake portrait\n",  # answered verb, then not
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "A faded portrait of a duke." in out  # the grain answers examine
    assert "Just some scenery. Don't worry about it." in out  # the scenery default
