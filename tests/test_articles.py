# test_articles.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Articles. The `named` attribute suppresses the article entirely (Linda, not
"The Linda"); the indefinite article auto-picks a/an from the name's first letter
("a gold coin", "an iron sword"). Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "P"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A hall."\n'
    'thing linda of character in hall\n    name "Linda"\n    words linda\n    named\n'
    'thing sword in hall\n    name "iron sword"\n    words iron, sword\n'
    'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
)


def test_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_named_suppresses_article_on_frotz(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="push linda\npush sword\n",  # the default uses "${The noun} holds firm."
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Linda holds firm." in out  # named: no article
    assert "The iron sword holds firm." in out  # ordinary: keeps the article
    assert "The Linda" not in out  # the bug this prevents


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_indefinite_a_an_on_frotz(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],  # the room listing uses ${a obj}
        input="look\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You can see a gold coin here." in out  # consonant -> a
    assert "You can see an iron sword here." in out  # vowel -> an
    assert "You can see Linda here." in out  # named -> no article
    assert "a iron" not in out and "an gold" not in out


# The article words live in the language layer (art_the / art_a blocks), so a game
# (or a language pack) can override them, and the compiler derives `feminine` from
# a name ending in -a for a gendered language to read.
GENDER_GAME = (
    'game\n    title "G"\n    start sala\n'
    'room sala\n    name "Sala"\n    desc "Una sala."\n'
    'thing lampara in sala\n    name "lampara"\n    words lampara\n'
    '    on examine\n        say "${The lampara}, ${a lampara}."\n        stop\n'
    'thing libro in sala\n    name "libro"\n    words libro\n'
    '    on examine\n        say "${The libro}, ${a libro}."\n        stop\n'
    'block art_the(o, c)\n    if o is feminine\n        show("la ")\n'
    '    else\n        show("el ")\n    print_name(o)\n'
    'block art_a(o, c)\n    if o is feminine\n        show("una ")\n'
    '    else\n        show("un ")\n    print_name(o)\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_gender_articles_override_on_frotz(tmp_path):
    story = tmp_path / "g.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GENDER_GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine lampara\nexamine libro\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "la lampara, una lampara." in out  # -a name: feminine, from art_the/art_a
    assert "el libro, un libro." in out  # default masculine


# A three-gender, case-inflected language (German) declares gender with the article
# der/die/das on the object, and asks for a case with ${the:acc noun}. The gender
# maps to feminine/neuter attributes; the case reaches art_the as a third argument.
# ${the noun} with no tag calls art_the with two arguments, so its third local
# defaults to 0 (nominative). A masculine noun ending in -a ("Gorilla") must stay
# masculine: spelling derivation is off for German.
GERMAN_GAME = (
    'game\n    title "D"\n    start raum\n'
    'summon.language "german"\n'
    'room raum\n    name "Raum"\n    desc "Ein Raum."\n'
    'thing kiste in raum\n    name "Kiste"\n    words kiste\n    die\n'
    '    on examine\n        say "${the kiste}/${the:acc kiste}/${the:dat kiste}"\n        stop\n'
    'thing buch in raum\n    name "Buch"\n    words buch\n    das\n'
    '    on examine\n        say "${the buch}/${the:acc buch}/${the:dat buch}"\n        stop\n'
    'thing gorilla in raum\n    name "Gorilla"\n    words gorilla\n    der\n'
    '    on examine\n        say "${the gorilla}/${the:acc gorilla}/${a:acc gorilla}"\n        stop\n'
)


def _german_lib():
    # The game selects summon.language "german", so a german.granule must be found.
    # Point the resolver at the bundled cosmos/ directory.
    import os
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "cosmos")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_gender_and_case_on_frotz(tmp_path):
    story = tmp_path / "d.z5"
    prog = cosmos.combined_program(
        parse(GERMAN_GAME), lib_dirs=(_german_lib(),), story_dir=_german_lib()
    )
    story.write_bytes(generate(analyze(prog)))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="x kiste\nx buch\nx gorilla\n",  # x is the German examine verb too
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "die Kiste/die Kiste/der Kiste" in out  # feminine: nom/acc same, dat der
    assert "das Buch/das Buch/dem Buch" in out  # neuter: nom/acc das, dat dem
    assert "der Gorilla/den Gorilla/einen Gorilla" in out  # masculine, not feminine


OVERRIDES = (
    'game\n    title "O"\n    start r\n'
    'room r\n    name "R"\n    desc "A room."\n'
    'thing water in r\n    name "water"\n    words water\n    fixed\n'
    '    indefinite "some"\n'
    'thing box of container in r\n    name "pine box"\n    words pine, box\n'
    '    openable\n    open false\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_article_override_and_closed_qualifier_on_frotz(tmp_path):
    # `indefinite "some"` overrides the derived a/an (Pablo Martinez's request:
    # per-object articles), and a closed openable announces itself in the
    # listing, the PunyInform qualifier.
    story = tmp_path / "o.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(OVERRIDES)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="open box\nlook\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You can see some water here." in out  # the override
    assert "You can see a pine box (closed) here." in out  # before opening
    assert "You can see a pine box here." in out  # after: qualifier gone
