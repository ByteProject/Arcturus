# test_get_idioms.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The English GET idioms (field report: GET IN X ran take, not enter).
"get" stays a take synonym, but with a direction word it is movement or
boarding, the classic reading: GET IN/INTO X enters, GET ON X enters (the
take+on particle), GET OUT OF X and GET OFF X-you-are-in exit, a bare GET
IN/OUT/UP/DOWN walks, and GET OFF HAT stays the wearing verb. All of it
lives in the English pack's remap_action/compound (idioms are language);
German and Spanish are untouched."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start farm\n'
    'room farm\n    name "Farm"\n    desc "A farm."\n'
    '    up loft\n'
    'room loft\n    name "Loft"\n    desc "The loft."\n    down farm\n'
    'thing lamp in farm\n    name "lamp"\n    words lamp\n'
    'thing hat in farm\n    name "hat"\n    words hat\n    wearable\n'
    'thing box of container in farm\n    name "box"\n    words box\n    open\n'
    'thing cart of supporter in farm\n    name "cart"\n    words cart\n'
    'thing haystack of container in farm\n'
    '    name "haystack"\n    words haystack\n    scenery\n    open\n'
    '    on enter self\n        say "PLUNGE."\n'
)

_STORY = None


def _play(cmds):
    global _STORY
    if _STORY is None:
        _STORY = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY), io).run(max_steps=40_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def _reply(cmds):
    text = _play(cmds)
    last = cmds[-1]
    at = text.rindex(">" + last)
    return text[at:].split("\n")[1]


def test_plain_get_is_still_take():
    assert "Got it." in _reply(["get lamp"])


def test_get_in_and_into_are_enter():
    assert "PLUNGE." in _reply(["get in haystack"])
    assert "PLUNGE." in _reply(["get into haystack"])


def test_get_on_is_enter():
    # A supporter: boarding it is the default enter.
    assert "Done." in _reply(["get on cart"])


def test_get_out_of_and_get_off_are_exit():
    assert "Done." in _reply(["get in box", "get out of box"])
    assert "Done." in _reply(["get on cart", "get off cart"])


def test_bare_get_up_and_down_walk():
    text = _play(["get up"])
    assert "Loft" in text
    text = _play(["get up", "get down"])
    assert text.count("Farm") >= 2


def test_get_off_a_worn_thing_stays_take_off():
    assert "Off it comes." in _reply(["wear hat", "get off hat"])


def test_put_into_splits_the_nouns():
    assert "Done." in _reply(["put lamp into box"])


def test_bare_get_out_while_nested_is_exit():
    # GET OUT / GET UP with no noun, while inside or on something, means
    # getting off it, never a walk (the adopter's crate answered "There's
    # no exit in that direction"). Un-nested, the walk stays a walk (the
    # test above covers it).
    assert "Done." in _reply(["get in box", "get out"])
    assert "Done." in _reply(["get on cart", "get up"])
