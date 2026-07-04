# __main__.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The console entry: `python3 -m actaea <story>`. Today (M1) it loads and
validates a story file and reports its header; as the milestones land it
grows into the headless runner that drives CZECH and Praxix (the M6 gate)
and, from M7, hands off to the tkinter front-end unless asked to stay on
the console."""

import argparse
import sys

from . import __version__
from .errors import ActaeaError
from .loader import load_file


def _report(story) -> str:
    h = story.header
    lines = [
        f"version   z{h.version} (packed addresses x{story.memory.scale})",
        f"release   {h.release} / serial {h.serial}",
        f"length    {h.file_length} bytes",
        f"checksum  {h.checksum:#06x} "
        + ("(verified)" if story.checksum_ok() else "(MISMATCH)"),
        f"start     {h.initial_pc:#06x} (initial program counter)",
        f"memory    dynamic below {h.static_base:#06x}, "
        f"high from {h.high_base:#06x}",
        f"tables    dictionary {h.dictionary:#06x}, objects {h.objects:#06x}, "
        f"globals {h.globals_:#06x}, abbreviations {h.abbreviations:#06x}",
    ]
    extras = []
    if h.alphabet:
        extras.append(f"alphabet {h.alphabet:#06x}")
    if h.terminating:
        extras.append(f"terminating chars {h.terminating:#06x}")
    if h.header_ext:
        extras.append(f"header extension {h.header_ext:#06x}")
    if extras:
        lines.append("extras    " + ", ".join(extras))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="actaea",
        description="Actaea, the Arcturus reference Z-machine interpreter "
        "(versions 5 and 8).",
    )
    ap.add_argument("story", help="a .z5 or .z8 story file")
    ap.add_argument(
        "--header",
        action="store_true",
        help="load and validate the story, print its header, and exit",
    )
    ap.add_argument("--version", action="version", version=f"actaea {__version__}")
    args = ap.parse_args(argv)

    try:
        story = load_file(args.story)
    except OSError as e:
        print(f"actaea: {e}", file=sys.stderr)
        return 2
    except ActaeaError as e:
        print(f"actaea: {e}", file=sys.stderr)
        return 2

    print(_report(story))
    if not args.header:
        # The run loop arrives with M3; until then --header is the only mode.
        print("\n(actaea M1: loading and validation only; no execution yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
