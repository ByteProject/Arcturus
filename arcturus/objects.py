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
_MAX_PROPERTIES = 62  # user properties 1..62; 63 is reserved for react

# Property 63 holds the packed address of the object's react routine (B4.5b);
# the dispatcher reads it to run the object's handlers.
REACT_PROP = 63

# `name` is the short name, not a numbered property. `words` IS a numbered
# property, holding an array of dictionary addresses (filled in B4.5d.1).
_SPECIAL = {"name"}

# The conversation topic table (docs/02 section 14). A person with `topic`
# declarations carries a `topics` property holding the address of its table:
# a count word, then one fixed-size record per topic, then the per-topic
# match-word sub-arrays. Each record is TOPIC_REC bytes:
#   +0 body routine    (2, packed)  the exchange to run
#   +2 menu label      (2, packed)  the string shown in the conversations menu
#   +4 when-guard      (2, packed)  visibility test routine, 0 if no `when`
#   +6 match words     (2)          address of this topic's word sub-array, 0 none
#   +8 flags           (1)          static: bit0 ONCE, bit1 HIDDEN at start
#   +9 state           (1)          mutable: bit0 RETIRED, bit1 HIDDEN now
# The granules read the table through the cosmos_topic_* backing routines, so
# this byte layout lives only here and in codegen (which emits those routines).
TOPIC_REC = 10
TOPIC_ONCE = 0x01  # flags byte: retire this topic after it runs once
TOPIC_HIDDEN = 0x02  # flags/state byte: out of view (initial flag and live state)
TOPIC_RETIRED = 0x01  # state byte: a `once` topic that has already run


def topic_routine_name(objname: str, idx: int) -> str:
    """The routine that runs topic `idx` of object `objname` (its body). Named
    deterministically so objects.py (the table) and codegen.py (the routine)
    agree without a registry, exactly like react_<obj>."""
    return f"topic_{objname}_{idx}"


def topic_when_name(objname: str, idx: int) -> str:
    """The visibility-guard routine for topic `idx` (its `when` condition),
    emitted only when the topic has a `when`."""
    return f"topicwhen_{objname}_{idx}"


def prop_routine_name(objname: str, pname: str) -> str:
    """The routine that computes property `pname` of `objname` (a `<name> block`
    property). Named deterministically so the property table (here) and the routine
    (codegen) agree, like react_<obj> and the topic routines."""
    return f"prop_{objname}_{pname}"


@dataclass
class Layout:
    obj_number: dict[str, int] = field(default_factory=dict)
    attr_number: dict[str, int] = field(default_factory=dict)
    kind_attr: dict[str, int] = field(default_factory=dict)  # kind name -> attribute
    prop_number: dict[str, int] = field(default_factory=dict)
    table: bytearray = field(default_factory=bytearray)
    # (offset within `table`, string id) to patch with a packed string address.
    string_fixups: list[tuple[int, str]] = field(default_factory=list)
    strings: dict[str, str] = field(default_factory=dict)
    # Property-table pointers are absolute story-file addresses; they are stored
    # relative here and made absolute (plus the object-table base) in build_story.
    # Each entry is (offset-of-pointer-word, relative-target-offset).
    prop_pointers: list[tuple[int, int]] = field(default_factory=list)
    # (offset within `table`, routine name) to patch with a routine's packed
    # address - used for the react property (B4.5b).
    routine_fixups: list[tuple[int, str]] = field(default_factory=list)
    # (offset within `table`, word) to patch with the word's dictionary address,
    # for each entry of an object's words property (B4.5d).
    word_fixups: list[tuple[int, str]] = field(default_factory=list)
    # Objects that have a react routine; their react property (63) is emitted.
    react_objects: set = field(default_factory=set)
    # Computed (`<name> block`) properties, as (objname, pname, is_text, decl):
    # codegen emits a prop_<obj>_<pname> routine for each, and the property stores
    # its packed address (a routine_fixup), read by "print or run" at the use site.
    computed_props: list = field(default_factory=list)
    # True if any object is `named` (a thing with a proper name). The article in
    # ${the noun} only needs its runtime named-check when this holds, so a game
    # with no named objects pays nothing for it.
    has_named: bool = False


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


