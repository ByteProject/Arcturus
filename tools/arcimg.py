#!/usr/bin/env python3
# arcimg.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arcimg: the arc_image preparation tool.

An arc_image id is a resource slot: a room says `arc_image 8`, and an aware
interpreter loads picture 8. This tool turns an author's source art into the
numbered picture files that back those slots, and packs them for distribution.

Two picture shapes (docs/00, the graphics plan):

  infocom   320x72   9 rows, the upper third, the classic Arthur look
  daad      320x96   12 rows, the upper half, the Rabenstein look

Both are pixel-art dimensions that hold a whole number of 8-pixel text rows, so
the status bar sits flush beneath the band. On modern systems an interpreter
integer-scales the picture to the window (crisp for pixel art); the display is
integer-scaled either way, so pixel art is the medium that looks best.

Commands:

  arcimg pack SOURCES... -o story.arcres
      Zip the numbered PNGs found in the given files/directories into an
      .arcres pack (one file, keyed by id, the story kept separate). Stdlib
      only: pixel artists whose art is already sized never need anything else.

  arcimg prep SOURCE --id N --mode {infocom,daad} [-o DIR]
      Produce N.png sized to a mode. A PNG already at the exact mode size is
      just copied (stdlib). Any other source (a photo, a JPEG, a wrong size) is
      centre-cropped to the mode's aspect and resized, which needs Pillow; the
      tool offers to install it, guided, the first time it is needed.

  arcimg info SOURCE
      Report the size of a PNG, or list the pictures in an .arcres pack.

