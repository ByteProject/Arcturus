# test_meta.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Meta verbs (B5.4d.1): score reports, restart confirms, xyzzy winks, and a
cancelled quit does not advance the world. Also the parser's can't-see for an
object named out of scope, including a give recipient. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Meta"\n    start vault\n'
    'room vault\n    name "The Vault"\n    desc "A small vault."\n    east hall\n'
    'room hall\n    name "The Hall"\n    desc "A long hall."\n'
    'thing coin in vault\n    name "gold coin"\n    words gold, coin\n'
    'thing guard of person in vault\n    name "burly guard"\n    words burly, guard\n'
    'thing wizard of person in hall\n    name "old wizard"\n    words old, wizard\n'
)


def test_meta_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_meta_verbs_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    script = (
        "score\n"
        "xyzzy\n"
        "restart\n"
        "no\n"  # decline the restart
        "quit\n"
        "no\n"  # decline the quit
        "take coin\n"  # still playing after both declines
    )
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You have scored" in out
    assert "briefly clever" in out
    assert "Start over from the very beginning?" in out
    assert "Got it." in out  # the game kept running after the declines


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_unseen_recipient_cant_see_on_frotz(tmp_path):
    # The recipient is in another room: "give coin to wizard" must report can't
    # see, not run give against the in-scope guard or an empty recipient.
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take coin\ngive coin to wizard\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You see nothing of the sort here." in out
    assert "doesn't want" not in out  # give never dispatched
    assert "therapy" not in out  # nor the only-animate nudge
