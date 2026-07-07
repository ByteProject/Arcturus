# test_self_pattern.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`self` as a handler-pattern operand (docs/01 section 12): inside an object
or kind body, `on put noun in self` and `on enter self` name the enclosing
object in its own pattern. Field report: replacing the object's name with
`self` in such headers was a compile error, while `self` worked everywhere
else, an inconsistency. In a kind body each instance guards its own number;
a free-standing rule has no enclosure and errors with guidance."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start farm\n'
    'room farm\n    name "Farm"\n    desc "x"\n'
    'thing coin in farm\n    name "coin"\n    words coin\n'
    'thing box of container in farm\n    name "box"\n    words box\n    open\n'
    'thing haystack of container in farm\n'
    '    name "haystack"\n    words haystack\n    scenery\n    open\n'
    '    on enter self\n'
    '        say "PLUNGE."\n'
    '    on put noun in self\n'
    '        move noun to nothing\n'
    '        say "VANISH ${the noun}."\n'
    'kind hidey of container\n'
    '    on enter self\n'
    '        say "SQUEEZE ${the noun}."\n'
    'thing barrel of hidey in farm\n    name "barrel"\n    words barrel\n    open\n'
    'thing crate of hidey in farm\n    name "crate"\n    words crate\n    open\n'
)


def _play(cmds):
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(story, io).run(max_steps=30_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_self_in_the_second_slot_guards_the_owner():
    text = _play(["put coin in haystack"])
    assert "VANISH the coin." in text


def test_self_pattern_does_not_catch_other_containers():
    text = _play(["put coin in box"])
    assert "VANISH" not in text
    assert "Done." in text


def test_self_as_the_noun_slot():
    text = _play(["enter haystack"])
    assert "PLUNGE." in text
    assert "can't get inside" not in text


def test_self_in_a_kind_body_means_each_instance():
    text = _play(["enter barrel", "out", "enter crate"])
    assert "SQUEEZE the barrel." in text
    assert "SQUEEZE the crate." in text


def test_self_in_a_free_rule_errors_with_guidance():
    bad = ('game\n    title "T"\n    start r\n'
           'room r\n    name "R"\n    desc "x"\n'
           'on enter self\n    say "no"\n')
    with pytest.raises(ArcError, match="enclosing object"):
        analyze(cosmos.combined_program(parse(bad)))
