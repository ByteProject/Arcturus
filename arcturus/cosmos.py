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
# `language` selects a translation pack (milestone B7), handled elsewhere. The
# tuned abbreviation set is NOT a dotted feature: the standard set is always
# applied, and a story overrides it by summoning its own abbreviations.granule by
# name (summon abbreviations.granule), a per-game file in the story directory that
# the loader intercepts as data, not runtime blocks (B6, _ABBREV_GRANULE below).
_NON_GRANULE_FEATURES = {"language"}

# The language layer: English is the default and lives in english.prelude (always
# loaded). Every other language is a granule, `<code>.granule`, compiled in place
# of english.prelude when `summon.language "<code>"` selects it. So a plain game is
# English and pays nothing for the alternates, and a language pack is forked and
# shared exactly like any other granule.
_DEFAULT_LANGUAGE = "english"

# The Cosmos library version. It is independent of the compiler version: the
# bundled library can move ahead of (or behind) arcc, and since the embedded
# library is not visible on disk, the banner reports it alongside arcc's version.
COSMOS_VERSION = "0.14.3"

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


# The per-game abbreviation file (B6): summoned like a granule, but its content is
# compile-time data for the text encoder, not runtime blocks.
_ABBREV_GRANULE = "abbreviations.granule"


def _summons(program: ast.Program) -> list:
    return [d for d in program.decls if isinstance(d, ast.Summon)]


def _language_marker(decls) -> str:
    """The code from a `language "..."` marker in these declarations, or None. A
    language pack self-identifies with it; the loader uses it to require selection
    through summon.language and to reject a plain summon of a language granule."""
    for d in decls:
        if isinstance(d, ast.LanguageDecl):
            return d.code
    return None


def _language_choice(game: ast.Program) -> str:
    """The language a game selects with `summon.language "spanish"`, or the default.
    Only the game may select it (not a granule), and only once."""
    chosen = None
    for s in _summons(game):
        if s.form == "feature" and s.target == "language":
            if s.arg is None:
                raise ArcError(
                    'summon.language needs a language, e.g. summon.language "spanish"',
                    s.line, filename="<summon>",
                )
            code = s.arg.lower()
            if chosen is not None and chosen != code:
                raise ArcError(
                    "a game may summon only one language", s.line, filename="<summon>"
                )
            chosen = code
    return chosen or _DEFAULT_LANGUAGE


def _resolve_language(language: str, lib_dirs, story_dir):
    """Find a language pack's granule, `<language>.granule`, and return (source,
    srcname). Resolved like a summoned granule: the story directory, then each -L
    directory, then the bundled copy, so a fork is picked up over the built-in
    one. Raises ArcError when no such language is available."""
    fname = language + ".granule"
    roots = ([story_dir] if story_dir else []) + list(lib_dirs)
    for root in roots:
        path = os.path.join(root, fname)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read(), os.path.abspath(path)
    bundled = granule_sources()
    if fname in bundled:
        return bundled[fname], fname
    raise ArcError(
        f"summon.language: no language '{language}' (looked for {fname} in the "
        f"story directory, the -L directories, and the bundled granules)",
        filename="<summon>",
    )


def extract_abbreviations(src: str, srcname: str) -> list:
    """The abbreviation strings a generated abbreviations.granule carries, in order
    (B6). The file is not compiled as runtime blocks, only lexed: every plain
    string literal in it is one abbreviation, in the order the table uses."""
    from .lexer import tokenize
    from . import tokens as T

    out: list = []
    for tok in tokenize(src, srcname):
        if tok.kind != T.STRING:
            continue
        parts = tok.value
        if len(parts) == 1 and isinstance(parts[0], ast.StringText):
            out.append(parts[0].text)
        elif parts:  # interpolation or multiple parts: not a plain abbreviation
            raise ArcError(
                "abbreviations.granule may only hold plain string literals",
                tok.line, filename=srcname,
            )
    return out


def _quote(s: str) -> str:
    """Write `s` as an Arcturus string literal the lexer reads back unchanged: the
    escapes it knows (\" \\ \\$ \\n), and nothing else, so leading and trailing
    single spaces survive (the lexer only collapses runs of whitespace)."""
    out = ['"']
    for ch in s:
        if ch == '"' or ch == "\\":
            out.append("\\" + ch)
        elif ch == "$":
            out.append("\\$")
        elif ch == "\n":
            out.append("\\n")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _round_trips(s: str) -> bool:
    """True if `s` survives being written as a literal and lexed back. The lexer
    collapses a run of two or more whitespace characters to one space, so an
    abbreviation containing such a run cannot be stored faithfully and is dropped."""
    return extract_abbreviations(_quote(s), "<check>") == [s]


