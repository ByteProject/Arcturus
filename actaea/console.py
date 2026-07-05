# console.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The terminal front-end (M11): a real playing interpreter in a terminal,
in the manner of fizmo-ncursesw. The game-drawn status bar renders live from
the cell grid, colours and styles come through curses attributes, the lower
window word-wraps and pages with [MORE], input is edited inline with the
game's input colour, and timed input runs on the terminal's own clock.

This is the third front-end on the same headless core, and the proof of the
io boundary: the VM cannot tell this apart from the tkinter window or the
pipe harness. Nothing here is reachable from the core; __main__ imports it
only when --console asks (and the plain pipe mode, --headless, stays what
debuggers and build tools script against).

curses is the Python standard library's, so the everything-Python goal
holds: no binaries, no third-party packages. On platforms without curses
(Windows outside WSL), __main__ degrades to the headless pipe with a note."""

import curses
import locale

from .errors import ActaeaError
from .io import IOSystem
from .screen import BOLD, ITALIC, REVERSE
from .vm import VM

# Z-machine colour codes 2..9 are, in order, exactly curses colours 0..7.
_CURSES_COLOUR = {z: z - 2 for z in range(2, 10)}

# The standard set's RGB, for mapping a true colour to the nearest of the
# eight the terminal is sure to have.
_RGB = {
    0: (0, 0, 0), 1: (229, 34, 34), 2: (0, 172, 59), 3: (234, 222, 74),
    4: (0, 111, 197), 5: (188, 84, 253), 6: (35, 205, 229), 7: (255, 255, 255),
}

_KEY_ZSCII = {
    curses.KEY_UP: 129, curses.KEY_DOWN: 130,
    curses.KEY_LEFT: 131, curses.KEY_RIGHT: 132,
    **{getattr(curses, f"KEY_F{n}"): 132 + n for n in range(1, 13)},
}


def _nearest(hexcolour: str) -> int:
    r, g, b = (int(hexcolour[i:i + 2], 16) for i in (1, 3, 5))
    return min(
        _RGB,
        key=lambda c: (r - _RGB[c][0]) ** 2 + (g - _RGB[c][1]) ** 2
        + (b - _RGB[c][2]) ** 2,
    )


class CursesIO(IOSystem):
    """The io boundary against the terminal app below."""

    supports_timed = True  # the terminal has a clock: getch timeouts

    def __init__(self, app: "ConsoleApp"):
        self.app = app

    def print_text(self, text: str) -> None:
        self.app.write(text)

    def read_line(self, max_len, preload="", terminators=frozenset(),
                  timeout=0.0, on_timeout=None):
        return self.app.read_line(max_len, preload, terminators,
                                  timeout, on_timeout)

    def read_char(self, timeout=0.0, on_timeout=None) -> int:
        return self.app.read_char(timeout, on_timeout)

    def erase_lower(self) -> None:
        self.app.erase_lower()

    def save_path(self, default: str):
        return self.app.ask_filename("Save to", default)

    def restore_path(self, default: str):
        return self.app.ask_filename("Restore from", default)

    def transcript_path(self, default: str):
        return self.app.ask_filename("Transcript to", default)


class ConsoleApp:
    """The terminal: an upper region painted from the cell grid, a lower
    curses window that scrolls, wraps at word boundaries, and pages."""

    def __init__(self, story, stdscr):
        self.scr = stdscr
        curses.raw()
        try:
            curses.start_color()
            curses.use_default_colors()
        except curses.error:
            pass  # a monochrome terminal is a fine Z-machine screen
        self._pairs = {}
        self._next_pair = 1
        self.term_h, self.term_w = stdscr.getmaxyx()

        self.vm = VM(story, CursesIO(self))
        self.vm.screen.on_change = self._grid_changed
        self._grid_dirty = False
        self._split = 0
        self.lower = None
        self._make_lower(0)

        # The word-wrap buffer: the unfinished output line as (char, attr)
        # pairs, broken at spaces when it outgrows the width.
        self._pending: list = []
        # [MORE] paging: lines scrolled since the player last had a say.
        self._since_input = 0

    # -- geometry ---------------------------------------------------------------

    def _make_lower(self, split: int) -> None:
        self._split = split
        h = max(1, self.term_h - split)
        self.lower = curses.newwin(h, self.term_w, split, 0)
        self.lower.scrollok(True)
        self.lower.keypad(True)
        self.lower.move(h - 1, 0)  # story text grows from the bottom up

    def _resized(self) -> None:
        self.term_h, self.term_w = self.scr.getmaxyx()
        self.scr.erase()
        self._make_lower(min(self._split, self.term_h - 1))
        self._grid_dirty = True

    # -- colours and styles ------------------------------------------------------

    def _pair(self, fg: int, bg: int) -> int:
        if not curses.has_colors():
            return 0
        key = (fg, bg)
        if key not in self._pairs:
            if self._next_pair >= curses.COLOR_PAIRS:
                return 0
            curses.init_pair(self._next_pair, fg, bg)
            self._pairs[key] = self._next_pair
            self._next_pair += 1
        return curses.color_pair(self._pairs[key])

    def _cc(self, value) -> int:
        """A model colour as a curses colour: -1 keeps the terminal's own."""
        if isinstance(value, str):
            return _nearest(value)
        return _CURSES_COLOUR.get(value, -1)

    def _attr(self, style: int, fg, bg) -> int:
        a = self._pair(self._cc(fg), self._cc(bg))
        if style & BOLD:
            a |= curses.A_BOLD
        if style & ITALIC:
            a |= getattr(curses, "A_ITALIC", curses.A_UNDERLINE)
        if style & REVERSE:
            a |= curses.A_REVERSE
        return a

    def _look(self) -> int:
        m = self.vm.screen
        return self._attr(m.style, m.fg, m.bg)

    # -- the upper window: the grid, painted onto the screen ---------------------

    def _grid_changed(self) -> None:
        self._grid_dirty = True
        model_rows = self.vm.screen.rows
        if model_rows != self._split:
            # The split moved: hand the difference to or from the lower
            # window. Its content scrolls on; interpreters never preserved
            # text under a grown status area.
            self._make_lower(min(model_rows, self.term_h - 1))

    def _paint_grid(self) -> None:
        self._grid_dirty = False
        model = self.vm.screen
        for r in range(min(self._split, model.rows)):
            row = model.grid[r]
            for c in range(min(self.term_w - 1, model.cols)):
                cell = row[c]
                try:
                    self.scr.addstr(r, c, cell.char,
                                    self._attr(cell.style, cell.fg, cell.bg))
                except curses.error:
                    pass  # the terminal edge: curses objects, harmlessly
        self.scr.noutrefresh()

    def _refresh(self) -> None:
        if self._grid_dirty:
            self._paint_grid()
        self.lower.noutrefresh()
        curses.doupdate()

    # -- the lower window: wrap, scroll, page -----------------------------------

    def write(self, text: str) -> None:
        attr = self._look()
        width = self.term_w - 1
        for ch in text:
            if ch == "\n":
                self._emit_line(newline=True)
                continue
            self._pending.append((ch, attr))
            if len(self._pending) >= width:
                # Break at the last space; a spaceless line breaks hard.
                brk = next(
                    (i for i in range(len(self._pending) - 1, -1, -1)
                     if self._pending[i][0] == " "),
                    None,
                )
                keep = []
                if brk is not None:
                    keep = self._pending[brk + 1:]
                    del self._pending[brk:]
                else:
                    keep = []
                self._emit_line(newline=True)
                self._pending = keep

    def _emit_line(self, newline: bool) -> None:
        for ch, attr in self._pending:
            try:
                self.lower.addstr(ch, attr)
            except curses.error:
                pass
        self._pending = []
        if newline:
            try:
                self.lower.addstr("\n")
            except curses.error:
                pass
            self._since_input += 1
            self._maybe_page()

    def _maybe_page(self) -> None:
        page = self.lower.getmaxyx()[0] - 1
        if page > 1 and self._since_input >= page:
            y, x = self.lower.getyx()
            try:
                self.lower.addstr("[MORE]", curses.A_REVERSE)
            except curses.error:
                pass
            self._refresh()
            self.lower.getch()
            self.lower.move(y, x)
            self.lower.clrtoeol()
            self._since_input = 0

    def erase_lower(self) -> None:
        self._pending = []
        self.lower.erase()
        # Colour the cleared screen in the game's background (the terminal
        # counterpart of the window repaint at erase, S 8.7.3.3).
        self.lower.bkgd(" ", self._pair(-1, self._cc(self.vm.screen.bg)))
        self.lower.move(self.lower.getmaxyx()[0] - 1, 0)
        self._since_input = 0

    # -- input -------------------------------------------------------------------

    def _flush_prompt(self) -> None:
        """The unfinished line (the prompt) goes to the screen; input
        continues on it."""
        self._emit_line(newline=False)
        self._since_input = 0

    def _redraw_input(self, origin, buffer, attr) -> None:
        y, x = origin
        self.lower.move(y, x)
        self.lower.clrtoeol()
        for ch in buffer:
            try:
                self.lower.addstr(ch, attr)
            except curses.error:
                pass

    def read_line(self, max_len, preload="", terminators=frozenset(),
                  timeout=0.0, on_timeout=None):
        self._flush_prompt()
        attr = self._look()
        buffer = list(preload)
        # The game printed the preload; input starts where it began, so
        # editing it redraws over the game's own characters.
        y, x = self.lower.getyx()
        origin = (y, max(0, x - len(preload)))
        self._refresh()
        self.lower.timeout(int(timeout * 1000) if timeout and on_timeout else -1)
        try:
            while True:
                try:
                    key = self.lower.get_wch()
                except curses.error:
                    # The timeout struck: run the interrupt. Lift the typed
                    # line first, in case it prints; put the line back after.
                    self.lower.move(*origin)
                    self.lower.clrtoeol()
                    self._refresh()
                    ended = on_timeout()
                    self._flush_prompt()
                    origin = self.lower.getyx()
                    if ended:
                        return "".join(buffer), 0
                    self._redraw_input(origin, buffer, attr)
                    self._refresh()
                    continue
                if key == curses.KEY_RESIZE:
                    self._resized()
                    origin = (self.lower.getmaxyx()[0] - 1, 0)
                    self._redraw_input(origin, buffer, attr)
                    self._refresh()
                    continue
                if isinstance(key, int):
                    code = _KEY_ZSCII.get(key)
                    if code and (code in terminators or 255 in terminators):
                        return "".join(buffer), code
                    if key in (curses.KEY_BACKSPACE, curses.KEY_DC):
                        key = "\x7f"
                    else:
                        continue
                if key in ("\n", "\r"):
                    self.lower.addstr("\n")
                    self._since_input = 0
                    return "".join(buffer), 13
                if key in ("\x7f", "\b", "\x08"):
                    if buffer:
                        buffer.pop()
                        self._redraw_input(origin, buffer, attr)
                        self._refresh()
                    continue
                if key.isprintable() and len(buffer) < max_len:
                    buffer.append(key)
                    try:
                        self.lower.addstr(key, attr)
                    except curses.error:
                        pass
                    self._refresh()
        finally:
            self.lower.timeout(-1)

    def read_char(self, timeout=0.0, on_timeout=None) -> int:
        self._flush_prompt()
        self._refresh()
        self.lower.timeout(int(timeout * 1000) if timeout and on_timeout else -1)
        try:
            while True:
                try:
                    key = self.lower.get_wch()
                except curses.error:
                    if on_timeout():
                        return 0
                    self._refresh()
                    continue
                if key == curses.KEY_RESIZE:
                    self._resized()
                    self._refresh()
                    continue
                self._since_input = 0
                if isinstance(key, int):
                    code = _KEY_ZSCII.get(key)
                    if code:
                        return code
                    if key in (curses.KEY_BACKSPACE, curses.KEY_DC):
                        return 8
                    continue
                if key in ("\n", "\r"):
                    return 13
                if key == "\x1b":
                    return 27
                return ord(key)
        finally:
            self.lower.timeout(-1)

    def ask_filename(self, verb: str, default: str):
        self.write(f"\n{verb} [{default}]: ")
        line, _ = self.read_line(120)
        self.write("\n")
        return line.strip() or default

    # -- the run ------------------------------------------------------------------

    def run(self) -> None:
        try:
            self.vm.run()
        except (EOFError, KeyboardInterrupt):
            return
        except ActaeaError as e:
            self.write(f"\n[actaea: {e}]\n")
        # The story quit: hold the final screen (some games print their
        # closing text immediately before @quit; it must be readable).
        self._emit_line(newline=False)
        self.write("\n[The story has ended. Press any key.]")
        self._flush_prompt()
        self._refresh()
        self.lower.getch()


def play(story) -> None:
    locale.setlocale(locale.LC_ALL, "")  # accents render as themselves
    curses.wrapper(lambda scr: ConsoleApp(story, scr).run())
