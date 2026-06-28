# test_words.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Object words -> dictionary addresses (B4.5d.1). Each object's words property
holds an array of dictionary entry addresses so the parser can match typed words
to objects."""

from arcturus import zstring
from arcturus.codegen import generate
from arcturus.objects import build_layout
from arcturus.parser import parse
from arcturus.sema import analyze

SRC = (
    'thing lamp in cave\n'
    '    name "lamp"\n'
    '    words brass, lamp, lantern\n'
    'room cave\n'
    '    name "Cave"\n'
)


def _word(data, off):
    return (data[off] << 8) | data[off + 1]


def _words_array(data, obj_num, words_prop):
    """Read an object's words-property array of dictionary addresses."""
    obj_table = _word(data, 0x0A)
    entry = obj_table + 63 * 2 + (obj_num - 1) * 14
    pos = _word(data, entry + 12)
    pos += 1 + data[pos] * 2  # skip the short name
    while data[pos] != 0:
        size = data[pos]
        if size & 0x80:  # two-byte size form
            pnum, length, dstart = size & 0x3F, data[pos + 1] & 0x3F, pos + 2
            if pnum == words_prop:
                return [_word(data, dstart + i * 2) for i in range(length // 2)]
            pos = dstart + length
        else:  # one-byte form
            pos += 1 + (2 if (size & 0x40) else 1)
    return []


def test_words_property_holds_dictionary_addresses():
    world = analyze(parse(SRC))
    layout = build_layout(world)
    data = generate(world)
    addrs = _words_array(data, layout.obj_number["lamp"], layout.prop_number["words"])
    decoded = [zstring.decode(bytes(data[a : a + 6])) for a in addrs]
    assert decoded == ["brass", "lamp", "lantern"]
