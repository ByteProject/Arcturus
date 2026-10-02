# test_scenery_contents.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""constant scenery_contents = 1: the room description lists what sits on
or in scenery holders, one paragraph each (the PunyInform
OPTIONAL_PRINT_SCENERY_CONTENTS bridge). Off by default, folded away; the
knowledge model gates each item; the language layer words the line."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = (
    'room shop\n    name "Shop"\n    desc "Dusty."\n'
    'thing counter2 of supporter in shop\n    name "counter"\n    words counter\n'
    '    scenery\n    fixed\n'
    'thing jar of container in shop\n    name "alcove"\n    words alcove\n'
    '    scenery\n    open\n    fixed\n'
    'thing bell in counter2\n    name "bell"\n'
    'thing candle in counter2\n    name "candle"\n'
    'thing key in jar\n    name "key"\n'
)
ON = 'game\n    title "S"\n    start shop\nconstant scenery_contents = 1\n' + BASE
OFF = 'game\n    title "S"\n    start shop\n' + BASE


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, cmds):
    return subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input=cmds, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_scenery_holders_get_their_paragraphs(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(ON))
    out = _run(story, "take bell\nlook\n")
    assert "On the counter you can see a bell and a candle." in out
    assert "In the alcove you can see a key." in out
    assert "On the counter you can see a candle." in out  # updates live
    assert "You can see a counter" not in out             # scenery stays unlisted


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_off_by_default(tmp_path):
    story = tmp_path / "s.z5"
    story.write_bytes(_build(OFF))
    out = _run(story, "look\n")
    assert "On the counter" not in out
    assert "you can see a bell" not in out
    # and the opt-out build is smaller: the pass folded away
    assert len(_build(OFF)) < len(_build(ON))


def test_closed_scenery_holder_speaks_as_memory():
    # Charles Moore Jr.'s report (2026-09-24): with the constant on, a
    # scenery cupboard closed again kept "In the cupboard you can see a
    # bell." The knowledge model is right to remember the bell (the inline
    # listing says "a cupboard (closed) (contains a bell)"); the paragraph
    # now says the same honest thing, never a sight the player lacks.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'constant scenery_contents = 1\n'
        'game\n    title "SC"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing cupboard of container in hall\n    name "cupboard"\n'
        '    words cupboard\n    scenery\n    openable\n'
        'thing bell in cupboard\n    name "bell"\n    words bell\n'
    )
    io = CaptureIO(script=["look", "open cupboard", "look", "close cupboard",
                           "look"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    looks = io.text.split(">look")
    assert "bell" not in looks[1].split(">open")[0]             # secret until opened
    assert "In the cupboard you can see a bell." in looks[2]    # open: sight
    assert "The cupboard (closed) contains a bell." in looks[3]  # closed: memory
    assert "you can see a bell" not in looks[3]
