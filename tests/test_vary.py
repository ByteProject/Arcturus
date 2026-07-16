# test_vary.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""vary (docs/01, Output and text): prose that varies by itself, each site
keeping one invisible word of state (Dialog's select, I7's [one of],
Stefan's naming and the Arcturus statement form). Policies: sequence
(advance once, stick on the last), loop (round-robin), mutate (random,
never twice in a row), dice (the honest roll, stateless). A bare string
line is its own variant; an `or` line opens a statement-group variant.
Costs nothing in a game that never varies (the untouched ceilings)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

HEAD = (
    'game\n    title "V"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _replies(story, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = []
    for chunk in io.text.split(">")[1:]:
        lines = chunk.strip().split("\n")
        out.append(" ".join(l.strip() for l in lines[1:] if l.strip()))
    return out


def _game(policy_block, extra=""):
    return HEAD + extra + 'verb "v"\n    v\non v\n' + policy_block


def test_sequence_advances_then_sticks():
    story = _build(_game(
        '    vary sequence\n'
        '        "First."\n'
        '        "Second."\n'
        '        "Last, forever."\n'))
    r = _replies(story, ["v"] * 5)
    assert r[:5] == ["First.", "Second.", "Last, forever.",
                     "Last, forever.", "Last, forever."]


def test_loop_wraps_round_robin():
    story = _build(_game(
        '    vary loop\n'
        '        "A."\n'
        '        "B."\n'
        '        "C."\n'))
    r = _replies(story, ["v"] * 7)
    assert r[:7] == ["A.", "B.", "C.", "A.", "B.", "C.", "A."]


def test_mutate_never_repeats_consecutively():
    story = _build(_game(
        '    vary mutate\n'
        '        "Alpha."\n'
        '        "Beta."\n'
        '        "Gamma."\n'))
    r = _replies(story, ["v"] * 30)[:30]
    assert all(a != b for a, b in zip(r, r[1:]))          # the contract
    assert len(set(r)) >= 2                                # it does vary


def test_dice_rolls_honestly():
    story = _build(_game(
        '    vary dice\n'
        '        "Heads."\n'
        '        "Tails."\n'))
    r = _replies(story, ["v"] * 20)[:20]
    assert set(r) <= {"Heads.", "Tails."}
    assert len(set(r)) == 2  # 20 rolls landing one-sided is 2^-19 unlucky


def test_or_group_runs_statements():
    # A statement-group variant acts, not just speaks: the loop's third turn
    # runs the group and flips the flag.
    src = _game(
        '    vary loop\n'
        '        "A tap drips."\n'
        '        "A fly circles."\n'
        '    or\n'
        '        say "The fridge shudders."\n'
        '        now fridge is suspect\n',
        extra=('thing fridge in hall\n    name "fridge"\n    words fridge\n'
               '    suspect false\n'))
    src += 'verb "check"\n    check\non check\n    if fridge is suspect\n        say "flagged"\n'
    story = _build(src)
    r = _replies(story, ["v", "v", "v", "check"])
    assert r[2] == "The fridge shudders."
    assert r[3] == "flagged"


def test_two_sites_keep_independent_state():
    src = HEAD + (
        'verb "tick"\n    tick\non tick\n'
        '    vary loop\n        "a1"\n        "a2"\n'
        'verb "tock"\n    tock\non tock\n'
        '    vary sequence\n        "b1"\n        "b2"\n'
    )
    story = _build(src)
    r = _replies(story, ["tick", "tock", "tick", "tock", "tick", "tock"])
    assert r[:6] == ["a1", "b1", "a2", "b2", "a1", "b2"]


def test_vary_in_a_desc_block():
    # The computed-property context: a room description that changes with
    # each look (sequence: fresh arrival wording once, then the settled one).
    src = (
        'game\n    title "V"\n    start cellar\n'
        'room cellar\n    name "Cellar"\n'
        '    desc block\n'
        '        vary sequence\n'
        '            "Stairs descend into a dark that feels inhabited."\n'
        '            "The cellar again. The dark has not warmed to you."\n'
    )
    story = _build(src)
    io = CaptureIO(script=["look", "look"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "feels inhabited" in io.text
    assert "has not warmed to you" in io.text


# -- parse errors -------------------------------------------------------------

def test_single_variant_is_an_error():
    with pytest.raises(ArcError, match="at least"):
        _build(_game('    vary loop\n        "Only."\n'))


def test_statements_after_bare_strings_need_or():
    with pytest.raises(ArcError, match="`or` line"):
        _build(_game(
            '    vary loop\n'
            '        "A."\n'
            '        say "B."\n'))


def test_block_named_vary_still_calls():
    # `vary` is claimed only before a policy word: a block of that name is
    # untouched.
    src = HEAD + (
        'block vary()\n    say "the block ran"\n'
        'verb "v"\n    v\non v\n    vary\n'
    )
    story = _build(src)
    r = _replies(story, ["v"])
    assert r[0] == "the block ran"
