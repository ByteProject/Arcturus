# test_lower.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Lowering tests (B4.2): byte patterns for representative expressions and
control flow, and a numeric program that computes and runs on Frotz."""

import shutil
import subprocess

import pytest

from arcturus.assembler import Routine
from arcturus.codegen import _globals_map, generate
from arcturus.errors import ArcError
from arcturus.lower import Context, compile_block
from arcturus.parser import parse
from arcturus.sema import analyze


def lower_start(src):
    world = analyze(parse(src))
    handler = next(h for h in world.free_handlers if "start" in h.events)
    rt = Routine("m", nlocals=0)
    ctx = Context(world, _globals_map(world))
    ctx.prescan(handler.body)
    compile_block(rt, ctx, handler.body)
    rt.nlocals = ctx.nlocals()
    return rt, ctx


def test_let_arithmetic_bytes():
    rt, _ = lower_start("on start\n    let n = 1 + 2\n")
    # add (long form 0x14) of small constants 1 and 2, stored into local 1.
    assert bytes(rt.code) == bytes([0x14, 0x01, 0x02, 0x01])


def test_multiplication_uses_mul():
    rt, _ = lower_start("on start\n    let n = 4 * 5\n")
    assert bytes(rt.code) == bytes([0x16, 0x04, 0x05, 0x01])


def test_nlocals_counts_lets():
    _, ctx = lower_start("on start\n    let a = 0\n    let b = 0\n    let c = 0\n")
    assert ctx.nlocals() == 3


def test_change_to_local_stores():
    # change of a local compiles to a store into that local's slot.
    rt, _ = lower_start("on start\n    let n = 0\n    change n to 7\n")
    # let n = 0 -> store local1, 0 ; change n to 7 -> store local1, 7
    assert bytes(rt.code) == bytes([0x0D, 0x01, 0x00, 0x0D, 0x01, 0x07])


def test_while_emits_jump_and_branch():
    rt, _ = lower_start(
        "on start\n    let i = 0\n    while i < 3\n        change i to i + 1\n"
    )
    code = bytes(rt.code)
    assert 0x8C in code  # an unconditional jump (back to the loop top)


def test_object_access_deferred_to_b43():
    # A property read is not lowerable yet.
    with pytest.raises(ArcError):
        lower_start('thing gem\n    value 3\non start\n    say gem.value\n')


# -- end to end on Frotz ---------------------------------------------------

CALC = (
    'game\n'
    '    title "Calc"\n'
    '    serial "260627"\n'
    '    start void\n'
    '\n'
    'on start\n'
    '    let n = 0\n'
    '    let i = 1\n'
    '    while i <= 5\n'
    '        change n to n + i\n'
    '        change i to i + 1\n'
    '    say "Sum is:"\n'
    '    say n\n'
    '    if n > 10\n'
    '        say "Big."\n'
    '    else\n'
    '        say "Small."\n'
    '\n'
    'room void\n'
    '    name "Void"\n'
)


def test_calc_compiles_valid_z5():
    data = generate(analyze(parse(CALC)))
    assert data[0x00] == 5
    assert ((data[0x1C] << 8) | data[0x1D]) == sum(data[0x40:]) & 0xFFFF


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_calc_runs_on_frotz(tmp_path):
    story = tmp_path / "calc.z5"
    story.write_bytes(generate(analyze(parse(CALC))))
    result = subprocess.run(
        [_frotz(), "-p", str(story)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
    )
    out = result.stdout
    assert "15" in out  # 1+2+3+4+5
    assert "Big." in out  # 15 > 10
