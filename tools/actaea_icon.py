#!/usr/bin/env python3
# actaea_icon.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
#
# Cut the Actaea icon set from Stefan's star artwork (artworks/actaea.jpeg).
#
# One master painting, three platform conventions:
#
#   actaea.icns   macOS: the art masked into the Big Sur rounded rectangle
#                 (824 of 1024 content, radius 185, the native grid), all
#                 ten iconset sizes, assembled by the system's iconutil.
#   actaea.ico    Windows: the full square, the sizes Explorer asks for.
#   actaea.png    Linux and the Tk window icon: the full square at 512.
#   actaea-128.png  the About panel's star.
#
# The squircle mask is drawn at 4x and downscaled so the corners land
# smooth; each icns size is resampled from the masked 4096 master, never
# from a smaller sibling. Dev-only tool (Pillow, like arcimg); the
# interpreter never imports it. Run from the repo root on a Mac;
# the outputs are committed like the fonts.

import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

SRC = "artworks/actaea.jpeg"
OUT = "actaea/gui/icons"

# Apple's Big Sur icon grid, scaled by 4 for the supersampled master.
CANVAS = 4096
CONTENT = 824 * 4
RADIUS = 185 * 4

ICONSET = [
    ("icon_16x16.png", 16), ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32), ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128), ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256), ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512), ("icon_512x512@2x.png", 1024),
]

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def squircle_master(art: Image.Image) -> Image.Image:
    """The art in the native macOS shape: content square centered on a
    transparent canvas, corners rounded on Apple's grid."""
    content = art.resize((CONTENT, CONTENT), Image.LANCZOS)
    mask = Image.new("L", (CONTENT, CONTENT), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, CONTENT - 1, CONTENT - 1), radius=RADIUS, fill=255)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    margin = (CANVAS - CONTENT) // 2
    canvas.paste(content, (margin, margin), mask)
    return canvas


def main() -> int:
    art = Image.open(SRC).convert("RGBA")
    os.makedirs(OUT, exist_ok=True)

    # macOS: iconset from the squircle master, then iconutil.
    master = squircle_master(art)
    with tempfile.TemporaryDirectory() as tmp:
        iconset = os.path.join(tmp, "actaea.iconset")
        os.makedirs(iconset)
        for name, size in ICONSET:
            master.resize((size, size), Image.LANCZOS).save(
                os.path.join(iconset, name))
        icns = os.path.join(OUT, "actaea.icns")
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns],
                       check=True)

    # Windows: the full square; Pillow derives every listed size.
    art.resize((256, 256), Image.LANCZOS).save(
        os.path.join(OUT, "actaea.ico"),
        sizes=[(s, s) for s in ICO_SIZES])

    # Linux, the Tk window icon, and the About panel.
    art.resize((512, 512), Image.LANCZOS).save(
        os.path.join(OUT, "actaea.png"))
    art.resize((128, 128), Image.LANCZOS).save(
        os.path.join(OUT, "actaea-128.png"))

    for fn in sorted(os.listdir(OUT)):
        path = os.path.join(OUT, fn)
        print("%-18s %8d bytes" % (fn, os.path.getsize(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
