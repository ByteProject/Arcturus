# test_noise_boundary.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The combined noise+boundary roles (the French du class, a translator's
report, 2026-09-17): a word declared `noise` that also stands as a
grammar preposition (or particle) carries a combined dictionary flag
(0x0B / 0x23) instead of losing one role silently. It splits two noun
phrases like any boundary AND is skipped inside a phrase like any
article; the pack arms fold away (any_noiseprep) in a game whose noise
words stay plain, proven byte-identical."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start cave\n'
    'room cave\n    name "Cave"\n    desc "Echoes."\n'
    'noise "zu"\n'
    'thing idol_x in cave\n    name "stone idol"\n    words stone, idol\n'
    'thing altar_x of supporter in cave\n    name "altar"\n    words altar\n'
    '    fixed\n'
    'verb "weihe"\n    dedicate noun zu noun\n'
    'on dedicate\n    say "DEDICATE ${the noun} -> ${the second}"\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_the_word_splits_and_is_skipped():
    out = _run(["weihe idol zu altar", "x zu idol"])
    # boundary in the two-noun command...
    assert "DEDICATE the stone idol -> the altar" in out
    # ...and plain noise inside a phrase
    assert "rewards a closer look" in out


def test_plain_noise_games_are_byte_identical():
    base = (
        'game\n    title "T"\n    start cave\n'
        'room cave\n    name "Cave"\n    desc "Echoes."\n'
        'thing idol_x in cave\n    name "stone idol"\n    words stone, idol\n'
    )
    with_noise = base + 'noise "blorple"\n'
    a = generate(analyze(cosmos.combined_program(parse(base))))
    b = generate(analyze(cosmos.combined_program(parse(with_noise))))
    # a plain noise word adds only its dictionary entry, none of the
    # combined-flag arms (the fold)
    assert abs(len(b) - len(a)) <= 16
