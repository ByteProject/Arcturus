#!/usr/bin/env python3
# monogram_bold.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
#
# Generate the drawn BOLD cut of monogram for Actaea's Retro look.
#
# monogram (datagoblin, CC0) ships a single weight, and aqua Tk will not
# synthesize one, so Retro had no bold. This builds the classical bitmap
# bold, every glyph unioned with itself shifted one pixel right, but in
# the PIXEL DOMAIN, the way the shape actually lives: each glyph is
# rasterized onto its own design grid (64 font units to the pixel, the
# width of monogram's stems), OR-ed with a one-pixel shift of itself, and
# traced back into clean, non-overlapping outlines. The first attempt
# simply overlaid a shifted copy of the contours and relied on the
# rasterizer's fill rule to union them: FreeType (nonzero) obliged,
# CoreText (even-odd) hollowed every overlap into lattice (Stefan's
# screenshot). Tracing leaves nothing for fill rules to disagree about.
#
# Advances stay untouched: the mono rhythm holds, bold fills more of each
# cell. The result is saved as ITS OWN FAMILY, "monogram bold", regular
# weight: CoreText's matcher served monogram's Italic cut to roman
# requests when two cuts shared a family, so the bold never enters that
# lottery; Actaea asks for it by name.
#
# Dev-only tool (fontTools, installed like pytest); the interpreter never
# imports it. Run from the repo root; the output is committed like the
# other faces. CC0 permits the derivative; the dedication carries forward.

import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

SRC = "actaea/gui/fonts/monogram-extended.ttf"
DST = "actaea/gui/fonts/monogram-extended-bold.ttf"
FAMILY = "monogram bold"
PX = 64          # font units per design pixel: monogram's stems measure 64


def _contours(glyph):
    pts = list(glyph.coordinates)
    ends = list(glyph.endPtsOfContours)
    out, start = [], 0
    for e in ends:
        out.append(pts[start:e + 1])
        start = e + 1
    return out


def _rectilinear_on_grid(contours):
    for c in contours:
        for i, (x1, y1) in enumerate(c):
            x2, y2 = c[(i + 1) % len(c)]
            if x1 % PX or y1 % PX:
                return False
            if x1 != x2 and y1 != y2:
                return False
    return True


def _rasterize(contours):
    """Fill the rectilinear contours (nonzero winding) into a set of
    design-pixel cells. A cell (cx, cy) covers [cx*PX, (cx+1)*PX) by
    [cy*PX, (cy+1)*PX). Scanline per cell row: a vertical edge crossing
    the row's midline flips the winding by its direction."""
    cells = set()
    verticals = []          # (x, ylo, yhi, direction)
    ys = []
    for c in contours:
        for i, (x1, y1) in enumerate(c):
            x2, y2 = c[(i + 1) % len(c)]
            if x1 == x2 and y1 != y2:
                d = 1 if y2 > y1 else -1
                verticals.append((x1 // PX, min(y1, y2) // PX,
                                  max(y1, y2) // PX, d))
                ys += [min(y1, y2) // PX, max(y1, y2) // PX]
    if not verticals:
        return cells
    for row in range(min(ys), max(ys)):
        crossings = sorted((x, d) for x, ylo, yhi, d in verticals
                           if ylo <= row < yhi)
        winding = 0
        prev_x = None
        for x, d in crossings:
            if winding != 0 and prev_x is not None:
                for cx in range(prev_x, x):
                    cells.add((cx, row))
            winding += d
            prev_x = x
    return cells


def _trace(cells):
    """Cells back to closed rectilinear contours, filled area kept on the
    LEFT of the walk, so outers and holes wind oppositely by construction
    and any fill rule agrees on the result."""
    edges = {}              # start point -> list of end points
    def add(a, b):
        edges.setdefault(a, []).append(b)
    for (x, y) in cells:
        if (x, y - 1) not in cells:
            add((x, y), (x + 1, y))          # bottom: rightward
        if (x, y + 1) not in cells:
            add((x + 1, y + 1), (x, y + 1))  # top: leftward
        if (x - 1, y) not in cells:
            add((x, y + 1), (x, y))          # left: downward
        if (x + 1, y) not in cells:
            add((x + 1, y), (x + 1, y + 1))  # right: upward
    contours = []
    while edges:
        start = next(iter(edges))
        path = [start]
        prev_dir = None
        cur = start
        while True:
            outs = edges[cur]
            if len(outs) == 1:
                nxt = outs.pop()
            elif prev_dir is None:
                # A loop STARTING on a checkerboard corner: either arm
                # closes correctly, pick deterministically.
                nxt = sorted(outs)[0]
                outs.remove(nxt)
            else:
                # A checkerboard corner mid-walk: prefer the LEFT turn
                # relative to the incoming direction, which keeps the walk
                # on its own loop instead of jumping to the touching one.
                dx, dy = prev_dir
                left = (cur[0] - dy, cur[1] + dx)
                nxt = left if left in outs else outs[0]
                outs.remove(nxt)
            if not outs:
                del edges[cur]
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            if nxt == start:
                break
            path.append(nxt)
            cur = nxt
        # Collapse collinear runs.
        slim = []
        n = len(path)
        for i, p in enumerate(path):
            a, b = path[i - 1], path[(i + 1) % n]
            if (a[0] == p[0] == b[0]) or (a[1] == p[1] == b[1]):
                continue
            slim.append(p)
        if len(slim) >= 4:
            contours.append(slim)
    return contours


def main() -> int:
    font = TTFont(SRC)
    glyf = font["glyf"]
    done = skipped = 0
    for name in glyf.keys():
        glyph = glyf[name]
        if glyph.numberOfContours <= 0:
            continue  # empty or composite: composites inherit their base
        contours = _contours(glyph)
        if not _rectilinear_on_grid(contours):
            skipped += 1
            continue
        cells = _rasterize(contours)
        # COUNTER-PRESERVING bold, the classical refinement: a pixel only
        # thickens rightward where that does not bridge a one-pixel gap to
        # the next stem. A blanket shift welded monogram's m into a solid
        # block (its counters are a single pixel); with the guard, tight
        # glyphs keep their daylight and roomy ones take the full weight.
        bold = cells | {(x + 1, y) for (x, y) in cells
                        if (x + 2, y) not in cells}
        traced = _trace(bold)
        pts, ends, flags = [], [], []
        for c in traced:
            pts += [(x * PX, y * PX) for (x, y) in c]
            flags += [1] * len(c)
            ends.append(len(pts) - 1)
        glyph.coordinates = GlyphCoordinates(pts)
        glyph.endPtsOfContours = ends
        glyph.flags = bytearray(flags)
        glyph.numberOfContours = len(ends)
        glyph.program = ttProgram.Program()
        glyph.program.fromBytecode(b"")
        glyph.recalcBounds(glyf)
        done += 1

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
    print("wrote %s (%d glyphs emboldened, %d skipped)" % (DST, done, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
