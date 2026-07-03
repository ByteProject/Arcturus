# test_scoring.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Scoring (docs/01): score just works. `scoring` in the game block makes
every room pay on first visit and every takeable thing on first take (except
the start room and start inventory; `scored false` opts out); `award N`
covers events, `award N for <pool>` makes branches count once at their
maximum; the compiler sums max_score; a bare `ranks` ladder spreads itself
over the max and the score verb announces the rank."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "S"\n    start hall\n    scoring\n'
    "global hacked = false\n"
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    "    south hall\n"
    "    east shed\n"
    'room shed\n    name "Shed"\n    desc "A shed."\n'
    "    scored false\n"
    "    west yard\n"
    'thing coin in hall\n    name "coin"\n    words coin\n'
    'thing pebble in hall\n    name "pebble"\n    words pebble\n'
    "    scored false\n"
    'thing statue in hall\n    name "statue"\n    words statue\n    fixed\n'
    'thing torch in player\n    name "torch"\n    words torch\n'
    'thing door_thing in hall\n    name "door panel"\n    words panel\n'
    "    fixed\n"
    "    on push\n"
    "        if hacked\n"
    "            award 10 for door_solved \"outsmarting the door\"\n"
    "        else\n"
    "            award 5 for door_solved \"outsmarting the door\"\n"
    '        say "The panel yields."\n'
    'verb "meditate"\n    meditate\n'
    "on meditate\n"
    "    award 3\n"
    '    say "Insight arrives."\n'
    "ranks\n"
    '    "Novice"\n'
    '    "Adept"\n'
    '    "Master"\n'
)
# The sum the compiler should reach: coin 5 + yard 5 (hall is start, shed
# and pebble opted out, statue fixed, torch starts held) + pool max 10 +
# anonymous 3 = 23.


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "s.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_max_score_sums_itself(tmp_path):
    out = _play(tmp_path, GAME, "score\n")
    assert "of a possible 23" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_auto_rooms_and_things_with_exclusions(tmp_path):
    # coin pays, pebble (opted out) does not, torch (start inventory) does
    # not; yard pays, shed (opted out) does not, hall (start) does not.
    out = _play(
        tmp_path, GAME,
        "take coin\ntake pebble\ndrop torch\ntake torch\nn\ne\nscore\n",
    )
    assert "scored 10 of a possible 23" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_award_pays_once(tmp_path):
    out = _play(tmp_path, GAME, "meditate\nmeditate\nscore\n")
    assert "scored 3 of" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_pool_pays_first_branch_only(tmp_path):
    # The 5-point branch fires first; the pool is spent, the 10-point branch
    # can never add more. Max still counted the pool once, at 10.
    out = _play(tmp_path, GAME, "push panel\npush panel\nscore\n")
    assert "scored 5 of a possible 23" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_rank_pins_points_and_percent(tmp_path):
    # A definite pin sits verbatim; a percent pin scales with the max (23):
    # 50 percent of 23 = 11.
    src = GAME.replace(
        'ranks\n    "Novice"\n    "Adept"\n    "Master"\n',
        'ranks\n    "Novice"\n    "Adept" at 8 points\n    "Master" at 50 percent\n',
    )
    out = _play(tmp_path, src, "take coin\nmeditate\nscore\nn\nscore\n")
    # 8 points (coin + award 3) = Adept exactly at its definite pin;
    # 13 points passes 11 (50 percent) = Master.
    assert "rank of Adept" in out
    assert "rank of Master" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_ranks_announced_and_spread(tmp_path):
    # Three ranks over max 23: thresholds 0, 11, 23. Score 0 = Novice;
    # 13 points = Adept.
    out = _play(
        tmp_path, GAME,
        "score\ntake coin\nn\nmeditate\nscore\n",
    )
    assert "rank of Novice" in out
    assert "rank of Adept" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_full_score_breakdown(tmp_path):
    src = GAME.replace('game\n    title "S"', "summon.extendedverbs\ngame\n    title \"S\"")
    out = _play(tmp_path, src, "push panel\nfull\n")
    assert "5 points, for outsmarting the door" in out


def test_stats_carry_the_plan(tmp_path):
    stats = {}
    generate(analyze(cosmos.combined_program(parse(GAME))), stats=stats)
    assert stats["max_score"] == 23
    assert stats["award_pools"] == 1
    assert stats["award_sites"] == 1
    assert stats["ranks"] == 3
