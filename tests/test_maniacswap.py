# test_maniacswap.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""maniacswap (summon.maniacswap, Stefan's design round 2026-08-18).

Multiple player characters: `playable` marks a body, BECOME swaps from
anywhere (disconnected maps included, through the reach), the left body
freezes in place holding its own inventory, and the standard self words
follow the keyboard (the SELF pronoun, role 7). The story gates swaps in
fiction with an ordinary `on become` handler; the shared `hibernated`
vocabulary means a summoned NPC engine never drives a frozen PC nor the
body being ridden."""

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


def _run(story, cmds, tail=("quit", "y")):
    io = CaptureIO(script=list(cmds) + list(tail))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except SystemExit:
        pass
    return io.text


HEAD = (
    'game\n    title "M"\n    start lab\n'
    'summon.maniacswap\n'
    'player.name "Werner"\n'
    'player.named\n'
    'player.desc "Werner, chief of the station."\n'
    'player.words werner\n'
    'room lab\n    name "Lab"\n    desc "The lab."\n'
    'room dock\n    name "Dock"\n    desc "The dock."\n'
    'thing olivia of character in dock\n'
    '    name "Olivia"\n    named\n    feminine\n    words olivia\n'
    '    playable\n'
    '    desc "Olivia, chief engineer."\n'
    'thing wrench in olivia\n'
    '    name "wrench"\n    words wrench\n    desc "A pipe wrench."\n'
)


def test_become_swaps_across_disconnected_maps():
    out = _run(_build(HEAD), ["become olivia", "x me", "i"])
    assert "You are now Olivia." in out
    assert "The dock." in out          # arrival describes her room
    assert "Olivia, chief engineer." in out  # ME follows the keyboard
    assert "a wrench" in out           # her inventory, not Werner's


def test_self_words_follow_and_bodies_stay_nameable():
    src = HEAD.replace('room lab\n    name "Lab"\n    desc "The lab."\n',
                       'room lab\n    name "Lab"\n    desc "The lab."\n'
                       '    east dock\n')
    src = src.replace('room dock\n    name "Dock"\n    desc "The dock."\n',
                      'room dock\n    name "Dock"\n    desc "The dock."\n'
                      '    west lab\n')
    out = _run(_build(src), ["become olivia", "west", "x werner",
                             "become werner", "x olivia"])
    # the abandoned boot body is listed and examinable in third person
    assert "You can see Werner here." in out
    assert "Werner, chief of the station." in out
    # and swapping back in the same room relists Olivia at once
    assert "You are now Werner." in out
    assert "Olivia, chief engineer." in out


def test_not_playable_and_already_self_refuse():
    src = HEAD + (
        'thing guard of character in lab\n'
        '    name "guard"\n    words guard\n    desc "A guard."\n'
    )
    out = _run(_build(src), ["become guard", "become werner"])
    assert "You can't be the guard." in out
    assert "You already are." in out


def test_the_story_gates_the_swap():
    src = HEAD + (
        'flag intercom_up = false\n'
        'on become when noun is olivia\n'
        '    if intercom_up is false\n'
        '        change refused to 1\n'
        '        say "You cannot reach her over the intercom."\n'
        '        stop\n'
        '    continue\n'
        'verb "repair"\n    repair\n'
        'on repair\n    change intercom_up to true\n    say "Fixed."\n'
    )
    out = _run(_build(src), ["become olivia", "repair", "become olivia", "x me"])
    assert "You cannot reach her over the intercom." in out
    assert "You are now Olivia." in out
    assert "Olivia, chief engineer." in out


def test_left_body_freezes_under_the_npc_engine():
    src = (
        'game\n    title "MB"\n    start yard\n'
        'summon.maniacswap\n'
        'summon.npcengine\n'
        'player.name "Werner"\n'
        'player.named\n'
        'player.words werner\n'
        'room yard\n    name "Yard"\n    desc "A yard."\n    north gate\n'
        'room gate\n    name "Gatehouse"\n    desc "The gatehouse."\n'
        '    south yard\n'
        'thing rounds_man of character in yard\n'
        '    name "watchman"\n    words watchman\n    desc "On his rounds."\n'
        '    playable\n'
        '    patrol yard, gate\n'
        'on start\n    resume(rounds_man)\n'
    )
    story = _build(src)
    # riding the watchman pauses his patrol; leaving him keeps him frozen
    # exactly where he was left (the gatehouse)
    out = _run(story, ["z", "become watchman", "z", "z",
                       "become werner", "z", "z", "north", "look"])
    after = out.split("You are now the watchman.")[1]
    assert "heads" not in after and "arrives" not in after
    assert "You can see a watchman here." in after


def test_playable_needs_a_character():
    src = HEAD + (
        'thing crate in lab\n    name "crate"\n    words crate\n    playable\n'
    )
    with pytest.raises(ArcError, match="of character"):
        _build(src)


def test_unsummoned_playable_stays_an_ordinary_property():
    src = HEAD.replace("summon.maniacswap\n", "")
    out = _run(_build(src), ["become olivia", "x me"])
    # no BECOME verb without the summon; the self words stay the library's
    assert "You are now" not in out
    assert "Werner, chief of the station." in out


def test_german_swap_speaks_natively():
    src = (
        'game\n    title "D"\n    start labor\n'
        'summon.language "german"\n'
        'summon.maniacswap\n'
        'player.name "Werner"\n'
        'player.named\n'
        'player.words werner\n'
        'room labor\n    name "Labor"\n    desc "Das Labor."\n'
        'room dock\n    name "Dock"\n    desc "Das Dock."\n'
        'thing olivia of character in dock\n'
        '    name "Olivia"\n    named\n    feminine\n    words olivia\n'
        '    playable\n'
        '    desc "Olivia, die Chefingenieurin."\n'
    )
    out = _run(_build(src), ["werde olivia", "untersuche mich"],
               tail=("ende", "j"))
    assert "Du bist jetzt Olivia." in out
    assert "Olivia, die Chefingenieurin." in out


def test_spanish_swap_speaks_natively():
    src = (
        'game\n    title "E"\n    start sala\n'
        'summon.language "spanish"\n'
        'summon.maniacswap\n'
        'player.name "Werner"\n'
        'player.named\n'
        'player.words werner\n'
        'room sala\n    name "Sala"\n    desc "La sala."\n'
        'room muelle\n    name "Muelle"\n    desc "El muelle."\n'
        'thing olivia of character in muelle\n'
        '    name "Olivia"\n    named\n    feminine\n    words olivia\n'
        '    playable\n'
        '    desc "Olivia, la ingeniera jefa."\n'
    )
    out = _run(_build(src), ["encarna olivia", "examinate"],
               tail=("fin", "s"))
    assert "Ahora eres Olivia." in out
    assert "Olivia, la ingeniera jefa." in out


# --- body: the boot body has a name (docs/01 chapter 22) ------------------

DEMON = (
    'summon.maniacswap\n'
    'game\n    title "P"\n    start cellar\n    body demon\n'
    'room cellar\n    name "Cellar"\n    desc "Damp stone."\n    north kitchen\n'
    'room kitchen\n    name "Kitchen"\n    desc "Copper pans."\n    south cellar\n'
    'thing demon of character in cellar\n    name "the demon"\n    named\n'
    '    words demon\n    desc "A shape that is mostly appetite."\n'
    'thing jane of character in kitchen\n    name "Jane"\n    named\n    feminine\n'
    '    words jane\n    playable\n    desc "A cook."\n'
    '    on become\n        say "You pour yourself into Jane."\n'
    '        move demon to nothing\n        continue\n'
    'thing ladle in jane\n    name "ladle"\n    words ladle\n'
    'thing horn in player\n    name "horn"\n    words horn\n'
    'verb "leave"\n    vleave\n'
    'on vleave\n'
    '    if player is demon\n        say "You are already yourself."\n        stop\n'
    '    move demon to here\n    say "You slip out."\n    become(demon)\n'
    'on start\n    say "You wake in the dark, hungry."\n'
)


def test_body_names_the_boot_body():
    # The field thread (improvmonster and EdwardianDuck, 2026-09-28): once
    # you left the seeded player there was no name for it. With `body` the
    # boot body is an ordinary character: start in it by declaration (no
    # arrival before the intro), test it, lose it, return to it from code.
    out = _run(_build(DEMON), ["examine me", "inventory", "become jane",
                               "examine me", "inventory", "leave",
                               "examine me", "look"])
    head = out.split(">examine me")[0]
    assert head.index("You wake in the dark") < head.index("Cellar")   # intro first
    assert out.count("Cellar\nDamp stone.") == 1                     # no second arrival
    assert "A shape that is mostly appetite." in out.split(">examine me")[1]
    assert " a horn" in out.split(">inventory")[1]                    # `in player` = in the body
    assert "You pour yourself into Jane." in out
    assert "A cook." in out.split(">examine me")[2]                   # ME followed the keyboard
    assert " a ladle" in out.split(">inventory")[2]
    assert "You slip out." in out
    assert "A shape that is mostly appetite." in out.split(">examine me")[3]
    assert "You can see Jane here." in out.split(">look")[1]


def test_body_needs_the_granule_and_a_character():
    with pytest.raises(ArcError, match="maniacswap"):
        _build('game\n    title "P"\n    start r\n    body bob\n'
               'room r\n    name "R"\n    desc "x"\n'
               'thing bob of character in r\n    name "Bob"\n    words bob\n')
    with pytest.raises(ArcError, match="character"):
        _build('summon.maniacswap\ngame\n    title "P"\n    start r\n    body rock\n'
               'room r\n    name "R"\n    desc "x"\n'
               'thing rock in r\n    name "rock"\n    words rock\n')
    with pytest.raises(ArcError, match="player.<property>"):
        _build('summon.maniacswap\ngame\n    title "P"\n    start r\n    body bob\n'
               'player.name "Henrik"\n'
               'room r\n    name "R"\n    desc "x"\n'
               'thing bob of character in r\n    name "Bob"\n    words bob\n')
