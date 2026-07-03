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
def test_ask_and_narrowing_answer(tmp_path):
    # The tie asks; a bare adjective as the answer weaves into the command
    # ("take coin" + "gold" resolves like "take gold coin" typed whole).
    out = _play(tmp_path, GAME, "take coin\ngold\ni\n")
    assert "Which do you mean, the gold coin or the silver coin?" in out
    assert "Got it." in out
    assert "gold coin" in out.rsplit("You're carrying:", 1)[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ask_answered_with_fresh_command(tmp_path):
    # An answer that starts with a verb is a change of mind: it replaces the
    # ambiguous command outright.
    out = _play(tmp_path, GAME, "take coin\ntake chest\ni\n")
    assert "Which do you mean," in out
    assert "stays exactly where it is" not in out  # chest is takeable? no:
    # the chest is an ordinary container, so it is simply taken.
    assert "oak chest" in out.rsplit("You're carrying:", 1)[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ask_empty_answer_gives_up(tmp_path):
    out = _play(tmp_path, GAME, "take coin\n\nlook\n")
    assert "You'll have to be more specific." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ask_repeats_until_narrowed(tmp_path):
    # An answer that does not narrow re-asks with the grown line; a second,
    # useful answer still lands.
    out = _play(tmp_path, GAME, "take coin\ncoin\nsilver\ni\n")
    assert out.count("Which do you mean,") >= 2
    assert "silver coin" in out.rsplit("You're carrying:", 1)[1]


SPANISH = (
    'summon.language "spanish"\n'
    'game\n    title "Cual"\n    start sala\n'
    'room sala\n    name "La Sala"\n    desc "Una sala."\n'
    'thing oro in sala\n    name "moneda de oro"\n    words moneda, oro\n'
    'thing plata in sala\n    name "moneda de plata"\n    words moneda, plata\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_spanish_ask(tmp_path):
    out = _play(tmp_path, SPANISH, "coge la moneda\noro\ni\n")
    assert "¿A cuál te refieres, la moneda de oro o la moneda de plata?" in out
    assert "Cogida." in out


GERMAN = (
    'summon.language "german"\n'
    'game\n    title "Welche"\n    start halle\n'
    'room halle\n    name "Die Halle"\n    desc "Eine Halle."\n'
    'thing hammer in halle\n    name "Hammer"\n    der\n    words hammer, werkzeug\n'
    'thing meissel in halle\n    name "Meißel"\n    der\n    words meissel, werkzeug\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_ask_declines_accusative(tmp_path):
    # "Was meinst du" takes the accusative: den Hammer, not der Hammer.
    out = _play(tmp_path, GERMAN, "nimm das werkzeug\nhammer\ni\n")
    assert "Was meinst du: den Hammer oder den Meißel?" in out
    assert "Genommen." in out


LOCK_GAME = (
    'game\n    title "L"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing gate in hall\n    name "iron gate"\n    words gate, lock\n'
    "    fixed\n    openable\n    open false\n    lockable\n    locked\n"
    "    unseal_with key\n"
    'thing key in hall\n    name "small key"\n    words key\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_noun_that_doubles_as_verb_in_two_noun_slot(tmp_path):
    # "lock" is a verb AND the gate's noun: the two-noun boundary must split
    # at the preposition ("with"), never at a verb-flagged noun word, or the
    # first phrase comes up empty (the pick-the-lock bug, 2026-07-03).
    out = _play(tmp_path, LOCK_GAME, "take key\nunlock lock with key\nopen gate\n")
    assert "Unlocked." in out
    assert "Open." in out


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
