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
    # An unbundled language is a clean error, not a crash. English (the default),
    # Spanish, and German (both bundled) all combine.
    with pytest.raises(ArcError):
        cosmos.combined_program(parse('summon.language "klingon"\n' + MIN))
    assert cosmos.combined_program(parse(MIN))  # english default works
    assert cosmos.combined_program(parse('summon.language "spanish"\n' + MIN))
    assert cosmos.combined_program(parse('summon.language "german"\n' + MIN))


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


GERMAN_GAME = (
    'summon.language "german"\n'
    'game\n    title "J"\n    start kueche\n'
    'room kueche\n    name "Kueche"\n    desc "Eine Kueche."\n'
    'thing schluessel in kueche\n    name "Schluessel"\n    words schluessel\n    der\n'
    'thing lampe in kueche\n    name "Lampe"\n    words lampe\n    die\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_build_plays_on_frotz(tmp_path):
    # The bundled german.granule: gender declared with der/die/das, and the article
    # inflecting for case through the ${the:...} tags in the messages.
    story = tmp_path / "d.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GERMAN_GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="x schluessel\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "einen Schluessel" in out  # masculine accusative in the room listing
    assert "eine Lampe" in out  # feminine
    assert "An dem Schluessel" in out  # masculine dative, from ${the:dat noun}


GERMAN_SWITCH = (
    'summon.language "german"\n'
    'game\n    title "S"\n    start raum\n'
    'room raum\n    name "Raum"\n    desc "Ein Raum."\n'
    'thing lampe in raum\n    name "Lampe"\n    words lampe\n    die\n    switchable\n'
    '    on switch_on\n        say "[AN]"\n'
    '    on switch_off\n        say "[AUS]"\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_switch_particles_on_frotz(tmp_path):
    # The particle words are declared in german.granule (`particle on "an", "ein"`),
    # not hardcoded in the compiler. The base verb "schalt(e)" combines with a
    # particle before or after the noun; "an"/"ein" switch on, "aus"/"ab" switch off.
    story = tmp_path / "s.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GERMAN_SWITCH)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="schalte die lampe an\nschalte die lampe ein\nschalte an lampe\n"
        "schalte die lampe aus\nschalte die lampe ab\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("[AN]") == 3  # an (after), ein (after), an (before the noun)
    assert out.count("[AUS]") == 2  # aus, ab


GERMAN_LOCK = (
    'summon.language "german"\n'
    'game\n    title "L"\n    start raum\n'
    'room raum\n    name "Raum"\n    desc "Ein Raum."\n    north flur\n'
    'room flur\n    name "Flur"\n    desc "Ein Flur."\n    south raum\n'
    'thing tuer of door in raum, flur\n    name "Tuer"\n    words tuer\n    die\n'
    '    lockable\n    locked\n    unseal_with schluessel\n'
    'thing schluessel in raum\n    name "Schluessel"\n    words schluessel\n    der\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_separable_lock_verbs_on_frotz(tmp_path):
    # The natural German is the separable "schliess die Tuer mit dem Schluessel
    # auf/ab/zu": a base "schliess(e)" verb combines with the auf/zu/ab particles
    # into unlock (auf) and lock (zu, ab). "ab" is also the switch-off particle;
    # compound() disambiguates by the base verb, so it means lock after schliess.
    story = tmp_path / "l.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GERMAN_LOCK)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="nimm schluessel\nschliesse die tuer mit dem schluessel auf\n"
        "schliesse die tuer mit dem schluessel ab\n"
        "schliesse die tuer mit dem schluessel zu\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("Aufgeschlossen.") == 1  # auf -> unlock
    assert out.count("Abgeschlossen.") == 2  # ab and zu -> lock


def test_non_english_game_skips_the_english_default_abbreviations():
    # The baked default is English-tuned; a Spanish game gets no default set (an
    # author runs --make-abbreviations for its own), while English keeps the default.
    from arcturus import codegen, abbrev
    es = analyze(cosmos.combined_program(parse('summon.language "spanish"\n' + MIN)))
    en = analyze(cosmos.combined_program(parse(MIN)))
    assert codegen._abbreviations_for(es) == []
    assert codegen._abbreviations_for(en) == abbrev.DEFAULT_ABBREVS


def test_generic_summon_of_a_language_pack_is_rejected():
    # A language pack self-identifies (`language "spanish"`); summoning it the plain
    # way would leave English baked in, so it errors with a pointer to
    # summon.language rather than build a broken bilingual story.
    with pytest.raises(ArcError):
        cosmos.combined_program(parse("summon spanish.granule\n" + MIN))


def test_summon_language_requires_a_language_pack():
    # summon.language on a granule that is not a language pack (no marker) errors.
    with pytest.raises(ArcError):
        cosmos.combined_program(parse('summon.language "statusline"\n' + MIN))
