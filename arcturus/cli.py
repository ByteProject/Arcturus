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

from . import __version__, build_id
from . import abbrev as abbrev_lib
from . import ast
from . import cosmos as cosmos_lib
from .astdump import dump
from .codegen import generate, harvest_strings
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


def _python() -> str:
    """The Python actually executing the tool (a bug report names the real
    environment, not the minimum requirement)."""
    return f"Python {platform.python_version()}"


def _banner() -> str:
    """The bare call: the one banner, then the usage lines. Composed from
    _header() so the two can never drift apart; there is no lean variant
    (Stefan's rule: the same banner everywhere, every time; only the
    updater wears its own dress)."""
    return (
        _header()
        + '\n'
        'This is the compiler for the Arcturus programming language. Type -h for help.\n'
        'Compiles to Infocom format, also called Z-machine story files.\n'
        '\n'
        'Usage: "arcc [options] <file.storyarc>"\n'
    )


class _ArcParser(argparse.ArgumentParser):
    """argparse, with the house banner on every mouth it speaks through:
    --help opens with the header (every arcc output shows the banner) and
    closes with one blank line (the house rule for every tool's output);
    a usage error carries the header on stderr the same way."""

    def print_help(self, file=None):
        out = file or sys.stdout
        print(_header(), file=out)
        super().print_help(out)
        print(file=out)

    def error(self, message):
        print(_header(), file=sys.stderr)
        super().error(message)


def _build_argparser() -> argparse.ArgumentParser:
    ap = _ArcParser(
        prog="arcc",
        description="Compile Arcturus (.storyarc) file to Z-machine format.",
    )
    ap.add_argument("source", nargs="?", help="the .storyarc story file")
    ap.add_argument(
        "-o", "--output", metavar="FILE", help="the story file to write"
    )
    ap.add_argument(
        "--zversion",
        type=int,
        choices=(5, 8),
        default=5,
        metavar="{5,8}",
        help="the Z-machine version to target: 5 (default) or 8. The generated "
        "code is identical; z8 raises the story-file size limit (512KB vs 256KB) "
        "for a large modern-only release. The story source does not change.",
    )
    ap.add_argument(
        "-L",
        "--lib",
        action="append",
        default=[],
        metavar="DIR",
        help="add an ABSOLUTE directory to the search path for granule (.granule) "
        "files a story summons by name; repeatable. Lets a project point at a "
        "forked or shared library rather than carry its own copy.",
    )
    ap.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="script mode: suppress the banner and the compile statistics, "
        "printing only the result line and any errors. Compiles are verbose by "
        "default: the banner always shows, and a successful compile prints the "
        "statistics ledger (what the story uses of each Z-machine ceiling).",
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
        "--eject-granule",
        metavar="NAME",
        help="write a single bundled granule (e.g. statusline) into the current "
        "directory for forking, then exit. Edit it and summon it by name.",
    )
    ap.add_argument(
        "--make-abbreviations",
        action="store_true",
        help="compute a tuned abbreviation set for the story (and the granules it "
        "summons) and write abbreviations.granule beside it, then exit. Summon that "
        "file to compress this story further than the built-in default.",
    )
    ap.add_argument(
        "--version", action=_VersionAction, nargs=0,
        help="show the version, the exact build, and the environment, then exit",
    )
    ap.add_argument(
        "--update", action=_UpdateAction, nargs=0,
        help="refresh this standalone (and actaea/arcimg beside it) to the "
        "latest published build, then exit. The ONLY command that touches "
        "the network; arcc never checks by itself.",
    )
    return ap


class _UpdateAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        from .updater import run_update
        parser.exit(run_update())


class _VersionAction(argparse.Action):
    """Print the version block verbatim. argparse's built-in `version` action
    runs the text through the help formatter, which reflows the lines into one
    wrapped paragraph; a plain print keeps the block as written."""

    def __call__(self, parser, namespace, values, option_string=None):
        # Trailing blank line so the shell prompt does not sit flush against
        # the block (the same courtesy the Actaea CLI keeps).
        print(_version_text() + "\n")
        parser.exit(0)


