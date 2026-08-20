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
    'summon.statusline\n'
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

    # THE SHAPE IT OPENS IN. With nothing remembered, the window takes the
    # modern 4:5 of the desktop interpreters: 80 cells wide, and as tall as
    # the ratio makes it. Measured before the story runs, since fitting the
    # window to a picture band adjusts the height afterwards.
    app.root.update_idletasks()
    opening_w = app.root.winfo_width()
    opening_h = app.root.winfo_height()
    assert app._aspect_var.get() == "modern"
    # It opens at the size the shape asks for, and that size fits the screen.
    # Modern is a portrait page, 4:5. A short
    # desktop scales it down keeping the ratio until the seventy-column
    # floor; there the width holds and the height takes what the desktop
    # honestly offers (wm_maxsize, dock included), which is the nearest
    # portrait the machine has: on the laptop that is a window slightly
    # taller than wide at seventy columns.
    want_w, want_h = app._aspect_size()
    assert opening_w == want_w
    # The shape survives the fit: unclamped it is exactly 4:5 portrait, and
    # at the floor the window is never squatter than the desktop forces.
    if want_w > 70 * app.cell_w + 2 * app._margin:
        assert want_h == want_w * 5 // 4
    else:
        assert want_h >= want_w          # the nearest portrait: taller or square
    # The desktop has the last word on height (menu bar, dock): the window
    # asks for the shape and takes what it is given.
    assert 0 < opening_h <= want_h
    assert opening_h <= app.root.winfo_screenheight()
    assert app._cols >= 70
    # And the two shapes really are different shapes: classic is the wider,
    # shorter 4:3, modern the taller 4:5.
    app._aspect_var.set("classic")
    classic_w, classic_h = app._aspect_size()
    app._aspect_var.set("modern")
    modern_w, modern_h = app._aspect_size()
    assert classic_h / classic_w < modern_h / modern_w

    script = ["look", "recite", "quit", "y"]
    more_seen = []
    end_in_view = []
    first_line_seen = []
    first_pause_clean = []
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
            if not first_pause_clean:
                # THE PAGE ON OFFER STARTS ON SCREEN, and the furniture
                # matches the model. The story asked for its picture before
                # printing a word, so a pause with no band is a pause measured
                # against a screen that does not exist (the geometry-lag bug);
                # and a pause whose own page has partly scrolled off means the
                # reading area was not the size the pager believed.
                # The furniture must already be on screen: the story asked
                # for a picture band before it printed a word, so by the time
                # it stops for a key the band must have claimed its rows and
                # the reading area must be the smaller one. Deferring that to
                # an idle pass let the whole boot be laid out at the full
                # window size and then shrink under itself, scrolling the top
                # away unread (Stefan's screenshot, 2026-08-20).
                first_pause_clean.append(
                    (app.vm.screen.image is None) == (app._band_h == 0)
                    and app.text.bbox("page_start") is not None)
            app._key_code = 32
            app._key.set(" ")
            app.root.after(30, pump)
            return
        if app._reading_line:
            # BEFORE any update: the question is whether the story's own boot
            # left the prompt on screen, not whether an idle pass can repair
            # it afterwards.
            end_in_view.append(app.text.bbox("end-1c") is not None)
            if not first_line_seen:
                first_line_seen.append(
                    more_seen != [] or app.text.bbox("1.0") is not None)
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
    # NOTHING SCROLLS AWAY UNREAD. At the first prompt no key has been
    # pressed except in answer to a [MORE], so every line printed since the
    # start must still be on screen. Anything else means text went past the
    # top edge with no pause to stop it (Stefan's screenshot, 2026-08-20: the
    # blank line the library puts under the status bar had scrolled off).
    assert first_line_seen and first_line_seen[0], (
        "boot text scrolled off with no [MORE] to stop it")
    assert first_pause_clean and first_pause_clean[0], (
        "text had already scrolled off the top when the first [MORE] came: "
        "the reading area was not the size the pager thought it was")
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
    # The picture fills the screen width (inside the frame) at its aspect.
    # That width is the CURRENT column count: the window opens at its shape,
    # and on a screen too short for 4:5 at 80 columns it opens narrower.
    assert scaled.width() == app._cols * app.cell_w
    assert abs(scaled.height() / scaled.width() - 96 / 320) < 0.02
    # The band follows the SCALED picture's height, so the art keeps its
    # aspect at any window width (fullscreen included) and is never cropped
    # (the old mode-rows clamp cut the bottom of every scene at fonts whose
    # cells are not 8-pixel squares; the fullscreen fix removed it). On a
    # fixed 8-pixel-cell screen this equals the mode's rows exactly.
    # The band is the picture's own height, no letterbox: spare pixels put
    # anywhere in the stack read as a blank row (Stefan tried all three
    # placements on screen, 2026-08-20). The WINDOW gives them up instead.
    assert band and max(band) == scaled.height()
    # So the window fits its contents exactly and the reading area is a whole
    # number of rows: what the pager counts is what the window shows, with no
    # orphan strip anywhere to imitate a line.
    assert app.text.winfo_height() % app.cell_h == 0
    assert app._reading_lines() == app.text.winfo_height() // app.cell_h
    assert app.root.winfo_height() == (
        2 * app._margin + app._band_h + app.cell_h
        + app.text.winfo_height()), "the window does not fit its contents"
    # The column count is derived FROM the window's width (the aspect or the
    # player's hand decides the width; the width decides the columns), and
    # the division's few leftover pixels rest in the right margin, exactly as
    # the cell grid has always drawn them.
    assert app._cols == (app.root.winfo_width() - 2 * app._margin) // app.cell_w
    assert app._cols >= 70
    # The text area is a WHOLE number of lines (so it never shows a half row),
    # and it shrank to fit under the picture band.
    n = int(app.text.cget("height"))
    assert n >= 1
    without_band = (app.root.winfo_height() - 2 * app._margin
                    - app.cell_h) // app.cell_h
    assert n < without_band  # the band took some of the rows
    # WHAT IT REMEMBERS. The shape and the exact place on screen are written
    # to the settings, so the next launch opens where this one was left
    # instead of wherever the window manager puts it.
    import json
    app._persist_now()      # what closing the window does
    saved = json.load(open(tmp_path / "actaea" / "settings.json"))
    assert saved["aspect"] == "modern"
    assert "+" in saved["geometry"] and "x" in saved["geometry"]
    app.root.destroy()
