# io.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The boundary between the VM core and the world (docs/06 section 4): the
single most important design choice in Actaea. The core calls ONLY what is
declared here; a front-end implements it. The console harness implements it
against stdin/stdout for the conformance gate, the tkinter front-end (M7+)
against widgets, and tests against a capture buffer. The core never knows
which it is talking to.

The interface grows milestone by milestone, and only ever with methods the
core actually calls: text output now (M3); line and character input when
read arrives; the screen-model calls (split, cursor, styles, colours) speak
to screen.py's cell model rather than this interface, because the cell
buffer is core-owned truth and front-ends RENDER it (they never hold state).
What belongs here is what crosses the boundary as an event: text flowing
out, keys flowing in, save/restore file channels."""

import os
import sys


class IOSystem:
    """The abstract boundary. Methods raise until a front-end provides them,
    so a core feature reaching for missing I/O fails loudly, not quietly."""

    def print_text(self, text: str) -> None:
        """Story text for the current window, already decoded to str.
        Buffering/word-wrap policy is the screen model's job (M7/M8); until
        then this is a straight pipe."""
        raise NotImplementedError("this front-end does not print")

    def read_line(self, max_len: int) -> str:
        """A line of player input (read/aread). Returns the typed text
        without its terminator. ECHO IS THE FRONT-END'S JOB: the player's
        line is part of the screen text (S 7.1.1.1), but only the front-end
        knows whether it is already visible (a widget shows the typing, a
        terminal echoes it, a pipe shows nothing), so each implementation
        echoes exactly when needed and the VM never does."""
        raise NotImplementedError("this front-end does not read lines")

    def read_char(self) -> int:
        """One keypress as a ZSCII code (read_char, M7)."""
        raise NotImplementedError("this front-end does not read keys")

    def erase_lower(self) -> None:
        """Clear the lower window (erase_window 0 / -1 / -2). A scrolling
        console keeps its transcript (nothing to clear that would not lose
        history); a windowed front-end wipes its text area."""

    # The save/restore file channels (M10): the VM builds and parses the
    # Quetzal bytes itself; all it needs from the front-end is WHERE. None
    # means the player changed their mind, which the VM reports as an
    # ordinary save/restore failure.

    def save_path(self, default: str):
        """A path to write a save to, or None if cancelled."""
        raise NotImplementedError("this front-end does not save")

    def restore_path(self, default: str):
        """A path to read a save from, or None if cancelled."""
        raise NotImplementedError("this front-end does not restore")


class ConsoleIO(IOSystem):
    """The plain console: what the headless harness (CZECH, Praxix, and
    `python3 -m actaea` before the GUI exists) runs against."""

    def __init__(self):
        # A terminal shows keystrokes as they are typed; a pipe shows
        # nothing, so scripted play (walkthrough files) needs the echo for
        # a readable transcript.
        self._echo = not sys.stdin.isatty()

    def print_text(self, text: str) -> None:
        sys.stdout.write(text)

    def read_line(self, max_len: int) -> str:
        sys.stdout.flush()
        line = input()[:max_len]
        if self._echo:
            sys.stdout.write(line + "\n")
        return line

    def read_char(self) -> int:
        sys.stdout.flush()
        ch = sys.stdin.read(1)
        if ch == "":
            raise EOFError
        return 13 if ch == "\n" else ord(ch)

    def _ask_filename(self, default: str):
        # The dfrotz manner: prompt with a default, take a line, an empty
        # line means the default. Scripted play (a walkthrough on stdin)
        # feeds the name the same way it feeds commands.
        sys.stdout.write(f"Please enter a filename [{default}]: ")
        sys.stdout.flush()
        try:
            line = input().strip()
        except EOFError:
            return None
        name = line or default
        if self._echo:
            sys.stdout.write(name + "\n")
        return name

    def save_path(self, default: str):
        return self._ask_filename(default)

    def restore_path(self, default: str):
        return self._ask_filename(default)


class CaptureIO(IOSystem):
    """Collects output for assertions; used by the tests and by transcript
    comparison in the conformance harness. Input can be scripted."""

    def __init__(self, script=(), save_dir=None):
        self.output: list = []
        self.script = list(script)
        # Where scripted saves land; the script supplies bare filenames the
        # way a player would, and they resolve into this directory (a test's
        # tmp_path). None = the current directory.
        self.save_dir = save_dir

    def print_text(self, text: str) -> None:
        self.output.append(text)

    def read_line(self, max_len: int) -> str:
        line = self.script.pop(0)[:max_len]
        self.output.append(line + "\n")  # the transcript shows the command
        return line

    def read_char(self) -> int:
        # A scripted keypress: one entry per key, as a 1-character string.
        # "\n" or an empty entry means Enter (walkthrough files answer
        # press-any-key moments with blank lines, the dfrotz convention).
        ch = self.script.pop(0)
        return 13 if ch in ("\n", "") else ord(ch[0])

    def _next_filename(self, default: str):
        name = self.script.pop(0).strip() or default
        self.output.append(name + "\n")  # the transcript shows the answer
        return os.path.join(self.save_dir, name) if self.save_dir else name

    def save_path(self, default: str):
        return self._next_filename(default)

    def restore_path(self, default: str):
        return self._next_filename(default)

    @property
    def text(self) -> str:
        return "".join(self.output)
