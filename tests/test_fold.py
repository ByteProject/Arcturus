# test_fold.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The crossword fold (docs/01 chapter 21): a language pack declares
`fold "ä" "ae"` pairs, and every dictionary word containing a source gains
its folded sibling automatically, the pack's own vocabulary and the game's
words alike. Declare the proper spelling once ("tür", "Spaß"); the
crossword form (tuer, spass) is derived, one-way by design. A pack without
folds (English, Spanish) carries none of the machinery."""

import contextlib
import io

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _replies(src, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io_ = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io_).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io_.text


GAME = (
    'summon.language "german"\n'
    'game\n    title "F"\n    start keller\n'
    'room keller\n    name "Keller"\n    desc "Ein Keller."\n    south hof\n'
    'room hof\n    name "Hof"\n    desc "Ein Hof."\n    north keller\n'
    'thing tuer of door in keller, hof\n    name "Tür"\n    words tür, türe\n'
    '    die\n'
    'thing spass in keller\n    name "Spaß"\n    words "spaß"\n    der\n'
)


def test_folded_object_words_resolve():
    # The author declares tür and spaß only; the typed crossword forms
    # resolve, and the umlaut spellings keep working.
    out = _replies(GAME, ["untersuche tuer", "untersuche tuere",
                          "nimm spass", "untersuche tür"])
    assert out.count("An der Tür ist nichts Besonderes zu sehen.") == 3
    assert "Du nimmst den Spaß an dich." in out


def test_folded_verbs_and_directions_resolve():
    # The granule declares only the umlaut spellings now (öffne, süden);
    # the folded forms keep working exactly as when they were hand-doubled.
    out = _replies(GAME, ["oeffne tuer", "hoere", "gehe sueden"])
    assert "Geöffnet." in out
    assert "Ein Hof." in out  # sueden walked south
    assert "Du horchst" in out  # hoere is the fold of höre


def test_folded_separable_verb_resolves():
    # "schliesse" is the fold of "schließe" (the ß rule); the entry carries
    # the same verb data, so the plain close works from the sibling.
    out = _replies(GAME, ["oeffne tuer", "schliesse tuer"])
    assert "Geschlossen." in out


def test_collision_keeps_the_declared_word_and_notes():
    # fold("drücke") is "druecke", which this author declared as a THING
    # word: the declared meaning wins, arcc says the verb's sibling was not
    # registered, and the thing stays reachable under its own name.
    src = (
        'summon.language "german"\n'
        'game\n    title "K"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing knopf in r\n    name "Druecke-Schild"\n    words druecke\n'
        '    das\n'
    )
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        generate(analyze(cosmos.combined_program(parse(src))))
    assert 'folded spelling "druecke"' in err.getvalue()
    out = _replies(src, ["untersuche druecke"])
    assert "Druecke-Schild" in out


def test_shared_spelling_between_two_things_asks():
    # fold("maße") is "masse", another thing's declared word: both objects
    # now answer to the typed "masse", which is a genuine ambiguity, and the
    # parser asks instead of silently picking a winner. No note: nothing was
    # lost, the word reaches both meanings.
    src = (
        'summon.language "german"\n'
        'game\n    title "M"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing masse in r\n    name "graue Masse"\n    words masse\n    die\n'
        'thing masze in r\n    name "Maße"\n    words "maße"\n    das\n'
    )
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        generate(analyze(cosmos.combined_program(parse(src))))
    assert "folded spelling" not in err.getvalue()
    out = _replies(src, ["untersuche masse"])
    assert "Was meinst du" in out


def test_plural_group_words_fold():
    # A group word with an umlaut ("münzen") sweeps when typed folded.
    src = (
        'summon.language "german"\n'
        'summon.plurals\n'
        'game\n    title "P"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing m1 in r\n    name "Goldmünze"\n    words goldmünze\n'
        '    plural münzen\n    die\n'
        'thing m2 in r\n    name "Silbermünze"\n    words silbermünze\n'
        '    plural münzen\n    die\n'
    )
    out = _replies(src, ["nimm muenzen"])
    assert "Goldmünze" in out and "Silbermünze" in out


def test_packs_without_folds_carry_nothing():
    # English declares no folds: the world records none and an accented
    # word gains no sibling (the machinery is inert, not merely unused).
    w = analyze(cosmos.combined_program(parse(
        'game\n    title "E"\n    start r\nroom r\n    name "R"\n    desc "x"\n'
    )))
    assert w.folds == []
