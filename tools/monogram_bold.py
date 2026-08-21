#!/usr/bin/env python3
# monogram_bold.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
#
# Generate the drawn BOLD cut of monogram for Actaea's Retro look.
#
# monogram (datagoblin, CC0) ships a single weight, and aqua Tk will not
# synthesize one, so Retro had no bold at all. This makes the classical
# bitmap bold: every glyph unioned with itself shifted one design pixel to
# the right, exactly how the 8-bit machines and DOS text modes did it.
# TrueType's nonzero winding renders overlapping contours as their union,
# so the construction is purely mechanical: append a shifted copy of each
# simple glyph's contours. Advances stay untouched: the mono rhythm holds,
# the bold simply fills more of each cell.
#
# The result is saved as ITS OWN FAMILY, "monogram bold", regular weight:
# CoreText's matcher already served monogram's Italic cut to roman requests
# when two cuts shared the family, so the bold never enters that lottery;
# Actaea asks for the family by name.
#
# Dev-only tool (fontTools, installed like pytest); the interpreter never
# imports it. Run from the repo root; the output is committed like the
# other faces. CC0 permits the derivative; the dedication carries forward.

import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

SRC = "actaea/gui/fonts/monogram-extended.ttf"
DST = "actaea/gui/fonts/monogram-extended-bold.ttf"
FAMILY = "monogram bold"


def main() -> int:
    font = TTFont(SRC)
    upm = font["head"].unitsPerEm
    # The design grid: at 8 points monogram renders one pixel per design
    # pixel, so a design pixel is upm/8 units. Verified against the "0"
    # advance, which measures three design pixels.
    px = upm // 8
    glyf = font["glyf"]
    emboldened = 0
    for name in glyf.keys():
        glyph = glyf[name]
        if glyph.numberOfContours <= 0:
            continue  # empty or composite: composites inherit their base
        coords, ends, flags = (glyph.coordinates, glyph.endPtsOfContours,
                               glyph.flags)
        n = len(coords)
        shifted = coords.copy()
        shifted.translate((px, 0))
        # GlyphCoordinates treats + as vector addition: concatenate by hand.
        glyph.coordinates = GlyphCoordinates(list(coords) + list(shifted))
        glyph.endPtsOfContours = list(ends) + [e + n for e in ends]
        glyph.flags = bytearray(list(flags) + list(flags))
        glyph.numberOfContours = len(glyph.endPtsOfContours)
        # The original hinting program indexed the original points: drop it
        # (a pixel font on its grid needs no hints).
        if hasattr(glyph, "program"):
            from fontTools.ttLib.tables import ttProgram
            glyph.program = ttProgram.Program()
            glyph.program.fromBytecode(b"")
        glyph.recalcBounds(glyf)
        emboldened += 1

    name = font["name"]
    for nid in (1, 16):
        name.setName(FAMILY, nid, 3, 1, 0x409)
        name.setName(FAMILY, nid, 1, 0, 0)
    for nid, val in ((2, "Regular"), (17, "Regular"),
                     (4, FAMILY), (6, "monogrambold"),
                     (3, "monogram bold: Actaea Retro derived cut")):
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)

    font.save(DST)
    print("wrote %s (%d glyphs emboldened, design pixel %d units)"
          % (DST, emboldened, px))
    return 0


if __name__ == "__main__":
    sys.exit(main())
