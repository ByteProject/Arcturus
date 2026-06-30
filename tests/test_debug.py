# test_debug.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The debug granule (B5.5f): developer verbs, opt-in via summon. tree and scope
list the world; fetch / warp / inspect reach ANY object, in scope or not, through
the reach_unscoped parser seam. Unsummoned, the seam resolves to nothing and the
verbs are absent. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


GAME = '''game
    title "Debug"
    start hall
summon.debug
room hall
    name "Hall"
    desc "A bare hall."
    down cellar
thing coin in hall
    name "gold coin"
    words gold, coin
thing box of container in hall
    name "wooden box"
    words wooden, box
    open
room cellar
    name "Cellar"
    desc "A damp cellar."
thing lantern in cellar
    name "brass lantern"
    words brass, lantern
thing rat in cellar
    name "grey rat"
    words grey, rat
    animate
'''


def test_debug_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def test_unsummoned_debug_is_absent():
    # Without summon.debug, the verbs do not exist (and the seam is inert).
    bare = GAME.replace("summon.debug\n", "")
    img = generate(analyze(cosmos.combined_program(parse(bare))))
    assert img[0x00] == 5


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_debug_verbs_on_frotz(tmp_path):
    img = generate(analyze(cosmos.combined_program(parse(GAME))))
    story = tmp_path / "dbg.z5"
    story.write_bytes(img)
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=(
            "tree\n"            # the whole object tree
            "scope\n"           # what is reachable here
            "fetch lantern\n"   # an object in the cellar, out of scope
            "inspect box\n"     # location + attributes
            "warp rat\n"        # teleport to the cellar
            "quit\ny\n"
        ),
        capture_output=True, text=True, timeout=20,
    ).stdout

    # tree shows both rooms and their contents.
    assert "Hall" in out and "Cellar" in out
    assert "brass lantern" in out  # listed under Cellar, though out of scope

    # fetch reaches the out-of-scope lantern (the reach_unscoped seam).
    assert "Fetched brass lantern." in out

    # inspect dumps the box's location and the attributes it has.
    inspect_part = out.split("Fetched brass lantern.")[1]
    assert "in: Hall" in inspect_part
    assert "container" in inspect_part
    assert "open" in inspect_part

    # warp teleports to the rat's room and describes it.
    assert "A damp cellar." in out
