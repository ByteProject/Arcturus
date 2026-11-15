# test_exit_tiebreak.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Leaving one of two alike perches leaves the one you are on
(improvmonster's report, 2026-11-15): standing on the left of two mats,
EXIT MAT asked "which do you mean, the left mat or the right mat?". The
tiebreak now gives EXIT the player's own perch, and take_off (English's
GET OFF X, which turns into an exit once the noun is known) either side:
the perch or a held thing. A bare GET OFF on something leaves it, like
GET OUT and GET DOWN. Every pack."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


EN = (
    'game\n    title "T"\n    start dojo\n'
    'room dojo\n    name "Dojo"\n    desc "Mats."\n'
    'thing lmat of supporter in dojo\n    name "left mat"\n    words mat, >left\n'
    'thing rmat of supporter in dojo\n    name "right mat"\n    words mat, >right\n'
    'thing hat in dojo\n    name "hat"\n    words hat\n    wearable\n'
)


def test_every_phrasing_leaves_the_mat_underfoot():
    out = _run(EN, ["stand on left mat", "exit mat",
                    "stand on right mat", "leave mat",
                    "stand on left mat", "get off mat",
                    "stand on right mat", "get off the mat"])
    assert "Which do you mean" not in out
    assert out.count("You get off the left mat.") == 2
    assert out.count("You get off the right mat.") == 2


def test_off_the_mats_the_question_stands():
    out = _run(EN, ["exit mat"])
    assert "Which do you mean, the left mat or the right mat?" in out


def test_a_bare_get_off_leaves_the_perch():
    out = _run(EN, ["stand on left mat", "get off"])
    assert "You get off the left mat." in out
    assert "requires you to be more specific" not in out


def test_get_off_still_takes_off_what_is_worn():
    out = _run(EN, ["take hat", "wear hat", "get off hat"])
    assert "Which do you mean" not in out
    assert "You get off" not in out


DE = (
    'summon.language "german"\n'
    'game\n    title "T"\n    start dojo\n'
    'room dojo\n    name "Dojo"\n    desc "Matten."\n'
    'thing lmat of supporter in dojo\n    name "Strohmatte"\n    words matte, strohmatte, >stroh\n    die\n'
    'thing rmat of supporter in dojo\n    name "Gummimatte"\n    words matte, gummimatte, >gummi\n    die\n'
)


def test_german_leaves_the_mat_underfoot():
    out = _run(DE, ["stell dich auf die strohmatte", "verlasse matte",
                    "stell dich auf die gummimatte", "verlasse die matte"])
    assert "Du stellst dich auf die Strohmatte." in out
    assert "Welche" not in out
    assert "Du steigst von der Strohmatte herunter." in out
    assert "Du steigst von der Gummimatte herunter." in out


ES = (
    'summon.language "spanish"\n'
    'game\n    title "T"\n    start dojo\n'
    'room dojo\n    name "Dojo"\n    desc "Esterillas."\n'
    'thing lmat of supporter in dojo\n    name "esterilla izquierda"\n'
    '    words esterilla, >izquierda\n    feminine\n'
    'thing rmat of supporter in dojo\n    name "esterilla derecha"\n'
    '    words esterilla, >derecha\n    feminine\n'
)


def test_spanish_leaves_the_mat_underfoot():
    out = _run(ES, ["siéntate en la esterilla izquierda", "sal de la esterilla",
                    "siéntate en la esterilla derecha", "sal de la esterilla"])
    assert "cuál" not in out.lower()
    parts = out.split("sal de la esterilla")
    assert "Te sientas en la esterilla izquierda." in out
    assert "Te levantas de la esterilla izquierda." in parts[1]
    assert "Te levantas de la esterilla derecha." in parts[2]
