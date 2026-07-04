# test_worldmodel.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The B2 done-test: the world-model IR for both example games is correct."""

import os

from arcturus import worldmodel as wm
from arcturus.parser import parse
from arcturus.sema import analyze

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def world(name):
    path = os.path.join(EXAMPLES, name)
    with open(path, "r", encoding="utf-8") as fh:
        return analyze(parse(fh.read(), path), filename=path)


def test_brass_lantern_ir():
    w = world("brass-lantern.storyarc")
    assert w.start_room == "hallway"

    # Objects and their categories (player comes from the standard prelude).
    assert w.objects["hallway"].category == "room"
    assert w.objects["cellar"].category == "room"
    assert w.objects["lantern"].category == "thing"
    assert "player" in w.objects

    # The lantern's switch handlers and a game-introduced boolean property.
    lantern = w.objects["lantern"]
    events = [h.events for h in lantern.handlers]
    assert ["switch_on"] in events and ["switch_off"] in events
    assert w.properties["pulled"].origin == "game"
    assert w.properties["pulled"].storage == wm.STORE_ATTRIBUTE

    # A standard boolean property is an attribute; a standard value is a slot.
    assert w.properties["lit"].storage == wm.STORE_ATTRIBUTE
    assert w.properties["name"].type == "text"
    assert w.properties["name"].storage == wm.STORE_SLOT

    # The direction is wired as a property value on the room.
    assert "north" in w.objects["hallway"].props

    # The added verb maps to the pull action.
    assert any("pull" == g.action for v in w.verbs for g in v.grammar)

    # Every is-test in the game is a boolean property test.
    assert set(w.is_resolutions.values()) == {wm.IS_PROPERTY}

    # on start is a free-standing handler.
    assert any(h.events == ["start"] for h in w.free_handlers)


def test_cloak_of_darkness_ir():
    w = world("cloak-of-darkness.storyarc")
    assert w.start_room == "foyer"

    # The hook is a supporter; its kind chain runs through thing.
    hook = w.objects["hook"]
    assert hook.kind == "supporter"
    assert hook.chain == ["supporter", "thing"]

    # The cloak starts carried by the player.
    assert w.objects["cloak"].location == "player"

    # disturbed is a numeric global, not a property.
    assert "disturbed" in w.globals and w.globals["disturbed"].type == "number"
    assert "disturbed" not in w.properties

    # The foyer overrides go north; the 1:1 port carries no grains (the
    # original Cloak answers for nothing beyond its three objects).
    foyer = w.objects["foyer"]
    assert any("go" in h.events for h in foyer.handlers)
    assert not foyer.grains

    # read -> examine and hang -> put are bound as verb actions.
    actions = {g.action for v in w.verbs for g in v.grammar}
    assert {"examine", "put"} <= actions

    # The bar light tests resolve as boolean property tests; the dark-go
    # handler's `way is not north` is a plain equality.
    assert set(w.is_resolutions.values()) == {wm.IS_PROPERTY, wm.IS_EQUALITY}
