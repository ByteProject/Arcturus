# test_custom_directions.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Custom directions ride the spare standard properties (Charles's report):
a game declares its own words onto fore/aft/port/starboard (`direction fore
"widdershins", "wid"`) and gets a full direction, bare typed word,
abbreviation, exits, and handlers alike. The canonical word a property
answers to in OUTPUT follows the most specific declaration: the game's
rebind speaks the game's word (never the property name), while a granule
that merely ADDS vocabulary to a worded property (nautical's ALOFT riding
up) never steals the canonical."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'summon.verbose_exits\n'
    'game\n    title "D"\n    start hub\n'
    'direction fore "widdershins", "wid"\n'
    'direction aft "turnwise", "turn"\n'
    'room hub\n    name "Hub"\n    desc "The hub."\n    fore rim\n'
    'room rim\n    name "Rim"\n    desc "The rim."\n    aft hub\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_a_rebound_spare_direction_walks_by_word_and_abbreviation():
    out = _run(["widdershins", "turnwise", "wid"])
    assert out.count("Rim") >= 2   # there, back, there again
    assert "Hub" in out[out.index("turnwise"):]


def test_output_speaks_the_game_s_word_never_the_property_name():
    # A blocked try lists the live exits: the game hears widdershins,
    # not the carrier property's internal name.
    out = _run(["turnwise"])
    assert "You can only go widdershins from here." in out
    assert "go fore" not in out


def test_a_granule_synonym_never_steals_a_worded_canonical():
    # summon.nautical adds ALOFT as vocabulary riding up; up stays the
    # canonical word the exit list speaks.
    game = (
        'summon.verbose_exits\nsummon.nautical\n'
        'game\n    title "D"\n    start deck\n'
        'room deck\n    name "Deck"\n    desc "The deck."\n    up crow\n'
        'room crow\n    name "Crow"\n    desc "The nest."\n    down deck\n'
    )
    out = _run(["port"], game=game)
    assert "You can only go up from here." in out
