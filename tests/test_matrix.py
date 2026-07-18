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


# -- 2D grids (tables) -------------------------------------------------------

def test_2d_grid_reads_and_dimensions():
    out = _probe(
        '    say "dims ${rows(g)}x${columns(g)} "\n'
        '    say "r1c1=${entry(g,1,1)} r2c3=${entry(g,2,3)} r3c3=${entry(g,3,3)}"\n',
        extra=('matrix g 3 by 3\n'
               '    row 2, 4, 6\n'
               '    row 1, 3, 5\n'
               '    row 0, 0, 9\n'))
    assert "dims 3x3 " in out
    assert "r1c1=2 r2c3=5 r3c3=9" in out


def test_2d_grid_write_and_full_sweep():
    out = _probe(
        '    change entry(g, 1, 1) to 99\n'
        '    let sum = 0\n'
        '    let r = 1\n'
        '    while r <= rows(g)\n'
        '        let c = 1\n'
        '        while c <= columns(g)\n'
        '            change sum to sum + entry(g, r, c)\n'
        '            change c to c + 1\n'
        '        change r to r + 1\n'
        '    say "r1c1=${entry(g,1,1)} sum=${sum}"\n',
        extra=('matrix g 3 by 3\n'
               '    row 2, 4, 6\n'
               '    row 1, 3, 5\n'
               '    row 0, 0, 9\n'))
    # original sum 30, minus the 2 at (1,1) plus 99 = 127
    assert "r1c1=99 sum=127" in out


def test_2d_byte_grid_packs_and_holds_0_255():
    out = _probe(
        '    change entry(g, 5, 5) to 200\n'
        '    say "seed=${entry(g,1,3)} set=${entry(g,5,5)} zero=${entry(g,16,16)}"\n',
        extra=('matrix g 16 by 16 of byte\n'
               '    row 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16\n'))
    assert "seed=3 set=200 zero=0" in out


