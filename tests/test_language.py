# test_language.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The language-layer swap: `summon.language "x"` compiles the x.granule language
pack in place of english.prelude (B7 seam 4). English is the default."""

import pytest

from arcturus import cosmos
from arcturus.errors import ArcError
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

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
    # An unbundled language is a clean error, not a crash. English (the default)
    # and Spanish (bundled) both combine.
    with pytest.raises(ArcError):
        cosmos.combined_program(parse('summon.language "klingon"\n' + MIN))
    assert cosmos.combined_program(parse(MIN))  # english default works
    assert cosmos.combined_program(parse('summon.language "spanish"\n' + MIN))


import shutil
import subprocess


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


SPANISH_GAME = (
    'summon.language "spanish"\n'
    'game\n    title "J"\n    start cocina\n'
    'room cocina\n    name "Cocina"\n    desc "Una cocina."\n'
    'thing lampara in cocina\n    name "lampara de bronce"\n    words lampara\n'
    'thing libro in cocina\n    name "libro rojo"\n    words libro\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_spanish_build_plays_on_frotz(tmp_path):
    story = tmp_path / "j.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(SPANISH_GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="coger lampara\ncoger libro\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "una lampara" in out  # feminine gender derived from the head noun
    assert "un libro" in out  # masculine
    # The take message agrees its participle with the object's gender, no author
    # work: a feminine lampara is "Cogida", a masculine libro "Cogido".
    assert "Cogida." in out
    assert "Cogido." in out


def test_non_english_game_skips_the_english_default_abbreviations():
    # The baked default is English-tuned; a Spanish game gets no default set (an
    # author runs --make-abbreviations for its own), while English keeps the default.
    from arcturus import codegen, abbrev
    es = analyze(cosmos.combined_program(parse('summon.language "spanish"\n' + MIN)))
    en = analyze(cosmos.combined_program(parse(MIN)))
    assert codegen._abbreviations_for(es) == []
    assert codegen._abbreviations_for(en) == abbrev.DEFAULT_ABBREVS
