#!/usr/bin/env python3
# barflush_probe.py
# Probe for Stefan's report (2026-08-21): Score/Moves still sit adrift of
# the window's right edge after Cosmos 1.16.3 placed them flush.
#
# The GUI's edge fill (app.py, Stefan's fill 2026-07-28) paints every
# upper row out to the canvas edge in its trailing colour, so the BAR
# always reaches the edge on a screenshot even when the game painted
# fewer columns: the text is the only honest witness. This probe boots a
# story in the real window, waits for the first prompt, and prints the
# numbers nobody can argue with: the window's column count, the header's
# stamped count, the model's count, and the exact columns of row 1's
# text runs. Run from the repo root:
#
#   python3 probes/barflush_probe.py <story.z5>

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actaea.loader import load_file
from actaea.gui.app import ActaeaApp


def main() -> int:
    story_path = sys.argv[1]
    story = load_file(story_path)
    app = ActaeaApp(story, "bar probe", story_path=story_path)
    if len(sys.argv) > 2:
        # Reproduce a WIDE window (Stefan's screenshots): the drift only
        # shows away from the aspect's own size.
        app.root.geometry(sys.argv[2])
        app._want_width = int(sys.argv[2].split("x")[0])

    state = {"ticks": 0}

    def pump():
        state["ticks"] += 1
        if app._reading_line or app.vm.halted or state["ticks"] > 400:
            app.root.after(50, report)
            return
        if app._reading_key:
            # A title screen (H2's) waits on a key: press through it.
            app._key_code = 32
            app._key.set(" ")
        app.root.after(25, pump)

    def report():
        model = app.vm.screen
        mem = app.vm.mem
        print("window cols (_cols):", app._cols)
        print("header cols (0x21): ", mem.byte(0x21))
        print("header rows (0x20): ", mem.byte(0x20))
        print("model cols:         ", model.cols, "rows:", model.rows)
        if model.rows:
            row = model.grid[0]
            text = "".join(cell.char for cell in row)
            print("row 1 len:", len(text))
            print("row 1: %r" % text)
            stripped = text.rstrip()
            print("last inked column: %d of %d"
                  % (len(stripped), model.cols))
            # Where does the REVERSE styling stop? The edge fill hides
            # this on screen; the model remembers.
            from actaea.screen import REVERSE
            rev = [i + 1 for i, cell in enumerate(row)
                   if cell.style & REVERSE]
            print("reverse cells: %s..%s (%d of %d)"
                  % (rev[0] if rev else "-", rev[-1] if rev else "-",
                     len(rev), model.cols))
            # THE PIXEL TRUTH (2026-08-21, round three): the model can be
            # flush while the canvas is not. cell arithmetic uses the
            # INTEGER cell_w = measure("0"), but a whole row drawn as one
            # text item advances by the font's TRUE fractional widths,
            # and the error compounds across a hundred columns.
            cw = app.cell_w
            print("cell_w (integer):   ", cw)
            print("cols*cell_w:        ", model.cols * cw)
            print("font.measure(row):  ", app.font.measure(text))
            print("drift over the row: ", model.cols * cw
                  - app.font.measure(text), "px",
                  "(%.2f cells)" % ((model.cols * cw
                                     - app.font.measure(text)) / cw))
            app.root.update_idletasks()
            print("canvas width:       ", app.canvas.winfo_width())
            for item in app.canvas.find_all():
                if app.canvas.type(item) == "text":
                    x1, y1, x2, y2 = app.canvas.bbox(item)
                    if y1 < app.cell_h:
                        print("row-1 text item: x %d..%d (model end %d)"
                              % (x1, x2, len(text.rstrip()) * cw))
        # Never quit() during a live wait_variable: answer the prompt out
        # of the machine first, exactly as the GUI test does.
        if app._reading_line:
            app.text.insert("end-1c", "quit")
            app._on_return(None)
            app.root.after(100, answer_yes)
        else:
            app.root.quit()

    def answer_yes():
        if app._reading_line:
            app.text.insert("end-1c", "y")
            app._on_return(None)
        if app._reading_key:
            app._key_code = ord("y")
            app._key.set("y")
        app.root.after(150, lambda: app.root.quit()
                       if app.vm.halted else answer_yes())

    app.root.after(25, pump)
    try:
        app.run()
    except SystemExit:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
