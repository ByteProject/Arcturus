# test_session.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Record / replay / check (actaea/session.py): the Arcturus answer to
Inform's RECORDING and REPLAY, at the io boundary. A session records the
commands AND the game's replies to a readable file; replay feeds the
commands back; check re-runs them and reports, in plain words, whether the
game still plays the same, stopping at the first divergence. Driven here
through SessionIO over a scripted CaptureIO, the same boundary a front-end
uses."""

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.session import SessionIO, parse_walkthrough, _norm
from actaea.vm import VM

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "S"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A bare hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A grassy yard."\n    south hall\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp, brass\n'
)


def _story(src=GAME):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(story, io):
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except (IndexError, EOFError):
        pass  # the script (or a spent CaptureIO) ended the run


def _record(story, commands, path):
    """Play `commands` through a recording session, writing to `path`."""
    io = SessionIO(CaptureIO(script=list(commands)), record_path=str(path))
    _run(story, io)
    io.close()
    return io


def _check(story, path, report):
    with open(path, encoding="utf-8") as fh:
        intro, turns = parse_walkthrough(fh.read())
    io = SessionIO(CaptureIO(), check=(intro, turns), report=report.append)
    _run(story, io)
    io.close()
    return io


# -- recording ---------------------------------------------------------------

def test_record_writes_a_readable_walkthrough(tmp_path):
    path = tmp_path / "walk.txt"
    _record(_story(), ["take lamp", "north", "south"], path)
    text = path.read_text()
    # Commands are the editable spine, marked with "> ".
    assert "> take lamp" in text
    assert "> north" in text
    assert "> south" in text
    # The game's replies sit in the file too (so check has something to compare).
    assert "Got it." in text
    assert "A grassy yard." in text


def test_recorded_commands_parse_back_out(tmp_path):
    path = tmp_path / "walk.txt"
    _record(_story(), ["take lamp", "north"], path)
    _intro, turns = parse_walkthrough(path.read_text())
    assert [c for c, _ in turns] == ["take lamp", "north"]


# -- check: matches, and diverges --------------------------------------------

def test_check_passes_on_an_unchanged_game(tmp_path):
    path = tmp_path / "walk.txt"
    _record(_story(), ["take lamp", "north", "south"], path)
    report = []
    io = _check(_story(), path, report)
    assert not io.diverged
    assert report == []


def test_check_reports_the_first_divergence(tmp_path):
    path = tmp_path / "walk.txt"
    _record(_story(), ["take lamp", "north", "south"], path)
    # Change the yard's description; NORTH's reply now differs.
    changed = GAME.replace("A grassy yard.", "A muddy yard.")
    report = []
    io = _check(_story(changed), path, report)
    assert io.diverged
    joined = "\n".join(report)
    assert "north" in joined            # names the command that broke
    assert "A grassy yard." in joined   # shows the before
    assert "A muddy yard." in joined    # shows the now
    assert "diverged" in joined


def test_check_stops_at_the_first_divergence(tmp_path):
    # Two independent changes; only the first is reported (state has moved,
    # so everything after is noise).
    path = tmp_path / "walk.txt"
    _record(_story(), ["take lamp", "north", "south"], path)
    changed = GAME.replace("A bare hall.", "A dim hall.")  # HALL desc, the LOOK
    report = []
    io = _check(_story(changed), path, report)
    assert io.diverged
    assert io.compared >= 1
    # Only one divergence block is emitted (it stops).
    assert "\n".join(report).count("diverged here") == 1


# -- hand-added commands are NEW, not failures -------------------------------

def test_hand_added_command_is_new_not_a_failure(tmp_path):
    # A commands-only file the author wrote by hand: no replies to check, so
    # every command runs and none fails.
    path = tmp_path / "cmds.txt"
    path.write_text("> take lamp\n> north\n> jump\n")
    report = []
    io = _check(_story(), path, report)
    assert not io.diverged
    assert report == []


def test_mixed_recorded_and_hand_added(tmp_path):
    # One recorded command (checked) plus one hand-added (NEW): the recorded
    # one still matches, the new one just runs.
    path = tmp_path / "walk.txt"
    _record(_story(), ["take lamp", "north"], path)
    text = path.read_text().rstrip() + "\n> jump\n"  # append a bare command
    path.write_text(text)
    report = []
    io = _check(_story(), path, report)
    assert not io.diverged


# -- parsing + normalization -------------------------------------------------

def test_parse_walkthrough_marks_replyless_commands_none():
    intro, turns = parse_walkthrough("> take lamp\nGot it.\n> jump\n")
    assert turns[0] == ("take lamp", "Got it.\n") or turns[0][0] == "take lamp"
    assert turns[1][0] == "jump"
    assert turns[1][1] is None  # no reply recorded -> NEW


def test_parse_walkthrough_skips_comments():
    intro, turns = parse_walkthrough("# a note\n> north\nYou go north.\n")
    assert [c for c, _ in turns] == ["north"]


def test_norm_ignores_cosmetic_spacing_and_prompt():
    assert _norm("\n\nGot it.\n\n>") == _norm("Got it.")
