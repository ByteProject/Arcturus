# test_quotes.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The quotes granule (the centered reverse-video quote box) and the banner
control it pairs with: `banner false` stops the automatic banner, and
print_banner() shows it when the author wants it."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Q"\n    headline "H"\n    author "A"\n    start r\n'
    "    banner false\n"
    "summon.quotes\n"
    "on start\n"
    "    quote(2, 20)\n"
    "    quote_line()\n"
    '    show("The quoted line.")\n'
    "    quote_line()\n"
    '    show("      -- Author")\n'
    "    quote_done()\n"
    "    print_banner()\n"
    '    say "After the banner."\n'
    'room r\n    name "R"\n    desc "A room."\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_quote_box_then_banner_on_frotz(tmp_path):
    story = tmp_path / "q.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=" \nquit\ny\n",  # the keypress that closes the box, then quit
        capture_output=True, text=True, timeout=15,
    ).stdout
    # The quote shows, and the banner arrives AFTER it (the Trinity order).
    assert "The quoted line." in out
    assert "H by A" in out
    assert out.index("The quoted line.") < out.index("H by A")
    assert "After the banner." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_banner_false_without_print_banner_suppresses_it(tmp_path):
    # H2's "return 2" pattern: banner false and no print_banner() call anywhere
    # means the banner never prints (and DCE drops the banner routine).
    src = (
        'game\n    title "Q"\n    headline "NEVERSHOWN"\n    author "A"\n'
        "    start r\n    banner false\n"
        'on start\n    say "Straight into the story."\n'
        'room r\n    name "R"\n    desc "A room."\n'
    )
    story = tmp_path / "n.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(src)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="quit\ny\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Straight into the story." in out
    assert "NEVERSHOWN" not in out
