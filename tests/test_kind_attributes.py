# test_kind_attributes.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The kind attribute budget (docs/01 section 5; the field wall Charles Moore
Jr. hit porting a 200K game). A kind is Arcturus sugar, not a Z-machine
concept, so it must not silently steal from the 48-attribute ceiling the way
Inform's classes never do. Three tiers:

- Lever 1: a kind is given a runtime attribute ONLY when the program tests
  `obj is <kind>` somewhere. A kind used only to organize, share handlers or
  properties, or span scenery is compile-time and costs zero attributes.
- Attribute-backed while the budget (after the real flags) has room, busiest
  kinds first, so the one-byte test_attr goes to the hot tests.
- Catalog spill: the overflow tested kinds become membership scans, so kinds
  are effectively unlimited and a flag ceiling is the only real ceiling.
"""

from arcturus import cosmos
from arcturus.parser import parse
from arcturus.sema import analyze
from arcturus.objects import build_layout


def _layout(game):
    world = analyze(cosmos.combined_program(parse(game)))
    return world, build_layout(world)


def test_untested_kind_costs_no_attribute():
    game = (
        'game\n    title "T"\n    start hall\n'
        'kind weapon of thing\n'
        'kind decor of thing\n'          # only ever spans/organizes: never tested
        'room hall\n    name "Hall"\n    desc "D."\n'
        'thing sword of weapon in hall\n    name "sword"\n'
        'thing vase of decor in hall\n    name "vase"\n'
        'verb "wield"\n    wield noun\n'
        'on wield\n    if noun is weapon\n        say "You brandish it."\n'
    )
    world, layout = _layout(game)
    assert "weapon" in layout.kind_attr        # tested -> attribute-backed
    assert "decor" not in layout.kind_attr     # never is-tested -> free
    assert "decor" not in world.kind_tests
    assert layout.kind_spilled == []


def test_tested_kind_counts_every_site():
    game = (
        'game\n    title "T"\n    start hall\n'
        'kind relic of thing\n'
        'room hall\n    name "Hall"\n    desc "D."\n'
        'thing idol of relic in hall\n    name "idol"\n'
        'verb "appraise"\n    appraise noun\n'
        'on appraise\n'
        '    if noun is relic\n        say "Old."\n'
        '    if noun is not relic\n        say "New."\n'
    )
    world, _ = _layout(game)
    assert world.kind_tests["relic"] == 2      # both sites counted (also negated)
