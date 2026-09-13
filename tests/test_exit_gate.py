# test_exit_gate.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The lid gates the way OUT as it gates the way in (a field report,
2026-09-13: a player could exit a closed, even locked container, which
stayed closed behind them). Core rejects on every path (EXIT and the
walk's implicit exit); foresight opens on the promise discipline, and a
locked lid speaks the open's own refusal."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hold\n'
    'room hold\n    name "Cargo Hold"\n    desc "Crates."\n    north deck\n'
    'room deck\n    name "Deck"\n    desc "Open air."\n'
    'thing trunk of container in hold\n    name "steamer trunk"\n'
    '    words steamer, trunk\n    openable\n    open\n    lockable\n'
    '    unseal_with stamp\n'
    'thing stamp in player\n    name "brass stamp"\n    words brass, stamp\n'
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


def test_exit_refuses_a_shut_lid_on_both_paths():
    out = _run(["enter trunk", "close trunk", "exit", "north", "look",
                "open trunk", "exit"])
    # EXIT and the walk both refuse; the player is still in the trunk
    # (the look shows no room heading change), and opening frees them.
    assert out.count("The steamer trunk is shut.") == 2
    assert "Deck" not in out
    assert "You get out of the steamer trunk." in out


def test_foresight_opens_the_lid_and_locked_speaks_open():
    game = "summon.foresight\n" + GAME
    out = _run(["enter trunk", "close trunk", "exit",
                "enter trunk", "close trunk", "lock trunk", "exit"], game)
    assert "(opening the steamer trunk first)" in out
    assert out.count("You get out of the steamer trunk.") == 1
    # the locked lid earns exactly the open's refusal
    assert "The steamer trunk is locked." in out
    assert "is shut." not in out
