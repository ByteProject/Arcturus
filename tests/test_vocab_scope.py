# test_vocab_scope.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Name-derived vocabulary and hidden objects (B4.5e.4): an object with no
explicit words is matched by its name, and a hidden object cannot be seen,
listed, or taken until it is revealed. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Vocab Test"\n'
    '    start vault\n'
    'room vault\n'
    '    name "The Vault"\n'
    '    desc "A steel vault."\n'
    'thing panel in vault\n'  # no `words`: matched by its name
    '    name "brass panel"\n'
    '    fixed\n'
    '    on push\n'
    '        now coin is not hidden\n'
    '        say "The panel slides aside."\n'
    'thing coin in vault\n'
    '    name "gold coin"\n'
    '    words gold, coin\n'
    '    hidden\n'
    'verb "push", "press"\n'
    '    push noun\n'
)


def test_vocab_scope_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_name_vocab_and_hidden_on_frotz(tmp_path):
    story = tmp_path / "vs.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take coin\npush panel\ntake coin\n",  # hidden, reveal, take
        capture_output=True, text=True, timeout=15,
    ).stdout
    # The panel is referred to by its name (no explicit words).
    assert "The panel slides aside." in out
    # The coin is hidden at first (not takeable), then revealed and taken.
    assert "You can't see that here." in out  # take coin while hidden
    assert "Taken." in out  # take coin after the panel reveals it
    # A hidden object is not listed in the room.
    assert "gold coin here" not in out.split("The panel slides aside.")[0]
