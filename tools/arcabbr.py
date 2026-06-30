#!/usr/bin/env python3
# arcabbr.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Regenerate the baked-in default abbreviation set (arcturus/abbrev.py).

Compiles tools/corpus.storyarc (a representative standard-library story, NOT a
game), harvests every string the compiler would encode into it, runs the
abbreviation optimizer over that pool, and rewrites the DEFAULT_ABBREVS literal
in arcturus/abbrev.py. The corpus is standard-library only and written in plain
house-voice prose, so the chosen abbreviations are the ones common to most games
(the stock phrasings of description plus the always-present library messages),
which is what a default should compress without wasting slots on any one game's
private vocabulary. The slow, per-game route is the compiler's
--make-abbreviations pass; this tool only feeds the fast default.

    python3 tools/arcabbr.py            # rewrite arcturus/abbrev.py in place
    python3 tools/arcabbr.py --print    # print the set without writing
"""

from __future__ import annotations

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from arcturus import abbrev, cosmos, zstring  # noqa: E402
from arcturus.codegen import generate  # noqa: E402
from arcturus.parser import parse  # noqa: E402
from arcturus.sema import analyze  # noqa: E402

_CORPUS = os.path.join(_HERE, "corpus.storyarc")
_ABBREV_PY = os.path.join(_ROOT, "arcturus", "abbrev.py")


def harvest(path: str) -> list[str]:
    """Every string the compiler encodes into the corpus story, minus the banner
    (its title/author/serial are story-specific, not library text)."""
    src = open(path, "r", encoding="utf-8").read()
    program = cosmos.combined_program(parse(src, path), story_dir=os.path.dirname(path))
    world = analyze(program, filename=path)
    # Compile with the default OFF so the harvest is the raw program text, not the
    # abbreviation strings themselves.
    saved = abbrev.DEFAULT_ABBREVS
    abbrev.DEFAULT_ABBREVS = []
    zstring.begin_harvest()
    try:
        generate(world)
    finally:
        strings = zstring.end_harvest()
        abbrev.DEFAULT_ABBREVS = saved
    return [s for s in strings if "Serial number" not in s]


def render(abbrevs: list[str]) -> str:
    lines = ["DEFAULT_ABBREVS: list[str] = ["]
    for s in abbrevs:
        lines.append(f"    {s!r},")
    lines.append("]")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    strings = harvest(_CORPUS)
    abbrevs = abbrev.compute(strings)
    sys.stderr.write(
        f"corpus: {len(strings)} strings, {sum(len(s) for s in strings)} chars "
        f"-> {len(abbrevs)} abbreviations\n"
    )
    block = render(abbrevs)
    if "--print" in argv:
        print(block)
        return 0
    src = open(_ABBREV_PY, "r", encoding="utf-8").read()
    new = re.sub(
        r"DEFAULT_ABBREVS: list\[str\] = \[.*?\n\]",
        block,
        src,
        count=1,
        flags=re.DOTALL,
    )
    if new == src:
        sys.stderr.write("error: could not find DEFAULT_ABBREVS to replace\n")
        return 1
    open(_ABBREV_PY, "w", encoding="utf-8").write(new)
    sys.stderr.write(f"rewrote {os.path.relpath(_ABBREV_PY, _ROOT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
