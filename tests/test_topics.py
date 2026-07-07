# test_topics.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The `topic` construct (conversation model). Sub-step 1: a person's topics
parse with their modifiers (words / when / once / hidden) and body (you / reply /
say / reveal / hide) and collect onto the object. Sub-step 2: the runtime, where
each person's topics lower to a table the conversation granules walk, the body
statements lower (you / reply auto-quote and attribute, reveal / hide flip a
sibling topic's visibility), and the topic_* intrinsics read the table. The
ask/tell and menu granules that drive it arrive in the following sub-steps."""

import shutil
import subprocess

import pytest

from arcturus import ast, cosmos
from arcturus import objects as objmod
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n'
    'thing linda of character in hall\n    name "Linda"\n    words linda\n'
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
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    assert img[0x00] == 5


def test_topic_table_emits():
    """Sub-step 2: each topic lowers to a record whose body and when-guard
    routines, menu label, and match words are wired through the object table's
    fixups. A `when`-less topic emits no guard; the words go to the dictionary."""
    layout = objmod.build_layout(analyze(parse(GAME)))
    assert "topics" in layout.prop_number

    routines = {nm for _off, nm in layout.routine_fixups}
    assert "topic_linda_0" in routines  # paris body
    assert "topic_linda_1" in routines  # louvre body
    assert "topicwhen_linda_0" in routines  # paris has `when true`
    assert "topicwhen_linda_1" not in routines  # louvre has no `when`

    words = {w for _off, w in layout.word_fixups}
    assert {"paris", "france"} <= words  # the ask/tell match words

    labels = set(layout.strings.values())
    assert {"Ask about Paris", "The Louvre"} <= labels


def test_topic_bodies_link_without_helpers():
    """The body and when-guard routines are emitted unconditionally when topics
    exist, because the table references them by name: GAME has no caller for any
    topic intrinsic, so the cosmos_topic_* helpers are gated off, yet the image
    still links (proving the bodies, not the helpers, back the table fixups)."""
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    assert img[0x00] == 5


# A driving game: a `chat` verb walks the person's topics, lists the visible
# ones, runs the first, then lists again. It exercises the whole runtime, since
# the conversation granules that normally call these intrinsics are not built yet.
DRIVE = '''game
    title "Topics"
    start hall
room hall
    name "Hall"
    desc "A bare hall."
thing linda of character in hall
    name "Linda"
    named
    words linda
    topic paris "Ask about Paris" words paris, france when true once
        you "How do you like Paris?"
        reply "I love it, especially the Louvre."
        reveal louvre
    topic louvre "The Louvre" hidden
        reply "Ah, the art."
    topic weather "The weather" when false
        reply "Looks like rain."
verb "chat"
    chat noun
on chat
    let i = 0
    while i < topics_count(noun)
        if topic_visible(noun, i)
            topic_label(noun, i)
            say " (shown)"
        change i to i + 1
    say "--- run ---"
    topic_run(noun, 0)
    say "--- after ---"
    let j = 0
    while j < topics_count(noun)
        if topic_visible(noun, j)
            topic_label(noun, j)
            say " (shown)"
        change j to j + 1
'''


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_topic_runtime_on_frotz(tmp_path):
    img = generate(analyze(cosmos.combined_program(parse(DRIVE))))
    story = tmp_path / "topics.z5"
    story.write_bytes(img)
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="chat linda\nquit\ny\n",
        capture_output=True, text=True, timeout=20,
    ).stdout

    before, _, after = out.partition("--- run ---")
    run, _, after = after.partition("--- after ---")

    # Before: only Paris is in view (Louvre is hidden, the weather's `when` is false).
    assert "Ask about Paris (shown)" in before
    assert "The Louvre" not in before
    assert "The weather" not in before

    # The exchange auto-quotes and attributes: the player as "You", the NPC by name.
    assert 'You: "How do you like Paris?"' in run
    assert 'Linda: "I love it, especially the Louvre."' in run

    # After: `reveal louvre` brought the Louvre into view, `once` retired Paris,
    # and the false-guarded weather topic is still hidden.
    assert "The Louvre (shown)" in after
    assert "Ask about Paris" not in after
    assert "The weather" not in after


# Sub-step 3: ask/tell topic dispatch through the extendedverbs granule. The
# subject (paris, louvre) is a topic word, not an object, so the verb is one noun
# plus a trailing preposition; the handler scans the typed words for a visible
# topic. ask and tell share the path. Linda has `words woman` so she is in scope
# under a name that is not also a topic word.
ASKTELL = '''game
    title "AskTell"
    start hall
summon.infocom_talking
room hall
    name "Hall"
    desc "A bare hall."
thing linda of character in hall
    name "Linda"
    named
    words linda, woman
    topic paris "Paris" words paris, france when true once
        you "How do you like Paris?"
        reply "I love it, especially the Louvre."
        reveal louvre
    topic louvre "The Louvre" words louvre, art hidden
        reply "Ah, the art."
'''


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ask_tell_dispatch_on_frotz(tmp_path):
    img = generate(analyze(cosmos.combined_program(parse(ASKTELL))))
    story = tmp_path / "asktell.z5"
    story.write_bytes(img)
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=(
            "ask linda about louvre\n"   # hidden at the start: no match, flat default
            "ask linda about paris\n"    # runs, reveals louvre, retires paris (once)
            "ask linda about paris\n"    # retired: flat default
            "tell linda about louvre\n"  # now revealed: tell reaches it too
            "ask linda about jupiter\n"  # no such topic: flat default
        ),
        capture_output=True, text=True, timeout=20,
    ).stdout
    parts = out.split(">")

    # parts[0] is the banner/room; parts[1..5] are the five command responses.
    assert "stays mum" in parts[1]  # louvre hidden -> flat default
    assert 'You: "How do you like Paris?"' in parts[2]  # paris runs
    assert 'Linda: "I love it, especially the Louvre."' in parts[2]
    assert "stays mum" in parts[3]  # paris retired by `once`
    assert 'Linda: "Ah, the art."' in parts[4]  # tell reaches the revealed topic
    assert "stays mum" in parts[5]  # unknown subject -> flat default


REVIVE = (
    'game\n    title "T"\n    start hall\n'
    'summon.infocom_talking\n'
    'room hall\n    name "Hall"\n    desc "x"\n'
    'thing bob of character in hall\n    name "Bob"\n    words bob\n    named\n'
    '    topic secret "a secret" words secret once\n'
    '        reply "I did it."\n'
    '    topic poke "a poke" words poke\n'
    '        reply "Poke."\n'
    '        reveal secret\n'
)


def test_reveal_brings_back_a_once_topic():
    # `once` stops the PLAYER, not the author: a spent `once` topic can be
    # revealed back in code, runs again, then retires again (docs/01 15).
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    story = load(generate(analyze(cosmos.combined_program(parse(REVIVE)))))
    io = CaptureIO(script=[
        "ask bob about secret",   # runs
        "ask bob about secret",   # once: stays mum
        "ask bob about poke",     # body reveals secret
        "ask bob about secret",   # revived: runs again
        "ask bob about secret",   # once again: stays mum
    ])
    try:
        VM(story, io).run(max_steps=5_000_000)
    except IndexError:
        pass
    parts = io.text.split(">")
    assert 'Bob: "I did it."' in parts[1]   # first telling
    assert "stays mum" in parts[2]          # once retired it
    assert 'Bob: "I did it."' in parts[4]   # reveal brought it back, it ran again
    assert "stays mum" in parts[5]          # and once retired it once more