Pillow is an author-side convenience, never shipped to players: arcc and the
Actaea interpreter stay pure standard library. It is reached only to resize or
convert a source that is not already a mode-sized PNG.
"""

import argparse
import os
import re
import shutil
import struct
import sys
import zipfile

__version__ = "1.0.1"

# The build fingerprint, in the manner of arcc and actaea: __version__ names the
# intended release, and __build__ is a short content hash the amalgamator bakes
# into build/arcimg so `arcimg --version` names the exact build. None here means
# the tool is running from source, not the standalone.
__build__ = None


def build_id() -> str:
    return __build__ or "source"


def _banner() -> str:
    """The identity block, matching the arcc and actaea family: three lines and
    no build id, so it stays clean leading every command; --version appends the
    build itself (version_text)."""
    return (
        f"arcimg v{__version__} - image processor and converter\n"
        "Part of Arcturus, programming language & compiler for the Infocom "
        "Z-machine\n"
        "Copyright (c) 2026, Stefan Vogt | "
        "https://github.com/ByteProject/Arcturus"
    )


def _version_text() -> str:
    """The banner plus the exact build, for `arcimg --version`."""
    return f"{_banner()}\nBuild {build_id()}"


# The picture modes: mode name -> (width, height) in pixels. Both are whole
# multiples of the 8-pixel text row (72 = 9 rows, 96 = 12 rows), which is what
# lets the status bar align flush under the band on every target.
MODES = {
    "infocom": (320, 72),   # 9 rows, upper third, the Arthur look
    "daad": (320, 96),      # 12 rows, upper half, the Rabenstein look
}

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_NUMBERED = re.compile(r"^(\d+)\.png$", re.IGNORECASE)


# -- small stdlib helpers (no Pillow) ------------------------------------------

def _numbered_id(name: str):
    """The id from a `<number>.png` filename, or None. The number is the
    resource slot, so 8.png is picture 8."""
    m = _NUMBERED.match(os.path.basename(name))
    return int(m.group(1)) if m else None


def _png_size_bytes(data: bytes):
    """(width, height) read straight from a PNG's IHDR header, or None if the
    bytes are not a PNG. No decode, no third-party library."""
    if len(data) < 24 or data[:8] != _PNG_SIG or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _png_size(path: str):
    """(width, height) of a PNG file, or None if it is not a readable PNG."""
    try:
        with open(path, "rb") as f:
            return _png_size_bytes(f.read(24))
    except OSError:
        return None


def _mode_of(dims):
    """The mode name whose dimensions match, or None."""
    for name, wh in MODES.items():
        if wh == dims:
            return name
    return None


def _modes_str():
    return ", ".join(f"{n} {w}x{h}" for n, (w, h) in MODES.items())


# -- Pillow, reached only when a source must be resized or converted -----------

def _ensure_pillow():
    """Return PIL.Image, installing Pillow first (with the author's consent) if
    it is missing. Pillow is needed only to resize or convert a source that is
    not already a mode-sized PNG; mode-sized PNGs never reach here."""
    try:
        from PIL import Image
        return Image
    except ImportError:
        pass

    print("arcimg: this step needs Pillow (the Python imaging library), which")
    print("        is not installed for this interpreter:")
    print(f"          {sys.executable}")
    try:
        answer = input("Install Pillow now with pip? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        print()
        print("arcimg: without Pillow this tool can only pack art that is")
        print("        already a PNG at a mode's exact size. Size your picture")
        print(f"        to one of: {_modes_str()}, then use `arcimg pack`.")
        raise SystemExit(2)

    import subprocess
    rc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "Pillow"]
    ).returncode
    if rc != 0:
        print("arcimg: pip could not install Pillow.", file=sys.stderr)
        raise SystemExit(2)
    try:
        from PIL import Image
        return Image
    except ImportError:
        print("arcimg: Pillow installed but could not be imported; try again "
              "in a fresh shell.", file=sys.stderr)
        raise SystemExit(2)


def _crop_to_ratio(img, tw: int, th: int):
    """Centre-crop an image to the target aspect ratio (so a resize afterwards
    never squashes it), keeping as much of the picture as the ratio allows."""
    w, h = img.size
    target = tw / th
    cur = w / h
    if cur > target:                 # too wide: trim the sides
        new_w = max(1, round(h * target))
        x = (w - new_w) // 2
        return img.crop((x, 0, x + new_w, h))
    if cur < target:                 # too tall: trim top and bottom
        new_h = max(1, round(w / target))
        y = (h - new_h) // 2
        return img.crop((0, y, w, y + new_h))
    return img


# -- commands ------------------------------------------------------------------

def cmd_prep(args) -> int:
    w, h = MODES[args.mode]
    out_dir = args.out or "."
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, f"{args.id}.png")

    # Fast path: art already a PNG at the exact mode size is just numbered and
    # copied. This is the pixel artist's whole workflow, and it needs no Pillow.
    if _png_size(args.source) == (w, h):
        shutil.copyfile(args.source, dest)
        print(f"arcimg: {args.source} is already {w}x{h} ({args.mode}); "
              f"wrote {dest}")
        return 0

    # Anything else (a photo, a JPEG, a wrong-sized PNG): crop to the mode's
    # aspect and resize to it. This is where Pillow is needed.
    Image = _ensure_pillow()
    try:
        img = Image.open(args.source).convert("RGB")
    except (OSError, ValueError) as exc:
        print(f"arcimg: cannot read {args.source}: {exc}", file=sys.stderr)
        return 2
    img = _crop_to_ratio(img, w, h)
    img = img.resize((w, h), Image.LANCZOS)
    img.save(dest, "PNG")
    print(f"arcimg: wrote {dest} ({w}x{h}, {args.mode} mode)")
    return 0


def _collect_numbered(sources):
    """Map id -> path for every <number>.png in the given files and directories.
    A later source with the same id wins, so a specific file can override a
    directory listed before it."""
    entries = {}
    for src in sources:
        if os.path.isdir(src):
            for name in sorted(os.listdir(src)):
                iid = _numbered_id(name)
                if iid is not None:
                    entries[iid] = os.path.join(src, name)
        elif os.path.isfile(src):
            iid = _numbered_id(src)
            if iid is None:
                print(f"arcimg: skipping {src}: not a <number>.png file",
                      file=sys.stderr)
            else:
                entries[iid] = src
        else:
            print(f"arcimg: skipping {src}: no such file or directory",
                  file=sys.stderr)
    return entries


def cmd_pack(args) -> int:
    entries = _collect_numbered(args.sources)
    if not entries:
        print("arcimg: no <number>.png files to pack", file=sys.stderr)
        return 2

    # Validate every entry is a real PNG, and note any that are not a standard
    # mode size (allowed, but usually a mistake worth flagging).
    for iid in sorted(entries):
        dims = _png_size(entries[iid])
        if dims is None:
            print(f"arcimg: {entries[iid]} is not a valid PNG", file=sys.stderr)
            return 2
        if _mode_of(dims) is None:
            print(f"arcimg: note: {os.path.basename(entries[iid])} is "
                  f"{dims[0]}x{dims[1]}, not a standard mode size "
                  f"({_modes_str()})")

    try:
        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
            for iid in sorted(entries):
                z.write(entries[iid], f"{iid}.png")
    except OSError as exc:
        print(f"arcimg: cannot write {args.out}: {exc}", file=sys.stderr)
        return 2
    ids = ", ".join(str(i) for i in sorted(entries))
    print(f"arcimg: wrote {args.out} ({len(entries)} pictures: {ids})")
    return 0


def cmd_info(args) -> int:
    src = args.source
    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            names = [n for n in z.namelist() if _numbered_id(n) is not None]
            print(f"{src}: {len(names)} pictures")
            for n in sorted(names, key=_numbered_id):
                dims = _png_size_bytes(z.read(n))
                shape = f"{dims[0]}x{dims[1]}" if dims else "?"
                mode = _mode_of(dims) if dims else None
                tag = f" ({mode} mode)" if mode else ""
                print(f"  {_numbered_id(n):>4}  {shape}{tag}")
        return 0

    dims = _png_size(src)
    if dims is None:
        print(f"arcimg: {src} is not a PNG or an .arcres pack", file=sys.stderr)
        return 2
    mode = _mode_of(dims)
    tag = f" ({mode} mode)" if mode else " (not a standard mode size)"
    print(f"{src}: {dims[0]}x{dims[1]}{tag}")
    return 0


class _Version(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(_version_text() + "\n")
        parser.exit()


class _Parser(argparse.ArgumentParser):
    """An ArgumentParser whose help leads with the banner, so `-h` (and each
    subcommand's `-h`) shows the identity block the way every other invocation
    does. Subparsers inherit this class, so `arcimg pack -h` gets it too."""

    def format_help(self) -> str:
        # A trailing blank line too, so help ends with the same whitespace before
        # the prompt that command output does.
        return f"{_banner()}\n\n{super().format_help()}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(
        prog="arcimg",
        description="Prepare and pack arc_image pictures for Arcturus stories.",
    )
    ap.add_argument("--version", action=_Version, nargs=0,
                    help="show the version banner and exit")
    sub = ap.add_subparsers(dest="command")

    p_pack = sub.add_parser(
        "pack", help="zip numbered PNGs into an .arcres pack")
    p_pack.add_argument("sources", nargs="+",
                        help="directories and/or <number>.png files")
    p_pack.add_argument("-o", "--out", required=True,
                        help="the .arcres pack to write")
    p_pack.set_defaults(func=cmd_pack)

    p_prep = sub.add_parser(
        "prep", help="size a source image to a mode and number it")
    p_prep.add_argument("source", help="the source image (PNG, or any format "
                        "Pillow reads)")
    p_prep.add_argument("--id", type=int, required=True,
                        help="the picture id (the resource slot); output is "
                        "<id>.png")
    p_prep.add_argument("--mode", choices=sorted(MODES), default="daad",
                        help="the picture shape (default: daad)")
    p_prep.add_argument("-o", "--out", help="output directory (default: .)")
    p_prep.set_defaults(func=cmd_prep)

    p_info = sub.add_parser(
        "info", help="report a PNG's size or list a pack's pictures")
    p_info.add_argument("source", help="a PNG file or an .arcres pack")
    p_info.set_defaults(func=cmd_info)
    return ap


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Every invocation leads with the header, the way arcc and actaea do; no
    # command shows the banner and a usage hint.
    if args.command is None:
        print(_banner())
        print("\nType 'arcimg -h' for help.   Commands: pack, prep, info\n")
        return 0
    print(_banner() + "\n")
    rc = args.func(args)
    print()  # a blank line between the output and the prompt
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
