# test_chaining.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Command chaining (docs/02 section 8b): several commands on one line, joined
by the language layer's chain words ("and", "then", the comma; y/luego in
Spanish, und/dann in German). The chain stops at a failed command: a parse
failure, or a refusal path setting `refused`. An outcome that already holds
("you already have it") does not stop it. AGAIN repeats only the last command
of a chained line (the resolved-operands replay the loop already keeps)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "C"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp\n'
    '    desc "A dented lamp."\n'
    'thing box in hall\n    name "wooden box"\n    words box\n'
    '    desc "A pine box."\n'
    'thing statue in hall\n    name "stone statue"\n    words statue\n'
    "    fixed\n"
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "c.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_chain_and_then_comma(tmp_path):
    # Three commands on one line, mixing all three separators; every one runs.
    out = _play(tmp_path, GAME, "take lamp and take box, then go north\ni\n")
    assert out.count("Got it.") == 2
    assert "Yard" in out
    assert "brass lamp" in out and "wooden box" in out  # both in inventory


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_chain_stops_on_refusal(tmp_path):
    # The statue is fixed: its refusal stops the line, so the move never runs.
    out = _play(tmp_path, GAME, "take statue and go north\nlook\n")
    assert "stays exactly where it is" in out
    assert "Yard" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_chain_stops_on_parse_failure(tmp_path):
    # An unknown word in the middle command ends the line there.
    out = _play(tmp_path, GAME, "take lamp and frobnicate box then go north\nlook\n")
    assert "Got it." in out
    assert "Yard" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_already_satisfied_does_not_stop(tmp_path):
    # "You already have it" is not a refusal: the goal holds, the line goes on.
    out = _play(tmp_path, GAME, "take lamp\ntake lamp and go north\n")
    assert "You already have the brass lamp." in out
    assert "Yard" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_each_command_takes_a_turn(tmp_path):
    # A chained line is several turns, not one (Inform's model): the turn
    # counter advances per command.
    out = _play(tmp_path, GAME, "take lamp and take box\nscore\n")
    assert "in that direction" not in out  # sanity: nothing misparsed
    assert out.count("Got it.") == 2


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_again_repeats_last_command_only(tmp_path):
    # AGAIN after a chained line replays only the LAST command (Option B):
    # after "x lamp and x box", g repeats the box examine, not the whole line.
    out = _play(tmp_path, GAME, "x lamp and x box\ng\n")
    assert out.count("A dented lamp.") == 1
    assert out.count("A pine box.") == 2
    assert "There's nothing to repeat." not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_trailing_chain_word_is_harmless(tmp_path):
    # "take lamp and" has no second command: the take still runs cleanly, and
    # the dangling word never reaches the verb grammar as an extra word.
    out = _play(tmp_path, GAME, "take lamp and\ni\n")
    assert "Got it." in out
    assert "lost me after that" not in out


GRAIN_GAME = (
    'game\n    title "G"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    "    grains\n"
    '        examine "mural" say "A faded mural."\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_grain_refusal_stops_chain(tmp_path):
    # A grain word hit with a verb the grain does not answer gets the scenery
    # brush-off from the GENERATED grain routine; that refusal stops the line.
    # The verb it does answer chains on normally.
    out = _play(tmp_path, GRAIN_GAME, "take mural and go north\nlook\n")
    assert "Just some scenery." in out
    assert "Yard" not in out
    out = _play(tmp_path, GRAIN_GAME, "x mural and go north\n")
    assert "A faded mural." in out
    assert "Yard" in out


SPANISH = (
    'summon.language "spanish"\n'
    'game\n    title "Cadena"\n    start sala\n'
    'room sala\n    name "La Sala"\n    desc "Una sala."\n'
    "    north patio\n"
    'room patio\n    name "El Patio"\n    desc "Un patio."\n'
    'thing lampara in sala\n    name "lámpara"\n    words lampara\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_spanish_chain(tmp_path):
    # y / luego / the comma chain in Spanish; the whole line runs.
    out = _play(tmp_path, SPANISH, "coge la lampara y mira, luego ve al norte\n")
    assert "El Patio" in out


GERMAN = (
    'summon.language "german"\n'
    'game\n    title "Kette"\n    start halle\n'
    'room halle\n    name "Die Halle"\n    desc "Eine Halle."\n'
    "    north hof\n"
    'room hof\n    name "Der Hof"\n    desc "Ein Hof."\n'
    'thing lampe in halle\n    name "die Lampe"\n    words lampe\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_chain(tmp_path):
    # und / dann chain in German; the whole line runs.
    out = _play(tmp_path, GERMAN, "nimm die lampe und schau, dann geh nach norden\n")
    assert "Der Hof" in out
