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
import os
import platform
import sys

from . import __version__
from . import cosmos as cosmos_lib
from .astdump import dump
from .codegen import generate
from .errors import ArcError
from .irdump import dump as dump_ir
from .parser import parse
from .sema import analyze

def _host_os() -> str:
    """A short label for the host operating system, for the banner tag line:
    MacOS ARM, Linux64, Windows, and so on."""
    name = platform.system()
    machine = (platform.machine() or "").lower()
    if name == "Darwin":
        return "MacOS ARM" if machine in ("arm64", "aarch64") else "MacOS x86"
    if name == "Linux":
        return "Linux64" if machine in ("x86_64", "aarch64", "arm64") else "Linux32"
    if name == "Windows":
        return "Windows"
    return name or "unknown"


def _banner() -> str:
    return (
        f'Arcturus -- [ arcc {__version__} | Cosmos {cosmos_lib.COSMOS_VERSION} '
        f'| python3 | stdlib | {_host_os()} ]\n'
        'Copyright (c) 2026, Stefan Vogt.\n'
        'https://github.com/ByteProject/Arcturus\n'
        '\n'
        'This is the compiler for the Arcturus programming language. Type -h for help.\n'
        'Compiles to Infocom format, also called Z-machine story files.\n'
        '\n'
        'Usage: "arcc [options] <file.storyarc>"\n'
    )


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
        "--dump-ir",
        action="store_true",
        help="print the analyzed world-model IR",
    )
    ap.add_argument(
        "--no-cosmos",
        action="store_true",
        help="compile the game alone, without the bundled Cosmos library",
    )
    ap.add_argument(
        "--extract-library",
        metavar="DIR",
        help="write the bundled Cosmos library (.prelude/.granule) into DIR for "
        "editing, then exit. Fork it wholesale and compile against it with -L DIR.",
    )
    ap.add_argument(
        "--eject-language",
        nargs="?",
        const=".",
        metavar="DIR",
        help="write the English language file (english.prelude) into DIR (default: "
        "the current directory) for message customization, then exit.",
    )
    ap.add_argument(
        "--version", action="version", version=f"Arcturus {__version__}"
    )
    return ap


def _write_library_files(target_dir: str, names) -> int:
    sources = cosmos_lib.prelude_sources()
    if not sources:
        print("arcc: error: no bundled Cosmos library to write", file=sys.stderr)
        return 2
    missing = [n for n in names if n not in sources]
    if missing:
        print(f"arcc: error: not in the bundled library: {', '.join(missing)}",
              file=sys.stderr)
        return 2
    os.makedirs(target_dir, exist_ok=True)
    for name in names:
        with open(os.path.join(target_dir, name), "w", encoding="utf-8") as fh:
            fh.write(sources[name])
    return 0


def _extract_library(target_dir: str) -> int:
    """Write the whole bundled Cosmos library to DIR for wholesale forking."""
    names = list(cosmos_lib.prelude_sources())
    rc = _write_library_files(target_dir, names)
    if rc == 0:
        print(f"arcc: wrote {len(names)} Cosmos library files to {target_dir}/ "
              f"(compile against them with -L {target_dir})")
    return rc


def _eject_language(target_dir: str) -> int:
    """Write just the English language file for message customization."""
    name = "english.prelude"
    rc = _write_library_files(target_dir, [name])
    if rc == 0:
        out = os.path.join(target_dir, name)
        print(f"arcc: wrote {out} (edit its msg_* blocks, then summon it or "
              f"compile with -L {target_dir})")
    return rc


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = _build_argparser()
    args = ap.parse_args(argv)

    # Library-extraction utilities run without a story file.
    if args.extract_library is not None:
        return _extract_library(args.extract_library)
    if args.eject_language is not None:
        return _eject_language(args.eject_language)

    if not args.source:
        print(_banner(), file=sys.stderr)
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

    # Compile the game together with the bundled Cosmos library (docs/02).
    if not args.no_cosmos:
        program = cosmos_lib.combined_program(program)

    try:
        world = analyze(program, filename=args.source)
    except ArcError as exc:
        print(exc.format(), file=sys.stderr)
        return 1

    if args.dump_ir:
        print(dump_ir(world))
        return 0

    if args.output:
        try:
            story = generate(world)
        except ArcError as exc:
            print(exc.format(), file=sys.stderr)
            return 1
        try:
            with open(args.output, "wb") as fh:
                fh.write(story)
        except OSError as exc:
            print(f"arcc: error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"{args.source}: wrote {args.output} ({len(story)} bytes)")
        return 0

    objects = len(world.objects)
    print(f"{args.source}: parsed and checked cleanly ({objects} objects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
