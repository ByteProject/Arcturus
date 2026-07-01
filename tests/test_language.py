# test_language.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The language-layer swap: `summon.language "x"` compiles the x.prelude language
layer in place of english.prelude (B7 seam 4). English is the default."""

import pytest

from arcturus import cosmos
from arcturus.errors import ArcError
from arcturus.parser import parse

MIN = 'game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "x"\n'


def test_default_language_is_english():
    assert cosmos._language_choice(parse(MIN)) == "english"


def test_summon_language_selects():
    prog = parse('summon.language "spanish"\n' + MIN)
    assert cosmos._language_choice(prog) == "spanish"


def test_summon_language_needs_an_argument():
    with pytest.raises(ArcError):
        cosmos._language_choice(parse("summon.language\n" + MIN))


def test_two_languages_is_an_error():
    prog = parse('summon.language "spanish"\nsummon.language "german"\n' + MIN)
    with pytest.raises(ArcError):
        cosmos._language_choice(prog)


def test_unknown_language_errors_at_combine():
    # No spanish.prelude is bundled yet, so selecting it is a clean error, not a
    # crash. English (the default) always combines.
    with pytest.raises(ArcError):
        cosmos.combined_program(parse('summon.language "spanish"\n' + MIN))
    assert cosmos.combined_program(parse(MIN))  # english default works
