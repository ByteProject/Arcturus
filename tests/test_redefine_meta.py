# test_redefine_meta.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`redefine verb ... meta` (improvmonster's report, 2026-10-30): redefine
replaces a verb whole and may restate it out-of-world; enhance takes no
meta; and an action is in the world or out of it, never both, so a meta
verb naming an in-world verb's action is refused, naming both verbs."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _compile(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_compile(src)), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


BASE = (
    'game\n    title "G"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing statue in hall\n    name "statue"\n    words statue\n'
    '    on other\n        say "[statue other]"\n'
)


def test_a_redefined_verb_can_turn_meta():
    src = BASE + (
        'redefine verb "xyzzy", "plugh" meta\n    credits\n'
        'thing book in hall\n    name "book"\n    words book\n'
        'on credits\n    change meta_turn to 1\n    say "Written in Arcturus."\n')
    out = _run(src, ["xyzzy", "plugh", "x statue"])
    parts = out.split(">")[1:]
    assert "Written in Arcturus." in parts[0] and "Written in Arcturus." in parts[1]
    assert "[statue other]" not in parts[0] + parts[1]   # meta: past every handler
    assert "[statue other]" in parts[2]                  # examine stays in the world


def test_a_redefine_without_meta_leaves_a_meta_verb_meta():
    src = BASE + 'redefine verb "version", "ver"\n    version\n'
    out = _run(src, ["ver"])
    assert "[statue other]" not in out.split(">")[1]


def test_enhance_takes_no_meta():
    with pytest.raises(ArcError, match="redefine verb ... meta"):
        _compile(BASE + 'enhance verb "xyzzy" meta\n    xyzzy noun\n')


@pytest.mark.parametrize("decl, meta_verb, other", [
    ('verb "peek" meta\n    examine noun\n', "peek", "examine"),
    ('redefine verb "examine", "x" meta\n    examine noun\n', "examine", "read"),
    ('verb "about" meta\n    about\nverb "credits"\n    about\n', "about", "credits"),
])
def test_an_action_is_in_the_world_or_out_of_it(decl, meta_verb, other):
    with pytest.raises(ArcError) as e:
        _compile(BASE + decl + 'on about\n    say "About."\n')
    msg = str(e.value)
    assert f'verb "{meta_verb}" is meta' in msg and f'verb "{other}" names' in msg


def test_two_meta_verbs_may_share_an_action():
    src = BASE + ('verb "about" meta\n    about\nverb "credits" meta\n    about\n'
                  'on about\n    say "About."\n')
    out = _run(src, ["credits", "about"])
    assert out.count("About.") == 2 and "[statue other]" not in out
