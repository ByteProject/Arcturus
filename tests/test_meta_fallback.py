# test_meta_fallback.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The English meta words work in every language pack (docs/02 section 11):
QUIT, SCORE, SAVE, RESTORE/LOAD, UNDO, AGAIN, OOPS, TRANSCRIPT and their
kin answer in a German or Spanish game, because a player used to English
adventures guesses the localized session verb wrong at first and the
session must never be hostage to vocabulary. The replies stay native."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GERMAN = (
    'game\n    title "T"\n    start bau\n'
    'summon.language "german"\n'
    'room bau\n    name "Bau"\n    desc "Eine stille Kammer."\n'
)

SPANISH = (
    'game\n    title "T"\n    start sala\n'
    'summon.language "spanish"\n'
    'room sala\n    name "Sala"\n    desc "Una sala tranquila."\n'
)

_STORY = {}


def _run(cmds, game):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_english_meta_words_in_german():
    out = _run(["score", "undo", "oops"], GERMAN)
    assert "Dieses Spiel zählt keine Punkte." in out
    assert "Es gibt nichts rückgängig zu machen." in out
    assert "Es gibt nichts zu korrigieren." in out


def test_english_meta_words_in_spanish():
    out = _run(["score", "undo", "oops"], SPANISH)
    assert "Este juego no lleva puntuación." in out
    assert "No hay nada que deshacer." in out
    assert "No hay nada que corregir." in out
