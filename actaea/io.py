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

    def set_style(self, style: int) -> None:
        """A text-style hint (set_text_style's argument). A style-less
        front-end (the console harness) ignores it; the GUI renders it. A
        hint rather than a required capability, so it defaults to nothing."""

    def set_colour(self, fg: int, bg: int) -> None:
        """A colour hint (set_colour's standard colour numbers); as with
        styles, colourless front-ends ignore it."""

    def set_true_colour(self, fg: int, bg: int) -> None:
        """A Standard 1.1 true-colour hint (15-bit RGB words; -1 keeps, -2
        default). Ignored wherever colour is not rendered."""


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


class CaptureIO(IOSystem):
    """Collects output for assertions; used by the tests and by transcript
    comparison in the conformance harness. Input can be scripted."""

    def __init__(self, script=()):
        self.output: list = []
        self.script = list(script)

    def print_text(self, text: str) -> None:
        self.output.append(text)

    def read_line(self, max_len: int) -> str:
        line = self.script.pop(0)[:max_len]
        self.output.append(line + "\n")  # the transcript shows the command
        return line

    def read_char(self) -> int:
        # A scripted keypress: one entry per key, as a 1-character string
        # ("\n" for Enter). ASCII covers the harness's needs.
        ch = self.script.pop(0)
        return 13 if ch == "\n" else ord(ch[0])

    @property
    def text(self) -> str:
        return "".join(self.output)
