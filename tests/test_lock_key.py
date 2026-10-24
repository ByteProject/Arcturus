# test_lock_key.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Locks demand their key IN HAND (a field report from a Dialog port: a
bare UNLOCK always unlocked, because the handler auto-supplied the lock's
own key without checking the player carried it; LOCK and OPEN-with-key
shared the hole). The auto-supply itself stays: a bare UNLOCK with the
key in hand works, a keyless bolt (`lockable` with no `unseal_with`)
still works bare-handed, and the refusal never names the key, so an
undiscovered lock keeps its secret."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south hall\n'
    'thing gate of door in hall, yard\n    name "oak gate"\n    words gate, oak\n'
    '    lockable\n    locked\n    unseal_with key\n'
    'thing key in hall\n    name "brass key"\n    words key, brass\n'
    'thing bolt in hall\n    name "iron bolt"\n    words bolt, iron\n'
    '    fixed\n    openable\n    lockable\n    locked\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_bare_unlock_needs_the_key_in_hand():
    # The reported bug: with the key lying on the floor, a bare UNLOCK
    # opened every lock. Now it refuses, without naming the key.
    out = _run(["unlock gate", "open gate"])
    assert "looking hopeful isn't helping" in out
    assert "brass key" not in out.split("unlock gate")[1]
    assert "locked" in out  # the open still refused


def test_bare_unlock_with_the_key_in_hand_works():
    out = _run(["take key", "unlock gate", "open gate"])
    assert "You don't have the right key." not in out
    assert "You unlock the oak gate with the brass key." in out
    assert "Open." in out


def test_named_key_must_be_held_too():
    # "unlock gate with key" while the key lies on the floor.
    out = _run(["unlock gate with key"])
    assert "looking hopeful isn't helping" in out


def test_open_with_key_must_be_held_too():
    out = _run(["open gate with key"])
    assert "looking hopeful isn't helping" in out


def test_bare_lock_needs_the_key_too():
    out = _run(["take key", "unlock gate", "drop key", "lock gate"])
    assert "looking hopeful isn't helping" in out


def test_keyless_bolt_stays_bare_handed():
    # lockable with no unseal_with: locking and unlocking by hand.
    out = _run(["unlock bolt", "lock bolt"])
    assert "You don't have the right key." not in out


def test_keyless_lock_cannot_be_unlocked_by_the_verb():
    # THE bug (Charles Moore Jr., "still there"): a lockable + locked thing
    # with no unseal_with unlocked bare-handed. It must refuse now: no
    # opener defined means no opener to hold. The story springs it itself.
    out = _run(["unlock bolt"])
    assert "looking hopeful isn't helping" in out   # refused, not "Unlocked."
    assert "Unlocked." not in out


def test_unlock_something_not_locked_opens_it():
    # Unlocking an already-unlocked lockable thing is a no-op, so it opens.
    out = _run(["take key", "unlock gate", "unlock gate"])
    assert "already unlocked, so you skip the suspense" in out
    assert "Open." in out.split("skip the suspense")[-1]


def test_crowbar_springs_a_keyless_lock():
    # The use case for keyless locks (Stefan): the story unlocks it itself,
    # e.g. a crowbar handler doing `now bolt is not locked`, after which the
    # bolt opens normally.
    game = GAME + (
        'verb "pry"\n    pry noun\n'
        'on pry\n    now bolt is not locked\n    say "The bolt gives with a screech."\n'
    )
    out = _run(["pry bolt", "open bolt"], game=game)
    assert "gives with a screech" in out
    assert "Open." in out.split("open bolt")[-1]   # now openable


ALTERED = GAME.replace(
    "    lockable\n    locked\n    unseal_with key\n",
    "    lockable\n    locked\n    unseal_with key\n"
    "    on unlock\n        alter block\n            show \"The gate gives\"\n"
    "            if second is nothing\n                show \" (bare)\"\n"
    "            say \".\"\n        continue\n"
    "    on open\n        alter \"The gate swings wide.\"\n        continue\n",
    1)


def test_a_bare_lock_or_unlock_names_the_key_it_reached_for():
    # auraes (2026-10-24): the player who typed no key learns which one
    # turned the lock, in the report itself; a typed key keeps the short line.
    out = _run(["take key", "unlock gate", "lock gate", "unlock gate with key"])
    assert "You unlock the oak gate with the brass key." in out.split(">unlock gate")[1]
    assert "You lock the oak gate with the brass key." in out.split(">lock gate")[1]
    assert "Unlocked." in out.split(">unlock gate with key")[1]


def test_second_stays_what_the_player_typed():
    # The library no longer rewrites `second`: an alter at report time
    # still sees `second is nothing` after a bare UNLOCK.
    out = _run(["take key", "unlock gate"], game=ALTERED)
    assert "The gate gives (bare)." in out


def test_open_with_key_runs_the_real_unlock_and_keeps_the_open_alter():
    # The thing's own `on unlock` and its alter answer for OPEN X WITH KEY,
    # and the open's alter lands on the open, not on the unlock line.
    out = _run(["take key", "open gate with key"], game=ALTERED)
    part = out.split(">open gate with key")[1]
    assert "The gate gives." in part
    assert "The gate swings wide." in part
    assert part.index("The gate gives.") < part.index("The gate swings wide.")
    assert "Unlocked." not in part and "Open." not in part


def test_the_key_line_in_german_and_spanish():
    de = (
        'summon.language "german"\n'
        'game\n    title "T"\n    start halle\n'
        'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
        'thing truhe of container in halle\n    name "Truhe"\n    words truhe\n'
        '    feminine\n    openable\n    fixed\n    lockable\n    locked\n    unseal_with schluessel\n'
        'thing schluessel in player\n    name "Messingschlüssel"\n    words schlüssel\n'
    )
    assert "Du schließt die Truhe mit dem Messingschlüssel auf." in _run(["entriegele truhe"], game=de)
    es = (
        'summon.language "spanish"\n'
        'game\n    title "T"\n    start sala\n'
        'room sala\n    name "Sala"\n    desc "Una sala."\n'
        'thing cofre of container in sala\n    name "cofre"\n    words cofre\n'
        '    openable\n    fixed\n    lockable\n    locked\n    unseal_with llave\n'
        'thing llave in player\n    name "llave de latón"\n    words llave\n    feminine\n'
    )
    assert "Abres el cofre con la llave de latón." in _run(["destranca cofre"], game=es)
