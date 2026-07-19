# test_conversations.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The conversations granule (sub-step 4): the menu presentation of the `topic`
model. TALK TO a person lists their visible topics numbered; a single keypress
runs one (read_key / the read_char opcode); the menu redraws as topics reveal and
retire; 0 ends it. Built on the same topic table the ask/tell path walks. Driven
on Frotz, one keypress per line (dumb Frotz reads the first char of each line)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


GAME = '''game
    title "ConvMenu"
    start hall
summon.conversations
room hall
    name "Hall"
    desc "A bare hall."
thing pat of character in hall
    name "Pat"
    named
    words pat
    topic weather "the weather" words weather
        you "Some weather we're having."
        reply "Could be worse."
        reveal secret
    topic city "the city" words city
        you "How long have you lived here?"
        reply "All my life."
    topic secret "the secret" words secret hidden once
        reply "All right, all right. The money's in the locker."
'''


def test_conversations_compiles():
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    assert img[0x00] == 5


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_conversation_menu_on_frotz(tmp_path):
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    story = tmp_path / "conv.z5"
    story.write_bytes(img)
    # talk, pick 1 (weather: reveals secret, then weather drops off), 0 to end.
    # The menu is painted in the upper window, so dumb Frotz dumps its repaints
    # inline; assertions are substring-presence, order-independent.
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="talk to pat\n1\n0\nquit\ny\n",
        capture_output=True, text=True, timeout=20,
    ).stdout

    # The numbered menu, weather first; the hidden secret starts off the list.
    assert "Talk to Pat about:" in out
    assert "1. the weather" in out
    assert "2. the city" in out

    # Picking 1 runs the exchange in the main window.
    assert 'You: "Some weather we\'re having."' in out
    assert 'Pat: "Could be worse."' in out

    # After the pick the menu repaints: weather has dropped off (discussed) and the
    # revealed secret appears. That weather is gone is provable from the renumber -
    # the city is now 1 and the secret is 2, not 2 and 3.
    assert "1. the city" in out
    assert "2. the secret" in out

    # 0 ends the conversation and returns to the main prompt.
    assert "You let the conversation rest there." in out


# When both presentations are summoned, the menu wins the mutual exclusion:
# ASK opens the menu (asking IS talking) and TELL answers with the use-TALK
# hint, IN EITHER SUMMON ORDER: whichever granule owns the typed word, the
# verbs converge on the same behavior (Stefan's ruling, 2026-07-04).
BOTH = '''game
    title "Both"
    start hall
summon.extendedverbs
summon.conversations
room hall
    name "Hall"
    desc "A bare hall."
thing pat of character in hall
    name "Pat"
    named
    words pat
    topic weather "the weather" words weather
        you "Some weather we're having."
        reply "Could be worse."
'''


def test_both_summoned_compiles():
    assert generate(analyze(cosmos.combined_program(parse(BOTH))))[0x00] == 5


def _menu_owns_ask_tell(tmp_path, src, name):
    story = tmp_path / name
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(src)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="tell pat about weather\nask pat about weather\n1\n0\nquit\ny\n",
        capture_output=True, text=True, timeout=20,
    ).stdout
    # tell answers with the hint and never opens the menu or runs the topic.
    tell_part = out.split("Talk to Pat about:")[0]
    assert "just TALK TO Pat" in tell_part
    assert "Could be worse." not in tell_part
    # ask opens the menu and the picked topic runs.
    assert "Talk to Pat about:" in out
    assert "Could be worse." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_menu_wins_over_ask_tell_on_frotz(tmp_path):
    _menu_owns_ask_tell(tmp_path, BOTH, "both.z5")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_menu_wins_in_the_other_summon_order(tmp_path):
    # The convergence must not depend on which granule owns the dictionary
    # word: reverse the summons and ask/tell behave identically.
    src = BOTH.replace(
        "summon.extendedverbs\nsummon.conversations",
        "summon.conversations\nsummon.extendedverbs",
    )
    _menu_owns_ask_tell(tmp_path, src, "reversed.z5")


def test_conversations_and_infocom_talking_exclude_each_other():
    # The two presentations of the topic model are mutually exclusive by
    # design (Stefan's ruling, 2026-07-04): an author settles on one.
    src = BOTH.replace("summon.extendedverbs", "summon.infocom_talking")
    with pytest.raises(Exception, match="picks exactly one"):
        cosmos.combined_program(parse(src))


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ask_tell_in_a_menu_only_game(tmp_path):
    # Without extendedverbs the conversations granule supplies ASK and TELL
    # itself: ask opens the menu, tell hints at TALK TO.
    src = BOTH.replace("summon.extendedverbs\n", "")
    _menu_owns_ask_tell(tmp_path, src, "menuonly.z5")


def _ask_headless(game, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds) + ["quit", "y"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


# The infocom-style ask/tell routes each subject to its own topic, and a
# topic whose match-words overlap the NPC's own name no longer fires for
# every ask (the field report via Charles Moore Jr.: "the first topic's
# response no matter what I ask"). Only the SUBJECT phrase, the words after
# the about/for separator, is scanned; the listener's name before it is not.
CAPTAIN = (
    'game\n    title "C"\n    start deck\nsummon.infocom_talking\n'
    'room deck\n    name "Deck"\n    desc "A deck."\n'
    'thing captain of character in deck\n    name "old captain"\n'
    '    words captain, old, jack\n'
    '    topic person "himself" words captain, jack\n'
    '        you "Tell me about yourself."\n'
    '        reply "I am Captain Jack."\n'
    '    topic ship "the ship" words ship, vessel\n'
    '        you "Tell me of the ship."\n'
    '        reply "She is the finest afloat."\n'
)


def test_ask_routes_to_the_named_subject_not_the_first_topic():
    out = _ask_headless(CAPTAIN, ["ask captain about ship"])
    assert "She is the finest afloat." in out
    assert "I am Captain Jack." not in out


def test_ask_about_the_npc_name_still_reaches_its_topic():
    # ASK JACK ABOUT JACK: the second "jack" is the subject, so the self
    # topic answers. This is why the fix scans by position (after the
    # separator) rather than skipping the person's whole vocabulary.
    out = _ask_headless(CAPTAIN, ["ask captain about jack"])
    assert "I am Captain Jack." in out


def test_ask_about_an_unknown_subject_hits_the_flat_default():
    out = _ask_headless(CAPTAIN, ["ask captain about nonsense"])
    assert "I am Captain Jack." not in out
    assert "She is the finest afloat." not in out
