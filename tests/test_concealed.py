# test_concealed.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Concealment expires on acquisition (auraes's report, 2026-09-13: a
concealed thing taken and dropped went invisible again while still sitting
there). Concealed means "not yet noticed"; gain, the one acquisition path,
clears it, so a dropped thing lists like anything else. The clear folds
away behind any_concealed, which counts runtime `now x is concealed`
statements too, not only declarations."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start storeroom\n'
    'room storeroom\n    name "Storeroom"\n    desc "Crates of lamp oil."\n'
    'thing lens in storeroom\n    name "spare lens"\n    words lens\n'
    '    concealed\n'
)

# Nothing DECLARES concealed here; only play conceals the mark. The fold
# must count the `now` statement, or gain's clear would fold away from
# under a game that conceals things at runtime only.
RUNTIME = (
    'game\n    title "T"\n    start cellar\n'
    'room cellar\n    name "Cellar"\n    desc "Bare stone."\n'
    'thing mark in cellar\n    name "chalk mark"\n    words mark, chalk\n'
    'verb "smudge"\n    smudge\n'
    'on smudge\n    now mark is concealed\n    say "Smudged."\n'
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


def test_taking_clears_concealment():
    out = _run(["look", "take lens", "drop lens", "look"])
    before, after = out.split("Down it goes.", 1)
    # unlisted while concealed, takeable anyway, listed after the drop
    assert "You can see" not in before
    assert "You take the spare lens with you." in before
    assert "You can see a spare lens here." in after


def test_runtime_concealment_still_expires_on_take():
    out = _run(["smudge", "look", "take mark", "drop mark", "look"],
               game=RUNTIME)
    smudged = out.split("Smudged.", 1)[1]
    # concealed by play: the look after SMUDGE omits it
    assert "mark" not in smudged.split("take mark")[0].split("Cellar", 1)[1]
    # taken and dropped: gain cleared the runtime-set flag, so it lists
    assert "mark" in smudged.rsplit("Cellar", 1)[1]
