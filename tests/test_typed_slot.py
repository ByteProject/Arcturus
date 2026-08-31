# test_typed_slot.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The typed surface (docs/01 chapter 14): an author's own verb line carries
a `text` slot (TYPE 1451 INTO TERMINAL, the Hibernated 1 shape), and `typed`
reads what it absorbed: compared against a literal (the compiler adds the
literal's words to the dictionary itself), printed back verbatim in ${typed},
or read as a number through typed_number. Every reading is raw text, so codes
that are no dictionary word still compare and echo. A game that never reads
the slot compiles byte-identical (the blocks are dead code)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze


GAME = (
    'game\n    title "Typed"\n    author "T"\n    start lab\n'
    'room lab\n    name "Lab"\n    desc "A terminal hums beside a dial."\n'
    'thing terminal in lab\n    name "terminal"\n    words terminal\n    fixed\n'
    'thing dial in lab\n    name "dial"\n    words dial\n    fixed\n'
    '    reading 1\n'
    'thing statue in lab\n    name "statue"\n    words statue\n    fixed\n'
    'verb "type"\n    type text into noun\n'
    'verb "set", "adjust"\n    set noun to text\n'
    'on type terminal\n'
    '    if typed is "1451"\n'
    '        say "Access granted."\n'
    '    else\n'
    '        if typed is "open sesame"\n'
    '            say "A drawer slides open."\n'
    '        else\n'
    '            say "Rejected: ${typed}."\n'
    'on set dial\n'
    '    if typed_number > 0\n'
    '        if typed_number < 5\n'
    '            change dial.reading to typed_number\n'
    '            say "The dial clicks to ${dial.reading}."\n'
    '            stop\n'
    '    say "No setting called ${typed}."\n'
)


def _play(src, script):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(script) + ["quit", "y"])
    try:
        VM(load(story), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_typed_compares_prints_and_numbers():
    out = _play(GAME, [
        "type 1451 into terminal",       # a code that is no dictionary word
        "type open sesame into terminal", # a two-word literal, in order
        "type sesame open into terminal", # order matters
        "type swordfish into terminal",   # unknown word still echoes
        "set dial to 3",
        "set dial to 9",                  # a number outside the author's range
        "set dial to fun",                # not a number at all
    ])
    assert "Access granted." in out
    assert "A drawer slides open." in out
    assert "Rejected: sesame open." in out
    assert "Rejected: swordfish." in out
    assert "The dial clicks to 3." in out
    assert "No setting called 9." in out
    assert "No setting called fun." in out


def test_unclaimed_set_falls_to_the_standard_refusal():
    # SET STATUE TO 1: the statue has no on set, so the action falls through
    # the ordinary chain; nothing about the slot preempts normal dispatch.
    out = _play(GAME, ["set statue to 1"])
    assert "clicks" not in out and "No setting" not in out


def test_typed_number_facts():
    # The documented facts: digits through and through, at most four of
    # them; anything else reads 0.
    game = GAME + (
        'verb "probe"\n    probe text into noun\n'
        'on probe terminal\n'
        '    say "n=${typed_number}."\n'
    )
    out = _play(game, [
        "probe 9999 into terminal",
        "probe 12345 into terminal",   # five digits: past the honest ceiling
        "probe 12a4 into terminal",    # digits and letters mixed
    ])
    assert "n=9999." in out
    assert out.count("n=0.") == 2


def test_typed_misuse_and_length_are_compile_errors():
    bad = GAME + 'on start\n    let x = typed\n'
    with pytest.raises(ArcError, match="typed is text"):
        generate(analyze(cosmos.combined_program(parse(bad))))
    bad = GAME.replace('"open sesame"', '"one two three four"')
    with pytest.raises(ArcError, match="one to three words"):
        generate(analyze(cosmos.combined_program(parse(bad))))


def test_a_story_global_named_typed_wins():
    # Data beats the reading, the rule everywhere: a game that declares its
    # own `typed` global owns the name outright.
    game = (
        'global typed = 7\n'
        'game\n    title "Shadow"\n    author "T"\n    start lab\n'
        'room lab\n    name "Lab"\n    desc "Bare."\n'
        'on start\n    say "typed is ${typed}."\n'
    )
    out = _play(game, [])
    assert "typed is 7." in out


def test_the_slot_speaks_german_and_spanish():
    # The matcher lives in the agnostic skeleton, so a pack needs nothing:
    # the same verb shape reads typed in every language.
    de = (
        'summon.language "german"\n'
        'game\n    title "Tipp"\n    author "T"\n    start labor\n'
        'room labor\n    name "Labor"\n    desc "Ein Terminal summt."\n'
        'thing terminal in labor\n    name "Terminal"\n    neuter\n'
        '    words terminal\n    fixed\n'
        'verb "tippe"\n    tippe text in noun\n'
        'on tippe terminal\n'
        '    if typed is "1451"\n'
        '        say "Zugang gewährt."\n'
        '    else\n'
        '        say "Abgelehnt: ${typed}."\n'
    )
    out = _play(de, ["tippe 1451 in terminal", "tippe unsinn in terminal"])
    assert "Zugang gewährt." in out and "Abgelehnt: unsinn." in out

    es = (
        'summon.language "spanish"\n'
        'game\n    title "Teclea"\n    author "T"\n    start sala\n'
        'room sala\n    name "Sala"\n    desc "Una terminal zumba."\n'
        'thing terminal in sala\n    name "terminal"\n    feminine\n'
        '    words terminal\n    fixed\n'
        'verb "teclea"\n    teclea text en noun\n'
        'on teclea terminal\n'
        '    if typed is "1451"\n'
        '        say "Acceso concedido."\n'
        '    else\n'
        '        say "Rechazado: ${typed}."\n'
    )
    out = _play(es, ["teclea 1451 en terminal", "teclea tonteria en terminal"])
    assert "Acceso concedido." in out and "Rechazado: tonteria." in out
