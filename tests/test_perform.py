# test_perform.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""perform("take", book): run an action as part of the current turn, the
way the player's own command would dispatch it (Inform's <<take book>>,
Dialog's (try ...)). The full pipeline runs (refusals, handlers, messages,
the after phase); a direction rides the way slot (perform("go", west));
the enclosing command's operands are restored; the return value is 1
unless the performed action refused. Costs nothing unless called (DCE)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, cmds):
    return subprocess.run(
        [_frotz(), "-p", "-w", "80", str(story)],
        input=cmds, capture_output=True, text=True, timeout=15,
    ).stdout


GAME = (
    'game\n    title "P"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "Bare."\n    east yard\n'
    'room yard\n    name "Yard"\n    desc "Green."\n    west hall\n'
    'thing book in hall\n    name "book"\n'
    'thing anvil in hall\n    name "anvil"\n    fixed\n'
    'thing bob of character in hall\n    name "Bob"\n    named\n'
    'verb "grab"\n    grab\n'
    'on grab\n'
    '    if perform("take", book) is 1\n'
    '        say "(carried)"\n'
    '    if perform("take", anvil) is 0\n'
    '        say "(refused, and the turn goes on)"\n'
    'verb "flee"\n    flee\n'
    'on flee\n'
    '    perform("go", east)\n'
    'verb "donate"\n    donate\n'
    'on donate\n'
    '    perform("take", book)\n'
    '    perform("give", book, bob)\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_perform_runs_the_full_pipeline(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "grab\ni\n")
    assert "Got it." in out                       # the action's own message
    assert "(carried)" in out                     # success returns 1
    assert "exactly where it is" in out           # the refusal message ran
    assert "(refused, and the turn goes on)" in out
    assert "a book" in out.split("carrying")[-1]  # and the book is held


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_perform_go_rides_the_way_slot(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "flee\n")
    assert "Yard" in out and "Green." in out      # a full move with arrival


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_perform_two_nouns(tmp_path):
    # The second noun lands: Bob's default give refusal names both operands
    # (characters decline gifts unless a handler accepts; the message IS
    # the proof the full two-noun pipeline ran).
    story = tmp_path / "p.z5"
    story.write_bytes(_build(GAME))
    out = _run(story, "donate\n")
    assert "Bob doesn't want the book." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_perform_restores_the_outer_operands(tmp_path):
    # AGAIN replays what the player typed, not what perform dispatched: the
    # outer command's operands survive the inner action.
    src = GAME.replace(
        'verb "grab"\n    grab\n',
        'verb "grab"\n    grab noun\n',
    ).replace(
        'on grab\n',
        'on grab\n'
        '    say "Grabbing ${the noun}."\n',
    )
    story = tmp_path / "p.z5"
    story.write_bytes(_build(src))
    out = _run(story, "grab bob\nagain\n")
    assert out.count("Grabbing Bob.") == 2        # noun survived perform


def test_perform_unknown_action_is_a_compile_error():
    src = GAME.replace('perform("take", book)', 'perform("teka", book)', 1)
    with pytest.raises(Exception, match="unknown action"):
        _build(src)
