# test_binary.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The binary model (the open/close symmetry for two-state devices): the
library owns the state (`active`), flips it with default reports, refuses
already-on/already-off honestly in the verb contract before any handler,
and couples `lit` on glow things (binary + lit declared). `switchable` is
the compatibility alias; flavor handlers override the default and then own
the flip. Games without binary things stay byte-identical (any_binary)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "B"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    south cave\n'
    'room cave\n    name "Cave"\n    desc "A dank cave."\n    lit false\n    north hall\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp\n    binary\n    lit false\n'
    'thing radio in hall\n    name "radio"\n    words radio\n    binary\n'
    'thing rock in hall\n    name "rock"\n    words rock\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "b.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_defaults_flip_and_refuse_honestly(tmp_path):
    out = _play(tmp_path, GAME,
                "turn on lamp\nturn on lamp\nturn off lamp\nturn off lamp\n"
                "turn on radio\nturn on rock\n")
    assert "You switch the brass lamp on." in out
    assert "The brass lamp is already on." in out
    assert "You switch the brass lamp off." in out
    assert "The brass lamp is already off." in out
    assert "You switch the radio on." in out          # no glow needed
    assert "The rock isn't the switching kind." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_glow_couples_light(tmp_path):
    # binary + lit = a glow thing: the default flip carries the light, so
    # a dark room yields to the switch and darkens again, zero author code.
    out = _play(tmp_path, GAME,
                "take lamp\nsouth\nturn on lamp\nlook\nturn off lamp\n")
    assert "Pitch black" in out
    assert "A dank cave." in out
    assert out.index("A dank cave.") > out.index("Pitch black")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_switchable_alias_still_compiles_and_plays(tmp_path):
    src = GAME.replace("    binary\n    lit false\n",
                       "    switchable\n    lit false\n", 1)
    out = _play(tmp_path, src, "turn on lamp\nturn on lamp\n")
    assert "You switch the brass lamp on." in out
    assert "The brass lamp is already on." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_flavor_handler_owns_prose_and_flip(tmp_path):
    src = GAME.replace(
        "    binary\n    lit false\n",
        "    binary\n    lit false\n"
        "    on switch_on\n        now self is active\n"
        "        now self is lit\n        say \"A soft hiss.\"\n", 1)
    out = _play(tmp_path, src, "turn on lamp\nturn on lamp\nturn off lamp\n")
    assert "A soft hiss." in out                       # the flavor spoke
    assert "The brass lamp is already on." in out      # contract still guards
    assert "You switch the brass lamp off." in out     # default off intact


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_defaults_speak_german(tmp_path):
    src = (
        'summon.language "german"\n'
        'game\n    title "B"\n    start raum\n'
        'room raum\n    name "Raum"\n    desc "Ein Raum."\n'
        'thing lampe in raum\n    name "Lampe"\n    words lampe\n    die\n'
        "    binary\n    lit false\n"
    )
    out = _play(tmp_path, src,
                "schalte die lampe an\nschalte die lampe an\n"
                "schalte die lampe aus\nschalte die lampe aus\n")
    assert "Du schaltest die Lampe ein." in out
    assert "Die Lampe ist schon an." in out
    assert "Du schaltest die Lampe aus." in out
    assert "Die Lampe ist schon aus." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_spanish_defaults_agree_in_gender(tmp_path):
    src = (
        'summon.language "spanish"\n'
        'game\n    title "B"\n    start sala\n'
        'room sala\n    name "Sala"\n    desc "Una sala."\n'
        'thing lampara in sala\n    name "lampara"\n    words lampara\n    la\n'
        "    binary\n    lit false\n"
    )
    out = _play(tmp_path, src,
                "enciende la lampara\nenciende la lampara\n")
    assert "Enciendes la lampara." in out
    assert "ya está encendida." in out                 # feminine agreement
