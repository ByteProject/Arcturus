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
    assert "You don't have the right key." in out
    assert "brass key" not in out.split("unlock gate")[1]
    assert "locked" in out  # the open still refused


def test_bare_unlock_with_the_key_in_hand_works():
    out = _run(["take key", "unlock gate", "open gate"])
    assert "You don't have the right key." not in out
    assert "Unlocked." in out
    assert "Open." in out


def test_named_key_must_be_held_too():
    # "unlock gate with key" while the key lies on the floor.
    out = _run(["unlock gate with key"])
    assert "You don't have the right key." in out


def test_open_with_key_must_be_held_too():
    out = _run(["open gate with key"])
    assert "You don't have the right key." in out


def test_bare_lock_needs_the_key_too():
    out = _run(["take key", "unlock gate", "drop key", "lock gate"])
    assert "You don't have the right key." in out


def test_keyless_bolt_stays_bare_handed():
    # lockable with no unseal_with: locking and unlocking by hand.
    out = _run(["unlock bolt", "lock bolt"])
    assert "You don't have the right key." not in out
