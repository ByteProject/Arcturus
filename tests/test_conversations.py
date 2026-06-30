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
    # talk, pick 1 (weather: reveals secret, then weather drops off), 0 to end.
    # The menu is painted in the upper window, so dumb Frotz dumps its repaints
    # inline; assertions are substring-presence, order-independent.
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="talk to pat\n1\n0\nquit\ny\n",
        capture_output=True, text=True, timeout=20,
    ).stdout

    # The numbered menu, weather first; the hidden secret starts off the list.
    assert "Talk to Pat about:" in out
    assert "1. the weather" in out
    assert "2. the city" in out

    # Picking 1 runs the exchange in the main window.
    assert 'You: "Some weather we\'re having."' in out
    assert 'Pat: "Could be worse."' in out

    # After the pick the menu repaints: weather has dropped off (discussed) and the
    # revealed secret appears. That weather is gone is provable from the renumber -
    # the city is now 1 and the secret is 2, not 2 and 3.
    assert "1. the city" in out
    assert "2. the secret" in out

    # 0 ends the conversation and returns to the main prompt.
    assert "You let the conversation rest there." in out


# When both presentations are summoned, the menu wins: ask/tell stop dispatching
# topics and redirect the player to TALK TO (the mutual exclusion).
BOTH = '''game
    title "Both"
    start hall
summon.extendedverbs
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
'''


def test_both_summoned_compiles():
    assert generate(analyze(cosmos.combined_program(parse(BOTH))))[0x00] == 5


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_menu_wins_over_ask_tell_on_frotz(tmp_path):
    img = generate(analyze(cosmos.combined_program(parse(BOTH))))
    story = tmp_path / "both.z5"
    story.write_bytes(img)
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="ask pat about weather\ntalk to pat\n1\n0\nquit\ny\n",
        capture_output=True, text=True, timeout=20,
    ).stdout

    # ask redirects to TALK TO and does NOT run the topic.
    ask_part = out.split("Talk to Pat about:")[0]
    assert "just TALK TO Pat" in ask_part
    assert "Could be worse." not in ask_part

    # The menu still runs the topic when picked.
    assert "Could be worse." in out
