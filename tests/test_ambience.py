# test_ambience.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The ambience granule (summon.ambience): rooms and things murmur over time.
Cadence (about/every), written order with once, block and per-line when
guards, do-lines, the ambience_rate dial, and the summon gate. Deterministic
tests use `every`; `about` rides the interpreter's random and is smoke-tested
only for silence when muted."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    "summon.ambience\n"
    'game\n    title "A"\n    start hall\n'
    "global storm = false\n"
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    "    ambience every 2 turns\n"
    '        "A shutter bangs somewhere upstairs."\n'
    '        "Dust sifts from the rafters." when storm\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    "    south hall\n"
    "    ambience every 2 turns in order once\n"
    '        "First the birds fall silent."\n'
    '        "Then the light goes strange."\n'
    "        do last_line\n"
    'thing radio in hall\n    name "radio"\n    words radio\n'
    "    switchable\n"
    "    powered false\n"
    "    ambience every 2 turns when self is powered\n"
    '        "The radio crackles through dead frequencies."\n'
    "    on switch_on\n"
    "        now self is powered\n"
    '        say "Click."\n'
    'verb "hush"\n    hush\n'
    "on hush\n"
    "    change ambience_rate to 0\n"
    '    say "Hushed."\n'
    "block last_line()\n"
    '    say "And then, nothing at all."\n'
)

WAITS = "wait\n" * 12


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "a.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_every_cadence_and_line_guard(tmp_path):
    # The strict clock fires; the guarded line stays silent while storm is
    # false. With one eligible line and a one-line no-repeat exemption for
    # single... the single eligible line repeats (count > 1 exempts nothing
    # here: the OTHER line is guard-dead, so the eligible one is retried).
    out = _play(tmp_path, GAME, WAITS)
    assert out.count("A shutter bangs") >= 2
    assert "Dust sifts" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_in_order_once_with_do_line(tmp_path):
    # The yard tells its three lines in written order (the third computed by
    # a do-block), then falls silent forever.
    out = _play(tmp_path, GAME, "n\n" + WAITS + WAITS)
    assert out.index("First the birds") < out.index("light goes strange")
    assert out.index("light goes strange") < out.index("nothing at all")
    assert out.count("First the birds") == 1
    assert out.count("nothing at all") == 1


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_room_blocks_stay_home(tmp_path):
    # The hall's lines never play in the yard.
    out = _play(tmp_path, GAME, "n\n" + WAITS)
    assert "A shutter bangs" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_thing_block_gated_on_state(tmp_path):
    # The radio murmurs only once switched on (its block guard).
    quiet = _play(tmp_path, GAME, WAITS)
    assert "crackles" not in quiet
    loud = _play(tmp_path, GAME, "switch on radio\n" + WAITS)
    assert "crackles" in loud


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_rate_zero_mutes_everything(tmp_path):
    out = _play(tmp_path, GAME, "hush\n" + WAITS)
    assert "Hushed." in out
    assert "A shutter bangs" not in out


def test_ambience_without_summon_is_an_error(tmp_path):
    src = (
        'game\n    title "N"\n    start r\n'
        'room r\n    name "R"\n    desc "A room."\n'
        "    ambience\n"
        '        "A draught."\n'
    )
    with pytest.raises(ArcError, match="summon.ambience"):
        analyze(cosmos.combined_program(parse(src)))


# The granule adds its own free `on each_turn` (the ambience pulse). A game's
# OWN free `on each_turn` must still fire alongside it: life-cycle events are
# pulses every hook shares, not player actions the first handler consumes.
# Regressed a reporter's "summon.ambience turns off bare each_turns"
# (2026-07-05): free life-cycle handlers used to consume-chain, so the first
# to return (a bare handler returns 1 by default) silenced the rest.
COEXIST = (
    "summon.ambience\n"
    'game\n    title "Coexist"\n    start hall\n'
    'on each_turn\n    say "TICK"\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    ambience every 1 turns\n"
    '        "A shutter bangs."\n'
    'thing coin in hall\n    name "coin"\n    words coin\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_bare_each_turn_coexists_with_ambience(tmp_path):
    out = _play(tmp_path, COEXIST, "wait\nwait\nwait\n")
    # The game's own pulse fires every turn...
    assert out.count("TICK") == 3
    # ...and the ambience block still murmurs on its clock (every turn here),
    # which it could not do while the bare each_turn consumed the pulse.
    assert out.count("A shutter bangs.") >= 2


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_multiple_free_each_turn_rules_all_fire(tmp_path):
    # Two bare `on each_turn` rules, no granule: both fire every turn. A
    # life-cycle pulse is never consumed by one hook to the exclusion of
    # the next.
    src = (
        'game\n    title "TwoPulse"\n    start hall\n'
        'on each_turn\n    say "ALPHA"\n'
        'on each_turn\n    say "BETA"\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
    )
    out = _play(tmp_path, src, "wait\nwait\n")
    assert out.count("ALPHA") == 2
    assert out.count("BETA") == 2
