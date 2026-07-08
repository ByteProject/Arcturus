# test_unknown_word.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Unresolved nouns fail the parse instead of dispatching (the adopter's
custom-verb trap: "read sdlfjh" ran the author's handler as if the player
had typed a bare "read"). A word the dictionary does not know at all is
named back (parse_fault 4, msg_unknown_word); a known object word that
nothing in scope answers to stays the classic can't-see (fault 1). A bare
verb still reaches the handler with noun = nothing, which is now the ONLY
thing noun = nothing means."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Read"\n    start den\n'
    'room den\n    name "Den"\n    desc "Cosy."\n'
    'thing book in den\n    name "book"\n'
    'thing gem in vault\n    name "gem"\n'
    'room vault\n    name "Vault"\n    desc "Far away."\n'
    'verb "read"\n    read noun\n'
    'on read\n'
    '    if noun is nothing\n'
    '        say "Specify reading material."\n'
    '        stop\n'
    '    say "Read: ${the noun}."\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, cmds):
    return subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input=cmds, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_the_three_cases_are_told_apart(tmp_path):
    story = tmp_path / "r.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "read\nread sdlfjh\nread gem\nread book\n")
    assert "Specify reading material." in out          # bare verb: the author's
    assert 'know the word "sdlfjh"' in out             # typo: named back
    assert "You see nothing of the sort here." in out  # real thing, not here
    assert "Read: the book." in out                    # the working case


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_standard_and_two_noun_verbs_name_typos_too(tmp_path):
    story = tmp_path / "r.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "take zzqua\ngive zzqua to book\nput book in zzqua\n")
    assert out.count('know the word "zzqua"') == 3


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_and_spanish_name_the_word(tmp_path):
    de = (
        'game\n    title "L"\n    start halle\nsummon.language "german"\n'
        'room halle\n    name "Halle"\n    desc "Leer."\n'
        'thing buch in halle\n    name "Buch"\n    das\n'
    )
    story = tmp_path / "de.z5"
    story.write_bytes(_build(de))
    out = _run(story, "nimm qqjx\n")
    assert 'Das Wort "qqjx" kennt diese Geschichte nicht.' in out

    es = (
        'game\n    title "L"\n    start sala\nsummon.language "spanish"\n'
        'room sala\n    name "Sala"\n    desc "Nada."\n'
        'thing libro in sala\n    name "libro"\n'
    )
    story = tmp_path / "es.z5"
    story.write_bytes(_build(es))
    out = _run(story, "coge qqjx\n")
    assert 'Esta historia no conoce la palabra "qqjx".' in out
