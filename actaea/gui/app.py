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
from ..screen import BOLD, FIXED, ITALIC, REVERSE, TRUE_COLOURS, true_colour_hex
from ..vm import VM
from . import dress
from . import fonts as fontpack

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
        # Atomic: write beside, rename over. A process dying mid-dump left a
        # torn file that read back as NOTHING, and every setting silently
        # fell to its default (Stefan's text size went 14 -> 13 overnight
        # that way). rename on the same filesystem cannot tear.
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
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
                 seed=None, root=None, story_path=None):
        # A bare launch hands its file-dialog root along to BE this window's
        # root: this platform's Tk does not survive a second one.
        self.root = root if root is not None else tk.Tk()
        self.root.deiconify()
        self.root.title(f"{title} - Actaea")
        # Remembered for the On Launch "open the last story" preference.
        self._story_path = story_path
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
        # The picture the band's GEOMETRY was last sized for; the sentinel is
        # distinct from None, which means "no picture" (see _grid_changed).
        self._band_state = False
        # Settings the menu drives, remembered across sessions; colours
        # before anything calls _colour.
        st = _load_settings()
        self._use_colours = tk.BooleanVar(value=bool(st.get("game_colours", True)))
        self._font_size = tk.IntVar(value=int(st.get("size", 13)))
        self._rows_var = tk.IntVar(value=int(st.get("rows", 30)))
        # THE SHAPE OF THE WINDOW. Modern is the taller, book-like 4:5 that
        # modern desktop interpreters open in; classic is the 4:3 of the machines the
        # format came from. The window is 80 cells wide either way, so the
        # ratio decides the height, and both are relative: a bigger font makes
        # a bigger window of the same shape.
        self._aspect_var = tk.StringVar(
            value=st.get("aspect", "modern") if
            st.get("aspect") in ("modern", "classic") else "modern")
        # Where the window was when it was last closed, size and position
        # both ("WxH+X+Y"), so it opens where the player left it.
        self._saved_geometry = st.get("geometry") or ""
        # A bare 'actaea' (the dock-icon launch) either asks for a story or
        # reopens the last one; the player chooses in View > On Launch.
        self._launch_var = tk.StringVar(
            value=st.get("on_launch")
            if st.get("on_launch") in ("ask", "last") else "ask")
        self._mac_integration()
        # The star: Dock tile (macOS), title-bar and taskbar icon where
        # the platform shows one. Dressing never stops a story.
        dress.dress(self.root)

        # THE LOOK (Actaea 2.0). Three named typographic identities, never
        # freely mixable (Stefan's ruling): Novel, serif prose over a mono
        # machine voice, the default; Clean, sans prose over the same mono;
        # Retro, one pixel face for everything, the way a real 8-bit screen
        # was. The faces ship with Actaea and are registered with the OS at
        # startup (fonts.py); the eight font objects below are SHARED by the
        # widget, the tags, and the grid, and a look or size change
        # reconfigures them in place, so even text already on screen changes
        # its clothes.
        self._look_var = tk.StringVar(
            value=st.get("look") if st.get("look") in fontpack.LOOKS
            else fontpack.DEFAULT_LOOK)
        fontpack.register()
        self.font = tkfont.Font(root=self.root)
        self.font_bold = tkfont.Font(root=self.root, weight="bold")
        self.font_italic = tkfont.Font(root=self.root, slant="italic")
        self.font_bold_italic = tkfont.Font(root=self.root, weight="bold",
                                            slant="italic")
        self.font_prose = tkfont.Font(root=self.root)
        self.font_prose_bold = tkfont.Font(root=self.root, weight="bold")
        self.font_prose_italic = tkfont.Font(root=self.root, slant="italic")
        self.font_prose_bold_italic = tkfont.Font(root=self.root,
                                                  weight="bold",
                                                  slant="italic")
        self._build_fonts()
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

        # The window IS the story's 80-cell screen, inside the frame.
        if self._sane_geometry(self._saved_geometry):
            try:
                self.root.geometry(self._saved_geometry)
                self._want_width = int(self._saved_geometry.split("x")[0])
                self._relayout()
            except (tk.TclError, ValueError):
                self._apply_geometry()
        else:
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
            frame, wrap="word", font=self.font_prose, undo=False,
            # A Text's DEFAULT requested width is eighty characters, and a
            # toplevel grows back to its children's natural size when it maps,
            # overriding wm geometry: the window could never be narrower than
            # eighty columns, whatever shape was asked for (measured: asked
            # 894 wide, mapped at 971). Request next to nothing instead; the
            # pack fill stretches to whatever the window really is, and the
            # window's own geometry is the only authority on size.
            width=20,
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
        # it, so nothing scrolls past unread. Paging is MEASURED: the widget
        # itself is asked where the page boundary fell (_insert_paged), so it
        # is exact for any face, fixed or proportional.
        # How many display lines the reading area has, kept by _relayout: the
        # widget's own pixel height lags a turn behind (see there).
        self._text_rows = 0
        # Guards the re-base against re-entering itself: it waits for keys,
        # which lets the event loop (and another resize) run.
        self._rebasing = False
        # The window height last asked for by the fit-to-contents snap; it is
        # compared against, never subtracted from (see _relayout).
        self._snapped_to = 0
        # The width this app ASKED for. The snap and any other height-only
        # adjustment must never read winfo_width() for it: geometry is
        # asynchronous, so mid-boot the widget still reports the previous
        # width, and re-asserting it flips the window between two widths,
        # re-wrapping every line while the pager is counting them (caught by
        # the GUI test as text scrolling off before the first pause).
        self._want_width = 0
        # True while a resize event is being handled. The snap below must not
        # run then: a resize rescales the picture, which would ask to fit the
        # window, which is another resize event (it ran away at 154% CPU on
        # Stefan's machine and could not be quit, 2026-08-20).
        self._in_resize = False
        self.text.mark_set("page_start", "end-1c")
        self.text.mark_gravity("page_start", "left")

        self._line_ready = tk.BooleanVar(value=False)
        self._key: tk.StringVar = tk.StringVar(value="")  # the wake signal
        self._key_code = 0            # the actual key, as a ZSCII/Unicode code
        self._reading_line = False
        self._reading_key = False
        self._closed = False
        # File > Open mid-session: the path to switch to. The waits treat a
        # pending switch like a close (EOFError unwinds the old machine), but
        # the window survives and boots the new story in place.
        self._switch_to = None
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
        # Cmd-Q on macOS quits the Tk app without WM_DELETE_WINDOW firing,
        # which lost the remembered geometry: route it through the same door.
        try:
            self.root.createcommand("tk::mac::Quit", self._on_close)
        except tk.TclError:
            pass
        self.text.focus_set()

        self.vm = VM(story, GuiIO(self), seed=seed)
        self.vm.screen.on_change = self._grid_changed
        self._build_menu()

    # -- the menu, the About panel, the settings ----------------------------------

    def _aqua(self) -> bool:
        return self.root.tk.call("tk", "windowingsystem") == "aqua"

    def _mac_integration(self) -> None:
        """macOS niceties. The BOLD name in the menu bar belongs to the
        hosting bundle, and dress.predress rewrites that bundle's
        in-memory name to Actaea; __main__ calls it before the first Tk
        root (the menu bar snapshots the name then), and the repeat here
        is a free second chance for anyone driving play() directly. The
        About item in that menu is ours, and so is the Apple Event a
        double-clicked story arrives on (the .app stub's launch path)."""
        if not self._aqua():
            return
        dress.predress()
        self.root.createcommand("tkAboutDialog", self._about)
        # Finder hands opened documents to a running app as Apple Events;
        # aqua Tk surfaces them through this command. Mid-session it is
        # exactly File > Open with the path already chosen.
        try:
            self.root.createcommand("::tk::mac::OpenDocument",
                                    self._open_documents)
        except tk.TclError:
            pass

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        if self._aqua():
            appmenu = tk.Menu(menubar, name="apple")
            appmenu.add_command(label="About Actaea", command=self._about)
            appmenu.add_separator()
            menubar.add_cascade(menu=appmenu)
        # File: the door. A story can open mid-session without quitting.
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="Open...", accelerator="Cmd+O",
                          command=self._open_dialog)
        menubar.add_cascade(label="File", menu=filem)
        self.root.bind("<Command-o>", lambda e: self._open_dialog())
        self.root.bind("<Control-o>", lambda e: self._open_dialog())

        view = tk.Menu(menubar, tearoff=0)
        # The Typeface menu is the whole typographic surface (Stefan's
        # ruling: no free font choices): three coherent identities, each a
        # prose face and a machine face that belong together.
        looks = tk.Menu(view, tearoff=0)
        for value, label in (("novel", "Novel"), ("clean", "Clean"),
                             ("retro", "Retro")):
            looks.add_radiobutton(label=label, variable=self._look_var,
                                  value=value, command=self._relook)
        size = tk.Menu(view, tearoff=0)
        for n in (11, 12, 13, 14, 16, 18, 20):
            size.add_radiobutton(label=f"{n} pt", variable=self._font_size,
                                 value=n, command=self._retype)
        lines = tk.Menu(view, tearoff=0)
        for n in (25, 30, 35, 40):
            lines.add_radiobutton(label=f"{n} lines", variable=self._rows_var,
                                  value=n, command=self._reheight)
        shape = tk.Menu(view, tearoff=0)
        shape.add_radiobutton(label="Modern (4:5)", variable=self._aspect_var,
                              value="modern", command=self._reshape)
        shape.add_radiobutton(label="Classic (4:3)", variable=self._aspect_var,
                              value="classic", command=self._reshape)
        view.add_cascade(label="Typeface", menu=looks)
        view.add_cascade(label="Text Size", menu=size)
        view.add_cascade(label="Window Shape", menu=shape)
        view.add_cascade(label="Screen Height", menu=lines)
        view.add_separator()
        view.add_checkbutton(label="Game Colors", variable=self._use_colours,
                             command=self._colours_toggled)
        menubar.add_cascade(label="Visuals", menu=view)

        # Settings: behaviour, not appearance. On Launch lives here; it
        # never belonged under a visuals menu.
        settings = tk.Menu(menubar, tearoff=0)
        launch = tk.Menu(settings, tearoff=0)
        launch.add_radiobutton(label="Ask for a story",
                               variable=self._launch_var, value="ask",
                               command=self._persist)
        launch.add_radiobutton(label="Open the last story",
                               variable=self._launch_var, value="last",
                               command=self._persist)
        settings.add_cascade(label="On Launch", menu=launch)
        menubar.add_cascade(label="Settings", menu=settings)
        if not self._aqua():
            helpm = tk.Menu(menubar, tearoff=0)
            helpm.add_command(label="About Actaea", command=self._about)
            menubar.add_cascade(label="Help", menu=helpm)
        self.root.config(menu=menubar)

    def _about(self) -> None:
        """The About panel, laid out like one: the star, the name large,
        the facts in their own lines, the repository clickable, and the
        bundled typefaces' license record one click away."""
        win = tk.Toplevel(self.root)
        win.title("About Actaea")
        win.resizable(False, False)
        star = dress.icon_path("actaea-about.png")
        if star:
            try:
                img = tk.PhotoImage(file=star)
                badge = tk.Label(win, image=img)
                badge._star = img  # keep referenced or Tk drops it
                badge.pack(pady=(20, 0))
            except tk.TclError:
                pass
        name_font = tkfont.nametofont("TkDefaultFont").copy()
        name_font.configure(size=24, weight="bold")
        tk.Label(win, text="Actaea", font=name_font).pack(padx=48, pady=(6, 0))
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
        row = tk.Frame(win)
        row.pack(pady=(2, 16))
        lic = fontpack.licenses_path()
        if lic:
            tk.Button(row, text="Typeface Licenses",
                      command=lambda: webbrowser.open(
                          "file://" + lic)).pack(side="left", padx=(0, 8))
        tk.Button(row, text="OK", command=win.destroy).pack(side="left")
        win.bind("<Return>", lambda e: win.destroy())
        win.bind("<Escape>", lambda e: win.destroy())
        win.transient(self.root)
        # Centered over the game window, not wherever the window manager
        # drops a fresh toplevel (Stefan, 2026-08-21).
        win.update_idletasks()
        x = (self.root.winfo_rootx()
             + (self.root.winfo_width() - win.winfo_reqwidth()) // 2)
        y = (self.root.winfo_rooty()
             + max(0, (self.root.winfo_height()
                       - win.winfo_reqheight()) // 3))
        win.geometry("+%d+%d" % (max(0, x), max(0, y)))
        win.grab_set()

    def _persist(self) -> None:
        """Write the settings soon, not now: a menu action that just asked
        for a new window size must not record the size the window still has.
        root.geometry() is asynchronous, and persisting in the same breath
        saved the OLD height, which is why a reshaped window reopened short
        (Stefan, 2026-08-21). Closing writes immediately (_persist_now)."""
        if getattr(self, "_persist_job", None) is not None:
            try:
                self.root.after_cancel(self._persist_job)
            except tk.TclError:
                pass
        self._persist_job = self.root.after(400, self._persist_now)

    def _persist_now(self) -> None:
        self._persist_job = None
        _save_settings({
            "look": self._look_var.get(),
            "on_launch": self._launch_var.get(),
            "last_story": self._story_path
            or _load_settings().get("last_story"),
            "size": self._font_size.get(),
            "rows": self._rows_var.get(),
            "game_colours": self._use_colours.get(),
            "aspect": self._aspect_var.get(),
            "geometry": self._geometry_now(),
        })

    def _geometry_now(self) -> str:
        """The window as it stands, size and position ("WxH+X+Y"), so the next
        run opens where this one was left rather than wherever the window
        manager feels like. A geometry that never got applied (Tk's 200x200
        default) is NOT the window as it stands: persisting one poisoned the
        settings once, and every later launch faithfully restored the
        accident (Stefan's tiny-window hunt, 2026-08-21). An insane reading
        keeps the previous good value."""
        try:
            self.root.update_idletasks()
            geo = self.root.winfo_geometry()
        except tk.TclError:
            return self._saved_geometry
        return geo if self._sane_geometry(geo) else self._saved_geometry

    @staticmethod
    def _sane_geometry(geo: str) -> bool:
        """A believable remembered window: laid out at least once."""
        try:
            size = geo.split("+")[0]
            w, h = (int(v) for v in size.split("x"))
        except (ValueError, AttributeError):
            return False
        return w >= 400 and h >= 300

    def _apply_geometry(self) -> None:
        """The window at the chosen aspect."""
        self.cell_w = self.font.measure("0")
        self.cell_h = self.font.metrics("linespace")
        w, h = self._aspect_size()
        self._want_width = w
        self.root.geometry(f"{w}x{h}")
        self._relayout()

    def _aspect_size(self):
        """The window's size for the chosen shape.

        Modern is the portrait page of the modern desktop interpreters:
        4:5, taller than wide. On a big display that is exactly what opens. On a laptop
        it cannot be had at full width: portrait at eighty columns needs some
        1250 points of height and the desktop has about 900 once the menu bar
        and dock take theirs (the reference crop that briefly turned this
        ratio landscape was itself a clamped window, not the intent). So the
        shape scales down keeping the ratio, and when it reaches the
        seventy-column floor the width holds and the height takes everything
        the desktop honestly offers, which lands as tall as the screen
        allows: the nearest portrait the machine has. The room comes from
        wm_maxsize, the window manager's own account of the usable area, so
        the dock is finally part of the arithmetic instead of a surprise.
        Classic is the squat 4:3 of the machines the format came from, at
        the full eighty columns."""
        m = self._margin
        try:
            usable = self.root.wm_maxsize()[1]
        except tk.TclError:
            usable = self.root.winfo_screenheight()
        # wm_maxsize accounts for the dock but NOT for the menu bar, the
        # title bar, or the few points of placement slack under the menu bar.
        # Asking for more than truly fits made macOS clamp the window, the
        # whole-row fit then trimmed the clamped result, and that shrunken
        # height was persisted and restored forever after (Stefan's settings
        # remembered 860x793 where 860x852 fits): ask only for what fits.
        room = usable - 65
        width = 80 * self.cell_w + 2 * m
        if self._aspect_var.get() == "classic":
            return width, min(width * 3 // 4, room)
        height = width * 5 // 4
        if height > room:
            height = room
            width = height * 4 // 5
            floor = 70 * self.cell_w + 2 * m
            if width < floor:
                width = floor
        return width, height

    def _reshape(self) -> None:
        """The aspect changed from the menu: reshape in place, keeping the
        window where the player put it."""
        w, h = self._aspect_size()
        self.root.geometry(f"{w}x{h}")
        self._relayout()
        self._persist()

    def _rows_geometry(self) -> None:
        """The Screen Height menu asks for an exact number of text rows, which
        overrides the aspect until the aspect is chosen again."""
        m = self._margin
        self._want_width = 80 * self.cell_w + 2 * m
        self.root.geometry(
            f"{80 * self.cell_w + 2 * m}"
            f"x{self._rows_var.get() * self.cell_h + 2 * m}"
        )
        self._relayout()

    def _relayout(self, snap: bool = False) -> None:
        """Set the text area to a WHOLE number of lines, so scrolled text never
        shows a half-clipped row at the top (the picture band and status bar can
        be any pixel height; the text below them takes the whole lines that fit
        and the leftover pixels join the bottom margin)."""
        if not hasattr(self, "text"):
            return  # called once from __init__ before the widgets exist
        band = getattr(self, "_band_h", 0)
        status = self.cell_h if getattr(self, "_grid_shown", False) else 0
        line_h = getattr(self, "line_h", self.cell_h)
        # The real window height wins once the window is mapped: fullscreen
        # and maximize add rows the settings never knew about, and the story
        # text should claim them (Stefan's report: the picture scaled while
        # the text stayed at its settings height). Before mapping, the
        # settings height stands.
        real = self.root.winfo_height() if hasattr(self, "root") else 0
        if real > 5 * line_h:
            avail = real - 2 * self._margin - band - status
        else:
            avail = self._rows_var.get() * line_h - band - status
        n = max(1, avail // line_h)
        # A window's-eye view of its own arithmetic, for diagnosing a reading
        # area that does not match what the player sees. Off unless asked for:
        #   ACTAEA_GEOM=1 actaea story.z5      (writes ~/actaea-geom.log)
        if os.environ.get("ACTAEA_GEOM"):
            try:
                with open(os.path.expanduser("~/actaea-geom.log"), "a") as fh:
                    fh.write(
                        "relayout: window=%d margin=%d band=%d bar=%d "
                        "avail=%d cell_h=%d rows=%d leftover_px=%d "
                        "text_px_now=%d\n"
                        % (real, self._margin, band, status, avail,
                           self.cell_h, n, avail - n * self.cell_h,
                           self.text.winfo_height()))
            except OSError:
                pass
        # The authority on how tall the reading area is. Tk applies a geometry
        # change when it next goes idle, and the story prints a whole boot
        # (intro, banner, opening room) without ever returning to the event
        # loop, so asking the widget for its pixel height mid-boot answers with
        # the size it had before the picture band arrived. This number is right
        # the moment it is computed, and the pager reads it.
        # THE WINDOW GIVES UP THE REMAINDER. A picture scaled to the window's
        # width is as tall as its aspect makes it, so what is left for text is
        # rarely a whole number of lines, and those few orphan pixels read as a
        # blank row wherever they are put (all three placements were tried on
        # Stefan's screen and all three were wrong). The window is therefore
        # resized to fit its contents exactly, ONCE, when the furniture
        # changes: the height is computed from first principles rather than
        # subtracted from the current one, so it converges instead of walking
        # the window down a few pixels per layout, which is what an earlier
        # attempt did. Never on a plain resize, so it cannot fight a drag.
        # NEVER SNAP AN UNMAPPED WINDOW. The snap fits the window to its
        # contents, and during boot it can fire before the window manager has
        # applied the initial geometry: it then measures Tk's 200-pixel
        # default, "fits" the window to six lines, and its own only-once
        # guard holds the accident (Stefan's tiny launches; his geometry log
        # caught it: window=200 at first layout, snapped to 181 and locked;
        # the millisecond race with the WM is why harnesses, which force the
        # layout before the story runs, never reproduced it). The
        # believability test from the settings work answers the question.
        if (snap and not self._in_resize and real > 5 * self.cell_h
                and self._sane_geometry(
                    "%dx%d" % (self.root.winfo_width(), real))):
            want = 2 * self._margin + band + status + n * line_h
            if want != real and want != self._snapped_to:
                self._snapped_to = want
                w_now = self._want_width or self.root.winfo_width()
                self.root.geometry("%dx%d" % (w_now, want))
        was = self._text_rows
        self._text_rows = n
        if int(self.text.cget("height")) != n:
            self.text.configure(height=n)
            # The pixels follow later: Tk resizes the widget when it next goes
            # idle, and update_idletasks here does NOT bring that forward (it
            # was measured: still 439 pixels for a widget just told to be six
            # lines). So the row count above is the authority mid-turn, and
            # the VIEW is put right on the idle pass that does the resize, and
            # again before the story waits for input (_settle_view). Tk keeps
            # the TOP line when a Text widget shrinks, so without that the
            # prompt ends up below the bottom edge and stays there.
            self.text.after_idle(self._tail_into_view)
            # A SHRINK OVER UNREAD TEXT RE-BASES RATHER THAN SCROLLS. The
            # picture band claiming its rows is the case docs/08 section 3
            # legislates for, and the rule there is absolute: the re-base
            # never eats a line. The same applies to the status bar taking
            # its row and to the player shrinking the window mid-turn.
            if was > n:
                self._rebase_page()

    def _on_root_resize(self, event=None) -> None:
        """Fullscreen and maximize change the window's real width: recompute
        the column count, re-stamp the header, and re-width the cell grid
        (vm.screen_resized does both), so the game paints its status bar
        across the whole window on its next turn, the v5 way (no resize
        interrupt exists; the console front-end behaves identically)."""
        if not hasattr(self, "text") or not hasattr(self, "vm"):
            return
        if self._in_resize:
            return
        self._in_resize = True
        try:
            self._resize_body()
        finally:
            self._in_resize = False

    def _resize_body(self) -> None:
        # The player's own hand sets the width now: it becomes the one the
        # height-only adjustments preserve.
        self._want_width = self.root.winfo_width()
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
        self._rows_geometry()
        self._persist()

    def _build_fonts(self) -> None:
        """Shape the shared font objects to the current look and text size,
        and refresh the metrics everything else measures with.

        The mono four dress the machine voice: the status grid, the input
        line, the [MORE] marker, and fixed-pitch text. The prose four dress
        the story. Retro points both at monogram, one face for everything,
        at the size Stefan's ratio derives (24 reads like Noto's 14),
        snapped to the pixel grid of eights so it stays crisp."""
        look = self._look_var.get()
        prose_fam, mono_fam = fontpack.resolve(look, self.root)
        base = self._font_size.get()
        # The menu size MEANS Noto: every face wears its optical factor so
        # all looks read at the same apparent size (Stefan's ruling; the
        # factors live in fonts.OPTICAL_FACTORS, one number per face).
        prose_size = fontpack.scaled_size(prose_fam, base)
        mono_size = fontpack.scaled_size(mono_fam, base)
        retro = look == "retro"
        # Retro's bold is the DRAWN cut (its own family, generated from
        # monogram; see fonts.RETRO_BOLD): the family carries the boldness,
        # so the weight stays normal and the matcher never guesses. The
        # slant stays pinned in Retro: the italic cut is retired and a
        # synthetic oblique shears pixel stems.
        bold_fam_mono, bold_fam_prose, bold_weight = mono_fam, prose_fam, "bold"
        if retro and fontpack.usable(self.root, fontpack.RETRO_BOLD):
            bold_fam_mono = bold_fam_prose = fontpack.RETRO_BOLD
            bold_weight = "normal"
        it_slant = "roman" if retro else "italic"
        self.font.configure(family=mono_fam, size=mono_size,
                            weight="normal", slant="roman")
        self.font_bold.configure(family=bold_fam_mono, size=mono_size,
                                 weight=bold_weight, slant="roman")
        self.font_italic.configure(family=mono_fam, size=mono_size,
                                   weight="normal", slant=it_slant)
        self.font_bold_italic.configure(family=bold_fam_mono, size=mono_size,
                                        weight=bold_weight, slant=it_slant)
        self.font_prose.configure(family=prose_fam, size=prose_size,
                                  weight="normal", slant="roman")
        self.font_prose_bold.configure(family=bold_fam_prose,
                                       size=prose_size, weight=bold_weight,
                                       slant="roman")
        self.font_prose_italic.configure(family=prose_fam, size=prose_size,
                                         weight="normal", slant=it_slant)
        self.font_prose_bold_italic.configure(family=bold_fam_prose,
                                              size=prose_size,
                                              weight=bold_weight,
                                              slant=it_slant)
        # The cell is the MONO cell (the Standard's screen units); the text
        # area lays out in PROSE lines, which are taller than the cell in
        # the serif look.
        self.cell_w = self.font.measure("0")
        self.cell_h = self.font.metrics("linespace")
        self.line_h = max(self.font_prose.metrics("linespace"), self.cell_h)

    def _relook(self) -> None:
        """The Look menu: reshape the shared fonts in place (text already on
        screen changes with them), let the column count and the grid follow
        the new cell, and re-fit the reading area. The window keeps its size
        and place; only the type changes."""
        self._build_fonts()
        if not self._in_resize:
            self._in_resize = True
            try:
                self._resize_body()
            finally:
                self._in_resize = False
        # The new face has a new line height: give the window's remainder up
        # so the reading area holds WHOLE lines of it (a half line peeking
        # out under the status bar was the first thing Stefan's eye found).
        self._relayout(snap=True)
        self._settle_view()
        self._persist()

    def _retype(self) -> None:
        self._build_fonts()
        self._apply_geometry()
        self._persist()

    def _colours_toggled(self) -> None:
        # Existing text KEEPS its tags; each look tag is reconfigured for
        # the new setting (deleting them would strip the story's text to
        # the widget default, black, invisible on a game-painted screen).
        bg = self._colour(self.vm.screen.bg, "white")
        self._window_bg = bg
        for tag in self.text.tag_names():
            if not tag.startswith(("look-", "input-", "more-")):
                continue
            fixed = tag.endswith("-f")
            body = tag[:-2] if fixed else tag
            kind, style, fg_part, bg_part = body.split("-", 3)
            style = int(style)
            if kind == "more":
                # The marker's NAME carries the plain style; its LOOK is
                # that style reversed (the [MORE] convention).
                style ^= REVERSE
            self._configure_look(tag, style,
                                 self._parse_colour(fg_part),
                                 self._parse_colour(bg_part),
                                 fixed if kind == "look" else False)
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
        # PAINTING is coalesced into one repaint per idle cycle: a bar paint
        # writes eighty cells and each one signals a change, so redrawing per
        # write would be absurd. The model signals grid AND picture changes
        # through here, so that repaint refreshes both.
        #
        # GEOMETRY cannot wait, though, and this is where it used to. The
        # story prints a whole turn (a boot: intro, banner, room, prompt)
        # without ever returning to the event loop, so an idle repaint applies
        # the picture band and the status bar's row only AFTER all that text
        # has been laid out at the old size. The reading area then shrank by a
        # dozen rows under text already printed, which scrolled away unread
        # with no [MORE] to stop it: the blank line the library puts under the
        # bar was the first thing to go (Stefan's screenshot, 2026-08-20).
        # Furniture that changes the reading area is therefore applied AT
        # ONCE, and only when it actually changes, so the pager always knows
        # how tall the page is while the story is still printing it.
        model = self.vm.screen
        if (model.rows > 0) != self._grid_shown:
            self._redraw_grid()          # packs or unpacks the bar, relayouts
        if model.image != self._band_state:
            self._band_state = model.image
            self._repaint_image()        # sizes the band, relayouts
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
            # No picture: the canvas UNPACKS entirely. A packed canvas asked
            # for height 0 still renders Tk's one-pixel minimum, a hairline
            # across the top of every pictureless game (Stefan's screenshot).
            self._image_canvas.configure(height=0)
            self._image_canvas.pack_forget()
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
        # The band is exactly as tall as the picture. Rounding it leaves spare
        # pixels that read as a blank row wherever they are put: under the
        # picture they double the library's blank line, above it they open a
        # gap that was never there, under the text they look like a spare line
        # (Stefan caught all three, 2026-08-20). The window gives them up
        # instead, in _relayout.
        # Returning from bandless to banded: back into the stack, topmost,
        # above the status grid when one is up.
        if not self._image_canvas.winfo_manager():
            before = self.canvas if self._grid_shown else self._lower_frame
            self._image_canvas.pack(fill="x", side="top",
                                    padx=self._margin, pady=(self._margin, 0),
                                    before=before)
        # The picture is centered in the band (at the ordinary width it fills
        # it edge to edge, so nothing moves); the band wears the game
        # background so any letterbox margin is the game's colour.
        self._image_canvas.configure(
            height=band_h,
            background=self._colour(self.vm.screen.bg, "black"),
        )
        if photo is not None:
            # Centered within the grid width (edge to edge at that width),
            # left-aligned with the bar and the text, and anchored to the
            # BOTTOM of the band: the picture sits flush against the status
            # bar and the text below it, and the few spare pixels that round
            # the band to whole rows stay at the top, against the window's
            # edge, where nothing mistakes them for a blank line.
            self._image_canvas.create_image(target_w // 2, 0, image=photo,
                                            anchor="n")
        self._band_h = band_h
        # The text below re-fits to whole lines under the band, and the window
        # takes up the slack so nothing is left over.
        self._relayout(snap=True)
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
                self._relayout(snap=True)
            return
        if not self._grid_shown:
            # Left/right frame, same as the picture and text; no vertical inset
            # (the bar sits flush under the picture and above the text).
            self.canvas.pack(fill="x", before=self._lower_frame, padx=m)
            self._grid_shown = True
            self._relayout(snap=True)
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
                    # EVERY GLYPH IS PINNED TO ITS CELL (Stefan's status
                    # bar, 2026-08-21, found by measuring): a run drawn as
                    # one text item advances by the font's TRUE fractional
                    # widths, while the grid reckons in the integer
                    # cell_w, and the difference compounds: 55px over 70
                    # columns at mono 13, the right block landing five
                    # cells left of where the model has it. A terminal
                    # has hard cells; this canvas must too.
                    font = self._styled_font(style)
                    for i, ch in enumerate(chars):
                        if ch != " ":
                            self.canvas.create_text(
                                (start + i) * self.cell_w, y, text=ch,
                                anchor="nw", fill=fg_c, font=font,
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
                if tag.startswith(("look-", "input-", "more-")):
                    self.text.tag_delete(tag)
        self.text.delete("1.0", "end")
        self.text.mark_set("input_start", "end-1c")
        self._start_page()  # a wiped screen starts a fresh page

    # -- output --------------------------------------------------------------

    def _styled_font(self, style: int):
        """The MACHINE voice: the mono face in the style's cut. The grid,
        the input line, the [MORE] marker, and fixed-pitch text all speak
        in it; in Retro it is the same face as the prose, by ruling."""
        if style & BOLD and style & ITALIC:
            return self.font_bold_italic
        if style & BOLD:
            return self.font_bold
        if style & ITALIC:
            return self.font_italic
        return self.font

    def _prose_font(self, style: int):
        """The STORY's voice: the look's prose face in the style's cut."""
        if style & BOLD and style & ITALIC:
            return self.font_prose_bold_italic
        if style & BOLD:
            return self.font_prose_bold
        if style & ITALIC:
            return self.font_prose_italic
        return self.font_prose

    def _fixed_now(self, style: int) -> bool:
        """Must this text be fixed-pitch? Two doors, both the Standard's:
        the FIXED text style (set_text_style bit 8), and Flags 2 bit 1,
        which a game may set and clear at run time to force the whole
        lower window fixed (S 8.1); it is read per print, as asked."""
        if style & FIXED:
            return True
        try:
            return bool(self.vm.mem.word(0x10) & 2)
        except Exception:
            return False

    def _look_tag(self) -> str:
        """A Text tag for the model's CURRENT look (style + colours),
        created on first use. Roman-default text in the prose face uses no
        tag at all: the widget's own font IS the prose face."""
        m = self.vm.screen
        style, fg, bg = m.style, m.fg, m.bg
        fixed = self._fixed_now(style)
        if style == 0 and fg == 1 and bg == 1 and not fixed:
            return ""
        name = f"look-{style}-{fg}-{bg}" + ("-f" if fixed else "")
        if name not in self._tags_made:
            self._configure_look(name, style, fg, bg, fixed)
            self._tags_made.add(name)
        return name

    def _configure_look(self, name: str, style: int, fg, bg,
                        fixed: bool = True) -> None:
        fg_c = self._colour(fg, "black")
        bg_c = self._colour(bg, self._window_bg)
        if style & REVERSE:
            fg_c, bg_c = bg_c, fg_c
        self.text.tag_configure(
            name, foreground=fg_c, background=bg_c,
            font=(self._styled_font(style) if fixed
                  else self._prose_font(style)),
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
        if self._closed:
            return    # the window died during a [MORE] pause mid-print:
                      # there is no widget left to keep books on
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

    def _start_page(self) -> None:
        """A new page begins here: the reader has just acted (a command, a
        keypress, a [MORE]) or the screen was wiped. Everything after this
        mark is unread: the pager measures from it, and the re-base below
        must never discard anything past it."""
        try:
            self.text.mark_set("page_start", "end-1c")
            self.text.mark_gravity("page_start", "left")
        except tk.TclError:
            pass

    def _rebase_page(self) -> None:
        """The reading area just shrank under text nobody has read yet.

        docs/08 section 3, the windowed profile: the first picture re-bases
        the screen, and THE RE-BASE NEVER EATS A LINE. Every line on the page
        is unread, so if the page no longer fits, it is shown from its top,
        a window-full at a time behind honest [MORE]s, until the newest lines
        stand bottom-anchored above the prompt. Scrollback does not
        substitute for that: the lines have to pass before the player's eyes.

        The same rule serves the status bar claiming its row and the player
        shrinking the window mid-turn: any shrink over unread text."""
        if self._closed or self._rebasing or self._reading_line:
            return
        page = self._page_height()
        if page < 2:
            return
        self._rebasing = True
        try:
            while not self._closed:
                self.text.update_idletasks()
                unread = self._display_lines("page_start", "end-1c")
                if unread <= page:
                    break          # what is left fits: show it and carry on
                stop = self.text.index(
                    "page_start + %d display lines display lineend" % page)
                if self.text.compare(stop, ">=", "end-1c"):
                    break
                self.text.see("page_start")
                self._pause_at(stop)
                self.text.mark_set("page_start", stop)
        finally:
            self._rebasing = False
        # The window height last asked for by the fit-to-contents snap; it is
        # compared against, never subtracted from (see _relayout).
        self._snapped_to = 0
        # The width this app ASKED for. The snap and any other height-only
        # adjustment must never read winfo_width() for it: geometry is
        # asynchronous, so mid-boot the widget still reports the previous
        # width, and re-asserting it flips the window between two widths,
        # re-wrapping every line while the pager is counting them (caught by
        # the GUI test as text scrolling off before the first pause).
        self._want_width = 0
        # True while a resize event is being handled. The snap below must not
        # run then: a resize rescales the picture, which would ask to fit the
        # window, which is another resize event (it ran away at 154% CPU on
        # Stefan's machine and could not be quit, 2026-08-20).
        self._in_resize = False
        self._tail_into_view()

    def _display_lines(self, start: str, end: str) -> int:
        try:
            n = self.text.count(start, end, "displaylines")
        except tk.TclError:
            return 0
        if isinstance(n, tuple):
            n = n[0] if n else 0
        return int(n or 0)

    def _settle_view(self) -> None:
        """About to hand the screen to the player: make any pending resize
        real and put the tail back in view.

        The story prints a whole turn without returning to the event loop, so
        a resize asked for mid-turn (the picture band claiming rows, the
        status bar appearing) is still pending here, and Tk keeps the TOP line
        when a Text widget shrinks. Left alone, the player is offered a prompt
        that is below the bottom edge of the window, with no sign that
        anything is there (Stefan's screenshot, 2026-08-20). Idle tasks only:
        no input is processed, so nothing can re-enter."""
        if self._closed:
            return
        try:
            self.text.update_idletasks()
            self.text.see("end")
        except tk.TclError:
            pass

    def _tail_into_view(self) -> None:
        if not self._closed:
            try:
                self.text.see("end")
            except tk.TclError:
                pass  # the window went away between the request and the idle

    def _reading_lines(self) -> int:
        """How many display lines the reading area REALLY has at this moment.

        Measured from the pixels the widget HAS, never from the height it
        asked for. The two part company constantly: at boot the widget is
        given the settings height and keeps it only until the picture band
        claims its rows, and the player is free to change the text size, the
        screen height, the window, or fullscreen at any time. Nothing here is
        ever stored, so every one of those settles itself."""
        rows = self._text_rows
        if rows >= 2:
            return rows
        if self.line_h <= 0:
            return 0
        try:
            rows = self.text.winfo_height() // self.line_h
        except tk.TclError:
            return 0
        if rows >= 2:
            return rows
        # Not laid out yet (the window exists before the story starts): what
        # it asked for is the best guess available.
        try:
            return int(self.text.cget("height"))
        except (tk.TclError, ValueError):
            return 0

    def _page_height(self) -> int:
        """Display lines to print before pausing: the reading area, whole.

        One row is held back, the way the console front end does it: the
        marker is appended to the last line printed, so if that line is
        already near the right margin the marker wraps, and without a row in
        hand the wrap would push a line off the top unread."""
        rows = self._reading_lines()
        return rows - 1 if rows >= 3 else 0

    def _insert(self, s: str, tag: str) -> None:
        if self._closed:
            return
        if tag:
            self.text.insert("end-1c", s, (tag,))
        else:
            self.text.insert("end-1c", s)

    def _insert_paged(self, s: str, tag: str) -> None:
        # MEASURED, NOT COMPUTED (the 2.0 architecture): the text goes in and
        # the WIDGET is asked how many display lines the unread page now
        # holds. When it overflows, the cut is the index Tk names for the
        # page's last display line, the tail is lifted back out, the [MORE]
        # waits, and the tail goes in again as the next page. The old pager
        # modelled Tk's word-wrap arithmetically from the fixed cell width,
        # which was exact for one font it could never leave; measurement is
        # exact for any face, which is what the proportional looks need.
        if (self._page_height() < 2 or self._reading_line
                or self._reading_key or self._closed):
            self._insert(s, tag)
            self._start_page()
            return
        rest = s
        while rest and not self._closed:
            self._insert(rest, tag)
            rest = ""
            self.text.update_idletasks()
            page = self._page_height()
            if page < 2:
                return
            used = self._display_lines("page_start", "end-1c")
            if used <= page:
                return
            cut = self.text.index("page_start + %d display lines" % page)
            if self.text.compare(cut, ">=", "end-1c"):
                return
            rest = self.text.get(cut, "end-1c")
            self.text.delete(cut, "end-1c")
            self._page_pause()

    def _page_pause(self) -> None:
        """Show [MORE] after the last line printed and wait for any key."""
        self._pause_at(self.text.index("end-1c"))
        self._start_page()

    def _log_geom(self, what: str) -> None:
        if not os.environ.get("ACTAEA_GEOM"):
            return
        try:
            with open(os.path.expanduser("~/actaea-geom.log"), "a") as fh:
                fh.write(
                    "%s: rows=%d page=%d pager_lines=%d text_px=%d cell_h=%d "
                    "band=%d bar=%s window=%d\n"
                    % (what, self._reading_lines(), self._page_height(),
                       self._display_lines("page_start", "end-1c"),
                       self.text.winfo_height(),
                       self.cell_h, getattr(self, "_band_h", 0),
                       self._grid_shown, self.root.winfo_height()))
        except OSError:
            pass

    def _log_gap(self, where: str) -> None:
        """At a pause: exactly how much room is left below the marker, in
        pixels and in rows. Settles by measurement what counting rows in a
        screenshot cannot."""
        if not os.environ.get("ACTAEA_GEOM"):
            return
        try:
            box = self.text.bbox(where)
            height = self.text.winfo_height()
            with open(os.path.expanduser("~/actaea-geom.log"), "a") as fh:
                if box is None:
                    fh.write("  gap: the marker's line is not on screen\n")
                else:
                    bottom = box[1] + box[3]
                    fh.write(
                        "  gap: marker_line_bottom=%d text_height=%d "
                        "free_px=%d free_rows=%.2f cell_h=%d\n"
                        % (bottom, height, height - bottom,
                           (height - bottom) / self.cell_h, self.cell_h))
        except (tk.TclError, ZeroDivisionError):
            pass

    def _pause_at(self, where: str) -> None:
        """[MORE] at `where`, and any key goes on.

        `where` is the end of the last line the reader has been shown, which
        for ordinary paging is the end of the text and for a re-base is the
        bottom of the window-full being offered. Inserting it there rather
        than painting over the last line is Stefan's ruling: the marker
        covers nothing, and it is taken out again afterwards, so it never
        becomes part of the transcript."""
        if self._closed:
            return
        self._log_geom("[MORE]")
        self._log_gap(where)
        self.text.mark_set("more_mark", where)
        self.text.mark_gravity("more_mark", "left")
        tag = self._more_tag()
        if tag:
            self.text.insert(where, "[MORE]", (tag,))
        else:
            self.text.insert(where, "[MORE]")
        end_of_marker = self.text.index("more_mark + 6c")
        self.text.see(end_of_marker)
        self._reading_key = True
        self._key.set("")
        self.root.wait_variable(self._key)
        self._reading_key = False
        try:
            self.text.delete("more_mark", "more_mark + 6c")
        except tk.TclError:
            pass

    def _input_look_tag(self) -> str:
        """The player's typing, in the game's input colours and the PROSE
        face: Stefan's ruling, the page speaks with one voice and the
        status bar is the only place the machine keeps its own. The tag
        still exists for the colours."""
        m = self.vm.screen
        name = f"input-{m.style}-{m.fg}-{m.bg}"
        if name not in self._tags_made:
            self._configure_look(name, m.style, m.fg, m.bg, fixed=False)
            self._tags_made.add(name)
        return name

    def _more_tag(self) -> str:
        """The marker wears the CURRENT look, reversed: on a game-coloured
        screen it is the game's own colours the other way round, the way the
        curses front end draws its [MORE] in A_REVERSE."""
        m = self.vm.screen
        name = f"more-{m.style}-{m.fg}-{m.bg}"
        if name not in self._tags_made:
            self._configure_look(name, m.style ^ REVERSE, m.fg, m.bg,
                                 fixed=False)
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
        if self._closed or self._switch_to:
            raise EOFError
        self._max_len = max_len
        self._terminators = terminators
        self._terminator = 13
        self._timed_out = False
        # The input wears the CURRENT look: Cosmos sets the input colour
        # (zcolor.input) right before every read, so the tag resolved here
        # is the game's choice; the caret matches it.
        self._input_tag = self._input_look_tag()
        self.text.configure(
            insertbackground=self._colour(self.vm.screen.fg, "black")
        )
        self._reading_line = True
        self._log_geom("prompt")
        self._line_ready.set(False)
        if preload:
            self._absorb_preload(preload)
        self.text.mark_set("insert", "end-1c")
        self._start_page()
        self._settle_view()
        self._start_timer(timeout, on_timeout)
        self.root.wait_variable(self._line_ready)
        self._stop_timer()
        self._reading_line = False
        if self._closed or self._switch_to:
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
        self._start_page()
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
        if self._closed or self._switch_to:
            raise EOFError
        self._reading_key = True
        self._timed_out = False
        self._key_code = 0
        self._key.set("")
        self._start_page()
        self._settle_view()
        self._start_timer(timeout, on_timeout)
        self.root.wait_variable(self._key)
        self._stop_timer()
        self._reading_key = False
        if self._closed or self._switch_to:
            raise EOFError
        # The reader just pressed a key of their own: a fresh page starts.
        self._start_page()
        return 0 if self._timed_out else self._key_code

    # -- lifecycle --------------------------------------------------------------------

    def _on_close(self):
        # Where the window stood, so it opens there next time (Stefan: having
        # to move it across the screen at every launch is as annoying for his
        # adopters as it is for him).
        if getattr(self, "_persist_job", None) is not None:
            try:
                self.root.after_cancel(self._persist_job)
            except tk.TclError:
                pass
            self._persist_job = None
        try:
            self._persist_now()
        except tk.TclError:
            pass
        self._closed = True
        # Unblock whichever wait is spinning so the run loop can unwind.
        self._line_ready.set(True)
        self._key.set("\n")
        self.root.destroy()

    def run(self) -> None:
        """Start the machine once the window is up, then hand the thread to
        tkinter. The VM blocks only inside wait_variable, so the window
        stays alive the whole way.

        "Up" means MAPPED: the boot used to race the window manager, and a
        story starting before the map was stamped with the default eighty
        columns while the window really held ninety-five, so the first
        status bar was painted for a screen that did not exist (Stefan's
        H2 screenshot: the score block adrift of the prose's right edge).
        Waiting for visibility, then measuring once, makes the first
        screen's geometry the real one."""
        try:
            self.root.wait_visibility(self.root)
        except tk.TclError:
            pass
        self._on_root_resize()
        self.root.after(20, self._run_vm)
        self.root.mainloop()

    def _run_vm(self):
        try:
            self.vm.run()
            if not self._closed and not self._switch_to:
                self.append_story("\n[The story has ended.]\n")
        except EOFError:
            pass  # the window closed (or is switching) mid-read
        except ActaeaError as e:
            if not self._closed:
                self.append_story(f"\n[actaea: {e}]\n")
        if self._switch_to and not self._closed:
            path, self._switch_to = self._switch_to, None
            self._load_story(path)

    # -- File > Open: another story in the same window -----------------------

    def _open_dialog(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title="Open a story",
            filetypes=[("Z-machine stories", "*.z5 *.z8 *.zblorb"),
                       ("All files", "*")],
        )
        if path:
            self._open_path(path)

    def _open_documents(self, *paths) -> None:
        """A story double-clicked in Finder or dropped on the Dock icon,
        arriving as an Apple Event (::tk::mac::OpenDocument). One window,
        one story: the first real file wins."""
        for path in paths:
            if path and os.path.isfile(path):
                self._open_path(path)
                return

    def _open_path(self, path: str) -> None:
        if self.vm.halted or self._closed:
            # Nothing is waiting to unwind: boot directly.
            self._load_story(path)
            return
        # Ask the running machine to stand down: the flag turns the next
        # wait (or the one currently blocking) into an EOFError, the run
        # loop unwinds, and _run_vm boots the new story.
        self._switch_to = path
        self._line_ready.set(True)
        self._key.set("\n")

    def _load_story(self, path: str) -> None:
        """Boot `path` in this window, replacing the current machine: the
        screen wipes, the caches empty, the title and the remembered story
        follow, and the new story runs on the same widgets."""
        from ..loader import load_file
        from ..__main__ import _resolve_images
        try:
            story = load_file(path)
        except (OSError, ActaeaError) as e:
            from tkinter import messagebox
            messagebox.showerror("Actaea", str(e), parent=self.root)
            return
        images_dir, images_zip = _resolve_images(path, None)
        self._images_dir = images_dir
        self._images_zip = images_zip
        self._photo_cache.clear()
        self._scaled_cache.clear()
        self._drawn_image = False
        self._band_state = False
        self._story_path = os.path.abspath(path)
        self.root.title(f"{os.path.basename(path)} - Actaea")
        self.vm = VM(story, GuiIO(self))
        self.vm.screen.on_change = self._grid_changed
        self._reading_line = self._reading_key = False
        self._timed_out = False
        # A fresh machine means a fresh screen: the same wipe an in-game
        # erase performs, which also re-bases the paper colour.
        self.clear_story()
        self._grid_changed()
        self._persist()
        self.root.after(20, self._run_vm)


def play(story, title: str, images_dir=None, images_zip=None, seed=None,
         root=None, story_path=None) -> None:
    ActaeaApp(story, title, images_dir, images_zip, seed, root=root,
              story_path=story_path).run()
