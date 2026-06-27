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
from .assembler import Routine, RoutineRef, link
from .errors import ArcError
from .lower import Context, compile_block

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


def _start_handler(world: wm.World):
    for h in world.free_handlers:
        if "start" in h.events:
            return h
    return None


def _empty_dictionary() -> bytes:
    # 0 word separators, entry length 9 (6 text + 3 data), 0 entries.
    return bytes([0x00, 0x09, 0x00, 0x00])


# Builtin numeric references get fixed global slots; game globals follow.
_BUILTIN_GLOBALS = ["turns", "score", "max_score", "player", "here"]


def _globals_map(world: wm.World) -> dict:
    m: dict = {}
    n = 16
    for name in _BUILTIN_GLOBALS:
        m[name] = n
        n += 1
    for name in world.globals:
        if name not in m:
            m[name] = n
            n += 1
    return m


def build_story(world: wm.World, entry: Routine, routines: list) -> bytes:
    """Assemble a complete z5 image from the entry stub and routines, laying out
    the standard memory regions. Shared by generate() and the backend tests."""
    sf = storyfile.StoryFile(version=5)

    # Dynamic memory: globals and the object table (property defaults, no
    # objects yet).
    globals_addr = sf.append(bytes(_GLOBALS_BYTES))
    objects_addr = sf.append(bytes(_PROP_DEFAULTS_BYTES))

    # Static memory: abbreviations and the dictionary.
    static_base = sf.here()
    abbrev_addr = sf.append(bytes(_ABBREV_BYTES))
    dict_addr = sf.append(_empty_dictionary())

    # High memory: the entry stub and routines, run from the initial PC.
    high_base = sf.here()
    blob, initial_pc = link(entry, routines, high_base)
    sf.append(blob)

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


def generate(world: wm.World) -> bytes:
    """Lower the world model to a complete z5 story file image.

    The entry stub calls the main routine and quits; the main routine prints the
    banner and runs the `on start` handler. The full turn loop and the rest of
    the handlers arrive with Cosmos (B4.5)."""
    gmap = _globals_map(world)

    entry = Routine("__entry__", entry=True)
    entry.op("call_vn", RoutineRef("__main__"))
    entry.op("quit")

    main = Routine("__main__", nlocals=0)
    main.op("print", text=banner_text(world))
    handler = _start_handler(world)
    if handler is not None:
        ctx = Context(world, gmap)
        ctx.prescan(handler.body)
        compile_block(main, ctx, handler.body)
        main.nlocals = ctx.nlocals()
    main.op("rfalse")

    return build_story(world, entry, [main])
