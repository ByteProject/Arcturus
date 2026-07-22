# test_enhance_redefine.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Grammar surgery (the verbs overhaul, phase 5), Stefan's spellings:
`enhance verb` appends grammar lines and synonyms to an existing family;
`redefine verb` replaces it whole, words included, and says so out loud.
The old way, a plain redeclaration, shadowed word by word and left the
family's other synonyms pointing at the old grammar; it still works, but
the compiler now says what it is doing and names the two honest forms."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = (
    'game\n    title "E"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing bell in hall\n    name "brass bell"\n    words bell, brass\n'
    'thing hammer in player\n    name "hammer"\n    words hammer\n'
    'thing bob in hall\n    name "Bob"\n    words bob\n    named\n    animate\n'
    '    on give\n        say "Bob pockets ${the noun}."\n'
)


def _run(extra, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(BASE + extra))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_enhance_adds_a_synonym_to_a_standard_family():
    out = _run('enhance verb "take", "snatch"\n', ["snatch bell", "i"])
    assert "Got it." in out
    assert "brass bell" in out.split(">i")[-1]


def test_enhance_adds_grammar_lines_and_keeps_the_old_ones():
    out = _run(
        'verb "ring"\n    ring noun\n'
        'enhance verb "ring"\n    ring noun with noun\n'
        'on ring\n'
        '    if second is not nothing\n'
        '        say "You ring ${the noun} with ${the second}."\n'
        '        stop\n'
        '    say "You ring ${the noun} barehanded."\n',
        ["ring bell", "ring bell with hammer"])
    assert "barehanded" in out
    assert "with the hammer" in out


def test_redefine_replaces_the_family_whole():
    # GIVE keeps working through the new grammar; FEED, an old synonym the
    # redefinition does not restate, is gone from the dictionary entirely.
    out = _run('redefine verb "give"\n    give noun to noun\n',
               ["take bell", "give bell to bob", "feed bell to bob"])
    assert "Bob pockets the brass bell." in out
    assert "doesn't know the word \"feed\"" in out or "don't add up" in out


def test_redefine_keeps_the_actions_contract():
    # Requirements live on the ACTION; replacing the wording does not shed
    # the contract, so an unheld gift still refuses before the handler.
    out = _run('redefine verb "give"\n    give noun to noun\n',
               ["give bell to bob"])
    assert "You aren't carrying the brass bell." in out
    assert "pockets" not in out


def test_enhance_of_nothing_is_a_clear_error():
    with pytest.raises(ArcError, match="no verb \"warble\""):
        analyze(cosmos.combined_program(parse(
            BASE + 'enhance verb "warble"\n    warble noun\n')))


def test_redefine_of_nothing_is_a_clear_error():
    with pytest.raises(ArcError, match="no verb \"warble\""):
        analyze(cosmos.combined_program(parse(
            BASE + 'redefine verb "warble"\n    warble noun\n')))


def test_redefine_without_grammar_is_refused():
    with pytest.raises(ArcError, match="needs grammar lines"):
        analyze(cosmos.combined_program(parse(
            BASE + 'redefine verb "give"\n')))


def test_plain_shadowing_still_works_but_says_so(capsys):
    out = _run('verb "take", "grab"\n    take noun\n', ["take bell"])
    assert "Got it." in out
    err = capsys.readouterr().err
    assert "shadows it word by word" in err
    assert "redefine verb" in err
