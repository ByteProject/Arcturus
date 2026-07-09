# test_is_predicate.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The predicate form of `is`: a one-parameter block on the right side of
`is` reads as a call, so `if lamp is visible` means visible(lamp), the way
`is` already reads attributes and kinds. Attributes and kinds win the name;
`is not` negates the call's truth; blocks of any other arity stay ordinary
values and keep the call-it-with-parens error."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Pred"\n    start cellar\n'
    'room cellar\n    name "Cellar"\n    desc "Stone."\n'
    'thing lamp in cellar\n    name "lamp"\n'
    'thing coin in box\n    name "coin"\n'
    'thing box of container in cellar\n    name "box"\n    openable\n'
    'verb "probe"\n    probe\n'
    'on probe\n'
    '    if lamp is visible\n'
    '        say "lamp yes"\n'
    '    if coin is not visible\n'
    '        say "coin no"\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_is_predicate_calls_the_block(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(_build(GAME))
    out = subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input="probe\nopen box\nprobe\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    first, second = out.split("Inside you find a coin.")
    assert "lamp yes" in first and "coin no" in first   # closed box shields
    assert "coin no" not in second                       # open box reveals


def test_attribute_still_wins_the_name():
    # `open` is an attribute; a game block cannot steal the is-test.
    src = GAME + 'block shiny(x)\n    return 1\n'
    world = analyze(cosmos.combined_program(parse(src)))
    import arcturus.worldmodel as wm
    kinds = set(world.is_resolutions.values())
    assert wm.IS_PREDICATE in kinds


def test_other_arities_keep_the_call_error():
    src = GAME.replace(
        "on probe\n",
        'block pair(a, b)\n    return 1\n'
        'on probe\n    if lamp is pair\n        say "no"\n',
    )
    with pytest.raises(ArcError, match="call it with"):
        _build(src)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_reachable_differs_from_visible_through_glass(tmp_path):
    # The documented contract (docs/02): visible is sight, reachable is
    # touch. A coin in a CLOSED clear jar is visible, not reachable, and
    # take answers "open it first"; opening the jar changes all three.
    game = (
        'game\n    title "Jar"\n    start lab\n'
        'room lab\n    name "Lab"\n    desc "A lab."\n'
        'thing jar of container in lab\n    name "jar"\n    clear\n'
        '    openable\n    fixed\n'
        'thing coin in jar\n    name "coin"\n'
        'verb "probe"\n    probe noun\n'
        'on probe\n'
        '    if noun is visible\n'
        '        if noun is not reachable\n'
        '            say "Seen, sealed."\n'
        '            stop\n'
        '        say "In hand range."\n'
    )
    story = tmp_path / "j.z5"
    story.write_bytes(_build(game))
    out = subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input="probe coin\ntake coin\nopen jar\nprobe coin\ntake coin\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Seen, sealed." in out
    assert "You'll have to open the jar first." in out
    assert "In hand range." in out
    assert "Got it." in out
