# test_hex_literals.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""0xFF literals (auraes's ask, 2026-09-28), and the article twin's low
byte read with one band (his byte-saving note): the sentence-initial
capital of a hand-set article still prints."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
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
        pass
    return io.text


def test_hex_literals_are_numbers():
    src = (
        'constant MASK = 0x0B\n'
        'game\n    title "H"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'on start\n'
        '    say "${0xFF} ${MASK} ${band(0xFF0F, 0x00FF)}"\n'
    )
    assert "255 11 15" in _run(src, [])


def test_hex_needs_digits_and_fits():
    with pytest.raises(ArcError):
        parse("constant M = 0x\n")
    with pytest.raises(ArcError):
        parse("constant M = 0x10000\n")


def test_hand_set_article_still_capitalizes():
    src = (
        'game\n    title "A"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing water in r\n    name "water"\n    words water\n'
        '    article "the"\n    indefinite "some"\n    fixed\n'
    )
    out = _run(src, ["take water", "look"])
    assert "The water stays exactly where it is." in out
    assert "You can see some water here." in out
