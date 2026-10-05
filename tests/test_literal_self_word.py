# test_literal_self_word.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A self word that doubles as a grammar literal (auraes's French "soi":
player.words soi beside `enter soi sur noun`, 2026-10-04). The phrase
scanner skipped it as a leading preposition and found no noun; a
preposition with nothing after it is content, so PRENDRE SOI names the
player while the literal line keeps working and a true leading
preposition (LOOK AT X) still skips."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "Soi"\n    start salon\n'
    'player.words soi, "soi-meme"\n'
    'room salon\n    name "Salon"\n    desc "A salon."\n'
    'thing fauteuil of supporter in salon\n    name "fauteuil"\n'
    '    words fauteuil\n    fixed\n    desc "Velvet."\n'
    'verb "asseoir"\n    enter soi sur noun\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_a_last_word_literal_is_content():
    out = _run(["take soi", "examine soi", "asseoir soi sur fauteuil",
                "look at fauteuil"])
    assert "firm grip on yourself" in out                       # take self
    assert "admire ourselves" in out                            # examine self
    assert "requires you to be more specific" not in out
    assert "You get on the fauteuil." in out                    # the literal line
    assert "Velvet." in out.split(">look at fauteuil")[1]       # AT still leads


def test_a_literal_only_line_is_a_complete_command():
    # auraes (2026-10-05): `exit soi` beside `exit soi de noun`. The flag
    # model cannot say "the literal alone is a whole command", so LEVER
    # SOI bound the player as the noun; the verb now takes the table, and
    # the bare line leaves the noun empty.
    src = GAME + 'verb "lever"\n    exit soi\n    exit soi de/du noun\n'
    io = CaptureIO(script=["asseoir soi sur fauteuil", "lever soi",
                           "asseoir soi sur fauteuil", "lever soi du fauteuil"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert out.count("You get off the fauteuil.") == 2
    assert "aren't in that" not in out
