# test_conversations.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The conversations granule (sub-step 4): the menu presentation of the `topic`
model. TALK TO a person lists their visible topics numbered; a single keypress
runs one (read_key / the read_char opcode); the menu redraws as topics reveal and
retire; 0 ends it. Built on the same topic table the ask/tell path walks. Driven
on Frotz, one keypress per line (dumb Frotz reads the first char of each line)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


GAME = '''game
    title "ConvMenu"
    start hall
summon.conversations
room hall
    name "Hall"
    desc "A bare hall."
thing pat of person in hall
    name "Pat"
    named
    words pat
    topic weather "the weather" words weather
        you "Some weather we're having."
        reply "Could be worse."
        reveal secret
    topic city "the city" words city
        you "How long have you lived here?"
        reply "All my life."
    topic secret "the secret" words secret hidden once
        reply "All right, all right. The money's in the locker."
'''


def test_conversations_compiles():
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    assert img[0x00] == 5


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_conversation_menu_on_frotz(tmp_path):
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    story = tmp_path / "conv.z5"
    story.write_bytes(img)
    # talk, pick 1 (weather, reveals secret), pick 3 (the secret, once), 0 to end.
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="talk to pat\n1\n3\n0\nquit\ny\n",
        capture_output=True, text=True, timeout=20,
    ).stdout

    # The numbered menu, with the hidden topic absent at first.
    assert "Talk to Pat about:" in out
    assert "1. the weather" in out
    assert "2. the city" in out

    first_menu = out.split("Could be worse.")[0]
    assert "the secret" not in first_menu  # hidden until revealed

    # Picking 1 runs the exchange and reveals the secret as a new numbered option.
    assert 'You: "Some weather we\'re having."' in out
    assert 'Pat: "Could be worse."' in out
    assert "3. the secret" in out

    # Picking 3 runs the secret; `once` retires it, so it is gone from the last menu.
    assert 'Pat: "All right, all right. The money\'s in the locker."' in out
    last_menu = out.split("rest there")[0].rsplit("Talk to Pat about:", 1)[1]
    assert "the secret" not in last_menu

    # 0 ends the conversation and returns to the main prompt.
    assert "You let the conversation rest there." in out