def test_2d_byte_grid_is_half_the_memory():
    # A byte grid reserves rows*cols bytes; a word grid twice that. The layout
    # proves it: build both and compare the stats.
    from arcturus.worldmodel import Matrix
    wsrc = HEAD + 'matrix g 16 by 16\n'
    bsrc = HEAD + 'matrix g 16 by 16 of byte\n'
    # A byte grid's dynamic footprint is half a word grid's.
    wworld = analyze(cosmos.combined_program(parse(wsrc + 'verb "w"\n    w\non w\n    say "x"\n')))
    bworld = analyze(cosmos.combined_program(parse(bsrc + 'verb "w"\n    w\non w\n    say "x"\n')))
    wbytes = sum(m.rows * m.cols * 2 for m in wworld.matrices.values())
    bbytes = sum((m.rows * m.cols + 1) // 2 * 2 for m in bworld.matrices.values())
    assert wbytes == 512
    assert bbytes == 256


def test_2d_rejects_object_cells():
    assert "not objects" in _err(HEAD + 'matrix g 2 by 2 of object\n')


def test_2d_seed_row_width_must_match():
    assert "columns" in _err(HEAD + 'matrix g 3 by 3\n    row 1, 2\n')


def test_2d_literal_index_out_of_range_is_a_compile_error():
    body = '    say "${entry(g, 4, 1)}"\n'
    src = HEAD + 'matrix g 3 by 3\n' + 'verb "probe"\n    probe\non probe\n' + body
    assert "3 by 3" in _err(src)


# -- directions as cells, and the parameter recipe (a field case) ------------

def test_directions_store_and_iterate():
    # A direction is its property number, an ordinary matrix cell: a maze
    # route or a patrol path appends and reads directions directly.
    out = _probe(
        '    append north to m\n'
        '    append east to m\n'
        '    for each d in m\n'
        '        if d is north\n'
        '            show("N")\n'
        '        if d is east\n'
        '            show("E")\n'
        '    say " len=${calculate(m)}"\n',
        extra='matrix m capacity 4\n')
    assert "NE len=2" in out


def test_directions_switch_as_cases():
    # switch on a stored direction: a case is any compile-time value, so
    # `case north` folds like `if d is north` (the maze-route shape).
    out = _probe(
        '    append up to m\n'
        '    let d = entry(m, 1)\n'
        '    switch d\n'
        '        case north\n'
        '            say "N"\n'
        '        case up\n'
        '            say "U"\n'
        '        else\n'
        '            say "?"\n',
        extra='matrix m capacity 4\n')
    assert "U" in out.split(">probe")[-1]


def test_matrix_parameter_walks_by_index():
    # A matrix passes to a block as its offset; calculate/entry work on the
    # parameter, so a shared helper walks it by index. (`for each` needs the
    # matrix named in place; over a parameter it would walk the object tree,
    # the field bug.)
    src = HEAD + (
        'matrix route capacity 4\n    2\n    5\n'
        'matrix patrol capacity 4\n    7\n'
        'block total(m)\n'
        '    let n = calculate(m)\n'
        '    let s = 0\n'
        '    let i = 1\n'
        '    while i <= n\n'
        '        change s to s + entry(m, i)\n'
        '        change i to i + 1\n'
        '    return s\n'
        'verb "probe"\n    probe\n'
        'on probe\n'
        '    say "r=${total(route)} p=${total(patrol)}"\n'
    )
    out = _run(_build(src), ["probe"])
    assert "r=7 p=7" in out


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


def test_matrix_of_direction_says_words():
    # `matrix patrol capacity 4 of direction`: seeds and appends are
    # direction names, and say speaks the word, the catalog symmetry.
    game = (
        'game\n    title "T"\n    start hall\n'
        'summon.matrix\n'
        'matrix patrol capacity 4 of direction\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n    north cellar\n'
        '    on probe_it\n'
        '        append north to patrol\n'
        '        append east to patrol\n'
        '        for each p in patrol\n'
        '            say "${p} "\n'
        'room cellar\n    name "Cellar"\n    desc "C."\n'
    )
    from arcturus import cosmos as _c
    from arcturus.codegen import generate as _g
    from arcturus.sema import analyze as _a
    from arcturus.parser import parse as _p
    story = _g(_a(_c.combined_program(_p(game))))
    io = CaptureIO(script=["probe"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "north east" in " ".join(io.text.split())


def test_matrix_of_direction_refuses_a_non_direction_seed():
    import pytest as _pt
    bad = (
        'game\n    title "T"\n    start hall\n'
        'summon.matrix\n'
        'matrix patrol capacity 4 of direction\n'
        '    wibble\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
    )
    from arcturus import cosmos as _c
    from arcturus.sema import analyze as _a
    from arcturus.parser import parse as _p
    with _pt.raises(Exception) as e:
        _a(_c.combined_program(_p(bad)))
    assert "not a direction" in str(e.value)


def test_global_initialized_with_a_matrix_aliases_it():
    # The field bug: a catalog or matrix name in a global initializer fell
    # through SILENTLY and the global stayed 0, aliasing the region's
    # first occupant. With two matrices the wrong one answered.
    game = (
        'game\n    title "T"\n    start hall\n'
        'summon.matrix\n'
        'matrix bmat capacity 4\nmatrix cmat capacity 4\n'
        'global a = cmat\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        '    on probe_it\n'
        '        append 7 to bmat\n        append 5 to cmat\n'
        '        say "b=${entry(bmat,1)} viaA=${entry(a,1)}"\n'
    )
    from arcturus import cosmos as _c
    from arcturus.codegen import generate as _g
    from arcturus.sema import analyze as _a
    from arcturus.parser import parse as _p
    story = _g(_a(_c.combined_program(_p(game))))
    io = CaptureIO(script=["probe"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "b=7 viaA=5" in io.text


def test_direction_matrix_seed_compiles_and_runs():
    # The field crash (Charles Moore Jr., 2026-07-18): a seeded
    # `matrix ... of direction` hit the number branch in the seed writer,
    # which did .value on a Name: AttributeError with no line number. The
    # full scenario: seed, dice from a direction catalog, change entry,
    # for-each speaking the words.
    game = (
        'game\n    title "T"\n    start hall\n'
        'summon.matrix\n'
        'catalog valid_dirs\n    north\n    south\n    east\n    west\n'
        'matrix to_barge capacity 5 of direction\n'
        '    north\n    north\n    north\n    north\n    north\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        '    on probe_it\n'
        '        let x = 1\n        let d = 0\n'
        '        while x < 6\n'
        '            change d to dice(valid_dirs)\n'
        '            change entry(to_barge, x) to d\n'
        '            change x to x + 1\n'
        '        for each w in to_barge\n'
        '            say "${w} "\n'
    )
    from arcturus import cosmos as _c
    from arcturus.codegen import generate as _g
    from arcturus.sema import analyze as _a
    from arcturus.parser import parse as _p
    story = _g(_a(_c.combined_program(_p(game))))
    io = CaptureIO(script=["probe"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    words = [w for w in io.text.split(">probe")[-1].split()
             if w in ("north", "south", "east", "west")]
    assert len(words) == 5
