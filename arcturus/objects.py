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


def amb_play_name(objname: str, idx: int) -> str:
    return f"amb_play_{objname}_{idx}"


def amb_guard_name(objname: str, idx: int) -> str:
    return f"amb_guard_{objname}_{idx}"


def amb_lg_name(objname: str, idx: int) -> str:
    return f"amb_lg_{objname}_{idx}"


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
    # Tested kinds that overflowed the attribute budget: their `obj is <kind>`
    # is a catalog membership scan instead of a test_attr (Step 2). Empty
    # whenever the flags plus tested kinds fit in 48, which is nearly always.
    kind_spilled: list = field(default_factory=list)
    # kind name -> word offset of its synthesized extent catalog (the object
    # numbers of its transitive instances), for the spilled kinds only.
    kind_catalog: dict[str, int] = field(default_factory=dict)
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
    # Offset of the ambience table inside `table` (-1 when no block exists);
    # build_story seeds the __ambience__ global with its absolute address.
    ambience_off: int = -1
    # Scoring (docs/01): offsets of the rank ladder and the labelled-pool
    # tables (-1 when absent), and the rank threshold patch sites
    # (position, percent-or-None, index, count); thresholds are written in
    # build_story once the compiler-summed max_score is known.
    ranks_off: int = -1
    pools_off: int = -1
    rank_sites: list = field(default_factory=list)
    # Text globals: (global name, string id) pairs; build_story seeds each
    # global's slot with its initializer's packed string address.
    global_strings: list = field(default_factory=list)
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
    # True if any object is `pluribus` (grammatically plural: the scissors).
    # The articles, the ${is x} copula, and the message branches guard on
    # any_pluribus, so an unmarked game folds them all away.
    has_pluribus: bool = False
    # True if any object is `beyond` (visible, not touchable); the touch
    # guards fold away without one.
    has_beyond: bool = False
    # True if any (non-movable) object declares `spans`. The scope code guards its
    # spans checks with `any_spans()`, which folds to this; a game with no spanning
    # objects folds the checks away and dead-code elimination drops the spans
    # blocks, so it pays nothing for the feature.
    has_spans: bool = False
    # The directions ALIVE in this game, in canonical order: those with player
    # words declared (the pack's compass set; nautical when its granule is
    # summoned) or written as an exit on some room. The exits_count /
    # exit_prop / exit_name trio iterates exactly these, so a standard
    # direction nobody can walk (the nautical four in a landlocked game)
    # adds nothing to the verbose_exits routines.
    live_directions: list = field(default_factory=list)
    # catalog name -> word offset from the catalog region's start; the region's
    # byte offset within the table. __catalogs__ = objects_addr + region_off.
    catalogs: dict = field(default_factory=dict)
    catalog_region_off: int = 0
    # matrix name -> word offset from the SAME region's start (matrices share
    # the catalog region, base, and [count, widest, cells] header). The only
    # differences from a catalog are the reserved spare cells (capacity beyond
    # the seed) and that `count` is the live, mutable length.
    matrices: dict = field(default_factory=dict)
    # True if any object is of the `door` kind. The go handler guards its door
    # detour (open/lock check, step to the far side) with `any_doors()`, so a game
    # with no doors folds it away and pays nothing.
    has_doors: bool = False
    # True if anything declares `grains`. The parser's find_scenery guards its
    # grain-chain walker with `any_grains()`, so a game with no grains folds the
    # walker away and pays nothing.
    has_grains: bool = False


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


def _name_head(decl) -> str:
    """The head noun of the object name (its first word), lowercased, or '' if
    unreadable. In Spanish the head noun leads ("lampara de bronce"), and gender is
    read from it, not the whole name."""
    if decl is not None and decl.form == ast.PROP_VALUE and decl.values:
        v = decl.values[0]
        if isinstance(v, ast.StringLit):
            text = "".join(
                p.text for p in v.parts if isinstance(p, ast.StringText)
            ).strip()
            if text:
                return text.split()[0].lower()
    return ""


# Word endings that are reliably feminine in Spanish, regardless of the final
# letter (la cancion, la ciudad, la virtud, la costumbre). Checked before the
# plain -a / -o rule so a feminine noun that does not end in -a is still caught.
_SPANISH_FEMININE_SUFFIXES = ("cion", "ción", "sion", "sión", "dad", "tad", "tud", "umbre")


