# test_locals_limit.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A Z-machine routine holds at most 15 locals (parameters included). A
block that declares more used to compile into an illegal routine header
and crash the interpreter mid-game ("call to non-routine"); now it is a
compile error that names the count and the cure. Found the hard way when
try_line, already at the ceiling, briefly gained a sixteenth local."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze


def _compile(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_sixteen_locals_is_a_compile_error():
    lets = "\n".join(f"    let v{i} = {i}" for i in range(16))
    src = (
        'game\n    title "T"\n    start r\n'
        'room r\n    name "R"\n    desc "d"\n'
        f"block crowded()\n{lets}\n    return v0\n"
        "on start\n    let x = crowded\n"
    )
    with pytest.raises(ArcError, match="at most 15"):
        _compile(src)


def test_fifteen_locals_still_compiles():
    lets = "\n".join(f"    let v{i} = {i}" for i in range(15))
    src = (
        'game\n    title "T"\n    start r\n'
        'room r\n    name "R"\n    desc "d"\n'
        f"block crowded()\n{lets}\n    return v0\n"
        "on start\n    let x = crowded\n"
    )
    assert _compile(src)
