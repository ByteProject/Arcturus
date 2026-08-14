# test_exit_validation.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Named exit targets are validated at compile time (a field report from
Ichiro Ota: a typo'd room name compiled silently into the runtime "There's
no exit in that direction.", and worse, an exit naming a plain THING walked
the player inside it, a pitch-black soft-lock). The legal targets are
exactly three: a declared room, a door-kind thing, or a computed block;
`nothing` stays legal as the explicit no-exit."""

import pytest

from arcturus import cosmos
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = 'game\n    title "T"\n    start hall\n'


def _analyze(src):
    return analyze(cosmos.combined_program(parse(BASE + src)))


def test_exit_to_an_undeclared_room_is_a_compile_error():
    with pytest.raises(ArcError, match="names 'attic', which is not declared"):
        _analyze('room hall\n    name "H"\n    desc "x"\n    north attic\n')


def test_exit_to_a_plain_thing_is_a_compile_error():
    # The soft-lock: before the check, this walked the player INTO the lamp.
    with pytest.raises(ArcError, match="neither a room nor a door"):
        _analyze(
            'room hall\n    name "H"\n    desc "x"\n    south lamp\n'
            'thing lamp in hall\n    name "lamp"\n    words lamp\n'
        )


def test_exit_to_a_kind_is_a_compile_error():
    with pytest.raises(ArcError, match="a kind; an exit needs a room"):
        _analyze(
            'kind cellar of room\n'
            'room hall\n    name "H"\n    desc "x"\n    north cellar\n'
        )


def test_the_legal_targets_pass():
    # A room, a two-sided door, an instance of a room kind, and the
    # explicit `nothing` all compile.
    _analyze(
        'kind wing of room\n'
        'room hall\n    name "H"\n    desc "x"\n'
        '    north attic\n    east oak\n    west gallery\n    south nothing\n'
        'room attic\n    name "A"\n    desc "y"\n    south hall\n'
        'room vault\n    name "V"\n    desc "z"\n    west oak\n'
        'room gallery of wing\n    name "G"\n    desc "g"\n    east hall\n'
        'thing oak of door in hall, vault\n    name "oak door"\n'
        '    words oak, door\n'
    )


# --- locations: the last dangling reference (a field lesson, 2026-08-14) ----
#
# An example lost its Truhe declaration to an editor accident, and
# `thing schluessel in truhe` compiled SILENTLY: the key stranded outside
# the tree, no error, the game simply missing its object. Exits and spans
# already refused a dangling name; `in` now does too.


def test_a_thing_in_an_undeclared_container_is_a_compile_error():
    with pytest.raises(ArcError, match="'key' is placed in 'chest'"):
        _analyze(
            'room hall\n    name "H"\n    desc "x"\n'
            'thing key in chest\n    name "key"\n    words key\n'
        )


def test_the_legal_locations_pass():
    # A room, a container, the player, and backstage (no location at all).
    _analyze(
        'room hall\n    name "H"\n    desc "x"\n'
        'thing box of container in hall\n    name "box"\n    words box\n'
        'thing key in box\n    name "key"\n    words key\n'
        'thing coin in player\n    name "coin"\n    words coin\n'
        'thing ghost\n    name "ghost"\n    words ghost\n'
    )
