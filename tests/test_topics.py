# test_topics.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The `topic` construct (conversation model, sub-step 1): a person's topics parse
with their modifiers (words / when / once / hidden) and body (you / reply / say /
reveal / hide), collect onto the object, and compile inert for now. The runtime
dispatch arrives with the topic table and the conversation granules."""

from arcturus import ast, cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n'
    'thing linda of person in hall\n    name "Linda"\n    words linda\n'
    '    topic paris "Ask about Paris" words paris, france when true once\n'
    '        you "How do you like Paris?"\n'
    '        reply "I love it, especially the Louvre."\n'
    '        reveal louvre\n'
    '    topic louvre "The Louvre" hidden\n'
    '        reply "Ah, the art!"\n'
)


def test_topics_parse_and_collect():
    world = analyze(parse(GAME))
    linda = world.objects["linda"]
    assert len(linda.topics) == 2

    paris = linda.topics[0]
    assert paris.subject == "paris"
    assert paris.words == ["paris", "france"]
    assert paris.once is True and paris.hidden is False
    assert paris.when is not None
    kinds = [type(s).__name__ for s in paris.body]
    assert kinds == ["Line", "Line", "TopicToggle"]
    assert paris.body[0].who == "you" and paris.body[1].who == "reply"
    assert paris.body[2].reveal is True and paris.body[2].target == "louvre"

    louvre = linda.topics[1]
    assert louvre.subject == "louvre"
    assert louvre.words == [] and louvre.hidden is True and louvre.once is False


def test_game_with_topics_compiles():
    # Inert for now: topics carry no runtime yet, but a game with them is valid.
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    assert img[0x00] == 5
