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
# it renders into the top canvas. The id is slot 1, so the file is 1.png.
GAME = (
    'constant arc_mode = 12\n'   # DAAD mode, to match the 320x96 probe art
    'constant starfield = 1\n'
    'game\n    title "Window Probe"\n    start deck\n'
    'room deck\n    name "Observation Deck"\n    desc "Stars wheel past."\n'
    '    arc_image starfield\n'
    # LONGER THAN A PAGE, deliberately: with the picture band taking rows
    # there is little reading area left, so RECITE overflows it and the
    # window's [MORE] has to stop and wait. The pump below answers it the
    # way a player would.
    'on start\n'
    + "".join('    say "The watch changes at midnight and the deck is cold, '
              'line %d of the opening."\n' % i for i in range(1, 13))
    + 'verb "recite"\n    reciting\n'
    'on reciting\n'
    + "".join('    say "Line %d of the long watch, counted off against the '
              'turning of the ship and the cold."\n' % i
              for i in range(1, 41))
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
    # A SMALL WINDOW on purpose. Stefan's screenshot was a window resized well
    # below its saved row count, and that is what made the boot bug show: with
    # a picture band on top there was room for a dozen lines, the story printed
    # more than that before its first prompt, and nothing paused because the
    # widget had not yet been given its real size.
    cfg = tmp_path / "actaea"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "settings.json").write_text(
        '{"family": "Menlo", "size": 14, "rows": 20, "game_colours": true}')

    world = analyze(cosmos.combined_program(parse(GAME)))
    story = load(generate(world))
    # The id is the resource slot, so the file is 1.png (starfield = 1).
    _make_png(tmp_path / "1.png", 320, 96, (20, 30, 90))

    try:
        app = ActaeaApp(story, "probe", images_dir=str(tmp_path))
    except tk.TclError:
        pytest.skip("no display for tkinter")

    script = ["look", "recite", "quit", "y"]
    more_seen = []
    end_in_view = []
    band = []
    caret_checks = []

    def check_caret_discipline():
        # The caret never leaves the input line (the 2026-07-22 field
        # report: arrow keys walked it into the transcript). Driven through
        # the handlers directly, the deterministic route.
        import types
        ev = lambda keysym: types.SimpleNamespace(keysym=keysym, char="")
        caret_checks.append(("up", app._on_key(ev("Up")) == "break"))
        caret_checks.append(("down", app._on_key(ev("Down")) == "break"))
        app._on_key(ev("Home"))
        caret_checks.append(
            ("home", app.text.compare("insert", "==", "input_start")))
        caret_checks.append(("left-at-start",
                             app._on_key(ev("Left")) == "break"))
        # The compiled game declares the roomier buffers (the 60-character
        # wall of the same field report): the read hands the GUI 120.
        caret_checks.append(("buffer", app._max_len == 120))

    def pump():
        if app.vm.halted or app._closed:
            app.root.quit()
            return
        if app._reading_key:
            # A [MORE] pause: the marker is on screen, at the end of what has
            # been shown, and any key continues. Without this the window would
            # simply wait, which is exactly what it should do to a player.
            more_seen.append("[MORE]" in app.text.get("1.0", "end"))
            app._key_code = 32
            app._key.set(" ")
            app.root.after(30, pump)
            return
        if app._reading_line:
            # BEFORE any update: the question is whether the story's own boot
            # left the prompt on screen, not whether an idle pass can repair
            # it afterwards.
            end_in_view.append(app.text.bbox("end-1c") is not None)
            app.root.update_idletasks()
            band.append(app._image_canvas.winfo_reqheight())
            # THE PROMPT MUST BE ON SCREEN. It was not at boot: the widget is
            # asked for the settings height and keeps it only until the
            # picture band claims its rows, and the story prints its whole
            # boot without returning to the event loop, so the text ran on
            # past the bottom edge with the prompt below it (Stefan's
            # screenshot, 2026-08-20).
            if not caret_checks:
                check_caret_discipline()
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
    # PAGING: the long recital stopped at least once with [MORE] showing, and
    # the marker left no trace behind it.
    assert more_seen, "a passage taller than the window never paused"
    assert all(more_seen), "the pause happened with no [MORE] on screen"
    assert "[MORE]" not in out
    assert "Line 40 of the long watch" in out
    # Every prompt was visible when it was offered, boot included.
    assert end_in_view and all(end_in_view), end_in_view
    # The page is measured from the pixels the reading area HAS, so it agrees
    # with the window rather than with what the widget asked for.
    assert app._reading_lines() == app.text.winfo_height() // app.cell_h
    assert app._page_height() == app._reading_lines() - 1
    assert caret_checks and all(ok for _, ok in caret_checks), caret_checks
    assert "Window Probe" in out
    assert "Observation Deck" in out
    assert out.count("Stars wheel past.") >= 2  # the boot look and the typed one
    assert "We'll leave it there." in out
    assert "[The story has ended.]" in out
    # The picture band rendered: the model asked for the room's image and it
    # was scaled to fill the window width at its 320x96 aspect ratio (crisp
    # pixel-grid scaling), so the band is full width and the height follows.
    # The mode is the game default, 12 (DAAD), carried in the opcode operand.
    assert app.vm.screen.image == (1, 12)
    scaled = app._scaled_image(1, app._band_width())
    # The picture fills the 80-cell screen width (inside the frame) at its aspect.
    assert scaled.width() == 80 * app.cell_w
    assert abs(scaled.height() / scaled.width() - 96 / 320) < 0.02
    # The band follows the SCALED picture's height, so the art keeps its
    # aspect at any window width (fullscreen included) and is never cropped
    # (the old mode-rows clamp cut the bottom of every scene at fonts whose
    # cells are not 8-pixel squares; the fullscreen fix removed it). On a
    # fixed 8-pixel-cell screen this equals the mode's rows exactly.
    assert band and max(band) == scaled.height()
    # The window is the 80-cell screen plus the frame on both sides.
    assert app.root.winfo_width() == 80 * app.cell_w + 2 * app._margin
    # The text area is a WHOLE number of lines (so it never shows a half row),
    # and it shrank to fit under the picture band.
    n = int(app.text.cget("height"))
    assert n >= 1
    assert n < app._rows_var.get()  # the band took some of the rows
    app.root.destroy()
