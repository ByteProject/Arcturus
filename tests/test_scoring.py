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
        [_frotz(), "-p", "-w", "500", str(story)],
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
def test_scoreless_game_says_so(tmp_path):
    # No scoring meta, no awards: SCORE answers honestly instead of
    # "0 of a possible 0" (Stefan's ruling, 2026-07-04).
    src = (
        'game\n    title "NS"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
    )
    out = _play(tmp_path, src, "score\n")
    assert "does not keep score" in out
    assert "0 of a possible" not in out


def test_score_reports_turns(tmp_path):
    # SCORE is the one score verb, Infocom-shaped: score, maximum, and the
    # turn count in one line (Stefan's ruling, 2026-07-04; there is no FULL).
    out = _play(tmp_path, GAME, "push panel\nscore\nwait\nscore\n")
    assert "in 1 turn," in out  # the singular branch
    assert "in 2 turns," in out


def test_gain_pays_a_scored_thing_once(tmp_path):
    # The Cosmos gain(obj), teleport's sibling: a cutscene handover pays the
    # thing's points once and marks it moved and seen; a second gain (or a
    # later real TAKE) pays nothing. move alone would pay nothing at all.
    src = GAME.replace(
        'verb "meditate"',
        'verb "bestow"\n    bestow\n\non bestow\n    gain(coin)\n    say "Bestowed."\n\nverb "meditate"',
    )
    out = _play(tmp_path, src, "bestow\nscore\ndrop coin\ntake coin\nscore\n")
    assert "scored 5 of a possible" in out
    assert out.count("Bestowed.") == 1
    assert "scored 10 " not in out  # neither the re-take nor a re-gain pays


def test_teleport_pays_a_scored_room_once(tmp_path):
    # The Cosmos teleport(dest): a cutscene arrival in a scored room pays
    # its points exactly once, marks it visited, and describes it, so a
    # bypassed GO never strands max_score points.
    src = GAME.replace(
        'verb "meditate"',
        'verb "warp"\n    warp\n\non warp\n    teleport(yard)\n\nverb "meditate"',
    )
    out = _play(tmp_path, src, "warp\nscore\ns\nwarp\nscore\n")
    assert out.count("Yard\nA yard.") == 2  # described on each arrival
    assert "scored 5 of a possible" in out
    assert "scored 10 " not in out  # the second warp pays nothing


def test_stats_carry_the_plan(tmp_path):
    stats = {}
    generate(analyze(cosmos.combined_program(parse(GAME))), stats=stats)
    assert stats["max_score"] == 23
    assert stats["award_pools"] == 1
    assert stats["award_sites"] == 1
    assert stats["ranks"] == 3
