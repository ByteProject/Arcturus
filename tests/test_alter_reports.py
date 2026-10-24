# test_alter_reports.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Every standard verb's report speaks through `success`, so an object's
`alter` replaces it (auraes's report, 2026-10-23: an alter on PUSH did
nothing; the audit found SMELL, LISTEN, TOUCH, JUMP, WAIT, SING, YES, NO
and the shiftable push the same). A refusal never alters: a plain PUSH on
an ordinary thing keeps its line."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "A"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south hall\n'
    'thing crate in hall\n    name "crate"\n    words crate\n    shiftable\n'
    '    on push\n        alter "[SHOVE]"\n        continue\n'
    'thing rose in hall\n    name "rose"\n    words rose\n'
    '    on smell\n        alter "[SMELL]"\n        continue\n'
    '    on listen\n        alter "[LISTEN]"\n        continue\n'
    '    on touch\n        alter "[TOUCH]"\n        continue\n'
    'thing button in hall\n    name "button"\n    words button\n'
    '    on push\n        alter "[CLICK]"\n        continue\n'
    'on jump\n    alter "[JUMP]"\n    continue\n'
    'on wait\n    alter "[WAIT]"\n    continue\n'
    'on sing\n    alter "[SING]"\n    continue\n'
)


def test_alter_replaces_every_plain_report():
    io = CaptureIO(script=["smell rose", "listen to rose", "touch rose", "jump",
                           "wait", "sing", "push button", "push crate north"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(GAME))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    for marker in ("[SMELL]", "[LISTEN]", "[TOUCH]", "[JUMP]", "[WAIT]", "[SING]", "[SHOVE]"):
        assert marker in out, marker
    assert "put your shoulder" not in out
    assert "[CLICK]" not in out and "a bit of a push" in out     # a refusal never alters
