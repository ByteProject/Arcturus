# test_conversations_menu_spacing.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The conversations menu (docs/01 chapter 22): each exchange is its own
paragraph (fos13's report, 2026-10-23: menu picks happen inside one TALK
TO, and the question-and-answer pairs stacked line on line). The first
sits directly under the command like any reply; each later one, and the
closing line after any exchange, opens a new paragraph."""

import os

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "granules",
                       "conversations.storyarc")


def _talk(keys):
    with open(EXAMPLE, encoding="utf-8") as fh:
        src = fh.read()
    story = generate(analyze(cosmos.combined_program(
        parse(src, "conversations.storyarc"), story_dir=os.path.dirname(EXAMPLE))))
    io = CaptureIO(script=["talk to esme"] + list(keys) + ["look"])
    try:
        VM(load(story), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    t = io.text
    return t[t.find(">talk to esme"):t.find(">look")]


def test_each_exchange_is_its_own_paragraph():
    out = _talk(["1", "2", "0"])
    assert out.startswith('>talk to esme\nYou: "')                 # first: under the command
    assert 'make."\n\nYou: "This road.' in out                      # later: its own paragraph
    assert 'sat down."\n\nYou let the conversation rest there.' in out


def test_leaving_at_once_stays_one_line():
    assert _talk(["0"]).startswith(">talk to esme\nYou let the conversation rest there.")


def test_a_topic_that_reveals_itself_stays_in_the_menu():
    # fos13 (2026-10-24): repeated conversations. The menu retired a topic
    # AFTER its body ran, so the body's own `reveal` was undone; it retires
    # first now, and the topic stays.
    src = (
        'summon.conversations\n'
        'game\n    title "R"\n    start garden\n'
        'room garden\n    name "Garden"\n    desc "A garden."\n'
        'thing esme of character in garden\n    name "Esme"\n    named\n    words esme\n'
        '    topic weather "the weather"\n        you "How\'s the weather?"\n'
        '        reply "Grey, as always."\n        reveal weather\n'
        '    topic road "the road"\n        you "And the road?"\n        reply "Long."\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=["talk to esme", "1", "1", "1", "0"])
    try:
        VM(load(story), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    assert io.text.count("Grey, as always.") == 3
