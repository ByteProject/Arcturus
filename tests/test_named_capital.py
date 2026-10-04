# test_named_capital.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A named object's lowercase name at a sentence start (Charles Moore
Jr.'s report, 2026-09-24: "the cat is beyond your reach."). The compiler
keeps a capitalized twin (name_cap) for named things whose literal name
starts lowercase, and the art blocks' capitalized path reads it; games
whose named things are capitalized, or have none, are byte-identical (the
untouched ceilings)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


GAME = (
    'game\n    title "B"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing bob of character in hall\n    name "Bob"\n    named\n'
    '    words bob\n    beyond\n'
    'thing cat of character in hall\n    name "the cat"\n    named\n'
    '    words cat\n    beyond\n'
    'verb "greet"\n    reachagnostic\n    vgreet noun\n'
    'on vgreet\n    say "${The noun} looks up. You nod at ${the noun}."\n'
)


def test_lowercase_named_opens_a_sentence_capitalized():
    out = _run(GAME, ["take cat", "take bob", "greet cat"])
    assert "The cat is beyond your reach." in out
    assert "the cat is beyond" not in out
    assert "Bob is beyond your reach." in out
    assert "The cat looks up. You nod at the cat." in out   # mid-sentence stays lowercase


def test_the_player_opens_a_sentence_capitalized():
    # auraes's note (2026-10-04): "yourself is not on the menu." The packs
    # name the player lowercase; the seeded player gets the twin too.
    src = (
        'game\n    title "E"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
    )
    out = _run(src, ["eat me"])
    assert "Yourself is not on the menu." in out


def test_german_spells_the_player_subject_out():
    src = (
        'summon.language "german"\n'
        'game\n    title "E"\n    start hall\n'
        'room hall\n    name "Halle"\n    desc "x"\n'
    )
    out = _run(src, ["iss mich"])
    assert "Du selbst stehst nicht auf der Speisekarte." in out
