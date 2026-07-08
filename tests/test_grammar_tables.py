# test_grammar_tables.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The positional grammar layer (docs/02 section 8c). A verb whose grammar the
flag model cannot represent (a leading preposition on a two-noun verb, or
wording that selects the action) is compiled to a grammar table and matched
positionally; every other verb stays on the classic flag path, byte for byte.

The anchor case is the one that triggered the overhaul: `dig in noun with
held` used to split at the leading IN, leaving the first noun empty and the
rest one ambiguous phrase. The capability case is a wording-selected action:
LOOK UNDER and LOOK BEHIND reaching different actions, which the flag model
(one action byte per verb word) cannot express at all."""

import pytest

from arcturus import cosmos
from arcturus import worldmodel as wm
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start beach\n'
    'room beach\n    name "Beach"\n    desc "Sand."\n'
    'thing sand in beach\n    name "sand"\n    words sand\n'
    'thing shovel in beach\n    name "shovel"\n    words shovel\n'
    'thing bed in beach\n    name "bed"\n    words bed\n'
    'verb "dig", "excavate"\n'
    '    dig\n'
    '    dig noun\n'
    '    dig noun with held\n'
    '    dig in noun with held\n'
    'on dig\n'
    '    if noun is nothing\n        say "DIG BARE."\n        stop\n'
    '    if second is nothing\n        say "DIG ${the noun}."\n        stop\n'
    '    say "DIG ${the noun} USING ${the second}."\n'
    'verb "peek"\n'
    '    look_under under noun\n'
    '    look_behind behind noun\n'
    'on look_under\n    say "UNDER ${the noun}."\n'
    'on look_behind\n    say "BEHIND ${the noun}."\n'
)

_STORY = {}


def _run(cmds, game=GAME, key=None):
    if isinstance(cmds, str):
        cmds = [cmds]
    k = key or game
    if k not in _STORY:
        _STORY[k] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[k]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def _reply(cmds, game=GAME, key=None):
    text = _run(cmds, game, key)
    last = cmds if isinstance(cmds, str) else cmds[-1]
    at = text.rindex(">" + last)
    return text[at:].split("\n")[1]


# -- the anchor case: the dig grammar from the field report -----------------

def test_dig_acceptance_cases():
    assert "DIG BARE." in _reply("dig")
    assert "DIG the sand." in _reply("dig sand")
    assert "DIG the sand USING the shovel." in _reply("dig sand with shovel")
    # These two were the broken ones: the leading IN ate the first noun.
    assert "DIG the sand." in _reply("dig in sand")
    assert "DIG the sand USING the shovel." in _reply("dig in sand with shovel")
    # A synonym reaches the same table.
    assert "DIG the sand USING the shovel." in _reply("excavate in sand with shovel")
    # Articles inside the slots are ordinary phrase content.
    assert "DIG the sand USING the shovel." in _reply("dig in the sand with the shovel")


def test_wording_selects_the_action():
    # The capability the flag model cannot express: one verb word, two actions,
    # chosen by the literal in the line.
    assert "UNDER the bed." in _reply("peek under bed")
    assert "BEHIND the bed." in _reply("peek behind bed")


def test_no_line_fits_is_the_extra_words_fault():
    # PEEK BED matches neither line (both need their literal): the verb was
    # understood, the rest was not.
    assert "You lost me after that." in _reply("peek bed")


def test_empty_slot_is_left_to_the_action():
    # DIG WITH SHOVEL fits `dig noun with held` with an empty first slot: the
    # noun stays nothing and the action asks its own question.
    assert "DIG BARE." in _reply("dig with shovel")


def test_unresolved_slot_faults_honestly():
    # An unknown word in a two-slot line is rejected, not run with no noun,
    # and named back (parse_fault 4).
    assert 'know the word "xyzzq"' in _reply("dig in xyzzq with shovel")


def test_slot_ambiguity_asks_and_the_answer_resolves():
    text = _run(["dig sand shovel", "sand"])
    assert "Which do you mean, the sand or the shovel?" in text
    assert "DIG the sand." in text


def test_pronoun_binds_inside_a_slot():
    text = _run(["dig sand", "dig in it with shovel"])
    assert "DIG the sand USING the shovel." in text


def test_oops_corrects_into_the_table():
    text = _run(["dig in samd with shovel", "oops sand"])
    assert 'know the word "samd"' in text
    assert "DIG the sand USING the shovel." in text


def test_chaining_runs_both_tabled_commands():
    text = _run(["dig in sand and peek under bed"])
    assert "DIG the sand." in text
    assert "UNDER the bed." in text


def test_again_replays_a_tabled_command():
    text = _run(["dig in sand with shovel", "g"])
    assert text.count("DIG the sand USING the shovel.") == 2


def test_quoted_literal_is_the_same_word():
    # The quoted form used to crash the compiler; now it is the bare word.
    game = GAME.replace("dig in noun with held", 'dig "in" noun with held')
    assert "DIG the sand USING the shovel." in _reply(
        "dig in sand with shovel", game=game, key="quoted"
    )


# -- the tabling rule and its guardrails -------------------------------------

def _world(game):
    return analyze(cosmos.combined_program(parse(game)))


def test_shipped_packs_have_no_tabled_verb():
    # The zero-cost proof: every standard verb in every language pack fits the
    # flag model, so no story pays for the matcher unless its own grammar asks
    # for it (the size ceilings pin the byte side of this).
    for example in (
        "examples/cloak-of-darkness.storyarc",
        "examples/beispiel-deutsch.storyarc",
        "examples/ejemplo-espanol.storyarc",
    ):
        with open(example, encoding="utf-8") as fh:
            assert wm.tabled_verbs(_world(fh.read())) == [], example


def test_needs_table_rule():
    w = _world(GAME)
    tabled = {v.words[0] for v in wm.tabled_verbs(w)}
    assert tabled == {"dig", "peek"}
    # look (leading AT on a one-noun verb) and switch (particle-decided
    # actions, identical shapes) stay on the flag path.
    for verb in w.verbs:
        if verb.words[0] in ("look", "switch"):
            assert not wm.needs_table(verb)


def test_positional_verb_rejects_adjacent_slots():
    game = GAME.replace("dig noun with held", "dig noun noun")
    with pytest.raises(ArcError, match="literal word between"):
        _world(game)


def test_positional_verb_rejects_reverse():
    game = GAME.replace("dig noun with held", "dig noun with held reverse")
    with pytest.raises(ArcError, match="reverse"):
        _world(game)


# -- the German pack drives the same agnostic matcher ------------------------

GAME_DE = (
    'summon.language "german"\n'
    'game\n    title "T"\n    start strand\n'
    'room strand\n    name "Strand"\n    desc "Sand."\n'
    'thing sand in strand\n    name "Sand"\n    words sand\n    masculine\n'
    'thing schaufel in strand\n    name "Schaufel"\n    words schaufel\n    feminine\n'
    'verb "grabe", "grab"\n'
    '    dig\n'
    '    dig noun\n'
    '    dig noun mit noun\n'
    '    dig in noun mit noun\n'
    'on dig\n'
    '    if noun is nothing\n        say "GRABE BLOSS."\n        stop\n'
    '    if second is nothing\n        say "GRABE ${the noun}."\n        stop\n'
    '    say "GRABE ${the noun} MIT ${the second}."\n'
)


def test_german_tabled_verb():
    # The handler prints `${the ...}` (nominative); the parse is what is
    # under test: the leading IN and the typed articles must not derail it.
    assert "GRABE BLOSS." in _reply("grabe", game=GAME_DE, key="de")
    assert "GRABE der Sand." in _reply("grabe den sand", game=GAME_DE, key="de")
    assert "GRABE der Sand MIT die Schaufel." in _reply(
        "grabe in dem sand mit der schaufel", game=GAME_DE, key="de"
    )
