# test_screen.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M8: the cell-grid screen model. The model is renderer-agnostic
truth, so everything here runs headless: the grid semantics directly, then
a real Arcturus game with summon.statusline driving the grid through the
actual opcodes (the Cosmos status bar lands in row 1, styled, stable across
turns). What the Canvas paints from this model is the visible half of the
done-test, verified by a human in the window."""

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.screen import REVERSE, ScreenModel
from actaea.vm import VM

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


class _Sink(CaptureIO):
    def __init__(self):
        super().__init__()
        self.erased = 0

    def erase_lower(self):
        self.erased += 1


def _model():
    sink = _Sink()
    return ScreenModel(sink, cols=20), sink


# -- the grid, directly -----------------------------------------------------------

def test_lower_window_passes_through():
    m, sink = _model()
    m.write("hello")
    assert sink.text == "hello"
    assert m.rows == 0


def test_upper_window_places_cells_and_clips():
    m, sink = _model()
    m.split(2)
    m.select(1)
    m.set_cursor(1, 3)
    m.write("STATUS")
    assert m.row_text(1) == "  STATUS" + " " * 12
    # Nothing leaked to the lower window.
    assert sink.text == ""
    # A write past the last column clips; the row stays exactly cols wide.
    m.set_cursor(2, 18)
    m.write("OVERFLOW")
    assert m.row_text(2).endswith("OVE")
    assert len(m.row_text(2)) == 20


def test_split_keeps_contents_and_homes_a_lost_cursor():
    m, _ = _model()
    m.split(2)
    m.select(1)
    m.set_cursor(2, 1)
    m.write("KEEP")
    m.split(3)                    # growing keeps rows
    assert m.row_text(2).startswith("KEEP")
    m.set_cursor(3, 5)
    m.split(2)                    # shrinking drops row 3, homes the cursor
    assert m.cursor == (1, 1)
    assert m.row_text(2).startswith("KEEP")


def test_selecting_upper_homes_the_cursor():
    m, _ = _model()
    m.split(1)
    m.select(1)
    m.set_cursor(1, 9)
    m.select(0)
    m.select(1)
    assert m.cursor == (1, 1)


def test_erase_variants():
    m, sink = _model()
    m.split(1)
    m.select(1)
    m.write("XXXXX")
    m.erase_window(1)
    assert m.row_text(1) == " " * 20
    m.write("YYYY")
    m.erase_window(-1)            # unsplit and clear everything
    assert m.rows == 0 and m.window == 0
    assert sink.erased == 1
    m.split(1)
    m.select(1)
    m.write("ABCDEFG")
    m.set_cursor(1, 4)
    m.erase_line()
    assert m.row_text(1) == "ABC" + " " * 17


def test_styles_travel_with_cells():
    m, _ = _model()
    m.split(1)
    m.select(1)
    m.style = REVERSE
    m.write("HI")
    assert m.grid[0][0].style == REVERSE
    assert m.grid[0][2].style == 0  # untouched cells stay roman


def test_change_signal_fires_on_visible_changes():
    m, _ = _model()
    hits = []
    m.on_change = lambda: hits.append(1)
    m.split(1)
    m.select(1)
    m.write("A")
    m.erase_window(1)
    assert len(hits) == 3
    m.select(0)
    m.write("lower text")   # pass-through: not a grid change
    assert len(hits) == 3


# -- the real thing: Cosmos's status bar over the actual opcodes ---------------------

GAME = (
    "summon.statusline\n"
    'game\n    title "Grid Probe"\n    start deck\n    scoring\n'
    'room deck\n    name "Observation Deck"\n    desc "Stars wheel past."\n'
    "    south hold\n"
    'room hold\n    name "Cargo Hold"\n    desc "Crates."\n'
    "    north deck\n"
)


def test_cosmos_statusline_draws_into_the_grid():
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    vm = VM(story, CaptureIO(script=["south", "look", "quit", "y"]))
    vm.run(max_steps=2_000_000)
    assert vm.halted
    # The bar kept exactly one row split open through play.
    assert vm.screen.rows == 1
    row = vm.screen.row_text(1)
    # After moving south the bar names the current room, with the score
    # and move counters on the right (the scoring game shows Score/Moves).
    assert "Cargo Hold" in row
    assert "Score" in row and "Moves" in row
    # The Cosmos bar draws in reverse video, cell by cell.
    assert vm.screen.grid[0][1].style & REVERSE
    # And the room description still flowed to the lower window.
    assert "Crates." in vm.io.text


# -- M9: the current look (styles and colours in the model) ---------------------------

def test_colour_state_semantics():
    from actaea.screen import true_colour_hex

    m, _ = _model()
    m.set_colour(5, 2)            # yellow on black
    assert (m.fg, m.bg) == (5, 2)
    m.set_colour(0, 0)            # 0 keeps both
    assert (m.fg, m.bg) == (5, 2)
    m.set_colour(1, 0)            # back to the default foreground
    assert (m.fg, m.bg) == (1, 2)
    m.set_true_colour(0x001D, -1)  # true red, keep background
    assert m.fg == true_colour_hex(0x001D) and m.bg == 2
    m.set_true_colour(-2, -2)     # defaults
    assert (m.fg, m.bg) == (1, 1)
    # Cells written under a colour carry it.
    m.split(1)
    m.select(1)
    m.set_colour(3, 9)
    m.write("R")
    assert (m.grid[0][0].fg, m.grid[0][0].bg) == (3, 9)


def test_style_set_and_clear():
    from actaea.screen import BOLD, ITALIC

    m, _ = _model()
    m.set_style(BOLD)
    m.set_style(ITALIC)           # styles accumulate (S 8.7.1)
    assert m.style == BOLD | ITALIC
    m.set_style(0)                # 0 returns to roman
    assert m.style == 0


def test_colour_and_font_opcodes():
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from zasm import L, QUIT, S, SP, V, build, ext, long2, print_num, vop

    # set_colour 5,2; set_true_colour red,default; set_font twice.
    vm, io, _ = build(
        long2(0x1B, S(5), S(2))                       # set_colour yellow/black
        + ext(0x0D, L(0x001D), L(0xFFFE))             # true red fg, default bg
        + ext(0x04, S(4), store=SP) + print_num(V(SP))  # font 4: prev is 1
        + ext(0x04, S(3), store=SP) + print_num(V(SP))  # font 3: refused, 0
        + ext(0x04, S(0), store=SP) + print_num(V(SP))  # query: still 4
        + QUIT
    )
    vm.run(max_steps=50)
    from actaea.screen import true_colour_hex

    assert vm.screen.fg == true_colour_hex(0x001D)
    assert vm.screen.bg == 1  # -2 = back to default
    assert io.text == "104"  # prev font 1, refusal 0, query answers 4


def test_zcolor_game_drives_the_model():
    # An Arcturus game using the colour syntax: the compiler lowers
    # say.<colour> to set_colour pairs around the text; after play the
    # model is back at the base colour.
    src = (
        'game\n    title "Colour Probe"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "Plain."\n'
        'thing gem in hall\n    name "gem"\n    words gem\n'
        "    on examine\n"
        '        say.yellow "It glitters."\n'
    )
    story = load(generate(analyze(cosmos.combined_program(parse(src)))))
    vm = VM(story, CaptureIO(script=["examine gem", "quit", "y"]))
    vm.run(max_steps=2_000_000)
    assert vm.halted
    assert "It glitters." in vm.io.text
    # flags1 claims colour, so the library's colour path was live.
    assert vm.mem.byte(0x01) & 0x01


# --- the screen size the game is told about -------------------------------
#
# Header 0x21/0x20 must be the front-end's real screen, not a constant (S 11.1).
# Actaea answered 80 columns whatever the terminal was, which is how a status bar
# in a 103-column window came to stop at column 80 (the field report). The io
# boundary now carries the size, and a front-end that can be resized re-stamps
# it through VM.screen_resized().

class _SizedIO(CaptureIO):
    def __init__(self, cols=80, lines=255):
        super().__init__()
        self.size = (cols, lines)

    def screen_size(self):
        return self.size


def _story(src='game\n    title "T"\n    start hall\n'
                'room hall\n    name "Hall"\n    desc "A hall."\n'):
    return load(generate(analyze(cosmos.combined_program(parse(src)))))


def test_the_header_carries_the_front_end_s_size():
    io = _SizedIO(cols=103, lines=30)
    vm = VM(_story(), io)
    assert vm.mem.byte(0x21) == 103      # width in characters
    assert vm.mem.byte(0x20) == 30       # height in lines
    assert vm.mem.word(0x22) == 103      # width in units (one unit per cell)
    assert vm.mem.word(0x24) == 30
    assert vm.screen.cols == 103         # ... and the grid is that wide


def test_a_pipe_still_reports_eighty_by_infinite():
    # The default in io.IOSystem: nothing scrolls in a pipe, so 255 lines is
    # the standard's "infinite" and the honest answer.
    vm = VM(_story(), CaptureIO())
    assert vm.mem.byte(0x21) == 80
    assert vm.mem.byte(0x20) == 255


def test_a_resize_restamps_the_header_and_widens_the_grid():
    io = _SizedIO(cols=80, lines=24)
    vm = VM(_story(), io)
    vm.screen.split(1)
    assert len(vm.screen.grid[0]) == 80
    io.size = (120, 45)
    vm.screen_resized()
    assert vm.mem.byte(0x21) == 120
    assert vm.mem.byte(0x20) == 45
    assert vm.screen.cols == 120
    assert len(vm.screen.grid[0]) == 120   # the row grew with the screen


def test_a_narrower_screen_clips_the_grid_rows():
    io = _SizedIO(cols=120, lines=40)
    vm = VM(_story(), io)
    vm.screen.split(1)
    io.size = (60, 40)
    vm.screen_resized()
    assert vm.screen.cols == 60
    assert len(vm.screen.grid[0]) == 60


def test_an_absurd_size_is_clamped_to_the_header_s_range():
    # The header holds one byte each, so a 400-column terminal reports 255 and
    # a zero-sized one reports 1, rather than writing rubbish into the header.
    io = _SizedIO(cols=400, lines=0)
    vm = VM(_story(), io)
    assert vm.mem.byte(0x21) == 255
    assert vm.mem.byte(0x20) == 1
