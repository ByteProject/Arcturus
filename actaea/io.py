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
        """A line of player input (read/aread, M7). Returns the typed text
        without its terminator."""
        raise NotImplementedError("this front-end does not read lines")

    def read_char(self) -> int:
        """One keypress as a ZSCII code (read_char, M7)."""
        raise NotImplementedError("this front-end does not read keys")


class ConsoleIO(IOSystem):
    """The plain console: what the headless harness (CZECH, Praxix, and
    `python3 -m actaea` before the GUI exists) runs against."""

    def print_text(self, text: str) -> None:
        sys.stdout.write(text)

    def read_line(self, max_len: int) -> str:
        return input()[:max_len]


class CaptureIO(IOSystem):
    """Collects output for assertions; used by the tests and by transcript
    comparison in the conformance harness. Input can be scripted."""

    def __init__(self, script=()):
        self.output: list = []
        self.script = list(script)

    def print_text(self, text: str) -> None:
        self.output.append(text)

    def read_line(self, max_len: int) -> str:
        return self.script.pop(0)[:max_len]

    @property
    def text(self) -> str:
        return "".join(self.output)
