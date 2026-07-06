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

import struct
import zlib

# The deck carries an arc_image, so the one GUI test (one Tk root per process,
# the Tk 9.0 rule) also covers the picture band: the room draws its picture and
# it renders into the top canvas.
GAME = (
    'game\n    title "Window Probe"\n    start deck\n'
    'room deck\n    name "Observation Deck"\n    desc "Stars wheel past."\n'
    '    arc_image "starfield"\n'
)


def _make_png(path, w, h, rgb):
    """A tiny solid-colour PNG, no third-party libraries (the zero-dependency
    rule is the whole point of using tkinter's own PNG support)."""
    raw = bytearray()
    row = bytes(rgb) * w
    for _ in range(h):
        raw.append(0)
        raw += row

    def chunk(tag, data):
        c = tag + data
        return (struct.pack(">I", len(data)) + c
                + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def test_a_game_plays_in_the_window(tmp_path, monkeypatch):
    from actaea.gui.app import ActaeaApp

    # The app reads and writes persistent settings (the View menu);
    # the test must see neither the user's nor leave its own.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    world = analyze(cosmos.combined_program(parse(GAME)))
    story = load(generate(world))
    image_names = {i: n for n, i in world.images.items()}  # {1: "starfield"}
    _make_png(tmp_path / "starfield.png", 320, 96, (20, 30, 90))

    try:
        app = ActaeaApp(story, "probe", image_names=image_names,
                        images_dir=str(tmp_path))
    except tk.TclError:
        pytest.skip("no display for tkinter")

    script = ["look", "quit", "y"]
    band = []

    def pump():
        if app.vm.halted or app._closed:
            app.root.quit()
            return
        if app._reading_line:
            app.root.update_idletasks()
            band.append(app._image_canvas.winfo_reqheight())
            if script:
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
    # The picture band rendered: the model asked for the room's image and the
    # canvas took the PNG's height (96), so a real picture is on screen.
    assert app.vm.screen.image == (1, 0)
    assert band and max(band) == 96
    app.root.destroy()
