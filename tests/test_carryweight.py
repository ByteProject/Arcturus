# test_carryweight.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The weight budget (summon.carryweight, docs/01 chapters 6 and 12): every
carryable thing weighs 0.5 units unless it declares `weight N.N` (tenths
fixed-point; `no_weight` is zero), the player carries at most the budget
(10.0 default, `constant weight_cap` fixed, `global carry_weight` dynamic),
TAKE prices a container with its contents, and a count limit enforces
independently beside it (the beer-barrel ruling). Driven on Actaea."""

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'summon.carryweight\n'
    'constant weight_cap = 3\n'
    'game\n    title "W"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing feather in hall\n    name "feather"\n    words feather\n'
    '    weight no_weight\n'
    'thing keg in hall\n    name "keg"\n    words keg\n    weight 2.5\n'
    'thing book in hall\n    name "book"\n    words book\n'
    'thing sack of container in hall\n    name "sack"\n    words sack\n'
    '    open\n    weight 0.2\n'
    'thing brick in sack\n    name "brick"\n    words brick\n    weight 1.8\n'
    'verb "weigh"\n    weighing\n'
    'on weighing\n    show "The sack: "\n    say_weight(sack.totalweight)\n'
    '    say ""\n'
)


def _run(cmds, game=GAME):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(game))))),
           io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_the_budget_prices_defaults_declared_and_zero():
    # keg 2.5 + book 0.5 (the default) + feather 0.0 fills a 3.0 budget
    # exactly; the 2.0 sack (0.2 + its 1.8 brick, priced together) no
    # longer fits, and does after the keg goes down.
    out = _run(["weigh", "take keg", "take book", "take feather",
                "take sack", "drop keg", "take sack"])
    assert "The sack: 2.0 kg" in out
    assert "That is too heavy to carry with everything else." in out
    assert out.count("You take the sack with you.") == 1


def test_the_dynamic_budget_moves_at_run_time():
    game = GAME.replace("constant weight_cap = 3\n",
                        "global carry_weight = 3\n").replace(
        'on weighing\n    show "The sack: "\n    say_weight(sack.totalweight)\n'
        '    say ""\n',
        'on weighing\n    change carry_weight to 9.9\n'
        '    say "You feel mighty."\n')
    out = _run(["take keg", "take sack", "weigh", "take sack"], game=game)
    assert "That is too heavy to carry with everything else." in out
    assert "You feel mighty." in out
    assert out.count("You take the sack with you.") == 1


def test_count_and_weight_enforce_independently():
    # The beer-barrel ruling: two hands' worth OR 3.0 units, whichever runs
    # out first. Three weightless things hit the count; one 2.5 keg plus a
    # 0.5 book hits the weight with the count barely started.
    game = GAME.replace("summon.carryweight\n",
                        "summon.carryweight\nconstant item_cap = 2\n")
    out = _run(["take feather", "take book", "take keg"], game=game)
    # feather 0.0 + book 0.5 fine; the keg is the THIRD item: count first.
    assert "Your hands are full, and so are your pockets." in out
    out = _run(["take keg", "take book"], game=game)
    # keg 2.5 + book 0.5 = 3.0 fits; the count (2) fits: both allowed.
    assert out.count(" with you.") == 2


def test_put_into_a_carried_sack_pays_the_tolls():
    # The sack hole, put edition (2026-09-08): putting a floor thing into
    # a carried container enters the carried subtree, so it pays what a
    # take pays. Carrying the sack and its brick reads 2.0 of 3.0; the
    # 2.5 keg never sneaks in from the floor, the weightless feather does.
    out = _run(["take sack", "put keg in sack", "put feather in sack",
                "weigh"])
    assert "too heavy to carry" in out
    assert "The sack: 2.0 kg" in out  # the keg stayed out, the feather is free
    # The count enforces the same way: with item_cap 3 the carried sack,
    # brick, and feather sit at the cap, a floor book is the fourth and
    # refuses, while rearranging what is already carried stays free.
    game = GAME.replace("summon.carryweight\n",
                        "summon.carryweight\nconstant item_cap = 3\n")
    out = _run(["take sack", "take feather", "put feather in sack",
                "put book in sack", "look"], game=game)
    assert "Your hands are full, and so are your pockets." in out
    assert "You can see a keg and a book" in out  # the book never moved


def test_a_destination_on_the_ground_prices_nothing():
    # Hands at the cap, but the crate sits on the floor: floor-to-floor
    # is not entering the carried subtree, so no toll speaks.
    game = GAME.replace("summon.carryweight\n",
                        "summon.carryweight\nconstant item_cap = 2\n")
    game = game + ('thing crate of container in hall\n    name "crate"\n'
                   '    words crate\n    open\n')
    out = _run(["take sack", "put book in crate", "look"], game=game)
    assert "full" not in out
    assert "contains a book" in out


def test_the_packs_speak_the_refusal():
    de = (
        'summon.language "german"\n'
        'summon.carryweight\nconstant weight_cap = 1\n'
        'game\n    title "G"\n    start halle\n'
        'room halle\n    name "Halle"\n    desc "Kahl."\n'
        'thing amboss in halle\n    name "Amboss"\n    words amboss\n'
        '    der\n    weight 5.0\n'
    )
    out = _run(["nimm amboss"], game=de)
    assert "Das ist zu schwer, mit allem, was du schon trägst." in out
    es = (
        'summon.language "spanish"\n'
        'summon.carryweight\nconstant weight_cap = 1\n'
        'game\n    title "E"\n    start sala\n'
        'room sala\n    name "Sala"\n    desc "Nada."\n'
        'thing yunque in sala\n    name "yunque"\n    words yunque\n'
        '    weight 5.0\n'
    )
    out = _run(["coge yunque"], game=es)
    assert "Pesa demasiado con todo lo que ya llevas." in out
