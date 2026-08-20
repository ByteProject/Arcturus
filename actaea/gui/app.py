# app.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The M7 shell: one window, the scrolling lower text area with word wrap,
and inline input, the way interpreters have looked since the eighties: the
player types at the story's prompt, in the story's own text flow, not into
a separate entry box.

How input blocks without freezing the window: the VM runs on the tkinter
thread and its read_line/read_char calls spin the event loop with
wait_variable until a key event completes the input. The window keeps
painting, scrolling, and responding while the machine waits; when the
player presses Return (or any key, for read_char), the variable flips and
the VM resumes. Single-threaded, no locks, no queues.

The Text widget is read-only except for the live input region: everything
before the input mark is story text and refuses edits; the region from the
mark to the end is the player's line.

The upper window (M8) is a Canvas above the text area, rendered FROM the
cell model in screen.py: exact cell geometry (a measured monospace font
fixes the cell size), repainted when the model signals a change, never
holding screen state of its own. Reverse-video cells render inverted; the
full style and colour treatment arrives with M9. The Canvas is the surface
the later arc_image work draws pictures onto, which is why cell geometry
is exact from day one."""

import base64
import json
import os
import tkinter as tk
import webbrowser
from math import gcd as _gcd
from tkinter import filedialog
from tkinter import font as tkfont

from .. import __version__
from ..errors import ActaeaError
from ..io import IOSystem
from ..screen import BOLD, ITALIC, REVERSE, TRUE_COLOURS, true_colour_hex
from ..vm import VM
from .pager import Pager

# Tk keysyms for the keys with ZSCII input codes of their own (S 3.8):
# cursors, function keys, and the numeric keypad. read_char hands these
# codes to the game, and read ends on the ones the story's terminating-
# characters table lists.
_FUNCTION_KEYS = {
    "Up": 129, "Down": 130, "Left": 131, "Right": 132,
    **{f"F{n}": 132 + n for n in range(1, 13)},
    **{f"KP_{n}": 145 + n for n in range(10)},
}

_REPO_URL = "https://github.com/ByteProject/Arcturus"


def _settings_path() -> str:
    base = os.environ.get(
        "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
    )
    return os.path.join(base, "actaea", "settings.json")


def _load_settings() -> dict:
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_settings(data: dict) -> None:
    path = _settings_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass  # settings are a convenience; play goes on without them


class GuiIO(IOSystem):
    """The io boundary against the shell. The widget shows the player's
    typing live, so read_line never echoes (the io.py contract)."""

    # The event loop can run input interrupts, so this front-end claims
    # the header's timed-input bit.
    supports_timed = True

    # The window can draw pictures (arc_image, B11), so it claims the header's
    # picture-available bit; the console and headless front-ends do not.
    supports_pictures = True

    def __init__(self, app: "ActaeaApp"):
        self.app = app

    def screen_size(self):
        """The window starts as an 80-cell screen by construction, and the
        column count follows the REAL window width from then on (maximize,
        fullscreen): the app recomputes it on resize and re-stamps the
        header, the same fix the console front-end got first. The height is
        the chosen number of text rows."""
        return (max(1, int(getattr(self.app, "_cols", 80))),
                max(1, int(self.app._rows_var.get())))

    def print_text(self, text: str) -> None:
        self.app.append_story(text)

    def read_line(self, max_len, preload="", terminators=frozenset(),
                  timeout=0.0, on_timeout=None):
        return self.app.wait_for_line(
            max_len, preload, terminators, timeout, on_timeout
        )

    def read_char(self, timeout=0.0, on_timeout=None) -> int:
        return self.app.wait_for_key(timeout, on_timeout)

    def erase_lower(self) -> None:
        self.app.clear_story()

    # The save/restore channels: native file dialogs, on the same single
    # thread everything else runs on (the VM is only ever inside an opcode
    # here, exactly as it is inside wait_variable). An empty answer from a
    # cancelled dialog returns None, which the VM reports as failure.

    _FILETYPES = [("Quetzal saves", "*.qzl *.sav"), ("All files", "*")]

    def save_path(self, default: str):
        return filedialog.asksaveasfilename(
            parent=self.app.root, title="Save the story",
            initialfile=default, defaultextension=".qzl",
            filetypes=self._FILETYPES,
        ) or None

    def restore_path(self, default: str):
        return filedialog.askopenfilename(
            parent=self.app.root, title="Restore a saved story",
            filetypes=self._FILETYPES,
        ) or None

    def transcript_path(self, default: str):
        return filedialog.asksaveasfilename(
            parent=self.app.root, title="Transcript file",
            initialfile=default, defaultextension=".txt",
            filetypes=[("Transcripts", "*.txt"), ("All files", "*")],
        ) or None


class ActaeaApp:
    """The window: a Text widget with a scrollbar, inline input, and the
    run loop driving the VM through GuiIO."""

    def __init__(self, story, title: str, images_dir=None, images_zip=None,
                 seed=None):
        self.root = tk.Tk()
        self.root.title(f"{title} - Actaea")
        # arc_image (B11): an arc_image id IS the resource slot, so a picture the
        # model asks for is loaded by number, either as <id>.png from a loose
        # images directory or as Pict <id> from the story's Blorb pack. No name
        # manifest. Loaded on demand and cached; PhotoImages must be kept
        # referenced or tkinter garbage-collects them off the canvas.
        self._images_dir = images_dir
        self._images_zip = images_zip
        self._photo_cache: dict = {}    # id -> native PhotoImage
        self._scaled_cache: dict = {}   # (id, target_width) -> scaled PhotoImage
        self._drawn_image = False  # a sentinel distinct from None (no picture)
        # Settings the menu drives, remembered across sessions; colours
        # before anything calls _colour.
        st = _load_settings()
        self._use_colours = tk.BooleanVar(value=bool(st.get("game_colours", True)))
        self._font_size = tk.IntVar(value=int(st.get("size", 13)))
        self._rows_var = tk.IntVar(value=int(st.get("rows", 30)))
        self._mac_integration()

        self.font = tkfont.nametofont("TkFixedFont").copy()
        self.font.configure(size=self._font_size.get())
        if st.get("family"):
            self.font.configure(family=st["family"])
        self._family_var = tk.StringVar(value=self.font.actual("family"))
        # The style variants, shared by the grid and the lower-window tags.
        self.font_bold = self.font.copy()
        self.font_bold.configure(weight="bold")
        self.font_italic = self.font.copy()
        self.font_italic.configure(slant="italic")
        self.font_bold_italic = self.font.copy()
        self.font_bold_italic.configure(weight="bold", slant="italic")
        self._tags_made: set = set()
        # The screen background: white paper until the game paints it. A
        # game wanting a dark screen sets its background and erases (the
        # compiler emits exactly that for zcolor.background); the erase is
        # where the repaint happens, like every desktop terp.
        self._window_bg = "white"
        # A thin frame in the screen background around the whole content, so the
        # text and picture are not flush against the window edge. It is part of
        # the window, not the 80-cell screen: the picture, status bar, and text
        # all sit inside it, sharing the 80-cell width. It follows the game
        # background (white paper, or a game's own colour), so it reads as a
        # matte around the screen rather than a white border on a dark game.
        self._margin = 10

        self.cell_w = self.font.measure("0")
        self.cell_h = self.font.metrics("linespace")

        # The window IS the story's 80-cell screen, inside the frame.
        self._apply_geometry()
        self.root.configure(background=self._window_bg)

        # The picture band (arc_image): a Canvas pinned to the top, inside the
        # frame, above the status grid and the text. Height 0 (hidden) until a
        # room asks for a picture; packed first so it stays topmost.
        m = self._margin
        self._image_canvas = tk.Canvas(
            self.root, height=0, borderwidth=0, highlightthickness=0,
            background=self._window_bg,
        )
        self._image_canvas.pack(fill="x", side="top", padx=m, pady=(m, 0))
        # A window resize (maximize, fullscreen) widens the canvas; repaint
        # the band at the new width. The repaint's state key includes the
        # width, so the settle-out Configure events after our own height
        # change dedup to nothing (no loop, no flicker).
        self._image_canvas.bind("<Configure>", lambda e: self._repaint_image())
        # The game's column count follows the real window width (the status
        # bar must span a maximized window; the console got this first).
        self._cols = 80
        self.root.bind("<Configure>", self._on_root_resize)

        # The upper window (status bar): a cell grid, shown only while the story
        # keeps a split open.
        self.canvas = tk.Canvas(
            self.root, height=0, borderwidth=0, highlightthickness=0,
            background=self._window_bg,
        )
        self._grid_shown = False
        self._redraw_queued = False
        self._band_h = 0  # current picture-band height in pixels (0 = none)

        frame = tk.Frame(self.root, background=self._window_bg)
        frame.pack(fill="both", expand=True, padx=m, pady=(0, m))
        self._lower_frame = frame
        self.text = tk.Text(
            frame, wrap="word", font=self.font, undo=False,
            # No padding inside the text: an 80-character line then measures
            # exactly 80 cells, so the text, the status bar, and the picture all
            # share that width and left edge. The margin around the screen is the
            # frame, added by the outer packing, not here.
            padx=0, pady=0, borderwidth=0, highlightthickness=0,
            background=self._window_bg, foreground="black",
            insertbackground="black",
        )
        # No scrollbar: interpreters never had one, the native widget is an
        # unstyleable white strip on a game-painted dark screen (Stefan's
        # eye, 2026-07-05), and the wheel, trackpad, and the unread-text
        # return cover every way a player actually moves through the text. Fill
        # the width but NOT the height: the height is set to a whole number of
        # text lines (_relayout), so scrolled text never shows a half-clipped
        # top line; the leftover pixels are the frame's bottom margin.
        self.text.pack(fill="x", side="top")

        # The input mark: everything before it is story text and immutable.
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_gravity("input_start", "left")
        # Story text goes in a page at a time and stops with [MORE] when the
        # reading area is full, the way the curses front end has always done
        # it, so nothing scrolls past unread. The pager counts the display
        # lines; the widget half is further down.
        self._pager = Pager()

        self._line_ready = tk.BooleanVar(value=False)
        self._key: tk.StringVar = tk.StringVar(value="")  # the wake signal
        self._key_code = 0            # the actual key, as a ZSCII/Unicode code
        self._reading_line = False
        self._reading_key = False
        self._closed = False
        self._max_len = 0
        self._input_tag = ""
        self._terminators = frozenset()
        self._terminator = 13
        self._timer = None            # the pending after() id for timed input
        self._timed_out = False

        self.text.bind("<Key>", self._on_key)
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        # Keep the caret out of the story text: any click refocuses the end.
        self.text.bind("<Button-1>", lambda e: self.root.after(1, self._to_end))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.text.focus_set()

        self.vm = VM(story, GuiIO(self), seed=seed)
        self.vm.screen.on_change = self._grid_changed
        self._build_menu()

    # -- the menu, the About panel, the settings ----------------------------------

    def _aqua(self) -> bool:
        return self.root.tk.call("tk", "windowingsystem") == "aqua"

    def _mac_integration(self) -> None:
        """macOS niceties. The BOLD name in the menu bar belongs to the
        hosting bundle: bare Python has no bundle of its own, so it says
        Python unless pyobjc is installed (then it says Actaea); a proper
        .app rename is a packaging concern, out of scope here. The About
        item in that menu is ours either way."""
        if not self._aqua():
            return
        try:
            from Foundation import NSBundle  # optional; never required

            b = NSBundle.mainBundle()
            info = b.localizedInfoDictionary() or b.infoDictionary()
            if info is not None:
                info["CFBundleName"] = "Actaea"
        except Exception:
            pass
        self.root.createcommand("tkAboutDialog", self._about)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        if self._aqua():
            appmenu = tk.Menu(menubar, name="apple")
            appmenu.add_command(label="About Actaea", command=self._about)
            appmenu.add_separator()
            menubar.add_cascade(menu=appmenu)
        view = tk.Menu(menubar, tearoff=0)
        # The Font menu lists EVERY fixed-pitch family the system has. The
        # scan instantiates a font per family, so it runs once, lazily, the
        # first time the menu opens.
        fonts = tk.Menu(view, tearoff=0,
                        postcommand=lambda: self._fill_font_menu(fonts))
        size = tk.Menu(view, tearoff=0)
        for n in (11, 12, 13, 14, 16, 18, 20):
            size.add_radiobutton(label=f"{n} pt", variable=self._font_size,
                                 value=n, command=self._retype)
        lines = tk.Menu(view, tearoff=0)
        for n in (25, 30, 35, 40):
            lines.add_radiobutton(label=f"{n} lines", variable=self._rows_var,
                                  value=n, command=self._reheight)
        view.add_cascade(label="Font", menu=fonts)
        view.add_cascade(label="Text Size", menu=size)
        view.add_cascade(label="Screen Height", menu=lines)
        view.add_separator()
        view.add_checkbutton(label="Game Colours", variable=self._use_colours,
                             command=self._colours_toggled)
        menubar.add_cascade(label="View", menu=view)
        if not self._aqua():
            helpm = tk.Menu(menubar, tearoff=0)
            helpm.add_command(label="About Actaea", command=self._about)
            menubar.add_cascade(label="Help", menu=helpm)
        self.root.config(menu=menubar)

    def _fill_font_menu(self, menu: tk.Menu) -> None:
        if getattr(self, "_fonts_filled", False):
            return
        self._fonts_filled = True
        current = self._family_var.get()
        names = set()
        for fam in tkfont.families(self.root):
            if fam.startswith(("@", ".")):
                continue  # Windows vertical variants and hidden UI faces
            try:
                if tkfont.Font(root=self.root, family=fam).metrics("fixed"):
                    names.add(fam)
            except tk.TclError:
                continue
        names.add(current)  # whatever plays now is always offerable
        for fam in sorted(names):
            menu.add_radiobutton(label=fam, variable=self._family_var,
                                 value=fam, command=self._retype)

    def _about(self) -> None:
        """The About panel, laid out like one: name large, the facts in
        their own lines, the repository clickable."""
        win = tk.Toplevel(self.root)
        win.title("About Actaea")
        win.resizable(False, False)
        name_font = tkfont.nametofont("TkDefaultFont").copy()
        name_font.configure(size=24, weight="bold")
        tk.Label(win, text="Actaea", font=name_font).pack(padx=48, pady=(22, 0))
        tk.Label(win, text=f"Version {__version__}").pack(pady=(0, 10))
        tk.Label(
            win, justify="center",
            text="Z-machine v5/8 interpreter, debugger and disassembler\n"
                 "Standard 1.1 conformant\n"
                 "Part of Arcturus (programming language & compiler)",
        ).pack(padx=28)
        tk.Label(win, text="Copyright (c) 2026, Stefan Vogt").pack(pady=(10, 0))
        link = tk.Label(win, text=_REPO_URL, fg="#2b66c4", cursor="hand2")
        link.pack(pady=(0, 10))
        link.bind("<Button-1>", lambda e: webbrowser.open(_REPO_URL))
        tk.Button(win, text="OK", command=win.destroy).pack(pady=(2, 16))
        win.bind("<Return>", lambda e: win.destroy())
        win.bind("<Escape>", lambda e: win.destroy())
        win.transient(self.root)
        win.grab_set()

    def _persist(self) -> None:
        _save_settings({
            "family": self._family_var.get(),
            "size": self._font_size.get(),
            "rows": self._rows_var.get(),
            "game_colours": self._use_colours.get(),
        })

    def _apply_geometry(self) -> None:
        self.cell_w = self.font.measure("0")
        self.cell_h = self.font.metrics("linespace")
        m = self._margin
        # 80 cells wide and the chosen number of text rows tall, plus the frame
        # on every side.
        self.root.geometry(
            f"{80 * self.cell_w + 2 * m}"
            f"x{self._rows_var.get() * self.cell_h + 2 * m}"
        )
        self._relayout()

    def _relayout(self) -> None:
        """Set the text area to a WHOLE number of lines, so scrolled text never
        shows a half-clipped row at the top (the picture band and status bar can
        be any pixel height; the text below them takes the whole lines that fit
        and the leftover pixels join the bottom margin)."""
        if not hasattr(self, "text"):
            return  # called once from __init__ before the widgets exist
        band = getattr(self, "_band_h", 0)
        status = self.cell_h if getattr(self, "_grid_shown", False) else 0
        # The real window height wins once the window is mapped: fullscreen
        # and maximize add rows the settings never knew about, and the story
        # text should claim them (Stefan's report: the picture scaled while
        # the text stayed at its settings height). Before mapping, the
        # settings height stands.
        real = self.root.winfo_height() if hasattr(self, "root") else 0
        if real > 5 * self.cell_h:
            avail = real - 2 * self._margin - band - status
        else:
            avail = self._rows_var.get() * self.cell_h - band - status
        n = max(1, avail // self.cell_h)
        if int(self.text.cget("height")) != n:
            self.text.configure(height=n)

    def _on_root_resize(self, event=None) -> None:
        """Fullscreen and maximize change the window's real width: recompute
        the column count, re-stamp the header, and re-width the cell grid
        (vm.screen_resized does both), so the game paints its status bar
        across the whole window on its next turn, the v5 way (no resize
        interrupt exists; the console front-end behaves identically)."""
        if not hasattr(self, "text") or not hasattr(self, "vm"):
            return
        inner = self.root.winfo_width() - 2 * self._margin
        if inner < 10 * self.cell_w:
            return  # not mapped yet, or absurdly narrow: keep the old truth
        cols = max(20, inner // self.cell_w)
        if cols != self._cols:
            self._cols = cols
            self.vm.screen_resized()
            self._redraw_grid()
            self._repaint_image()
        # Height may change without the width (fullscreen on a narrow
        # window, vertical maximize): the text re-fits either way, and the
        # bar's edge fill follows the canvas even when the column count
        # did not move.
        self._relayout()
        if getattr(self, "_grid_shown", False):
            self._redraw_grid()

    def _reheight(self) -> None:
        self._apply_geometry()
        self._persist()

    def _retype(self) -> None:
        n = self._font_size.get()
        fam = self._family_var.get()
        for f in (self.font, self.font_bold, self.font_italic,
                  self.font_bold_italic):
            f.configure(size=n, family=fam)
        # Tags reference the font objects, so existing text re-dresses with
        # them; only the cell geometry needs recomputing.
        self._apply_geometry()
        self._grid_changed()
        self._persist()

    def _colours_toggled(self) -> None:
        # Existing text KEEPS its tags; each look tag is reconfigured for
        # the new setting (deleting them would strip the story's text to
        # the widget default, black, invisible on a game-painted screen).
        bg = self._colour(self.vm.screen.bg, "white")
        self._window_bg = bg
        for tag in self.text.tag_names():
            if tag.startswith("look-"):
                _, style, fg_part, bg_part = tag.split("-", 3)
                self._configure_look(tag, int(style),
                                     self._parse_colour(fg_part),
                                     self._parse_colour(bg_part))
        self.text.configure(
            background=bg,
            insertbackground=self._colour(self.vm.screen.fg, "black"),
        )
        self.canvas.configure(background=bg)
        self._image_canvas.configure(background=bg)
        self.root.configure(background=bg)
        self._lower_frame.configure(background=bg)
        self._grid_changed()
        self._persist()

    @staticmethod
    def _parse_colour(part: str):
        return part if part.startswith("#") else int(part)

    # -- the upper window ---------------------------------------------------------

    def _grid_changed(self) -> None:
        # Coalesce bursts of screen changes into one repaint per idle cycle.
        # The model signals grid AND picture changes through here, so a repaint
        # refreshes both.
        if not self._redraw_queued:
            self._redraw_queued = True
            self.root.after_idle(self._repaint)

    def _repaint(self) -> None:
        self._redraw_queued = False
        self._redraw_grid()
        self._repaint_image()

    # -- the picture band (arc_image) -------------------------------------------

    def _load_image(self, image_id: int):
        """The native PhotoImage for a picture id, loaded as <id>.png and cached.
        None when the file is missing or not a readable image, so a missing
        picture degrades to an empty band rather than a crash."""
        if image_id in self._photo_cache:
            return self._photo_cache[image_id]
        photo = self._read_photo(image_id)
        self._photo_cache[image_id] = photo
        return photo

    def _load_image_bytes(self, image_id: int):
        """The raw PNG bytes for a picture id: from the loose images
        directory or the Blorb pack. None on any miss. (The .arcres zip
        was retired, 2026-07-31; the Blorb is the one pack.)"""
        fname = f"{image_id}.png"
        if self._images_dir:
            try:
                with open(os.path.join(self._images_dir, fname), "rb") as fh:
                    return fh.read()
            except OSError:
                return None
        if self._images_zip:
            try:
                from ..loader import blorb_picture
                return blorb_picture(self._images_zip, image_id)
            except (OSError, KeyError):
                return None
        return None

    def _read_photo(self, image_id: int):
        """Read <id>.png into a PhotoImage. None on any miss (bad path,
        absent entry, unreadable image)."""
        data = self._load_image_bytes(image_id)
        if data is None:
            return None
        try:
            # tkinter reads PNG bytes through the base64 `data` option.
            return tk.PhotoImage(data=base64.b64encode(data).decode("ascii"))
        except tk.TclError:
            return None

    def _scaled_image(self, image_id: int, target_w: int):
        """The picture scaled to fill target_w at its own aspect ratio, so the
        band fills the upper part of the window whatever the font size, and
        the whole window width in fullscreen (the field report: a maximized
        window left the picture at the 80-cell width).
        These are pixel-art scenes (320x96 for the Amiga/ST art), so scaling
        stays on the pixel grid to keep it crisp instead of blurring it:
        tkinter's own zoom (integer up) and subsample (integer down) combine to
        a rational factor that fills the width EXACTLY (880/320 = 11/4 becomes
        zoom(11).subsample(4)). A pathological ratio falls back to the nearest
        integer zoom, and an oversized picture is subsampled down. Cached per
        (id, width) so a repaint at the same size costs nothing."""
        native = self._load_image(image_id)
        if native is None:
            return None
        iw = native.width() or 1
        key = (image_id, target_w)
        cached = self._scaled_cache.get(key)
        if cached is not None:
            return cached
        if iw == target_w:
            scaled = native
        else:
            # Pillow first, when the machine has it (Stefan's ruling,
            # 2026-07-28, the one sanctioned exception beside arcimg's own:
            # the authors who use arc_image have Pillow installed, and exact
            # width gives them a perfect representation for debugging their
            # games). Nearest-neighbour, so the pixels stay crisp.
            scaled = self._pil_scaled(image_id, target_w)
            if scaled is None:
                # The zero-dependency standard: tk's zoom-then-subsample
                # chain scales by quarter steps (4.25x, 4.5x, 4.75x), so the
                # picture lands within a quarter of the native width of the
                # target at any window size, crisp, with the bar's edge fill
                # dressing the small remainder.
                if iw <= target_w:
                    best = None
                    for b in (4, 2, 1):
                        a = (target_w * b) // iw
                        if a < b:
                            a = b
                        # keep the intermediate zoom's memory sane
                        while a > b and iw * a > 8192:
                            a -= 1
                        w = iw * a // b
                        if w <= target_w and (best is None or w > best[2]):
                            best = (a, b, w)
                    a, b, _w = best
                    scaled = native.zoom(a) if a > 1 else native
                    if b > 1:
                        scaled = scaled.subsample(b)
                else:
                    f = max(1, -(-iw // target_w))  # ceil: never overshoot
                    scaled = native.subsample(f)
        self._scaled_cache[key] = scaled
        return scaled

    def _pil_scaled(self, image_id: int, target_w: int):
        """Exact-width scaling through Pillow when available (sanctioned:
        see _scaled_image): nearest-neighbour keeps the pixel art crisp, and
        the result becomes a tk PhotoImage through an in-memory PPM. None
        when Pillow is absent or anything fails; the tk path stands in."""
        try:
            from PIL import Image
        except ImportError:
            return None
        try:
            import io
            raw = self._load_image_bytes(image_id)
            if raw is None:
                return None
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            iw, ih = img.size
            th = max(1, round(ih * target_w / iw))
            img = img.resize((target_w, th), Image.NEAREST)
            buf = io.BytesIO()
            img.save(buf, format="PPM")
            return tk.PhotoImage(data=buf.getvalue())
        except Exception:
            return None

    def _band_width(self) -> int:
        """The width the band scales to: the CELL GRID's exact pixel width
        (columns times cell width), so the picture, the status bar, and the
        text always share one width and one left edge. The raw canvas width
        can be up to a cell wider (the integer division's remainder), which
        made the fullscreen bar run visibly short of the picture (Stefan's
        report, 2026-07-28); the remainder now stays background margin on
        the right, same as the grid's own."""
        cols = getattr(self, "_cols", 80)
        return max(20, cols) * self.cell_w

    def _repaint_image(self) -> None:
        img = self.vm.screen.image  # (id, mode) or None
        # The change key folds in the band's real width (a font-size change or
        # a WINDOW RESIZE rescales; the field report was fullscreen leaving
        # the picture at the 80-cell width), the cell height, and the game
        # background (a background change repaints the band's letterbox), so
        # the band only redraws when something it shows actually changed.
        target_w = self._band_width()
        state = (None if img is None
                 else (img, target_w, self.cell_h, self.vm.screen.bg))
        if state == self._drawn_image:
            return  # nothing changed (the dedup: no reload, no flicker)
        self._drawn_image = state
        self._image_canvas.delete("all")
        if img is None:
            self._image_canvas.configure(height=0)
            self._band_h = 0
            self._band_px = 0
            self._relayout()
            return
        # The band's HEIGHT follows the scaled picture, so the aspect holds at
        # any window width (fullscreen included); at the ordinary 80-cell width
        # this equals mode * cell_h exactly, the fixed-screen geometry. The
        # mode height stands in when the picture itself is missing.
        image_id, mode = img
        photo = self._scaled_image(image_id, target_w)
        if photo is not None:
            band_h = photo.height()
            self._band_px = photo.width()
        else:
            band_h = mode * self.cell_h if mode and mode > 0 else 0
            self._band_px = 0
        # The picture is centered in the band (at the ordinary width it fills
        # it edge to edge, so nothing moves); the band wears the game
        # background so any letterbox margin is the game's colour.
        self._image_canvas.configure(
            height=band_h,
            background=self._colour(self.vm.screen.bg, "black"),
        )
        if photo is not None:
            # Centered within the grid width (edge to edge at that width),
            # left-aligned with the bar and the text.
            self._image_canvas.create_image(target_w // 2, 0, image=photo,
                                            anchor="n")
        self._band_h = band_h
        self._relayout()  # the text below re-fits to whole lines under the band
        if self._grid_shown:
            self._redraw_grid()  # the bar's edge fill follows the band width

    def _colour(self, value, default: str) -> str:
        """A cell/model colour as a tk colour: 1 (or anything unmapped) is
        the front-end default, 2..12 the standard set via the Standard's
        recommended true colours, a #rrggbb string passes through. With
        Game Colours off (the View menu), everything is the default:
        black on white paper, styles kept, an e-reader's idea of a game."""
        if not self._use_colours.get():
            return default
        if isinstance(value, str):
            return value
        word = TRUE_COLOURS.get(value)
        return true_colour_hex(word) if word is not None else default

    def _redraw_grid(self) -> None:
        model = self.vm.screen
        m = self._margin
        if model.rows == 0:
            if self._grid_shown:
                self.canvas.pack_forget()
                self._grid_shown = False
                self._relayout()
            return
        if not self._grid_shown:
            # Left/right frame, same as the picture and text; no vertical inset
            # (the bar sits flush under the picture and above the text).
            self.canvas.pack(fill="x", before=self._lower_frame, padx=m)
            self._grid_shown = True
            self._relayout()
        self.canvas.configure(height=model.rows * self.cell_h)
        self.canvas.delete("all")
        for r in range(1, model.rows + 1):
            row = model.grid[r - 1]
            y = (r - 1) * self.cell_h
            c = 0
            while c < model.cols:
                # A run of cells sharing one look draws as one segment.
                start = c
                key = (row[c].style, row[c].fg, row[c].bg)
                while c < model.cols and (row[c].style, row[c].fg, row[c].bg) == key:
                    c += 1
                chars = "".join(cell.char for cell in row[start:c])
                x = start * self.cell_w
                style, fg, bg = key
                fg_c = self._colour(fg, "black")
                bg_c = self._colour(bg, self._window_bg)
                if style & REVERSE:
                    fg_c, bg_c = bg_c, fg_c
                if bg_c != self._window_bg:
                    self.canvas.create_rectangle(
                        x, y, x + (c - start) * self.cell_w, y + self.cell_h,
                        fill=bg_c, width=0,
                    )
                if chars.strip():
                    self.canvas.create_text(
                        x, y, text=chars, anchor="nw", fill=fg_c,
                        font=self._styled_font(style),
                    )
            # Stefan's fill (2026-07-28): the band canvas spans the whole
            # window and wears the game background, so its letterbox READS
            # as picture; the bar must reach the same edge or it looks
            # short (the fullscreen reports). Paint every upper row from
            # its last cell to the canvas's real right edge in the row's
            # own trailing colour: flush with the band strip at any width,
            # any scaler, any cause. No scaling tricks, no dependencies.
            row_px = model.cols * self.cell_w
            edge = max(self.canvas.winfo_width(),
                       getattr(self, "_band_px", 0))
            if edge > row_px and row:
                last = row[-1]
                lf = self._colour(last.fg, "black")
                lb = self._colour(last.bg, self._window_bg)
                if last.style & REVERSE:
                    lf, lb = lb, lf
                if lb != self._window_bg:
                    self.canvas.create_rectangle(
                        row_px, y, edge, y + self.cell_h,
                        fill=lb, width=0,
                    )

    def clear_story(self) -> None:
        # An erase paints the screen in the game's CURRENT background
        # (S 8.7.3.3): this is the moment zcolor.background takes over the
        # whole window rather than only the cells behind new text.
        bg = self._colour(self.vm.screen.bg, "white")
        if bg != self._window_bg:
            self._window_bg = bg
            fg = self._colour(self.vm.screen.fg, "black")
            self.text.configure(background=bg, insertbackground=fg)
            self.canvas.configure(background=bg)
            self._image_canvas.configure(background=bg)  # band letterbox = paper
            # The frame around the screen follows the game background too, so it
            # reads as a matte, not a white border on a dark game.
            self.root.configure(background=bg)
            self._lower_frame.configure(background=bg)
            self._tags_made.clear()  # cached looks resolved the old paper
            for tag in self.text.tag_names():
                if tag.startswith("look-"):
                    self.text.tag_delete(tag)
        self.text.delete("1.0", "end")
        self.text.mark_set("input_start", "end-1c")
        self._pager.reset(0)  # a wiped screen starts a fresh page

    # -- output --------------------------------------------------------------

    def _styled_font(self, style: int):
        if style & BOLD and style & ITALIC:
            return self.font_bold_italic
        if style & BOLD:
            return self.font_bold
        if style & ITALIC:
            return self.font_italic
        return self.font

    def _look_tag(self) -> str:
        """A Text tag for the model's CURRENT look (style + colours),
        created on first use. Roman-default text uses no tag at all."""
        m = self.vm.screen
        style, fg, bg = m.style, m.fg, m.bg
        if style == 0 and fg == 1 and bg == 1:
            return ""
        name = f"look-{style}-{fg}-{bg}"
        if name not in self._tags_made:
            self._configure_look(name, style, fg, bg)
            self._tags_made.add(name)
        return name

    def _configure_look(self, name: str, style: int, fg, bg) -> None:
        fg_c = self._colour(fg, "black")
        bg_c = self._colour(bg, self._window_bg)
        if style & REVERSE:
            fg_c, bg_c = bg_c, fg_c
        self.text.tag_configure(
            name, foreground=fg_c, background=bg_c,
            font=self._styled_font(style),
        )

    def append_story(self, s: str) -> None:
        # A print can land MID-READ: a timed-input interrupt routine spoke
        # (S 8.4.2 asks the interpreter to redisplay the line after). The
        # typed text lifts off, the story text goes in, the line comes back.
        typed = ""
        if self._reading_line:
            typed = self.text.get("input_start", "end-1c")
            self.text.delete("input_start", "end-1c")
        tag = self._look_tag()
        self.text.mark_set("insert", "end-1c")
        self._insert_paged(s, tag)
        self.text.mark_set("input_start", "end-1c")
        if typed:
            self._insert_input(typed)
        self.text.see("end")

    # -- [MORE] paging ---------------------------------------------------------
    #
    # A passage taller than the reading area would otherwise scroll past, and
    # this window has no [MORE] of its own to stop it (the curses front end has
    # always had one). The text goes in a page at a time: when the page fills,
    # a reverse-video [MORE] is APPENDED at the end of what has been shown, so
    # it covers nothing, and any key prints the next page. The page is measured
    # from the text area's CURRENT height, so a picture band taking rows or a
    # fullscreen window giving them back is accounted for by itself.

    def _page_height(self) -> int:
        """Display lines the reader gets before the pause, one row kept for
        the [MORE] itself."""
        try:
            rows = int(self.text.cget("height"))
        except (tk.TclError, ValueError):
            return 0
        return rows - 1

    def _insert(self, s: str, tag: str) -> None:
        if tag:
            self.text.insert("end-1c", s, (tag,))
        else:
            self.text.insert("end-1c", s)

    def _insert_paged(self, s: str, tag: str) -> None:
        page = self._page_height()
        # Mid-read printing (a timed interrupt) and key waits must not open a
        # second wait inside the first, and a screen with no room to page
        # cannot pause at all: in both cases the text goes in whole.
        if page < 2 or self._reading_line or self._reading_key or self._closed:
            self._insert(s, tag)
            self._pager.reset(0)
            return
        rest = s
        while rest:
            room = page - self._pager.lines
            if room <= 0:
                self._page_pause()
                if self._closed:
                    self._insert(rest, tag)
                    return
                continue
            piece, rest = self._pager.feed(rest, max(2, self._cols), room)
            if piece:
                self._insert(piece, tag)
            if rest:
                self._page_pause()
                if self._closed:
                    self._insert(rest, tag)
                    return

    def _page_pause(self) -> None:
        """Show [MORE] at the end of the text and wait for any key."""
        mark = self.text.index("end-1c")
        self._insert("[MORE]", self._more_tag())
        self.text.see("end")
        self._reading_key = True
        self._key.set("")
        self.root.wait_variable(self._key)
        self._reading_key = False
        # The marker never becomes part of the transcript on screen: it is
        # taken out again, and the story text continues exactly where it was.
        self.text.delete(mark, "end-1c")
        self._pager.reset(self._pager.column)

    def _more_tag(self) -> str:
        """The marker wears the CURRENT look, reversed: on a game-coloured
        screen it is the game's own colours the other way round, the way the
        curses front end draws its [MORE] in A_REVERSE."""
        m = self.vm.screen
        name = f"more-{m.style}-{m.fg}-{m.bg}"
        if name not in self._tags_made:
            self._configure_look(name, m.style ^ REVERSE, m.fg, m.bg)
            self._tags_made.add(name)
        return name

    def _insert_input(self, s: str) -> None:
        """Text into the editable region, wearing the input look. The
        input_start mark's left gravity keeps it before what is inserted."""
        if self._input_tag:
            self.text.insert("end-1c", s, (self._input_tag,))
        else:
            self.text.insert("end-1c", s)

    # -- input: lines ----------------------------------------------------------

    def wait_for_line(self, max_len, preload="", terminators=frozenset(),
                      timeout=0.0, on_timeout=None):
        if self._closed:
            raise EOFError
        self._max_len = max_len
        self._terminators = terminators
        self._terminator = 13
        self._timed_out = False
        # The input wears the CURRENT look: Cosmos sets the input colour
        # (zcolor.input) right before every read, so the tag resolved here
        # is the game's choice; the caret matches it.
        self._input_tag = self._look_tag()
        self.text.configure(
            insertbackground=self._colour(self.vm.screen.fg, "black")
        )
        self._reading_line = True
        self._line_ready.set(False)
        if preload:
            self._absorb_preload(preload)
        self.text.mark_set("insert", "end-1c")
        self._pager.reset(self._pager.column)
        self._start_timer(timeout, on_timeout)
        self.root.wait_variable(self._line_ready)
        self._stop_timer()
        self._reading_line = False
        if self._closed:
            raise EOFError
        self._dress_input()
        line = self.text.get("input_start", "end-1c")
        if self._timed_out:
            # The interrupt ended the read: what was typed goes back to the
            # game as buffer leftovers (next read's preload), so it comes
            # off the screen; the game owns it now.
            self.text.delete("input_start", "end-1c")
            return line, 0
        # The typed line becomes story text, newline included.
        self.append_story("\n")
        self._pager.reset(0)
        return line, self._terminator

    def _absorb_preload(self, preload: str) -> None:
        """The game handed the read a part-typed line (S 15 read, byte 1).
        By convention the game has already printed it, so the characters
        sit at the end of the story text: pull the input mark back over
        them and they become editable, exactly as if typed. If they are
        not there (a timed-out line coming back), insert them."""
        n = len(preload)
        if self.text.get(f"input_start -{n} chars", "input_start") == preload:
            self.text.mark_set("input_start", f"input_start -{n} chars")
            self._dress_input()
        else:
            self._insert_input(preload)

    # -- timed input: the after() loop that makes interrupts fire --------------

    def _start_timer(self, timeout, on_timeout) -> None:
        if timeout > 0 and on_timeout:
            self._timer = self.root.after(
                max(1, int(timeout * 1000)), self._tick, timeout, on_timeout
            )

    def _stop_timer(self) -> None:
        if self._timer is not None:
            self.root.after_cancel(self._timer)
            self._timer = None

    def _tick(self, timeout, on_timeout) -> None:
        # Fires inside the event loop while the VM is parked in
        # wait_variable; on_timeout re-enters the VM for the interrupt
        # routine (vm.call_interrupt), whose printing lands through
        # append_story's mid-read path. True means end the input.
        self._timer = None
        if self._closed or not (self._reading_line or self._reading_key):
            return
        if on_timeout():
            self._timed_out = True
            if self._reading_line:
                self._line_ready.set(True)
            else:
                self._key_code = 0
                self._key.set("\x00")
        else:
            self._start_timer(timeout, on_timeout)

    def _dress_input(self) -> None:
        if self._input_tag:
            self.text.tag_add(self._input_tag, "input_start", "end-1c")

    def _on_key_release(self, event):
        # Freshly typed characters carry no tag; sweep the input region so
        # the line shows its colour as it is typed, not only on commit.
        if self._reading_line:
            self._dress_input()

    def _on_return(self, event):
        # Return answers a key-wait too: "press any key" must mean ANY key
        # (the dedicated binding fires before _on_key, so feed the wait
        # here; Stefan's play-through caught space working and Return not).
        if self._reading_key:
            self._key_code = 13
            self._key.set("\n")
            return "break"
        if self._reading_line:
            self._line_ready.set(True)
        return "break"

    def _on_backspace(self, event):
        if self._reading_key:
            self._key_code = 8  # ZSCII 8, delete
            self._key.set("\x08")
            return "break"
        # Never eat into the story text before the input mark.
        if not self._reading_line:
            return "break"
        if self.text.compare("insert", "<=", "input_start"):
            return "break"
        return None

    def _on_key(self, event):
        if self._reading_key:
            if event.char:
                self._key_code = ord(event.char)
                self._key.set(event.char)
            else:
                code = _FUNCTION_KEYS.get(event.keysym)
                if code:
                    self._key_code = code
                    self._key.set("\x00")
            return "break"
        if not self._reading_line:
            return "break"  # story is thinking: swallow stray typing
        if not event.char:
            # A function key ends the line if the story's terminating-
            # characters table names it (S 10.7); 255 names them all.
            code = _FUNCTION_KEYS.get(event.keysym)
            if code and (code in self._terminators or 255 in self._terminators):
                self._terminator = code
                self._line_ready.set(True)
                return "break"
            # The caret never leaves the input line (the field report: arrow
            # keys walked it up into the transcript). Page keys scroll the
            # VIEW only; Home means the start of the INPUT; Left stops at
            # the prompt. Up and Down do nothing until they mean history.
            if event.keysym in ("Up", "Down"):
                return "break"
            if event.keysym in ("Prior", "Next"):
                self.text.yview_scroll(
                    -1 if event.keysym == "Prior" else 1, "pages")
                return "break"
            if event.keysym == "Home":
                self.text.mark_set("insert", "input_start")
                return "break"
            if event.keysym == "Left" and self.text.compare(
                    "insert", "<=", "input_start"):
                return "break"
            return None  # Right, End and friends keep their meaning
        if self.text.compare("insert", "<", "input_start"):
            self.text.mark_set("insert", "end-1c")
        # Typing pulls the view back to the prompt (the player may have
        # scrolled up to read; their keystrokes belong at the bottom).
        self.text.see("end")
        if len(self.text.get("input_start", "end-1c")) >= self._max_len:
            return "break"  # the buffer is full: the machine set the limit
        return None

    def _to_end(self):
        if self._reading_line:
            self.text.mark_set("insert", "end-1c")

    # -- input: single keys --------------------------------------------------------

    def wait_for_key(self, timeout=0.0, on_timeout=None) -> int:
        if self._closed:
            raise EOFError
        self._reading_key = True
        self._timed_out = False
        self._key_code = 0
        self._key.set("")
        self._pager.reset(self._pager.column)
        self._start_timer(timeout, on_timeout)
        self.root.wait_variable(self._key)
        self._stop_timer()
        self._reading_key = False
        if self._closed:
            raise EOFError
        # The reader just pressed a key of their own: a fresh page starts.
        self._pager.reset(self._pager.column)
        return 0 if self._timed_out else self._key_code

    # -- lifecycle --------------------------------------------------------------------

    def _on_close(self):
        self._closed = True
        # Unblock whichever wait is spinning so the run loop can unwind.
        self._line_ready.set(True)
        self._key.set("\n")
        self.root.destroy()

    def run(self) -> None:
        """Start the machine once the window is up, then hand the thread to
        tkinter. The VM blocks only inside wait_variable, so the window
        stays alive the whole way."""
        self.root.after(20, self._run_vm)
        self.root.mainloop()

    def _run_vm(self):
        try:
            self.vm.run()
            if not self._closed:
                self.append_story("\n[The story has ended.]\n")
        except EOFError:
            pass  # the window closed mid-read: nothing left to do
        except ActaeaError as e:
            if not self._closed:
                self.append_story(f"\n[actaea: {e}]\n")


def play(story, title: str, images_dir=None, images_zip=None, seed=None) -> None:
    ActaeaApp(story, title, images_dir, images_zip, seed).run()
