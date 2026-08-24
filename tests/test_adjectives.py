# test_adjectives.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The adjective marker and the ZIL match classes (docs/01 chapter 14): a
`words` entry with a leading > is ordinary vocabulary AND the object's
adjective, the qualifier class. Matching scores in Infocom's classes,
adjective+noun above noun-only above adjective-only, and only the highest
class present survives: one noun match beats every adjective-only match in
scope, a unique adjective-only match still binds (the sausage rule), and a
shared one asks. In German, an unknown typed word sheds an adjective ending
and is accepted only when the stem is a marked adjective, so one declared
stem carries every declined form; nouns never strip (the D ruling)."""

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
    'game\n    title "Z"\n    start lounge\n'
    'room lounge\n    name "Lounge"\n    desc "A lounge."\n'
    'thing couch in lounge\n    name "red couch"\n    words couch, sofa, >red\n'
    '    fixed\n'
    '    on examine\n        say "[COUCH]"\n        stop\n'
    'thing guitar in lounge\n    name "red guitar"\n    words guitar, >red\n'
    '    on examine\n        say "[GUITAR]"\n        stop\n'
    'thing sausage in lounge\n    name "green sausage"\n'
    '    words sausage, >green\n'
    '    on examine\n        say "[SAUSAGE]"\n        stop\n'
    'thing chest of container in lounge\n    name "wooden chest"\n'
    '    words #chest, box, trunk, >wooden, >heavy\n'
    '    openable\n'
    '    on examine\n        say "[CHEST]"\n        stop\n'
)


def test_a_unique_adjective_binds_the_sausage_rule():
    # Only the sausage is green: the lone adjective finds it, class 1
    # unopposed, exactly Infocom's rule.
    out = _replies(GAME, ["examine green"])
    assert "[SAUSAGE]" in out


def test_a_shared_adjective_asks_the_ruled_sentence():
    out = _replies(GAME, ["examine red"])
    assert "Which do you mean, the red couch or the red guitar?" in out


def test_the_ask_takes_a_noun_answer():
    out = _replies(GAME, ["examine red", "couch"])
    assert "[COUCH]" in out


def test_a_noun_match_outranks_adjective_only():
    # "red guitar": the guitar matches adjective+noun (class 3), the couch
    # adjective-only (class 1); no question, the guitar wins.
    out = _replies(GAME, ["examine red guitar"])
    assert "[GUITAR]" in out
    assert "Which do you mean" not in out


def test_trigger_and_adjectives_share_a_declaration():
    # Stefan's declaration: words #chest, box, trunk, >wooden, >heavy.
    out = _replies(GAME, ["examine wooden chest"])
    assert "[CHEST]" in out
    out = _replies(GAME, ["examine heavy trunk"])
    assert "[CHEST]" in out


def test_an_unknown_adjective_stays_honest():
    out = _replies(GAME, ["examine blue"])
    assert 'know the word "blue"' in out


GERMAN = (
    'summon.language "german"\n'
    'game\n    title "H"\n    start halle\n'
    'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
    'thing truhe of container in halle\n    name "rote Truhe"\n'
    '    words truhe, >rot\n    die\n    openable\n'
    '    on examine\n        say "[ROTE-TRUHE]"\n        stop\n'
    'thing kiste of container in halle\n    name "grüne Kiste"\n'
    '    words kiste, >grün\n    die\n    openable\n'
    '    on examine\n        say "[GRUENE-KISTE]"\n        stop\n'
)


def test_german_declined_forms_reach_the_stem():
    # One declared stem (>rot), every ending typed: the strip sheds
    # en/er/es/em and the bare e, and the stem matches.
    for form in ("rote", "roten", "roter", "rotes", "rotem"):
        out = _replies(GERMAN, [f"untersuche {form} truhe"])
        assert "[ROTE-TRUHE]" in out, form


def test_german_strip_composes_with_the_fold_table():
    # grün declared once: the umlaut form declines ("grüne") and the
    # crossword sibling declines too ("gruenen"), through fold plus strip.
    out = _replies(GERMAN, ["untersuche die grüne kiste"])
    assert "[GRUENE-KISTE]" in out
    out = _replies(GERMAN, ["untersuche gruenen kiste"])
    assert "[GRUENE-KISTE]" in out


def test_german_nouns_never_strip():
    # The D ruling stands: noun forms are declaration work, and an unknown
    # noun inflection is reported, never dissolved.
    out = _replies(GERMAN, ["untersuche truhen"])
    assert 'kennt diese Geschichte nicht' in out


def test_german_garbage_never_strips():
    out = _replies(GERMAN, ["untersuche xyzen truhe"])
    assert '"xyzen"' in out


def test_games_without_markers_record_nothing():
    w = analyze(cosmos.combined_program(parse(
        'game\n    title "E"\n    start r\nroom r\n    name "R"\n    desc "x"\n'
    )))
    assert w.uses_adjectives is False
