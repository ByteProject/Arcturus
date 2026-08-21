#!/usr/bin/env python3
# about_mockup.py
# Mockups for Stefan's About-panel star size (2026-08-21): four panels
# in ONE image (comparisons never live in separate windows), star at
# 128 (current), 192, 256, and 320 points, everything else held equal.
# Rendered at 2x, matching how the panel appears on his retina screen.
# Output: ~/Desktop/actaea-about-sizes.png

import os

from PIL import Image, ImageDraw, ImageFont

ART = "artworks/actaea.jpeg"
FONTS = "actaea/gui/fonts"
OUT = os.path.expanduser("~/Desktop/actaea-about-sizes.png")

SIZES = [(128, "128 pt (current)"), (192, "192 pt"),
         (256, "256 pt"), (320, "320 pt")]
S = 2                       # retina scale: 1 pt = 2 px
PANEL_W = 486 * S
GAP = 40
LABEL_H = 70

BODY = ["Z-machine v5/8 interpreter, debugger and disassembler",
        "Standard 1.1 conformant",
        "Part of Arcturus (programming language & compiler)"]


def panel(art, star_pt, fonts):
    name_f, ver_f, body_f, link_f = fonts
    star_px = star_pt * S
    h = (40 * S + star_px + 6 * S + 34 * S + 26 * S + 3 * 22 * S
         + 30 * S + 24 * S + 60 * S)
    img = Image.new("RGB", (PANEL_W, h), "white")
    d = ImageDraw.Draw(img)
    y = 40 * S
    star = art.resize((star_px, star_px), Image.LANCZOS)
    img.paste(star, ((PANEL_W - star_px) // 2, y))
    y += star_px + 10 * S

    def center(text, font, fill, dy):
        nonlocal y
        w = d.textlength(text, font=font)
        d.text(((PANEL_W - w) // 2, y), text, font=font, fill=fill)
        y += dy

    center("Actaea", name_f, "black", 40 * S)
    center("Version 2.0.0", ver_f, "#222222", 30 * S)
    y += 8 * S
    for line in BODY:
        center(line, body_f, "#111111", 21 * S)
    y += 10 * S
    center("Copyright (c) 2026, Stefan Vogt", body_f, "#111111", 24 * S)
    center("https://github.com/ByteProject/Arcturus", link_f, "#2b66c4",
           24 * S)
    return img


def main() -> int:
    art = Image.open(ART).convert("RGB")
    name_f = ImageFont.truetype(os.path.join(FONTS, "Roboto-Bold.ttf"),
                                26 * S)
    ver_f = ImageFont.truetype(os.path.join(FONTS, "Roboto-Regular.ttf"),
                               14 * S)
    body_f = ImageFont.truetype(os.path.join(FONTS, "Roboto-Regular.ttf"),
                                13 * S)
    label_f = ImageFont.truetype(os.path.join(FONTS, "Roboto-Bold.ttf"),
                                 15 * S)
    fonts = (name_f, ver_f, body_f, ver_f)

    panels = [panel(art, pt, fonts) for pt, _ in SIZES]
    height = max(p.height for p in panels) + LABEL_H
    total_w = GAP + sum(p.width + GAP for p in panels)
    sheet = Image.new("RGB", (total_w, height + GAP * 2), "#3a3a3c")
    d = ImageDraw.Draw(sheet)
    x = GAP
    for p, (pt, label) in zip(panels, SIZES):
        sheet.paste(p, (x, GAP))
        d.rectangle((x - 1, GAP - 1, x + p.width, GAP + p.height),
                    outline="#8a8a8e")
        w = d.textlength(label, font=label_f)
        d.text((x + (p.width - w) // 2, GAP + height - LABEL_H + 20),
               label, font=label_f, fill="white")
        x += p.width + GAP
    sheet.save(OUT)
    print("wrote %s (%dx%d)" % (OUT, sheet.width, sheet.height))
    return 0


if __name__ == "__main__":
    return_code = main()
    raise SystemExit(return_code)