# Languages whose gender has NO spelling rule, so the compiler must not guess it
# from a name. German is the case: it has three genders and the author declares the
# article (der/die/das), and a masculine noun can end in -a, so the two-gender -a
# heuristic would mis-gender it. Every other language (English ignores the bit,
# Spanish and a hand-rolled gendered game read the -a rule) leaves derivation on.
_NO_SPELLING_GENDER = frozenset({"german"})


def _spelling_gender_language(world: wm.World) -> bool:
    """Whether to fill `feminine` from a name's spelling. On by default, and off
    only for a language that declares gender explicitly (German), so its masculine
    -a nouns are not silently made feminine."""
    for s in getattr(world, "summons", []):
        if getattr(s, "form", None) == "feature" and getattr(s, "target", None) == "language":
            return not (bool(s.arg) and s.arg.lower() in _NO_SPELLING_GENDER)
    return True


def _derive_feminine(decl) -> bool:
    """Whether to set `feminine` on an object from its name, for a gendered
    language to read. A head noun with a reliably feminine suffix, or ending in -a,
    is feminine; everything else defaults masculine. The author overrides the few
    the spelling cannot reveal (la llave, el mapa). English never reads the bit."""
    head = _name_head(decl)
    if not head:
        return False
    if head.endswith(_SPANISH_FEMININE_SUFFIXES):
        return True
    return head.endswith("a")


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
                # The only real attribute ceiling: genuine object attributes
                # (mutable per-object boolean state). Kinds never cause this,
                # they spill to catalog membership; so name attributes, not
                # kinds. (Attributes spilling to property bytes is a later
                # lever, when even this ceiling can move.)
                raise _err(
                    f"more than {_MAX_ATTRIBUTES} attributes: the Z-machine "
                    f"v5 limit. Kinds do not count here (they spill to "
                    f"catalogs); this is genuine object attribute state")
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

    # Does any object resolve to `pluribus` (grammatical plural)? Same folding
    # role as has_named, for the number-agreement machinery.
    if "pluribus" in layout.attr_number:
        for name in world.objects:
            decl = _effective_props(world, world.objects[name]).get("pluribus")
            if decl is not None and _bool_value(decl):
                layout.has_pluribus = True
                break

    # Does any object resolve to `beyond`? Same folding role as the others. A
    # runtime `now ... is beyond` also counts (world.sets_beyond): the
    # player-beyond mount declares beyond on nothing and still needs the touch
    # guards compiled in.
    if "beyond" in layout.attr_number:
        if getattr(world, "sets_beyond", False):
            layout.has_beyond = True
        else:
            for name in world.objects:
                decl = _effective_props(world, world.objects[name]).get("beyond")
                if decl is not None and _bool_value(decl):
                    layout.has_beyond = True
                    break

    # The live directions (see the Layout field): worded, or used as an exit.
    worded = set(world.directions.values())
    used = set()
    dir_names = set(prelude._DIRECTIONS)
    for name, obj in world.objects.items():
        for pname in _effective_props(world, obj):
            if pname in dir_names:
                used.add(pname)
    layout.live_directions = [
        d for d in prelude._DIRECTIONS
        if (d in worded or d in used) and d in layout.prop_number
    ]

    # Does any non-movable object declare `spans`? Only then does the scope code
    # keep its spans checks (any_spans folds to this); otherwise they cost nothing.
    for name, obj in world.objects.items():
        if not obj.spans:
            continue
        eff = _effective_props(world, obj)
        if ("fixed" in eff and _bool_value(eff["fixed"])) or (
            "scenery" in eff and _bool_value(eff["scenery"])
        ):
            layout.has_spans = True
            break

    # Is any object a door? Only then does the go handler keep its door detour
    # (any_doors folds to this); a game with no doors pays nothing for it.
    for obj in world.objects.values():
        if "door" in obj.chain:
            layout.has_doors = True
            break

    # Does anything declare grains? Only then does the parser keep its grain-chain
    # walker (any_grains folds to this); a game with no grains pays nothing.
    for obj in world.objects.values():
        if obj.grains:
            layout.has_grains = True
            break
    if not layout.has_grains:
        for kind in world.kinds.values():
            if kind.grains:
                layout.has_grains = True
                break

    # Kind-membership attributes (Lever 1): only kinds the program actually
    # tests with `obj is <kind>` need a runtime identity. A kind used purely
    # to organize, share handlers or properties, or span scenery is resolved
    # at compile time (spanning expands to concrete rooms; handlers weave into
    # react routines; inheritance merges) and costs ZERO attributes. Tested
    # kinds take the attribute slots the real flags left free, busiest first
    # (world.kind_tests ranks them), so the scarce one-byte test_attr goes to
    # the hot tests. When the 48 budget runs out here, the remaining tested
    # kinds SPILL to catalog membership (build_kind_spill, below) rather than
    # erroring: a class never steals a slot from a flag, and running out of
    # attributes for kinds is not a ceiling. `a` at this point is the flag
    # count, so the surviving budget is _MAX_ATTRIBUTES - a.
    tested = sorted(world.kind_tests, key=lambda k: (-world.kind_tests[k], k))
    for kname in tested:
        if a >= _MAX_ATTRIBUTES:
            break  # the rest spill to catalog membership
        layout.kind_attr[kname] = a
        a += 1
    layout.kind_spilled = [k for k in tested if k not in layout.kind_attr]
    # A spilled kind's transitive instances (every object whose chain includes
    # it), in ascending object-number order. `obj is <spilled_kind>` becomes a
    # membership scan of this list, so kinds are limitless past the attribute
    # budget. Computed here because the extents feed the catalog region below.
    kind_extents = {
        kname: [layout.obj_number[o] for o, obj in world.objects.items()
                if kname in obj.chain]
        for kname in layout.kind_spilled
    }

    # Catalog word offsets, BEFORE the table is emitted: a property can hold
    # a catalog name (`writing PLAQUE_TEXT`), and _fill_property needs the
    # offset while the property tables are being written. The offsets follow
    # from declaration order alone ([count, widest, e1..eN] per catalog), so
    # they are known before the region itself is appended below. The spilled
    # kinds' extent catalogs share the region, their offsets continuing after
    # the author catalogs.
    woff = 0
    for cname, cat in world.catalogs.items():
        layout.catalogs[cname] = woff
        woff += 2 + len(cat.values)
    for kname in layout.kind_spilled:
        layout.kind_catalog[kname] = woff
        woff += 2 + len(kind_extents[kname])
    # Matrices continue in the same region after the catalogs and kind extents.
    # A matrix reserves its full CAPACITY of cells (not just the seed), because
    # append grows the live count into the spare slots at runtime.
    for mname, mx in world.matrices.items():
        layout.matrices[mname] = woff
        if mx.is_2d and mx.cell == "byte":
            # A byte-packed grid: rows*cols bytes, rounded up to whole words so
            # the next table stays word-aligned. Half the memory of word cells.
            woff += (mx.rows * mx.cols + 1) // 2
        elif mx.is_2d:
            woff += mx.rows * mx.cols          # a flat word grid, no header
        else:
            woff += 2 + mx.capacity            # [count, capacity, cells]

    _emit_table(world, layout)
    # The catalog region (docs/01, catalogs): every declared catalog laid
    # out end to end inside the dynamic table, so a single entry is
    # rewritable in place (change entry(...) is one storew and there is no
    # heap anywhere). Per catalog: [count, widest, e1..eN] as words; widest
    # is the longest text entry's display length (for the quote box) and 0
    # for number and object catalogs. Text entries are string fixups into
    # the shared pool (identical text stored once); offsets are in WORDS
    # from the region start, whose byte address seeds __catalogs__.
    layout.catalog_region_off = len(layout.table)
    for cname, cat in world.catalogs.items():
        widest = 0
        if cat.etype == "text":
            widest = max(len(_plain(v)) for v in cat.values)
        _append_word(layout.table, len(cat.values))
        _append_word(layout.table, widest)
        for v in cat.values:
            at = len(layout.table)
            if cat.etype == "text":
                sid = f"cat_{cname}@{at}"
                layout.strings[sid] = _plain(v)
                layout.string_fixups.append((at, sid))
                _append_word(layout.table, 0)
            elif cat.etype == "number":
                _append_word(layout.table, v.value & 0xFFFF)
            else:
                _append_word(layout.table, layout.obj_number.get(v.ident, 0))
    # The spilled kinds' extent catalogs, same [count, widest, e1..eN] shape,
    # widest 0 (object entries), in the same order their offsets were assigned.
    for kname in layout.kind_spilled:
        members = kind_extents[kname]
        _append_word(layout.table, len(members))
        _append_word(layout.table, 0)
        for num in members:
            _append_word(layout.table, num)
    # Matrices: [count=live length, capacity, seed..., spare zeros]. The header
    # is a catalog's [count, widest] with the never-used-for-a-matrix `widest`
    # word repurposed to hold the CAPACITY: the mutators read it there so a
    # call carries at most three operands (the Z-machine call limit), and it is
    # genuinely useful at runtime. Every catalog read verb still works because
    # none reads the widest value, only the offsets around it. `count` starts
    # at the seed length and is mutated in place by append/remove; spare cells
    # up to capacity are zeros for append to grow into. Phase 1 backs every
    # cell (number, object, byte alike) with a word; byte packing lands with
    # the 2D work, so `of byte` here range-checks to 0..255 without yet halving
    # memory.
    for mname, mx in world.matrices.items():
        if mx.is_2d:
            # A 2D grid: rows * cols cells row-major, no header (the dimensions
            # are compile-time constants and every cell is live). Seed rows
            # fill from the top; the rest are zeros. Byte cells pack one per
            # byte (padded to a whole word); other cells are words.
            seeded = []
            for row in mx.seed_rows:
                seeded.extend(v.value for v in row)
            total = mx.rows * mx.cols
            if mx.cell == "byte":
                for k in range(total):
                    layout.table.append((seeded[k] if k < len(seeded) else 0) & 0xFF)
                if total % 2:  # pad to a whole word
                    layout.table.append(0)
            else:
                for k in range(total):
                    _append_word(layout.table, (seeded[k] if k < len(seeded) else 0) & 0xFFFF)
            continue
        _append_word(layout.table, len(mx.seed))
        _append_word(layout.table, mx.capacity)
        for v in mx.seed:
            if mx.cell == "object":
                _append_word(layout.table, layout.obj_number.get(v.ident, 0))
            else:  # number or byte
                _append_word(layout.table, v.value & 0xFFFF)
        for _ in range(mx.capacity - len(mx.seed)):
            _append_word(layout.table, 0)
    return layout


