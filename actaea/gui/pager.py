# pager.py
# part of Actaea, the Arcturus reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus
#
# [MORE] PAGING FOR THE WINDOW, the counting half.
#
# The window front end shows story text in a scrollback widget, so without
# paging a passage taller than the reading area simply scrolls past. The
# curses front end has paged since it was written (console.py, _maybe_page);
# this is the same behaviour for the window, kept deliberately separate from
# it: what the two share is a line count, while measuring the height, drawing
# the marker and waiting for the key are nothing alike.
#
# The class here owns the ARITHMETIC and nothing else, so it can be tested
# without a display: how many display lines a piece of text will take, and
# where to cut it so exactly the rest of the page is printed and no more. The
# widget glue lives in app.py.
#
# The window's font is fixed-width and the text area has no internal padding,
# so a display line is exactly `width` characters and the wrapping can be
# computed rather than measured. Tk's wrap="word" is what is reproduced here:
# a word moves to the next line whole, unless it is longer than a whole line,
# in which case it is broken at the margin.


def _tokens(text: str):
    """The text as runs of spaces, runs of other characters, and newlines,
    in order. Wrapping decisions are made a token at a time."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\n":
            out.append("\n")
            i += 1
            continue
        j = i
        space = ch == " "
        while j < n and text[j] != "\n" and (text[j] == " ") == space:
            j += 1
        out.append(text[i:j])
        i = j
    return out


class Pager:
    """Counts display lines since the reader last had a say, and cuts text at
    the page boundary.

    `column` is where the cursor sits on its display line, and `lines` is how
    many display lines have been printed since the last keypress. Both belong
    to the front end's real state: the front end resets them whenever the
    player acts or the screen is wiped."""

    def __init__(self):
        self.column = 0
        self.lines = 0

    def reset(self, column: int = 0) -> None:
        self.lines = 0
        self.column = column

    def feed(self, text: str, width: int, room: int):
        """Split `text` so that at most `room` more display lines are printed.

        Returns (piece, remainder). `piece` is what fits and may be printed
        now; a non-empty `remainder` means the page filled and the reader owes
        a keypress. `self.lines` and `self.column` are advanced by what the
        piece will occupy, so the caller inserts the piece verbatim."""
        if width < 2:
            width = 2
        if room <= 0:
            return "", text
        used = 0
        col = self.column
        out = []
        rest = text
        for token in _tokens(text):
            if token == "\n":
                out.append(token)
                rest = rest[len(token):]
                col = 0
                used += 1
                if used >= room:
                    break
                continue
            if token[0] == " ":
                # Spaces fill to the margin and are swallowed by the wrap:
                # Tk never carries a run of blanks onto the next line.
                out.append(token)
                rest = rest[len(token):]
                col += len(token)
                if col < width:
                    continue
                col = 0
                used += 1
                if used >= room:
                    break
                continue
            word = token
            while word:
                room_left = width - col
                if len(word) <= room_left:
                    out.append(word)
                    rest = rest[len(word):]
                    col += len(word)
                    word = ""
                    continue
                if len(word) <= width and col > 0:
                    # It fits on a line of its own: wrap before it.
                    col = 0
                    used += 1
                    if used >= room:
                        word = ""       # the rest stays in `rest`
                        break
                    continue
                # Longer than a whole line: Tk breaks it at the margin.
                out.append(word[:room_left])
                rest = rest[room_left:]
                word = word[room_left:]
                col = 0
                used += 1
                if used >= room:
                    break
            if used >= room:
                break
        piece = "".join(out)
        # The remainder is taken from the ORIGINAL text by length, so a break
        # inside a token cannot desynchronise the two halves.
        remainder = text[len(piece):]
        self.column = col
        self.lines += used
        return piece, remainder
