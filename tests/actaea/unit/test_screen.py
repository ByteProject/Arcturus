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
