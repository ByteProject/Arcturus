# test_direction_grammar.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The `direction` grammar slot (docs/01 section 10): SWIM SOUTH and PUSH
CRATE WEST. A line ending in `direction` consumes exactly one direction
word positionally; the value rides `way`, which the parser binds on every
command anyway. The slot always tables its verb (the flag model's arity
byte cannot say "and a direction may stand here"), so a game that never
writes one stays byte-identical, which the size ceilings prove."""

import pytest

from arcturus import cosmos
from arcturus import worldmodel as wm
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start pool\n'
    'room pool\n    name "Pool"\n    desc "Water."\n    south shore\n'
    'room shore\n    name "Shore"\n    desc "Land."\n    north pool\n'
    'thing crate in pool\n    name "crate"\n    words crate\n    fixed\n'
    'verb "swim", "paddle"\n'
    '    swim\n'
    '    swim direction\n'
    'verb "shove"\n'
    '    push noun\n'
    '    push noun direction\n'
    'on swim\n'
    '    if way is nothing\n        say "SWIM WHERE?"\n        stop\n'
    '    if way is south\n        say "SWIM SOUTH."\n        stop\n'
    '    say "SWIM SOMEWHERE."\n'
    'on push\n'
    '    if noun is nothing\n        say "PUSH WHAT?"\n        stop\n'
    '    if way is nothing\n        say "NO BUDGE."\n        stop\n'
    '    if way is west\n        say "PUSH ${the noun} WEST."\n        stop\n'
    '    say "PUSH ${the noun} SOMEWHERE."\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if isinstance(cmds, str):
        cmds = [cmds]
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def _reply(cmds, game=GAME):
    text = _run(cmds, game)
    last = cmds if isinstance(cmds, str) else cmds[-1]
    at = text.rindex(">" + last)
    return text[at:].split("\n")[1]


def test_intransitive_direction():
    assert "SWIM WHERE?" in _reply("swim")          # the bare line still fits
    assert "SWIM SOUTH." in _reply("swim south")
    assert "SWIM SOMEWHERE." in _reply("paddle north")  # synonym, same table


def test_noun_then_direction():
    # The direction word bounds the noun phrase: the noun is "crate", the
    # direction rides `way`.
    assert "PUSH the crate WEST." in _reply("shove crate west")
    assert "PUSH the crate SOMEWHERE." in _reply("shove crate north")
    assert "NO BUDGE." in _reply("shove crate")      # the plain line, way empty


def test_honest_refusals():
    # A non-direction word where the slot demands one is refused, not
    # silently dropped; parser honesty holds on the tabled path.
    assert "lost me" in _reply("swim crate")


def test_direction_slot_tables_the_verb():
    w = analyze(cosmos.combined_program(parse(GAME)))
    tabled = {v.words[0] for v in wm.tabled_verbs(w)}
    assert "swim" in tabled and "shove" in tabled


def test_direction_slot_must_close_its_line():
    bad = (
        'game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "d"\n'
        'verb "push"\n    push direction noun\n'
        'on push\n    say "x"\n'
    )
    with pytest.raises(ArcError, match="last item on its line"):
        analyze(cosmos.combined_program(parse(bad)))


def test_one_direction_slot_per_line():
    bad = (
        'game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "d"\n'
        'verb "swim"\n    swim direction direction\n'
        'on swim\n    say "x"\n'
    )
    with pytest.raises(ArcError, match="at most one"):
        analyze(cosmos.combined_program(parse(bad)))
