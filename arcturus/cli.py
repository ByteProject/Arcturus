# cli.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The arcc command-line interface.

For the current milestones the CLI parses a story file and reports success or a
precise diagnostic. Code generation to a Z-machine story file (the -o option)
arrives in a later milestone.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .astdump import dump
from .errors import ArcError
from .parser import parse

_BANNER = f'''Arcturus {__version__}

This program is a compiler of Infocom format (also called "Z-machine") story
files. It is written in Python and needs only the standard library.
Copyright (c) 2026, Stefan Vogt.

Usage: "arcc [options] <file.storyarc>"'''


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="arcc",
        description="Compile Arcturus (.storyarc) file to Z-machine format.",
    )
    ap.add_argument("source", nargs="?", help="the .storyarc story file")
    ap.add_argument(
        "-o", "--output", metavar="FILE", help="the story file to write"
    )
    ap.add_argument(
        "-L",
        "--lib",
        action="append",
        default=[],
        metavar="DIR",
        help="add a directory to the search path for Cosmos prelude (.prelude) "
        "and extension (.granule) files; repeatable. Lets a project summon the "
        "shared library rather than carry its own copy.",
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
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = _build_argparser()
    args = ap.parse_args(argv)

    if not args.source:
        print(_BANNER, file=sys.stderr)
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
