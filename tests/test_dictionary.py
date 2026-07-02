# test_dictionary.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Dictionary tests (B4.4): vocabulary collection, the sorted 6-byte entries,
and an aread/tokenize echo program that recognizes words on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import assembler as a
from arcturus import dictionary, zstring
from arcturus import worldmodel as wm
from arcturus.codegen import (
    PARSE_BUFFER_ADDR,
    TEXT_BUFFER_ADDR,
    build_story,
)
from arcturus.parser import parse
from arcturus.sema import analyze

SRC = (
    'verb "take", "get"\n'
    '    take noun\n'
    'thing lamp in cave\n'
    '    name "lamp"\n'
    '    words brass, lamp, lantern\n'
    'room cave\n'
    '    name "Cave"\n'
)


def world():
    return analyze(parse(SRC))


def test_vocabulary_collected():
    assert dictionary.collect_vocab(world()) == {
        "take", "get", "brass", "lamp", "lantern",
    }


def test_entries_are_sorted_six_byte_words():
    data, offsets = dictionary.build(world())
    nsep = data[0]
    entry_len = data[1 + nsep]
    count = (data[2 + nsep] << 8) | data[3 + nsep]
    assert entry_len == 9  # 6 text + 3 data
    # take, get, brass, lamp, lantern. No particle words: those are declared in the
    # language layer (`particle on "on"`), and this bare program has no Cosmos.
    assert count == 5
    base = 4 + nsep
    # The 6-byte text of consecutive entries is strictly ascending (sorted).
    prev = None
    for i in range(count):
        text = bytes(data[base + i * entry_len : base + i * entry_len + 6])
        if prev is not None:
            assert text > prev
        prev = text
    # 'lamp' resolves to its encoded entry.
    assert data[offsets["lamp"] : offsets["lamp"] + 6] == zstring.encode_dict_word("lamp")


def test_verb_words_carry_their_action():
    from arcturus.codegen import _action_numbers

    w = world()
    actions = _action_numbers(w)
    data, off = dictionary.build(w, actions)
    # 'take'/'get' are verb words for the take action; 'lamp' is a plain noun.
    for verb in ("take", "get"):
        flags, action = data[off[verb] + 6], data[off[verb] + 7]
        assert flags & 0x80 and action == actions["take"]
    assert data[off["lamp"] + 6] & 0x80 == 0  # not a verb


# -- end to end on Frotz: read a line, echo per-word recognition -----------


def _echo_story():
    """A hand-assembled routine: read a line, then print 1 for each recognized
    word and 0 for each unknown one (proves tokenizing against the dictionary)."""
    entry = a.Routine("__entry__", entry=True)
    entry.op("call_vn", a.RoutineRef("__main__"))
    entry.op("quit")

    m = a.Routine("__main__", nlocals=4)  # 1:count 2:i 3:widx 4:addr
    m.op("print", text="> ")
    m.op("aread", a.Const(TEXT_BUFFER_ADDR), a.Const(PARSE_BUFFER_ADDR),
         store=a.Variable(a.STACK))
    m.op("loadb", a.Const(PARSE_BUFFER_ADDR), a.Const(1), store=a.Variable(1))
    m.op("print", text="Recognised: ")
    m.op("store", a.Const(2), a.Const(0))  # i = 0
    m.label("loop")
    m.op("je", a.Variable(2), a.Variable(1), branch=("done", True))
    m.op("mul", a.Variable(2), a.Const(2), store=a.Variable(3))  # widx = i*2
    m.op("add", a.Variable(3), a.Const(1), store=a.Variable(3))  # widx += 1
    m.op("loadw", a.Const(PARSE_BUFFER_ADDR), a.Variable(3), store=a.Variable(4))
    m.op("jz", a.Variable(4), branch=("zero", True))  # dict address 0 = unknown
    m.op("print", text="1")
    m.jump("after")
    m.label("zero")
    m.op("print", text="0")
    m.label("after")
    m.op("add", a.Variable(2), a.Const(1), store=a.Variable(2))  # i += 1
    m.jump("loop")
    m.label("done")
    m.op("new_line")
    m.op("rfalse")
    return build_story(world(), entry, [m])


def test_echo_story_is_valid():
    data = _echo_story()
    assert data[0x00] == 5
    assert ((data[0x1C] << 8) | data[0x1D]) == sum(data[0x40:]) & 0xFFFF


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_tokenizing_recognizes_words_on_frotz(tmp_path):
    story = tmp_path / "echo.z5"
    story.write_bytes(_echo_story())
    result = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take lamp zzz\n",
        capture_output=True,
        text=True,
        timeout=15,
    )
    # take and lamp are in the dictionary, zzz is not.
    assert "Recognised: 110" in result.stdout
