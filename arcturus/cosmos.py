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
import sys

from . import ast
from .errors import ArcError
from .parser import parse

# Dotted features that the loader does not resolve to a plain runtime granule:
# `language` selects a translation pack (milestone B7) and `abbreviations` is
# consumed by the compiler's text encoder, not compiled as runtime blocks (B6).
# They parse and are recognized here, but loading them is handled elsewhere.
_NON_GRANULE_FEATURES = {"language", "abbreviations"}

# The Cosmos library version. It is independent of the compiler version: the
# bundled library can move ahead of (or behind) arcc, and since the embedded
# library is not visible on disk, the banner reports it alongside arcc's version.
COSMOS_VERSION = "0.1.0"

# Set by the amalgamated build to a dict of {filename: source}.
_EMBEDDED = None


def _bundled_sources(suffix: str) -> dict:
    """Return {filename: source} for the bundled Cosmos files with the given
    suffix (".prelude" or ".granule"), in a stable order. The amalgamated build
    embeds them via _EMBEDDED; the package build reads cosmos/ from disk."""
    if _EMBEDDED is not None:
        return {n: s for n, s in _EMBEDDED.items() if n.endswith(suffix)}
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
            if name.endswith(suffix):
                with open(os.path.join(cosmos_dir, name), "r", encoding="utf-8") as fh:
                    out[name] = fh.read()
    return out


def prelude_sources() -> dict:
    """Return {filename: source} for the bundled Cosmos prelude files."""
    return _bundled_sources(".prelude")


def granule_sources() -> dict:
    """Return {filename: source} for the bundled Cosmos granule files (the
    official summonable features that ship inside arcc)."""
    return _bundled_sources(".granule")


def _summons(program: ast.Program) -> list:
    return [d for d in program.decls if isinstance(d, ast.Summon)]


def _read_granule(path):
    with open(path, "r", encoding="utf-8") as fh:
        return "file:" + os.path.abspath(path), fh.read(), os.path.basename(path)


def _resolve_summon(s: ast.Summon, bundled: dict, lib_dirs, story_dir):
    """Resolve one summon to (key, source, srcname), or (None, None, None) for a
    feature the loader does not compile as runtime blocks (language,
    abbreviations). The three forms (docs/05):
      feature  summon.statusline         - the bundled copy, always.
      name     summon statusline.granule - story dir, then each -L dir, then the
               bundled copy (with a notice when it falls back), else an error.
      path     summon "x.granule"        - an explicit file (absolute, or for a
               bare name the story dir then the cwd); no bundled fallback.
    Raises ArcError on a missing file or unknown feature."""
    if s.form == "feature":
        if s.target in _NON_GRANULE_FEATURES:
            return None, None, None
        fname = s.target + ".granule"
        if fname in bundled:
            return "feature:" + fname, bundled[fname], fname
        raise ArcError(
            f"summon: unknown built-in feature '{s.target}'", s.line,
            filename="<summon>",
        )

    if s.form == "name":
        fname = s.target  # e.g. "statusline.granule"
        roots = ([story_dir] if story_dir else []) + list(lib_dirs)
        for root in roots:
            path = os.path.join(root, fname)
            if os.path.isfile(path):
                return _read_granule(path)
        if fname in bundled:
            # Found nothing local; fall back to the bundled copy, and say so, so
            # the author knows their fork was not picked up.
            print(
                f"arcc: note: '{fname}' not found in the story directory or any "
                f"-L directory; using the bundled granule",
                file=sys.stderr,
            )
            return "feature:" + fname, bundled[fname], fname
        raise ArcError(
            f"summon: cannot find granule '{fname}' (not local, no -L copy, and "
            f"no bundled granule by that name)", s.line, filename="<summon>",
        )

    # form == "path": an explicit quoted file, no bundled fallback.
    rel = s.target
    if os.path.isabs(rel) or os.path.dirname(rel):
        # An absolute path, or a relative path with directories: as written.
        candidates = [rel]
    else:
        # A bare filename: the story directory, then the cwd.
        candidates = ([os.path.join(story_dir, rel)] if story_dir else []) + [rel]
    for path in candidates:
        if os.path.isfile(path):
            return _read_granule(path)
    raise ArcError(f"summon: cannot find granule '{rel}'", s.line, filename="<summon>")


def _load_granules(game: ast.Program, lib_dirs, story_dir) -> list:
    """Resolve and parse every granule the game summons (transitively, since a
    granule may summon another), each loaded once. Granule blocks are tagged
    `granule` so they override a library block but yield to the game
    (most-specific-wins). Unsummoned granules are never read, so they never ship."""
    bundled = granule_sources()
    loaded: dict = {}
    order: list = []
    worklist = _summons(game)
    while worklist:
        s = worklist.pop(0)
        key, src, srcname = _resolve_summon(s, bundled, lib_dirs, story_dir)
        if key is None or key in loaded:
            continue
        prog = parse(src, srcname)
        gdecls: list = []
        for d in prog.decls:
            if isinstance(d, ast.BlockDecl):
                d.origin = "granule"
            gdecls.append(d)
        loaded[key] = gdecls
        order.append(key)
        worklist.extend(_summons(prog))  # a granule may summon further granules
    out: list = []
    for key in order:
        out.extend(loaded[key])
    return out


def combined_program(game: ast.Program, lib_dirs=(), story_dir=None) -> ast.Program:
    """Combine the Cosmos library, any summoned granules, and the game into one
    program to analyze and compile. Order encodes precedence: library first
    (tagged `library`), then granules (tagged `granule`), then the game, so a
    game block overrides a granule block overrides a library block of the same
    name (most-specific-wins). lib_dirs and story_dir locate file summons."""
    decls: list = []
    for name, src in prelude_sources().items():
        for d in parse(src, name).decls:
            if isinstance(d, ast.BlockDecl):
                d.origin = "library"
            decls.append(d)
    decls.extend(_load_granules(game, lib_dirs, story_dir))
    decls.extend(game.decls)
    return ast.Program(decls)
