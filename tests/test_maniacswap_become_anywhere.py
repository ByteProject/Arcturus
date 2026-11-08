# test_maniacswap_become_anywhere.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""BECOME is a swap from anywhere, not a touch (improvmonster's reports,
2026-11-01): the reach and sealed gates never refuse it, and a body seated
on a supporter or inside a container arrives in its ROOM, still seated,
able to see, take, get out, and walk off."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


GAME = (
    'summon.maniacswap\n'
    'game\n    title "G"\n    start hall\n    body henrik\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south hall\n'
    'thing henrik of character in hall\n    name "Henrik"\n    named\n    words henrik\n    playable\n'
    'thing mare of supporter in hall\n    name "mare"\n    words mare\n'
    'thing wardrobe of container in yard\n    name "wardrobe"\n    words wardrobe\n    openable\n{wopen}'
    'thing sofa of supporter in yard\n    name "sofa"\n    words sofa\n'
    'thing greta of character in {where}\n    name "Greta"\n    named\n    words greta\n    playable\n'
    'thing jar in hall\n    name "jar"\n    words jar\n    beyond\n'
    'thing ida of character in jar\n    name "Ida"\n    named\n    words ida\n    playable\n'
    'thing lamp in yard\n    name "lamp"\n    words lamp\n'
    'on after enter mare\n    now player is beyond\n'
)


def test_become_crosses_the_reach_and_sealed_gates():
    out = _run(GAME.format(where="wardrobe", wopen=""),
               ["enter mare", "become greta", "become henrik", "become ida"])
    parts = out.split(">")[1:]
    assert "You are now Greta." in parts[1]        # from a beyond player, into a shut wardrobe
    assert "You are now Henrik." in parts[2]       # back onto the mare
    assert "You are now Ida." in parts[3]          # into a beyond holder
    assert "beyond your reach" not in out and "open the wardrobe first" not in out


@pytest.mark.parametrize("where, heading, getoff", [
    ("sofa", "Yard (on the sofa)", "You get off the sofa."),
    ("wardrobe", "Yard (in the wardrobe)", "You get out of the wardrobe."),
])
def test_a_seated_body_arrives_in_its_room(where, heading, getoff):
    out = _run(GAME.format(where=where, wopen="    open\n"),
               ["become greta", "take lamp", "exit", "south"])
    parts = out.split(">")[1:]
    assert heading in parts[0] and "Pitch black" not in parts[0]
    assert "You take the lamp with you." in parts[1]
    assert getoff in parts[2]
    assert "Hall" in parts[3] and "no exit" not in parts[3]
