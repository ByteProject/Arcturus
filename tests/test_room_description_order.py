# test_room_description_order.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The room description's order (docs/01 chapter 7; Stefan's ruling
2026-11-21): the description, then what sits on or in scenery holders,
then the paragraphs things own (appearance, unmoved intro), then the
combined sentence of the plain items, and last the paragraphs characters
own. A character without a paragraph stays in the sentence. An existence
object's paragraph sits with the things' in every room it is in."""

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
        pass  # script exhausted at the next prompt
    return io.text


def _look(out):
    return out.split(">look")[1].split(">")[0]


DINER = (
    'constant scenery_contents = true\n'
    'game\n    title "T"\n    start diner\n'
    'room diner\n    name "Diner"\n    desc "A chrome diner."\n    east yard\n'
    'room yard\n    name "Yard"\n    desc "Gravel."\n    west diner\n'
    'thing table of supporter in diner\n    name "table"\n    words table\n    scenery\n'
    'thing plate in table\n    name "plate"\n    words plate\n'
    'thing cook of character in diner\n    name "cook"\n    words cook\n'
    '    appearance "The cook leans on the counter."\n'
    'thing lamp in diner\n    name "lamp"\n    words lamp\n'
    'thing jar in diner\n    name "jar"\n    words jar\n'
    '    intro "A glass jar sits on the floor."\n'
)


def _order(text, *parts):
    at = [text.index(p) for p in parts]
    return at == sorted(at)


def test_scenery_things_sentence_then_characters():
    look = _look(_run(DINER, ["look"]))
    assert _order(look, "A chrome diner.", "On the table you can see a plate.",
                  "A glass jar sits on the floor.", "You can see a lamp here.",
                  "The cook leans on the counter.")


def test_a_character_without_a_paragraph_stays_in_the_sentence():
    src = DINER + 'thing waiter of character in diner\n    name "waiter"\n    words waiter\n'
    look = _look(_run(src, ["look"]))
    assert "You can see a lamp and a waiter here." in look
    assert _order(look, "You can see a lamp and a waiter here.",
                  "The cook leans on the counter.")


def test_without_a_characters_paragraph_the_things_close_on_the_sentence():
    src = DINER.replace('    appearance "The cook leans on the counter."\n', '')
    look = _look(_run(src, ["look"]))
    assert _order(look, "A glass jar sits on the floor.",
                  "You can see a cook and a lamp here.")


def test_a_taken_intro_joins_the_sentence():
    look = _look(_run(DINER, ["take jar", "drop jar", "look"]))
    assert "You can see a jar and a lamp here." in look
    assert "A glass jar" not in look
    assert _order(look, "You can see a jar and a lamp here.",
                  "The cook leans on the counter.")


def test_without_scenery_contents_the_things_come_first():
    src = DINER.replace("constant scenery_contents = true\n", "")
    look = _look(_run(src, ["look"]))
    assert "On the table" not in look
    assert _order(look, "A chrome diner.", "A glass jar sits on the floor.",
                  "You can see a lamp here.", "The cook leans on the counter.")


def test_an_existence_objects_paragraph_sits_with_the_things_everywhere():
    src = DINER + (
        'thing radio in diner, yard\n    name "radio"\n    words radio\n'
        '    fixed\n    appearance "A radio crackles somewhere."\n'
        'thing crate in diner, yard\n    name "crate"\n    words crate\n    fixed\n'
        'thing pebble in yard\n    name "pebble"\n    words pebble\n'
    )
    out = _run(src, ["look", "east", "look"])
    diner = out.split(">look")[1].split(">")[0]
    yard = out.split(">look")[2].split(">")[0]
    assert _order(diner, "A glass jar", "A radio crackles somewhere.",
                  "You can see", "crate", "The cook leans")
    assert _order(yard, "Gravel.", "A radio crackles somewhere.",
                  "You can see", "crate")
