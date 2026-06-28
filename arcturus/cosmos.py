# cosmos.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Loading and bundling the Cosmos standard library.

Cosmos is ordinary Arcturus source under cosmos/*.prelude, compiled together
with the author's game (docs/02 section 1). This module finds those sources and
combines their declarations with the game's into one program before semantic
analysis, so the game resolves against Cosmos and vice versa.

When running from the package, the sources are read from the cosmos/ directory.
The single-file `arcc` build embeds them instead and sets `_EMBEDDED`, so the
standalone compiler carries Cosmos with it.
"""

from __future__ import annotations

import os

from . import ast
from .parser import parse

# The Cosmos library version. It is independent of the compiler version: the
# bundled library can move ahead of (or behind) arcc, and since the embedded
# library is not visible on disk, the banner reports it alongside arcc's version.
COSMOS_VERSION = "0.1.0"

# Set by the amalgamated build to a dict of {filename: source}.
_EMBEDDED = None


def prelude_sources() -> dict:
    """Return {filename: source} for the bundled Cosmos prelude files, in a
    stable order."""
    if _EMBEDDED is not None:
        return dict(_EMBEDDED)
    # In the amalgamated build the module has no __file__; Cosmos is embedded
    # there via _EMBEDDED, so an absent file just means "no directory to read".
    module_file = globals().get("__file__")
    if module_file is None:
        return {}
    here = os.path.dirname(os.path.abspath(module_file))
    cosmos_dir = os.path.join(here, os.pardir, "cosmos")
    out: dict = {}
    if os.path.isdir(cosmos_dir):
        for name in sorted(os.listdir(cosmos_dir)):
            if name.endswith(".prelude"):
                with open(os.path.join(cosmos_dir, name), "r", encoding="utf-8") as fh:
                    out[name] = fh.read()
    return out


def combined_program(game: ast.Program) -> ast.Program:
    """Prepend the Cosmos declarations to the game's, yielding one program to
    analyze and compile. Cosmos blocks are tagged `library` so a game block of
    the same name overrides them (most-specific-wins)."""
    decls: list = []
    for name, src in prelude_sources().items():
        for d in parse(src, name).decls:
            if isinstance(d, ast.BlockDecl):
                d.origin = "library"
            decls.append(d)
    decls.extend(game.decls)
    return ast.Program(decls)
