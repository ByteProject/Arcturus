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

# The standard colour numbers (S 8.3.1): 1 is "the default", the numbers
# from 2 map to real colours. 0 means "keep the current one" in set_colour.
DEFAULT_COLOUR = 1

# The Standard's recommended true colours for the standard set (S 8.3.7),
# as 15-bit words (5 bits per component, red in the low bits).
TRUE_COLOURS = {
    2: 0x0000,  # black
    3: 0x001D,  # red
    4: 0x0340,  # green
    5: 0x03BD,  # yellow
    6: 0x59A0,  # blue
    7: 0x7C1F,  # magenta
    8: 0x77A0,  # cyan
    9: 0x7FFF,  # white
    10: 0x5AD6,  # light grey
    11: 0x4631,  # medium grey
    12: 0x2D6B,  # dark grey
}


def true_colour_hex(word: int) -> str:
    """A 15-bit true-colour word as tk's #rrggbb (S 8.3.7: red in bits 0-4,
    green 5-9, blue 10-14; components scale 0..31 up to 0..255)."""
    def scale(c5: int) -> int:
        return (c5 * 255 + 15) // 31
    r = scale(word & 0x1F)
    g = scale((word >> 5) & 0x1F)
    b = scale((word >> 10) & 0x1F)
    return f"#{r:02x}{g:02x}{b:02x}"


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

    # -- the current look (M9): one truth for BOTH windows -------------------------
    # fg/bg hold either a standard colour number (int) or a precomputed
    # #rrggbb string from set_true_colour; renderers resolve both.

    def set_style(self, style: int) -> None:
        """set_text_style semantics (S 8.7.1): 0 returns to roman, anything
        else adds to the styles in force."""
        if style == 0:
            self.style = ROMAN
        else:
            self.style |= style

    def set_colour(self, fg: int, bg: int) -> None:
        """The standard colour numbers: 0 keeps the current colour, 1 is
        the default, 2.. name real colours (S 8.3.1)."""
        if fg:
            self.fg = fg
        if bg:
            self.bg = bg

    def set_true_colour(self, fg: int, bg: int) -> None:
        """Standard 1.1 true colour: 15-bit RGB words, -1 keeps the current
        colour, -2 returns to the default (S 8.3.7)."""
        if fg >= 0:
            self.fg = true_colour_hex(fg)
        elif fg == -2:
            self.fg = DEFAULT_COLOUR
        if bg >= 0:
            self.bg = true_colour_hex(bg)
        elif bg == -2:
            self.bg = DEFAULT_COLOUR

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
