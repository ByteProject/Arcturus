# test_pager.py
# part of Actaea, the Arcturus reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""[MORE] paging for the window front end: the counting half (gui/pager.py).

The window shows story text in a scrollback widget, so a passage taller than
the reading area used to scroll past it; the curses front end has paged since
it was written. The Pager owns the arithmetic alone, which is what makes it
testable without a display: how many display lines a piece of text takes at a
given width, and where to cut it so exactly the rest of the page is printed.

The window's font is fixed-width and its text area has no padding, so a
display line is exactly `width` characters and Tk's wrap="word" can be
computed rather than measured."""

from actaea.gui.pager import Pager


def test_a_short_line_fits_and_leaves_the_page_open():
    p = Pager()
    piece, rest = p.feed("Hello.\n", width=40, room=10)
    assert piece == "Hello.\n"
    assert rest == ""
    assert p.lines == 1
    assert p.column == 0


def test_text_without_a_newline_advances_the_column():
    p = Pager()
    piece, rest = p.feed("Hello.", width=40, room=10)
    assert (piece, rest) == ("Hello.", "")
    assert p.lines == 0        # nothing has scrolled yet
    assert p.column == 6


def test_wrapping_counts_the_lines_a_paragraph_will_take():
    # Six five-letter words at width 20: "abcde fghij klmno" fills seventeen
    # columns and the next word will not fit, so the break lands there and
    # the rest makes a second display line.
    p = Pager()
    text = "abcde fghij klmno pqrst uvwxy zabcd\n"
    piece, rest = p.feed(text, width=20, room=10)
    assert rest == ""
    assert piece == text
    assert p.lines == 2, p.lines


def test_the_page_fills_and_the_rest_is_handed_back():
    p = Pager()
    text = "one\ntwo\nthree\nfour\nfive\n"
    piece, rest = p.feed(text, width=40, room=2)
    assert piece == "one\ntwo\n"
    assert rest == "three\nfour\nfive\n"
    assert p.lines == 2


def test_the_remainder_continues_where_it_stopped():
    p = Pager()
    text = "one\ntwo\nthree\n"
    piece, rest = p.feed(text, width=40, room=1)
    p.reset(p.column)
    piece2, rest2 = p.feed(rest, width=40, room=1)
    assert (piece, piece2) == ("one\n", "two\n")
    assert rest2 == "three\n"


def test_a_word_longer_than_a_line_is_broken_at_the_margin():
    p = Pager()
    piece, rest = p.feed("x" * 25, width=10, room=2)
    assert piece == "x" * 20        # two full lines
    assert rest == "x" * 5
    assert p.lines == 2


def test_a_word_that_does_not_fit_moves_whole_to_the_next_line():
    # The break lands BEFORE the word: what is printed now ends with the
    # space, and the word itself starts the next page.
    p = Pager()
    piece, rest = p.feed("aaaa bbbbbbbb", width=10, room=1)
    assert piece == "aaaa "
    assert rest == "bbbbbbbb"
    assert p.lines == 1


def test_a_blank_line_counts_as_a_line():
    p = Pager()
    piece, rest = p.feed("\n\n\n", width=40, room=2)
    assert piece == "\n\n"
    assert rest == "\n"
    assert p.lines == 2


def test_no_room_hands_everything_back():
    p = Pager()
    piece, rest = p.feed("anything", width=40, room=0)
    assert (piece, rest) == ("", "anything")


def test_reset_starts_a_fresh_count_but_keeps_the_column():
    p = Pager()
    p.feed("Hello.", width=40, room=10)
    p.reset(p.column)
    assert p.lines == 0 and p.column == 6
    # Text after a [MORE] continues on the same display line.
    piece, rest = p.feed(" More.\n", width=40, room=2)
    assert (piece, rest) == (" More.\n", "")
    assert p.lines == 1


def test_a_real_paragraph_pages_at_the_right_place():
    # A room description at the width and height a picture band leaves in
    # Actaea's window: 80 columns, a dozen rows of text under the band.
    text = (
        "The gatehouse arch is a black mouth in a blacker wall, and the "
        "portcullis teeth above it have not been raised in living memory.\n"
        "A lantern gutters on its hook by the guardroom door.\n"
        "You can go north or east.\n"
    )
    p = Pager()
    piece, rest = p.feed(text, width=80, room=2)
    assert rest, "the passage is taller than two lines: it must pause"
    assert piece + rest == text
    assert p.lines == 2
