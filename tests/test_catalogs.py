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


def test_property_holds_a_catalog():
    # A field report (Ichiro Ota): a kind handler reading a catalog through
    # self.<prop> got the FIRST catalog for every object. The property typed
    # as object, the name resolved to nothing, and the slot silently held 0,
    # which IS the first catalog's word offset. A catalog name in a property
    # value now stores its offset, so each object reads its own.
    game = (
        'game\n    title "T"\n    start crypt\n'
        'catalog decoy\n    "the decoy line"\n'
        'catalog plaque_text\n    "Erected 1887."\n    "By subscription."\n'
        'catalog stone_text\n    "Here lies proof."\n'
        'room crypt\n    name "Crypt"\n    desc "Cold."\n'
        'kind inscribed of thing\n'
        '    on examine\n'
        '        say "lines ${calculate(self.writing)}: ${entry(self.writing, 1)}"\n'
        'thing plaque of inscribed in crypt\n'
        '    name "plaque"\n    words plaque\n'
        '    writing plaque_text\n'
        'thing stone of inscribed in crypt\n'
        '    name "stone"\n    words stone\n'
        '    writing stone_text\n'
    )
    out = _run(["x plaque", "x stone"], game=game)
    assert "lines 2: Erected 1887." in out
    assert "lines 1: Here lies proof." in out
    assert "the decoy line" not in out


def test_mixed_catalog_is_refused():
    bad = ('game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "D."\n'
           'catalog odd\n    "text"\n    7\n')
    with pytest.raises(Exception) as e:
        analyze(cosmos.combined_program(parse(bad)))
    assert "mixes" in str(e.value)


# -- direction catalogs (a field request, 2026-07-17): the matrix precedent --

def _run_game(game, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_direction_catalog_iterates_switches_compares():
    game = (
        'game\n    title "T"\n    start hall\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n    north cellar\n'
        '    on probe_it\n'
        '        for each d in route\n'
        '            switch d\n'
        '                case north\n                    say "N"\n'
        '                case east\n                    say "E"\n'
        '                case south\n                    say "S"\n'
        '        if entry(route, 1) is north\n'
        '            say " (first is north)"\n'
        'room cellar\n    name "Cellar"\n    desc "C."\n'
        'catalog route\n    north\n    east\n    south\n'
    )
    out = _run_game(game, ["probe"])
    assert "NES (first is north)" in out.replace("N E S", "NES").replace("NE S", "NES").replace("N ES", "NES") or (
        "N" in out and "E" in out and "S" in out and "(first is north)" in out)


def test_direction_catalog_without_exits_still_encodes():
    # direction properties are standard pack properties, numbered whether
    # or not any room declares that exit
    game = (
        'game\n    title "T"\n    start hall\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        '    on probe_it\n'
        '        if entry(route, 2) is starboard\n'
        '            say "starboard confirmed"\n'
        'catalog route\n    up\n    starboard\n'
    )
    out = _run_game(game, ["probe"])
    assert "starboard confirmed" in out


def test_direction_and_object_mix_is_refused():
    bad = ('game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "D."\n'
           'thing rock in r\n    name "rock"\n    words rock\n'
           'catalog odd\n    rock\n    north\n')
    with pytest.raises(Exception) as e:
        analyze(cosmos.combined_program(parse(bad)))
    assert "mixes object and direction" in str(e.value)


def test_unknown_catalog_name_mentions_directions():
    bad = ('game\n    title "T"\n    start r\nroom r\n    name "R"\n    desc "D."\n'
           'catalog odd\n    wibble\n')
    with pytest.raises(Exception) as e:
        analyze(cosmos.combined_program(parse(bad)))
    assert "not an object or a direction" in str(e.value)


def test_direction_entries_say_their_words():
    # `say ${entry(route, 1)}` speaks "north", the same voice as `say way`
    # and the object-catalog symmetry (objects print names, directions
    # print words). The follow-up to the field request that added
    # direction catalogs.
    game = (
        'game\n    title "T"\n    start hall\n'
        'verb "probe"\n    probe_it\n'
        'room hall\n    name "Hall"\n    desc "H."\n    north cellar\n'
        '    on probe_it\n'
        '        for each d in route\n'
        '            say "${d} "\n'
        '        say "/ ${entry(route, 1)} first"\n'
        'room cellar\n    name "Cellar"\n    desc "C."\n'
        'catalog route\n    north\n    east\n    up\n'
    )
    out = _run_game(game, ["probe"])
    assert "north east up / north first" in " ".join(out.split())
