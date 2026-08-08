# test_go_other.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""on go other (docs/01 chapter 8, tier 4 of the movement model; a field
report from the German forum): the per-room fallback fires for any direction
that has no exit and no specific `on go <direction>` handler, standing alone
if the room wants it that way (the handbook's ledge example has no sibling
handler at all). Genuine exits and specific overrides always win, whatever
the declaration order; a computed exit answering nothing counts as no exit,
one answering a room counts as a genuine exit. Before the fix the compiler
refused the pattern outright ('kinds in patterns are not supported yet')."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

# The ledge shape from the handbook plus every interplay: a static exit, a
# consuming specific handler, a continuing specific handler, and a computed
# exit that swings with a flag.
GAME = (
    'game\n    title "T"\n    start cell\n'
    'flag portal_open\n'
    'room cell\n    name "Cell"\n    desc "A cell."\n'
    '    north yard\n'
    '    east block\n'
    '        if portal_open\n            return yard\n'
    '        return nothing\n'
    '    on go south\n'
    '        say "The south wall is padded."\n'
    '    on go west\n'
    '        say "You lean on the west wall."\n'
    '        continue\n'
    '    on go other\n'
    '        say "White wall to the ${way}."\n'
    '        stop\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south cell\n'
    'verb "portal" meta\n    portal\n'
    'on portal\n    change portal_open to true\n    say "The portal hums."\n'
)

# Declaration order must not matter: other first, specific after.
ORDERED = (
    'game\n    title "T"\n    start cell\n'
    'room cell\n    name "Cell"\n    desc "A cell."\n'
    '    on go other\n'
    '        say "Blank stone everywhere."\n'
    '        stop\n'
    '    on go south\n'
    '        say "The south wall whispers."\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_fallback_answers_exitless_directions():
    out = _run(["up", "down"])
    assert "White wall to the up." in out
    assert "White wall to the down." in out
    assert "You can't go that way." not in out


def test_a_real_exit_always_wins():
    out = _run(["north"])
    assert "Yard" in out
    assert "White wall" not in out


def test_a_consuming_specific_handler_wins():
    out = _run(["south"])
    assert "The south wall is padded." in out
    assert "White wall" not in out


def test_a_continuing_specific_handler_falls_to_the_fallback():
    out = _run(["west"])
    assert "You lean on the west wall." in out
    assert "White wall to the west." in out


def test_a_computed_exit_swings_the_fallback():
    out = _run(["east", "portal", "east"])
    # Shut: the computed exit answers nothing, the fallback speaks.
    assert "White wall to the east." in out
    # Open: the computed exit answers a room, the fallback stays silent.
    assert "Yard" in out.rsplit(">east", 1)[1]


def test_declaration_order_does_not_matter():
    out = _run(["south", "north"], game=ORDERED)
    assert "The south wall whispers." in out
    assert "Blank stone everywhere." in out
