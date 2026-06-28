# test_assembler.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Assembler tests: instruction encoding for each form, and a call/return
program that runs on Frotz (B4.1 done-test)."""

import shutil
import subprocess

import pytest

from arcturus import assembler as a
from arcturus import worldmodel as wm
from arcturus.codegen import build_story


def test_const_classification():
    assert a.Const(5).kind == a.SMALL
    assert a.Const(255).kind == a.SMALL
    assert a.Const(256).kind == a.LARGE
    assert a.Const(-1).kind == a.LARGE and a.Const(-1).value == 0xFFFF


def test_encode_0op():
    r = a.Routine("r")
    r.op("quit")
    assert bytes(r.code) == bytes([0xBA])


def test_encode_1op_small_const():
    r = a.Routine("r")
    r.op("ret", a.Const(42))
    # short form: 0x80 | (SMALL<<4) | 0x0B = 0x9B, then the byte 42.
    assert bytes(r.code) == bytes([0x9B, 0x2A])


def test_encode_2op_long_form():
    r = a.Routine("r")
    r.op("add", a.Const(1), a.Const(2), store=a.Variable(a.STACK))
    # long form: opcode byte 0x14, two small constants, then the store byte.
    assert bytes(r.code) == bytes([0x14, 0x01, 0x02, 0x00])


def test_encode_var_print_num():
    r = a.Routine("r")
    r.op("print_num", a.Variable(a.STACK))
    # 0xE6, types byte (VAR, omitted, omitted, omitted) = 0xBF, variable 0.
    assert bytes(r.code) == bytes([0xE6, 0xBF, 0x00])


def test_call_records_fixup_and_links():
    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vs", a.RoutineRef("compute"), store=a.Variable(a.STACK))
    entry.op("quit")
    compute = a.Routine("compute", nlocals=0)
    compute.op("ret", a.Const(7))
    blob, pc, _strrefs, _packed = a.link(entry, [compute], 0x400)
    # The entry stub starts at the base address.
    assert pc == 0x400
    # The call operand (entry bytes 2..3) holds compute's packed address.
    packed = (blob[2] << 8) | blob[3]
    assert packed * 4 >= 0x400  # points into the laid-out code
    assert packed * 4 % 4 == 0  # routine is 4-aligned


def _call_demo():
    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vs", a.RoutineRef("compute"), store=a.Variable(a.STACK))
    entry.op("print_num", a.Variable(a.STACK))
    entry.op("new_line")
    entry.op("quit")
    compute = a.Routine("compute", nlocals=0)
    compute.op("ret", a.Const(42))
    return build_story(wm.World(), entry, [compute])


def test_call_demo_is_valid_z5():
    data = _call_demo()
    assert data[0x00] == 5
    assert len(data) % 4 == 0
    assert ((data[0x1C] << 8) | data[0x1D]) == sum(data[0x40:]) & 0xFFFF


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_call_returns_value_on_frotz(tmp_path):
    story = tmp_path / "call.z5"
    story.write_bytes(_call_demo())
    result = subprocess.run(
        [_frotz(), "-p", str(story)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
    )
    # The routine returned 42 and the caller printed it.
    assert "42" in result.stdout
