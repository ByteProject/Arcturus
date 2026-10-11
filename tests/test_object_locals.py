# test_object_locals.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A local that holds an object speaks its name (EdwardianDuck's note,
2026-10-05: `let d = bedroom` then `say "${d}"` printed 14). The static
classifier now knows an object by name, the object builtins, an object
local, and the tree reads; the article forms were right all along."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds=()):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_object_locals_print_their_names():
    src = (
        'game\n    title "L"\n    start bedroom\n'
        'room bedroom\n    name "Bedroom"\n    desc "x"\n'
        'thing lamp in bedroom\n    name "brass lamp"\n    words lamp\n'
        'thing box of container in bedroom\n    name "box"\n    words box\n    open\n'
        'thing coin in box\n    name "coin"\n    words coin\n'
        'on start\n'
        '    let d = bedroom\n'
        '    say "${a d}|${the d}|${d}|${bedroom}"\n'
        '    let h = here\n'
        '    say "${h}"\n'
        '    let p = parent_of(coin)\n'
        '    say "${p}"\n'
        '    let f = first_in(box)\n'
        '    say "${f}"\n'
        '    let n = 14\n'
        '    say "${n}"\n'
    )
    out = _run(src)
    assert "a Bedroom|the Bedroom|Bedroom|Bedroom" in out
    assert "\nBedroom\n" in out.split("|")[-1]      # here, through a local
    assert "\nbox\n" in out                           # parent_of
    assert "\ncoin\n" in out                          # first_in
    assert "\n14\n" in out                            # a plain number stays digits