def _version_text() -> str:
    """The full identity block for `arcc --version`: the release, the exact
    build, the embedded library version, and the environment, so a bug report
    can name precisely what it ran. Distinct from the compile banner, which
    stays a lean per-build ledger."""
    return (
        f"Arcturus {__version__} (build {build_id()})\n"
        "Programming language and compiler for the Infocom Z-machine\n"
        f"Cosmos standard library {cosmos_lib.COSMOS_VERSION} "
        f"| {_python()} | {_host_os()}\n"
        "Copyright (c) 2026, Stefan Vogt "
        "| https://github.com/ByteProject/Arcturus"
    )


def _all_library_sources() -> dict:
    """Every bundled Cosmos source, preludes and granules together."""
    return {**cosmos_lib.prelude_sources(), **cosmos_lib.granule_sources()}


def _write_library_files(target_dir: str, names) -> int:
    sources = _all_library_sources()
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
    """Write the whole bundled Cosmos library to DIR for wholesale forking: every
    prelude AND every granule, so a project can point -L at it."""
    names = list(_all_library_sources())
    rc = _write_library_files(target_dir, names)
    if rc == 0:
        print(f"arcc: wrote {len(names)} Cosmos library files to {target_dir}/ "
              f"(compile against them with -L {target_dir})")
    return rc


def _eject_granule(name: str) -> int:
    """Write a single bundled granule into the current directory, for forking one
    feature next to a story. Accepts the bare name or the .granule filename."""
    fname = name if name.endswith(".granule") else name + ".granule"
    granules = cosmos_lib.granule_sources()
    if fname not in granules:
        avail = ", ".join(sorted(n[:-len(".granule")] for n in granules))
        print(f"arcc: error: no bundled granule '{name}' (have: {avail})",
              file=sys.stderr)
        return 2
    src = granules[fname]
    with open(fname, "w", encoding="utf-8") as fh:
        fh.write(src)
    # A language pack is selected with summon.language, not a plain summon, so its
    # notice must say so.
    code = cosmos_lib._language_marker(parse(src, fname).decls)
    if code is not None:
        stem = fname[: -len(".granule")]
        print(
            f'arcc: wrote {fname} (a language pack; edit it, then select it with '
            f'summon.language "{stem}")'
        )
    else:
        print(f"arcc: wrote {fname} (edit it, then summon it by name: summon {fname})")
    return 0


def _eject_language(target_dir: str) -> int:
    """Write just the English language file for message customization."""
    name = "english.prelude"
    rc = _write_library_files(target_dir, [name])
    if rc == 0:
        out = os.path.join(target_dir, name)
        print(f"arcc: wrote {out} (edit its msg_* blocks, then summon it or "
              f"compile with -L {target_dir})")
    return rc


def _is_abbrev_summon(d) -> bool:
    """True for a summon of the per-game abbreviations file, in any form."""
    return isinstance(d, ast.Summon) and (
        os.path.basename(d.target) == cosmos_lib._ABBREV_GRANULE
        or (d.form == "feature" and d.target == "abbreviations")
    )


