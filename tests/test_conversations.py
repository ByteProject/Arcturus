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


# -- the idle fallback topic (per-NPC default answer; Stefan's ruling) -------

IDLE_GAME = (
    'game\n    title "I"\n    start deck\nsummon.infocom_talking\n'
    'room deck\n    name "Deck"\n    desc "A deck."\n'
    'thing captain of character in deck\n    name "old captain"\n'
    '    words captain, old\n'
    '    topic ship "the ship" words ship, vessel\n'
    '        you "Tell me of the ship."\n'
    '        reply "She is the finest afloat."\n'
    '    topic shrug "his mood" idle\n'
    '        reply "The captain says nothing useful."\n'
)


def test_idle_answers_ask_and_tell_when_no_topic_matches():
    out = _ask_headless(IDLE_GAME, ["ask captain about weather",
                                    "tell captain about storms"])
    assert out.count("The captain says nothing useful.") == 2
    # A worded topic still wins over the idle.
    out2 = _ask_headless(IDLE_GAME, ["ask captain about ship"])
    assert "She is the finest afloat." in out2
    assert "says nothing useful" not in out2


def test_idle_once_answers_then_yields_to_the_flat_default():
    game = (
        'game\n    title "I"\n    start deck\nsummon.infocom_talking\n'
        'room deck\n    name "Deck"\n    desc "A deck."\n'
        'thing captain of character in deck\n    name "old captain"\n'
        '    words captain\n'
        '    topic done "x" idle once\n'
        '        reply "That is all on unfamiliar matters."\n'
    )
    out = _ask_headless(game, ["ask captain about x", "ask captain about y"])
    assert out.count("That is all on unfamiliar matters.") == 1
    assert "stays mum" in out.split("about y")[-1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_idle_topic_is_invisible_to_the_menu(tmp_path):
    # Stefan's point: a default is meaningless in the menu presentation, so an
    # idle topic is never listed there. The menu (an upper-window draw) shows
    # only the worded topics; driven on Frotz, like the other menu tests.
    game = (
        'game\n    title "M"\n    start hall\nsummon.conversations\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing pat of character in hall\n    name "Pat"\n    named\n    words pat\n'
        '    topic weather "the weather" words weather\n'
        '        reply "Could be worse."\n'
        '    topic shrug "his mood" idle\n'
        '        reply "Never shown in a menu."\n'
    )
    story = tmp_path / "im.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(game)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="talk to pat\n0\nquit\ny\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "1. the weather" in out
    assert "his mood" not in out
    assert "Never shown in a menu." not in out


def test_idle_with_words_is_refused():
    from arcturus.errors import ArcError
    game = (
        'game\n    title "I"\n    start hall\nsummon.infocom_talking\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing bob of character in hall\n    name "Bob"\n    words bob\n'
        '    topic oops "x" idle words weather\n'
        '        reply "x"\n'
    )
    with pytest.raises(ArcError, match="takes no `words`"):
        analyze(cosmos.combined_program(parse(game)))


def test_no_idle_topic_leaves_the_helper_unemitted():
    # Pay-for-use: a conversation game with no idle topic never references
    # cosmos_topic_idle, so it is dead-code-eliminated (byte-identical).
    import arcturus.codegen as cg
    generate(analyze(cosmos.combined_program(parse(GAME))))
    assert "cosmos_topic_idle" not in cg._LAST_LIVE_ROUTINES


def test_again_repeats_a_conversation_topic():
    # AGAIN restores a command's resolved operands, not the words the player
    # typed, and a topic's subject lives in those words: the replay used to
    # find no subject and fall to the flat default (the field report). The
    # granule now remembers what the person answered and repeats it.
    out = _ask_headless(CAPTAIN, ["ask captain about ship", "again", "again"])
    assert out.count("She is the finest afloat.") == 3


def test_again_does_not_replay_a_stale_topic():
    # An exchange that matched nothing clears the memory, so a later AGAIN
    # cannot resurrect an older topic (or fire one person's topic at another).
    out = _ask_headless(CAPTAIN, ["ask captain about ship",
                                  "ask captain about nonsense", "again"])
    assert out.count("She is the finest afloat.") == 1


def test_ask_and_tell_can_answer_differently():
    # One topic serves both verbs (it is one subject), and `action`
    # distinguishes them when the exchange should differ.
    game = (
        'game\n    title "T"\n    start deck\nsummon.infocom_talking\n'
        'room deck\n    name "Deck"\n    desc "A deck."\n'
        'thing lady of character in deck\n    name "Mrs. Loudbottom"\n'
        '    words lady\n    named\n'
        '    topic vase "the vase" words vase\n'
        '        if action is tell\n'
        '            reply "I know all about that vase."\n'
        '        else\n'
        '            reply "The vase was my mother\'s."\n'
    )
    out = _ask_headless(game, ["ask lady about vase", "tell lady about vase"])
    assert "The vase was my mother's." in out
    assert "I know all about that vase." in out


# -- shared subjects (Stefan's ruling; the field report of five NPCs each
# repeating one villain's vocabulary) ---------------------------------------

SUBJECT_GAME = (
    'game\n    title "S"\n    start square\nsummon.infocom_talking\n'
    'subject cowboy "the evil cowboy" words cowboy, buckaroo, mean\n'
    '    reply "Nobody here likes to talk about him."\n'
    'room square\n    name "Square"\n    desc "Dust."\n'
    'thing pope of character in square\n    name "Pope Leo"\n'
    '    words pope\n    named\n'
    '    topic cowboy\n        reply "I think he\'s swell."\n'
    'thing sheriff of character in square\n    name "sheriff"\n'
    '    words sheriff\n'
    '    topic cowboy once\n        reply "I\'ll see him hang."\n'
    'thing bard of character in square\n    name "bard"\n    words bard\n'
    '    topic cowboy "that dreadful man"\n'
    '        reply "I wrote a song about him."\n'
    'thing drunk of character in square\n    name "drunk"\n    words drunk\n'
    '    topic cowboy\n'
)


def test_one_subject_serves_the_whole_cast():
    # Each character answers in its own voice, and every synonym the SUBJECT
    # declares works for all of them: adding a word is one edit, not five.
    out = _ask_headless(SUBJECT_GAME, [
        "ask pope about cowboy", "ask sheriff about buckaroo",
        "ask bard about mean"])
    assert "I think he's swell." in out
    assert "I'll see him hang." in out
    assert "I wrote a song about him." in out


def test_a_topic_without_a_body_takes_the_subjects_default():
    out = _ask_headless(SUBJECT_GAME, ["ask drunk about cowboy"])
    assert "Nobody here likes to talk about him." in out


def test_a_character_keeps_its_own_modifiers_and_label():
    # `once` is per character: the sheriff answers once and then falls silent,
    # while the pope keeps answering.
    out = _ask_headless(SUBJECT_GAME, [
        "ask sheriff about cowboy", "ask sheriff about cowboy",
        "ask pope about cowboy"])
    assert out.count("I'll see him hang.") == 1
    assert "I think he's swell." in out


def test_the_shared_vocabulary_is_emitted_once():
    # The byte payoff: identical match-word lists collapse to one array that
    # every record points at, so a big cast costs records, not vocabularies.
    story = generate(analyze(cosmos.combined_program(parse(SUBJECT_GAME))))
    lone = SUBJECT_GAME.replace(
        'thing sheriff of character in square\n    name "sheriff"\n'
        '    words sheriff\n'
        '    topic cowboy once\n        reply "I\'ll see him hang."\n', '')
    smaller = generate(analyze(cosmos.combined_program(parse(lone))))
    # Dropping a whole character saves a record and its routine, but NOT a
    # second copy of the words: the four-character build is not four
    # vocabularies bigger.
    assert len(story) - len(smaller) < 120


def test_a_topic_naming_no_subject_still_needs_a_label():
    from arcturus.errors import ArcError
    game = (
        'game\n    title "S"\n    start hall\nsummon.infocom_talking\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing bob of character in hall\n    name "Bob"\n    words bob\n'
        '    topic weather\n        reply "Wet."\n'
    )
    with pytest.raises(ArcError, match="needs a label"):
        analyze(cosmos.combined_program(parse(game)))


def test_a_topic_naming_a_subject_may_not_redeclare_words():
    from arcturus.errors import ArcError
    game = SUBJECT_GAME.replace(
        '    topic cowboy\n        reply "I think he\'s swell."\n',
        '    topic cowboy words rustler\n        reply "Swell."\n')
    with pytest.raises(ArcError, match="already owns the match words"):
        analyze(cosmos.combined_program(parse(game)))
