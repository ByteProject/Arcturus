# test_vehicles.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""convey(vehicle, dest): move a vehicle the player rides. The player is
inside the vehicle in the object tree, so moving the vehicle moves the
player; convey refreshes `here` (the cached room a plain move leaves
stale, the vehicle trap Charles hit) and describes the arrival. Costs
nothing unless called (DCE)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "V"\n    start dock\n'
    'flag adrift\n'
    'room dock\n    name "Dock"\n    desc "Planks."\n    south reach\n'
    'room reach\n    name "Reach"\n    desc "Water."\n    south delta\n'
    'room delta\n    name "Delta"\n    desc "Reeds."\n'
    'thing boat of container in dock\n    name "boat"\n    open\n    fixed\n'
    'thing oar in boat\n    name "oar"\n'
    'verb "go2"\n    go2\n'
    'on go2\n    change adrift to true\n    say "Off."\n'
    'on each_turn\n'
    '    if adrift is true\n'
    '        let nxt = here.south\n'
    '        if nxt is nothing\n'
    '            change adrift to false\n'
    '        else\n'
    '            convey(boat, nxt)\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_convey_carries_the_player_and_refreshes_here(tmp_path):
    story = tmp_path / "v.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input="enter boat\ngo2\nz\nx oar\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    # the boat drifts Dock -> Reach -> Delta, carrying the player, and the
    # room re-describes each hop with the nested suffix
    assert "Reach (in the boat)" in out
    assert "Delta (in the boat)" in out
    # scope followed: the oar (inside the moving boat) is still examinable
    assert "oar" in out.lower()
    # here really moved: the old room is not what the player sees at the end
    assert out.rstrip().endswith(">") or "Delta" in out.split("Reach")[-1]


def test_convey_folds_away_unused():
    from arcturus.lower import LowerError  # noqa: F401
    plain = (
        'game\n    title "V"\n    start dock\n'
        'room dock\n    name "Dock"\n    desc "Planks."\n'
        'thing rock in dock\n    name "rock"\n'
    )
    convey = plain + (
        'room reach\n    name "Reach"\n    desc "W."\n'
        'thing boat of container in dock\n    name "boat"\n    open\n    fixed\n'
        'verb "go2"\n    go2\n'
        'on go2\n    convey(boat, reach)\n'
    )
    a = generate(analyze(cosmos.combined_program(parse(plain))))
    b = generate(analyze(cosmos.combined_program(parse(convey))))
    assert len(a) < len(b)  # the caller pays; the plain game does not