def _name_first_letter(decl) -> str:
    """The first letter of a text property's literal value (the object's name),
    lowercased, or '' if it cannot be read. Used to derive the a/an article."""
    if decl is not None and decl.form == ast.PROP_VALUE and decl.values:
        v = decl.values[0]
        if isinstance(v, ast.StringLit):
            for part in v.parts:
                if isinstance(part, ast.StringText) and part.text.strip():
                    return part.text.strip()[0].lower()
    return ""


def _bool_value(decl: ast.PropertyDecl) -> bool:
    if decl.form == ast.PROP_BOOL:
        return True
    if decl.form == ast.PROP_VALUE and decl.values:
        v = decl.values[0]
        return isinstance(v, ast.Bool) and v.value
    return False


def build_layout(world: wm.World, react_objects=None) -> Layout:
    layout = Layout()
    if react_objects:
        layout.react_objects = set(react_objects)

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

    # Does any object resolve to `named`? The article printer (${the noun}) uses
    # this to skip its runtime named-check entirely in a game with no named
    # objects, so the common case costs nothing.
    if "named" in layout.attr_number:
        for name in world.objects:
            decl = _effective_props(world, world.objects[name]).get("named")
            if decl is not None and _bool_value(decl):
                layout.has_named = True
                break

    # Kinds get attributes too, so `obj is <kind>` lowers to a test_attr: an
    # object carries the attribute of every kind in its chain (B4.5c).
    for kname in sorted(world.kinds):
        if a >= _MAX_ATTRIBUTES:
            raise _err("more than 48 attributes (properties plus kinds)")
        layout.kind_attr[kname] = a
        a += 1

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

    # Build each object's property table and fill its entry. Objects with `topic`
    # declarations record where their `topics` property pointer sits; the topic
    # tables are appended after all property tables and the pointers patched.
    topic_sites: dict[str, int] = {}
    tree = _build_tree(world, layout)
    for name, num in layout.obj_number.items():
        obj = world.objects[name]
        eff = _effective_props(world, obj)

        prop_addr = len(table)
        _emit_property_table(world, layout, name, eff, topic_sites)

        entry = entries_at + (num - 1) * _ENTRY_SIZE
        # Attributes are 48 bits across the first six bytes, most significant
        # bit first: attribute a lives in byte a//8 at bit (7 - a%8). Set the
        # bit only when the object's effective boolean for that property is true.
        for pname, decl in eff.items():
            anum = layout.attr_number.get(pname)
            if anum is not None and _bool_value(decl):
                table[entry + anum // 8] |= 0x80 >> (anum % 8)
        # Indefinite article: when the author did not set `an` either way, derive
        # it from the name (a vowel-initial name takes "an"), so listings read
        # "an apple" / "a coin" with no author work.
        an_num = layout.attr_number.get("an")
        if an_num is not None and "an" not in eff:
            if _name_first_letter(eff.get("name")) in ("a", "e", "i", "o", "u"):
                table[entry + an_num // 8] |= 0x80 >> (an_num % 8)
        # Kind-membership attributes: one for each kind in the object's chain.
        for kname in obj.chain:
            katt = layout.kind_attr.get(kname)
            if katt is not None:
                table[entry + katt // 8] |= 0x80 >> (katt % 8)
        # A v4+ object entry is 14 bytes: six attribute bytes (set above), then
        # the parent, sibling, and child object numbers as 16-bit words, then a
        # pointer to this object's property table (standard 1.1, section 12.3.2).
        parent, sibling, child = tree[name]
        _put_word(table, entry + 6, parent)
        _put_word(table, entry + 8, sibling)
        _put_word(table, entry + 10, child)
        # The pointer must be an absolute story-file address, but the object
        # table's base is not fixed until build_story places it, so record the
        # relative target and let build_story add the base.
        layout.prop_pointers.append((entry + 12, prop_addr))

    # Topic tables, appended after every property table so a person's `topics`
    # property can point at one. Done last because the records reference packed
    # routine and string addresses resolved only at link time.
    _emit_topic_tables(world, layout, topic_sites)


def _emit_topic_tables(world, layout, topic_sites: dict) -> None:
    """Emit each person's topic table and patch its `topics` property pointer.
    A table is a count word, then a TOPIC_REC record per topic, then the
    per-topic match-word sub-arrays. The record fields are filled by fixups
    resolved in build_story: the body and when-guard routines (routine_fixups),
    the menu label (string_fixups), and the words sub-array pointer
    (prop_pointers, made absolute against the object-table base). See TOPIC_REC."""
    table = layout.table
    for name, prop_site in topic_sites.items():
        topics = world.objects[name].topics
        table_off = len(table)
        # Patch the object's `topics` property to point at this table.
        layout.prop_pointers.append((prop_site, table_off))
        _put_word(table, prop_site, 0)  # placeholder until build_story adds base
        # Count word, then the fixed-size records.
        table += bytes(2)
        _put_word(table, table_off, len(topics))
        word_ptr_sites = []
        for idx, topic in enumerate(topics):
            rec = len(table)
            table += bytes(TOPIC_REC)
            # +0 body routine, +4 when-guard: packed addresses via routine fixups.
            layout.routine_fixups.append((rec + 0, topic_routine_name(name, idx)))
            if topic.when is not None:
                layout.routine_fixups.append((rec + 4, topic_when_name(name, idx)))
            # +2 menu label: a packed string allocated into the layout's pool.
            label = _topic_label(topic)
            sid = f"topiclabel@{rec}"
            layout.strings[sid] = label
            layout.string_fixups.append((rec + 2, sid))
            # +8 flags: ONCE and the initial HIDDEN bit (static); +9 state begins
            # as the live mirror of HIDDEN so a hidden topic starts out of view.
            flags = (TOPIC_ONCE if topic.once else 0) | (TOPIC_HIDDEN if topic.hidden else 0)
            table[rec + 8] = flags
            table[rec + 9] = TOPIC_HIDDEN if topic.hidden else 0
            word_ptr_sites.append((rec + 6, topic.words))
        # The match-word sub-arrays (count word + a dictionary address per word),
        # pointed at from each record's +6 field.
        for ptr_site, words in word_ptr_sites:
            if not words:
                continue
            sub_off = len(table)
            layout.prop_pointers.append((ptr_site, sub_off))
            table += bytes(2)
            _put_word(table, sub_off, len(words))
            for w in words:
                data_at = len(table)
                table += bytes(2)
                layout.word_fixups.append((data_at, w.lower()))


def _topic_label(topic) -> str:
    """The topic's menu label, as plain text. Interpolation in a label is not
    supported (a menu line is a static string), so only the literal text counts."""
    lbl = topic.label
    if isinstance(lbl, ast.StringLit):
        return _plain(lbl)
    return ""


def _emit_property_table(world, layout, name, eff, topic_sites=None) -> None:
    table = layout.table
    # The property table opens with the object's short name: a length byte
    # giving the number of 2-byte words in the Z-string, then the Z-string
    # itself (standard 1.1, section 12.3.1). It comes from the `name` property.
    short = ""
    if "name" in eff and eff["name"].form == ast.PROP_VALUE and eff["name"].values:
        v = eff["name"].values[0]
        if isinstance(v, ast.StringLit):
            short = _plain(v)
    encoded = zstring.encode(short) if short else b""
    table.append(len(encoded) // 2)
    table += encoded

    # Properties are listed in descending property number. React (63) is the
    # highest, so it comes first: a two-byte value holding the packed address of
    # this object's react routine, backpatched in build_story via a routine
    # fixup (the object table base is not known until then).
    if name in layout.react_objects:
        layout.table.append(0x40 | REACT_PROP)
        data_at = len(layout.table)
        layout.table += b"\x00\x00"
        layout.routine_fixups.append((data_at, "react_" + name))

    # Then the user properties. Every value Arcturus stores is two bytes, so each
    # uses the one-byte size form: bit 6 set means "two data bytes", and the low
    # five bits hold the property number (section 12.4.2.1).
    items = []
    for pname, decl in eff.items():
        if pname == "words":
            continue  # emitted from the merged vocabulary below
        pnum = layout.prop_number.get(pname)
        if pnum is not None:
            items.append((pnum, pname, decl))
    # The words property is the object's matchable vocabulary: its explicit
    # `words` plus the significant words of its `name`. It is emitted for every
    # object that has any, so a thing named but lacking `words` is still parsable.
    words_prop = layout.prop_number.get("words")
    vocab = object_words(eff, world.objects[name].category == "room")
    if words_prop is not None and vocab:
        items.append((words_prop, "words", vocab))
    # A person with `topic` declarations gets a `topics` property holding a
    # pointer to its topic table; the table itself is appended after all property
    # tables (the pointer is patched there, so only its site is reserved here).
    topics_prop = layout.prop_number.get("topics")
    if topics_prop is not None and world.objects[name].topics:
        items.append((topics_prop, "topics", None))
    for pnum, pname, decl in sorted(items, reverse=True, key=lambda it: it[0]):
        if pname == "words":
            _emit_words(layout, pnum, decl)
            continue
        table.append(0x40 | pnum)  # bit 6 = two data bytes; low bits = number
        data_at = len(table)
        table += b"\x00\x00"  # placeholder, filled by _fill_property
        if pname == "topics":
            if topic_sites is not None:
                topic_sites[name] = data_at  # patched in _emit_topic_tables
            continue
        if decl is not None and decl.form == ast.PROP_BLOCK:
            # A computed property: store the packed address of its block routine
            # (codegen emits prop_<obj>_<pname>), and record it so codegen knows to
            # compile the routine and treat reads of this property as "print or run".
            layout.routine_fixups.append((data_at, prop_routine_name(name, pname)))
            is_text = world.properties[pname].type == prelude.T_TEXT
            layout.computed_props.append((name, pname, is_text, decl))
            continue
        _fill_property(world, layout, pname, decl, data_at)
    # A property list is terminated by a size byte of zero (standard 1.1, section
    # 12.4.1). Without it, get_prop_addr for an absent property walks past this
    # object into whatever follows: it only ever "worked" because the object table
    # was trailed by the zero-filled abbreviation table, so the first zero there
    # ended the walk. Filling that table (B6 abbreviations) removed the accidental
    # terminator, so each property list now ends with its own.
    table.append(0)


def object_words(eff: dict, is_room: bool = False) -> list:
    """An object's matchable vocabulary: its explicit `words`, then any new words
    from its `name` (so `name "rusted lever"` makes lever and rusted match even
    with no `words` line). Rooms contribute only explicit words, not their name,
    so a room name is not a noun the player can take or examine."""
    words: list = []
    if "words" in eff:
        words.extend(v.ident.lower() for v in eff["words"].values if isinstance(v, ast.Name))
    if not is_room and "name" in eff and eff["name"].form == ast.PROP_VALUE and eff["name"].values:
        v = eff["name"].values[0]
        if isinstance(v, ast.StringLit):
            for w in _plain(v).lower().split():
                if w.isalnum() and w not in words:
                    words.append(w)
    return words


def _emit_words(layout: Layout, pnum: int, words: list) -> None:
    """The words property is an array of dictionary addresses (two bytes each).
    It uses the two-byte size form (section 12.4.2.1): first byte bit 7 set with
    the property number, second byte bit 7 set with the data length. Each entry
    is backpatched with its word's dictionary address."""
    length = len(words) * 2
    layout.table.append(0x80 | pnum)
    layout.table.append(0x80 | (length & 0x3F))
    for w in words:
        data_at = len(layout.table)
        layout.table += b"\x00\x00"
        layout.word_fixups.append((data_at, w))


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
