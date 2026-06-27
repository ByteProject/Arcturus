# codegen.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Code generation for the version 5 backend (milestone B3).

This is the minimum viable backend: it emits a valid z5 story file that prints
the banner, runs the `on start` handler's `say` lines, and quits. There are no
routine calls, no objects in the tree yet, and no expressions; the main code is
one straight-line instruction stream at the initial program counter.

The object table, dictionary, and turn loop arrive with Cosmos (B4). The
construct-to-opcode mapping is recorded in docs/04-codegen-mapping.md.
"""

from __future__ import annotations

import datetime

from . import __version__
from . import ast
from . import storyfile
from . import worldmodel as wm
from . import zstring
from .errors import ArcError

# 0OP opcodes used here (Z-machine standard 1.1, section 14).
OP_PRINT = 0xB2  # print the inline literal Z-string that follows
OP_NEW_LINE = 0xBB
OP_QUIT = 0xBA

# Region sizes.
_GLOBALS_BYTES = 240 * 2  # 240 globals
_PROP_DEFAULTS_BYTES = 63 * 2  # property defaults table (v4+: 63 words)
_ABBREV_BYTES = 96 * 2  # 96 abbreviation entries, empty for now


class CodegenError(ArcError):
    pass


def _meta(world: wm.World) -> dict:
    out: dict = {}
    if world.game is not None:
        for m in world.game.meta:
            out[m.key] = m.value
    return out


def _compiler_version() -> str:
    return ".".join(__version__.split(".")[:2])


def banner_text(world: wm.World) -> str:
    """The startup banner (docs/02 section 3). B3 emits it from the compiler as
    a provisional stand-in; Cosmos owns the banner from B4, where the library
    contributes its own name and version."""
    m = _meta(world)
    title = m.get("title", "Untitled")
    headline = m.get("headline", "An Interactive Fiction")
    author = m.get("author", "Anonymous")
    release = m.get("release", 1)
    serial = m.get("serial") or datetime.date.today().strftime("%y%m%d")
    line2 = f"{headline} by {author}"
    line3 = f"Release {release} / Serial number {serial} / Arcturus {_compiler_version()}"
    return f"\n{title}\n{line2}\n{line3}\n\n"


def _print(text: str) -> bytes:
    return bytes([OP_PRINT]) + zstring.encode(text)


def _start_handler(world: wm.World):
    for h in world.free_handlers:
        if "start" in h.events:
            return h
    return None


def _start_text(world: wm.World) -> list[str]:
    """The literal lines the `on start` handler says. B3 supports only `say`
    of plain text in the start handler."""
    handler = _start_handler(world)
    if handler is None:
        return []
    lines: list[str] = []
    for stmt in handler.body:
        if isinstance(stmt, ast.Say):
            lines.append(_literal(stmt.value, stmt.line))
        elif isinstance(stmt, (ast.Stop,)):
            break
        else:
            raise CodegenError(
                "the B3 backend supports only `say` of plain text in 'on "
                "start'; richer code generation arrives in a later milestone",
                getattr(stmt, "line", 0),
            )
    return lines


def _literal(expr: ast.Expr, line: int) -> str:
    if not isinstance(expr, ast.StringLit):
        raise CodegenError("expected a literal string", line)
    out: list[str] = []
    for part in expr.parts:
        if isinstance(part, ast.StringText):
            out.append(part.text)
        else:
            raise CodegenError(
                "string interpolation is not supported yet (B3)", line
            )
    return "".join(out)


def _empty_dictionary() -> bytes:
    # 0 word separators, entry length 9 (6 text + 3 data), 0 entries.
    return bytes([0x00, 0x09, 0x00, 0x00])


def generate(world: wm.World) -> bytes:
    """Lower the world model to a complete z5 story file image."""
    sf = storyfile.StoryFile(version=5)

    # Dynamic memory: globals and the object table (property defaults, no
    # objects yet).
    globals_addr = sf.append(bytes(_GLOBALS_BYTES))
    objects_addr = sf.append(bytes(_PROP_DEFAULTS_BYTES))

    # Static memory: abbreviations and the dictionary.
    static_base = sf.here()
    abbrev_addr = sf.append(bytes(_ABBREV_BYTES))
    dict_addr = sf.append(_empty_dictionary())

    # High memory: the main code, run from the initial program counter.
    code = bytearray()
    code += _print(banner_text(world))
    for line in _start_text(world):
        code += _print(line)
        code.append(OP_NEW_LINE)
    code.append(OP_QUIT)

    high_base = sf.here()
    initial_pc = high_base
    sf.append(bytes(code))

    # Header.
    m = _meta(world)
    sf.set_word(storyfile.H_RELEASE, m.get("release", 1))
    sf.set_word(storyfile.H_HIGH_BASE, high_base)
    sf.set_word(storyfile.H_INITIAL_PC, initial_pc)
    sf.set_word(storyfile.H_DICTIONARY, dict_addr)
    sf.set_word(storyfile.H_OBJECTS, objects_addr)
    sf.set_word(storyfile.H_GLOBALS, globals_addr)
    sf.set_word(storyfile.H_STATIC_BASE, static_base)
    sf.set_word(storyfile.H_ABBREV, abbrev_addr)
    serial = m.get("serial") or datetime.date.today().strftime("%y%m%d")
    sf.set_serial(serial)

    return sf.finalize()
