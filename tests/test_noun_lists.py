# test_noun_lists.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Noun lists in two-noun actions (the verbs overhaul, phase 6): "put coin
and nail in box" binds the second once and runs each listed item as its own
full turn, reported the sweep way ("gold coin: You put the gold coin"), stopping at the
first refusal, the chain rule. The "and" inside a two-noun verb's first
slot is a LIST, not a chain, exactly when no verb follows it and the
separator still lies ahead; everything else chains as it always did, and
single-noun lists keep riding the chain's verb borrow untouched."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "L"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south hall\n'
    'thing coin in player\n    name "gold coin"\n    words coin, gold\n'
    'thing nail in player\n    name "rusty nail"\n    words nail, rusty\n'
    'thing bolt in player\n    name "bolt"\n    words bolt\n'
    'thing gem in hall\n    name "gem"\n    words gem\n'
    'thing box of container in hall\n    name "wooden box"\n    words box\n'
    '    open\n    fixed\n'
    'thing bob in hall\n    name "Bob"\n    words bob\n    named\n    animate\n'
    '    on give\n        say "Bob pockets ${the noun}."\n'
)


def _run(cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_two_items_land_and_each_is_reported():
    out = _run(["put coin and nail in box", "take nail", "i"])
    assert "gold coin: You put the gold coin" in out
    assert "rusty nail: You put the rusty nail" in out
    # ...and the nail really moved: takeable back out of the box.
    assert "You take the" in out.split("take nail")[-1]


def test_three_items_with_comma_and():
    out = _run(["put coin, nail and bolt in box"])
    assert out.count("You put ") == 3


def test_a_list_still_chains_afterwards():
    out = _run(["put coin and nail in box then go north"])
    assert "rusty nail: You put the rusty nail" in out
    assert "Yard" in out


def test_single_noun_lists_sweep_like_two_noun_ones():
    # Stefan's ruling (2026-10-15, auraes's transcript): a one-noun verb
    # takes a list too, swept and labeled exactly like the two-noun list,
    # no paragraph break between the items.
    out = _run(["take gem and coin"])
    assert "gem: You take the" in out
    assert "gold coin: You already have the gold coin" in out
    assert "\n\ngold coin:" not in out


def test_one_noun_list_stops_at_a_refusal_and_a_verb_still_chains():
    out = _run(["take gem and box and coin", "drop gem and go north"])
    assert "gem: You take the" in out
    assert "box:" in out
    assert "coin:" not in out.split("box:")[1].split(">")[0]
    assert "gem: Down it goes." not in out      # a verb after and is a chain, not a list
    assert "Down it goes." in out and "Yard" in out


def test_an_unresolvable_item_stops_the_list():
    out = _run(["put coin and ghost in box"])
    assert "gold coin: You put the gold coin" in out
    assert "nothing of the sort" in out
    assert "rusty nail" not in out.split("You put ")[-1]


def test_the_contract_guards_each_item():
    # GIVE requires a carried noun; the gem is on the floor, so its item
    # refuses through the contract and the list stops there.
    out = _run(["give coin and gem to bob"])
    assert "Bob pockets the gold coin." in out
    assert "aren't carrying the gem" in out


def test_a_verb_after_and_still_chains():
    out = _run(["take gem and put coin in box"])
    assert "You take the" in out
    assert "You put " in out
