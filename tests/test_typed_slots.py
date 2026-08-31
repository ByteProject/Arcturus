# test_text_slot.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The typed input slots (docs/01 chapter 14): an author's verb line
declares WHAT it accepts (`letters`, `number`, `anychar`), the matcher
enforces the class so lines route by input kind, and the handler reads the
input back under the slot's own name: ${letters} and ${anychar} are the
words (compared against a literal, the compiler adding the literal's words
to the dictionary itself, or echoed verbatim), `number` the numeric value.
Every reading is raw, so codewords that are no dictionary word still
compare and echo. A game using no typed slot compiles byte-identical."""

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
    'verb "type"\n    type anychar into noun\n'
    'verb "speak"\n    speak letters to noun\n'
    'verb "set", "adjust"\n    set noun to number\n'
    'on type terminal\n'
    '    if anychar is "1451"\n'
    '        say "Access granted."\n'
    '    else\n'
    '        if anychar is "open sesame"\n'
    '            say "A drawer slides open."\n'
    '        else\n'
    '            say "Rejected: ${anychar}."\n'
    'on speak terminal\n'
    '    if letters is "friend"\n'
    '        say "The terminal warms to you."\n'
    '    else\n'
    '        say "Unmoved by ${letters}."\n'
    'on set dial\n'
    '    if number > 0\n'
    '        if number < 5\n'
    '            change dial.reading to number\n'
    '            say "The dial clicks to ${number}."\n'
    '            stop\n'
    '    say "The dial only goes 1 to 4, not ${number}."\n'
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


def test_slots_compare_print_and_route_by_class():
    out = _play(GAME, [
        "type 1451 into terminal",        # anychar takes digits
        "type open sesame into terminal", # a two-word literal, in order
        "type sesame open into terminal", # order matters
        "type swordfish into terminal",   # unknown word still echoes
        "speak friend to terminal",       # letters, the password shape
        "speak k9 to terminal",           # class fails: the LINE does not match
        "set dial to 3",
        "set dial to 9",                  # class passes; the range is the author's
        "set dial to red",                # class fails: no line fits
    ])
    assert "Access granted." in out
    assert "A drawer slides open." in out
    assert "Rejected: sesame open." in out
    assert "Rejected: swordfish." in out
    assert "The terminal warms to you." in out
    assert "The dial clicks to 3." in out
    assert "The dial only goes 1 to 4, not 9." in out
    # The two class failures answer with the no-line-fits message, before
    # any handler: the verb was understood, the input kind was not.
    assert out.count("You lost me after that.") == 2


def test_unclaimed_set_falls_to_the_standard_refusal():
    # SET STATUE TO 1: the statue has no on set, so the action falls through
    # the ordinary chain; nothing about the slot preempts normal dispatch.
    out = _play(GAME, ["set statue to 1"])
    assert "clicks" not in out and "No setting" not in out


def test_number_facts():
    # The documented facts: digits through and through, at most four of
    # them; a five-digit token still matches an anychar line but reads 0.
    game = GAME + (
        'verb "probe"\n    probe anychar into noun\n'
        'on probe terminal\n'
        '    say "n=${number}."\n'
    )
    out = _play(game, [
        "probe 9999 into terminal",
        "probe 12345 into terminal",   # five digits: past the honest ceiling
        "probe 12a4 into terminal",    # digits and letters mixed
    ])
    assert "n=9999." in out
    assert out.count("n=0.") == 2


def test_one_verb_routes_by_input_kind():
    # Two lines, two classes, two actions: the input kind picks the line,
    # the line picks the action. The grammar validates what no handler
    # if-chain could see.
    game = (
        'game\n    title "Route"\n    author "T"\n    start lab\n'
        'room lab\n    name "Lab"\n    desc "A safe."\n'
        'thing safe in lab\n    name "safe"\n    words safe\n    fixed\n'
        'verb "dial"\n'
        '    dial number into noun\n'
        '    whisper letters into noun\n'
        'on dial safe\n    say "Tumblers turn to ${number}."\n'
        'on whisper safe\n    say "You whisper ${letters} to the safe."\n'
    )
    out = _play(game, ["dial 42 into safe", "dial sesame into safe"])
    assert "Tumblers turn to 42." in out
    assert "You whisper sesame to the safe." in out


def test_misuse_and_length_are_compile_errors():
    bad = GAME + 'on start\n    let x = anychar\n'
    with pytest.raises(ArcError, match="holds the slot"):
        generate(analyze(cosmos.combined_program(parse(bad))))
    bad = GAME.replace('"open sesame"', '"one two three four"')
    with pytest.raises(ArcError, match="one to three words"):
        generate(analyze(cosmos.combined_program(parse(bad))))


def test_a_story_global_named_letters_wins():
    # Data beats the reading, the rule everywhere: a game that declares its
    # own `letters` global owns the name outright.
    game = (
        'global letters = 7\n'
        'game\n    title "Shadow"\n    author "T"\n    start lab\n'
        'room lab\n    name "Lab"\n    desc "Bare."\n'
        'on start\n    say "letters is ${letters}."\n'
    )
    out = _play(game, [])
    assert "letters is 7." in out


def test_the_slot_speaks_german_and_spanish():
    # The matcher lives in the agnostic skeleton, so a pack needs nothing:
    # the same verb shape reads the slot in every language.
    de = (
        'summon.language "german"\n'
        'game\n    title "Tipp"\n    author "T"\n    start labor\n'
        'room labor\n    name "Labor"\n    desc "Ein Terminal summt."\n'
        'thing terminal in labor\n    name "Terminal"\n    neuter\n'
        '    words terminal\n    fixed\n'
        'verb "tippe"\n    tippe anychar in noun\n'
        'on tippe terminal\n'
        '    if anychar is "1451"\n'
        '        say "Zugang gewährt."\n'
        '    else\n'
        '        say "Abgelehnt: ${anychar}."\n'
    )
    out = _play(de, ["tippe 1451 in terminal", "tippe unsinn in terminal"])
    assert "Zugang gewährt." in out and "Abgelehnt: unsinn." in out

    es = (
        'summon.language "spanish"\n'
        'game\n    title "Teclea"\n    author "T"\n    start sala\n'
        'room sala\n    name "Sala"\n    desc "Una terminal zumba."\n'
        'thing terminal in sala\n    name "terminal"\n    feminine\n'
        '    words terminal\n    fixed\n'
        'verb "teclea"\n    teclea anychar en noun\n'
        'on teclea terminal\n'
        '    if anychar is "1451"\n'
        '        say "Acceso concedido."\n'
        '    else\n'
        '        say "Rechazado: ${anychar}."\n'
    )
    out = _play(es, ["teclea 1451 en terminal", "teclea tonteria en terminal"])
    assert "Acceso concedido." in out and "Rechazado: tonteria." in out
