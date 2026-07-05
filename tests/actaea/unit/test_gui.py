# test_gui.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M7: the tkinter shell, driven programmatically: a story boots in
the window, scripted lines are typed into the Text widget at its prompts,
and the story plays to a clean quit. The real done-test is a human playing
both example games in the window; this keeps the machinery from regressing
in between.

ONE Tk root per process: Tk 9.0 on macOS dies with SIGTRAP when a second
root is created and wait_variable spins on it, so there is no separate
display probe; the app itself is the probe (TclError = no display = skip).
Skipped likewise where tkinter is not installed."""

import pytest

tk = pytest.importorskip("tkinter")

from actaea.loader import load

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Window Probe"\n    start deck\n'
    'room deck\n    name "Observation Deck"\n    desc "Stars wheel past."\n'
)


def test_a_game_plays_in_the_window(tmp_path, monkeypatch):
    from actaea.gui.app import ActaeaApp

    # The app reads and writes persistent settings (the View menu);
    # the test must see neither the user's nor leave its own.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    try:
        app = ActaeaApp(story, "probe")
    except tk.TclError:
        pytest.skip("no display for tkinter")

    script = ["look", "quit", "y"]

    def pump():
        if app.vm.halted or app._closed:
            app.root.quit()
            return
        if app._reading_line and script:
            app.text.insert("end-1c", script.pop(0))
            app._on_return(None)
        app.root.after(30, pump)

    app.root.after(20, app._run_vm)
    app.root.after(40, pump)
    app.root.after(10_000, app.root.quit)  # watchdog: never hang the suite
    app.root.mainloop()

    out = app.text.get("1.0", "end")
    assert app.vm.halted, "the story never reached its quit"
    assert "Window Probe" in out
    assert "Observation Deck" in out
    assert out.count("Stars wheel past.") >= 2  # the boot look and the typed one
    assert "We'll leave it there." in out
    assert "[The story has ended.]" in out
    app.root.destroy()
