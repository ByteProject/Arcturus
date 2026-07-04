# test_decode.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M2: the instruction decoder, one hand-built byte sequence per
encoding feature, then the disassembler over whole real stories (the
Arcturus-built probes and, when present, the conformance directory's)."""

import os

import pytest

from actaea.decode import (
    LARGE, SMALL, VARIABLE, DecodeError, decode, disassemble,
    format_instruction, walk_story,
)
from actaea.loader import load
from actaea.memory import Memory

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

CONFORMANCE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "actaea", "conformance"
)


def _mem(code: bytes, scale: int = 4) -> Memory:
    """A synthetic memory: a fake header (static base past everything, so
    reads work anywhere) followed by the code under test at 0x40."""
    img = bytearray(0x40) + bytearray(code)
    img[0x00] = 5
    img[0x0E] = (len(img) >> 8) & 0xFF  # static base = end of image
    img[0x0F] = len(img) & 0xFF
    return Memory(bytes(img), scale)


CODE = 0x40  # where _mem places the first instruction


def test_long_form_two_small_constants():
    # long 2OP je: opcode 1, both operands small constants. The branch byte
    # 0xC0 = on true (bit 7) + short form (bit 6) + offset 0 = rfalse.
    ins = decode(_mem(bytes([0x01, 7, 9, 0xC0])), CODE)
    assert (ins.form, ins.count, ins.name) == ("long", "2OP", "je")
    assert ins.operands == [(SMALL, 7), (SMALL, 9)]
    assert ins.branch == (True, 0)


def test_long_form_variable_operands():
    # add L00, G00 -> sp: long form with both type bits set stores.
    ins = decode(_mem(bytes([0x14 | 0x40 | 0x20, 1, 16, 0])), CODE)
    assert ins.name == "add"
    assert ins.operands == [(VARIABLE, 1), (VARIABLE, 16)]
    assert ins.store == 0


def test_short_form_1op_and_0op():
    # jz sp ?~rtrue: short form, one variable operand, branch on false.
    ins = decode(_mem(bytes([0x80 | 0x20 | 0x00, 0, 0x41])), CODE)
    assert (ins.form, ins.count, ins.name) == ("short", "1OP", "jz")
    assert ins.operands == [(VARIABLE, 0)]
    assert ins.branch == (False, 1)
    # rtrue: short form type 11 = 0OP.
    ins = decode(_mem(bytes([0xB0])), CODE)
    assert (ins.count, ins.name) == ("0OP", "rtrue")
    assert ins.next == CODE + 1


def test_variable_form_var_count():
    # call_vs 0x1234, 5, sp -> L02: VAR form, types large/small/variable.
    code = bytes([0xE0, 0b00_01_10_11, 0x12, 0x34, 5, 0, 3])
    ins = decode(_mem(code), CODE)
    assert (ins.form, ins.count, ins.name) == ("var", "VAR", "call_vs")
    assert ins.operands == [(LARGE, 0x1234), (SMALL, 5), (VARIABLE, 0)]
    assert ins.store == 3
    assert ins.next == CODE + len(code)


def test_variable_form_2op_count():
    # je in variable form (three operands: the multi-way equality test).
    code = bytes([0xC1, 0b01_01_01_11, 1, 2, 3, 0xC0])
    ins = decode(_mem(code), CODE)
    assert (ins.count, ins.name) == ("2OP", "je")
    assert ins.operands == [(SMALL, 1), (SMALL, 2), (SMALL, 3)]
    assert ins.branch == (True, 0)


def test_double_type_byte_call():
    # call_vs2 with 7 arguments takes two type bytes.
    code = bytes(
        [0xEC, 0b00_01_01_01, 0b01_01_01_11, 0x10, 0x00, 1, 2, 3, 4, 5, 6, 0]
    )
    ins = decode(_mem(code), CODE)
    assert ins.name == "call_vs2"
    assert len(ins.operands) == 7
    assert ins.operands[0] == (LARGE, 0x1000)
    assert ins.store == 0


def test_extended_form():
    # save_undo -> sp: 0xBE, EXT opcode 9, no operands, stores.
    ins = decode(_mem(bytes([0xBE, 0x09, 0xFF, 0])), CODE)
    assert (ins.form, ins.count, ins.name) == ("ext", "EXT", "save_undo")
    assert ins.operands == []
    assert ins.store == 0
    # art_shift 200, -3 -> L00 (large constants carry 16-bit values).
    code = bytes([0xBE, 0x03, 0b00_00_11_11, 0x00, 0xC8, 0xFF, 0xFD, 1])
    ins = decode(_mem(code), CODE)
    assert ins.name == "art_shift"
    assert ins.operands == [(LARGE, 200), (LARGE, 0xFFFD)]


def test_long_branch_negative_offset():
    # je 1, 2 with a two-byte branch offset of -20 (signed 14-bit).
    raw = (-20) & 0x3FFF
    code = bytes([0x01, 1, 2, 0x80 | (raw >> 8), raw & 0xFF])
    ins = decode(_mem(code), CODE)
    on_true, off = ins.branch
    assert on_true and off == -20


def test_inline_text_span():
    # print carries its Z-string inline: two words, the second ends it.
    code = bytes([0xB2, 0x11, 0x11, 0x91, 0x11, 0xB0])
    ins = decode(_mem(code), CODE)
    assert ins.name == "print"
    assert ins.text == bytes([0x11, 0x11, 0x91, 0x11])
    assert ins.next == CODE + 5
    assert "2 words" in format_instruction(ins)


def test_illegal_opcodes_name_the_address():
    # 0OP:5 (the old v4 save) is illegal in v5.
    with pytest.raises(DecodeError) as e:
        decode(_mem(bytes([0xB5])), CODE)
    assert "0OP:5" in str(e.value) and "0x" in str(e.value)


GAME = (
    'game\n    title "Decode Probe"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A hall."\n'
    'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
    "    on take\n"
    '        say "Chime."\n'
)


def _story(version=5):
    return load(generate(analyze(cosmos.combined_program(parse(GAME))), version=version))


def test_walks_an_arcturus_story():
    story = _story(5)
    routines = walk_story(story.memory, story.header.initial_pc)
    # The whole Cosmos runtime is statically reachable from the entry: the
    # loop, the parser, dispatch, the verb defaults. Hundreds of routines.
    assert len(routines) > 150
    total = sum(len(r.instructions) for r in routines.values())
    assert total > 2000


def test_walks_the_z8_build_too():
    story = _story(8)
    routines = walk_story(story.memory, story.header.initial_pc)
    assert len(routines) > 150


def test_disassembly_is_printable():
    out = disassemble(_story(5))
    assert "entry point" in out
    assert "locals):" in out
    # Spot-check the formatting conventions.
    assert " -> " in out and "?" in out and "sp" in out


@pytest.mark.skipif(
    not os.path.exists(os.path.join(CONFORMANCE, "czech.z5")),
    reason="conformance stories not present (kept out of the public repo)",
)
def test_walks_czech():
    from actaea.loader import load_file

    story = load_file(os.path.join(CONFORMANCE, "czech.z5"))
    routines = walk_story(story.memory, story.header.initial_pc)
    assert len(routines) > 20


@pytest.mark.skipif(
    not os.path.exists(os.path.join(CONFORMANCE, "praxix.z5")),
    reason="conformance stories not present (kept out of the public repo)",
)
def test_walks_praxix():
    from actaea.loader import load_file

    story = load_file(os.path.join(CONFORMANCE, "praxix.z5"))
    routines = walk_story(story.memory, story.header.initial_pc)
    assert len(routines) > 20
