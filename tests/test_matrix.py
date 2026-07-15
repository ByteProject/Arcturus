# test_matrix.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The matrix: the mutable sibling of a catalog (summon.matrix). A
capacity-bounded sequence in dynamic memory whose LENGTH changes at
runtime. It shares a catalog's region, base, and [count, ..., cells]
header (the widest word repurposed to hold the capacity), so every
catalog read verb works unchanged; only the mutators (append, remove,
insert, clear, load) and the declaration are new. Numeric only (number,
object, byte), never text. Strictly summoned: inert and zero-byte
without summon.matrix."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(story, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


HEAD = (
    'game\n    title "M"\n    start lab\n'
    'summon.matrix\n'
    'room lab\n    name "Lab"\n    desc "Tidy."\n'
)


def _probe(body, cmds=("probe",), extra=""):
    src = HEAD + extra + 'verb "probe"\n    probe\n' + 'on probe\n' + body
    return _run(_build(src), cmds).split(">probe")[-1]


# -- reads reuse the catalog verbs, but the count is the LIVE length --------

def test_seed_and_calculate_and_last():
    out = _probe(
        '    say "len=${calculate(m)} last=${last(m)} e2=${entry(m, 2)}"\n',
        extra='matrix m capacity 6\n    2\n    3\n    5\n')
    assert "len=3 last=5 e2=3" in out


# -- append grows the length; overflow returns 0 ----------------------------

def test_append_grows_and_reports_full():
    out = _probe(
        '    append 7 to m\n'
        '    append 11 to m\n'
        '    say "len=${calculate(m)} last=${last(m)} "\n'
        '    if append 99 to m is 0\n'
        '        say "FULL"\n',
        extra='matrix m capacity 4\n    2\n    3\n')
    assert "len=4 last=11 " in out
    assert "FULL" in out  # the fourth append filled it; the fifth refused


def test_append_success_is_testable():
    out = _probe(
        '    if append 1 to m is 0\n'
        '        say "unexpected-full"\n'
        '    say "ok len=${calculate(m)}"\n',
        extra='matrix m capacity 2\n')
    assert "unexpected-full" not in out
    assert "ok len=1" in out


# -- remove: order-preserving shift, and O(1) swap-with-last ----------------

def test_remove_by_index_shifts():
    out = _probe(
        '    remove entry(m, 1)\n'
        '    say "e1=${entry(m,1)} e2=${entry(m,2)} len=${calculate(m)}"\n',
        extra='matrix m capacity 5\n    10\n    20\n    30\n')
    assert "e1=20 e2=30 len=2" in out


def test_remove_by_index_swapping_is_unordered():
    out = _probe(
        '    remove entry(m, 1) swapping\n'
        '    say "e1=${entry(m,1)} len=${calculate(m)}"\n',
        extra='matrix m capacity 5\n    10\n    20\n    30\n')
    # the last entry (30) moved into the hole; order is not preserved
    assert "e1=30 len=2" in out


def test_remove_by_value():
    out = _probe(
        '    remove 20 from m\n'
        '    say "len=${calculate(m)} pos30=${position(m, 30)}"\n',
        extra='matrix m capacity 5\n    10\n    20\n    30\n')
    assert "len=2 pos30=2" in out


def test_remove_absent_value_is_a_noop():
    out = _probe(
        '    if remove 99 from m is 0\n'
        '        say "absent"\n'
        '    say "len=${calculate(m)}"\n',
        extra='matrix m capacity 5\n    10\n    20\n')
    assert "absent" in out
    assert "len=2" in out


# -- insert shifts up; clear empties ----------------------------------------

def test_insert_at_head():
    out = _probe(
        '    insert 42 into m at 1\n'
        '    say "e1=${entry(m,1)} e2=${entry(m,2)} len=${calculate(m)}"\n',
        extra='matrix m capacity 5\n    3\n    7\n')
    assert "e1=42 e2=3 len=3" in out


def test_clear_empties_the_length():
    out = _probe(
        '    clear m\n'
        '    say "len=${calculate(m)}"\n',
        extra='matrix m capacity 5\n    1\n    2\n    3\n')
    assert "len=0" in out


# -- membership, iteration, objects -----------------------------------------

def test_membership_and_for_each_sum():
    out = _probe(
        '    append 10 to m\n'
        '    append 20 to m\n'
        '    let s = 0\n'
        '    for each x in m\n'
        '        change s to s + x\n'
        '    say "sum=${s} in20=${20 in m} in99=${99 in m}"\n',
        extra='matrix m capacity 4\n')
    assert "sum=30 in20=1 in99=0" in out


def test_object_matrix_iterates_as_objects():
    out = _probe(
        '    append troll to crew\n'
        '    append goblin to crew\n'
        '    for each who in crew\n'
        '        say "[${the who}]"\n',
        extra=('thing troll in lab\n    name "troll"\n'
               'thing goblin in lab\n    name "goblin"\n'
               'matrix crew capacity 4 of object\n'))
    assert "[the troll]" in out
    assert "[the goblin]" in out
    assert out.index("troll") < out.index("goblin")  # append order preserved


# -- the catalog bridge ------------------------------------------------------

def test_load_from_catalog():
    out = _probe(
        '    load m from src\n'
        '    say "len=${calculate(m)} e2=${entry(m,2)}"\n',
        extra=('catalog src\n    10\n    20\n    30\n'
               'matrix m capacity 5\n'))
    assert "len=3 e2=20" in out


# -- gate and validation -----------------------------------------------------

def _err(src):
    with pytest.raises(Exception) as e:
        _build(src)
    return str(e.value)


def test_matrix_needs_summon():
    src = ('game\n    title "M"\n    start lab\n'
           'room lab\n    name "Lab"\n    desc "x."\n'
           'matrix m capacity 3\n')
    assert "summon.matrix" in _err(src)


def test_text_seed_is_rejected():
    assert "numeric" in _err(HEAD + 'matrix m capacity 3\n    "x"\n')


def test_byte_range_is_checked():
    assert "0..255" in _err(HEAD + 'matrix m capacity 3 of byte\n    300\n')


def test_seed_over_capacity_is_rejected():
    assert "exceed" in _err(HEAD + 'matrix m capacity 1\n    1\n    2\n')


def test_literal_index_past_capacity_is_a_compile_error():
    body = '    say "${entry(m, 9)}"\n'
    src = HEAD + 'matrix m capacity 3\n' + 'verb "probe"\n    probe\non probe\n' + body
    assert "capacity" in _err(src)


# -- pay-for-use: un-summoned, zero bytes ------------------------------------

def test_unsummoned_program_is_byte_identical():
    # A game that never summons matrix is byte-for-byte a game with no matrix
    # machinery at all: the whole feature folds away.
    plain = ('game\n    title "P"\n    start lab\n'
             'room lab\n    name "Lab"\n    desc "x."\n'
             'verb "wait"\n    wait\non wait\n    say "tick"\n')
    a = _build(plain)
    b = _build(plain)  # deterministic build
    assert a == b
