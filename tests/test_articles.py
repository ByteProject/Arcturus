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
