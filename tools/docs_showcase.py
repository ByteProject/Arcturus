#!/usr/bin/env python3
# docs_showcase.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Build the arc_image showcase pictures for docs/07 into artworks/docs/.

The author guide shows one master and its conversion on every machine, so a
reader can see what their painting becomes before they commit to the
workflow. Those pictures are DERIVED, never hand-made: this tool rebuilds
them from the committed corpus, so the guide can never drift away from what
the converters actually produce (the shop-window rule). Re-run it whenever a
converter changes:

    python3 tools/docs_showcase.py

SCALE AND ASPECT. Every showcase picture ends 192 pixels tall, at one
consistent scale: two screen pixels per master row. The width is then the
machine's TRUE window, which is the point of the comparison. A 320-wide
machine gives 640; the MSX and Spectrum crop their band to 256 columns and
so give 512, narrower on the page exactly as they are narrower on the
screen; the Apple II's 560 dots and the half-width pixels of the Model 4
and the Agon land at their own honest widths. Machines whose pixels are
half as wide as tall are doubled vertically, never horizontally, so nothing
is stretched into a shape the hardware does not have.

Stdlib only, deterministic: same corpus in, same bytes out.
"""

import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "artworks", "docs")
MASTER = "8"                    # the moon forest: the guide's example scene

_spec = importlib.util.spec_from_file_location(
    "arcimg", os.path.join(ROOT, "tools", "arcimg.py"))
arcimg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arcimg)

# tag -> (horizontal scale, vertical scale) taking each preview to 192 tall
SCALE = {
    "AMI": (2, 2), "AST": (2, 2), "DOS": (2, 2), "C64": (2, 2),
    "P4": (2, 2), "CPC": (2, 2), "A8": (2, 2), "NXT": (2, 2),
    "M65": (2, 2),
    "MS1": (2, 2), "MS2": (2, 2), "ZX3": (2, 2),   # 256-wide window -> 512
    "AP2": (1, 1),                                  # already 560x192
    "TRSM4": (1, 2), "AGN": (1, 2),                 # half-width pixels
}


def _scaled(rows, sx, sy):
    out = []
    for row in rows:
        wide = [c for c in row for _ in range(sx)]
        for _ in range(sy):
            out.append(list(wide))
    return out


def build():
    os.makedirs(OUT, exist_ok=True)
    written = []

    src = os.path.join(ROOT, "arc_image", "masters", f"{MASTER}.png")
    rows = arcimg._read_png(src)
    dest = os.path.join(OUT, "arcimage-master.png")
    arcimg._write_png(dest, _scaled(rows, 2, 2))
    written.append((dest, len(rows[0]) * 2, len(rows) * 2,
                    len({c for r in rows for c in r})))

    for tag, (sx, sy) in SCALE.items():
        prev = os.path.join(ROOT, "arc_image", "previews", tag.lower(),
                            f"{MASTER}-{tag}.png")
        if not os.path.exists(prev):
            print(f"  (skipped {tag}: no preview; run arcimg convert first)")
            continue
        rows = arcimg._read_png(prev)
        big = _scaled(rows, sx, sy)
        dest = os.path.join(OUT, f"arcimage-{tag.lower()}.png")
        arcimg._write_png(dest, big)
        written.append((dest, len(big[0]), len(big),
                        len({c for r in rows for c in r})))

    for path, w, h, colours in written:
        print(f"  {os.path.relpath(path, ROOT):<34} {w}x{h}, {colours} colours")
    print(f"wrote {len(written)} showcase pictures to "
          f"{os.path.relpath(OUT, ROOT)}/")


if __name__ == "__main__":
    build()
