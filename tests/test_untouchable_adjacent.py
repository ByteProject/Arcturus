# test_untouchable_adjacent.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Place-by-place scope (docs/01 chapter 7; improvmonster's request,
2026-11-12, named by Stefan): `untouchable from balcony` brings a thing,
or a holder's whole contents, into scope at places it does not sit in,
seen and not touched; `adjacent to hatch` does the same within reach. In
its own home the thing stays ordinary. make_untouchable / make_adjacent
and `change x.untouchable to ...` set one place at run time; nothing
clears it. Backstage `in scope` is unchanged."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_build(src)), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def _after(out, cmd):
    return out.split(">" + cmd)[1].split(">")[0]


GAME = (
    'game\n    title "T"\n    start balcony\n'
    'room balcony\n    name "Balcony"\n    desc "High up."\n    down courtyard\n'
    'room courtyard\n    name "Courtyard"\n    desc "Paved."\n    up balcony\n'
    '    untouchable from balcony\n'
    'thing fountain of supporter in courtyard\n    name "fountain"\n    words fountain\n    fixed\n'
    'thing coin in fountain\n    name "coin"\n    words coin\n'
    'thing box of container in courtyard\n    name "box"\n    words box\n    openable\n'
    'thing pearl in box\n    name "pearl"\n    words pearl\n'
    'thing urn of container in courtyard\n    name "urn"\n    words urn\n    open\n'
    'thing ash in urn\n    name "ash"\n    words ash\n'
    'thing gardener of character in courtyard\n    name "gardener"\n    words gardener\n'
    'thing hat in gardener\n    name "hat"\n    words hat\n    exposed\n'
    'thing purse in gardener\n    name "purse"\n    words purse\n'
    'room pantry\n    name "Pantry"\n    desc "Shelves."\n    east hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    west pantry\n'
    'thing hatch of supporter in pantry\n    name "hatch"\n    words hatch\n    fixed\n'
    '    adjacent to hall\n'
    'thing pie in hatch\n    name "pie"\n    words pie\n'
)


def test_seen_from_the_balcony_and_never_touched():
    out = _run(GAME, ["examine fountain", "examine coin", "take coin",
                      "push fountain"])
    assert "nothing of the sort" not in _after(out, "examine fountain")
    assert "nothing of the sort" not in _after(out, "examine coin")
    assert "The coin is beyond your reach." in _after(out, "take coin")
    assert "beyond your reach" in _after(out, "push fountain")


def test_at_home_it_is_an_ordinary_thing():
    out = _run(GAME, ["down", "take coin"])
    assert "You take the coin with you." in out


def test_the_view_stops_where_the_eye_does():
    out = _run(GAME, ["examine pearl", "examine ash", "examine hat",
                      "examine purse"])
    # a shut box hides its pearl; an open urn shows its ash
    assert "nothing of the sort" in _after(out, "examine pearl")
    assert "nothing of the sort" not in _after(out, "examine ash")
    # a character's exposed belonging shows, a private one does not
    assert "nothing of the sort" not in _after(out, "examine hat")
    assert "nothing of the sort" in _after(out, "examine purse")


def test_the_balcony_does_not_list_the_courtyard():
    out = _run(GAME, ["look"])
    assert "coin" not in _after(out, "look")


def test_adjacent_is_in_reach():
    src = GAME.replace("start balcony", "start hall")
    out = _run(src, ["examine pie", "take pie"])
    assert "You take the pie with you." in out


DROID = (
    'game\n    title "T"\n    start lab\n'
    'room lab\n    name "Lab"\n    desc "White."\n'
    'room vault\n    name "Vault"\n    desc "Dark steel."\n'
    'thing droid of character in lab\n    name "droid"\n    words droid\n'
    'thing chip in vault\n    name "chip"\n    words chip\n'
    'verb "hatch"\n    hatch\n'
    'on hatch\n'
    '    if chip.untouchable is nothing\n'
    '        make_untouchable(chip, droid)\n'
    '        say "Panel open."\n'
    '    else\n'
    '        change chip.untouchable to nothing\n'
    '        say "Panel shut."\n'
)


