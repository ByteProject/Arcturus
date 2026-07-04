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
mark to the end is the player's line. The M8 cell grid will sit above this
lower window; nothing here assumes it does not exist."""

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


class ActaeaApp:
    """The window: a Text widget with a scrollbar, inline input, and the
    run loop driving the VM through GuiIO."""

    def __init__(self, story, title: str):
        self.root = tk.Tk()
        self.root.title(f"{title} - Actaea")
        self.root.geometry("780x560")

        self.font = tkfont.nametofont("TkFixedFont").copy()
        self.font.configure(size=13)

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
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
