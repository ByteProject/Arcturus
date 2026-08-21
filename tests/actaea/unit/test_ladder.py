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


def test_a_stub_launch_has_no_tty_and_still_gets_the_window(
        tmp_path, monkeypatch):
    """The .app stub launch (Finder, Dock) runs with NO terminal at all,
    marked by ACTAEA_BUNDLE from the shim. Both tty gates must honor the
    mark: the bare-launch guard (the stub died at birth on a usage error
    nobody saw; Stefan's install, 2026-08-21) and the window ladder
    (which would have dropped a Finder launch to the headless pipe)."""
    story = _story(tmp_path)
    opened = []
    monkeypatch.setenv("ACTAEA_BUNDLE", "1")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(main_mod, "_startup_story",
                        lambda: (story, None))
    monkeypatch.setattr(main_mod, "_play_window",
                        lambda s, t, *a, **k: opened.append(t) or True)
    from actaea.gui import dress
    monkeypatch.setattr(dress, "predress", lambda: None)
    monkeypatch.setattr(dress, "refresh_stub", lambda bases=None: None)
    # Bare launch: the guard lets the bundle through to _startup_story
    # and the ladder hands the resolved story to the window.
    assert main_mod.main([]) == 0
    assert opened == ["ladder.z5"]
    # With a story argument (open -a Actaea --args story.z5): same door.
    assert main_mod.main([story]) == 0
    assert opened == ["ladder.z5", "ladder.z5"]


def test_a_piped_bare_launch_still_errors_without_the_mark(
        tmp_path, monkeypatch, capsys):
    """A developer piping into a bare `actaea` keeps the old contract:
    no story argument is still a usage error when no bundle mark and no
    tty are present."""
    monkeypatch.delenv("ACTAEA_BUNDLE", raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    try:
        main_mod.main([])
    except SystemExit as e:
        assert e.code == 2
    else:
        raise AssertionError("a piped bare launch must still error")
    assert "story" in capsys.readouterr().err
