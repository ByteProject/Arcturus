# test_kind_handler_precedence.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Instance handlers beat kind handlers: the doctrine (docs/01 section 9,
most specific wins) pinned as executable fact, in every dispatch shape.
Grown from a field report (2026-07-17) that could NOT be reproduced; this
file is the armor that keeps the answer true. Covers: same file, deep kind
chains, split vs combined verb lists, forward-declared kinds, and the
catalog-spilled kind path (the attribute budget exhausted), plus the
deferral direction: a verb the instance does not handle falls to the kind."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(game, cmds):
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


_HEAD = (
    'game\n    title "T"\n    start yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n'
)


def test_instance_beats_kind_combined_verb_list():
    game = _HEAD + (
        'kind scarecrow_kind of character\n'
        '    on push, pull, touch\n        say "The kind answers."\n'
        'thing willow of scarecrow_kind in yard\n'
        '    name "Willow"\n    words willow\n'
        '    on push, pull, touch\n        say "The instance answers."\n'
    )
    out = _run(game, ["push willow", "pull willow", "touch willow"])
    assert out.count("The instance answers.") == 3
    assert "The kind answers." not in out


def test_instance_beats_kind_through_a_chain():
    game = _HEAD + (
        'kind villager_base of character\n'
        '    on push\n        say "The base kind answers."\n'
        'kind scarecrow_kind of villager_base\n'
        'thing willow of scarecrow_kind in yard\n'
        '    name "Willow"\n    words willow\n'
        '    on push\n        say "The instance answers."\n'
    )
    out = _run(game, ["push willow"])
    assert "The instance answers." in out
    assert "The base kind answers." not in out


def test_unhandled_verb_falls_to_the_kind():
    game = _HEAD + (
        'kind scarecrow_kind of character\n'
        '    on push\n        say "Kind push."\n'
        '    on pull\n        say "Kind pull."\n'
        'thing oak of scarecrow_kind in yard\n'
        '    name "Oak"\n    words oak\n'
        '    on push\n        say "Instance push."\n'
    )
    out = _run(game, ["push oak", "pull oak"])
    assert "Instance push." in out
    assert "Kind pull." in out
    assert "Kind push." not in out


def test_instance_beats_forward_declared_kind():
    game = _HEAD + (
        'thing willow of npc in yard\n'
        '    name "Willow"\n    words willow\n'
        '    on push\n        say "The instance answers."\n'
        'kind npc of character\n'
        '    on push\n        say "The kind answers."\n'
    )
    out = _run(game, ["push willow"])
    assert "The instance answers." in out
    assert "The kind answers." not in out


def test_instance_beats_spilled_kind():
    # Exhaust the kind attribute slots so the tested kind spills to the
    # catalog membership scan, then assert precedence holds on that path.
    fillers = "".join(
        f'kind filler{i:02d} of thing\n'
        f'    on push\n        say "Filler {i:02d}."\n'
        f'thing f{i:02d} of filler{i:02d} in yard\n'
        f'    name "f{i:02d}"\n    words f{i:02d}x\n'
        for i in range(60)
    )
    # membership tests are what cost attribute slots (dispatch alone is
    # wired statically); a census handler testing every kind forces the
    # overflow into the catalog scan
    census = (
        'verb "census"\n    census_it\n'
        'on census_it\n'
        + "".join(f'    if noun is filler{i:02d}\n        say "m"\n'
                  for i in range(60))
    )
    game = _HEAD + fillers + census + (
        'thing special of filler40 in yard\n'
        '    name "special"\n    words special\n'
        '    on push\n        say "The instance answers."\n'
    )
    from arcturus.objects import build_layout
    world = analyze(cosmos.combined_program(parse(game)))
    layout = build_layout(world)
    assert len(layout.kind_spilled) > 0, "the spill never happened; the test lost its point"
    story = generate(world)
    io = CaptureIO(script=["push special", "push f05x"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "The instance answers." in io.text
    assert "Filler 05." in io.text      # kind handlers still fire for plain instances
