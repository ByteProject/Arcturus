# test_dawords.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The pronominal adverbs (docs/01 chapter 21): German fuses preposition and
referent into one word, damit, darauf, darin, daran, plus the colloquial
short forms. A da-word binds the freshest remembered non-animate thing into
the second slot (never the object being acted on, never a person, the ruled
semantics), satisfies a two-noun requirement, and is position-free. darunter
stays the look_under particle and binds the same referent into an empty noun
slot. An empty referent refuses with the honest pronoun ask."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _replies(src, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


GAME = (
    'summon.language "german"\n'
    'game\n    title "G"\n    start halle\n'
    'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
    'thing tisch of supporter in halle\n    name "Tisch"\n    words tisch\n'
    '    der\n    fixed\n'
    'thing buch in halle\n    name "Buch"\n    words buch\n    das\n'
    'thing tuer of door in halle, hof\n    name "Tür"\n    words tür\n    die\n'
    '    lockable\n    locked\n    unseal_with schluessel\n'
    'room hof\n    name "Hof"\n    desc "Ein Hof."\n'
    'thing schluessel in halle\n    name "Schlüssel"\n    words schlüssel\n'
    '    der\n'
    'thing wirtin of character in halle\n    name "Wirtin"\n    words wirtin\n'
    '    die\n'
    'thing truhe of container in halle\n    name "Truhe"\n    words truhe\n'
    '    die\n    openable\n'
)

ASK = "Du musst schon genau sagen, was gemeint ist."


def test_damit_binds_the_freshest_thing():
    out = _replies(GAME, ["nimm schluessel", "schliess die tuer damit auf"])
    assert "Aufgeschlossen." in out


def test_da_words_are_position_free():
    out = _replies(GAME, ["nimm schluessel", "schliess damit die tuer auf"])
    assert "Aufgeschlossen." in out


def test_darauf_satisfies_the_wohin_and_skips_the_acted_on():
    # The book is the freshest mention (just taken), but darauf must never
    # mean the book itself: the repick reaches the table.
    out = _replies(GAME, ["untersuche tisch", "nimm buch", "leg das buch darauf"])
    assert "Erledigt." in out
    assert "verlangt eine genauere Angabe" not in out


def test_darin_reaches_the_container():
    out = _replies(GAME, ["oeffne truhe", "nimm buch", "leg das buch darin"])
    assert "Erledigt." in out


def test_animate_referents_are_skipped():
    # Talking to the innkeeper makes her the freshest mention; damit still
    # reaches the key, because the German word never means a person.
    out = _replies(GAME, ["nimm schluessel", "rede mit wirtin",
                          "schliess die tuer damit auf"])
    assert "Aufgeschlossen." in out


def test_empty_referent_refuses_honestly():
    out = _replies(GAME, ["schliess die tuer damit auf"])
    assert ASK in out


def test_darunter_looks_under_the_freshest_thing():
    out = _replies(GAME, ["untersuche tisch", "schau darunter"])
    assert "Unter dem Tisch" in out


def test_non_compounding_verbs_keep_their_refusal():
    # "nimm darunter" is not a look_under compound: the ordinary incomplete
    # ask stands, no referent sneaks in.
    out = _replies(GAME, ["untersuche tisch", "nimm darunter"])
    assert "verlangt eine genauere Angabe" in out


def test_the_chain_showcase():
    # The forum sentence: take the key and unlock the door with it, one line.
    out = _replies(GAME, ["nimm den schluessel und schliess damit die tuer auf"])
    assert "Du nimmst den Schlüssel an dich." in out
    assert "Aufgeschlossen." in out