def _make_abbreviations(args) -> int:
    """Compute a tuned abbreviation set for the story (and the granules it summons)
    and write abbreviations.granule beside it. The harvest deliberately drops any
    abbreviations summon first, so a first run does not fail on the not-yet-existing
    file and a regeneration ignores the stale set rather than compounding it."""
    try:
        with open(args.source, "r", encoding="utf-8") as fh:
            src = fh.read()
    except OSError as exc:
        print(f"arcc: error: cannot read {args.source}: {exc}", file=sys.stderr)
        # The classic slips: `arcc update` without the dashes, `arcc --
        # update` with a stray space (the bare -- ends option parsing),
        # and a pasted command whose -- was smart-substituted into an
        # en/em dash (macOS text fields do this), which argparse reads
        # as a positional. All strand "update" in the source slot;
        # point at the flag instead of leaving a bare ENOENT.
        if args.source.lstrip("-\u2013\u2014") == "update":
            print("arcc: did you mean `arcc --update`?", file=sys.stderr)
        return 2
    try:
        program = parse(src, args.source)
        program.decls = [d for d in program.decls if not _is_abbrev_summon(d)]
        story_dir = os.path.dirname(os.path.abspath(args.source))
        combined = cosmos_lib.combined_program(
            program, lib_dirs=args.lib or (), story_dir=story_dir
        )
        world = analyze(combined, filename=args.source)
        strings = harvest_strings(world)
    except ArcError as exc:
        print(exc.format(), file=sys.stderr)
        return 1
    abbrevs = abbrev_lib.compute(strings)
    out_path = os.path.join(story_dir, cosmos_lib._ABBREV_GRANULE)
    cosmos_lib.write_abbreviations_granule(
        out_path, abbrevs, os.path.basename(args.source)
    )
    print(
        f"arcc: wrote {out_path} ({len(abbrevs)} abbreviations); "
        f"summon it (summon {cosmos_lib._ABBREV_GRANULE}) to use it"
    )
    return 0


def _kinds_note(stats: dict) -> str:
    """The kind budget, shown beside the attribute count so the two are never
    confused: kinds are Arcturus sugar, effectively unlimited, riding the
    attribute slots the real attributes leave free (the fast test) and
    spilling to catalog membership scans beyond. Only genuine attributes are
    bounded by the 48 ceiling."""
    backed = stats.get("kinds_backed", 0)
    spilled = stats.get("kinds_spilled", 0)
    total = backed + spilled
    if not total:
        return ""
    if spilled:
        return f", kinds {total} ({spilled} spilled to catalogs)"
    return f", kinds {total}"


def _stats_report(stats: dict, version: int) -> str:
    """The compile-statistics ledger: what the story uses of each ceiling. Each
    line groups what an author watches together; a value with a hard Z-machine
    limit is shown as used/ceiling, an open-ended one as a plain count."""
    free = stats["story_max"] - stats["story_bytes"]
    return "\n".join([
        "compile statistics:",
        f"  world     {stats['objects']} objects in {stats['kinds']} kinds; "
        f"{stats['grains']} grains, {stats['topics']} topics, "
        f"{stats['timers']} timers",
        f"  tables    attributes {stats['attributes']}/{stats['attributes_max']}"
        + _kinds_note(stats)
        + f", properties {stats['properties']}/{stats['properties_max']}, "
        f"globals {stats['globals']}/{stats['globals_max']}",
        f"  grammar   {stats['verbs']} verbs, {stats['grammar_lines']} grammar "
        f"lines, {stats['actions']} actions; {stats['dict_words']} dictionary "
        f"words",
        f"  scoring   {stats.get('award_sites', 0)} award sites, "
        f"{stats.get('award_pools', 0)} pools, {stats.get('scored_auto', 0)} "
        f"auto-scored; max_score {stats.get('max_score', 0)}"
        + (f", {stats.get('ranks', 0)} ranks" if stats.get('ranks') else ""),
        f"  text      abbreviations {stats['abbrevs']}/{stats['abbrevs_max']}; "
        f"{stats['string_bytes']} bytes of packed strings",
        f"  code      {stats['routines']} routines, {stats['code_bytes']} bytes "
        f"of z-code (inline text included)",
        f"  memory    {stats['readable_bytes']}/{stats['readable_max']} bytes "
        f"readable"
        + (f"; {stats['matrices']} matrices, {stats['matrix_bytes']} dynamic bytes"
           if stats.get('matrices') else ""),
        f"  story     {stats['story_bytes']}/{stats['story_max']} bytes "
        f"(z{version}); {free} free",
    ])


