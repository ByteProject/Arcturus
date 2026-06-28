# codegen.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Code generation for the version 5 backend.

Lays out the complete story file: the header, the global variables, the input
buffers, the object table (objects.py), the abbreviations area, the dictionary
(dictionary.py), and the high-memory code and strings. The entry stub calls a
main routine that prints the banner and runs the `on start` handler, lowered by
lower.py; the assembler (assembler.py) encodes and links the routines.

The full turn loop and the rest of the handlers arrive with Cosmos (B4.5). The
construct-to-opcode mapping is recorded in docs/04-codegen-mapping.md.
"""

from __future__ import annotations

import datetime

from . import __version__
from . import ast
from . import dictionary
from . import objects as objmod
from . import storyfile
from . import worldmodel as wm
from . import zstring
from .assembler import Const, Routine, RoutineRef, STACK, Variable, link
from .errors import ArcError
from .lower import Context, compile_block

_CONST_ONE = Const(1)

# Events fired by the turn loop (not by verb dispatch); excluded from react.
_EVENT_NAMES = {"start", "enter", "each_turn"}


def _action_numbers(world: wm.World) -> dict:
    """A deterministic action -> number map (0 means no action). The parser
    reuses this in B4.5d."""
    names = sorted(set(world.actions) | {"other"})
    return {name: i + 1 for i, name in enumerate(names)}


def _react_handlers(obj: wm.Obj, actions: dict):
    """The object's own pattern-less verb-action handlers, as (action, handler).
    Operand-pattern handlers, free rules, the kind chain, and `other` are
    deferred to B4.5d/e."""
    out = []
    for h in obj.handlers:
        if h.pattern:
            continue
        for ev in h.events:
            if ev in actions and ev not in _EVENT_NAMES and ev != "other":
                out.append((ev, h))
    return out


def _react_objects(world: wm.World, actions: dict) -> set:
    return {
        name
        for name, obj in world.objects.items()
        if _react_handlers(obj, actions)
    }


def gen_react_routines(world: wm.World, actions: dict, registry) -> list:
    """A react_<obj> routine for every object that has react handlers, calling
    the per-handler routines by their registry names."""
    hname = {id(h): nm for h, nm in registry}
    out = []
    for objname, obj in world.objects.items():
        pairs = _react_handlers(obj, actions)
        if not pairs:
            continue
        groups: dict = {}
        for action, h in pairs:
            groups.setdefault(action, []).append(hname[id(h)])
        out.append(_gen_react(objname, groups, actions))
    return out


def _gen_react(objname: str, groups: dict, actions: dict) -> Routine:
    """react_<obj>(action): switch on the action number; for each action run the
    object's handler routine(s) in order, returning 1 as soon as one consumes
    the action (returns 1), else 0."""
    rt = Routine("react_" + objname, nlocals=1)  # local 1 = the action number
    run_label = {}
    for i, action in enumerate(groups):
        run_label[action] = f"run{i}"
        rt.op("je", Variable(1), Const(actions[action]), branch=(run_label[action], True))
    rt.op("ret", Const(0))  # no handled action
    for action, hnames in groups.items():
        rt.label(run_label[action])
        for hn in hnames:
            rt.op("call_vs", RoutineRef(hn), store=Variable(STACK))
            rt.op("je", Variable(STACK), _CONST_ONE, branch=("__handled__", True))
        rt.op("ret", Const(0))  # this action's chain did not consume it
    rt.label("__handled__")
    rt.op("ret", _CONST_ONE)
    return rt

# Region sizes and the input-buffer layout (the buffer constants live in
# storyfile so the lowering can share them; re-exported here for callers/tests).
_GLOBALS_BYTES = storyfile.GLOBALS_BYTES
_PROP_DEFAULTS_BYTES = 63 * 2  # property defaults table (v4+: 63 words)
_ABBREV_BYTES = 96 * 2  # 96 abbreviation entries, empty for now
TEXT_BUFFER_ADDR = storyfile.TEXT_BUFFER_ADDR
TEXT_BUFFER_MAX = storyfile.TEXT_BUFFER_MAX
_TEXT_BUFFER_BYTES = storyfile.TEXT_BUFFER_BYTES
PARSE_BUFFER_ADDR = storyfile.PARSE_BUFFER_ADDR
PARSE_BUFFER_MAX = storyfile.PARSE_BUFFER_MAX
_PARSE_BUFFER_BYTES = storyfile.PARSE_BUFFER_BYTES


class CodegenError(ArcError):
    pass


class StringPool:
    """Strings allocated during lowering (text-property writes, dynamic text).
    build_story lays them out in high memory and backpatches their addresses."""

    def __init__(self) -> None:
        self.strings: dict[str, str] = {}

    def add(self, text: str) -> str:
        sid = f"s{len(self.strings)}"
        self.strings[sid] = text
        return sid


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



# Builtin references get fixed global slots; game globals follow. turns/score/
# max_score are numbers; player/here/noun/second hold object numbers at run time.
_BUILTIN_GLOBALS = ["turns", "score", "max_score", "player", "here", "noun", "second"]


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


def build_story(
    world: wm.World, entry: Routine, routines: list, layout=None, string_pool=None
) -> bytes:
    """Assemble a complete z5 image from the entry stub and routines, laying out
    the standard memory regions. Shared by generate() and the backend tests.
    `layout` is the object table (objects.Layout); without it the object area is
    just the empty property-defaults table."""
    sf = storyfile.StoryFile(version=5)

    # Dynamic memory: globals, the input buffers, and the object table.
    globals_addr = sf.append(bytes(_GLOBALS_BYTES))
    text_buf = bytearray(_TEXT_BUFFER_BYTES)
    text_buf[0] = TEXT_BUFFER_MAX
    sf.append(bytes(text_buf))  # lands at TEXT_BUFFER_ADDR
    parse_buf = bytearray(_PARSE_BUFFER_BYTES)
    parse_buf[0] = PARSE_BUFFER_MAX
    sf.append(bytes(parse_buf))  # lands at PARSE_BUFFER_ADDR
    if layout is not None:
        objects_addr = sf.append(bytes(layout.table))
        # Make the property-table pointers absolute now the base is known.
        for ptr_pos, target in layout.prop_pointers:
            sf.set_word(objects_addr + ptr_pos, objects_addr + target)
    else:
        objects_addr = sf.append(bytes(_PROP_DEFAULTS_BYTES))

    # Static memory: abbreviations and the dictionary built from the program's
    # vocabulary.
    static_base = sf.here()
    abbrev_addr = sf.append(bytes(_ABBREV_BYTES))
    dict_bytes, word_offsets = dictionary.build(world)
    dict_addr = sf.append(dict_bytes)

    # High memory: the entry stub and routines, run from the initial PC.
    high_base = sf.here()
    blob, initial_pc, strrefs, packed_routines = link(entry, routines, high_base)
    blob_start = sf.here()
    sf.append(blob)

    # Packed strings (object descriptions and strings allocated during lowering)
    # live in high memory, 4-aligned so their packed addresses are exact.
    all_strings: dict[str, str] = {}
    if layout is not None:
        all_strings.update(layout.strings)
    if string_pool is not None:
        all_strings.update(string_pool.strings)
    string_packed: dict[str, int] = {}
    for sid, text in all_strings.items():
        while sf.here() % 4 != 0:
            sf.append(b"\x00")
        string_packed[sid] = sf.here() // 4
        sf.append(zstring.encode(text))
    # Backpatch the object table (desc properties and react routine addresses)
    # and the code (string refs).
    if layout is not None:
        for offset, sid in layout.string_fixups:
            sf.set_word(objects_addr + offset, string_packed[sid])
        for offset, rname in layout.routine_fixups:
            sf.set_word(objects_addr + offset, packed_routines[rname])
        # Each words-property entry gets its word's absolute dictionary address.
        for offset, word in layout.word_fixups:
            sf.set_word(objects_addr + offset, dict_addr + word_offsets[word])
    for pos, sid in strrefs:
        sf.set_word(blob_start + pos, string_packed[sid])

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


def _self_operand(world: wm.World, handler: wm.Handler, layout):
    """What `self` is inside a handler routine: an object/room handler knows its
    owner at compile time (a constant), while a kind or free-standing handler
    runs for whichever object is the noun (the noun global)."""
    if (
        handler.owner is not None
        and not handler.origin_kind
        and handler.owner in layout.obj_number
    ):
        return Const(layout.obj_number[handler.owner])
    return Variable(_globals_map(world)["noun"])


def _compile_handler(world, gmap, layout, pool, handler, name) -> Routine:
    rt = Routine(name, nlocals=0)
    ctx = Context(
        world,
        gmap,
        layout=layout,
        self_value=_self_operand(world, handler, layout),
        in_handler=True,
        string_pool=pool,
    )
    ctx.prescan(handler.body)
    compile_block(rt, ctx, handler.body)
    rt.op("ret", _CONST_ONE)  # falling off the end consumes the action
    rt.nlocals = ctx.nlocals()
    return rt


def _compile_block(world, gmap, layout, pool, blk) -> Routine:
    rt = Routine("blk_" + blk.name, nlocals=len(blk.params))
    ctx = Context(world, gmap, params=blk.params, layout=layout, string_pool=pool)
    ctx.prescan(blk.body)
    compile_block(rt, ctx, blk.body)
    rt.op("rfalse")  # default return value if the block does not return one
    rt.nlocals = ctx.nlocals()
    return rt


def build_routines(world: wm.World, gmap: dict, layout, pool):
    """Emit a routine for the main entry, every `block`, and every handler
    except `on start` (which runs inside main for now). Returns the main
    routine, the extra routines, and a registry mapping each handler to its
    routine name for the dispatcher (B4.5b)."""
    main = Routine("__main__", nlocals=0)
    main.op("print", text=banner_text(world))
    start = _start_handler(world)
    if start is not None:
        ctx = Context(world, gmap, layout=layout, in_handler=True, string_pool=pool)
        ctx.prescan(start.body)
        compile_block(main, ctx, start.body)
        main.nlocals = ctx.nlocals()
    main.op("rfalse")

    routines = []
    for blk in world.blocks.values():
        routines.append(_compile_block(world, gmap, layout, pool, blk))

    registry = []
    n = 0
    for handler in world.all_handlers():
        if "start" in handler.events:
            continue  # on start is compiled into main
        name = f"h{n}"
        n += 1
        routines.append(_compile_handler(world, gmap, layout, pool, handler, name))
        registry.append((handler, name))

    return main, routines, registry


def generate(world: wm.World) -> bytes:
    """Lower the world model to a complete z5 story file image.

    The entry stub calls the main routine and quits; main prints the banner and
    runs `on start`. Every other handler and every block is compiled to its own
    routine. The dispatcher and turn loop that drive the handlers arrive with
    Cosmos (B4.5b onward)."""
    gmap = _globals_map(world)
    actions = _action_numbers(world)
    layout = objmod.build_layout(world, react_objects=_react_objects(world, actions))
    pool = StringPool()

    entry = Routine("__entry__", entry=True)
    entry.op("call_vn", RoutineRef("__main__"))
    entry.op("quit")

    main, routines, registry = build_routines(world, gmap, layout, pool)
    react_routines = gen_react_routines(world, actions, registry)

    return build_story(
        world,
        entry,
        [main] + routines + react_routines,
        layout=layout,
        string_pool=pool,
    )
