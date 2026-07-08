# test_containment_nothing.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The containment test is total: `nothing in X` (and `X holds nothing`) is
false, never an illegal @jin with object 0. Field report: a free `on take`
guarding on `noun is in table` sprayed interpreter warnings whenever the
noun was an unknown word (noun = nothing reaches game handlers by design;
the honest refusal lives in the Cosmos default the handler continues to)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hallway\n'
    'room hallway\n    name "Hallway"\n    desc "x"\n'
    'thing lamp in hallway\n    name "lamp"\n    words lamp\n'
    'thing bob of character in hallway\n    name "Bob"\n    words bob\n    named\n'
    'thing test_table of supporter in hallway\n    name "table"\n    words table\n'
    'thing cup in test_table\n    name "cup"\n    words cup\n'
    'on take\n'
    '    if noun is in test_table and bob is in here\n'
    '        say "STOPPED."\n'
    '        stop\n'
    '    continue\n'
    'on push\n'
    '    if test_table holds noun\n'
    '        say "HOLDS."\n'
    '        stop\n'
    '    continue\n'
)


def _play(cmds):
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(story, io).run(max_steps=30_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_unknown_word_is_refused_without_a_jin_warning():
    text = _play(["take sdjfh"])
    assert 'know the word "sdjfh"' in text  # named back (parse_fault 4)
    assert "STOPPED" not in text


def test_the_guard_still_guards():
    text = _play(["take cup", "take lamp"])
    assert "STOPPED." in text
    assert "Got it." in text


def test_holds_with_nothing_is_false():
    text = _play(["push zzzz"])
    assert "HOLDS" not in text
    assert 'know the word "zzzz"' in text


def test_the_article_prints_nothing_for_an_unresolved_object():
    # The same total-operator doctrine for the print path: ${the noun} with
    # noun = nothing prints the word, never an illegal print_obj 0. A bare
    # custom verb is the honest vehicle now that garbage nouns fault before
    # dispatch: the handler runs with noun = nothing only for a bare verb.
    game = GAME + (
        'verb "grope"\n    grope noun\n    grope\n'
        'on grope\n    say "You reach for ${the noun}."\n'
    )
    story = load(generate(analyze(cosmos.combined_program(parse(game)))))
    io = CaptureIO(script=["grope"])
    try:
        VM(story, io).run(max_steps=30_000_000)
    except IndexError:
        pass
    assert "You reach for nothing." in io.text
