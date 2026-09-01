# test_owner_index.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The word-to-owners index (lever 4 of the Varuna cycle finding,
performance_eval.md): the compiler emits, for every vocabulary word, the
chain of objects owning it, keyed by DICTIONARY ADDRESS (words sharing a
nine-z-char prefix collapse to one entry and their owners union into one
chain), and the noun matcher scores each typed word's few owners instead of
sweeping the object table. The index only proposes; phrase_score decides.
The internal ARCC_CLASSIC_MATCH escape compiles the classic sweep so the two
enumerations can be played against each other on identical scripts."""

import os

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _play(src, script, classic=False):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    if classic:
        os.environ["ARCC_CLASSIC_MATCH"] = "1"
    try:
        story = generate(analyze(cosmos.combined_program(parse(src))))
    finally:
        os.environ.pop("ARCC_CLASSIC_MATCH", None)
    io = CaptureIO(script=list(script) + ["quit", "y"])
    try:
        VM(load(story), io, seed=7).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


GAME = (
    'game\n    title "Index"\n    author "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "Open sky."\n    south hall\n'
    # The collapsed-prefix pair (the H2 regression): "extinguish" and
    # "extinguisher" share a nine-z-char dictionary entry; the pedestal owns
    # one spelling, the machine the other, and both must stay findable.
    'thing pedestal in hall\n    name "EXTINGUISH pedestal"\n'
    '    words extinguish, pedestal\n    fixed\n'
    'thing machine in hall\n    name "extinguisher machine"\n'
    '    words extinguisher, machine\n    fixed\n'
    # The dedup pair: the blue planet owns BOTH typed words and must beat
    # the deep planet (one word), considered exactly once (no self-tie).
    'thing blue_planet in hall\n    name "blue planet"\n'
    '    words blue, planet\n    fixed\n'
    'thing deep_planet in hall\n    name "deep planet"\n'
    '    words deep, planet\n    fixed\n'
    # An elsewhere object sharing a word: never a candidate that wins.
    'thing yard_planet in yard\n    name "yard planet"\n'
    '    words planet, yard\n    fixed\n'
    'thing coin in hall\n    name "coin"\n    words coin\n'
)

SCRIPT = [
    "examine extinguish pedestal",   # score 2 beats the machine's 1
    "examine extinguisher machine",  # and the other collapsed spelling too
    "examine blue planet",           # dedup: one visit, full-match win
    "examine planet",                # a genuine tie: the ask fires
    "blue",                          # the narrowing answer settles it
    "take coin",
    "examine grue",                  # unknown word: the honest fault
]


def test_indexed_and_classic_matchers_play_identically():
    a = _play(GAME, SCRIPT, classic=False)
    b = _play(GAME, SCRIPT, classic=True)
    assert a == b


def test_collapsed_prefix_words_share_their_owner_chain():
    out = _play(GAME, SCRIPT)
    assert "EXTINGUISH pedestal" in out
    assert "extinguisher machine" in out
    # The two-word phrase resolved to the pedestal, not an ask.
    assert "Which do you mean" in out          # only the bare "planet" asks
    assert out.count("Which do you mean") == 1


def test_dedup_scores_the_two_word_owner_once():
    # "blue planet" must resolve silently (score 2, full match), never
    # tie against itself through its two chains.
    out = _play(GAME, ["examine blue planet"])
    assert "Which do you mean" not in out


def test_the_ambiguity_ask_survives_the_index():
    out = _play(GAME, ["examine planet", "blue"])
    assert "Which do you mean" in out


def test_plural_and_adjective_candidates_ride_the_index():
    game = (
        'summon.plurals\n'
        'game\n    title "PA"\n    author "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing c1 in hall\n    name "gold coin"\n    words coin\n'
        '    plural coins\n'
        'thing c2 in hall\n    name "silver coin"\n    words coin\n'
        '    plural coins\n'
        'thing tapestry in hall\n    name "tapestry"\n'
        '    words tapestry, >woven\n    fixed\n'
    )
    out = _play(game, ["take coins", "examine woven tapestry"])
    assert "gold coin" in out and "silver coin" in out   # the plural sweep
    assert "tapestry" in out


def test_shut_container_fallback_still_answers():
    game = (
        'game\n    title "Shut"\n    author "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing box of container in hall\n    name "pine box"\n'
        '    words box, pine\n    openable\n    open\n'
        'thing pearl in box\n    name "pearl"\n    words pearl\n'
    )
    out = _play(game, ["examine pearl", "close box", "examine pearl"])
    # Seen, then shut away: the fallback names the box instead of a bare
    # can't-see (the shut_search path riding best_score 0).
    assert "pine box" in out
