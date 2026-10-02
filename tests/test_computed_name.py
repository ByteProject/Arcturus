# test_computed_name.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""name block (docs/01 chapter 5): the computed short name, Inform's
short_name in the block idiom (auraes's ask, 2026-09-23). It used to
compile and print garbage; now every object-name print site runs the
block (cosmos_print_name), games with literal names only keep the bare
opcode (the untouched ceilings). Alongside: the honest error for
`change obj.name`, and first_in / next_in, the tree links as values."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


NAMED = (
    'game\n    title "N"\n    start hall\n'
    'global polished = false\n'
    'room hall\n    name "Hall"\n    desc "Bare."\n'
    'thing coin in hall\n'
    '    name block\n'
    '        if polished is true\n'
    '            show("gleaming relic")\n'
    '        else\n'
    '            show("dull coin")\n'
    '    words coin, relic\n    desc "Round."\n'
    'thing jar of container in hall\n    name "jar"\n    words jar\n    open\n'
    'verb "polish"\n    vpolish noun\n'
    'on vpolish\n    change polished to true\n    say "You polish ${the noun}."\n'
)


def test_name_block_speaks_everywhere_and_follows_state():
    out = _run(NAMED, ["look", "take coin", "inventory", "polish coin",
                       "inventory", "put coin in jar", "look"])
    assert "You can see a dull coin and a jar here." in out
    assert "You take the dull coin with you." in out
    assert " a dull coin" in out.split(">inventory")[1]
    assert "You polish the gleaming relic." in out
    assert " a gleaming relic" in out.split(">inventory")[2]
    assert "You put the gleaming relic in the jar." in out
    assert "gleaming relic" in out.split(">look")[2]        # listed inside the jar
    assert "bg" not in out                                   # the old garbage


def test_change_name_names_the_cure():
    src = NAMED.replace("    change polished to true\n",
                        '    change noun.name to "relic"\n')
    with pytest.raises(ArcError) as e:
        generate(analyze(cosmos.combined_program(parse(src))))
    msg = str(e.value)
    assert "short name" in msg and "name block" in msg
    assert "boolean" not in msg


def test_first_in_and_next_in_walk_the_tree():
    src = (
        'game\n    title "F"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "Bare."\n'
        'thing box of container in hall\n    name "box"\n    words box\n    open\n'
        'thing coin in box\n    name "coin"\n    words coin\n'
        'thing nail in box\n    name "nail"\n    words nail\n'
        'on start\n'
        '    let c = first_in(box)\n'
        '    say "first ${c}"\n'
        '    say "second ${next_in(c)}"\n'
        '    say "end ${next_in(next_in(c))}"\n'
        '    if first_in(coin) is nothing\n'
        '        say "coin empty"\n'
        '    if first_in(box) is not nothing\n'
        '        say "box full"\n'
    )
    out = _run(src, [])
    head = out.split("F\n")[0]
    assert "first 4" in head and "second 5" in head and "end 0" in head
    assert "coin empty" in head and "box full" in head
