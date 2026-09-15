# test_intrinsics.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Intrinsic built-ins (B4.5b): the reserved functions that lower to opcodes -
read_line, peek/poke, the parse-buffer accessors, and call_handler."""

import shutil
import subprocess

import pytest

from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def compile_z5(src):
    return generate(analyze(parse(src)))


def test_all_intrinsics_compile():
    # Each intrinsic lowers without error (call_handler(0,0) is never run here).
    src = (
        'on start\n'
        '    let a = read_line()\n'
        '    let b = word_count()\n'
        '    let c = word_dict(0)\n'
        '    let d = word_len(0)\n'
        '    let e = word_pos(0)\n'
        '    let f = peek_byte(544)\n'
        '    let g = peek_word(544, 0)\n'
        '    poke_byte(544, 65)\n'
        '    poke_word(544, 1, 7)\n'
        '    let h = call_handler(0, 0)\n'
        'room r\n'
        '    name "r"\n'
    )
    assert compile_z5(src)[0x00] == 5


def test_scan_table_finds_and_misses():
    # scan_table(value, addr, count): the interpreter's table search
    # (auraes's ask, 2026-09-13). Poke three words into the text-buffer
    # scratch, then scan for a middle value (its address back, here as a
    # delta from the buffer base) and for an absent one (0).
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    src = (
        'on start\n'
        '    poke_word(544, 5, 111)\n'
        '    poke_word(544, 6, 222)\n'
        '    poke_word(544, 7, 333)\n'
        '    let hit = scan_table(222, 544 + 10, 3)\n'
        '    say "delta:"\n'
        '    say hit - 544\n'
        '    say "miss:"\n'
        '    say scan_table(999, 544 + 10, 3)\n'
        'room r\n'
        '    name "r"\n'
    )
    io = CaptureIO(script=[])
    try:
        VM(load(compile_z5(src)), io).run(max_steps=1_000_000)
    except IndexError:
        pass  # the script is exhausted at the first prompt
    assert "delta:" in io.text and "12" in io.text
    assert "miss:" in io.text and "0" in io.text


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


PEEK_POKE = (
    'on start\n'
    '    poke_word(544, 5, 1234)\n'  # write into the text buffer (scratch)
    '    say peek_word(544, 5)\n'
    'room r\n'
    '    name "r"\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_peek_poke_roundtrip_on_frotz(tmp_path):
    story = tmp_path / "pp.z5"
    story.write_bytes(compile_z5(PEEK_POKE))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "1234" in out


ECHO = (
    'verb "take", "get"\n'
    '    take noun\n'
    'thing lamp in cave\n'
    '    name "lamp"\n'
    '    words lamp, lantern, brass\n'
    'room cave\n'
    '    name "Cave"\n'
    'on start\n'
    '    let term = read_line()\n'
    '    let n = word_count()\n'
    '    let i = 0\n'
    '    let known = 0\n'
    '    while i < n\n'
    '        if word_dict(i) is not nothing\n'
    '            change known to known + 1\n'
    '        change i to i + 1\n'
    '    say "Known:"\n'
    '    say known\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_read_line_and_parse_buffer_on_frotz(tmp_path):
    story = tmp_path / "echo.z5"
    story.write_bytes(compile_z5(ECHO))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="take lamp lantern brass\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    # All four typed words are in the dictionary.
    assert "Known:" in out and "4" in out


def test_dict_entry_is_the_dictionary_address():
    # dict_entry("beacon"): the compile-time dictionary literal (the
    # Inform 'word' idiom, 2026-09-15); a plain string literal stays a
    # pooled STRING address, so only this form compares against
    # word_dict()'s answers.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    src = (
        'game\n    start plaza\n'
        'room plaza\n    name "Plaza"\n    desc "Broad."\n'
        'thing beacon in plaza\n    name "beacon"\n    words beacon, lamp\n'
        'verb "probe"\n    wprobe text\n'
        'on wprobe\n'
        '    if word_dict(1) is dict_entry("lamp")\n'
        '        say "THE LAMP WORD"\n'
        '    else\n'
        '        say "SOME OTHER WORD"\n'
    )
    from arcturus import cosmos
    io = CaptureIO(script=["probe lamp", "probe beacon"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=5_000_000)
    except IndexError:
        pass
    assert "THE LAMP WORD" in io.text
    assert "SOME OTHER WORD" in io.text


def test_dict_entry_unknown_is_a_compile_error():
    from arcturus import cosmos
    from arcturus.errors import ArcError
    src = (
        'game\n    start plaza\n'
        'room plaza\n    name "Plaza"\n    desc "x"\n'
        'on start\n    if word_dict(0) is dict_entry("xyzzyplugh")\n'
        '        say "never"\n'
    )
    with pytest.raises(ArcError, match="vocabulary"):
        generate(analyze(cosmos.combined_program(parse(src))))
