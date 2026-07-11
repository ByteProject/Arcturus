# test_pluribus.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""pluribus (e pluribus unum): ONE object that is grammatically plural (the
scissors, the boots), a field request. The articles read it ("some
scissors", German's bare indefinite plural and die/die/den by case,
Spanish unas/unos), the ${is x} copula agrees (is/are, ist/sind,
está/están), and the core messages conjugate, in all three languages. Not
the plurals granule, whose group words sweep several singular objects. An
unmarked game folds it all away (the untouched ceilings are the proof)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

ENGLISH = (
    'game\n    title "T"\n    start shed\n'
    'room shed\n    name "Shed"\n    desc "A shed."\n'
    'thing scissors in shed\n    name "scissors"\n    words scissors\n'
    '    desc "Sharp."\n    pluribus\n    fixed\n'
    'thing lamp in shed\n    name "brass lamp"\n    words lamp\n'
    'on start\n    say "${The scissors} ${is scissors} here; ${the lamp} ${is lamp} too."\n'
)

GERMAN = (
    'game\n    title "T"\n    start kammer\n'
    'summon.language "german"\n'
    'room kammer\n    name "Kammer"\n    desc "Eine Kammer."\n'
    'thing stiefel in kammer\n    name "Stiefel"\n    words stiefel\n'
    '    die\n    pluribus\n    fixed\n'
    'on start\n    say "${The stiefel} ${is stiefel} hier. Du siehst ${the:acc stiefel},'
    ' etwas liegt auf ${the:dat stiefel}."\n'
)

SPANISH = (
    'game\n    title "T"\n    start sala\n'
    'summon.language "spanish"\n'
    'room sala\n    name "Sala"\n    desc "Una sala."\n'
    'thing tijeras in sala\n    name "tijeras"\n    words tijeras\n'
    '    feminine\n    pluribus\n    fixed\n'
    'on start\n    say "${The tijeras} ${is tijeras} aquí."\n'
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


def test_english_agreement():
    out = _run(["look", "take scissors", "open scissors"], ENGLISH)
    assert "The scissors are here; the brass lamp is too." in out
    assert "You can see some scissors here." in out   # the indefinite plural
    assert "You can see a brass lamp here." in out    # singular untouched
    assert "The scissors stay exactly where they are." in out
    assert "The scissors don't open." in out


def test_german_agreement():
    out = _run(["schau", "nimm stiefel"], GERMAN)
    # sind, accusative die, dative den, and the bare indefinite plural.
    assert "Die Stiefel sind hier." in out
    assert "die Stiefel, etwas liegt auf den Stiefel" in out
    assert "Du siehst hier Stiefel." in out
    assert "Die Stiefel bleiben ziemlich genau, wo sie sind." in out


def test_spanish_agreement():
    out = _run(["mira", "coge tijeras"], SPANISH)
    assert "Las tijeras están aquí." in out
    assert "Ves unas tijeras." in out
    assert "Las tijeras se quedan justo donde están." in out
