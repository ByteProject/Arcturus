# test_catalogs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Catalogs (Stefan's star-catalog naming; the Dialog-lists request from
Charles Moore Jr. and Ichiro Ota, built the Arcturus way): a fixed ordered
collection declared once, one type of entry per catalog, laid out as a
static table in dynamic memory. calculate folds to a constant, entry/last
are one loadw, dice rides random, position (and `in`, which shares its
block) scan, change entry(...) is one storew, for each iterates, and a
catalog passes to a block as its offset. No heap anywhere; a game with no
catalog is byte-identical (the untouched ceilings)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start study\n'
    'summon.quotes\n'
    'catalog letter\n'
        '    "To be read when I am gone:"\n'
    '    "The garden knows. Dig nowhere."\n'
    '    "E. Mereweather"\n'
    'catalog primes\n'
    '    2\n'
    '    3\n'
    '    5\n'
    '    7\n'
    'catalog suspects\n'
    '    butler\n'
    '    gardener\n'
    'room study\n    name "Study"\n    desc "Shelves."\n'
    'thing butler of character in study\n    name "butler"\n    words butler\n'
    'thing gardener of character in study\n    name "gardener"\n    words gardener\n'
    'block read_out(cat)\n'
    '    say entry(cat, 2)\n'
    'verb "audit"\n    audit\n'
    'on audit\n'
    '    say "count ${calculate(letter)} / ${calculate(primes)}"\n'
    '    say "entry3: ${entry(letter, 3)}"\n'
    '    say "last: ${last(primes)}"\n'
    '    say "pos gardener: ${position(suspects, gardener)}"\n'
    '    say "pos player: ${position(suspects, player)}"\n'
    '    if butler in suspects\n'
    '        say "butler listed"\n'
    '    if not (player in suspects)\n'
    '        say "player unlisted"\n'
    '    let d = dice(primes)\n'
    '    if position(primes, d) > 0\n'
    '        say "dice landed on the table"\n'
    '    show("via block: ")\n'
    '    read_out(letter)\n'
    '    for each n in primes\n'
    '        show(n)\n'
    '        show(" ")\n'
    '    say ""\n'
    '    for each line in letter\n'
    '        say line\n'
    'verb "appeal"\n    appeal\n'
    'on appeal\n'
    '    change entry(letter, 3) to "Pardoned."\n'
    '    change entry(primes, 4) to 11\n'
    '    say "entry3 now: ${entry(letter, 3)}; last prime ${last(primes)}"\n'
    'verb "poster"\n    poster\n'
    'on poster\n'
    '    quote_catalog(letter)\n'
    '    say "posted"\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_reads_folds_and_scans():
    out = _run(["audit"])
    assert "count 3 / 4" in out
    assert "entry3: E. Mereweather" in out
    assert "last: 7" in out
    assert "pos gardener: 2" in out
    assert "pos player: 0" in out
    assert "butler listed" in out
    assert "player unlisted" in out
    assert "dice landed on the table" in out
    assert "via block: The garden knows. Dig nowhere." in out
    assert "2 3 5 7" in out
    assert "To be read when I am gone:\nThe garden knows. Dig nowhere.\nE. Mereweather" in out


def test_change_entry_rewrites_in_place():
    out = _run(["appeal", "audit"])
    assert "entry3 now: Pardoned.; last prime 11" in out
    assert "entry3: Pardoned." in out  # it stuck


import shutil
import subprocess


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_quote_catalog_draws_the_box(tmp_path):
    # The box paints the upper window and waits for a key, so this one
    # plays on dfrotz rather than the capture harness.
    story = tmp_path / "c.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", "-w", "120", str(story)],
        input="poster\n \nquit\ny\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "The garden knows. Dig nowhere." in out
    assert "posted" in out


def test_mixed_catalog_is_refused():
    bad = ('game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "D."\n'
           'catalog odd\n    "text"\n    7\n')
    with pytest.raises(Exception) as e:
        analyze(cosmos.combined_program(parse(bad)))
    assert "mixes" in str(e.value)
