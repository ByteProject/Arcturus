# test_give_show_self.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""GIVE or SHOW to yourself is refused before any handler runs
(improvmonster's report, 2026-10-30: in a maniacswap game the player's
body is a character, so a character kind's `on give` accepted a gift from
the player to the player). Every pack words the refusal."""

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


BODIES = (
    'summon.maniacswap\n'
    'game\n    title "G"\n    start hall\n    body henrik\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'kind person of character\n'
    '    on give\n        move noun to second\n        say "${The second} takes ${the noun}."\n'
    'thing henrik of person in hall\n    name "Henrik"\n    named\n    words henrik\n    playable\n'
    'thing greta of person in hall\n    name "Greta"\n    named\n    words greta\n    playable\n'
    'thing lamp in henrik\n    name "lamp"\n    words lamp\n'
    'thing key in henrik\n    name "key"\n    words key\n'
)


def test_giving_or_showing_to_yourself_is_refused_before_any_handler():
    out = _run(BODIES, ["give lamp to me", "show lamp to me", "give lamp and key to me",
                        "give lamp to greta"])
    parts = out.split(">")
    assert "You already have the lamp." in parts[1] and "takes" not in parts[1]
    assert "You know the lamp well enough already." in parts[2]
    assert "takes" not in parts[3]                                   # the list path too
    assert "Greta takes the lamp." in parts[4]


def test_the_packs_word_the_refusal():
    base = (
        'game\n    title "G"\n    start hall\n'
        'room hall\n    name "Halle"\n    desc "x"\n'
        'thing key in player\n    name "{name}"\n    words {word}\n{gender}'
    )
    de = 'summon.language "german"\n' + base.format(name="Schlüssel", word="schlüssel", gender="    der\n")
    out = _run(de, ["gib schlüssel an mich", "zeige schlüssel an mich"])
    assert "Du hast den Schlüssel doch schon." in out
    assert "Du kennst den Schlüssel schon zur Genüge." in out
    es = 'summon.language "spanish"\n' + base.format(name="llave", word="llave", gender="    feminine\n")
    out = _run(es, ["da la llave a yo", "muestra la llave a yo"])
    assert "Ya tienes la llave." in out
    assert "Ya conoces la llave de sobra." in out
