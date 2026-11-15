# test_item_count_holders.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`x.item_count` reads any holder, not only a container (improvmonster's
question, 2026-11-09): a supporter, a character, and the player count
what they hold, nested contents included, the same walk the carry limit
and item_cap use (docs/01 chapter 6)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start kitchen\n'
    'room kitchen\n    name "Kitchen"\n    desc "Tiles."\n'
    'thing table of supporter in kitchen\n    name "table"\n    words table\n    fixed\n'
    'thing tray of supporter in kitchen\n    name "tray"\n    words tray\n'
    'thing bowl of container in kitchen\n    name "bowl"\n    words bowl\n    open\n'
    'thing cup in kitchen\n    name "cup"\n    words cup\n'
    'thing pea in kitchen\n    name "pea"\n    words pea\n'
    'thing cook of character in kitchen\n    name "cook"\n    words cook\n'
    'thing spoon in cook\n    name "spoon"\n    words spoon\n'
    'thing ladle in cook\n    name "ladle"\n    words ladle\n'
    'verb "count"\n    count\n'
    'on count\n'
    '    say "Table ${table.item_count}, tray ${tray.item_count}, '
    'bowl ${bowl.item_count}, cook ${cook.item_count}, '
    'me ${player.item_count}."\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_supporters_count_what_is_on_them_all_the_way_down():
    out = _run(["count", "put pea in bowl", "put bowl on tray",
                "put cup on table", "put tray on table", "count"])
    assert "Table 0, tray 0, bowl 0, cook 2, me 0." in out
    # table: cup, tray, bowl on the tray, pea in the bowl
    assert "Table 4, tray 2, bowl 1, cook 2, me 0." in out


def test_the_player_counts_what_they_carry():
    out = _run(["take tray", "put cup on tray", "take pea", "count"])
    # tray, cup on the carried tray, pea
    assert "me 3." in out
