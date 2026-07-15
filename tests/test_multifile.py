# test_multifile.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Multi-file games (a field structure: main.storyarc summoning chapter
files for rooms, items, and message overrides): a summoned .storyarc is a
CHAPTER of the game and ranks as GAME, so its message overrides beat both
the library's and a summoned granule's, in any summon order; a late,
less-specific block silently loses to a chapter that already won. A
.granule stays a granule: above the library, below the game."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

MAIN = (
    'game\n    title "T"\n    start hall\n'
    'summon messages.storyarc\n'
    'summon.extendedverbs\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing rock in hall\n    name "rock"\n    words rock\n'
)

MESSAGES = (
    'block msg_cant_go()\n'
    '    say "No road that way, friend."\n'
    'block msg_rub()\n'
    '    say "The rock is unmoved by affection."\n'
)


def _run(cmds, tmp_path):
    (tmp_path / "messages.storyarc").write_text(MESSAGES)
    story = generate(analyze(cosmos.combined_program(
        parse(MAIN, "main.storyarc"), story_dir=str(tmp_path))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_chapter_overrides_library_and_granule(tmp_path):
    out = _run(["north", "rub rock"], tmp_path)
    assert "No road that way, friend." in out          # beats english.prelude
    assert "The rock is unmoved by affection." in out  # beats extendedverbs
    # And neither default leaked through.
    assert "There's no exit" not in out


# A chapter's VERB overrides a granule's verb of the same word, in ANY summon
# order (the field report: STAND redefined in a chapter still gave the extended
# verb set's "already on your feet", because a chapter's verb rode at granule
# rank and a later-summoned extendedverbs won the word). A chapter now ranks as
# GAME for every declaration, verbs included, not only blocks and handlers.
VERB_MAIN = (
    'game\n    title "T"\n    start hall\n'
    'summon grammar.storyarc\n'          # the chapter, summoned BEFORE ...
    'summon.extendedverbs\n'             # ... the granule that also defines STAND
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing crate in hall\n    name "crate"\n    words crate\n    supporter\n'
)

VERB_CHAPTER = (
    'verb "stand"\n'
    '    stand_on on noun\n'
    'on stand_on\n'
    '    if noun is nothing\n'
    '        say "Stand on what, exactly?"\n'
    '    else\n'
    '        perform("enter", noun)\n'
)


def test_chapter_verb_overrides_a_granule_verb_in_any_order(tmp_path):
    (tmp_path / "grammar.storyarc").write_text(VERB_CHAPTER)
    story = generate(analyze(cosmos.combined_program(
        parse(VERB_MAIN, "main.storyarc"), story_dir=str(tmp_path))))
    io = CaptureIO(script=["stand on crate"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text.split(">stand")[-1]
    assert "Done." in out                          # the chapter's stand_on ran
    assert "already on your feet" not in out       # not the extended STAND
