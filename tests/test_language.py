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


SPANISH_INFINITIVE = (
    'summon.language "spanish"\n'
    'game\n    title "I"\n    start r\n'
    'room r\n    name "R"\n    desc "Una sala."\n'
    'verb "zumba"\n    act_zumba\n'
    'on act_zumba\n    say "[ZUMBIDO]"\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_spanish_infinitive_retry_on_frotz(tmp_path):
    # The PunyInformES trick: an unknown first word ending in -r loses the -r in
    # the text buffer and the command re-tokenizes, so a regular infinitive finds
    # its imperative: "zumbar" reaches the verb declared only as "zumba".
    story = tmp_path / "i.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(SPANISH_INFINITIVE)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="zumbar\nzumba\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("[ZUMBIDO]") == 2  # the infinitive and the imperative both fire


PRONOUN_GAME = (
    'game\n    title "P"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing lamp in hall\n    name "brass lamp"\n    words brass, lamp\n'
    '    desc "A small brass lamp."\n'
    'thing box of container in hall\n    name "pine box"\n    words pine, box\n'
    '    openable\n    open\n'
    'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
    'thing marta of character in hall\n    name "Marta"\n    words marta\n'
    '    named\n    feminine\n    desc "She watches you evenly."\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_english_pronouns_on_frotz(tmp_path):
    # Part 1 of the pronoun work (docs/02 section 8a): "it" remembers the last
    # thing, "her"/"him" the last character by gender, a pronoun binds as a
    # second noun ("put coin in it"), and a referent that left scope answers
    # with the honest "you see nothing of the sort".
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(PRONOUN_GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take lamp\nx it\nx marta\nx her\nx box\nput coin in it\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("A small brass lamp.") == 1  # x it after take lamp
    assert out.count("She watches you evenly.") == 2  # x marta, then x her
    assert "Done." in out  # put coin in it: the pronoun bound as second noun


def test_the_second_noun_binds_a_pronoun():
    # A resolved SECOND noun becomes a pronoun referent, so a character named
    # only as the recipient of a two-object verb answers to "her" afterwards
    # (headless, so it runs without Frotz). Marta is never the primary noun.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    story = load(generate(analyze(cosmos.combined_program(parse(PRONOUN_GAME)))))
    io = CaptureIO(script=["take lamp", "show lamp to marta", "x her",
                           "quit", "y"])
    VM(story, io).run(max_steps=5_000_000)
    text = io.text
    at = text.index(">x her")
    # "her" resolved to Marta though she was only ever the second noun.
    assert "She watches you evenly." in text[at:at + 120]


GERMAN_PRONOUNS = (
    'summon.language "german"\n'
    'game\n    title "P"\n    start raum\n'
    'room raum\n    name "Raum"\n    desc "Ein Raum."\n'
    'thing lampe in raum\n    name "Lampe"\n    words lampe\n    die\n'
    '    desc "Eine kleine Lampe."\n'
    'thing schluessel in raum\n    name "Schluessel"\n    words schluessel\n    der\n'
    '    desc "Ein kalter Schluessel."\n'
    'thing buch in raum\n    name "Buch"\n    words buch\n    das\n'
    '    desc "Ein duennes Buch."\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_grammatical_pronouns_on_frotz(tmp_path):
    # German pronouns follow grammatical gender: die Lampe is "sie", der
    # Schluessel "ihn", das Buch "es" (accusative, the object of a command).
    story = tmp_path / "g.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GERMAN_PRONOUNS)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="nimm die lampe\nuntersuche sie\nnimm den schluessel\n"
        "untersuche ihn\nnimm das buch\nuntersuche es\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Eine kleine Lampe." in out
    assert "Ein kalter Schluessel." in out
    assert "Ein duennes Buch." in out


SPANISH_CLITICS = (
    'summon.language "spanish"\n'
    'game\n    title "C"\n    start sala\n'
    'room sala\n    name "Sala"\n    desc "Una sala."\n'
    'thing lampara in sala\n    name "lampara"\n    words lampara\n'
    '    desc "Una lampara pequena."\n'
    'thing libro in sala\n    name "libro"\n    words libro\n'
    '    desc "Un libro fino."\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_spanish_clitic_pronouns_on_frotz(tmp_path):
    # Part 2 of the pronoun work: an unknown first word ending in -lo/-la
    # splits its clitic off ("cogela" -> "coge" + the pending la), the verb
    # re-resolves, and the pronoun's referent becomes the noun. Chains with the
    # infinitive retry: "cogerlo" -> "coger" -> "coge". The bare article "la"
    # in "mira la lampara" stays an article (clitics are never dictionary
    # words), and the plural "cogelos" fails honestly until a plural model.
    story = tmp_path / "c.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(SPANISH_CLITICS)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="mira la lampara\ncógela\nmira el libro\ncogele\ncogerlo\ncogelos\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Una lampara pequena." in out  # the article resolved the lamp
    # cógela, typed WITH its accent: the fold (PunyInformES's ProcessChars)
    # de-accents the buffer, then the clitic split takes the lamp. And cogele,
    # the leismo form, takes the masculine referent like cogelo.
    assert "Cogida." in out
    assert out.count("Cogido.") == 1  # cogele: the leismo clitic took the book
    # cogerlo while already holding it: the chain (clitic split, then the -r
    # retry) resolved to take + libro, and take answers "you already have it".
    assert "Ya tienes el libro." in out
    assert "No ves nada de eso" in out  # cogelos: empty plural slot, honest
