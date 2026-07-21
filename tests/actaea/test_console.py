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


# --- the screen the game is told about ------------------------------------
#
# Header bytes 0x21/0x20 are the screen size a game reads to lay out anything
# that spans the screen (S 11.1). Actaea used to answer 80 columns whatever the
# terminal was, so a status bar in a 103-column window stopped at column 80 with
# a notch beyond it (the field report and its screenshot). The terminal front-end
# now reports the real thing, and a resize re-stamps it.

SIZE_GAME = (
    'game\n    title "W"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'on each_turn\n'
    '    say "WIDTH=${screen_width()} HEIGHT=${screen_height()}"\n'
)


def _set_size(fd, cols, lines):
    import fcntl
    import struct
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", lines, cols, 0, 0))


def _sizes_seen(raw):
    text = raw.decode("utf-8", "replace")
    plain = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text).replace("\r", "").replace("\n", "")
    return re.findall(r"WIDTH=(\d+) HEIGHT=(\d+)", plain)


def test_the_game_is_told_the_terminal_s_real_size(tmp_path):
    story = tmp_path / "size.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(SIZE_GAME)))))
    pid, fd = _spawn(story)
    try:
        _set_size(fd, 103, 30)
        _drain(fd, 1.2)
        os.write(fd, b"wait\r")
        seen = _sizes_seen(_drain(fd, 1.2))
        assert ("103", "30") in seen, seen
        # A resize reaches the game through the header, and it reads the new
        # size the next time it draws (v5 has no resize interrupt).
        _set_size(fd, 120, 45)
        os.write(fd, b"wait\r")
        seen = _sizes_seen(_drain(fd, 1.5))
        assert ("120", "45") in seen, seen
        os.write(fd, b"quit\ry\r")
        _drain(fd, 0.8)
        os.write(fd, b" ")
        _drain(fd, 0.4)
    finally:
        os.close(fd)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass


def test_the_status_bar_spans_the_whole_terminal(tmp_path):
    # The bar fills every column the terminal has, at any width. Measured from
    # the row-1 repaint the interpreter emits at startup.
    story = tmp_path / "t.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    esc = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b[()][AB0]|\x1b[=>]|\x1b\]0;.*?\x07")
    for cols in (60, 103, 120):
        pid, fd = _spawn(story)
        try:
            _set_size(fd, cols, 30)
            text = _drain(fd, 1.5).decode("utf-8", "replace")
            i = text.rfind("\x1b[H")
            j = text.find("\x1b[2;1H", i if i >= 0 else 0)
            assert i >= 0 and j > i, f"no row-1 paint at {cols} columns"
            assert len(esc.sub("", text[i:j])) == cols
            os.write(fd, b"quit\ry\r")
            _drain(fd, 0.8)
            os.write(fd, b" ")
            _drain(fd, 0.4)
        finally:
            os.close(fd)
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass


def test_text_survives_a_resize_and_re_wraps(tmp_path):
    # A curses window holds no history, so a resize used to leave the screen
    # blank until play scrolled text back in ("everything disappears, and it
    # comes back from the bottom as I type"). The console keeps a scrollback of
    # logical lines and repaints from it, re-wrapping to the new width.
    story = tmp_path / "t.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    pid, fd = _spawn(story)
    try:
        _set_size(fd, 80, 30)
        before = _drain(fd, 1.8).decode("utf-8", "replace")
        assert "The Long Hall" in re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", before)
        # Widen: the story text must be back on screen without a keypress.
        _set_size(fd, 120, 30)
        after = _drain(fd, 1.5).decode("utf-8", "replace")
        plain = re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][AB0]|\x1b[=>]", "", after)
        assert "An Interactive Fiction" in plain, plain[:400]
        # Narrow: the same text arrives again, wrapped to the smaller width, so
        # no repainted line can be longer than the screen.
        _set_size(fd, 50, 30)
        narrow = _drain(fd, 1.5).decode("utf-8", "replace")
        plain = re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][AB0]|\x1b[=>]", "",
                       narrow)
        assert "Interactive Fiction" in plain, narrow[:400]
        # Re-wrapped, not merely reprinted: the release line is 60 characters
        # and cannot survive intact on a 50-column screen.
        assert "Arcturus 1.3 / Cosmos 1.2" not in plain, plain[:400]
        os.write(fd, b"quit\ry\r")
        _drain(fd, 0.8)
        os.write(fd, b" ")
        _drain(fd, 0.4)
    finally:
        os.close(fd)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass


def test_a_cleared_screen_stays_cleared_across_a_resize(tmp_path):
    # The story erased the screen on purpose, so a resize must not bring the
    # old text back out of the scrollback.
    src = (
        'game\n    title "Wipe"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'verb "wipe"\n    wipe\n'
        'on wipe\n    clear_screen()\n    say "Wiped."\n'
    )
    story = tmp_path / "w.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(src)))))
    pid, fd = _spawn(story)
    try:
        _set_size(fd, 80, 30)
        _drain(fd, 1.5)
        os.write(fd, b"wipe\r")
        _drain(fd, 1.2)
        _set_size(fd, 110, 30)
        after = _drain(fd, 1.5).decode("utf-8", "replace")
        plain = re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][AB0]|\x1b[=>]", "", after)
        assert "Interactive Fiction" not in plain, plain[:300]
        os.write(fd, b"quit\ry\r")
        _drain(fd, 0.8)
        os.write(fd, b" ")
        _drain(fd, 0.4)
    finally:
        os.close(fd)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
