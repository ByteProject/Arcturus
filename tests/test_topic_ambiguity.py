# test_topic_ambiguity.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Shared topic words (docs/01 chapter 17; Charles Moore Jr.'s report,
2026-09-27: ASK ABOUT SMITH ran whichever Smith was declared first). The
words decide where they can (most typed words carried), an umbrella topic
whose every word was typed wins the bare word (the author's own answer),
and a cold tie is asked as dialogue naming only the topics in view; the
next line answers it, or runs as the next command."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'summon.infocom_talking\n'
    'game\n    title "S"\n    start cave\n'
    'room cave\n    name "Cave"\n    desc "Echoes."\n'
    'thing troll of character in cave\n    name "troll"\n    words troll\n'
    '    topic john "John Smith" words john, smith\n'
    '        reply "John? A liar and a thief."\n'
    '    topic mary "Mary Smith" words mary, smith\n'
    '        reply "Mary. She paid her toll."\n'
    '    topic ann "Ann Smith" words ann, smith hidden\n'
    '        reply "Ann? How do you know about Ann?"\n'
    'thing lamp in cave\n    name "lamp"\n    words lamp\n'
)
UMBRELLA = GAME.replace(
    "thing lamp in cave",
    '    topic smiths "the Smiths" words smith\n'
    '        reply "Which Smith? This valley is full of them."\n'
    'thing lamp in cave')


def _run(cmds, src=GAME):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_the_words_decide_where_they_can():
    out = _run(["ask troll about john smith", "ask troll about mary smith"])
    assert "John? A liar" in out
    assert "Mary. She paid" in out


def test_a_cold_tie_asks_as_dialogue_naming_only_known_topics():
    out = _run(["ask troll about smith", "mary"])
    assert 'The troll: "John Smith, or Mary Smith?"' in out
    assert "Ann" not in out                            # hidden: never offered
    assert "Mary. She paid" in out                     # the answer ran the topic


def test_a_change_of_mind_runs_as_the_next_command():
    out = _run(["ask troll about smith", "take lamp", "inventory"])
    assert "You take the lamp with you." in out
    assert out.count(">") == 3                         # no second prompt for it
    assert " a lamp" in out.split(">inventory")[1]


def test_the_umbrella_wins_the_bare_word_without_a_question():
    out = _run(["ask troll about smith", "ask troll about john smith"], UMBRELLA)
    assert "This valley is full of them." in out
    assert "John Smith, or Mary Smith?" not in out
    assert "John? A liar" in out                        # the full name still reaches John
