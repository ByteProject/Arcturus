# test_ladder.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The front-end ladder speaks when it steps down (the Fos report,
2026-08-11): a tkinter-less Python used to fall silently from the window
to the bare pipe on native Windows, which reads as Actaea being broken
beside a working Windows Frotz. docs/06 section 1 has always promised
"degrades to the next mode down and says so"; these tests hold the code
to it, and hold the hint to naming a real remedy per platform."""

import sys

import actaea.__main__ as main_mod
from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _story(tmp_path):
    src = ('game\n    title "L"\n    start hall\n'
           'room hall\n    name "Hall"\n    desc "A hall."\n')
    story = generate(analyze(cosmos.combined_program(parse(src))))
    p = tmp_path / "ladder.z5"
    p.write_bytes(story)
    return str(p)


def _run_ladder(tmp_path, monkeypatch, capsys):
    """Run main() on a tty where neither tkinter nor curses exists."""
    monkeypatch.setattr(main_mod, "_play_window", lambda *a, **k: False)
    monkeypatch.setattr(main_mod, "_play_terminal", lambda *a, **k: False)
    monkeypatch.setattr(main_mod, "_play_headless", lambda *a, **k: 0)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    rc = main_mod.main([_story(tmp_path)])
    assert rc == 0
    return capsys.readouterr().err


def test_the_ladder_says_so_on_every_step_down(tmp_path, monkeypatch, capsys):
    err = _run_ladder(tmp_path, monkeypatch, capsys)
    assert "no tkinter" in err
    assert "playing headless" in err


def test_the_hint_names_a_real_remedy_everywhere():
    # One hint per platform, each carrying the actual fix, not a shrug.
    for platform, needle in (
        ("win32", "tcl/tk and IDLE"),
        ("darwin", "brew install python-tk"),
        ("linux", "python3-tk"),
    ):
        real = sys.platform
        sys.platform = platform
        try:
            assert needle in main_mod._tk_hint()
        finally:
            sys.platform = real


def test_console_explains_a_curses_less_platform(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_mod, "_play_terminal", lambda *a, **k: False)
    monkeypatch.setattr(main_mod, "_play_headless", lambda *a, **k: 0)
    rc = main_mod.main(["--console", _story(tmp_path)])
    assert rc == 0
    err = capsys.readouterr().err
    assert "curses" in err
    assert "playing headless" in err
