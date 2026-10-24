# test_computed_values.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Computed value properties (docs/01 chapter 5; EdwardianDuck's report,
2026-10-18, lifted by Stefan's ruling 2026-10-24): a number or object
property may be a block that returns its value. Once any declaration is a
block, the property is computed everywhere: plain values become shared
routines and every read calls. A property declared only as a block takes
its type from its returns."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "C"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'flag stormy = false\n'
    'kind gauge of thing\n    reading 7\n'
    'thing barometer of gauge in hall\n    name "barometer"\n    words barometer\n'
    '    reading block\n        if stormy is true\n            return 3\n        return 9\n'
    'thing clock of gauge in hall\n    name "clock"\n    words clock\n'
    'thing sundial in hall\n    name "sundial"\n    words sundial\n    reading 1\n'
    'thing rock in hall\n    name "rock"\n    words rock\n'
    'thing key in hall\n    name "brass key"\n    words key\n'
    'thing tray in hall\n    name "tray"\n    words tray\n'
    '    best_key block\n        return key\n'
    '    mood block\n        say "grumpy"\n'
    'verb "read"\n    read noun\n'
    'on read\n    say "It reads ${noun.reading}."\n'
    'verb "storm"\n    storm\n'
    'on storm\n    change stormy to true\n    say "Thunder."\n'
    'verb "probe"\n    probe\n'
    'on probe\n    say "${tray.best_key} / ${the tray.best_key} / ${tray.mood}"\n'
)


def _run(cmds, src=GAME):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_a_computed_number_reads_its_block_its_default_and_zero():
    out = _run(["read barometer", "read clock", "read sundial", "read rock",
                "storm", "read barometer"])
    parts = out.split(">read ")
    assert "It reads 9." in parts[1]          # the block
    assert "It reads 7." in parts[2]          # the kind's plain default
    assert "It reads 1." in parts[3]          # an object's own literal
    assert "It reads 0." in parts[4]          # no such property
    assert "It reads 3." in parts[5]          # the block, after the storm


def test_block_only_properties_take_their_type_from_their_returns():
    out = _run(["probe"])
    assert "brass key / the brass key / grumpy" in out


def test_a_computed_property_is_never_changed():
    bad = GAME + 'verb "fix"\n    fix\non fix\n    change sundial.reading to 5\n'
    with pytest.raises(ArcError) as exc:
        generate(analyze(cosmos.combined_program(parse(bad))))
    assert "is computed" in str(exc.value)
