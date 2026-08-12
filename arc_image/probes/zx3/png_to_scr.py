"""Reconstruct a standard 6912-byte .scr from a Spectrum master PNG.

The masters in arc_image/masters/Spectrum_Masters are byte-validated
extractions of Stefan's 2022 .ZXS bands (256x96, exact Spectrum palette:
channel levels 0/215/255). This inverts the extraction: derive per-cell
ink/paper/bright and the bitmap, place the band at the top of a full
256x192 frame, black bar below - exactly the layout `arcimg unscr`
expects. Ink/paper role assignment inside a cell is not recoverable from
pixels (a role swap with inverted bitmap displays identically), so the
convention is: black is paper when present, otherwise the more frequent
color is paper.
"""
import sys
from PIL import Image


def zx_index(rgb):
    r, g, b = rgb
    for v in (r, g, b):
        if v not in (0, 215, 255):
            raise SystemExit(f"non-Spectrum channel value {rgb}")
    idx = (2 if r else 0) | (4 if g else 0) | (1 if b else 0)
    bright = 1 if 255 in (r, g, b) else 0
    return idx, bright


def scr_offset(y, xb):
    return ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | xb


def main(src, dst):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    assert (w, h) == (256, 96), f"expected 256x96, got {w}x{h}"
    px = im.load()
    out = bytearray(6912)
    for cy in range(12):
        for cx in range(32):
            counts = {}
            for yy in range(8):
                for xx in range(8):
                    idx, br = zx_index(px[cx * 8 + xx, cy * 8 + yy])
                    counts[(idx, br)] = counts.get((idx, br), 0) + 1
            nonblack = [k for k in counts if k[0] != 0]
            if len(nonblack) > 2 or (len(nonblack) == 2 and (0, 0) in counts):
                raise SystemExit(f"cell ({cx},{cy}) breaks the 2-color rule: "
                                 f"{sorted(counts)}")
            brights = {br for (_i, br) in nonblack}
            if len(brights) > 1:
                raise SystemExit(f"cell ({cx},{cy}) mixes bright tiers: "
                                 f"{sorted(counts)}")
            bright = brights.pop() if brights else 0
            if not nonblack:                       # all black
                ink = paper = 0
            elif (0, 0) in counts or (0, 1) in counts:  # black + one color
                paper, ink = 0, nonblack[0][0]
            elif len(nonblack) == 1:               # one solid color
                ink = paper = nonblack[0][0]
            else:                                  # two colors, no black
                a, b = sorted(nonblack, key=lambda k: counts[k])
                ink, paper = a[0], b[0]
            attr = (bright << 6) | (paper << 3) | ink
            out[6144 + cy * 32 + cx] = attr
            ink_rgb_lvl = 255 if bright else 215
            for yy in range(8):
                bbyte = 0
                for xx in range(8):
                    r, g, b = px[cx * 8 + xx, cy * 8 + yy]
                    idx = (2 if r else 0) | (4 if g else 0) | (1 if b else 0)
                    bbyte = (bbyte << 1) | (1 if idx == ink and ink != paper
                                            else 0)
                out[scr_offset(cy * 8 + yy, cx)] = bbyte
    with open(dst, "wb") as f:
        f.write(bytes(out))
    print(f"wrote {dst} (6912 bytes)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
