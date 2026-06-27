# irdump.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A readable, deterministic dump of the world-model IR, for `arcc --dump-ir`.

Only game-defined entities are shown by default; the standard Cosmos kinds and
properties are summarized as counts so the output stays about the author's
program.
"""

from __future__ import annotations

from . import worldmodel as wm


def dump(world: wm.World) -> str:
    out: list[str] = []
    out.append("World")
    out.append(f"  start_room: {world.start_room}")

    game_kinds = sorted(
        (k for k in world.kinds.values() if k.origin == "game"),
        key=lambda k: k.name,
    )
    std_kinds = sum(1 for k in world.kinds.values() if k.origin == "standard")
    out.append(f"  kinds (game): {len(game_kinds)}, standard: {std_kinds}")
    for k in game_kinds:
        out.append(f"    {k.name}: chain={k.chain}")

    out.append(f"  objects: {len([o for o in world.objects.values()])}")
    for name in sorted(world.objects):
        o = world.objects[name]
        out.append(f"    {o.name} ({o.category}) kind={o.kind} chain={o.chain}")
        if o.location:
            out.append(f"      location: {o.location}")
        if o.props:
            out.append(f"      props: {', '.join(sorted(o.props))}")
        for h in o.handlers:
            after = "after " if h.after else ""
            out.append(f"      on {after}{', '.join(h.events)}")

    game_props = sorted(
        (p for p in world.properties.values() if p.origin == "game"),
        key=lambda p: p.name,
    )
    std_props = sum(1 for p in world.properties.values() if p.origin == "standard")
    out.append(f"  properties (game): {len(game_props)}, standard: {std_props}")
    for p in game_props:
        out.append(f"    {p.name}: {p.type} -> {p.storage}")

    out.append(f"  verbs: {len(world.verbs)}")
    for v in world.verbs:
        actions = ", ".join(g.action for g in v.grammar)
        out.append(f"    {v.words} -> {actions}")

    if world.globals:
        out.append(f"  globals: {len(world.globals)}")
        for name in sorted(world.globals):
            g = world.globals[name]
            out.append(f"    {g.name}: {g.type}")
    if world.constants:
        out.append(f"  constants: {len(world.constants)}")
        for name in sorted(world.constants):
            c = world.constants[name]
            out.append(f"    {c.name}: {c.type}")
    if world.blocks:
        out.append(f"  blocks: {', '.join(sorted(world.blocks))}")

    out.append(f"  free handlers: {len(world.free_handlers)}")
    for h in world.free_handlers:
        out.append(f"    on {', '.join(h.events)}")

    props = sum(1 for v in world.is_resolutions.values() if v == wm.IS_PROPERTY)
    eq = sum(1 for v in world.is_resolutions.values() if v == wm.IS_EQUALITY)
    out.append(f"  is-tests: {props} property, {eq} equality")
    return "\n".join(out)
