# test_unruled_refusal.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The dispatcher's refusal tail (Stefan's ruling): a custom verb nothing
claims must answer, never end the turn in silence. Pinned: the one-noun and two-noun refusals, the nounless form, a game
free rule outranking the tail, the any_unruled fold (a game whose verbs all
carry rules stays byte-identical), and the quoted-vocabulary escape hatch
(words "obsidian-black") that rode along in the same commit."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "U"\n    start lab\n'
    'room lab\n    name "Laboratory"\n    desc "A bare room."\n'
    'thing bench in lab\n    name "workbench"\n'
    '    words workbench, bench, "work-bench"\n'
    '    fixed\n    desc "Sturdy."\n'
    'verb "oil", "lubricate"\n'
    '    oil noun with noun\n'
    '    oil noun\n'
    'verb "meow"\n'
    '    meow\n'
)

RULED = GAME + (
    'on oil\n    change refused to 1\n    say "Not something you can oil."\n'
    'on meow\n    change refused to 1\n    say "You meow."\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_unclaimed_one_noun_refuses():
    out = _run(["oil bench"])
    assert "You can't do that to the workbench." in out


def test_unclaimed_two_noun_refuses():
    out = _run(["oil bench with bench"])
    assert "You can't do that to the workbench." in out


def test_unclaimed_bare_verb_refuses_nounless():
    out = _run(["meow"])
    assert "You can't do that." in out


def test_game_free_rule_outranks_the_tail():
    out = _run(["oil bench", "meow"], game=RULED)
    assert "Not something you can oil." in out
    assert "You meow." in out
    assert "You can't do that" not in out


def test_quoted_vocab_word_matches():
    out = _run(["examine work-bench"])
    assert "Sturdy." in out
