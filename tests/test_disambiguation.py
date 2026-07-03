# test_disambiguation.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Disambiguation (docs/02 section 8): the noun matcher scores every in-scope
object by how many typed words its vocabulary contains and takes the single
best. A tie at the best score is a genuine ambiguity: the turn asks the player
which one is meant instead of silently taking whichever object comes first in
scope order (the gold coin / silver coin hole found 2026-07-03)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "D"\n    start vault\n'
    'room vault\n    name "Vault"\n    desc "A vault."\n'
    "    north lobby\n"
    'room lobby\n    name "Lobby"\n    desc "A lobby."\n'
    'thing gold in vault\n    name "gold coin"\n    words gold, coin\n'
    'thing silver in vault\n    name "silver coin"\n    words silver, coin\n'
    'thing chest of container in vault\n    name "oak chest"\n    words chest\n'
    "    openable\n    open false\n"
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "d.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_tie_is_never_taken_silently(tmp_path):
    # "take coin" matches both coins equally: nothing is taken, the turn
    # answers instead of guessing.
    out = _play(tmp_path, GAME, "take coin\ni\n")
    assert "Got it." not in out
    assert "gold coin" not in out.split(">")[2]  # inventory holds neither


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_adjective_narrows(tmp_path):
    # A distinguishing word resolves without any question: score 2 beats 1.
    out = _play(tmp_path, GAME, "take gold coin\ntake silver coin\ni\n")
    assert out.count("Got it.") == 2


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_single_word_unique_still_resolves(tmp_path):
    out = _play(tmp_path, GAME, "take gold\ni\n")
    assert "Got it." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ambiguity_stops_a_chain(tmp_path):
    # An ambiguous command is a failed command: the chained move never runs.
    out = _play(tmp_path, GAME, "take coin and go north\nlook\n")
    assert "Lobby" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_two_noun_slot_ambiguity(tmp_path):
    # The noun slots are scored phrases: the adjective resolves slot one, and
    # a bare "coin" stays ambiguous even with one coin inside the OPEN chest,
    # because an open container's contents are still in scope. Honest both ways.
    out = _play(
        tmp_path, GAME,
        "open chest\nput gold coin in chest\nput coin in chest\n"
        "put silver coin in chest\n",
    )
    assert out.count("Done.") == 2  # the two adjective forms; the bare one asked


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_shut_away_knowledge_survives(tmp_path):
    # The scoring matcher keeps the container knowledge model: naming a thing
    # you know is shut inside a closed chest (taking marked it seen) answers
    # "open it first" rather than "you can't see it".
    out = _play(
        tmp_path, GAME,
        "take gold coin\nopen chest\nput gold coin in chest\nclose chest\n"
        "take gold\n",
    )
    assert "You'll have to open the oak chest first." in out
