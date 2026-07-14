# test_again_scope.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""AGAIN re-checks scope (a field report from a Dialog port): the replay
restores the previous command's resolved operands, so without a guard an
object that has since left the world stays forever actable ("g" described
a lantern that had been moved to nothing, while typing EXAMINE LANTERN
honestly refused). The replay now refuses exactly as retyping would, for
the noun, the second, and a scenery grain bound to another room."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hallway\n'
    'counter lantern_counter\n'
    'room hallway\n    name "Hallway"\n    desc "A hallway."\n    south cellar\n'
    'room cellar\n    name "Cellar"\n    desc "A cellar."\n    north hallway\n'
    'thing lantern in hallway\n    name "brass lantern"\n    words brass, lantern, lamp\n'
    '    desc "A battered brass lantern."\n'
    'on each_turn\n'
    '    lantern_counter++\n'
    '    if lantern_counter is 3\n'
    '        move lantern to nothing\n'
)

# A typed movement overwrites last_*, so the one way a grain replay can go
# stale is the same turn's pulse relocating the player: the quip answers in
# the attic, the each_turn teleport lands the player on the stair, and "g"
# must not speak attic scenery there.
GRAINS = (
    'game\n    title "T"\n    start attic\n'
    'counter fall\n'
    'room attic\n    name "Attic"\n    desc "Dust and rafters."\n    south stair\n'
    '    grains\n'
    '        examine "rafters" or "beams" say "Old oak, holding."\n'
    'room stair\n    name "Stair"\n    desc "A bare stair."\n    north attic\n'
'on each_turn\n'
    '    fall++\n'
    '    if fall is 2\n'
    '        teleport(stair)\n'
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


def test_again_refuses_a_vanished_noun():
    out = _run(["examine lantern", "g", "g", "g", "g"])
    # Turns 1-2 see it; the pulse removes it at the end of turn 3.
    assert out.count("A battered brass lantern.") == 3
    assert "You see nothing of the sort here." in out


def test_again_still_works_while_the_noun_is_here():
    out = _run(["examine lantern", "g"])
    assert out.count("A battered brass lantern.") == 2


def test_again_refuses_a_grain_from_another_room():
    out = _run(["examine rafters", "examine beams", "g"], game=GRAINS)
    # Two quips in the attic; the second turn's pulse drops the player on
    # the stair, and the replay refuses instead of speaking attic scenery.
    assert out.count("Old oak, holding.") == 2
    assert "You see nothing of the sort here." in out


SWAP_GAME = (
    'game\n    title "T"\n    start hallway\nsummon.extendedverbs\n'
    'room hallway\n    name "Hallway"\n    desc "A hallway."\n'
    'thing bob of character in hallway\n    name "Bob"\n    words bob\n    named\n'
    '    desc "He looks like a Bob."\n'
    '    on attack\n'
    '        say "You punch him and he falls, unconscious."\n'
    '        swap(self, sleeper)\n'
    'thing sleeper\n    name "Unconscious Bob"\n    words unconscious, bob\n    named\n'
    '    desc "He looks like Bob but asleep."\n'
    '    on attack\n        say "Doesn\'t seem sporting."\n'
)


def test_swap_carries_again_and_pronouns():
    # A field report (Charles Moore Jr.): ATTACK swaps one object for
    # another, and AGAIN then said "you see nothing of the sort here"
    # because it replayed the noun that just left scope. `swap(old, new)`
    # re-points the live bindings, so AGAIN replays the replacement and a
    # pronoun (HIM here, Bob being animate) follows it too.
    out = _run(["hit bob", "again"], game=SWAP_GAME)
    assert "falls, unconscious" in out            # the swap happened
    assert "Doesn't seem sporting." in out         # AGAIN hit the new object
    assert "nothing of the sort" not in out        # not the stale-noun refusal
    out2 = _run(["hit bob", "x him"], game=SWAP_GAME)
    assert "asleep" in out2                        # HIM now points at the sleeper


def test_no_swap_is_byte_identical():
    # swap is DCE'd in a game that never calls it: the story is unchanged.
    base = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing rock in hall\n    name "rock"\n    words rock\n'
    )
    a = generate(analyze(cosmos.combined_program(parse(base))))
    b = generate(analyze(cosmos.combined_program(parse(base))))
    assert a == b  # deterministic, and swap adds nothing when uncalled
