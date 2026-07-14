# test_twonoun.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Two-noun grammar (B4.5e.4c): put noun on noun. The parser resolves a second
noun, and the default put handler moves the object onto a supporter, on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Put Test"\n'
    '    start hall\n'
    'room hall\n'
    '    name "The Hall"\n'
    '    desc "A wide hall."\n'
    'thing book in hall\n'
    '    name "red book"\n'
    '    words red, book\n'
    'thing table of supporter in hall\n'
    '    name "oak table"\n'
    '    words oak, table\n'
    '    fixed\n'
    '    on examine\n'
    '        if table holds book\n'
    '            say "The book rests on the table."\n'
    '        else\n'
    '            say "A bare oak table."\n'
    '        stop\n'
)


def test_twonoun_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_put_on_supporter_on_frotz(tmp_path):
    story = tmp_path / "pt.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine table\nput book on table\nexamine table\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "A bare oak table." in out  # before: nothing on it
    assert "Done." in out  # put book on table
    assert "The book rests on the table." in out  # after: the book moved onto it


OPEN_WITH_KEY = (
    'game\n    title "Open Test"\n    start r\n'
    'room r\n    name "R"\n    desc "A room."\n    north f\n'
    'room f\n    name "F"\n    desc "F."\n    south r\n'
    'thing gate of door in r, f\n    name "oak door"\n    words door, gate\n'
    '    lockable\n    locked\n    unseal_with key\n'
    'thing key in r\n    name "brass key"\n    words key\n'
    'thing stone in r\n    name "grey stone"\n    words stone\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_open_with_key_unlocks_then_opens_on_frotz(tmp_path):
    # "open the door with the key": the open action, given a second noun (the key),
    # unlocks a locked thing and then opens it. A wrong key does not fit.
    story = tmp_path / "ow.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(OPEN_WITH_KEY)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take key\ntake stone\nopen door with stone\nopen door with key\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "entirely unimpressed" in out  # wrong key: refused, still locked
    assert "Unlocked." in out  # right key: unlocked
    assert "Open." in out  # and then opened, in one command
