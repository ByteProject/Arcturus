# objects.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Z-machine version 5 object table.

Builds the property-defaults table, the object entries (attributes, the
parent/sibling/child tree, and the property-table pointer), and each object's
property table (the Z-encoded short name from `name`, then the slot properties
in descending property number). Numbers are assigned here and shared with the
lowering so code can reference objects, attributes, and properties.

Object numbering starts at 1 (object 0 is `nothing`). Attributes are numbered
0..47 and properties 1..63 (the v4+ ranges). `name` becomes the short name, not
a numbered property; `words` is parser vocabulary and is added in B4.4. A `desc`
property holds a packed string address, recorded as a fixup and backpatched once
high memory is laid out.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import ast
from . import prelude
from . import worldmodel as wm
from . import zstring

_NUM_DEFAULTS = 63  # property-defaults table size in v4+
_ENTRY_SIZE = 14  # object entry size in v4+
_MAX_ATTRIBUTES = 48
_MAX_PROPERTIES = 63

# Properties that are not stored as numbered properties.
_SPECIAL = {"name", "words"}


@dataclass
class Layout:
    obj_number: dict[str, int] = field(default_factory=dict)
    attr_number: dict[str, int] = field(default_factory=dict)
    prop_number: dict[str, int] = field(default_factory=dict)
    table: bytearray = field(default_factory=bytearray)
    # (offset within `table`, string id) to patch with a packed string address.
    string_fixups: list[tuple[int, str]] = field(default_factory=list)
    strings: dict[str, str] = field(default_factory=dict)
    # Property-table pointers are absolute story-file addresses; they are stored
    # relative here and made absolute (plus the object-table base) in build_story.
    # Each entry is (offset-of-pointer-word, relative-target-offset).
    prop_pointers: list[tuple[int, int]] = field(default_factory=list)


def _effective_props(world: wm.World, obj: wm.Obj) -> dict:
    """Merge the kind chain (root first) then the instance, so the instance and
    nearer kinds win. Values are PropertyDecls."""
    merged: dict = {}
    for kind_name in reversed(obj.chain):
        kind = world.kinds.get(kind_name)
        if kind is not None:
            merged.update(kind.props)
    merged.update(obj.props)
    return merged


def _bool_value(decl: ast.PropertyDecl) -> bool:
    if decl.form == ast.PROP_BOOL:
        return True
    if decl.form == ast.PROP_VALUE and decl.values:
        v = decl.values[0]
        return isinstance(v, ast.Bool) and v.value
    return False


def build_layout(world: wm.World) -> Layout:
    layout = Layout()

    # Object numbers (1..N), in collection order.
    for i, name in enumerate(world.objects, start=1):
        layout.obj_number[name] = i

    # Attribute and property numbers from the B2 storage classification.
    a = 0
    p = 1
    for name in sorted(world.properties):
        prop = world.properties[name]
        if prop.storage == wm.STORE_ATTRIBUTE:
            if a >= _MAX_ATTRIBUTES:
                raise _err("more than 48 attributes; attribute spill is a later milestone")
            layout.attr_number[name] = a
            a += 1
        elif name not in _SPECIAL:
            if p > _MAX_PROPERTIES:
                raise _err("more than 63 properties")
            layout.prop_number[name] = p
            p += 1

    _emit_table(world, layout)
    return layout


