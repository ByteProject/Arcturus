# test_as_player_matrix.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Every form an `as player` handler header can take (docs/01 chapter 22,
maniacswap), against every situation a body meets: a specific verb, the
`other` catch-all, `on after` for a verb and for other, an operand
pattern, several verbs, a `when` guard, a direction, a kind's handlers;
on the boot body, after BECOME and back, through perform, in a chained
line and in a noun list. The game is tests/data/as_player_matrix.storyarc;
each handler prints a bracketed marker. Built after improvmonster's
reports (2026-10-24) so no combination ships untested again."""

import os

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = os.path.join(os.path.dirname(__file__), "data", "as_player_matrix.storyarc")

COMMANDS = ["jump", "take lamp", "take key", "wave", "clap", "smell", "north",
            "south", "probe", "jump and wave", "drop lamp and key",
            "become greta", "sing", "jump", "take lamp", "north",
            "become henrik", "jump"]


def _turns():
    with open(GAME, encoding="utf-8") as fh:
        story = generate(analyze(cosmos.combined_program(parse(fh.read()))))
    io = CaptureIO(script=COMMANDS)
    try:
        VM(load(story), io).run(max_steps=40_000_000)
    except IndexError:
        pass
    text = io.text
    out = {}
    pos = text.index(">jump")
    for i, cmd in enumerate(COMMANDS):
        start = text.index(">" + cmd, pos)
        end = text.find(">", start + 1)
        out[i] = text[start:end if end != -1 else len(text)]
        pos = start + 1
    return out


T = _turns()


def test_specific_and_after_on_the_boot_body():
    assert "[H-JUMP]" in T[0] and "[H-AFTER-JUMP]" in T[0]


def test_operand_pattern_and_after_for_every_take():
    assert "[H-TAKE-LAMP]" in T[1] and "[H-AFTER-TAKE]" in T[1]
    assert "[H-TAKE-LAMP]" not in T[2] and "[H-AFTER-TAKE]" in T[2]


def test_several_verbs_in_one_header():
    assert "[H-WAVE-CLAP]" in T[3] and "[H-WAVE-CLAP]" in T[4]


def test_when_guard():
    assert "[H-SMELL-WHEN]" in T[5]


def test_direction_pattern_and_after_go():
    assert "[H-GO-NORTH]" in T[6] and "[H-AFTER-GO]" in T[6]
    assert "[H-GO-NORTH]" not in T[7] and "[H-AFTER-GO]" in T[7]


def test_performed_and_chained_actions():
    assert "[H-JUMP]" in T[8] and "[H-AFTER-JUMP]" in T[8]
    assert "[H-JUMP]" in T[9] and "[H-WAVE-CLAP]" in T[9]


def test_the_swap_is_not_the_new_bodys_action():
    assert "[K-" not in T[11]


def test_a_kinds_specific_other_and_after_handlers():
    assert "[K-SING]" in T[12] and "[K-AFTER-SING]" in T[12]
    assert "[K-OTHER]" in T[13] and "[K-AFTER-OTHER]" in T[13]
    assert "[H-" not in T[13]                     # Henrik's handlers left with him
    assert "[K-OTHER]" in T[14] and "[K-AFTER-OTHER]" in T[14]
    assert "[K-OTHER]" in T[15] and "[K-AFTER-OTHER]" in T[15]


def test_back_to_the_first_body():
    assert "[K-" not in T[16]
    assert "[H-JUMP]" in T[17] and "[K-" not in T[17]


def test_no_after_pass_follows_you_cant_do_that():
    src = (
        'game\n    title "R"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'verb "wave"\n    wave\n'
        'on after wave\n    say "[AFTER-WAVE]"\n'
    )
    io = CaptureIO(script=["wave"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "[AFTER-WAVE]" not in io.text
