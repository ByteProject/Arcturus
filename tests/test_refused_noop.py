# test_refused_noop.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A real refusal marks the turn refused (docs/01 chapter 13: the after
phase runs only on a completed action, and a chained line stops at a
refusal). Charles Moore Jr.'s report (2026-09-26): DROP of a thing not
held spoke the refusal and then ran the on after drop handler. The
"already" outcomes are not refusals (chapter 14) and are untouched."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "R"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing rock in hall\n    name "rock"\n    words rock\n'
    '    on after drop\n        say "AFTER DROP"\n'
    '    on after take\n        say "AFTER TAKE"\n'
    'thing hat in hall\n    name "hat"\n    words hat\n    wearable\n'
    '    on after wear\n        say "AFTER WEAR"\n'
    '    on after take_off\n        say "AFTER DOFF"\n'
    'thing box of container in hall\n    name "box"\n    words box\n'
    '    openable\n    lockable\n    fixed\n'
    '    on after open\n        say "AFTER OPEN"\n'
    '    on after close\n        say "AFTER CLOSE"\n'
    '    on after lock\n        say "AFTER LOCK"\n'
    'thing chair of supporter in hall\n    name "chair"\n    words chair\n'
    '    fixed\n'
    '    on after enter\n        say "AFTER ENTER"\n'
)


def _run(cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_a_real_refusal_skips_the_after_phase():
    # Not held is a real refusal: no after phase, no chain. The "already"
    # outcomes (already have it, already open, already there) are not
    # refusals by the chapter 14 rule and keep the line going; they are
    # left as they were.
    out = _run(["drop rock", "take rock", "drop rock", "take rock",
                "take rock", "open box", "open box", "sit on chair",
                "sit on chair"])
    assert out.count("AFTER DROP") == 1        # only the real drop
    assert "aren't carrying" in out.split(">take rock")[0]


def test_an_already_held_outcome_still_chains():
    out = _run(["take rock", "take rock and open box"])
    assert "already" in out
    assert "AFTER OPEN" in out                 # the line went on past the no-op


def test_a_real_refusal_stops_a_chained_line():
    out = _run(["drop rock then take rock"])
    assert "aren't carrying" in out
    assert "AFTER TAKE" not in out             # the chain stopped at the refusal
