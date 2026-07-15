# test_console.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea's curses front-end, driven through a real pty: the game-drawn
status bar renders from the cell grid, colours flow as ANSI sequences, play
works, and the final screen holds for a key. Skipped where there is no pty
or curses (native Windows); the harness never needs them."""

import os
import re
import select
import subprocess
import sys
import time

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

pty = pytest.importorskip("pty")
pytest.importorskip("curses")

GAME = (
    'game\n    title "Terminal"\n    start hall\n'
    "summon.statusline\n"
    'room hall\n    name "The Long Hall"\n    desc "A very long hall."\n'
    'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
)


def _spawn(story_path, *extra):
    pid, fd = pty.fork()
    if pid == 0:  # the child becomes the interpreter
        os.environ["TERM"] = "xterm-256color"
        os.execvp(sys.executable,
                  [sys.executable, "-m", "actaea", "--console",
                   *extra, str(story_path)])
    return pid, fd


def _drain(fd, seconds):
    out = b""
    end = time.time() + seconds
    while time.time() < end:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            try:
                out += os.read(fd, 65536)
            except OSError:
                break
    return out


def test_console_plays_with_a_live_status_bar(tmp_path):
    story = tmp_path / "t.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    pid, fd = _spawn(story)
    try:
        out = _drain(fd, 1.5)
        os.write(fd, b"take coin\r")
        out += _drain(fd, 1.0)
        os.write(fd, b"quit\ry\r")
        out += _drain(fd, 1.0)
        os.write(fd, b" ")  # the final press-any-key hold
        out += _drain(fd, 0.5)
    finally:
        os.close(fd)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
    text = out.decode("utf-8", "replace")
    plain = re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][0B]|\x1b[=>]", "", text)
    assert "\x1b[" in text  # colours/attributes really crossed the wire
    assert "The Long Hall" in plain  # the statusline granule, on the grid
    assert "Got it." in plain
    assert "story has ended" in plain


def test_console_record_writes_a_walkthrough(tmp_path):
    # --record works in the full terminal, not only the plain console: play a
    # couple of commands through the pty and the session file captures them
    # with the game's replies.
    story = tmp_path / "t.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    walk = tmp_path / "walk.txt"
    pid, fd = _spawn(story, "--record", str(walk))
    try:
        _drain(fd, 1.5)
        os.write(fd, b"take coin\r")
        _drain(fd, 1.0)
        os.write(fd, b"quit\ry\r")
        _drain(fd, 1.0)
        os.write(fd, b" ")
        _drain(fd, 0.5)
    finally:
        os.close(fd)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
    text = walk.read_text()
    assert "> take coin" in text     # the command, recorded from the terminal
    assert "Got it." in text         # and the game's reply beneath it
