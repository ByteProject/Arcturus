"""The arcturus / arcc command-line interface.

For the current milestones the CLI parses a .storyarc source file and reports
success or a precise diagnostic. Code generation to a z5 story file (the -o
option) arrives in a later milestone.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .astdump import dump
from .errors import ArcError
from .parser import parse


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(
        prog="arcc",
        description="Compile Arcturus (.storyarc) interactive fiction.",
    )
    ap.add_argument("source", nargs="?", help="the .storyarc source file")
    ap.add_argument(
        "-o", "--output", metavar="FILE", help="the z5 story file to write"
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="parse and report only, without generating code",
    )
    ap.add_argument(
        "--dump-ast",
        action="store_true",
        help="print the parsed abstract syntax tree",
    )
    ap.add_argument(
        "--version", action="version", version=f"Arcturus {__version__}"
    )
    args = ap.parse_args(argv)

    if not args.source:
        ap.print_usage(sys.stderr)
        print("arcc: error: no source file given", file=sys.stderr)
        return 2

    try:
        with open(args.source, "r", encoding="utf-8") as fh:
            src = fh.read()
    except OSError as exc:
        print(f"arcc: error: cannot read {args.source}: {exc}", file=sys.stderr)
        return 2

    try:
        program = parse(src, args.source)
    except ArcError as exc:
        print(exc.format(), file=sys.stderr)
        return 1

    if args.dump_ast:
        print(dump(program))
        return 0

    if args.output:
        print(
            "arcc: error: code generation is not implemented yet "
            "(this milestone parses only)",
            file=sys.stderr,
        )
        return 2

    decls = len(program.decls)
    print(f"{args.source}: parsed cleanly ({decls} top-level declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
