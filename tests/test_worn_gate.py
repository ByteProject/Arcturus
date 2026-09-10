# test_worn_gate.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The worn seam (Marco's cursed clothes, 2026-09-09): drop, put, and
insert of something WORN no longer bypass the take_off gate. The house
rejects and points at the door ("You would have to take the scarf off
first."); summon.foresight takes it off implicitly instead, running the
REAL take_off so an object's own refusing handler still rules
(promise-then-run, the take repair's honest residue). The sealed case
joins the same doctrine: a put of a thing shut behind clear glass
refuses bare and opens with foresight, the take's parity. The `held`
grammar slot, never enforced, is retired: the verb contract is the one
held spelling (Stefan's ruling)."""

import pytest

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "W"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing cloak in player\n    name "velvet cloak"\n    words cloak\n'
    '    wearable\n    worn\n'
    '    on take_off\n'
    '        say "The curse forbids it."\n'
    '        change refused to 1\n'
    'thing scarf in player\n    name "scarf"\n    words scarf\n'
    '    wearable\n    worn\n'
    'thing coin in jar\n    name "coin"\n    words coin\n'
    'thing jar of container in hall\n    name "glass jar"\n    words jar\n'
    '    clear\n    openable\n'
    'thing chest of container in hall\n    name "chest"\n    words chest\n'
    '    open\n'
)


def _run(cmds, game=GAME):
    io = CaptureIO(script=list(cmds) + ["quit", "y"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(game))))),
           io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_the_house_rejects_worn_through_every_door():
    out = _run(["drop scarf", "put scarf in chest", "insert scarf in chest",
                "inventory"])
    assert out.count("You would have to take the scarf off first.") == 3
    assert "scarf" in out.split("inventory")[-1]  # still worn, still carried


def test_the_gate_is_take_off_and_the_curse_holds_it():
    out = _run(["take off cloak", "drop cloak"])
    assert "The curse forbids it." in out
    assert "You would have to take the velvet cloak off first." in out


def test_foresight_takes_it_off_first():
    out = _run(["drop scarf", "look"], game="summon.foresight\n" + GAME)
    assert "(taking off the scarf first)" in out
    assert "Down it goes." in out
    assert "You can see a scarf" in out


def test_foresight_runs_the_real_gate_and_the_curse_still_rules():
    out = _run(["drop cloak", "inventory"], game="summon.foresight\n" + GAME)
    # Promise-then-run, the honest residue: the promise prints, the real
    # take_off runs, the curse refuses, the cloak stays on.
    assert "(taking off the velvet cloak first)" in out
    assert "The curse forbids it." in out
    assert "cloak" in out.split("inventory")[-1]


def test_sealed_put_matches_the_takes_parity():
    out = _run(["put coin in chest"])
    assert "open the glass jar first" in out
    out = _run(["put coin in chest", "look"], game="summon.foresight\n" + GAME)
    assert "(opening the glass jar first)" in out
    assert "chest (contains a coin)" in out


def test_the_held_slot_is_retired_with_advice():
    src = (
        'game\n    title "H"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'verb "brandish"\n    brandish held\n'
    )
    with pytest.raises(ArcError) as err:
        analyze(cosmos.combined_program(parse(src)))
    assert "requires noun carried" in str(err.value)


def test_the_packs_reject_in_their_own_words():
    de = (
        'summon.language "german"\n'
        'game\n    title "G"\n    start halle\n'
        'room halle\n    name "Halle"\n    desc "Kahl."\n'
        'thing mantel in player\n    name "Mantel"\n    words mantel\n'
        '    der\n    wearable\n    worn\n'
    )
    out = _run(["lass mantel fallen"], game=de)
    assert "Dazu müsstest du den Mantel erst ausziehen." in out
    es = (
        'summon.language "spanish"\n'
        'game\n    title "S"\n    start sala\n'
        'room sala\n    name "Sala"\n    desc "Nada."\n'
        'thing bufanda in player\n    name "bufanda"\n    words bufanda\n'
        '    feminine\n    wearable\n    worn\n'
    )
    out = _run(["deja bufanda"], game=es)
    assert "Tendrías que quitarte la bufanda primero." in out
