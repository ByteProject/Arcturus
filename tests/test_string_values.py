# test_string_values.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A plain string literal is a value (auraes's ruby, 2026-09-10; docs/01
chapter 10): a block returns one, a `let` holds one, a call passes one,
and `${my_block()}` speaks the returned text through the string
threshold (a number-returning path still speaks digits). Identical
literals share one pooled address, so `is` compares them true. The two
machine limits hold: interpolated text is not a value (clear error),
and a parameter is untyped (documented, not tested here)."""

import pytest

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.lower import LowerError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "S"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'global gem_examined = false\n'
    'block engraving()\n'
    '    if gem_examined\n'
    '        return "a warning in an older tongue"\n'
    '    return "something"\n'
    'block mixed()\n'
    '    if gem_examined\n'
    '        return "text now"\n'
    '    return 7\n'
    'block pick(label)\n'
    '    if label is "KEEPSAKE"\n'
    '        say "It is the keepsake."\n'
    'thing ruby in hall\n    name "ruby"\n    words ruby\n'
    '    desc block\n'
    '        say "There is ${engraving()} engraved on the ruby."\n'
    '        change gem_examined to true\n'
    'verb "ponder"\n    ponder\n'
    'on ponder\n'
    '    let s = "a riddle"\n'
    '    if s is "a riddle"\n'
    '        say "It is ${s}."\n'
    '    pick("KEEPSAKE")\n'
    '    say "Mixed: ${mixed()}."\n'
)


def _run(cmds, game=GAME):
    io = CaptureIO(script=list(cmds) + ["quit", "y"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(game))))),
           io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_a_returned_string_speaks_inside_the_sentence():
    out = _run(["x ruby", "x ruby"])
    assert "There is something engraved on the ruby." in out
    assert "There is a warning in an older tongue engraved on the ruby." in out


def test_let_argument_and_identity_comparison():
    out = _run(["ponder"])
    # The let speaks as text, the identical literal compares true, and the
    # string argument reaches the block and matches there.
    assert "It is a riddle." in out
    assert "It is the keepsake." in out


def test_a_mixed_block_speaks_numbers_as_digits():
    # The threshold discrimination: the same call site speaks a returned
    # number as digits and a returned string as text.
    out = _run(["ponder", "x ruby", "ponder"])
    assert "Mixed: 7." in out
    assert "Mixed: text now." in out


def test_interpolated_text_is_not_a_value():
    src = (
        'game\n    title "E"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'block bad()\n'
        '    return "the ${noun} form"\n'
    )
    with pytest.raises((ArcError, LowerError)) as err:
        generate(analyze(cosmos.combined_program(parse(src))))
    assert "not a value" in str(err.value)
