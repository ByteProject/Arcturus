# test_verbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Object verbs (B4.5e.3): take, drop, examine, inventory, their default
messages, an object handler overriding a default, and room darkness, on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Verb Test"\n'
    '    start room1\n'
    'room room1\n'
    '    name "Room One"\n'
    '    desc "A plain room."\n'
    '    north cave\n'
    'thing coin in room1\n'
    '    name "gold coin"\n'
    '    words gold, coin\n'
    'thing statue in room1\n'
    '    name "marble statue"\n'
    '    words marble, statue\n'
    '    fixed\n'
    'thing gem in room1\n'
    '    name "ruby gem"\n'
    '    words ruby, gem\n'
    '    desc "It glitters."\n'
    '    on drop\n'
    '        say "You cannot bear to part with the gem."\n'
    '        stop\n'
    'room cave\n'
    '    name "The Cave"\n'
    '    desc "Inky black."\n'
    '    lit false\n'
    '    south room1\n'
)


def test_verbs_compile():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_object_verbs_on_frotz(tmp_path):
    story = tmp_path / "v.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    script = (
        "take statue\n"  # fixed -> refused
        "examine gem\n"  # its description
        "take coin\n"  # Taken.
        "take gem\n"
        "inventory\n"  # carries coin and gem
        "drop gem\n"  # the gem's on drop overrides the default
        "north\n"  # into a dark room
    )
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input=script,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "That is fixed in place." in out  # take a fixed object
    assert "It glitters." in out  # examine
    assert "Taken." in out  # take default
    assert "You are carrying:" in out and "gold coin" in out  # inventory
    assert "You cannot bear to part with the gem." in out  # on drop override
    assert "It is pitch dark; you can't see a thing." in out  # darkness
