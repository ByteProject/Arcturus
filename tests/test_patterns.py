# test_patterns.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Operand patterns in handler headers (docs/01 section 12): `on put ruby in
chest` fires for exactly that pairing, `or` lists alternatives, a failed
pattern falls through to the next handler and the defaults, an all-guarded
group still reaches the object's `on other`, and patterns compose with the
after phase. Found documented-but-undispatched on 2026-07-04 (codegen
silently skipped every non-direction pattern); these pin the real thing.
Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, src, script):
    story = tmp_path / "p.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(src)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15,
    ).stdout


GAME = (
    'game\n    title "Patterns"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A hall."\n'
    'thing chest of container in hall\n    name "oak chest"\n    words oak, chest\n'
    "    open\n    fixed\n"
    'thing box of container in hall\n    name "tin box"\n    words tin, box\n'
    "    open\n    fixed\n"
    'thing ruby in hall\n    name "ruby"\n    words ruby\n'
    "    on put ruby in chest\n"
    '        say "The chest glows around the ruby."\n'
    'thing ring in hall\n    name "ring"\n    words ring\n'
    'thing idol in hall\n    name "idol"\n    words idol\n'
    "    on give idol or ring to keeper\n"
    '        say "The keeper accepts the offering."\n'
    "    on other\n"
    '        say "The idol radiates disapproval."\n'
    'thing keeper of character in hall\n    name "keeper"\n    words keeper\n'
)


def test_patterns_compile():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_pattern_matches_exact_pairing(tmp_path):
    out = _play(tmp_path, GAME, "take ruby\nput ruby in chest\n")
    assert "The chest glows around the ruby." in out
    assert "Done." not in out  # the handler replaced the default put


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_pattern_mismatch_falls_to_the_default(tmp_path):
    # Same noun, other container: the guard fails, the default put runs.
    out = _play(tmp_path, GAME, "take ruby\nput ruby in box\n")
    assert "Done." in out
    assert "glows" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_or_alternatives_share_one_handler(tmp_path):
    out = _play(
        tmp_path, GAME,
        "take idol\ngive idol to keeper\ntake ring\ngive ring to keeper\n",
    )
    # The idol's handler names both alternatives; it owns the idol's give
    # and, via the noun slot... the ring is NOT the idol's noun, so only
    # the idol's own give matches here.
    assert out.count("accepts the offering") == 1


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_failed_guard_still_reaches_on_other(tmp_path):
    # The idol's only specific give-handler is guarded on the keeper. The
    # catch-all answers TAKE (no specific handler), PUSH, and crucially GIVE
    # IDOL TO RING: the pattern guard fails, so the object never addressed
    # the give, and the catch-all gets its turn (the all-guarded rule, the
    # same behavior the direction guards always had). It ends without
    # continue, so it consumes each action.
    out = _play(tmp_path, GAME, "take idol\npush idol\ngive idol to ring\n")
    assert out.count("radiates disapproval") == 3
    assert "Got it." not in out  # the catch-all consumed the take too


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_pattern_composes_with_after(tmp_path):
    src = (
        'game\n    title "AfterPat"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing chest of container in hall\n    name "chest"\n    words chest\n'
        "    open\n    fixed\n"
        'thing ruby in hall\n    name "ruby"\n    words ruby\n'
        "    on after put ruby in chest\n"
        '        say "The chest hums approvingly."\n'
        'thing coin in hall\n    name "coin"\n    words coin\n'
    )
    out = _play(
        tmp_path, src,
        "take ruby\nput ruby in chest\ntake coin\nput coin in chest\n",
    )
    # The default put runs both times; only the matching pair hums, after.
    assert out.count("Done.") == 2
    assert out.count("hums approvingly") == 1
    assert out.index("Done.") < out.index("hums approvingly")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_free_patterned_rule(tmp_path):
    src = (
        'game\n    title "FreePat"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing bell in hall\n    name "bell"\n    words bell\n'
        'thing book in hall\n    name "book"\n    words book\n'
        "on take bell\n"
        '    say "A free rule rings."\n'
        "    continue\n"
    )
    out = _play(tmp_path, src, "take book\ntake bell\n")
    assert out.count("Got it.") == 2  # both takes complete
    assert out.count("free rule rings") == 1  # only the bell's

@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_direction_or_alternatives(tmp_path):
    # `on go south or up` (H2's fallen-shaft shape): one handler answers
    # both directions and no others.
    src = (
        'game\n    title "DirPat"\n    start pit\n'
        'room pit\n    name "The Pit"\n    desc "Smooth walls."\n'
        "    north hall\n"
        "    on go south or up\n"
        '        say "The walls are too smooth to climb."\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n    south pit\n'
    )
    out = _play(tmp_path, src, "south\nup\nnorth\n")
    assert out.count("too smooth to climb") == 2
    assert "Hall" in out  # north still leaves normally


def test_comma_in_a_pattern_is_a_named_error(tmp_path):
    src = (
        'game\n    title "CommaPat"\n    start pit\n'
        'room pit\n    name "The Pit"\n    desc "Walls."\n'
        "    on go south, up\n"
        '        say "no"\n'
    )
    with pytest.raises(Exception) as e:
        generate(analyze(cosmos.combined_program(parse(src))))
    assert "join" in str(e.value) and "'or'" in str(e.value)
