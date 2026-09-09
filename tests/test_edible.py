# test_edible.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The edible contract (docs/01 chapter 5; auraes's apple, 2026-09-09):
a thing flagged `edible` is consumed by EAT, gone from the world, with
the library's own line; everything else, characters included, stays not
on the menu (Stefan's ruling: the line is a good one). A floor apple
eats in one command through the take_probe gate put and insert use; a
story's `on eat` overrides for consequences; USE (summon.use) actually
eats now instead of performing an eat that refuses."""

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "E"\n    start pantry\n'
    'room pantry\n    name "Pantry"\n    desc "A pantry."\n'
    'thing apple in player\n    name "apple"\n    words apple\n    edible\n'
    'thing pear in pantry\n    name "pear"\n    words pear\n    edible\n'
    'thing rock in pantry\n    name "rock"\n    words rock\n'
    'thing cook of character in pantry\n    name "cook"\n    words cook\n'
)


def _run(cmds, game=GAME):
    io = CaptureIO(script=list(cmds) + ["quit", "y"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(game))))),
           io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_edible_is_consumed_held_or_from_the_floor():
    out = _run(["eat apple", "eat apple", "eat pear", "inventory"])
    assert out.count("goes down smoothly") == 2
    # The eaten apple is gone from the world, not merely from the hand.
    assert "You see nothing of the sort here." in out
    assert "precisely nothing" in out


def test_everything_else_stays_off_the_menu():
    out = _run(["eat rock", "eat cook"])
    assert "The rock is not on the menu." in out
    assert "The cook is not on the menu." in out


def test_a_story_on_eat_overrides_the_consume():
    game = GAME + (
        'on eat when noun is apple\n'
        '    say "Not before dinner."\n'
    )
    out = _run(["eat apple", "inventory"], game=game)
    assert "Not before dinner." in out
    assert "goes down smoothly" not in out
    assert "apple" in out  # still carried


def test_use_actually_eats_now():
    game = "summon.use\n" + GAME
    out = _run(["use apple"], game=game)
    assert "goes down smoothly" in out


def test_the_packs_eat_in_their_own_words():
    de = (
        'summon.language "german"\n'
        'game\n    title "G"\n    start kammer\n'
        'room kammer\n    name "Kammer"\n    desc "Kahl."\n'
        'thing apfel in player\n    name "Apfel"\n    words apfel\n'
        '    der\n    edible\n'
    )
    out = _run(["iss apfel"], game=de)
    assert "Der Apfel rutscht glatt hinunter." in out
    assert "nimmt die Gabe aber an." in out
    es = (
        'summon.language "spanish"\n'
        'game\n    title "S"\n    start cocina\n'
        'room cocina\n    name "Cocina"\n    desc "Nada."\n'
        'thing manzana in player\n    name "manzana"\n    words manzana\n'
        '    feminine\n    edible\n'
    )
    out = _run(["come manzana"], game=es)
    assert "La manzana baja sin problemas." in out
    assert "pero acepta la ofrenda." in out
