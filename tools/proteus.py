#!/usr/bin/env python3
# proteus.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""proteus: the Arcturus web export tool.

Proteus is the Arcturus web interpreter (a Z-machine-only fork of Parchment
with arc_image support, living in proteus/ inside the Arcturus repository).
This tool turns a finished game into one self-contained HTML file that plays
in any browser: the interpreter, the styles, the font, the story, and its
pictures, all inside a single page. Upload it anywhere (itch.io, your own
webspace) and it runs; there is nothing else to deploy.

Usage:

  proteus story.zblorb -o game.html
      The single-file shape: a zblorb made with `arcimg pack --zblorb`
      already carries the story and its pictures together.

  proteus story.z5 pictures.blorb -o game.html
      The pair shape: a bare story plus the pictures-only Blorb made with
      `arcimg pack --blorb`. The tool splices them into a zblorb first.

  proteus story.z5 -o game.html
      A text-only game; no pictures, no Blorb, still one page.

The web resources ride inside this tool (the amalgamated build embeds the
Proteus single-file template). Standard library only, the arcc manner.
"""

import argparse
import base64
import gzip
import re
import struct
import sys
from pathlib import Path

__version__ = "1.0.0"
__build__ = None

# The amalgamation replaces this with the gzipped, base64-coded template;
# from the repository the tool reads the built template beside itself
# instead, so the dev loop needs no amalgam.
TEMPLATE_B64: str | None = None

_REPO_TEMPLATE = Path(__file__).resolve().parent.parent / "proteus" / "dist" / "single-file" / "proteus.html"


def _banner() -> str:
    """The identity block, matching the arcc and actaea family."""
    return (
        f"proteus v{__version__} - web story builder\n"
        "Part of Arcturus, programming language & compiler for the Infocom "
        "Z-machine\n"
        "Copyright (c) 2026, Stefan Vogt | "
        "https://github.com/ByteProject/Arcturus"
    )


class _Parser(argparse.ArgumentParser):
    """The family's spacing on every argparse-driven exit: a blank line
    between the banner and the usage, between the usage and the error,
    and one before the prompt returns. Everything on stdout."""

    def error(self, message):
        print()
        self.print_usage(sys.stdout)
        print()
        print(f"{self.prog}: error: {message}")
        print()
        raise SystemExit(2)

    def print_help(self, file=None):
        print()
        super().print_help(file or sys.stdout)
        print()


class _Version(argparse.Action):
    """--version: the banner has already led the output (every invocation
    leads with it), so this adds the build line beneath and exits."""

    def __call__(self, parser, namespace, values, option_string=None):
        print(f"Build {__build__ or 'source'}")
        print()
        raise SystemExit(0)


def load_template() -> str:
    if TEMPLATE_B64 is not None:
        return gzip.decompress(base64.b64decode(TEMPLATE_B64)).decode("utf-8")
    if _REPO_TEMPLATE.is_file():
        return _REPO_TEMPLATE.read_text(encoding="utf-8")
    raise SystemExit(
        "proteus: no embedded template and no built one at "
        f"{_REPO_TEMPLATE}; run `node build.js && node tools/make-single-file.js "
        "--out dist/single-file` in proteus/ first, or use the amalgamated "
        "build/proteus."
    )


# --------------------------------------------------------------------------
# Blorb splicing: story + pictures-only blorb -> zblorb. An IFF FORM/IFRS
# holds chunks; RIdx (always first) indexes the resources by the byte
# offset of each chunk header. Inserting the ZCOD chunk shifts every
# offset, so the index is rebuilt, not patched.
# --------------------------------------------------------------------------

def _parse_blorb(data: bytes):
    if data[0:4] != b"FORM" or data[8:12] != b"IFRS":
        raise SystemExit("proteus: not a Blorb file")
    chunks = []  # (fourcc, payload, header_offset)
    pos = 12
    while pos + 8 <= len(data):
        fourcc = data[pos:pos + 4]
        (length,) = struct.unpack(">I", data[pos + 4:pos + 8])
        payload = data[pos + 8:pos + 8 + length]
        chunks.append((fourcc, payload, pos))
        pos += 8 + length + (length & 1)
    if not chunks or chunks[0][0] != b"RIdx":
        raise SystemExit("proteus: malformed Blorb, first chunk is not RIdx")
    return chunks


def _resource_entries(ridx_payload: bytes):
    (count,) = struct.unpack(">I", ridx_payload[0:4])
    entries = []  # (usage, number, chunk_header_offset)
    for i in range(count):
        usage, number, offset = struct.unpack(
            ">4sII", ridx_payload[4 + 12 * i:16 + 12 * i])
        entries.append((usage, number, offset))
    return entries


def splice_zblorb(story: bytes, blorb: bytes) -> bytes:
    """Insert the story as Exec 0 (ZCOD) into a pictures Blorb."""
    chunks = _parse_blorb(blorb)
    entries = _resource_entries(chunks[0][1])
    if any(usage == b"Exec" for usage, _, _ in entries):
        raise SystemExit(
            "proteus: that Blorb already carries a story (Exec); pass it "
            "alone, without the separate story file")

    # The body: the story first, then every old chunk except RIdx, in order.
    body = [(b"ZCOD", story)]
    offset_of = {}  # old header offset -> body index
    for fourcc, payload, old_offset in chunks[1:]:
        offset_of[old_offset] = len(body)
        body.append((fourcc, payload))

    # Lay the body out after the rebuilt RIdx and record new offsets.
    new_entries = [(b"Exec", 0, 0)]
    for usage, number, old_offset in entries:
        new_entries.append((usage, number, offset_of[old_offset]))
    ridx_len = 4 + 12 * len(new_entries)
    positions = []
    pos = 12 + 8 + ridx_len + (ridx_len & 1)
    for fourcc, payload in body:
        positions.append(pos)
        pos += 8 + len(payload) + (len(payload) & 1)

    ridx = struct.pack(">I", len(new_entries))
    for usage, number, body_index in new_entries:
        ridx += struct.pack(">4sII", usage, number, positions[body_index])

    out = bytearray()
    out += b"FORM\0\0\0\0IFRS"
    for fourcc, payload in [(b"RIdx", ridx)] + body:
        out += fourcc + struct.pack(">I", len(payload)) + payload
        if len(payload) & 1:
            out += b"\0"
    struct.pack_into(">I", out, 4, len(out) - 8)
    return bytes(out)


# --------------------------------------------------------------------------
# The page: inject the story into the template the way the Proteus
# single-file builder does it (gzip, base64, a text/plain;gzip script tag,
# and a story entry in the options), plus the title in the Actaea manner.
# --------------------------------------------------------------------------

def build_page(template: str, story_data: bytes, filename: str) -> str:
    packed = base64.b64encode(gzip.compress(story_data, 9)).decode("ascii")
    story_script = (
        f'<script type="text/plain;gzip" id="{filename}">{packed}</script>\n'
        f'<script>parchment_options.story = '
        f'{{"url": "embedded:{filename}", "format": "zcode"}}</script>\n'
    )
    if "</head>" not in template or "parchment_options" not in template:
        raise SystemExit("proteus: the template is missing its anchors; "
                         "rebuild the single-file template")
    page = template.replace("</head>", story_script + "</head>", 1)
    page = re.sub(r"<title>[^<]*</title>",
                  f"<title>Proteus - {filename}</title>", page, count=1)
    return page


def _looks_like_story(data: bytes) -> bool:
    return len(data) > 64 and data[0] in (3, 4, 5, 7, 8)


def _looks_like_blorb(data: bytes) -> bool:
    return data[0:4] == b"FORM" and data[8:12] == b"IFRS"


def main(argv=None) -> int:
    # Every invocation leads with the banner, the way arcc and actaea do.
    print(_banner())
    parser = _Parser(
        prog="proteus",
        description="Turn a finished Arcturus game into one self-contained "
                    "web page.")
    parser.add_argument("sources", nargs="+",
                        help="a zblorb; or a story file plus its pictures "
                             "Blorb; or a bare story for a text-only game")
    parser.add_argument("-o", "--out", required=True,
                        help="the HTML file to write")
    parser.add_argument("--version", action=_Version, nargs=0,
                        help="show the version and build")
    args = parser.parse_args(argv)
    print()

    try:
        return _run(args)
    except SystemExit as exc:
        # Our own refusals: print the message with the family's trailing
        # blank line instead of the bare stderr exit.
        if isinstance(exc.code, str):
            print(exc.code)
            print()
            return 1
        raise


def _run(args) -> int:
    if len(args.sources) > 2:
        raise SystemExit("proteus: at most two inputs, a story and its Blorb")

    files = []
    for src in args.sources:
        path = Path(src)
        if not path.is_file():
            raise SystemExit(f"proteus: cannot read {src}")
        files.append((path, path.read_bytes()))

    story_name = None
    if len(files) == 2:
        (p1, d1), (p2, d2) = files
        if _looks_like_blorb(d1) and _looks_like_story(d2):
            (p1, d1), (p2, d2) = (p2, d2), (p1, d1)
        if not (_looks_like_story(d1) and _looks_like_blorb(d2)):
            raise SystemExit("proteus: with two inputs, pass one story file "
                             "and one Blorb")
        story_data = splice_zblorb(d1, d2)
        story_name = p1.stem + ".zblorb"
        pictures = "spliced with its pictures"
    else:
        path, data = files[0]
        if _looks_like_blorb(data):
            chunks = _parse_blorb(data)
            entries = _resource_entries(chunks[0][1])
            if not any(usage == b"Exec" for usage, _, _ in entries):
                raise SystemExit(
                    "proteus: this Blorb holds pictures but no story; pass "
                    "the story file with it")
            pictures = ("with pictures"
                        if any(u == b"Pict" for u, _, _ in entries)
                        else "no pictures")
        elif _looks_like_story(data):
            pictures = "text only"
        else:
            raise SystemExit(f"proteus: {path.name} is neither a Z-machine "
                             "story nor a Blorb")
        story_data = data
        story_name = path.name

    page = build_page(load_template(), story_data, story_name)
    out = Path(args.out)
    out.write_text(page, encoding="utf-8")
    print(f"proteus: wrote {out} ({out.stat().st_size} bytes, "
          f"{story_name}, {pictures})")
    print()  # a blank line between the output and the prompt
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
