# test_sema.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Semantic-analysis unit tests: name resolution, the property model, the
is-test disambiguation, and the representative diagnostics from docs/01
section 16."""

import pytest

from arcturus import worldmodel as wm
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze


def sema(src):
    return analyze(parse(src))


def expect_error(src, substring):
    with pytest.raises(ArcError) as exc:
        sema(src)
    assert substring in str(exc.value), str(exc.value)


# -- property model --------------------------------------------------------


def test_boolean_property_is_attribute_candidate():
    w = sema("thing a\n    glowing true\n")
    p = w.properties["glowing"]
    assert p.type == "bool" and p.storage == wm.STORE_ATTRIBUTE


def test_value_property_is_slot():
    w = sema("thing a\n    weight 5\n")
    p = w.properties["weight"]
    assert p.type == "number" and p.storage == wm.STORE_SLOT


def test_words_is_a_list_property():
    w = sema("thing a\n    words red, blood, ruby\n")
    assert w.properties["words"].type == "list"


def test_property_type_consistent_across_sites_ok():
    # Declared on a kind and an instance with the same type: no clash.
    w = sema("kind k of thing\n    weight 0\nthing a of k\n    weight 5\n")
    assert w.properties["weight"].type == "number"
    assert len(w.properties["weight"].decl_sites) == 2


def test_property_type_clash():
    expect_error(
        "thing a\n    weight 5\nthing b\n    weight \"heavy\"\n",
        "one type program-wide",
    )


def test_mutate_undeclared_property():
    expect_error(
        "thing a\n    on examine\n        change a.foo to true\n",
        "undeclared property 'foo'",
    )


def test_now_needs_boolean_property():
    expect_error(
        "thing a\n    on examine\n        now a is name\n",
        "needs a boolean property",
    )


def test_now_undeclared_property():
    expect_error(
        "thing a\n    on examine\n        now a is sparkly\n",
        "undeclared property 'sparkly'",
    )


# -- conditions ------------------------------------------------------------


def test_non_boolean_condition_errors():
    expect_error(
        "global n = 0\nthing a\n    on examine\n        if n\n            say \"x\"\n",
        "must be boolean",
    )


def test_boolean_conditions_pass():
    # Comparison, property test, holds, logic, not: all boolean.
    sema(
        "global n = 0\n"
        "thing a\n"
        "    on examine\n"
        "        if n > 0\n"
        "            say \"1\"\n"
        "        if a is lit\n"
        "            say \"2\"\n"
        "        if player holds a\n"
        "            say \"3\"\n"
        "        if not (a is lit and n > 0)\n"
        "            say \"4\"\n"
    )


# -- is disambiguation -----------------------------------------------------


def test_is_property_versus_equality():
    w = sema(
        "thing ruby\n"
        "    name \"ruby\"\n"
        "thing chest\n"
        "    on examine\n"
        "        if chest is open\n"
        "            say \"1\"\n"
        "        if noun is ruby\n"
        "            say \"2\"\n"
    )
    vals = list(w.is_resolutions.values())
    assert vals.count(wm.IS_PROPERTY) == 1
    assert vals.count(wm.IS_EQUALITY) == 1


def test_is_clash_when_name_is_both_property_and_object():
    expect_error(
        "thing shiny\n"
        "    name \"s\"\n"
        "thing gem\n"
        "    shiny true\n"
        "    on examine\n"
        "        if gem is shiny\n"
        "            say \"x\"\n",
        "both a boolean property and an object",
    )


# -- names, handlers, kinds ------------------------------------------------


def test_unknown_name():
    expect_error(
        "thing a\n    on examine\n        say \"${blorp}\"\n",
        "unknown name 'blorp'",
    )


def test_unknown_action_in_handler():
    expect_error("thing a\n    on frobnicate\n        say \"x\"\n", "unknown verb or action")


def test_multi_verb_handler_validates_each_verb():
    # push, pull, turn are all standard actions.
    sema("thing a\n    on push, pull, turn\n        say \"nope\"\n")
    # one bad verb in the list is caught.
    expect_error(
        "thing a\n    on push, zap\n        say \"x\"\n", "unknown verb or action 'zap'"
    )


def test_on_other_is_allowed():
    w = sema("thing a\n    on other\n        say \"silence\"\n")
    assert w.objects["a"].handlers[0].events == ["other"]


def test_handler_operand_must_resolve():
    expect_error("on take florble\n    say \"x\"\n", "not an object, kind, or direction")


def test_change_here_rejected():
    expect_error(
        "thing a\n    on examine\n        change here to a\n",
        "maintained by Cosmos",
    )


def test_change_constant_rejected():
    expect_error(
        "constant max = 10\nthing a\n    on examine\n        change max to 5\n",
        "is a constant",
    )


def test_duplicate_declaration():
    expect_error(
        "thing a\n    name \"A\"\nthing a\n    name \"B\"\n", "duplicate declaration"
    )


def test_unknown_parent_kind():
    expect_error("thing a of wibble\n    name \"A\"\n", "unknown kind")


def test_cyclic_kind():
    expect_error("kind x of y\n    lit false\nkind y of x\n    lit false\n", "cyclic")


def test_unknown_start_room():
    expect_error("game\n    start nowhere\n", "start room 'nowhere' is not defined")


def test_add_remove_require_list_property():
    expect_error(
        "thing a\n    on examine\n        add \"x\" to a.name\n",
        "not a list property",
    )
