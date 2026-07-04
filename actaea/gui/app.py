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
        self.root.geometry("780x560")

        self.font = tkfont.nametofont("TkFixedFont").copy()
        self.font.configure(size=13)

        # The upper window: a Canvas over the text area, sized in exact
        # character cells, shown only while the story keeps a split open.
        self.cell_w = self.font.measure("0")
        self.cell_h = self.font.metrics("linespace")
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
        )
        scroll = tk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        # The input mark: everything before it is story text and immutable.
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_gravity("input_start", "left")

        self._line_ready = tk.BooleanVar(value=False)
        self._key: tk.StringVar = tk.StringVar(value="")
        self._reading_line = False
        self._reading_key = False
        self._closed = False
        self._max_len = 0

        self.text.bind("<Key>", self._on_key)
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
                reverse = key[0] & 1
                if reverse:
                    self.canvas.create_rectangle(
                        x, y, x + (c - start) * self.cell_w, y + self.cell_h,
                        fill="black", width=0,
                    )
                if chars.strip() or reverse:
                    self.canvas.create_text(
                        x, y, text=chars, anchor="nw", font=self.font,
                        fill="white" if reverse else "black",
                    )

    def clear_story(self) -> None:
        self.text.delete("1.0", "end")
        self.text.mark_set("input_start", "end-1c")

    # -- output --------------------------------------------------------------

    def append_story(self, s: str) -> None:
        self.text.mark_set("insert", "end-1c")
        self.text.insert("end-1c", s)
        self.text.mark_set("input_start", "end-1c")
        self.text.see("end")

    # -- input: lines ----------------------------------------------------------

    def wait_for_line(self, max_len: int) -> str:
        if self._closed:
            raise EOFError
        self._max_len = max_len
        self._reading_line = True
        self._line_ready.set(False)
        self.text.mark_set("insert", "end-1c")
        self.text.see("end")
        self.root.wait_variable(self._line_ready)
        self._reading_line = False
        if self._closed:
            raise EOFError
        line = self.text.get("input_start", "end-1c")
        # The typed line becomes story text, newline included.
        self.append_story("\n")
        return line

    def _on_return(self, event):
        if self._reading_line:
            self._line_ready.set(True)
        return "break"

    def _on_backspace(self, event):
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
        self.root.wait_variable(self._key)
        self._reading_key = False
        if self._closed:
            raise EOFError
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
