# test_perform_running.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""perform(action, statue): the RUNNING action redirected onto another
object (improvmonster's help request, 2026-11-11). His two attempts,
perform(action, x) and perform(verb_trigger, x), killed the compiler with a
Python traceback (a misnamed variable in perform's own error path). Now
the running action is a legal first argument, the target's own handlers
answer, a first argument that cannot be an action is refused by name, and
performing exactly the running command again is refused instead of
recursing until the machine dies. The debug SCOPE verb lists everything
in_scope answers for, backstage things and exposed belongings included
(improvmonster's report, 2026-11-12)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_build(src)), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


BASE = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing key in player\n    name "key"\n    words key\n'
    'thing statue in hall\n    name "statue"\n    words statue\n    fixed\n'
    '    on examine\n        say "The statue gazes back."\n'
    '    on push\n        say "The statue rocks on its plinth."\n'
    'thing shadow in hall\n    name "shadow"\n    words shadow\n    scenery\n'
    '    on smell\n        say "The shadow smells of nothing."\n'
)

REDIRECT = BASE + (
    '    on other\n'
    '        if second is self\n'
    '            perform(action, noun, statue)\n'
    '        else\n'
    '            perform(action, statue, second)\n'
)


def test_the_running_action_lands_on_the_target_and_its_handlers():
    out = _run(REDIRECT, ["examine shadow", "push shadow", "take shadow",
                          "smell shadow", "put key on shadow"])
    assert "The statue gazes back." in out
    assert "The statue rocks on its plinth." in out
    assert "The statue stays exactly where it is." in out
    # the shadow's own handler still answers first for its own verbs
    assert "The shadow smells of nothing." in out
    # the second slot redirects too
    assert "The statue won't hold it." in out


def test_performing_the_running_command_again_never_hangs():
    # Keeping `second` while the shadow IS the second re-enters its own
    # `on other`: the guard refuses the repeat instead of recursing.
    src = BASE + '    on other\n        perform(action, statue, second)\n'
    out = _run(src, ["put key on shadow", "look"])
    assert "Hall" in out.split("look")[-1]


def test_a_local_holding_an_action_is_accepted():
    src = BASE + (
        'verb "nudge"\n    nudge noun\n'
        'on nudge\n    let a = action_id("push")\n    perform(a, statue)\n'
    )
    out = _run(src, ["nudge shadow"])
    assert "The statue rocks on its plinth." in out


def test_verb_trigger_is_refused_by_name():
    src = BASE + '    on other\n        perform(verb_trigger, statue)\n'
    with pytest.raises(ArcError, match="verb_trigger is the word the player typed"):
        _build(src)


def test_a_value_that_is_not_an_action_is_refused():
    src = BASE + '    on other\n        perform(statue, statue)\n'
    with pytest.raises(ArcError, match="perform needs an action"):
        _build(src)


def test_a_quoted_action_is_unchanged():
    src = BASE + (
        'verb "nudge"\n    nudge noun\n'
        'on nudge\n    perform("push", statue)\n'
    )
    out = _run(src, ["nudge shadow"])
    assert "The statue rocks on its plinth." in out


SCOPE = (
    'summon.debug\n'
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing lamp in hall\n    name "lamp"\n    words lamp\n'
    'thing chip in scope\n    name "chip"\n    words chip\n    scenery\n'
    'thing guard of character in hall\n    name "guard"\n    words guard\n'
    'thing badge in guard\n    name "badge"\n    words badge\n    exposed\n'
    'thing purse in guard\n    name "purse"\n    words purse\n'
    'thing pebble in hall\n    name "pebble"\n    words pebble\n'
    'on start\n    move pebble to scope\n'
)


def test_scope_lists_what_the_parser_can_see():
    out = _run(SCOPE, ["scope"])
    listing = out.split(">scope")[-1]
    head, also = listing.split("Also in scope:")
    assert "lamp" in head and "guard" in head
    # backstage, moved backstage at run time, and an exposed belonging
    assert "chip" in also and "pebble" in also and "badge" in also
    # a character's private belonging is not in scope
    assert "purse" not in listing
