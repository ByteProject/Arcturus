# test_presence.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The two multi-room forms (docs/01 chapter 3, Stefan's ruling 2026-08-16,
from EdwardianDuck's field report):

- `in a, b` is the EXISTENCE form: one object, fully present in every
  listed room. The first room is its tree home; the describer presents it
  (appearance, intro, the combined sentence, its subtree) in each room,
  state is one, and the form requires `fixed`, rejects scenery, movables,
  and kinds, all loudly at compile time.
- Body `spans a, b` is the SIGHT form: referable from every listed room
  (or room kind), never presented there. Scenery's tool.

The containment test stays tree-truth by ruling: `if x in far_room` is
false, the author knows the declared rooms. Games using neither form stay
byte-identical (the size ceilings hold that line); a game using both pays
the 1-byte marker that keeps the walks apart."""

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
    'game\n    title "P"\n    start ledge\n'
    'room ledge\n    name "Ledge"\n    desc "A narrow ledge."\n    down gully\n'
    'room gully\n    name "Gully"\n    desc "A damp gully."\n    up ledge\n'
)

# EdwardianDuck's vine, verbatim in shape: a fixed existence object with an
# appearance, declared `in ledge, gully`.
VINE = HEAD + (
    'thing vine in ledge, gully\n'
    '    name "vine"\n    words vine\n    fixed\n'
    '    desc "A sturdy vine."\n'
    '    appearance "A vine hangs from ledge to gully."\n'
)


def test_existence_appearance_speaks_in_every_room():
    out = _run(_build(VINE), ["down", "look"])
    # the paragraph in the home room's opening description AND below
    assert out.count("A vine hangs from ledge to gully.") >= 3
    assert "You can see" not in out  # appearance replaces the listing line


def test_existence_object_examines_from_both_rooms():
    out = _run(_build(VINE), ["x vine", "down", "x vine"])
    assert out.count("A sturdy vine.") == 2


def test_plain_existence_object_joins_both_sentences():
    src = HEAD + 'thing anvil in ledge, gully\n    name "anvil"\n    words anvil\n    fixed\n'
    out = _run(_build(src), ["down"])
    assert out.count("You can see an anvil here.") == 2


def test_subtree_follows_and_state_is_one():
    src = HEAD + (
        'thing workbench of supporter in ledge, gully\n'
        '    name "workbench"\n    words workbench\n    fixed\n'
        'thing jar in workbench\n    name "jar"\n    words jar\n'
    )
    out = _run(_build(src), ["down", "take jar", "look", "up", "look"])
    # the far room shows the workbench with its jar, the jar is reachable
    # there, and once carried it is gone from BOTH rooms' sentences
    assert "You take the jar with you." in out
    head, _, tail = out.partition("You take the jar with you.")
    assert head.count("(on which is a jar)") == 2
    assert "(on which is a jar)" not in tail


def test_sight_form_is_referable_never_presented():
    src = HEAD + (
        'thing moon\n    name "moon"\n    words moon\n    scenery\n'
        '    spans ledge, gully\n    desc "Pale and patient."\n'
    )
    out = _run(_build(src), ["x moon", "down", "x moon", "look"])
    assert out.count("Pale and patient.") == 2
    assert "You can see" not in out


def test_both_forms_in_one_game_stay_apart():
    # the marker path: the anvil (existence) is listed in both rooms, the
    # moon (sight) in neither, and both answer EXAMINE from both rooms
    src = HEAD + (
        'thing anvil in ledge, gully\n    name "anvil"\n    words anvil\n    fixed\n'
        'thing moon\n    name "moon"\n    words moon\n    scenery\n'
        '    spans ledge, gully\n    desc "Pale and patient."\n'
    )
    out = _run(_build(src), ["x moon", "down", "x moon", "look"])
    assert out.count("You can see an anvil here.") >= 2
    assert "moon here" not in out
    assert out.count("Pale and patient.") == 2


def test_door_exists_on_both_sides():
    src = (
        'game\n    title "D"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "The hall."\n    east oak_door\n'
        'room vault\n    name "Vault"\n    desc "The vault."\n    west oak_door\n'
        'thing oak_door of door in hall, vault\n'
        '    name "oak door"\n    words door\n'
    )
    out = _run(_build(src), ["open door", "east", "look", "close door", "west"])
    # listed on both sides, and the state (open/closed) is one door's:
    # closed from the vault side, the walk back finds it shut
    assert out.count("You can see an oak door") >= 3
    assert "The oak door is shut." in out


def test_containment_stays_tree_truth():
    # Stefan's ruling: `in` answers the home room only; the author knows
    # the declared rooms and tests `here` directly.
    src = HEAD + (
        'thing vine in ledge, gully\n    name "vine"\n    words vine\n    fixed\n'
        'verb "probe"\n    probe\n'
        'on probe\n'
        '    if vine in ledge\n        say "Home yes."\n'
        '    if vine in gully\n        say "Far yes."\n'
        '    else\n        say "Far no."\n'
    )
    out = _run(_build(src), ["probe"])
    assert "Home yes." in out and "Far no." in out


# --- the compile gates, all loud ------------------------------------------

def _refuses(src, needle):
    with pytest.raises(ArcError) as e:
        _build(src)
    assert needle in str(e.value)


def test_movable_existence_is_a_compile_error():
    _refuses(HEAD + 'thing rock in ledge, gully\n    name "rock"\n    words rock\n',
             "movable")


def test_scenery_existence_is_a_compile_error():
    _refuses(HEAD + 'thing wall in ledge, gully\n    name "wall"\n    words wall\n    scenery\n',
             "uses `spans`")


def test_kind_target_existence_is_a_compile_error():
    _refuses(HEAD + 'kind outdoor of room\n'
                    'thing sun in ledge, outdoor\n    name "sun"\n    words sun\n    fixed\n',
             "takes named rooms")


def test_mixed_forms_are_a_compile_error():
    _refuses(HEAD + 'thing post in ledge, gully\n    name "post"\n    words post\n    fixed\n'
                    '    spans gully\n',
             "one or the other")


# --- the language layers' sentence tails ----------------------------------

GERMAN_HEAD = (
    'game\n    title "P"\n    start stube\n'
    'summon.language "german"\n'
    'room stube\n    name "Stube"\n    desc "Die Stube."\n    down keller\n'
    'room keller\n    name "Keller"\n    desc "Der Keller."\n    up stube\n'
)


def test_german_tail_speaks_the_far_side():
    src = GERMAN_HEAD + (
        'thing amboss in stube, keller\n'
        '    name "Amboss"\n    words amboss\n    fixed\n    der\n'
        'thing eimer in stube, keller\n'
        '    name "Eimer"\n    words eimer\n    fixed\n    der\n'
    )
    out = _run(_build(src), ["runter"], tail=("ende", "j"))
    # both rooms speak the combined sentence, accusative, with "und"
    assert out.count("Du siehst hier einen Amboss und einen Eimer.") == 2
