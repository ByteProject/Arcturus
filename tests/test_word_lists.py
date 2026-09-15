# test_word_lists.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The free-standing word LIST (docs/01 chapter 5; Stefan's ruling after
the with-words catalog misbuild, 2026-09-15): `list pronoms = se, lui`
declares chapter 5's word-array type at top level. Entries, bare or
quoted (an apostrophe form), enter the dictionary owned by nothing; the
table is a bare static run of dictionary addresses; words_addr folds to
a link-time constant and words_count to a compile-time one, so
scan_table searches it and paired lists read back by offset."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "Bare."\n'
    "list pronoms = se, lui, \"s'\"\n"
    'list replacements = soi, leur, sien\n'
    'verb "probe"\n    wprobe text\n'
    'on wprobe\n'
    '    let w = word_dict(1)\n'
    '    let hit = scan_table(w, words_addr(pronoms), words_count(pronoms))\n'
    '    if hit is 0\n'
    '        say "not a pronoun"\n'
    '        stop\n'
    '    let i = (hit - words_addr(pronoms)) / 2\n'
    '    if peek_word(words_addr(replacements), i) is dict_entry("leur")\n'
    '        say "slot ${i + 1}: pairs with leur"\n'
    '    else\n'
    '        say "slot ${i + 1}"\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_word_list_scans_and_pairs():
    out = _run(["probe se", "probe lui", "probe s'", "probe hall"])
    assert "slot 1" in out
    assert "slot 2: pairs with leur" in out
    assert "slot 3" in out              # the quoted apostrophe entry
    assert "not a pronoun" in out


def test_list_words_name_no_object():
    out = _run(["x se", "x lui"])
    # the words are in the dictionary but owned by nothing: the parser
    # finds no object, never an examinable table row
    assert "requires you to be more specific" in out or "can't see" in out
    assert "You see nothing of the sort" in out or "more specific" in out
