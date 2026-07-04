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

import tkinter as tk
from tkinter import font as tkfont

from ..errors import ActaeaError
from ..io import IOSystem
from ..screen import BOLD, ITALIC, REVERSE, TRUE_COLOURS, true_colour_hex
from ..vm import VM


class GuiIO(IOSystem):
    """The io boundary against the shell. The widget shows the player's
    typing live, so read_line never echoes (the io.py contract)."""

    def __init__(self, app: "ActaeaApp"):
        self.app = app

    def print_text(self, text: str) -> None:
        self.app.append_story(text)

    def read_line(self, max_len: int) -> str:
        return self.app.wait_for_line(max_len)

    def read_char(self) -> int:
        ch = self.app.wait_for_key()
        return 13 if ch in ("\r", "\n") else ord(ch)

    def erase_lower(self) -> None:
        self.app.clear_story()


class ActaeaApp:
    """The window: a Text widget with a scrollbar, inline input, and the
    run loop driving the VM through GuiIO."""

    def __init__(self, story, title: str):
        self.root = tk.Tk()
        self.root.title(f"{title} - Actaea")

        self.font = tkfont.nametofont("TkFixedFont").copy()
        self.font.configure(size=13)
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

        # The upper window: a Canvas over the text area, sized in exact
        # character cells, shown only while the story keeps a split open.
        self.cell_w = self.font.measure("0")
        self.cell_h = self.font.metrics("linespace")

        # The window opens WIDE ENOUGH for the story's screen: the model is
        # 80 columns, so the status bar and centred quote boxes must fit
        # without the player reaching for the window corner. Exactly 80
        # cells plus a small margin, about 30 lines tall.
        width = 80 * self.cell_w + 20
        height = 30 * self.cell_h
        self.root.geometry(f"{width}x{height}")
        self.canvas = tk.Canvas(
            self.root, height=0, borderwidth=0, highlightthickness=0,
            background="white",
        )
        self._grid_shown = False
        self._redraw_queued = False

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        self._lower_frame = frame
        self.text = tk.Text(
            frame, wrap="word", font=self.font, undo=False,
            padx=8, pady=6, borderwidth=0, highlightthickness=0,
            background="white", foreground="black", insertbackground="black",
        )
        # No scrollbar: interpreters never had one, the native widget is an
        # unstyleable white strip on a game-painted dark screen (Stefan's
        # eye, 2026-07-05), and the wheel, trackpad, and the unread-text
        # return cover every way a player actually moves through the text.
        self.text.pack(fill="both", expand=True)

        # The input mark: everything before it is story text and immutable.
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_gravity("input_start", "left")
        # The unread mark: where the player last stopped reading (set at
        # each completed input). When a burst of story text runs past a
        # screenful, the view returns HERE at the next input instead of
        # racing to the bottom, so long passages read from the top.
        self.text.mark_set("unread", "1.0")
        self.text.mark_gravity("unread", "left")

        self._line_ready = tk.BooleanVar(value=False)
        self._key: tk.StringVar = tk.StringVar(value="")
        self._reading_line = False
        self._reading_key = False
        self._closed = False
        self._max_len = 0
        self._input_tag = ""

        self.text.bind("<Key>", self._on_key)
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        # Keep the caret out of the story text: any click refocuses the end.
        self.text.bind("<Button-1>", lambda e: self.root.after(1, self._to_end))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.text.focus_set()

        self.vm = VM(story, GuiIO(self))
        self.vm.screen.on_change = self._grid_changed

    # -- the upper window ---------------------------------------------------------

    def _grid_changed(self) -> None:
        # Coalesce bursts of cell writes into one repaint per idle cycle.
        if not self._redraw_queued:
            self._redraw_queued = True
            self.root.after_idle(self._redraw_grid)

    def _colour(self, value, default: str) -> str:
        """A cell/model colour as a tk colour: 1 (or anything unmapped) is
        the front-end default, 2..12 the standard set via the Standard's
        recommended true colours, a #rrggbb string passes through."""
        if isinstance(value, str):
            return value
        word = TRUE_COLOURS.get(value)
        return true_colour_hex(word) if word is not None else default

    def _redraw_grid(self) -> None:
        self._redraw_queued = False
        model = self.vm.screen
        if model.rows == 0:
            if self._grid_shown:
                self.canvas.pack_forget()
                self._grid_shown = False
            return
        if not self._grid_shown:
            self.canvas.pack(fill="x", before=self._lower_frame)
            self._grid_shown = True
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
            self._tags_made.clear()  # cached looks resolved the old paper
            for tag in self.text.tag_names():
                if tag.startswith("look-"):
                    self.text.tag_delete(tag)
        self.text.delete("1.0", "end")
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_set("unread", "1.0")  # a wiped screen is all unread

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
            fg_c = self._colour(fg, "black")
            bg_c = self._colour(bg, self._window_bg)
            if style & REVERSE:
                fg_c, bg_c = bg_c, fg_c
            self.text.tag_configure(
                name, foreground=fg_c, background=bg_c,
                font=self._styled_font(style),
            )
            self._tags_made.add(name)
        return name

    def append_story(self, s: str) -> None:
        tag = self._look_tag()
        self.text.mark_set("insert", "end-1c")
        if tag:
            self.text.insert("end-1c", s, (tag,))
        else:
            self.text.insert("end-1c", s)
        self.text.mark_set("input_start", "end-1c")
        self.text.see("end")

    # -- input: lines ----------------------------------------------------------

    def _show_unread(self) -> None:
        """At an input point: if the text since the player's last input has
        scrolled past a screenful, bring its BEGINNING into view instead of
        the tail, so a long passage is read from the top down."""
        if self.text.bbox("unread") is None:
            self.text.yview("unread")

    def _mark_read(self) -> None:
        self.text.mark_set("unread", "end-1c")

    def wait_for_line(self, max_len: int) -> str:
        if self._closed:
            raise EOFError
        self._max_len = max_len
        # The input wears the CURRENT look: Cosmos sets the input colour
        # (zcolor.input) right before every read, so the tag resolved here
        # is the game's choice; the caret matches it.
        self._input_tag = self._look_tag()
        self.text.configure(
            insertbackground=self._colour(self.vm.screen.fg, "black")
        )
        self._reading_line = True
        self._line_ready.set(False)
        self.text.mark_set("insert", "end-1c")
        self._show_unread()
        self.root.wait_variable(self._line_ready)
        self._reading_line = False
        if self._closed:
            raise EOFError
        self._dress_input()
        line = self.text.get("input_start", "end-1c")
        # The typed line becomes story text, newline included.
        self.append_story("\n")
        self._mark_read()
        return line

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
            self._key.set("\n")
            return "break"
        if self._reading_line:
            self._line_ready.set(True)
        return "break"

    def _on_backspace(self, event):
        if self._reading_key:
            self._key.set("\x08")  # ZSCII 8, delete
            return "break"
        # Never eat into the story text before the input mark.
        if not self._reading_line:
            return "break"
        if self.text.compare("insert", "<=", "input_start"):
            return "break"
        return None

    def _on_key(self, event):
        if self._reading_key and event.char:
            self._key.set(event.char)
            return "break"
        if not self._reading_line:
            return "break"  # story is thinking: swallow stray typing
        if self.text.compare("insert", "<", "input_start"):
            self.text.mark_set("insert", "end-1c")
        if event.char:
            # Typing pulls the view back to the prompt (the player may have
            # scrolled up to read; their keystrokes belong at the bottom).
            self.text.see("end")
        if event.char and len(self.text.get("input_start", "end-1c")) >= self._max_len:
            return "break"  # the buffer is full: the machine set the limit
        return None

    def _to_end(self):
        if self._reading_line:
            self.text.mark_set("insert", "end-1c")

    # -- input: single keys --------------------------------------------------------

    def wait_for_key(self) -> str:
        if self._closed:
            raise EOFError
        self._reading_key = True
        self._key.set("")
        self._show_unread()
        self.root.wait_variable(self._key)
        self._reading_key = False
        if self._closed:
            raise EOFError
        self._mark_read()
        return self._key.get()

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


def play(story, title: str) -> None:
    ActaeaApp(story, title).run()
