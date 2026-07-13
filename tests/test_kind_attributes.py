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


# -- the spill (Tiers 2+3) ------------------------------------------------------

import pytest
from arcturus.codegen import generate
from arcturus.errors import ArcError
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _spill_game(n, body_extra=""):
    """n tested kinds, each with an instance; enough n forces a spill."""
    lines = ['game', '    title "T"', '    start hall']
    for i in range(n):
        lines.append(f'kind k{i} of thing')
    lines += ['room hall', '    name "Hall"', '    desc "D."']
    for i in range(n):
        lines += [f'thing o{i} of k{i} in hall', f'    name "obj{i}"',
                  f'    words obj{i}']
    lines += ['verb "probe"', '    probe noun', 'on probe']
    for i in range(n):
        lines += [f'    if noun is k{i}', f'        say "MATCH-k{i}"']
    return '\n'.join(lines) + '\n' + body_extra


def test_overflow_kinds_spill_to_catalogs():
    world, layout = _layout(_spill_game(60))
    assert layout.kind_spilled, "60 tested kinds should overflow the budget"
    assert all(k in layout.kind_catalog for k in layout.kind_spilled)
    # Attribute-backed and spilled are disjoint and together cover the tested.
    backed = {k for k in layout.kind_attr if k.startswith("k")}
    spilled = set(layout.kind_spilled)
    assert backed.isdisjoint(spilled)


def _run(game, cmds):
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_spilled_kind_membership_is_correct():
    # A spilled kind (tested via catalog scan) answers exactly like an
    # attribute-backed one: true for its instance, false for every other.
    world, layout = _layout(_spill_game(60))
    spilled = layout.kind_spilled[0]           # e.g. "k26"
    idx = spilled[1:]                          # the instance is obj<idx>
    out = _run(_spill_game(60), [f"probe obj{idx}"])
    assert f"MATCH-{spilled}" in out           # its own (spilled) kind matches
    assert out.count("MATCH-") == 1            # and nothing else does


def test_spilled_kind_inheritance():
    # Transitive membership through a SPILLED parent: `base` is tested once
    # while 60 filler kinds are tested three times each, so the fillers win
    # every attribute slot and `base` spills. An instance of a sub-kind of
    # base must still test true for base, via base's extent catalog (which
    # holds transitive instances). One `on probe` handler so it isn't
    # consumed before the base test runs.
    lines = ['game', '    title "T"', '    start hall',
             'kind base of thing', 'kind chick of base']
    for i in range(60):
        lines.append(f'kind f{i} of thing')
    lines += ['room hall', '    name "Hall"', '    desc "D."',
              'thing egg of chick in hall', '    name "egg"', '    words egg']
    for i in range(60):
        lines += [f'thing g{i} of f{i} in hall', f'    name "g{i}"',
                  f'    words g{i}']
    lines += ['verb "probe"', '    probe noun', 'on probe',
              '    if noun is base', '        say "BASE"']
    for _rep in range(3):                       # fillers tested 3x -> outrank base
        for i in range(60):
            lines += [f'    if noun is f{i}', f'        say "F{i}"']
    game = '\n'.join(lines) + '\n'
    world, layout = _layout(game)
    assert "base" in layout.kind_spilled        # forced to spill by frequency
    out = _run(game, ["probe egg"])
    assert "BASE" in out                        # egg is-a chick is-a base (spilled)


def test_flag_ceiling_names_flags_not_kinds():
    # 60 genuine boolean flags on one object overflow the 48 attributes. The
    # error must name flags, never kinds (kinds spill; flags cannot).
    flags = "".join(f'    flag{i}\n' for i in range(60))
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "D."\n'
        f'thing widget in hall\n    name "widget"\n{flags}'
        'verb "poke"\n    poke noun\n'
        'on poke\n    if noun is flag0\n        say "set"\n'
    )
    with pytest.raises(ArcError) as exc:
        generate(analyze(cosmos.combined_program(parse(game))))
    assert "boolean flags" in str(exc.value)
    assert "kinds do not count" in str(exc.value).lower()
