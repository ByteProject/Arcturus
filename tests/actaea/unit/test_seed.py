# test_seed.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""--seed N (a field request): a fixed seed makes a session reproducible,
dice and shuffled ambience included, and RESTART rewinds the generator so
the whole session replays identically. Never implied: --check and --replay
stay entropy-seeded unless the flag is given (Stefan's explicit ruling)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    "summon.ambience\n"
    'game\n    title "S"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    ambience about 2 turns\n"
    '        "A raven croaks."\n'
    '        "The wind gusts."\n'
    '        "A shutter bangs."\n'
    '        "Rain ticks at the glass."\n'
)


def _run(seed):
    story = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=["wait"] * 25 + ["quit", "y"])
    vm = VM(load(story), io, seed=seed)
    try:
        vm.run(max_steps=50_000_000)
    except IndexError:
        pass
    return io.text


def test_same_seed_same_session():
    assert _run(42) == _run(42)


def test_seed_reaches_the_generator():
    # Two seeds that happen to produce identical 25-turn ambience would be
    # astronomically unlucky; a plain equality here means the seed was
    # silently ignored, which is the regression this guards against.
    outs = {_run(s) for s in (1, 2, 3, 4)}
    assert len(outs) > 1
