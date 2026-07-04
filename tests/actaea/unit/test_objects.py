# test_objects.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M4: the object tree, attributes, and properties. The table logic
is exercised directly through ObjectTable over a zasm-built image, then the
opcodes end to end through the VM."""

import pytest

from actaea.objects import ObjectError
from zasm import (
    L, NEWLINE, QUIT, S, SP, V, branch, build, long2, objtable, print_num,
    run, short1, vop,
)

# A small world: 1 = a room holding 2 (a box) and 4 (a coin, the box's
# sibling); 3 = a gem inside the box. Attributes and properties to taste.
WORLD = objtable(
    [
        {"child": 2, "props": {5: b"\x12\x34", 3: b"\x07"}},
        {"parent": 1, "sibling": 4, "child": 3,
         "attrs": (0, 7, 47), "props": {10: b"\xAB\xCD", 6: b"ABCDEF"}},
        {"parent": 2, "attrs": (13,)},
        {"parent": 1, "props": {5: b"\x00\x2A"}},
    ],
    defaults=[100 + i for i in range(63)],
)


def _table():
    vm, io, _ = build(QUIT, objects=WORLD)
    return vm.objects


# -- the table, directly ----------------------------------------------------------

def test_attributes_set_test_clear():
    t = _table()
    assert t.test_attr(2, 0) and t.test_attr(2, 7) and t.test_attr(2, 47)
    assert not t.test_attr(2, 1) and not t.test_attr(2, 46)
    assert t.test_attr(3, 13)
    t.clear_attr(2, 7)
    assert not t.test_attr(2, 7)
    t.set_attr(2, 46)
    assert t.test_attr(2, 46) and t.test_attr(2, 47)  # neighbours undisturbed
    with pytest.raises(ObjectError):
        t.test_attr(2, 48)


def test_tree_reads_and_object_zero_is_a_fault():
    t = _table()
    assert t.parent(2) == 1 and t.sibling(2) == 4 and t.child(2) == 3
    assert t.parent(1) == 0 and t.child(1) == 2
    with pytest.raises(ObjectError) as e:
        t.parent(0)
    assert "nothing" in str(e.value)


def test_insert_makes_first_child():
    t = _table()
    t.insert(4, 2)  # the coin moves into the box
    assert t.parent(4) == 2
    assert t.child(2) == 4 and t.sibling(4) == 3  # gem chained behind it
    assert t.child(1) == 2 and t.sibling(2) == 0  # room's chain stitched


def test_remove_stitches_the_chain():
    t = _table()
    # Give the room three children: coin, then box, then insert a third.
    t.insert(3, 1)  # gem leaves the box for the room: child order 3, 2, 4
    assert t.child(1) == 3 and t.sibling(3) == 2 and t.sibling(2) == 4
    t.remove(2)     # the middle child
    assert t.sibling(3) == 4 and t.parent(2) == 0 and t.sibling(2) == 0
    t.remove(3)     # the first child
    assert t.child(1) == 4
    t.remove(4)
    assert t.child(1) == 0
    t.remove(4)     # removing a parentless object is a quiet no-op


def test_properties_read_write_defaults():
    t = _table()
    assert t.get_prop(1, 5) == 0x1234
    assert t.get_prop(1, 3) == 0x07
    assert t.get_prop(4, 5) == 0x2A
    # Absent: the defaults table answers (property n defaults to 100 + n - 1).
    assert t.get_prop(1, 10) == 109
    assert t.get_prop(3, 1) == 100
    t.put_prop(1, 5, 0xBEEF)
    assert t.get_prop(1, 5) == 0xBEEF
    t.put_prop(1, 3, 0x1FF)  # a byte property keeps the low byte
    assert t.get_prop(1, 3) == 0xFF
    with pytest.raises(ObjectError):
        t.put_prop(1, 9, 1)  # absent: put has no default to write to
    with pytest.raises(ObjectError):
        t.get_prop(2, 6)     # six bytes long: an illegal 1/2-byte read


def test_prop_addr_len_and_next():
    t = _table()
    a = t.get_prop_addr(2, 6)
    assert a != 0 and t.get_prop_len(a) == 6
    assert t.mem.mem[a:a + 6] == b"ABCDEF"
    assert t.get_prop_addr(2, 5) == 0
    assert t.get_prop_len(0) == 0
    assert t.get_prop_len(t.get_prop_addr(1, 5)) == 2
    assert t.get_prop_len(t.get_prop_addr(1, 3)) == 1
    # get_next_prop walks descending: 0 -> 10 -> 6 -> 0 on the box.
    assert t.get_next_prop(2, 0) == 10
    assert t.get_next_prop(2, 10) == 6
    assert t.get_next_prop(2, 6) == 0
    with pytest.raises(ObjectError):
        t.get_next_prop(2, 5)  # asking after a property the box lacks


# -- the opcodes, through the VM ------------------------------------------------------

def test_jin_and_attr_opcodes():
    out = run(
        long2(0x06, S(2), S(1))              # jin box, room: taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + long2(0x0A, S(2), S(7))            # test_attr box, 7: set in WORLD
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + long2(0x0C, S(2), S(7))            # clear_attr box, 7
        + long2(0x0A, S(2), S(7))            # now clear: branch NOT taken
        + branch(False, +6)
        + print_num(S(0)) + QUIT
        + long2(0x0B, S(3), S(20))           # set_attr gem, 20
        + long2(0x0A, S(3), S(20))
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + print_num(S(1)) + QUIT,
        objects=WORLD,
    )
    assert out == "1"


def test_tree_opcodes_store_and_branch():
    out = run(
        short1(0x03, S(3), store=SP)         # get_parent gem -> sp (the box)
        + print_num(V(SP)) + NEWLINE
        + short1(0x01, S(2), store=SP)       # get_sibling box: 4, branch taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + short1(0x02, S(3), store=SP)       # get_child gem: 0, NOT taken
        + branch(False, +6)
        + print_num(S(0)) + QUIT
        + print_num(V(SP)) + NEWLINE         # the stored 0 child
        + print_num(V(SP))                   # the stored sibling 4 beneath it
        + QUIT,
        objects=WORLD,
    )
    assert out == "2\n0\n4"


def test_insert_obj_moves_the_coin():
    out = run(
        long2(0x0E, S(4), S(2))              # insert_obj coin, box
        + long2(0x06, S(4), S(2))            # jin coin, box: taken now
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + short1(0x02, S(2), store=SP)       # get_child box -> the coin
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + print_num(V(SP))
        + QUIT,
        objects=WORLD,
    )
    assert out == "4"


def test_property_opcodes_end_to_end():
    out = run(
        long2(0x11, S(1), S(5), store=SP)    # get_prop room.5
        + print_num(V(SP)) + NEWLINE
        + vop(0x03, S(1), S(5), L(0x0100))   # put_prop room.5 = 256
        + long2(0x11, S(1), S(5), store=SP)
        + print_num(V(SP)) + NEWLINE
        + long2(0x11, S(3), S(2), store=SP)  # absent: default (101)
        + print_num(V(SP)) + NEWLINE
        + long2(0x12, S(2), S(6), store=SP)  # get_prop_addr box.6
        + short1(0x04, V(SP), store=SP)      # get_prop_len of it
        + print_num(V(SP)) + NEWLINE
        + long2(0x13, S(2), S(0), store=SP)  # get_next_prop box, 0 -> 10
        + print_num(V(SP))
        + QUIT,
        objects=WORLD,
    )
    assert out == "4660\n256\n101\n6\n10"
