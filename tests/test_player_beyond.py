# test_player_beyond.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The beyond property points both ways (docs/01, beyond): `now player is
beyond` puts the PLAYER out of everything's reach, the mounted-on-a-horse
case (a field request; needs scope surgery in Dialog, does not exist in
Inform). While the player is beyond, only the arm's bubble stays touchable:
themself, what they hold, and the thing they are on or in with everything it
carries. Sight and speech cross the gap, exactly as object-beyond already
rules. The refusal speaks player.beyond_why when the story set one (a
runtime-settable text whose slot sema allocates invisibly); nothing reverts
to the pack default. The mount pattern is the after phase: `on after enter
mare / now player is beyond`."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

# A fresh invented scene: a paddock, a mare (supporter), a saddlebag riding
# her with an apple in it, a key on the ground.
GAME = (
    'game\n    title "M"\n    start paddock\n'
    'room paddock\n    name "Paddock"\n    desc "A sunlit paddock."\n'
    'thing mare of supporter in paddock\n    name "grey mare"\n'
    '    words mare, grey, horse\n'
    'thing key in paddock\n    name "iron key"\n    words key, iron\n'
    'thing saddlebag of container in mare\n    name "saddlebag"\n'
    '    words saddlebag, bag\n    open\n'
    'thing apple in saddlebag\n    name "red apple"\n    words apple\n'
    'on after enter mare\n    now player is beyond\n'
    'on after exit mare\n    now player is not beyond\n'
)


def _run(src, cmds):
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_mounted_player_cannot_reach_the_ground():
    out = _run(GAME, ["enter mare", "take key"]).split(">take")[-1]
    assert "The iron key is beyond your reach." in out
    assert "Got it." not in out


def test_sight_crosses_the_gap():
    out = _run(GAME, ["enter mare", "examine key"]).split(">examine")[-1]
    assert "beyond your reach" not in out  # examine is never guarded


def test_the_bubble_holds_mount_and_its_cargo():
    # The mare, the saddlebag riding her, and the apple inside it are all
    # within arm's reach; held things stay held.
    out = _run(GAME, ["take key", "enter mare", "touch mare", "take apple",
                      "put key in saddlebag"])
    assert "You touch the grey mare" in out
    tail = out.split(">take apple")[-1]
    assert "Got it." in tail
    assert "Done." in out.split(">put")[-1]


def test_put_cannot_fish_the_ground():
    # PUT moves its noun without a hold check, so the noun guard must cover
    # it: no lifting things off the ground into the saddlebag while mounted.
    out = _run(GAME, ["enter mare", "put key in saddlebag"]).split(">put")[-1]
    assert "beyond your reach" in out
    assert "Done." not in out


def test_dismount_restores_reach():
    out = _run(GAME, ["enter mare", "exit", "take key"]).split(">take")[-1]
    assert "Got it." in out


def test_player_beyond_why_wins_and_nothing_reverts():
    src = GAME.replace(
        'on after enter mare\n    now player is beyond\n',
        'on after enter mare\n    now player is beyond\n'
        '    change player.beyond_why to "You can\'t reach that from up here."\n',
    ).replace(
        'on after exit mare\n    now player is not beyond\n',
        'on after exit mare\n    now player is not beyond\n'
        '    change player.beyond_why to nothing\n'
        'verb "vault"\n    vault\n'
        'on vault\n'
        '    now player is beyond\n'
        '    say "You spring onto the fence rail."\n',
    )
    out = _run(src, ["enter mare", "take key", "exit", "vault", "take key"])
    # Mounted: the custom line (the slot was allocated by the change).
    assert "You can't reach that from up here." in out
    # Vaulted (beyond again, why reverted to nothing): the pack default.
    assert "The iron key is beyond your reach." in out


def test_unnested_beyond_is_hands_bound():
    # A beyond player nested in nothing can touch only themself and what they
    # hold: tied to a chair, hands bound, for free.
    src = GAME + (
        'verb "surrender"\n    surrender\n'
        'on surrender\n    now player is beyond\n    say "Bound."\n'
    )
    out = _run(src, ["take apple", "surrender", "take key", "drop apple"])
    tail = out.split(">take key")[-1]
    assert "beyond your reach" in tail          # the ground is gone
    assert "Down it goes." in out.split(">drop")[-1] or "Dropped" in out.split(">drop")[-1]


def test_runtime_only_beyond_still_compiles_the_guards():
    # No object anywhere declares beyond; the game only ever sets it at
    # runtime. The any_beyond fold must still keep the guards (the sema
    # sets_beyond scan), or the bit would flip silently with no effect.
    out = _run(GAME, ["enter mare", "take key"]).split(">take")[-1]
    assert "beyond your reach" in out