def test_a_place_can_be_an_object_and_set_at_run_time():
    out = _run(DROID, ["examine chip", "hatch", "examine chip", "take chip",
                       "hatch", "examine chip"])
    parts = out.split(">examine chip")
    assert "nothing of the sort" in parts[1]
    assert "nothing of the sort" not in parts[2]
    assert "The chip is beyond your reach." in out
    assert "nothing of the sort" in parts[3]


def test_two_views_that_name_each_other_never_hang():
    src = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'room far\n    name "Far"\n    desc "Far."\n'
        'thing a in far\n    name "alpha"\n    words alpha\n    untouchable from b\n'
        'thing b in far\n    name "beta"\n    words beta\n    untouchable from a\n'
    )
    out = _run(src, ["examine alpha", "look"])
    assert "Hall" in _after(out, "look")


def test_reading_a_declared_list_gives_its_first_place():
    src = GAME + (
        'thing marker in balcony\n    name "marker"\n    words marker\n'
        '    untouchable from courtyard, hall\n'
        'verb "probe"\n    probe\n'
        'on probe\n    say "First: ${marker.untouchable}."\n'
    )
    out = _run(src, ["probe"])
    assert "First: Courtyard." in out


@pytest.mark.parametrize("line, msg", [
    ("    untouchable\n", "names the places it is seen from"),
    ("    untouchable balcony\n", "names the places it is seen from"),
    ("    adjacent hall\n", "names the places it is reached from"),
    ('    untouchable from "the balcony"\n', "names places: rooms or objects"),
])
def test_the_declaration_says_where_from(line, msg):
    src = GAME.replace("    untouchable from balcony\n", line)
    with pytest.raises(ArcError, match=msg):
        _build(src)


def test_a_bare_untouchable_points_to_beyond():
    src = GAME.replace("    untouchable from balcony\n", "    untouchable\n")
    with pytest.raises(ArcError, match="beyond"):
        _build(src)


def test_a_run_time_write_names_the_object():
    src = DROID.replace("make_untouchable(chip, droid)",
                        "let x = chip\n        make_untouchable(x, droid)")
    with pytest.raises(ArcError, match="needs the object by name"):
        _build(src)


WHY = GAME.replace(
    "    untouchable from balcony\n",
    '    untouchable from balcony "The courtyard is two floors down."\n')


def test_the_declared_text_speaks_the_refusal():
    out = _run(WHY, ["take coin", "push fountain", "examine coin"])
    assert "The courtyard is two floors down." in _after(out, "take coin")
    assert "The courtyard is two floors down." in _after(out, "push fountain")
    assert "nothing of the sort" not in _after(out, "examine coin")


def test_at_home_the_text_never_speaks():
    out = _run(WHY, ["down", "take coin"])
    assert "You take the coin with you." in out
    assert "two floors down" not in out


def test_the_things_own_text_wins_over_its_holders():
    src = WHY.replace(
        'thing coin in fountain\n    name "coin"\n    words coin\n',
        'thing coin in fountain\n    name "coin"\n    words coin\n'
        '    untouchable from balcony "The coin glints far below."\n')
    out = _run(src, ["take coin", "push fountain"])
    assert "The coin glints far below." in _after(out, "take coin")
    assert "The courtyard is two floors down." in _after(out, "push fountain")


def test_without_a_text_the_beyond_line_speaks():
    out = _run(GAME, ["take coin"])
    assert "The coin is beyond your reach." in out


def test_a_run_time_place_keeps_the_declared_text():
    src = DROID.replace(
        'thing chip in vault\n    name "chip"\n    words chip\n',
        'thing chip in vault\n    name "chip"\n    words chip\n'
        '    untouchable from vault "The chip sits deep behind the panel."\n')
    # the declared place (the vault) reads as set, so the first press
    # clears it and the second sets the droid
    out = _run(src, ["hatch", "hatch", "examine chip", "take chip"])
    assert "nothing of the sort" not in _after(out, "examine chip")
    assert "The chip sits deep behind the panel." in _after(out, "take chip")
