# test_sugar.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The readability fundamentals (Stefan's rulings, 2026-07-04): bare
zero-argument calls (print_banner, not print_banner()), the `is [not] in`
tree test, the par.say leading-paragraph say, and the banner spacing (title
directly under the status bar; a trailing pending break instead of story-side
par() calls)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "s.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", "-w", "90", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


GAME = (
    'game\n    title "S"\n    start lab\n'
    'room lab\n    name "Lab"\n    desc "A lab."\n'
    'thing box of container in lab\n    name "box"\n    words box\n'
    'thing coin in box\n    name "coin"\n    words coin\n'
    'block cheer()\n    say "Hooray."\n'
    'block greet(who)\n    say "Hi."\n'
    'thing bell in lab\n    name "bell"\n    words bell\n'
    "    on push\n"
    "        cheer\n"
    "        if coin is in box\n"
    '            say "In the box."\n'
    "        if coin is not in lab\n"
    '            say "Not loose."\n'
    "        let n = word_count\n"
    "        show(n)\n"
    '        say " words."\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_bare_calls_and_is_in(tmp_path):
    # A bare name that resolves to a zero-argument block or intrinsic is a
    # call, in statement and value position; `is [not] in` is the tree test.
    out = _play(tmp_path, GAME, "push bell\n")
    assert "Hooray." in out
    assert "In the box." in out
    assert "Not loose." in out
    assert "2 words." in out


def test_bare_call_with_params_errors():
    src = GAME.replace("        cheer\n", "        greet\n")
    with pytest.raises(ArcError) as e:
        generate(analyze(cosmos.combined_program(parse(src))))
    assert "takes 1 value(s); call it with (...)" in str(e.value)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_par_say_leads_with_a_break(tmp_path):
    src = GAME.replace(
        '        cheer\n',
        '        say.par "First."\n'
        '        par.say "Second."\n'
        '        par.say.par "Third."\n'
        '        say "Fourth."\n'
        '        cheer\n',
    )
    out = _play(tmp_path, src, "push bell\n")
    body = out[out.index("First.") : out.index("Fourth.")]
    # one blank line between each paragraph, never two (pending collapses)
    assert body.count("\n\n") == 3
    assert "\n\n\n" not in body


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_banner_sits_under_the_status_bar(tmp_path):
    # With the statusline, the title is the line after the bar (no stray
    # blank, unlike Inform); without, the banner opens the screen.
    out = _play(tmp_path, "summon.statusline\n" + GAME, "quit\ny\n")
    lines = out.splitlines()
    bar = next(i for i, l in enumerate(lines) if "Lab" in l and "Moves" in l)
    assert lines[bar + 1].strip() == "S"