def _emit_table(world: wm.World, layout: Layout) -> None:
    table = layout.table
    n = len(world.obj_number) if False else len(layout.obj_number)
    # Whether to fill `feminine` from a name's spelling (Spanish only). German gets
    # its gender from the author's der/die/das, so spelling is never consulted.
    derive_gender = _spelling_gender_language(world)

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
        # Grammatical gender: when the author did not set `feminine`, derive it from
        # the name (a name ending in -a is feminine), so a Spanish pack reads it for
        # la/una with no author work. English never reads the bit.
        fem_num = layout.attr_number.get("feminine")
        if derive_gender and fem_num is not None and "feminine" not in eff:
            if _derive_feminine(eff.get("name")):
                table[entry + fem_num // 8] |= 0x80 >> (fem_num % 8)
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
    _emit_ambience_tables(world, layout)
    _emit_scoring_tables(world, layout)
    # A global initialized with a string holds its packed address; register
    # the text so build_story can seed the slot once addresses are known.
    for gname, g in world.globals.items():
        if isinstance(g.value, ast.StringLit):
            sid = f"glob@{gname}"
            layout.strings[sid] = _plain(g.value)
            layout.global_strings.append((gname, sid))


def _emit_scoring_tables(world, layout) -> None:
    """The rank ladder (docs/01, Scoring): a count word, then (threshold,
    title) word pairs; the titles are string fixups and the thresholds are
    patched in build_story, where the compiler-summed max_score is known
    (even spread, or the entry's pinned percent). A pool's LABEL is author
    documentation and appears in the compile ledger; it is not emitted into
    the story file (there is no runtime breakdown verb; a future breakdown
    granule would revive the pool table here)."""
    table = layout.table
    if world.ranks:
        layout.ranks_off = len(table)
        table += bytes(2)
        _put_word(table, layout.ranks_off, len(world.ranks))
        for i, (title, pin) in enumerate(world.ranks):
            pos = len(table)
            table += bytes(4)
            layout.rank_sites.append((pos, pin, i, len(world.ranks)))
            sid = f"rank@{pos}"
            layout.strings[sid] = title
            layout.string_fixups.append((pos + 2, sid))


def _emit_ambience_tables(world, layout) -> None:
    """Emit the ambience table (summon.ambience, docs/05): a count word, then a
    ten-word record per block. The record is live data in dynamic memory; the
    last two words are the driver's state (cadence odds and the last line).

      +0 owner object   +2 is_room        +4 mode (0 about, 1 every,
      +6 rate (0: dial) +8 line count        2 in order, 3 in order once)
      +10 block guard   +12 play routine  +14 line guards (each packed, 0 none)
      +16 odds state    +18 last state

    The routine addresses arrive by the same fixups the topic tables use."""
    blocks = [
        (name, idx, amb)
        for name, obj in world.objects.items()
        for idx, amb in enumerate(obj.ambiences)
    ]
    if not blocks:
        return
    table = layout.table
    layout.ambience_off = len(table)
    table += bytes(2)
    _put_word(table, layout.ambience_off, len(blocks))
    mode_num = {"about": 0, "every": 1, "order": 2}
    for name, idx, amb in blocks:
        rec = len(table)
        table += bytes(20)
        _put_word(table, rec + 0, layout.obj_number.get(name, 0))
        _put_word(table, rec + 2, 1 if world.objects[name].category == "room" else 0)
        mode = mode_num[amb.mode]
        if amb.mode == "order" and amb.once:
            mode = 3
        _put_word(table, rec + 4, mode)
        _put_word(table, rec + 6, amb.rate or 0)
        _put_word(table, rec + 8, len(amb.lines))
        if amb.when is not None:
            layout.routine_fixups.append((rec + 10, amb_guard_name(name, idx)))
        layout.routine_fixups.append((rec + 12, amb_play_name(name, idx)))
        if any(l.when is not None for l in amb.lines):
            layout.routine_fixups.append((rec + 14, amb_lg_name(name, idx)))


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
        if pname in ("words", "plural"):
            continue  # both emitted as word arrays below
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
    # The plural property (the plurals granule's group vocabulary) is an array
    # of dictionary addresses exactly like words.
    plural_prop = layout.prop_number.get("plural")
    if plural_prop is not None and "plural" in eff:
        pvocab = [v.ident.lower() for v in eff["plural"].values if isinstance(v, ast.Name)]
        if pvocab:
            items.append((plural_prop, "plural", pvocab))
    # A person with `topic` declarations gets a `topics` property holding a
    # pointer to its topic table; the table itself is appended after all property
    # tables (the pointer is patched there, so only its site is reserved here).
    topics_prop = layout.prop_number.get("topics")
    if topics_prop is not None and world.objects[name].topics:
        items.append((topics_prop, "topics", None))
    # The spans property: the extra rooms a fixed object is in scope in. Emitted
    # like `words` (an array of object numbers) but only for a non-movable object
    # (fixed or scenery); on a movable object spans is ignored (docs/01 section 5).
    spans_prop = layout.prop_number.get("spans")
    obj_spans = world.objects[name].spans
    nonmovable = ("fixed" in eff and _bool_value(eff["fixed"])) or (
        "scenery" in eff and _bool_value(eff["scenery"])
    )
    if spans_prop is not None and obj_spans and nonmovable:
        items.append((spans_prop, "spans", obj_spans))
    for pnum, pname, decl in sorted(items, reverse=True, key=lambda it: it[0]):
        if pname in ("words", "plural"):
            _emit_words(layout, pnum, decl)
            continue
        if pname == "spans":
            _emit_spans(layout, pnum, decl)
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


def _emit_spans(layout: Layout, pnum: int, room_names: list) -> None:
    """The spans property: an array of room object numbers (two bytes each), the
    extra rooms this object is in scope in. Same two-byte size form as `words`,
    but each entry is a room's object number, known now, so no fixup is needed."""
    length = len(room_names) * 2
    layout.table.append(0x80 | pnum)
    layout.table.append(0x80 | (length & 0x3F))
    for rname in room_names:
        num = layout.obj_number.get(rname, 0)
        layout.table.append((num >> 8) & 0xFF)
        layout.table.append(num & 0xFF)


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
        if decl.form == ast.PROP_VALUE and decl.values:
            v = decl.values[0]
            if isinstance(v, ast.Number):
                value = v.value & 0xFFFF
            elif isinstance(v, ast.Name) and v.ident in layout.catalogs:
                # A catalog name stands for its word offset (sema typed the
                # property as number for exactly this), so the slot reads
                # back as the same small constant the name means in code.
                value = layout.catalogs[v.ident] & 0xFFFF
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


def _append_word(buf: bytearray, value: int) -> None:
    buf.append((value >> 8) & 0xFF)
    buf.append(value & 0xFF)


def _put_word(buf: bytearray, off: int, value: int) -> None:
    buf[off] = (value >> 8) & 0xFF
    buf[off + 1] = value & 0xFF


def _err(msg: str):
    from .errors import ArcError

    return ArcError(msg)