def _header() -> str:
    """THE banner, the same on every invocation, before any result: what is
    speaking, in which versions, in which environment, whose it is, and
    where it lives. The bare call adds usage lines after it; the updater
    alone wears its own header."""
    return (
        f'Arcturus -- [ arcc {__version__} | Cosmos {cosmos_lib.COSMOS_VERSION} '
        f'| {_python()} | {_host_os()} ]\n'
        'Programming language and compiler for the Infocom Z-machine\n'
        'Copyright (c) 2026, Stefan Vogt '
        '| https://github.com/ByteProject/Arcturus\n'
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = _build_argparser()
    args = ap.parse_args(argv)

    # The bare call: no story, no utility flag. It gets the full banner (which
    # carries the header inside it) and nothing else; printing the header
    # first as well showed the version block twice (fixed 2026-07-04).
    utility = (
        args.extract_library is not None
        or args.eject_language is not None
        or args.eject_granule is not None
    )
    if not args.source and not utility:
        if not getattr(args, "quiet", False):
            print(_banner(), file=sys.stderr)
        return 2

    if not getattr(args, "quiet", False):
        print(_header())

    # Library-extraction utilities run without a story file. Each success
    # closes with the house blank line.
    if args.extract_library is not None:
        rc = _extract_library(args.extract_library)
        if rc == 0:
            print()
        return rc
    if args.eject_language is not None:
        rc = _eject_language(args.eject_language)
        if rc == 0:
            print()
        return rc
    if args.eject_granule is not None:
        rc = _eject_granule(args.eject_granule)
        if rc == 0:
            print()
        return rc

    # -L directories must be absolute, so the library is deliberately placed and
    # there is no ambiguity about what a story summons by name (docs/05).
    for d in args.lib or ():
        if not os.path.isabs(d):
            print(f"arcc: error: -L path must be absolute: {d}", file=sys.stderr)
            return 2

    if args.make_abbreviations:
        return _make_abbreviations(args)

    try:
        with open(args.source, "r", encoding="utf-8") as fh:
            src = fh.read()
    except OSError as exc:
        print(f"arcc: error: cannot read {args.source}: {exc}", file=sys.stderr)
        # The classic slips: `arcc update` without the dashes, `arcc --
        # update` with a stray space (the bare -- ends option parsing),
        # and a pasted command whose -- was smart-substituted into an
        # en/em dash (macOS text fields do this), which argparse reads
        # as a positional. All strand "update" in the source slot;
        # point at the flag instead of leaving a bare ENOENT.
        if args.source.lstrip("-\u2013\u2014") == "update":
            print("arcc: did you mean `arcc --update`?", file=sys.stderr)
        return 2

    try:
        program = parse(src, args.source)
    except ArcError as exc:
        print(exc.format(), file=sys.stderr)
        return 1

    if args.dump_ast:
        print(dump(program))
        return 0

    # Compile the game together with the bundled Cosmos library and any granules
    # it summons (docs/02). Summoned files resolve relative to the story's own
    # directory first, then the -L search path.
    if not args.no_cosmos:
        story_dir = os.path.dirname(os.path.abspath(args.source))
        program = cosmos_lib.combined_program(
            program, lib_dirs=args.lib or (), story_dir=story_dir
        )

    try:
        world = analyze(program, filename=args.source)
    except ArcError as exc:
        print(exc.format(), file=sys.stderr)
        return 1

    if args.dump_ir:
        print(dump_ir(world))
        return 0

    if args.output:
        # Compiles are verbose by default: the statistics ledger prints after
        # every successful build (Stefan's rule: the switch is for suppressing
        # it, not requesting it). -q silences both the ledger and the banner.
        stats = None if args.quiet else {}
        try:
            story = generate(world, version=args.zversion, stats=stats)
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
        # arc_image (B11): pictures need no compiler sidecar. The id in each room's
        # arc_image slot IS the resource number, so an aware interpreter loads
        # <id>.png straight from the images directory (or the .arcres pack that
        # `arcimg` builds). Nothing extra is written beside the story.
        if stats is not None:
            print(_stats_report(stats, args.zversion))
            # One blank line after the output, the house rule for every tool
            # (-q is script mode and stays bare for pipelines).
            print()
        return 0

    objects = len(world.objects)
    print(f"{args.source}: parsed and checked cleanly ({objects} objects)")
    if not args.quiet:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
