# test_grains.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Scenery grains (B4.5e.5): a grain word answers the verbs it names with its
response, and any other action on it gets the scenery default. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Grain Test"\n'
    '    start gallery\n'
    'room gallery\n'
    '    name "The Gallery"\n'
    '    desc "A long gallery."\n'
    '    grains\n'
    '        examine "painting" or "portrait" say "A faded portrait of a duke."\n'
)


def test_grain_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_grain_on_frotz(tmp_path):
    story = tmp_path / "g.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine painting\ntake portrait\n",  # answered verb, then not
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "A faded portrait of a duke." in out  # the grain answers examine
    assert "Just some scenery. Don't worry about it." in out  # the scenery default


SHARED_WORD = (
    'game\n'
    '    title "Echo Test"\n'
    '    start nave\n'
    'room nave\n'
    '    name "The Nave"\n'
    '    desc "A tall nave. The crypt is down."\n'
    '    down crypt\n'
    '    grains\n'
    '        examine "echo" say "It rings high among the vaults."\n'
    'room crypt\n'
    '    name "The Crypt"\n'
    '    desc "A low crypt. The nave is up."\n'
    '    up nave\n'
    '    grains\n'
    '        examine "echo" say "It dies against the packed earth."\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_same_grain_word_in_two_rooms_on_frotz(tmp_path):
    # One dictionary word, two grains in two rooms: the word's grain chain is
    # walked and the grain whose owner is in scope answers, so each room keeps
    # its own response (docs/01 section 14).
    story = tmp_path / "e.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(SHARED_WORD)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine echo\ndown\nexamine echo\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "It rings high among the vaults." in out  # the nave's grain
    assert "It dies against the packed earth." in out  # the crypt's own answer


def test_a_word_split_across_two_grain_lines_is_noted(capsys):
    # A word answers with ONE grain, so a second line for the same word on the
    # same owner is dead code: the first grain answers whatever verb is typed
    # and the later line never runs. Silent until a field report caught it
    # (examine "junk" on one line, touch "junk" on the next). The note names
    # both cures.
    game = (
        'game\n    title "T"\n    start lab\n'
        'room lab\n    name "Lab"\n    desc "A lab."\n'
        '    grains\n'
        '        examine "junk" say "It\'s useless."\n'
        '        touch "junk" say "It\'s sticky."\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    err = capsys.readouterr().err
    assert "already answers" in err
    assert "one line" in err


def test_the_documented_multi_verb_line_is_quiet(capsys):
    game = (
        'game\n    title "T"\n    start lab\n'
        'room lab\n    name "Lab"\n    desc "A lab."\n'
        '    grains\n'
        '        examine, touch "junk" say "Sticky and useless."\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    assert "already answers" not in capsys.readouterr().err


def test_the_same_word_in_two_rooms_is_quiet(capsys):
    # The documented reuse: one word, different rooms, different answers.
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "H."\n    north cellar\n'
        '    grains\n        examine "steps" say "Worn smooth."\n'
        'room cellar\n    name "Cellar"\n    desc "C."\n    south hall\n'
        '    grains\n        examine "steps" say "Slick with damp."\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    assert "already answers" not in capsys.readouterr().err
