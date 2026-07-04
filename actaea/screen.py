# screen.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The window model and the cell grid (M8; Standard 1.1 section 8).

Version 5 has two windows and no automatic status line: the game draws
whatever status display it wants into the upper window. The lower window
(window 0) is the scrolling, buffered text flow and passes through to the
front-end's text area. The upper window (window 1) is the honest thing this
module exists for: a true rows-by-columns buffer of CELLS, each holding a
character with its style and colours, positioned by set_cursor, sized by
split_window, never an approximation stitched out of strings.

This model is the single truth. Front-ends RENDER it (the tkinter Canvas, a
future arc_image surface) and are told when it changed through on_change;
they never hold screen state of their own. That decoupling is deliberate
and forward-looking: the arc_image milestones (B11/B12) extend this grid
and its renderers to place pictures into cell regions, with the text path
unchanged, exactly as docs/06 sections 6 and 14 lay out.

Semantics held here, from the Standard:
- split_window keeps the upper window's contents (v5 does not blank on
  split); a cursor left outside the new size homes to 1,1 (S 8.7.2.2).
- Selecting the upper window homes its cursor (S 8.7.2).
- The upper window never scrolls and never wraps: text past the last
  column of a row is clipped (a status line that overruns is a bug in the
  game, not a layout event).
- erase_window: 1 clears the grid, 0 clears the lower window (a front-end
  affair, through the sink's erase_lower), -1 unsplits AND clears
  everything, -2 clears everything but keeps the split (S 8.7.3.3).
- erase_line clears from the cursor to the end of the row, upper window
  only (the lower window's line editing belongs to input, not here)."""

from dataclasses import dataclass

DEFAULT_COLS = 80

# Style bits, as set_text_style speaks them (S 8.7.1).
ROMAN, REVERSE, BOLD, ITALIC, FIXED = 0, 1, 2, 4, 8


@dataclass
class Cell:
    """One character cell: what it shows and how. Colours are the standard
    colour numbers (M9 renders them; the model records them from day one so
    the renderer never needs a second data path)."""

    char: str = " "
    style: int = ROMAN
    fg: int = 1   # 1 = the default colour
    bg: int = 1


def _blank_row(cols: int) -> list:
    return [Cell() for _ in range(cols)]


class ScreenModel:
    """The two-window screen: grid truth for the upper window, pass-through
    to the sink (an io.IOSystem) for the lower. `on_change` fires after any
    visible change to the grid or the split, so a renderer can repaint."""

    def __init__(self, sink, cols: int = DEFAULT_COLS, on_change=None):
        self.sink = sink
        self.cols = cols
        self.on_change = on_change
        self.rows = 0                 # the split: upper-window height
        self.grid: list = []          # rows x cols of Cell
        self.window = 0
        self.cursor = (1, 1)          # upper-window cursor, 1-based
        self.style = ROMAN            # current output style (both windows)
        self.fg = 1
        self.bg = 1

    # -- notification ----------------------------------------------------------

    def _changed(self) -> None:
        if self.on_change is not None:
            self.on_change()

    # -- the split and the windows ----------------------------------------------

    def split(self, lines: int) -> None:
        lines = max(0, lines)
        if lines > len(self.grid):
            self.grid.extend(_blank_row(self.cols) for _ in range(lines - len(self.grid)))
        elif lines < len(self.grid):
            del self.grid[lines:]
        self.rows = lines
        r, c = self.cursor
        if r > lines or c > self.cols:
            self.cursor = (1, 1)
        self._changed()

    def select(self, window: int) -> None:
        self.window = window
        if window == 1:
            self.cursor = (1, 1)  # S 8.7.2: selecting the upper window homes it

    def set_cursor(self, row: int, col: int) -> None:
        # Meaningful only over the grid; a lower-window set_cursor is a
        # no-op on a buffered window (S 8.7.2.3 note).
        if self.window == 1:
            self.cursor = (max(1, row), max(1, col))

    def get_cursor(self):
        return self.cursor if self.window == 1 else (self.rows + 1, 1)

    # -- writing -----------------------------------------------------------------

    def write(self, text: str) -> None:
        if self.window == 0:
            self.sink.print_text(text)
            return
        r, c = self.cursor
        changed = False
        for ch in text:
            if ch == "\n":
                r, c = r + 1, 1
                continue
            if 1 <= r <= self.rows and 1 <= c <= self.cols:
                self.grid[r - 1][c - 1] = Cell(ch, self.style, self.fg, self.bg)
                changed = True
            c += 1  # past the last column: clipped, the cursor still tracks
        self.cursor = (r, c)
        if changed:
            self._changed()

    # -- erasing ------------------------------------------------------------------

    def erase_window(self, n: int) -> None:
        if n == 1:
            for row in self.grid:
                for i in range(self.cols):
                    row[i] = Cell()
            self._changed()
        elif n == 0:
            self.sink.erase_lower()
        elif n == -1:
            self.split(0)
            self.window = 0
            self.sink.erase_lower()
            self._changed()
        elif n == -2:
            self.erase_window(1)
            self.sink.erase_lower()

    def erase_line(self) -> None:
        if self.window != 1:
            return
        r, c = self.cursor
        if 1 <= r <= self.rows:
            for i in range(c - 1, self.cols):
                self.grid[r - 1][i] = Cell()
            self._changed()

    # -- rendering helpers ------------------------------------------------------------

    def row_text(self, row: int) -> str:
        """Row contents as plain text (1-based), for tests and simple sinks."""
        return "".join(cell.char for cell in self.grid[row - 1])
