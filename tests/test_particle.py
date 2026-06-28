# test_particle.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Multi-word verbs (B4.5e.4): the parser combines a verb with a particle in the
language layer (switch + on -> switch_on, switch + off -> switch_off), driven on
Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Particle Test"\n'
    '    start lab\n'
    'room lab\n'
    '    name "The Lab"\n'
    '    desc "A tidy laboratory."\n'
    'thing lamp in lab\n'
    '    name "desk lamp"\n'
    '    words desk, lamp\n'
    '    switchable\n'
    '    on switch_on\n'
    '        say "The lamp glows."\n'
    '    on switch_off\n'
    '        say "The lamp dims."\n'
)


def test_particle_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_particle_verbs_on_frotz(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    # switch on / switch off / turn on all reach the right action via the particle.
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="switch on lamp\nswitch off lamp\nturn on lamp\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("The lamp glows.") == 2  # switch on, then turn on
    assert "The lamp dims." in out  # switch off -> switch_off via the off particle