def _emit_table(world: wm.World, layout: Layout) -> None:
    table = layout.table
    n = len(world.obj_number) if False else len(layout.obj_number)

    # Property-defaults table: 63 words, all zero.
    table += bytes(_NUM_DEFAULTS * 2)

    # Reserve the object entries; property tables follow them.
    entries_at = len(table)
    table += bytes(n * _ENTRY_SIZE)

    # Build each object's property table and fill its entry.
    tree = _build_tree(world, layout)
    for name, num in layout.obj_number.items():
        obj = world.objects[name]
        eff = _effective_props(world, obj)

        prop_addr = len(table)
        _emit_property_table(world, layout, name, eff)

        entry = entries_at + (num - 1) * _ENTRY_SIZE
        # Attributes (48 bits, attribute 0 = bit 7 of byte 0).
        for pname, decl in eff.items():
            anum = layout.attr_number.get(pname)
            if anum is not None and _bool_value(decl):
                table[entry + anum // 8] |= 0x80 >> (anum % 8)
        parent, sibling, child = tree[name]
        _put_word(table, entry + 6, parent)
        _put_word(table, entry + 8, sibling)
        _put_word(table, entry + 10, child)
        # The property-table pointer is absolute; resolved in build_story.
        layout.prop_pointers.append((entry + 12, prop_addr))


def _emit_property_table(world, layout, name, eff) -> None:
    table = layout.table
    # Short name from `name`.
    short = ""
    if "name" in eff and eff["name"].form == ast.PROP_VALUE and eff["name"].values:
        v = eff["name"].values[0]
        if isinstance(v, ast.StringLit):
            short = _plain(v)
    encoded = zstring.encode(short) if short else b""
    table.append(len(encoded) // 2)
    table += encoded

    # Slot properties in descending property number.
    items = []
    for pname, decl in eff.items():
        pnum = layout.prop_number.get(pname)
        if pnum is not None:
            items.append((pnum, pname, decl))
    for pnum, pname, decl in sorted(items, reverse=True):
        table.append(0x40 | pnum)  # one-byte size form, two data bytes
        data_at = len(table)
        table += b"\x00\x00"
        _fill_property(world, layout, pname, decl, data_at)


def _fill_property(world, layout, pname, decl, data_at) -> None:
    ptype = world.properties[pname].type
    if ptype == prelude.T_TEXT:
        if decl.form == ast.PROP_VALUE and decl.values and isinstance(
            decl.values[0], ast.StringLit
        ):
            sid = f"{pname}@{data_at}"
            layout.strings[sid] = _plain(decl.values[0])
            layout.string_fixups.append((data_at, sid))
        return  # block/computed text is deferred (B4.5)
    if ptype == prelude.T_OBJECT:
        target = 0
        if decl.form == ast.PROP_VALUE and decl.values:
            v = decl.values[0]
            if isinstance(v, ast.Name):
                target = layout.obj_number.get(v.ident, 0)
        _put_word(layout.table, data_at, target)
        return
    if ptype == prelude.T_NUMBER:
        value = 0
        if decl.form == ast.PROP_VALUE and decl.values and isinstance(
            decl.values[0], ast.Number
        ):
            value = decl.values[0].value & 0xFFFF
        _put_word(layout.table, data_at, value)
        return
    # list/block properties: deferred (words to B4.4, computed to B4.5)


def _build_tree(world: wm.World, layout: Layout) -> dict:
    """Compute (parent, sibling, child) object numbers for each object from the
    initial `in <location>` placements."""
    children: dict[str, list[str]] = {name: [] for name in layout.obj_number}
    parent_of: dict[str, str] = {}
    for name, obj in world.objects.items():
        if obj.location and obj.location in layout.obj_number:
            children[obj.location].append(name)
            parent_of[name] = obj.location

    tree: dict[str, tuple] = {}
    for name in layout.obj_number:
        parent = layout.obj_number.get(parent_of.get(name), 0)
        kids = children[name]
        child = layout.obj_number[kids[0]] if kids else 0
        tree[name] = (parent, 0, child)
    # Sibling chains: each child points to the next in its parent's list.
    for name, kids in children.items():
        for i, kid in enumerate(kids):
            nxt = layout.obj_number[kids[i + 1]] if i + 1 < len(kids) else 0
            p, _s, c = tree[kid]
            tree[kid] = (p, nxt, c)
    return tree


def _plain(lit: ast.StringLit) -> str:
    return "".join(
        part.text for part in lit.parts if isinstance(part, ast.StringText)
    )


def _put_word(buf: bytearray, off: int, value: int) -> None:
    buf[off] = (value >> 8) & 0xFF
    buf[off + 1] = value & 0xFF


def _err(msg: str):
    from .errors import ArcError

    return ArcError(msg)
