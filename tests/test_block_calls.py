# test_block_calls.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Block-call arity (Stefan's go of 2026-07-18): up to three arguments ride
the ordinary call's single types byte; four to seven ride the double-types
long call (call_vs2, the Z-machine's only irregular encoding); more than
seven is refused at compile time with the cure, since even the long call
fills at most seven locals. Found the hard way: before this, a four-argument
call compiled to garbage with no diagnostic."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(game, cmds):
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_four_and_seven_argument_calls():
    # The crossing case (four arguments, the first to need call_vs2) and the
    # ceiling case (seven), both computed and printed.
    game = (
        'game\n    title "T"\n    start hall\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        "    on probe_it\n"
        '        say "four: ${sum4(1, 2, 3, 4)}"\n'
        '        say "seven: ${sum7(1, 2, 3, 4, 5, 6, 7)}"\n'
        "block sum4(a, b, c, d)\n"
        "    return a + b + c + d\n"
        "block sum7(a, b, c, d, e, f, g)\n"
        "    return a + b + c + d + e + f + g\n"
    )
    out = _run(game, ["probe"])
    assert "four: 10" in out
    assert "seven: 28" in out


def test_eight_argument_call_is_refused():
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        "on start\n"
        '        say "${sum7(1, 2, 3, 4, 5, 6, 7, 8)}"\n'
        "block sum7(a, b, c, d, e, f, g)\n"
        "    return a\n"
    )
    with pytest.raises(ArcError) as e:
        generate(analyze(cosmos.combined_program(parse(game))))
    assert "at most 7 arguments" in str(e.value)


def test_eight_parameter_block_is_refused():
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        "block wide(a, b, c, d, e, f, g, h)\n"
        "    return a\n"
    )
    with pytest.raises(ArcError) as e:
        analyze(cosmos.combined_program(parse(game)))
    assert "at most 7" in str(e.value)