def write_abbreviations_granule(path: str, abbrevs: list, story_name: str) -> None:
    """Write a tuned abbreviation set (B6) as an abbreviations.granule the story can
    summon. It is Arcturus-lexable string data, not runtime code, so it highlights
    like any source and the loader reads it with extract_abbreviations(). Any
    abbreviation that could not be stored faithfully (a whitespace run the lexer
    would collapse) is dropped, so the file always reads back exactly as written."""
    abbrevs = [s for s in abbrevs if _round_trips(s)]
    lines = [
        "// abbreviations.granule",
        "// A tuned abbreviation set for this story's text, generated by",
        f"//   arcc --make-abbreviations {story_name}",
        "// Summon it (summon abbreviations.granule) to compress this story with its",
        "// own set instead of the built-in default; regenerate after large text",
        "// changes. Compile-time data for the text encoder, not runtime code.",
        "",
        "abbreviations",
    ]
    lines.extend("    " + _quote(s) for s in abbrevs)
    lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


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
        if s.target == "abbreviations":
            raise ArcError(
                "summon: the abbreviation set is not a dotted feature. The standard "
                "set is always applied; for a tuned set run `arcc "
                "--make-abbreviations` and summon the file it writes beside the "
                "story: summon abbreviations.granule",
                s.line, filename="<summon>",
            )
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


def _load_granules(game: ast.Program, lib_dirs, story_dir):
    """Resolve and parse every granule the game summons (transitively, since a
    granule may summon another), each loaded once. Granule blocks are tagged
    `granule` so they override a library block but yield to the game
    (most-specific-wins). Unsummoned granules are never read, so they never ship.
    A summoned abbreviations.granule is not compiled to blocks; its strings are
    extracted and returned separately. Returns (declarations, abbreviations)."""
    bundled = granule_sources()
    loaded: dict = {}
    order: list = []
    abbreviations: list = None
    worklist = _summons(game)
    while worklist:
        s = worklist.pop(0)
        key, src, srcname = _resolve_summon(s, bundled, lib_dirs, story_dir)
        if key is None or key in loaded:
            continue
        if srcname == _ABBREV_GRANULE:
            loaded[key] = []  # mark seen; its content is data, not runtime blocks
            abbreviations = extract_abbreviations(src, srcname)
            continue
        prog = parse(src, srcname)
        # A language pack must be selected with summon.language (which replaces
        # english.prelude); a plain summon would leave English baked in, so reject
        # it with a clear pointer rather than build a broken bilingual story.
        if _language_marker(prog.decls) is not None:
            # summon.language resolves by filename, so point at the file's stem, not
            # the marker code (a fork may keep the original marker).
            stem = srcname[:-len(".granule")] if srcname.endswith(".granule") else srcname
            raise ArcError(
                f"summon: '{srcname}' is a language pack; select it with "
                f'summon.language "{stem}", not a plain summon',
                s.line, filename="<summon>",
            )
        gdecls: list = []
        for d in prog.decls:
            if isinstance(d, (ast.BlockDecl, ast.Handler)):
                d.origin = "granule"
            gdecls.append(d)
        loaded[key] = gdecls
        order.append(key)
        worklist.extend(_summons(prog))  # a granule may summon further granules
    # The two conversation presentations are views of the same topic model
    # and are mutually exclusive by design: an author settles on one. Match
    # by filename so a local fork of either still counts as that presentation.
    stems = {os.path.basename(k.split(":", 1)[-1]) for k in loaded}
    if "conversations.granule" in stems and "infocom_talking.granule" in stems:
        raise ArcError(
            "summon: conversations and infocom_talking are two presentations "
            "of the same topic model; a game picks exactly one",
            0, filename="<summon>",
        )
    out: list = []
    for key in order:
        out.extend(loaded[key])
    return out, abbreviations


def combined_program(game: ast.Program, lib_dirs=(), story_dir=None) -> ast.Program:
    """Combine the Cosmos library, any summoned granules, and the game into one
    program to analyze and compile. Order encodes precedence: library first
    (tagged `library`), then granules (tagged `granule`), then the game, so a
    game block overrides a granule block overrides a library block of the same
    name (most-specific-wins). lib_dirs and story_dir locate file summons."""
    language = _language_choice(game)
    default_prelude = _DEFAULT_LANGUAGE + ".prelude"
    decls: list = []
    for name, src in prelude_sources().items():
        # The default language layer (english.prelude) is dropped when another
        # language replaces it; the rest of the preludes are agnostic and always
        # load.
        if language != _DEFAULT_LANGUAGE and name == default_prelude:
            continue
        for d in parse(src, name).decls:
            if isinstance(d, (ast.BlockDecl, ast.Handler)):
                d.origin = "library"
            decls.append(d)
    # A non-default language is a granule, <language>.granule, resolved like any
    # granule (the story directory, then each -L directory, then the bundled copy)
    # and compiled in place of english.prelude as the base language layer.
    if language != _DEFAULT_LANGUAGE:
        src, srcname = _resolve_language(language, lib_dirs, story_dir)
        lang_decls = parse(src, srcname).decls
        # A granule chosen with summon.language must be a language pack (carry the
        # `language` marker), so a plain granule is not mistaken for one.
        if _language_marker(lang_decls) is None:
            raise ArcError(
                f"summon.language: '{srcname}' is not a language pack (it has no "
                f'`language "..."` marker)', filename="<summon>",
            )
        for d in lang_decls:
            # The marker is a loader directive, not a runtime declaration; drop it
            # so semantic analysis never sees it.
            if isinstance(d, ast.LanguageDecl):
                continue
            if isinstance(d, ast.BlockDecl):
                d.origin = "library"
            decls.append(d)
    gdecls, abbreviations = _load_granules(game, lib_dirs, story_dir)
    decls.extend(gdecls)
    decls.extend(game.decls)
    return ast.Program(decls, abbreviations=abbreviations)
