# sema.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Semantic analysis: AST to the checked world-model IR.

Passes, in order:

1. collect    - gather game declarations (game block, kinds, objects, verbs,
                globals, constants, blocks, free-standing handlers, summons)
                into the World; report duplicate names.
2. kinds      - resolve each object's and kind's inheritance chain; report
                unknown parents and cycles.
3. properties - fix every property's type program-wide from its declarations,
                report a type clash naming both sites, and record the
                provisional storage (attribute candidate or slot).
4. bodies     - resolve names and check statements and expressions: mutate
                only declared properties, conditions must be boolean, resolve
                each `is` test as a property test or an equality, and validate
                handler events and operands.

The analyzer is parameterized by a prelude.Environment, so nothing about the
Cosmos standard library is hardcoded here.
"""

from __future__ import annotations

import dataclasses
import sys
from typing import Optional

from . import ast
from . import prelude
from . import worldmodel as wm
from .errors import ArcError


# The standard kinds an object IS rather than has (Stefan's ruling,
# 2026-08-24): never grantable as a bare attribute line or through `now`.
# Testing membership (`if noun is supporter`) stays ordinary; only the
# grant is refused, with the kind declaration named as the cure.
_KIND_NOT_ATTRIBUTE = frozenset(
    ("container", "supporter", "door", "character", "room", "thing")
)


class Analyzer:
    def __init__(
        self,
        program: ast.Program,
        env: Optional[prelude.Environment] = None,
        filename: str = "<source>",
    ) -> None:
        self.program = program
        self.env = env if env is not None else prelude.standard_environment()
        self._expired_lets: set = set()
        self.filename = filename
        self.world = wm.World()
        # Every property name the story's code READS (a dot access, or the
        # right side of an is-test): the unread-property note compares the
        # set props against it (see _lint_unread_props).
        self.prop_reads: set = set()
        # player.<prop> augmentations, applied to the seeded player object in
        # the properties pass.
        self._player_decls: list = []

    def _error(self, message: str, line: int) -> ArcError:
        return ArcError(message, line, None, self.filename)

    # -- entry -------------------------------------------------------------

    def analyze(self) -> wm.World:
        self._normalize_aliases()
        self._collect()
        # An object's category follows its kind chain: `thing parlor of
        # lounge`, where lounge is a kind OF ROOM, makes parlor a ROOM in
        # every respect (spans, exits, the start room, the room table),
        # exactly as if the room keyword had been used. The keyword is a
        # reading aid; the chain is the truth. (A field report: a spanned
        # instance of a room kind was refused as "not a room".)
        for obj in self.world.objects.values():
            if obj.category != "room" and self._rooted_in_room(obj.kind):
                obj.category = "room"
        self._resolve_kinds()
        # Catalog object entries must name real objects (checked here, after
        # every object is collected, so declaration order never matters). A
        # name that is no object but IS a direction reclassifies the catalog
        # as a DIRECTION catalog: each cell is the direction's property
        # number, the matrix precedent (a maze route, a patrol path), read
        # with the same verbs and compared with `if d is north`. Story names
        # win as everywhere: an object named north stays an object entry.
        for cat in self.world.catalogs.values():
            if cat.etype == "object":
                objs = [v for v in cat.values if v.ident in self.world.objects]
                dirs = [v for v in cat.values
                        if v.ident not in self.world.objects
                        and v.ident in self.env.directions]
                unknown = [v for v in cat.values
                           if v.ident not in self.world.objects
                           and v.ident not in self.env.directions]
                if unknown:
                    raise self._error(
                        f"catalog '{cat.name}': '{unknown[0].ident}' is not "
                        f"an object or a direction",
                        cat.line,
                    )
                if dirs and objs:
                    raise self._error(
                        f"catalog '{cat.name}' mixes object and direction "
                        f"entries; a catalog holds one type of value",
                        cat.line,
                    )
                if dirs:
                    cat.etype = "direction"
        # Matrix is strictly a summoned feature: a declaration is inert without
        # summon.matrix, and object-cell seeds must name real objects (checked
        # here, after every object is collected).
        if self.world.matrices and not self._has_summon("matrix"):
            first = next(iter(self.world.matrices.values()))
            raise self._error(
                "a matrix needs the granule: add summon.matrix", first.line)
        for mx in self.world.matrices.values():
            if mx.cell == "object":
                for v in mx.seed:
                    if v.ident not in self.world.objects:
                        raise self._error(
                            f"matrix '{mx.name}': '{v.ident}' is not an object",
                            mx.line)
            elif mx.cell == "direction":
                for v in mx.seed:
                    if getattr(v, "ident", None) is not None \
                            and v.ident not in self.env.directions:
                        raise self._error(
                            f"matrix '{mx.name}': '{v.ident}' is not a "
                            f"direction",
                            mx.line)
        self._build_properties()
        # Exits are validated once the members are on their objects (the
        # properties pass just filled obj.props) and the kind chains are
        # resolved (door detection).
        self._check_exits()
        self._check_locations()
        self._check_presence()
        self._check_npcengine()
        self._check_maniacswap()
        # After the members are collected: the automatic scored bits need
        # the real attributes (fixed blocks a thing, `scored false` opts
        # out), and the award scan feeds the compiler-summed max_score.
        self._auto_score()
        self._resolve_bodies()
        self._scan_awards()
        self._lint_unread_props()
        self._lint_alter_without_continue()
        self._lint_nautical_land_start()
        self._resolve_subjects()
        self._lint_self_perform()
        self._lint_grain_word_split()
        # A summoned abbreviations.granule (B6) is compile-time data, not runtime
        # blocks, so it rides on the program straight through to codegen.
        self.world.abbreviations = getattr(self.program, "abbreviations", None)
        # The direction property names (the standard set plus any declared), so
        # codegen may allow a COMPUTED exit (a direction property that is a
        # block) while a general computed value property stays unsupported.
        self.world.direction_props = set(self.env.directions)
        # The same set in declaration order (standard first, then customs as
        # declared), for everything that emits per-direction rows.
        self.world.direction_order = list(self.env.directions)
        # Does any `now ... is beyond` appear? The any_beyond fold must flip for
        # a game that never DECLARES beyond on an object but sets it at runtime
        # (the player-beyond mount: `now player is beyond` and nothing else), or
        # the touch guards would fold away and the bit would set silently.
        self.world.sets_beyond = self._sets_attr("beyond")
        self.world.sets_shiftable = self._sets_attr("shiftable")
        self.world.sets_restless = self._sets_attr("restless")
        self.world.uses_notify = getattr(self.program, "uses_notify", False)
        # Darkness reachability (arc_image_dark, B11): darkness can happen when
        # any room resolves `lit` to false at compile time (its own `lit false`
        # or an inherited kind default), or when any statement clears `lit` at
        # runtime. any_dark folds the draw path's darkness branch away when it
        # cannot happen; when it can, an images game must declare the picture
        # the band shows in the dark (Stefan's rule: darkness is a scene too,
        # so it gets a picture, never a stale leftover from the last lit room).
        dark_room = self._first_dark_room()
        self.world.uses_darkness = (
            dark_room is not None
            or self._sets_attr("lit", negated=True, skip_library=True)
        )
        if (
            self.world.uses_images
            and self.world.uses_darkness
            and "arc_image_dark" not in self.world.constants
        ):
            where = (
                f"room '{dark_room.name}' can be dark"
                if dark_room is not None
                else "a handler clears `lit` at runtime"
            )
            raise self._error(
                f"this game has pictures and darkness ({where}). Darkness is "
                f"a scene too, so give it one: declare `constant "
                f"arc_image_dark = <id>` with the picture the band shows in "
                f"the dark",
                dark_room.line if dark_room is not None else 0,
            )
        return self.world

    # The requirement bit per (slot, kind): the packed word requires_map
    # returns, read arithmetically by the loop's check (docs/01 chapter 13).
    _REQUIRE_BITS = {
        ("noun", "carried"): 1,
        ("noun", "animate"): 2,
        ("second", "carried"): 4,
        ("second", "animate"): 8,
    }

    def _add_requirement(self, action: str, r: "ast.RequiresDecl") -> None:
        bit = self._REQUIRE_BITS.get((r.slot, r.kind))
        if bit is None:
            kinds = sorted({k for _, k in self._REQUIRE_BITS})
            raise self._error(
                f"requires knows {', '.join(kinds)}; '{r.kind}' is not one "
                f"of them (slot '{r.slot}')",
                r.line,
            )
        self.world.requirements[action] = (
            self.world.requirements.get(action, 0) | bit
        )

    def _find_verb(self, word: str, line: int, what: str):
        """The existing verb owning this word, latest declaration first (the
        most specific one is the one an author means to touch)."""
        for verb in reversed(self.world.verbs):
            if word in verb.words:
                return verb
        raise self._error(
            f'{what} verb: no verb "{word}" exists yet; declare it with '
            f"`verb` first",
            line,
        )

    def _first_dark_room(self):
        """The first room whose `lit` resolves false at compile time: its own
        override, or the nearest kind in its chain that says `lit false` (the
        room kind itself defaults lit, so an untouched room is never dark)."""
        for obj in self.world.objects.values():
            if obj.category != "room" or obj.name == "scope":
                continue
            decl = obj.props.get("lit")
            if decl is None:
                for kname in obj.chain:
                    kind = self.world.kinds.get(kname)
                    if kind is not None and "lit" in kind.props:
                        decl = kind.props["lit"]
                        break
            if (
                decl is not None
                and decl.form == ast.PROP_VALUE
                and decl.values
                and isinstance(decl.values[0], ast.Bool)
                and decl.values[0].value is False
            ):
                return obj
        return None

    # -- pass 1: collect ---------------------------------------------------

    def _moves_to_scope(self, nodes) -> bool:
        """Does any `move ... to scope` appear in the program? A generic
        dataclass walk over the declarations and their bodies; when found,
        the backstage scope room is seeded so the name resolves."""
        found = [False]

        def visit(node):
            if isinstance(node, ast.Move) and isinstance(
                node.dest, ast.Name
            ) and node.dest.ident == "scope":
                found[0] = True
                return
            if not dataclasses.is_dataclass(node):
                return
            for f in dataclasses.fields(node):
                v = getattr(node, f.name)
                if isinstance(v, list):
                    for item in v:
                        if dataclasses.is_dataclass(item):
                            visit(item)
                elif dataclasses.is_dataclass(v):
                    visit(v)

        for n in nodes:
            if found[0]:
                break
            visit(n)
        return found[0]

    def _changes_prop_of(self, objname: str, prop: str) -> bool:
        """Does any `change <objname>.<prop> to ...` appear in the program?
        The same generic walk; used to auto-allocate a runtime-written
        property slot (player.beyond_why) so the write cannot halt."""
        found = [False]

        def visit(node):
            if (isinstance(node, ast.Change)
                    and isinstance(node.target, ast.Dot)
                    and isinstance(node.target.obj, ast.Name)
                    and node.target.obj.ident == objname
                    and node.target.prop == prop):
                found[0] = True
                return
            if not dataclasses.is_dataclass(node):
                return
            for f in dataclasses.fields(node):
                v = getattr(node, f.name)
                if isinstance(v, list):
                    for item in v:
                        if dataclasses.is_dataclass(item):
                            visit(item)
                elif dataclasses.is_dataclass(v):
                    visit(v)

        for n in self.program.decls:
            if found[0]:
                break
            visit(n)
        return found[0]

    def _normalize_aliases(self) -> None:
        """Rewrite property-name aliases across the whole program before any
        pass reads a name: `switchable` becomes `binary` (the binary model;
        one property, one attribute, two spellings) wherever it appears - a
        declaration line, an `is` test, a `now`, a when-clause. Shipped
        games keep compiling; every later pass sees only the canon."""
        import dataclasses

        def visit(node):
            if isinstance(node, ast.Name) and node.ident == "switchable":
                node.ident = "binary"
            if isinstance(node, ast.PropertyDecl) and node.name == "switchable":
                node.name = "binary"
            if isinstance(node, ast.Now) and node.prop == "switchable":
                node.prop = "binary"
            if not dataclasses.is_dataclass(node):
                return
            for f in dataclasses.fields(node):
                v = getattr(node, f.name)
                if isinstance(v, list):
                    for item in v:
                        if dataclasses.is_dataclass(item):
                            visit(item)
                elif dataclasses.is_dataclass(v):
                    visit(v)

        for n in self.program.decls:
            visit(n)

    def _sets_attr(self, attr: str, negated: bool = False,
                   skip_library: bool = False) -> bool:
        """Does any `now ... is <attr>` (or, with negated=True, `now ... is
        not <attr>`) appear in the program? The same generic walk as
        _moves_to_scope; used to flip a compile-time any_X fold for an
        attribute state that is only ever reached at runtime, never declared
        (set for beyond; cleared for lit, where clearing is what makes
        darkness reachable in an otherwise lit game). skip_library ignores
        library-origin declarations: Cosmos itself clears thing-lit in the
        binary model's glow coupling, which can only ever produce darkness
        alongside a dark-capable room, and the dark-room half of the
        darkness test already catches that; without the skip, every game
        would carry the light watch for a branch that folds away."""
        found = [False]

        def visit(node):
            if isinstance(node, ast.Now) and node.prop == attr \
                    and node.negated == negated:
                found[0] = True
                return
            if not dataclasses.is_dataclass(node):
                return
            for f in dataclasses.fields(node):
                v = getattr(node, f.name)
                if isinstance(v, list):
                    for item in v:
                        if dataclasses.is_dataclass(item):
                            visit(item)
                elif dataclasses.is_dataclass(v):
                    visit(v)

        for n in self.program.decls:
            if found[0]:
                break
            if skip_library and getattr(n, "origin", None) == "library":
                continue
            visit(n)
        return found[0]

    def _seen(self, name: str, line: int) -> None:
        if (
            name in self.world.objects
            or name in self.world.kinds
            or name in self.world.globals
            or name in self.world.constants
            or name in self.world.blocks
            or name in self.world.catalogs
            or name in self.world.matrices
        ):
            raise self._error(f"duplicate declaration of '{name}'", line)

    def _has_summon(self, target: str) -> bool:
        # Was a feature summoned (summon.<target>)? Used to gate features that
        # are inert without their granule, e.g. summon.matrix.
        return any(
            s.form == "feature" and s.target == target
            for s in self.world.summons
        )

    def _register_custom_directions(self) -> None:
        """Author-declared direction properties (Stefan's ruling, 2026-07-28):
        a `direction` declaration naming a property outside the standard set
        CREATES that direction, first-class: bare typed word, exits, `on go`
        handlers, `way`, the exit list, everything the compass has. Each one
        consumes a Z-machine property slot when a room uses it (the stock and
        the hard ceiling show in `arcc -s`); declared and never walked it
        costs only its dictionary words, and a game that declares none is
        byte-identical to one built before the feature existed. Registered in
        a pre-pass so a custom direction works in catalogs, matrices, and
        exits regardless of where in the source it is declared."""
        for decl in self.program.decls:
            if not isinstance(decl, ast.DirectionDecl):
                continue
            prop = decl.prop
            if self.env.is_direction(prop):
                continue
            if prop in self.env.properties:
                raise self._error(
                    f"'{prop}' cannot become a direction: it is already a "
                    f"standard property", decl.line)
            self.env.properties[prop] = prelude.StdProp(prop, prelude.T_OBJECT)
            self.env.directions.append(prop)

    def _collect(self) -> None:
        w = self.world
        self._register_custom_directions()
        # Seed standard kinds so the chain resolves against Cosmos.
        for sk in self.env.kinds.values():
            kind = wm.Kind(sk.name, sk.parent, "standard")
            # Universal kind defaults: only attributes true for essentially every
            # instance of the kind (a bowl is a container that never opens, so
            # `openable` is NOT a container default). All override per instance.
            # Rooms are lit; characters are animate; a door opens and is fixed in
            # place (its lock, if any, is per instance).
            if sk.name == "room":
                kind.props["lit"] = ast.PropertyDecl(name="lit", form=ast.PROP_BOOL)
            elif sk.name == "character":
                kind.props["animate"] = ast.PropertyDecl(name="animate", form=ast.PROP_BOOL)
            elif sk.name == "door":
                kind.props["openable"] = ast.PropertyDecl(name="openable", form=ast.PROP_BOOL)
                kind.props["fixed"] = ast.PropertyDecl(name="fixed", form=ast.PROP_BOOL)
            w.kinds[sk.name] = kind
        # Seed standard objects (player).
        for name, kind in self.env.objects.items():
            w.objects[name] = wm.Obj(name, "thing", kind, line=0)
        # Seed the scope room on demand (docs/01 chapter 3, Stefan's design):
        # `in scope` places an object BACKSTAGE, an invisible room whose
        # contents the parser always has in scope. Nothing is seeded, and
        # nothing costs a byte, unless some object asks for it, EITHER by a
        # `in scope` placement OR by a `move ... to scope` anywhere in the
        # code (revealing something into scope at run time, the frisk idiom).
        # A field report: move-to-scope without a placement failed with
        # "unknown name 'scope'", which was mechanically wrong.
        needs_scope = any(
            isinstance(d, ast.ObjectDecl) and d.location == "scope"
            for d in self.program.decls
        ) or self._moves_to_scope(self.program.decls)
        if needs_scope and "scope" not in w.objects:
            w.objects["scope"] = wm.Obj("scope", "room", "room", line=0)

        for decl in self.program.decls:
            if isinstance(decl, ast.GameBlock):
                if w.game is not None:
                    raise self._error("more than one game block", decl.line)
                w.game = decl
                for m in decl.meta:
                    if m.key == "start":
                        w.start_room = m.value
            elif isinstance(decl, ast.Summon):
                w.summons.append(decl)
            elif isinstance(decl, ast.KindDecl):
                self._seen(decl.name, decl.line)
                w.kinds[decl.name] = wm.Kind(
                    decl.name, decl.parent, "game", decl=decl, line=decl.line
                )
            elif isinstance(decl, ast.ObjectDecl):
                self._seen(decl.name, decl.line)
                w.objects[decl.name] = wm.Obj(
                    decl.name,
                    decl.category,
                    decl.parent or decl.category,
                    location=decl.location,
                    presence=list(decl.presence),
                    spans=list(decl.spans),
                    decl=decl,
                    line=decl.line,
                )
            elif isinstance(decl, ast.SubjectDecl):
                if decl.name in w.subjects:
                    raise self._error(
                        f"subject '{decl.name}' is declared twice", decl.line)
                if not decl.words:
                    raise self._error(
                        f"subject '{decl.name}' needs `words`: they are what "
                        f"the whole cast matches when the player raises it",
                        decl.line)
                w.subjects[decl.name] = decl
            elif isinstance(decl, ast.CatalogDecl):
                self._seen(decl.name, decl.line)
                values = [self._const_text(v) for v in decl.values]
                etype = None
                for v in values:
                    if isinstance(v, ast.StringLit):
                        vt = "text"
                    elif isinstance(v, ast.Number):
                        vt = "number"
                    elif isinstance(v, ast.Name):
                        vt = "object"
                    else:
                        raise self._error(
                            f"catalog '{decl.name}': an entry must be a "
                            f"string, a number, or an object name",
                            decl.line,
                        )
                    if etype is None:
                        etype = vt
                    elif vt != etype:
                        raise self._error(
                            f"catalog '{decl.name}' mixes {etype} and {vt} "
                            f"entries; a catalog holds one type of value",
                            decl.line,
                        )
                    if vt == "text" and any(
                        not isinstance(p, ast.StringText) for p in v.parts
                    ):
                        raise self._error(
                            f"catalog '{decl.name}': an entry is a static "
                            f"string, so ${{...}} interpolation cannot run "
                            f"in it",
                            decl.line,
                        )
                w.catalogs[decl.name] = wm.Catalog(
                    decl.name, etype, values, decl.line
                )
            elif isinstance(decl, ast.MatrixDecl):
                self._seen(decl.name, decl.line)

                def _check_val(v, mname=decl.name, cell=decl.cell, ln=decl.line):
                    # A matrix cell value: an object name for object cells, a
                    # direction name for direction cells, else a number
                    # (matrices are numeric, never text).
                    if cell == "object":
                        if not isinstance(v, ast.Name):
                            raise self._error(
                                f"matrix '{mname}' holds objects; a value must "
                                f"be an object name", ln)
                    elif cell == "direction":
                        if not isinstance(v, ast.Name) \
                                or v.ident not in self.env.directions:
                            got = getattr(v, "ident", None) or getattr(
                                v, "value", "?")
                            raise self._error(
                                f"matrix '{mname}' holds directions; "
                                f"'{got}' is not a direction", ln)
                    else:
                        if not isinstance(v, ast.Number):
                            raise self._error(
                                f"matrix '{mname}' holds numbers; a value must "
                                f"be a number (matrices are numeric, never "
                                f"text: use a catalog for words)", ln)
                        if cell == "byte" and not 0 <= v.value <= 255:
                            raise self._error(
                                f"matrix '{mname}' is of byte; {v.value} is "
                                f"outside 0..255", ln)

                if decl.rows > 0:  # 2D grid
                    if decl.cols < 1:
                        raise self._error(
                            f"matrix '{decl.name}': a 2D matrix needs at least "
                            f"one column", decl.line)
                    if decl.cell == "object":
                        raise self._error(
                            f"matrix '{decl.name}': a 2D matrix holds numbers "
                            f"or bytes, not objects", decl.line)
                    if len(decl.seed_rows) > decl.rows:
                        raise self._error(
                            f"matrix '{decl.name}': {len(decl.seed_rows)} seed "
                            f"rows exceed the {decl.rows} rows", decl.line)
                    seed_rows = []
                    for r in decl.seed_rows:
                        if len(r) != decl.cols:
                            raise self._error(
                                f"matrix '{decl.name}': a seed row has {len(r)} "
                                f"values but the matrix has {decl.cols} columns",
                                decl.line)
                        row = [self._const_text(v) for v in r]
                        for v in row:
                            _check_val(v)
                        seed_rows.append(row)
                    w.matrices[decl.name] = wm.Matrix(
                        decl.name, decl.cell, 0, [], decl.checked, decl.line,
                        rows=decl.rows, cols=decl.cols, seed_rows=seed_rows)
                else:  # 1D sequence
                    if decl.capacity < 1:
                        raise self._error(
                            f"matrix '{decl.name}': capacity must be at least 1",
                            decl.line)
                    if len(decl.seed) > decl.capacity:
                        raise self._error(
                            f"matrix '{decl.name}': {len(decl.seed)} seed values "
                            f"exceed the capacity of {decl.capacity}", decl.line)
                    seed = [self._const_text(v) for v in decl.seed]
                    for v in seed:
                        _check_val(v)
                    w.matrices[decl.name] = wm.Matrix(
                        decl.name, decl.cell, decl.capacity, seed,
                        decl.checked, decl.line)
            elif isinstance(decl, ast.VerbDecl):
                grammar = [wm.GrammarLine(g.action, g.items, g.reverse) for g in decl.grammar]
                if decl.mode == "enhance":
                    # `enhance verb "take", "snatch"`: append to the existing
                    # verb, new grammar lines and new synonym words alike; the
                    # anchor is the first word, which must already be a verb.
                    target = self._find_verb(decl.words[0], decl.line, "enhance")
                    for word in decl.words:
                        if word not in target.words:
                            target.words.append(word)
                    target.grammar.extend(grammar)
                    bind_to = {g.action for g in target.grammar}
                elif decl.mode == "redefine":
                    # `redefine verb "give"`: replace the existing verb WHOLE,
                    # words included, and say so out loud. The old synonyms go
                    # with it (the silent per-word shadowing this replaces
                    # left them pointing at the old grammar). The action's
                    # requirements are contract, not wording, and stand until
                    # a requires line changes them.
                    if not grammar:
                        raise self._error(
                            "redefine verb replaces the grammar, so it needs "
                            "grammar lines (enhance verb adds without them)",
                            decl.line,
                        )
                    target = self._find_verb(decl.words[0], decl.line, "redefine")
                    target.words = list(decl.words)
                    target.grammar = grammar
                    bind_to = {g.action for g in grammar}
                else:
                    # A plain redeclaration of an existing verb word shadows
                    # word by word, silently and confusingly (the old verb's
                    # OTHER synonyms keep their old meaning). Say so, and name
                    # the forms that state intent.
                    owner = None
                    for existing in w.verbs:
                        if any(word in existing.words for word in decl.words):
                            owner = existing
                            break
                    if owner is not None:
                        print(
                            f"arcc: note: verb \"{decl.words[0]}\" already "
                            f"exists; this declaration shadows it word by "
                            f"word. `redefine verb` replaces it whole and "
                            f"says so; `enhance verb` adds to it.",
                            file=sys.stderr,
                        )
                    w.verbs.append(wm.Verb(decl.words, grammar, decl.line))
                    bind_to = {g.action for g in decl.grammar}
                # `verb ... meta`: its actions join the out-of-world band
                # (dispatched past every object handler, `on other` included).
                if decl.meta:
                    for g in decl.grammar:
                        w.meta_actions.add(g.action)
                # In-body `requires noun carried` binds to this verb's own
                # actions (the sugar form; the top-level form names one).
                for r in decl.requirements:
                    for act in bind_to:
                        self._add_requirement(act, r)
            elif isinstance(decl, ast.RequiresDecl):
                self._add_requirement(decl.action, decl)
            elif isinstance(decl, ast.DirectionDecl):
                if not self.env.is_direction(decl.prop):
                    raise self._error(
                        f"'{decl.prop}' is not a standard direction property",
                        decl.line,
                    )
                for word in decl.words:
                    w.directions[word.lower()] = decl.prop
                # The canonical word a property answers to: the first word of
                # its first declaration, unless the game itself redeclares
                # (most specific wins). A granule ADDING vocabulary to a
                # worded property (nautical's ALOFT riding up) never steals
                # the canonical; a game rebinding a spare property does.
                if decl.words:
                    if decl.prop not in w.direction_names or decl.origin == "game":
                        w.direction_names[decl.prop] = decl.words[0].lower()
            elif isinstance(decl, ast.PlayerDecl):
                # Collected now, applied in the properties pass (below), where
                # types unify and the words lists merge.
                self._player_decls.append(decl.prop)
            elif isinstance(decl, ast.PronounDecl):
                for role in decl.roles:
                    if role not in prelude._PRONOUN_ROLES:
                        roles = ", ".join(prelude._PRONOUN_ROLES)
                        raise self._error(
                            f"'{role}' is not a pronoun role (use one of: "
                            f"{roles})",
                            decl.line,
                        )
                if len(decl.roles) == 1:
                    for word in decl.words:
                        w.pronouns[word.lower()] = decl.roles[0]
                else:
                    # A multi-role word (the German dative "ihm"): the pair
                    # maps to its own role id, resolved by recency in the
                    # skeleton. Only the declared combinations exist; a new
                    # one is added deliberately, never guessed.
                    key = tuple(sorted(decl.roles))
                    rid = prelude._PRONOUN_ROLE_SETS.get(key)
                    if rid is None:
                        raise self._error(
                            f"the pronoun role combination "
                            f"({', '.join(decl.roles)}) is not supported",
                            decl.line,
                        )
                    for word in decl.words:
                        w.pronoun_sets[word.lower()] = rid
                    w.uses_pronoun_sets = True
            elif isinstance(decl, ast.ParticleDecl):
                if decl.role not in prelude._PARTICLE_ROLES:
                    roles = ", ".join(prelude._PARTICLE_ROLES)
                    raise self._error(
                        f"'{decl.role}' is not a particle role (use one of: {roles})",
                        decl.line,
                    )
                for word in decl.words:
                    w.particles[word.lower()] = decl.role
            elif isinstance(decl, ast.ChainDecl):
                for word in decl.words:
                    if word.lower() not in w.chain_words:
                        w.chain_words.append(word.lower())
            elif isinstance(decl, ast.AllDecl):
                for word in decl.words:
                    if word.lower() not in w.all_words:
                        w.all_words.append(word.lower())
            elif isinstance(decl, ast.RanksDecl):
                if w.ranks:
                    raise self._error("more than one ranks ladder", decl.line)
                for title, pin in decl.entries:
                    if pin is not None and pin[0] == "percent" and not (0 <= pin[1] <= 100):
                        raise self._error(
                            f"a percent rank pin runs 0 to 100, got {pin[1]}",
                            decl.line,
                        )
                w.ranks = list(decl.entries)
            elif isinstance(decl, ast.NoiseDecl):
                for word in decl.words:
                    if word.lower() not in w.noise_words:
                        w.noise_words.append(word.lower())
            elif isinstance(decl, ast.FoldDecl):
                if (decl.src, decl.dst) not in w.folds:
                    w.folds.append((decl.src, decl.dst))
            elif isinstance(decl, ast.ActionDecl):
                for name in decl.names:
                    if name not in w.declared_actions:
                        w.declared_actions.append(name)
            elif isinstance(decl, ast.GlobalDecl):
                self._seen(decl.name, decl.line)
                role = getattr(decl, "role", "global")
                vt = self._value_type(decl.value)
                if role == "flag" and vt != prelude.T_BOOL:
                    raise self._error(
                        f"a flag starts true or false; '{decl.name}' was given "
                        "something else (use `counter` or `global`)",
                        decl.line,
                    )
                if role == "counter" and vt != prelude.T_NUMBER:
                    raise self._error(
                        f"a counter starts at a number; '{decl.name}' was given "
                        "something else (use `flag` or `global`)",
                        decl.line,
                    )
                w.globals[decl.name] = wm.Global(
                    decl.name, vt, decl.value, decl.line, role
                )
            elif isinstance(decl, ast.ConstantDecl):
                self._seen(decl.name, decl.line)
                # arc_image (B11): arc_mode is the game's picture mode, the band
                # height in text rows. Only 9 (Infocom mode) and 12 (DAAD mode)
                # exist, so a bad value is a clear error here rather than a wrong
                # band on an interpreter that trusts the mode.
                if decl.name == "arc_mode" and not (
                    isinstance(decl.value, ast.Number)
                    and decl.value.value in (9, 12)
                ):
                    raise self._error(
                        "arc_mode must be 9 (Infocom mode, 320x72) or 12 "
                        "(DAAD mode, 320x96)",
                        decl.line,
                    )
                # arc_image_dark is the darkness picture: a real resource id,
                # bounded exactly like a room's arc_image (0 is the clear code,
                # so it cannot be a picture).
                if decl.name == "arc_image_dark" and not (
                    isinstance(decl.value, ast.Number)
                    and 1 <= decl.value.value <= 0xFFFF
                ):
                    raise self._error(
                        "arc_image_dark must be a picture id, 1 to 65535 "
                        "(the picture the band shows in the dark)",
                        decl.line,
                    )
                w.constants[decl.name] = wm.Constant(
                    decl.name, self._value_type(decl.value), decl.value, decl.line
                )
            elif isinstance(decl, ast.BlockDecl):
                prior = w.blocks.get(decl.name)
                # Most-specific-wins, the chain complete: a game block
                # overrides a granule block overrides a library block of the
                # same name (combined_program loads in that order). Messages
                # (msg_*, line_*) are a granule's public skin and reskin
                # silently; capturing any OTHER granule block gets a note,
                # since colliding with a granule's internal helper by accident
                # breaks the granule mysteriously (the reason the old rule
                # forbade this outright). A repeat at the same origin is a
                # genuine duplicate.
                rank = {"library": 0, "granule": 1, "game": 2}
                new_r = rank.get(decl.origin, 2)
                prior_r = rank.get(prior.origin, 2) if prior is not None else -1
                if prior is not None and new_r < prior_r:
                    # The more specific block already won (a game chapter
                    # loaded before the granule it overrides): the less
                    # specific late arrival is simply not taken.
                    pass
                elif prior is not None and new_r > prior_r:
                    if prior.origin == "granule" and not (
                        decl.name.startswith("msg_")
                        or decl.name.startswith("line_")
                    ):
                        print(
                            f"arcc: note: block '{decl.name}' replaces a "
                            f"summoned granule's block of the same name; if "
                            f"this is not a deliberate override, rename "
                            f"yours (the granule may depend on its own)",
                            file=sys.stderr,
                        )
                    w.blocks[decl.name] = wm.Block(
                        decl.name, decl.params, decl.body, decl.line, decl.origin
                    )
                else:
                    self._seen(decl.name, decl.line)
                    w.blocks[decl.name] = wm.Block(
                        decl.name, decl.params, decl.body, decl.line, decl.origin
                    )
            elif isinstance(decl, ast.Handler):
                w.free_handlers.append(self._make_handler(decl, None, False))
            elif isinstance(decl, ast.GrainsAttach):
                # Attach grains to an existing object (resolved in pass 4).
                pass

        # Actions: the standard set, every action a verb grammar names, and
        # the bare `action` declarations (verbless actions: reachable by
        # dispatch and remap, never from the keyboard directly).
        w.actions = set(self.env.actions)
        for verb in w.verbs:
            for line in verb.grammar:
                w.actions.add(line.action)
        w.actions.update(w.declared_actions)

        # A reversed PREPOSITIONAL line (`fill noun with noun reverse`, the
        # pour phrasing) rides the flag model as one summary bit per verb, so
        # a flag-model verb must be all-of-one-mind about it: mixing a
        # reversed and an unreversed two-noun line under one verb word is a
        # thing one bit cannot say. Give the orders separate verb
        # declarations sharing the action (fill / pour), which is also how
        # they read.
        for verb in w.verbs:
            if wm.needs_table(verb):
                continue
            two_noun = [
                line for line in verb.grammar
                if sum(1 for it in line.items
                       if isinstance(it, ast.Slot)) == 2
                and any(isinstance(it, ast.Word) for it in line.items)
            ]
            if (any(line.reverse for line in two_noun)
                    and any(not line.reverse for line in two_noun)):
                raise self._error(
                    f"verb '{verb.words[0]}': its prepositional two-noun "
                    f"lines mix `reverse` and plain order; one verb word "
                    f"binds one order, so give the reversed order's words "
                    f"their own declaration naming the same action",
                    verb.line,
                )

        # A verb whose grammar the flag model cannot represent gets a positional
        # grammar table (docs/01 chapter 14). The table matcher walks each line
        # token by token, so a few shapes the classic splitter tolerated by
        # accident are checked honestly here.
        for verb in w.verbs:
            if not wm.needs_table(verb):
                continue
            head = verb.words[0]
            for phrase in verb.words:
                if len(phrase.split()) != 1:
                    raise self._error(
                        f"verb '{head}': positional grammar (a literal before "
                        f"the first noun, or wording that selects the action) "
                        f"needs single-word verb synonyms; '{phrase}' has more",
                        verb.line,
                    )
            for line in verb.grammar:
                # A `direction` slot consumes exactly one direction word (SWIM
                # SOUTH, PUSH CRATE WEST); the value rides `way`, as with go.
                # It is not a noun slot, so it is excluded from the noun-slot
                # rules below, and it must close its line: a direction word is
                # where an English movement phrase ends, and the matcher uses
                # it as the boundary that stops a noun phrase.
                dirs = [it for it in line.items
                        if isinstance(it, ast.Slot) and it.kind == "direction"]
                if len(dirs) > 1:
                    raise self._error(
                        f"verb '{head}': a grammar line takes at most one "
                        f"`direction` slot",
                        verb.line,
                    )
                if dirs and (not isinstance(line.items[-1], ast.Slot)
                             or line.items[-1].kind != "direction"):
                    raise self._error(
                        f"verb '{head}': a `direction` slot must be the last "
                        f"item on its line, like '{line.action} noun direction'",
                        verb.line,
                    )
                slots = [it for it in line.items
                         if isinstance(it, ast.Slot) and it.kind != "direction"]
                if len(slots) > 2:
                    raise self._error(
                        f"verb '{head}': a grammar line takes at most two noun "
                        f"slots",
                        verb.line,
                    )
                absorbs = [it for it in slots
                           if it.kind in ("text", "letters", "number",
                                          "anychar")]
                if len(absorbs) > 1:
                    raise self._error(
                        f"verb '{head}': one absorbing slot per line (text, "
                        f"letters, number, or anychar); two would fight over "
                        f"the same input",
                        verb.line,
                    )
                if line.reverse:
                    raise self._error(
                        f"verb '{head}': `reverse` is not available on a verb "
                        f"with positional grammar; give the reversed order its "
                        f"own line with a literal word instead",
                        verb.line,
                    )
                for a, b in zip(line.items, line.items[1:]):
                    if (isinstance(a, ast.Slot) and isinstance(b, ast.Slot)
                            and a.kind != "direction" and b.kind != "direction"):
                        raise self._error(
                            f"verb '{head}': in positional grammar two noun "
                            f"slots need a literal word between them, like "
                            f"'{line.action} noun with noun'",
                            verb.line,
                        )

    def _make_handler(
        self, decl: ast.Handler, owner: Optional[str], on_kind: bool
    ) -> wm.Handler:
        return wm.Handler(
            decl.events,
            decl.after,
            decl.pattern,
            decl.when,
            decl.body,
            owner,
            on_kind,
            decl.line,
            getattr(decl, "origin", None),
        )

    # -- pass 2: kind chains -----------------------------------------------

    def _resolve_kinds(self) -> None:
        w = self.world
        for kind in w.kinds.values():
            kind.chain = self._chain(kind.name, kind.line)
        for obj in w.objects.values():
            if obj.kind not in w.kinds:
                raise self._error(
                    f"'{obj.name}' is of unknown kind '{obj.kind}'", obj.line
                )
            obj.chain = self._chain(obj.kind, obj.line)
            # A spanned name is a declared room, or a room KIND (docs/01 chapter
            # 5): `the_sun spans outside_room` puts the object in scope in every
            # room of that kind. Every room is known at compile time, so a kind
            # expands to its rooms here; the runtime spans table and scope check
            # stay exactly as they are for a list of named rooms.
            expanded: list[str] = []
            for rname in obj.spans:
                if rname in w.kinds:
                    if "room" not in self._chain(rname, obj.line):
                        raise self._error(
                            f"'{obj.name}' spans '{rname}', a kind that is not a "
                            f"room kind", obj.line
                        )
                    rooms = [
                        o.name for o in w.objects.values()
                        if o.category == "room"
                        and rname in self._chain(o.kind, o.line)
                    ]
                    if not rooms:
                        raise self._error(
                            f"'{obj.name}' spans '{rname}', a room kind with no "
                            f"rooms", obj.line
                        )
                    for rm in rooms:
                        if rm not in expanded:
                            expanded.append(rm)
                    continue
                target = w.objects.get(rname)
                if target is None:
                    raise self._error(
                        f"'{obj.name}' spans unknown room or kind '{rname}'",
                        obj.line
                    )
                if target.category != "room":
                    raise self._error(
                        f"'{obj.name}' spans '{rname}', which is not a room", obj.line
                    )
                if rname not in expanded:
                    expanded.append(rname)
            obj.spans = expanded
            # The parser homes a spanning object with no `in` in spans[0]; when
            # that was a kind, repoint it to the first room the kind expanded to.
            if obj.location in w.kinds and expanded:
                obj.location = expanded[0]

    def _check_locations(self) -> None:
        """Every `in <name>` must name a declared object (a field lesson,
        2026-08-14: an example lost its Truhe declaration to an editor
        accident and `thing schluessel in truhe` compiled SILENTLY, the key
        stranded outside the tree). Exits and spans already refuse a
        dangling name; the plain location was the last reference that
        could dangle. A kind name was repointed to its first room by the
        spans homing before this runs, so whatever is left must be a real
        object; None stays legal (backstage), and `scope` was registered
        as an object when anything declared it."""
        w = self.world
        for obj in w.objects.values():
            if obj.location is None:
                continue
            if obj.location not in w.objects:
                raise self._error(
                    f"'{obj.name}' is placed in '{obj.location}', which is "
                    f"not declared: the object would be stranded outside "
                    f"the world",
                    obj.line,
                )

    def _effective_attr(self, obj, attr: str):
        """The effective PropertyDecl for an attribute: the instance wins,
        then the nearest kind in the chain (the _effective_props merge,
        reduced to one name)."""
        if attr in obj.props:
            return obj.props[attr]
        for kname in obj.chain:
            kind = self.world.kinds.get(kname)
            if kind is not None and attr in kind.props:
                return kind.props[attr]
        return None

    def _attr_truthy(self, obj, attr: str) -> bool:
        decl = self._effective_attr(obj, attr)
        if decl is None:
            return False
        if decl.form == ast.PROP_BOOL:
            return True
        if decl.form == ast.PROP_VALUE and decl.values:
            v = decl.values[0]
            return isinstance(v, ast.Bool) and v.value
        return False

    def _check_presence(self) -> None:
        """The existence form (`in a, b`, docs/01 chapter 3): the object is
        fully present in every listed room. Validated here, after the
        properties pass, because the gate reads effective attributes: the
        form is for FIXED objects only. Scenery is redirected to `spans`
        (the sight form, its tool), a movable object is refused outright
        (never the old silent drop), and the targets must be named rooms,
        never kinds (a kind target is the sight form's). When both forms
        are live in one game, each existence object gets a synthesized
        1-byte `presence` marker so the describer can tell them apart at
        run time; a game using one form (or none) allocates no marker and
        keeps its property numbering untouched."""
        w = self.world
        any_presence = False
        any_sight = False
        for obj in w.objects.values():
            if obj.spans and (self._attr_truthy(obj, "fixed")
                              or self._attr_truthy(obj, "scenery")):
                any_sight = True
            if not obj.presence:
                continue
            if obj.category == "room":
                raise self._error(
                    f"'{obj.name}' is a room: a room cannot exist inside "
                    f"other rooms", obj.line)
            seen: list[str] = []
            for rname in obj.presence:
                if rname in w.kinds:
                    raise self._error(
                        f"'{obj.name}' is declared in '{rname}', a kind: the "
                        f"existence form (`in a, b`) takes named rooms; to be "
                        f"referable from every room of a kind, use the sight "
                        f"form (`spans {rname}`)", obj.line)
                target = w.objects.get(rname)
                if target is None:
                    raise self._error(
                        f"'{obj.name}' is declared in unknown room '{rname}'",
                        obj.line)
                if target.category != "room":
                    raise self._error(
                        f"'{obj.name}' is declared in '{rname}', which is "
                        f"not a room", obj.line)
                if rname not in seen and rname != obj.location:
                    seen.append(rname)
            obj.presence = seen
            if self._attr_truthy(obj, "scenery"):
                raise self._error(
                    f"'{obj.name}' is scenery declared in several rooms: "
                    f"scenery seen from many rooms uses `spans` (referable, "
                    f"never listed); `in a, b` is the existence form, for a "
                    f"fixed object that is fully present in each", obj.line)
            if not self._attr_truthy(obj, "fixed"):
                raise self._error(
                    f"'{obj.name}' is declared in several rooms but is "
                    f"movable: an object can exist in several rooms only "
                    f"when `fixed` (a carried object's scope follows it)",
                    obj.line)
            any_presence = True
        if any_presence and any_sight:
            self._unify_property("presence", prelude.T_NUMBER, 0)
            for obj in w.objects.values():
                if obj.presence:
                    obj.props["presence"] = ast.PropertyDecl(
                        "presence", ast.PROP_VALUE,
                        values=[ast.Number(1, obj.line)], line=obj.line)

    def _check_npcengine(self) -> None:
        """The NPC engine's declaration surface (summon.npcengine, docs/01
        chapter 22), recognized ONLY when the granule is summoned, so that
        in every other game these names stay ordinary author properties and
        the build is byte-identical. On a character: `npc` (bare, joins the
        roster), `patrol r1, r2, ...` (adjacent rooms, walked in order),
        `territory r1, ...` (rooms or room kinds, wandered within),
        `pursue target` (a room or a character, seeded here and
        runtime-changeable), `opens_doors` (the door capability). Any
        movement declaration implies `npc`. Every roster member starts
        `hibernated` (Stefan's controls: inactive, zero per-turn cost)
        unless it declares `hibernated false`; the granule's own npc_engine
        object is the master gate and is exempt from the character rule.
        Roster members get a `pursue` slot even undeclared (send() writes
        it at runtime; the put_prop trap), and patrol members a cursor."""
        w = self.world
        if not any(s.form == "feature" and s.target == "npcengine"
                   for s in w.summons):
            return
        npcs: list = []
        any_patrol = False
        for obj in w.objects.values():
            if obj.name == "npc_engine":
                continue
            props = obj.props
            move_decls = [p for p in ("patrol", "territory", "pursue")
                          if p in props]
            is_npc = bool(move_decls) or "npc" in props
            if not is_npc:
                continue
            chain = self._chain(obj.kind, obj.line)
            if "character" not in chain:
                raise self._error(
                    f"'{obj.name}' declares NPC engine behavior "
                    f"({', '.join(move_decls) or 'npc'}) but is not a "
                    f"character; the engine drives things `of character`",
                    obj.line)
            if "patrol" in props:
                decl = props["patrol"]
                rooms = [v.ident for v in decl.values
                         if isinstance(v, ast.Name)]
                if len(rooms) < 2 or len(rooms) != len(decl.values):
                    raise self._error(
                        f"'{obj.name}': a patrol names at least two rooms, "
                        f"in walking order (`patrol office, street`)",
                        decl.line or obj.line)
                for rname in rooms:
                    if rname in w.kinds:
                        raise self._error(
                            f"'{obj.name}' patrols '{rname}', a kind: a "
                            f"patrol is a concrete route of named, adjacent "
                            f"rooms; to roam every room of a kind, use "
                            f"`territory {rname}`", decl.line or obj.line)
                    target = w.objects.get(rname)
                    if target is None or target.category != "room":
                        raise self._error(
                            f"'{obj.name}' patrols '{rname}', which is not "
                            f"a room", decl.line or obj.line)
                any_patrol = True
            if "territory" in props:
                decl = props["territory"]
                names = [v.ident for v in decl.values
                         if isinstance(v, ast.Name)]
                if not names or len(names) != len(decl.values):
                    raise self._error(
                        f"'{obj.name}': territory names rooms or room "
                        f"kinds", decl.line or obj.line)
                expanded: list = []
                for rname in names:
                    if rname in w.kinds:
                        if "room" not in self._chain(rname, obj.line):
                            raise self._error(
                                f"'{obj.name}': territory '{rname}' is a "
                                f"kind that is not a room kind",
                                decl.line or obj.line)
                        rooms = [o.name for o in w.objects.values()
                                 if o.category == "room"
                                 and rname in self._chain(o.kind, o.line)]
                        if not rooms:
                            raise self._error(
                                f"'{obj.name}': territory '{rname}' is a "
                                f"room kind with no rooms",
                                decl.line or obj.line)
                        for rm in rooms:
                            if rm not in expanded:
                                expanded.append(rm)
                        continue
                    target = w.objects.get(rname)
                    if target is None or target.category != "room":
                        raise self._error(
                            f"'{obj.name}': territory '{rname}' is not a "
                            f"room or a room kind", decl.line or obj.line)
                    if rname not in expanded:
                        expanded.append(rname)
                decl.values = [ast.Name(r, decl.line) for r in expanded]
            if "pursue" in props:
                decl = props["pursue"]
                if (len(decl.values) != 1
                        or not isinstance(decl.values[0], ast.Name)):
                    raise self._error(
                        f"'{obj.name}': pursue names one target, a room or "
                        f"a character (or nothing)", decl.line or obj.line)
                ident = decl.values[0].ident
                if ident != "nothing" and ident not in w.objects:
                    raise self._error(
                        f"'{obj.name}' pursues unknown '{ident}'",
                        decl.line or obj.line)
            npcs.append(obj.name)
        w.npcs = npcs
        # The engine claims its property names outright (the summon is the
        # opt-in, roster or none: the granule's own code reads them, and an
        # orders-only game rosters nobody): patrol and territory are room
        # arrays whatever their declared arity (a one-kind `territory
        # outside_room` must not type as a single object), read only
        # through the route intrinsics; every name gets a number even when
        # no character declares it, so the walk's get_prop_addr stays legal
        # in every engine game.
        for pname in ("patrol", "territory"):
            prop = w.properties.get(pname)
            if prop is None:
                w.properties[pname] = wm.Property(
                    pname, prelude.T_LIST, "game", wm.STORE_SLOT,
                    [(self.filename, 0)])
            else:
                prop.type = prelude.T_LIST
                prop.storage = wm.STORE_SLOT
        self._unify_property("hibernated", prelude.T_BOOL, 0)
        self._unify_property("opens_doors", prelude.T_BOOL, 0)
        self._unify_property("pursue", prelude.T_OBJECT, 0)
        self._unify_property("npc_cursor", prelude.T_NUMBER, 0)
        for name in npcs:
            obj = w.objects[name]
            if "hibernated" not in obj.props:
                obj.props["hibernated"] = ast.PropertyDecl(
                    "hibernated", ast.PROP_BOOL, line=obj.line)
            if "pursue" not in obj.props:
                obj.props["pursue"] = ast.PropertyDecl(
                    "pursue", ast.PROP_VALUE, values=[ast.Nothing()],
                    line=obj.line)
            if "patrol" in obj.props and "npc_cursor" not in obj.props:
                obj.props["npc_cursor"] = ast.PropertyDecl(
                    "npc_cursor", ast.PROP_VALUE,
                    values=[ast.Number(0, obj.line)], line=obj.line)

    def _check_maniacswap(self) -> None:
        """maniacswap (summon.maniacswap, docs/01 chapter 22): multiple
        player characters, BECOME to swap. Recognized only when summoned:
        `playable` marks a body the keyboard may claim (a character, on
        pain of an error), the boot player is playable by default (the
        starting body always is), and the granule's own code needs
        `playable` and `hibernated` (the vocabulary it shares with the
        NPC engine) to exist even in a game that declares neither."""
        w = self.world
        if not any(s.form == "feature" and s.target == "maniacswap"
                   for s in w.summons):
            return
        self._unify_property("playable", prelude.T_BOOL, 0)
        self._unify_property("hibernated", prelude.T_BOOL, 0)
        for obj in w.objects.values():
            if "playable" not in obj.props:
                continue
            if obj.name == "player":
                continue
            if "character" not in self._chain(obj.kind, obj.line):
                raise self._error(
                    f"'{obj.name}' is declared playable but is not a "
                    f"character; the keyboard drives things `of character`",
                    obj.line)
        player = w.objects.get("player")
        if player is not None and "playable" not in player.props:
            player.props["playable"] = ast.PropertyDecl(
                "playable", ast.PROP_BOOL, line=0)

    def _check_exits(self) -> None:
        """Every named exit target must exist and be walkable (a field report:
        a typo'd room name compiled silently into "There's no exit in that
        direction.", and an exit naming a plain THING walked the player inside
        it, a pitch-black soft-lock). The legal targets are exactly three: a
        declared room, a door-kind thing (east oak_door), or a computed block;
        `nothing` stays legal as the explicit no-exit. Runs after
        _resolve_kinds so door detection can read the resolved kind chain."""
        w = self.world
        # world.direction_props is not filled until the properties pass;
        # the environment already knows the full set here.
        dprops = set(self.env.directions)
        for obj in w.objects.values():
            if obj.category != "room":
                continue
            for pname, decl in obj.props.items():
                if pname not in dprops:
                    continue
                if getattr(decl, "form", None) != ast.PROP_VALUE:
                    continue  # a computed exit block decides at run time
                if not decl.values or not isinstance(decl.values[0], ast.Name):
                    continue
                ident = decl.values[0].ident
                if ident == "nothing":
                    continue
                line = getattr(decl, "line", 0) or obj.line
                target = w.objects.get(ident)
                if target is None:
                    if ident in w.kinds:
                        raise self._error(
                            f"room '{obj.name}': exit '{pname}' names "
                            f"'{ident}', a kind; an exit needs a room, a "
                            f"door, or a computed block", line
                        )
                    raise self._error(
                        f"room '{obj.name}': exit '{pname}' names '{ident}', "
                        f"which is not declared", line
                    )
                if target.category != "room" and "door" not in target.chain:
                    raise self._error(
                        f"room '{obj.name}': exit '{pname}' points at "
                        f"'{ident}', which is neither a room nor a door", line
                    )

    def _rooted_in_room(self, kind_name: str) -> bool:
        """Does this kind chain reach `room`? A tolerant walk: an unknown or
        cyclic kind answers False here and gets its proper error from the
        kind-resolution pass, with its own context."""
        seen: set[str] = set()
        cur: Optional[str] = kind_name
        while cur is not None and cur in self.world.kinds and cur not in seen:
            if cur == "room":
                return True
            seen.add(cur)
            cur = self.world.kinds[cur].parent
        return False

    def _chain(self, start: str, line: int) -> list[str]:
        chain: list[str] = []
        seen: set[str] = set()
        cur: Optional[str] = start
        while cur is not None:
            if cur in seen:
                raise self._error(
                    f"kind '{start}' has a cyclic inheritance chain", line
                )
            if cur not in self.world.kinds:
                raise self._error(f"unknown kind '{cur}'", line)
            seen.add(cur)
            chain.append(cur)
            cur = self.world.kinds[cur].parent
        return chain

    # -- pass 3: property model --------------------------------------------

    def _scan_awards(self) -> None:
        """Walk every body that will be compiled and register each `award`
        site: anonymous sites append their points, named pools keep one byte
        and their maximum (docs/01, Scoring). Done here, before layout, so
        the earned table and the pool table can be laid out with the fixup
        machinery; lowering asserts against these assignments."""
        w = self.world

        def scan(stmts):
            for st in stmts:
                if isinstance(st, ast.Award):
                    if st.pool is not None:
                        prior = w.award_pools.get(st.pool)
                        if prior is None:
                            idx = len(w.award_anon) + len(w.award_pools)
                            w.award_pools[st.pool] = (idx, st.points, st.label)
                        else:
                            idx, best, label = prior
                            w.award_pools[st.pool] = (idx, max(best, st.points), label or st.label)
                    else:
                        st.site = len(w.award_anon) + len(w.award_pools)
                        w.award_anon.append(st.points)
                if isinstance(st, ast.If):
                    for cl in st.clauses:
                        scan(cl.body)
                elif isinstance(st, (ast.While, ast.ForEach)):
                    scan(st.body)
                elif isinstance(st, ast.Switch):
                    for c in st.cases:
                        scan(c.body)

        for blk in w.blocks.values():
            scan(blk.body)
        for h in w.free_handlers:
            scan(h.body)
        for obj in w.objects.values():
            for h in obj.handlers:
                scan(h.body)
            for t in obj.topics:
                scan(t.body)
            for g in obj.grains:
                if g.body:
                    scan(g.body)
            for a in obj.ambiences:
                pass  # do-lines call blocks, scanned above
            for pname, decl in obj.props.items():
                if getattr(decl, "form", None) == ast.PROP_BLOCK and decl.body:
                    scan(decl.body)
        for kind in w.kinds.values():
            for h in kind.handlers:
                scan(h.body)

    def _auto_score(self) -> None:
        """With `scoring` in the game block, score just works: every room and
        every takeable thing gets the scored bit set automatically, except
        the start room, whatever the player starts holding, and anything
        backstage; `scored false` on an object opts it out; kinds with
        blocking attributes (scenery, fixed, animate) never pay. The compiler
        sums all of it into max_score (docs/01, Scoring)."""
        w = self.world
        game = w.game
        if game is None or not any(
            m.key == "scoring" and m.value is True for m in game.meta
        ):
            return
        for name, obj in w.objects.items():
            if name in ("player", "scope") or "scored" in obj.props:
                continue
            if obj.category == "room":
                if name != w.start_room:
                    obj.props["scored"] = ast.PropertyDecl(name="scored", form=ast.PROP_BOOL)
                continue
            if obj.location in ("player", "scope"):
                continue
            # A thing a plain take would refuse never pays, so it never
            # counts: its own attributes and its kind chain's decide (a door
            # is fixed by kind, a character animate).
            blocked = False
            for attr in ("scenery", "fixed", "animate"):
                if attr in obj.props:
                    blocked = True
                for k in obj.chain:
                    kind = w.kinds.get(k)
                    if kind is not None and attr in kind.props:
                        blocked = True
            if not blocked:
                obj.props["scored"] = ast.PropertyDecl(name="scored", form=ast.PROP_BOOL)

    def _build_properties(self) -> None:
        w = self.world
        # Seed standard properties so types are fixed by Cosmos first.
        for sp in self.env.properties.values():
            w.properties[sp.name] = wm.Property(
                sp.name,
                sp.type,
                "standard",
                wm.STORE_ATTRIBUTE if sp.type == prelude.T_BOOL else wm.STORE_SLOT,
            )

        # player.<prop> augmentations: words ADD to whatever earlier layers
        # declared (the language pack's standard self-words come first, the
        # game's own words append); any other property is set, later wins.
        player = w.objects.get("player")
        if player is not None:
            for m in self._player_decls:
                if m.form == ast.PROP_VALUE and m.values:
                    m.values = [self._const_text(v) for v in m.values]
                self._unify_property(m.name, self._declared_type(m), m.line)
                prior = player.props.get(m.name)
                if m.name == "words" and prior is not None and m.form == ast.PROP_VALUE:
                    prior.values = list(prior.values) + list(m.values)
                else:
                    if m.name == "words":
                        # The FIRST words declaration is the language
                        # layer's (the library loads before everything):
                        # the standard self words. Marked so maniacswap's
                        # SELF pronoun (dictionary role 7) takes exactly
                        # these, never the game's own appended third-person
                        # words, which must keep naming the boot body.
                        for v in m.values:
                            v.self_word = True
                    player.props[m.name] = m
            # `change player.beyond_why to "..."` (the player-beyond refusal's
            # custom wording, docs/01 beyond) allocates the slot invisibly: a
            # property must exist at compile time to be writable at runtime,
            # and demanding a declaration first would be a trap (the put_prop
            # halt). It starts as nothing, so the pack default speaks until
            # the story sets a line. One slot on the player, only in a game
            # that writes it.
            if "beyond_why" not in player.props:
                if self._changes_prop_of("player", "beyond_why"):
                    self._unify_property("beyond_why", prelude.T_TEXT, 0)
                    player.props["beyond_why"] = ast.PropertyDecl(
                        "beyond_why", ast.PROP_VALUE, [ast.Nothing()]
                    )

        # Game property declarations on kinds and objects.
        for kind in w.kinds.values():
            if kind.decl is not None:
                self._collect_members(kind.decl.members, kind.name, kind.props, True)
        for obj in w.objects.values():
            if obj.decl is not None:
                self._collect_members(obj.decl.members, obj.name, obj.props, False)
            # The glow derivation (the binary model): a binary that also
            # declares `lit` is a light source whose light follows its
            # state, so the library's switch defaults flip both. Derived
            # here so no author ever writes it; kinds contribute through
            # their collected props like everything else.
            if "binary" in obj.props and "lit" in obj.props                     and "glow" not in obj.props:
                obj.props["glow"] = ast.PropertyDecl(
                    name="glow", form=ast.PROP_BOOL)

    def _image_id(self, m: ast.PropertyDecl) -> int:
        """The numeric image id from `arc_image <id>`: the id IS the resource
        slot, so the interpreter loads <id>.png (and a retro build loads slot
        <id>). Written as a plain number (`arc_image 8`) or, for readability, a
        constant that folds to one (`arc_image forest`, with `constant forest =
        8`). Id 0 is reserved to mean 'no picture' (it clears the band), so a
        real picture must be 1 or more. No name manifest: the number is the one
        identifier shared by every target."""
        vals = m.values
        if len(vals) == 1:
            n = self._fold_image_id(vals[0])
            if n is not None:
                if n <= 0:
                    raise self._error(
                        "arc_image id must be 1 or more (0 means no picture)",
                        m.line,
                    )
                if n > 0xFFFF:
                    raise self._error(
                        "arc_image id is too large (max 65535)", m.line
                    )
                return n
        raise self._error(
            "arc_image needs a picture id: a number, or a constant that names "
            "one, like `arc_image 8` or `arc_image forest` (constant forest = 8)",
            m.line,
        )

    def _fold_image_id(self, v) -> Optional[int]:
        """Fold an arc_image value to its integer id, or None if it is neither a
        number literal nor a constant standing for one."""
        if isinstance(v, ast.Number):
            return v.value
        if isinstance(v, ast.Name):
            c = self.world.constants.get(v.ident)
            if c is not None and isinstance(c.value, ast.Number):
                return c.value.value
        return None

    def _const_text(self, v):
        """A property value naming a STRING constant stands for its literal:
        `desc DESC_OFFICE` reads exactly as the text written in place (the
        field request: one wording shared between desc and say). Number and
        object constants pass through untouched."""
        if isinstance(v, ast.Name):
            c = self.world.constants.get(v.ident)
            if c is not None and isinstance(c.value, ast.StringLit):
                return c.value
        return v

    def _collect_members(self, members, owner, props_out, on_kind) -> None:
        w = self.world
        for m in members:
            if isinstance(m, ast.PropertyDecl):
                # The standard kinds are KINDS, never bare attribute lines
                # (Stefan's ruling, 2026-08-24): a `supporter` line on a
                # thing compiled and half-worked, the any_enterable
                # machinery counting kinds only, which is how "(contains
                # yourself)" happened. Refuse loudly and name the cure.
                if (m.form == ast.PROP_BOOL
                        and m.name in _KIND_NOT_ATTRIBUTE):
                    raise self._error(
                        f"'{m.name}' on '{owner}' is a kind, not an "
                        f"attribute: declare `{'kind ' if on_kind else 'thing '}"
                        f"{owner} of {m.name} ...` instead",
                        m.line,
                    )
                if m.name == "beyond" and m.form != ast.PROP_BOOL:
                    # `beyond "why"` / `beyond block` (the Charles request):
                    # the attribute plus its own explanation. Split into the
                    # bool `beyond` and the text `beyond_why` (computed under
                    # the block form, the desc-block shape); the guard says
                    # the why instead of the generic msg_beyond.
                    battr = ast.PropertyDecl(name="beyond", form=ast.PROP_BOOL)
                    self._unify_property("beyond", prelude.T_BOOL, m.line)
                    props_out["beyond"] = battr
                    m.name = "beyond_why"
                if m.form == ast.PROP_VALUE and m.values:
                    m.values = [self._const_text(v) for v in m.values]
                    # A plain property string is a static Z-string: an ${...}
                    # inside one cannot run and is dropped at encode time.
                    # Say so, and name the cure, instead of printing a hole.
                    for v in m.values:
                        if isinstance(v, ast.StringLit) and any(
                            not isinstance(p, ast.StringText) for p in v.parts
                        ):
                            print(
                                f"arcc: note: '{m.name}' on '{owner}': "
                                f"interpolation in a plain property string is "
                                f"dropped at runtime; use a computed "
                                f"`{m.name} block` to word it by state",
                                file=sys.stderr,
                            )
                # `switchable` is the compatibility alias for `binary`: one
                # property, one attribute, two spellings; shipped games keep
                # compiling while the language says what the thing IS.
                if m.name == "switchable":
                    m.name = "binary"
                # A German gender article (der / die / das) is not a property in its
                # own right: it states the object's gender the way an author thinks
                # of it, and maps to the gender attributes. der is masculine, the
                # default, so it records nothing; die and das set feminine / neutral.
                if m.name in prelude._GENDER_ARTICLES:
                    attr = prelude._GENDER_ARTICLES[m.name]
                    if attr is not None:
                        self._unify_property(attr, prelude.T_BOOL, m.line)
                        props_out[attr] = ast.PropertyDecl(
                            name=attr, form=ast.PROP_BOOL, line=m.line
                        )
                    continue
                # arc_image <id> -> the picture's numeric id in the slot. The id
                # is the author's own number (or a constant that folds to one),
                # so the slot holds exactly what the interpreter loads as a file
                # (<id>.png) and a retro build loads as a slot. Record that the
                # game uses pictures, so any_images folds to 1.
                # weight <kg> (the carryweight granule, docs/01 chapter 6):
                # the slot holds TENTHS of the unit. A pointed literal (2.1)
                # arrives from the lexer already in tenths; a bare integer
                # (weight 2) means whole units and scales by ten here, so 2,
                # 2.0 and "2 kilograms" are the same fact. `weight no_weight`
                # is the readable zero. Scaled only under summon.carryweight:
                # without the granule the name is an ordinary property the
                # game owns, untouched.
                if m.name == "weight" and wm.has_summon(w, "carryweight"):
                    vals = []
                    for v in m.values:
                        if isinstance(v, ast.Name) and v.ident == "no_weight":
                            vals.append(ast.Number(0, m.line, tenths=True))
                        elif isinstance(v, ast.Number) and not v.tenths:
                            vals.append(ast.Number(v.value * 10, v.line,
                                                   tenths=True))
                        else:
                            vals.append(v)
                    m = ast.PropertyDecl(name="weight", form=m.form,
                                         values=vals, line=m.line)
                if m.name == "arc_image":
                    m = ast.PropertyDecl(
                        name="arc_image",
                        form=m.form,
                        values=[ast.Number(self._image_id(m), m.line)],
                        line=m.line,
                    )
                    w.uses_images = True
                # The trigger marker (docs/01 chapter 14): #-marked entries of
                # a words list become the object's `trigger` property, a vocab
                # array beside `words`. Registered only on first use, so a
                # game without the marker allocates no property number and
                # stays byte-identical; the marker keeps every trigger inside
                # the vocabulary it belongs to.
                if m.name == "words" and m.triggers:
                    self._unify_property("trigger", prelude.T_LIST, m.line)
                    props_out["trigger"] = ast.PropertyDecl(
                        "trigger",
                        ast.PROP_VALUE,
                        values=[ast.Name(t, m.line) for t in m.triggers],
                        line=m.line,
                    )
                    w.uses_triggers = True
                # The adjective marker (`words #chest, box, >wooden`): the
                # >-marked words become the object's `adjective` property, a
                # vocab array beside `words`, feeding the ZIL match classes.
                # Registered only on first use, like `trigger`.
                if m.name == "words" and m.adjectives:
                    self._unify_property("adjective", prelude.T_LIST, m.line)
                    props_out["adjective"] = ast.PropertyDecl(
                        "adjective",
                        ast.PROP_VALUE,
                        values=[ast.Name(t, m.line) for t in m.adjectives],
                        line=m.line,
                    )
                    w.uses_adjectives = True
                ty = self._declared_type(m)
                self._unify_property(m.name, ty, m.line)
                props_out[m.name] = m
            elif isinstance(m, ast.Handler):
                h = self._make_handler(m, owner, on_kind)
                if on_kind:
                    w.kinds[owner].handlers.append(h)
                else:
                    w.objects[owner].handlers.append(h)
            elif isinstance(m, ast.GrainsBlock):
                for g in m.grains:
                    self._add_grain(g, owner, on_kind)
            elif isinstance(m, ast.AmbienceBlock):
                # Ambience blocks (docs/01 chapter 22) live on objects, not kinds, and
                # need their granule (the driver) summoned.
                if on_kind:
                    raise self._error("ambience belongs on a room or thing, not a kind", m.line)
                if not any(
                    s.form == "feature" and s.target == "ambience"
                    for s in w.summons
                ):
                    raise self._error(
                        "an ambience block needs the granule: add summon.ambience",
                        m.line,
                    )
                if m.once and m.mode != "order" and len(m.lines) > 15:
                    # The shuffled deal tracks fired lines in one word.
                    raise self._error(
                        f"a `once` ambience block holds at most 15 lines "
                        f"(this one has {len(m.lines)}); split it into two "
                        f"blocks, or use `in order once`",
                        m.line,
                    )
                w.objects[owner].ambiences.append(m)
            elif isinstance(m, ast.TopicDecl):
                if m.idle and m.words:
                    # An idle topic answers when NOTHING else matched, so it
                    # cannot also carry subject words: the two are contradictory.
                    raise self._error(
                        f"topic '{m.subject}' is `idle` (the ask/tell fallback) "
                        f"and so takes no `words`: it answers when no worded "
                        f"topic matched. Drop the words, or drop `idle`",
                        m.line,
                    )
                if on_kind:
                    w.kinds[owner].topics.append(m)
                else:
                    w.objects[owner].topics.append(m)

    def _add_grain(self, g: ast.Grain, owner: str, on_kind: bool) -> None:
        grain = wm.Grain(g.verbs, g.words, owner, g.say, g.do, g.body, g.line)
        if on_kind:
            self.world.kinds[owner].grains.append(grain)
        else:
            self.world.objects[owner].grains.append(grain)

    def _declared_type(self, m: ast.PropertyDecl) -> Optional[str]:
        if m.form == ast.PROP_BOOL:
            return prelude.T_BOOL
        if m.form == ast.PROP_LIST:
            return prelude.T_LIST
        if m.form == ast.PROP_BLOCK:
            # A computed property yields a value when read; if the property
            # already has a value type, the block computes that type and does
            # not redefine it. Only an otherwise-unknown property types as block.
            existing = self.world.properties.get(m.name)
            return existing.type if existing is not None else prelude.T_BLOCK
        # PROP_VALUE: several values are a list literal; one value takes its type.
        existing = self.world.properties.get(m.name)
        if existing is not None and existing.type == prelude.T_LIST:
            return prelude.T_LIST
        if len(m.values) > 1:
            return prelude.T_LIST
        return self._value_type(m.values[0]) if m.values else None

    def _unify_property(self, name: str, ty: Optional[str], line: int) -> None:
        w = self.world
        prop = w.properties.get(name)
        if prop is None:
            if ty is None:
                ty = prelude.T_BOOL  # a bare name defaults to a boolean
            w.properties[name] = wm.Property(
                name,
                ty,
                "game",
                wm.STORE_ATTRIBUTE if ty == prelude.T_BOOL else wm.STORE_SLOT,
                [(self.filename, line)],
            )
            return
        prop.decl_sites.append((self.filename, line))
        if ty is not None and ty != prop.type:
            first = prop.decl_sites[0][1] if prop.decl_sites else line
            raise self._error(
                f"property '{name}' is used as {prop.type} (line {first}) and "
                f"as {ty} (line {line}); a property has one type program-wide",
                line,
            )

    def _value_type(self, expr: ast.Expr) -> Optional[str]:
        if isinstance(expr, ast.Number):
            return prelude.T_NUMBER
        if isinstance(expr, ast.StringLit):
            return prelude.T_TEXT
        if isinstance(expr, ast.Bool):
            return prelude.T_BOOL
        if isinstance(expr, ast.Name) and expr.ident in self.world.catalogs:
            # A property can hold a catalog: the value is the catalog's word
            # offset, a plain number, so `self.writing` travels into entry(),
            # quote_catalog(), and the rest exactly like the name written in
            # place (a field report: the slot used to type as object, resolve
            # to nothing, and silently read as the FIRST catalog).
            return prelude.T_NUMBER
        if isinstance(expr, (ast.Nothing, ast.Name)):
            return prelude.T_OBJECT
        if isinstance(expr, ast.Binary) and expr.op in ("+", "-", "*", "/", "mod"):
            return prelude.T_NUMBER
        return None

    # -- pass 4: bodies ----------------------------------------------------

    def _resolve_bodies(self) -> None:
        w = self.world
        # Computed property bodies, handler bodies, grains, on each owner.
        for kind in w.kinds.values():
            if kind.decl is not None:
                self._resolve_owner(kind.decl.members, on_kind=True)
        for obj in w.objects.values():
            if obj.decl is not None:
                self._resolve_owner(obj.decl.members, on_kind=False)
        # The player is SEEDED, not declared: its `player.<prop>`
        # augmentations live aside and must be resolved like any owner's
        # members, or an is-test in a player.desc block never resolves and
        # a typo there skips sema entirely (the worn field report).
        self._resolve_owner(self._player_decls, on_kind=False)
        for h in w.free_handlers:
            self._check_handler(h)
        for blk in w.blocks.values():
            if len(blk.params) > 7:
                # A Z-machine call fills at most 7 locals (even the long-call
                # pair), so an eighth parameter could never receive a value.
                raise self._error(
                    f"block '{blk.name}' declares {len(blk.params)} "
                    f"parameters, but a block takes at most 7 (the "
                    f"Z-machine's own call ceiling); group some into a "
                    f"catalog or a matrix, or split the block",
                    blk.line,
                )
            self._check_body(blk.body, set(blk.params))
        # Attached grains and game start. The outside-body form
        # (`foyer.grains`, docs/01 chapter 18) MERGES here: it was checked
        # but never added, so the whole form was silently dead (a field
        # investigation found it; the words never even reached the
        # dictionary). Attached grains join the owner's list exactly as an
        # inline block's do, so the word-split lint covers them too.
        for decl in self.program.decls:
            if isinstance(decl, ast.GrainsAttach):
                if decl.target not in w.objects:
                    raise self._error(
                        f"grains attached to unknown object '{decl.target}'",
                        decl.line,
                    )
                for g in decl.grains:
                    self._check_grain(g)
                    self._add_grain(g, decl.target, on_kind=False)
        if w.start_room is not None and w.start_room not in w.objects:
            line = w.game.line if w.game else 0
            raise self._error(
                f"game start room '{w.start_room}' is not defined", line
            )

    def _resolve_owner(self, members, on_kind: bool) -> None:
        for m in members:
            if isinstance(m, ast.PropertyDecl) and m.form == ast.PROP_BLOCK:
                self._check_body(m.body, set())
            elif isinstance(m, ast.TopicDecl):
                # Topic bodies are ordinary statement blocks (docs/01) and
                # get the ordinary checks; before this branch a `vary` in a
                # topic never received its state slot and the compiler
                # crashed on the missing offset (Charles Moore Jr.'s
                # request surfaced it: varied replies in a topic).
                self._check_body(m.body, set())
            elif isinstance(m, ast.Handler):
                self._check_handler(m, owned=True)
            elif isinstance(m, ast.GrainsBlock):
                for g in m.grains:
                    self._check_grain(g)
            elif isinstance(m, ast.AmbienceBlock):
                # Resolve the guards and the lines like any other body, so an
                # `is` test disambiguates and a do-block must exist.
                if m.when is not None:
                    self._check_condition(m.when, set(), m.line)
                probe = []
                for l in m.lines:
                    if l.when is not None:
                        self._check_condition(l.when, set(), l.line)
                    if l.text is not None:
                        probe.append(ast.Say(l.text))
                    else:
                        probe.append(ast.ExprStmt(ast.Call(l.do, [], l.line)))
                self._check_body(probe, set())

    def _check_handler(self, h, owned: bool = False) -> None:
        events = h.events if isinstance(h, wm.Handler) else h.events
        pattern = h.pattern
        body = h.body
        when = h.when
        line = h.line
        valid = self.world.actions | {"start", "enter", "each_turn", "other"}
        for ev in events:
            if ev not in valid:
                raise self._error(
                    f"unknown verb or action '{ev}' in handler header", line
                )
        for item in pattern:
            if isinstance(item, ast.Operand):
                for name in item.names:
                    self._check_operand(
                        name, line,
                        owned or getattr(h, "owner", None) is not None)
        if when is not None:
            self._check_condition(when, set(), line)
        self._check_body(body, set())

    def _check_operand(self, name: str, line: int, owned: bool = False) -> None:
        w = self.world
        if name == "self":
            # The enclosing object as its own operand (`on put noun in self`,
            # `on enter self`); in a kind body it means each instance. Only a
            # handler WITH an enclosure can say it.
            if owned:
                return
            raise self._error(
                "'self' in a handler header needs an enclosing object; a "
                "free-standing rule names its object instead",
                line,
            )
        if (
            name in w.objects
            or name in w.kinds
            or name in ("noun", "second", "other")
            or self.env.is_direction(name)
        ):
            return
        raise self._error(
            f"'{name}' in a handler header is not an object, kind, or direction",
            line,
        )

    def _check_grain(self, g: ast.Grain) -> None:
        for v in g.verbs:
            if v not in self.world.actions:
                raise self._error(
                    f"grain answers unknown verb '{v}'", g.line
                )
        if g.body:
            self._check_body(g.body, set())

    # -- statements --------------------------------------------------------

    def _check_body(self, stmts, locals_: set) -> None:
        # A nested body's lets die with it: remember them so a later
        # unknown-name error can teach the scoping instead of shrugging.
        outer = locals_
        locals_ = set(locals_)
        for s in stmts:
            self._check_stmt(s, locals_)
        for name in locals_ - outer:
            self._expired_lets.add(name)

    def _check_stmt(self, s, locals_: set) -> None:
        if isinstance(s, ast.Let):
            self._check_expr(s.value, locals_)
            locals_.add(s.name)
        elif isinstance(s, ast.Change):
            self._check_change(s, locals_)
        elif isinstance(s, ast.Now):
            self._check_now(s, locals_)
        elif isinstance(s, ast.Move):
            self._check_expr(s.obj, locals_)
            self._check_expr(s.dest, locals_)
        elif isinstance(s, (ast.Add, ast.Remove)):
            self._check_expr(s.value, locals_)
            self._check_list_place(s.target, locals_)
        elif isinstance(s, ast.Bump):
            g = self.world.globals.get(s.name)
            if g is None or g.role != "counter":
                raise self._error(
                    f"'{s.name}++' needs a counter; declare it with "
                    f"`counter {s.name}`",
                    s.line,
                )
        elif isinstance(s, ast.Award):
            if not (0 < s.points <= 250):
                raise self._error("award takes 1 to 250 points", s.line)
        elif isinstance(s, ast.Say):
            self._check_expr(s.value, locals_)
        elif isinstance(s, (ast.Stop, ast.Continue, ast.ZColor)):
            pass
        elif isinstance(s, ast.Finish):
            if s.message is not None:
                self._check_expr(s.message, locals_)
        elif isinstance(s, ast.Return):
            if s.value is not None:
                self._check_expr(s.value, locals_)
        elif isinstance(s, ast.ExprStmt):
            self._check_expr(s.expr, locals_)
        elif isinstance(s, ast.Schedule):
            self._check_expr(s.count, locals_)
            if s.event not in self.world.blocks:
                word = "every" if s.every else "after"
                raise self._error(
                    f"'{word} ... do {s.event}' names no block '{s.event}'", s.line
                )
        elif isinstance(s, ast.StopSchedule):
            self._check_expr(s.count, locals_)
            if s.event not in self.world.blocks:
                word = "every" if s.every else "after"
                raise self._error(
                    f"'stop {word} ... do {s.event}' names no block "
                    f"'{s.event}'", s.line
                )
        elif isinstance(s, ast.StopAllTimers):
            pass
        elif isinstance(s, ast.If):
            for clause in s.clauses:
                if clause.cond is not None:
                    self._check_condition(clause.cond, locals_, clause.line)
                self._check_body(clause.body, locals_)
        elif isinstance(s, ast.While):
            self._check_condition(s.cond, locals_, s.line)
            self._check_body(s.body, locals_)
        elif isinstance(s, ast.Vary):
            # Stamp the site's state slot: one word in the catalog region for
            # a stateful policy (sequence/loop hold a counter, mutate the last
            # pick); dice rolls fresh every time and carries nothing. Stamped
            # once (a body is only checked once, but be safe on reentry).
            if s.policy != "dice" and s.slot is None:
                s.slot = self.world.vary_slots
                self.world.vary_slots += 1
            for variant in s.variants:
                self._check_body(variant, locals_)
        elif isinstance(s, ast.ForEach):
            self._check_expr(s.source, locals_)
            inner = set(locals_)
            inner.add(s.var)
            self._check_body(s.body, inner)
        elif isinstance(s, ast.Switch):
            self._check_expr(s.subject, locals_)
            for case in s.cases:
                for v in case.values:
                    self._check_expr(v, locals_)
                self._check_body(case.body, locals_)

    def _check_change(self, s: ast.Change, locals_: set) -> None:
        self._check_expr(s.value, locals_)
        # The declaration head is a promise: a flag holds true or false, a
        # counter holds numbers. Literal mismatches are compile errors.
        if isinstance(s.target, ast.Name):
            g = self.world.globals.get(s.target.ident)
            if g is not None and g.role == "flag" and isinstance(s.value, ast.Number):
                raise self._error(
                    f"'{s.target.ident}' is a flag: it takes true or false",
                    s.line,
                )
            if g is not None and g.role == "counter" and isinstance(s.value, ast.Bool):
                raise self._error(
                    f"'{s.target.ident}' is a counter: it takes numbers",
                    s.line,
                )
        target = s.target
        if isinstance(target, ast.Name):
            name = target.ident
            if name in ("here", "turns"):
                raise self._error(
                    f"'{name}' is maintained by Cosmos and cannot be changed",
                    s.line,
                )
            if name in self.world.constants:
                raise self._error(
                    f"'{name}' is a constant and cannot be changed", s.line
                )
            if not (
                name in locals_
                or name in self.world.globals
                or name in self.env.builtins
            ):
                raise self._error(
                    f"'change' target '{name}' is not a local or global", s.line
                )
        elif isinstance(target, ast.Dot):
            self._check_expr(target.obj, locals_)
            if target.prop not in self.world.properties:
                raise self._error(
                    f"cannot change undeclared property '{target.prop}'", s.line
                )
        elif isinstance(target, ast.DynDot):
            self._check_expr(target.obj, locals_)
            self._check_expr(target.index, locals_)

    def _check_now(self, s: ast.Now, locals_: set) -> None:
        self._check_expr(s.target, locals_)
        # The standard kinds are KINDS, not grantable attributes (Stefan's
        # ruling, 2026-08-24): being a supporter is what a thing IS, declared
        # `of supporter`, never switched on. Testing `is supporter` stays
        # ordinary; only setting it is refused. Half-working attribute
        # grants were how "(contains yourself)" happened: the any_enterable
        # machinery counts kinds, so an attribute-only supporter kept the
        # nesting surface folded away.
        if s.prop in _KIND_NOT_ATTRIBUTE:
            raise self._error(
                f"'{s.prop}' is a kind, not an attribute: an object is "
                f"declared `of {s.prop}` and stays one",
                s.line,
            )
        prop = self.world.properties.get(s.prop)
        if prop is None:
            raise self._error(
                f"'now' sets undeclared property '{s.prop}'", s.line
            )
        if prop.type != prelude.T_BOOL:
            raise self._error(
                f"'now ... is {s.prop}' needs a boolean property, but "
                f"'{s.prop}' is {prop.type}",
                s.line,
            )

    def _check_list_place(self, target, locals_: set) -> None:
        if isinstance(target, ast.Dot):
            self._check_expr(target.obj, locals_)
            prop = self.world.properties.get(target.prop)
            if prop is None:
                raise self._error(
                    f"unknown list property '{target.prop}'", getattr(target, "line", 0)
                )
            if prop.type != prelude.T_LIST:
                raise self._error(
                    f"'{target.prop}' is not a list property", getattr(target, "line", 0)
                )
        else:
            self._check_expr(target, locals_)

    # -- expressions and conditions ----------------------------------------

    def _check_condition(self, expr, locals_: set, line: int) -> None:
        self._check_expr(expr, locals_)
        ty = self._infer_type(expr, locals_)
        if ty in (prelude.T_NUMBER, prelude.T_TEXT, prelude.T_OBJECT, prelude.T_LIST):
            raise self._error(
                "condition must be boolean; compare it (for example 'n > 0') "
                "or test a property",
                line,
            )

    def _check_expr(self, expr, locals_: set) -> None:
        if isinstance(expr, (ast.Number, ast.Bool, ast.Nothing)):
            return
        if isinstance(expr, ast.StringLit):
            for part in expr.parts:
                if isinstance(part, ast.StringInterp):
                    self._check_expr(part.expr, locals_)
            return
        if isinstance(expr, ast.Name):
            self._resolve_name(expr.ident, locals_, expr.line)
            return
        if isinstance(expr, ast.Dot):
            self.prop_reads.add(expr.prop)
            self._check_expr(expr.obj, locals_)
            return
        if isinstance(expr, ast.DynDot):
            self._check_expr(expr.obj, locals_)
            self._check_expr(expr.index, locals_)
            return
        if isinstance(expr, ast.Call):
            for a in expr.args:
                self._check_expr(a, locals_)
            return
        if isinstance(expr, ast.Unary):
            self._check_expr(expr.operand, locals_)
            return
        if isinstance(expr, (ast.Binary, ast.Logic)):
            self._check_expr(expr.left, locals_)
            self._check_expr(expr.right, locals_)
            return
        if isinstance(expr, ast.IsTest):
            self._resolve_is(expr, locals_)
            return

    def _resolve_is(self, expr: ast.IsTest, locals_: set) -> None:
        self._check_expr(expr.left, locals_)
        right = expr.right
        # `action is open` compares ACTIONS, always: the left side is the
        # dispatcher's action builtin, so a right side that happens to share
        # its name with a boolean property (open, hidden, locked) is the
        # ACTION of that name, never an attribute test on a number (the
        # playtest find, 2026-07-30: a grain's `if action is open` silently
        # tested the open attribute and fell to the else branch).
        left_is_action = (
            (isinstance(expr.left, ast.Name) and expr.left.ident == "action"
             and "action" not in locals_)
            or (isinstance(expr.left, ast.Call) and expr.left.name == "action"
                and not expr.left.args))
        if left_is_action and isinstance(right, ast.Name) \
                and right.ident not in locals_ \
                and right.ident not in self.world.objects \
                and right.ident in self.world.actions:
            self.world.is_resolutions[id(expr)] = wm.IS_EQUALITY
            return
        # A bare identifier naming a boolean property is a property test; a kind
        # name is a kind-membership test; otherwise the comparison is an equality
        # (docs/01 chapter 9).
        if isinstance(right, ast.Name):
            prop = self.world.properties.get(right.ident)
            is_obj = (
                right.ident in self.world.objects
                or right.ident in self.env.builtins
            )
            if prop is not None and prop.type == prelude.T_BOOL:
                if is_obj:
                    raise self._error(
                        f"'{right.ident}' is both a boolean property and an "
                        f"object; rename one",
                        expr.line,
                    )
                self.prop_reads.add(right.ident)
                self.world.is_resolutions[id(expr)] = wm.IS_PROPERTY
                return
            if right.ident in self.world.kinds:
                self.world.is_resolutions[id(expr)] = wm.IS_KIND
                # Count the test site: only membership-tested kinds need a
                # runtime identity, and the busiest ones earn the scarce
                # attribute slots (objects.build_layout ranks by this).
                self.world.kind_tests[right.ident] = (
                    self.world.kind_tests.get(right.ident, 0) + 1)
                return
            # A one-parameter block used as a predicate: `lamp is visible`
            # reads as visible(lamp), the way `is` already reads attributes
            # and kinds. Attributes and kinds win the name; blocks with any
            # other arity stay ordinary values (the equality error path
            # tells the author to call them).
            blk = self.world.blocks.get(right.ident)
            if blk is not None and len(blk.params) == 1:
                self.world.is_resolutions[id(expr)] = wm.IS_PREDICATE
                return
        # `if action is touch`: against `action`, a bare name reads as the
        # ACTION of that name, the sugar directions already have with `way`.
        # Resolved last, so a local, global, object, or kind of the same name
        # still wins; only then does the action vocabulary get a look.
        if isinstance(right, ast.Name) and self._names_the_action(expr.left, locals_) \
                and right.ident not in locals_ \
                and right.ident not in self.world.globals \
                and right.ident not in self.world.objects \
                and right.ident in wm.action_numbers(self.world):
            self.world.is_resolutions[id(expr)] = wm.IS_EQUALITY
            return
        self.world.is_resolutions[id(expr)] = wm.IS_EQUALITY
        self._check_expr(right, locals_)

    def _names_the_action(self, left, locals_: set) -> bool:
        """Is this the `action` intrinsic rather than something of that name?"""
        if not isinstance(left, ast.Name) or left.ident != "action":
            return False
        return ("action" not in locals_
                and "action" not in self.world.globals
                and "action" not in self.world.objects)

    def _resolve_name(self, name: str, locals_: set, line: int) -> None:
        w = self.world
        if (
            name in locals_
            or name in w.objects
            or name in w.kinds
            or name in w.globals
            or name in w.constants
            or name in w.blocks
            or name in w.catalogs
            or name in w.matrices
            or name in self.env.builtins
            or self.env.is_direction(name)
        ):
            return
        # A bare intrinsic name is a zero-argument call (print_banner,
        # read_key); lower resolves it after every data name.
        from .lower import INTRINSICS
        if name in INTRINSICS:
            return
        # `letters` and `anychar`, a typed input slot's absorbed words
        # (docs/01 chapter 14): legal in their forms (compared, printed;
        # `number` is the numeric reading, an ordinary block); lower
        # explains itself if one is misused as a plain value.
        if name in ("letters", "anychar"):
            return
        if name == "direction":
            raise self._error(
                "unknown name 'direction': the chosen direction rides `way` "
                "(if way is north, if way is aft); `direction` is the "
                "declaration keyword and the grammar slot",
                line,
            )
        if name in getattr(self, "_expired_lets", ()):
            raise self._error(
                f"unknown name '{name}': it was declared with `let` inside a "
                f"nested block (an if branch, a loop body) and ended with "
                f"that block. Declare it before the block (`let {name} = 0`) "
                f"and use `change {name} to ...` inside the branches",
                line,
            )
        raise self._error(f"unknown name '{name}'", line)

    def _infer_type(self, expr, locals_: set) -> Optional[str]:
        if isinstance(expr, ast.Number):
            return prelude.T_NUMBER
        if isinstance(expr, ast.StringLit):
            return prelude.T_TEXT
        if isinstance(expr, ast.Bool):
            return prelude.T_BOOL
        if isinstance(expr, ast.Nothing):
            return prelude.T_OBJECT
        if isinstance(expr, (ast.IsTest, ast.Logic)):
            return prelude.T_BOOL
        if isinstance(expr, ast.Unary):
            return prelude.T_BOOL if expr.op == "not" else prelude.T_NUMBER
        if isinstance(expr, ast.Binary):
            if expr.op in ("<", ">", "<=", ">=", "holds", "in"):
                return prelude.T_BOOL
            return prelude.T_NUMBER
        if isinstance(expr, ast.Name):
            return self._name_type(expr.ident, locals_)
        if isinstance(expr, ast.Dot):
            prop = self.world.properties.get(expr.prop)
            return prop.type if prop is not None else None
        return None  # Call, DynDot: unknown at this stage

    def _name_type(self, name: str, locals_: set) -> Optional[str]:
        if name in locals_:
            return None  # locals are untyped in v1
        g = self.world.globals.get(name)
        if g is not None:
            return g.type
        c = self.world.constants.get(name)
        if c is not None:
            return c.type
        b = self.env.builtins.get(name)
        if b is not None:
            return b.type
        if name in self.world.objects or self.env.is_direction(name):
            return prelude.T_OBJECT
        return None


    def _lint_unread_props(self) -> None:
        """A custom property set on an object but never read anywhere is
        almost always a typo, or a newer standard attribute compiled by an
        OLDER arcc (property names are open by design, so the declaration
        stays legal and silently inert: the `component` case, where a build
        predating the attribute accepted it as a custom property and the
        apron simply never entered scope). Say so, as a note."""
        std = set(self.env.properties)
        # tag rides props but is not one; trigger is synthesized from the #
        # marker and read through its intrinsic (trigger_addr), never as a
        # property, so the unread-lint has no business with either. presence
        # is the existence-form marker, synthesized and intrinsic-read too.
        skip = {"tag", "trigger", "adjective", "presence"}
        # item_cap is read by the container ceiling through the
        # container_cap intrinsic the moment any object declares it, and
        # weight by the carryweight granule through weight_of: intrinsic
        # get_props the dotted-read tracking never sees, so neither is
        # ever a typo to flag.
        skip.add("item_cap")
        if wm.has_summon(self.world, "carryweight"):
            skip.add("weight")
        if getattr(self.world, "npcs", None):
            # The engine's declaration surface (summon.npcengine) is read
            # through the route intrinsics and the roster walk, never as
            # plain property reads; with a roster live these are working
            # declarations, not typos.
            skip |= {"npc", "patrol", "territory", "npc_cursor"}
        noted = 0
        pools = [(o.name, o.props) for o in self.world.objects.values()]
        pools += [(k.name, k.props) for k in self.world.kinds.values()
                  if k.origin == "game"]
        for owner, props in pools:
            for pname in props:
                if pname in std or pname in skip or pname in self.prop_reads:
                    continue
                if self.env.is_direction(pname):
                    continue
                noted += 1
                if noted <= 5:
                    print(
                        f"arcc: note: property '{pname}' on '{owner}' is "
                        f"never read by the story or the library; a typo, or "
                        f"an attribute this arcc version does not know?",
                        file=sys.stderr,
                    )
        if noted > 5:
            print(f"arcc: note: ({noted - 5} more unread properties)",
                  file=sys.stderr)

    def _lint_self_perform(self) -> None:
        """perform re-enters the WHOLE handler chain, the calling handler
        included: an UNGUARDED `on burn` that performs "burn" dispatches back
        into itself forever (the field symptom: the interpreter dies at the
        prompt). A `when` guard or an operand pattern exempts the handler,
        because the re-entry can fail it and fall through, the legitimate
        re-dispatch shape; the unguarded shape is always a loop, so note it
        and name the cure (`continue` reaches the default without
        re-dispatching). An `on after <verb>` performing its own verb loops
        the same way (the perform's own after pass re-enters it)."""
        # Handlers with their owner: a THING instance's handlers run only
        # when its own object is the one acted on, so a same-action perform
        # aimed at an explicit DIFFERENT object can never re-enter them (the
        # field pushback: redirecting an action onto another object is the
        # common legitimate shape, narrowed out of the note by Stefan's
        # ruling). A kind's, a room's, or a free handler runs for any noun,
        # so its self-perform loops regardless of target: those keep the
        # note, as do dynamic targets nobody can prove at compile time.
        owned = []
        for name, obj in self.world.objects.items():
            inst = None if obj.category == "room" else name
            owned += [(h, inst) for h in obj.handlers]
        for kind in self.world.kinds.values():
            owned += [(h, None) for h in kind.handlers]
        owned += [(h, None) for h in self.world.free_handlers]
        for h, owner in owned:
            if h.when is not None or h.pattern:
                continue  # the re-entry can fail the guard: legitimate
            events = set(h.events)
            hit = [None]  # (line, event) of the first self-perform found

            def redirects_elsewhere(node):
                # Provably safe: instance-owned, and every performed operand
                # is an explicit object that is not this instance (nor self).
                if owner is None or len(node.args) < 2:
                    return False
                for a in node.args[1:]:
                    if not isinstance(a, ast.Name):
                        return False
                    if a.ident == "self" or a.ident == owner:
                        return False
                    if a.ident not in self.world.objects:
                        return False
                return True

            def visit(node):
                if (isinstance(node, ast.Call) and node.name == "perform"
                        and node.args
                        and isinstance(node.args[0], ast.StringLit)):
                    text = "".join(
                        p.text for p in node.args[0].parts
                        if isinstance(p, ast.StringText)
                    )
                    if text in events and hit[0] is None \
                            and not redirects_elsewhere(node):
                        hit[0] = (getattr(node, "line", h.line), text)
                    return
                if not dataclasses.is_dataclass(node):
                    return
                for f in dataclasses.fields(node):
                    v = getattr(node, f.name)
                    if isinstance(v, list):
                        for item in v:
                            if dataclasses.is_dataclass(item):
                                visit(item)
                    elif dataclasses.is_dataclass(v):
                        visit(v)

            for s in h.body:
                visit(s)
            if hit[0] is not None:
                line, ev = hit[0]
                print(
                    f"arcc: note: line {line}: 'on {ev}' performs its own "
                    f"action; perform re-enters the whole handler chain, "
                    f"this handler included, so an unguarded self-perform "
                    f"never returns. End with `continue` to reach the "
                    f"default instead, or add a `when` guard (or an operand "
                    f"pattern) the re-entry fails.",
                    file=sys.stderr,
                )

    def _resolve_subjects(self) -> None:
        """Tie every `topic <id>` that names a declared SUBJECT to it: the
        topic inherits the subject's match words, its label unless it wrote
        one of its own, and its default exchange unless it wrote a body. A
        topic that names no subject must carry its own label, as before."""
        w = self.world
        owners = [(n, o.topics) for n, o in w.objects.items()]
        owners += [(n, k.topics) for n, k in w.kinds.items()]
        for owner, topics in owners:
            for t in topics:
                subj = w.subjects.get(t.subject)
                if subj is None:
                    if t.label is None:
                        raise self._error(
                            f"topic '{t.subject}' needs a label (the line the "
                            f"conversations menu shows), or must name a "
                            f"`subject` declared elsewhere to inherit one",
                            t.line,
                        )
                    continue
                if t.words:
                    raise self._error(
                        f"topic '{t.subject}' names a subject, which already "
                        f"owns the match words; drop the `words` here (edit "
                        f"the subject to change them for the whole cast)",
                        t.line,
                    )
                t.words = list(subj.words)
                if t.label is None:
                    t.label = subj.label
                if not t.body and not t.idle:
                    if not subj.body:
                        raise self._error(
                            f"topic '{t.subject}' has no body and subject "
                            f"'{t.subject}' declares no default exchange: "
                            f"give one of them something to say",
                            t.line,
                        )
                    t.body = list(subj.body)

    def _grain_home_rooms(self, name: str) -> set:
        """The rooms a grain owner is statically at home in: a room is its
        own home; a thing's home is the room its `in` chain reaches, plus
        every room it spans. Used to tell deliberate cross-room word reuse
        (disjoint homes, documented and quiet) from a co-located collision
        (the same room, where only the first grain can ever answer)."""
        w = self.world
        obj = w.objects.get(name)
        if obj is None:
            return set()
        if obj.category == "room":
            return {name}
        rooms = set(obj.spans or [])
        seen: set = set()
        cur = obj
        while cur is not None and cur.name not in seen:
            seen.add(cur.name)
            if cur.category == "room":
                rooms.add(cur.name)
                break
            cur = w.objects.get(cur.location) if cur.location else None
        return rooms

    def _lint_grain_word_split(self) -> None:
        """A word answers with ONE grain, so a second grain for the same word
        leaves the later one dead wherever both are in scope: the parser
        finds the first grain for the word and that one answers, whatever
        verb was typed. Two shapes are noted, each silent-and-baffling in
        play until now (both field reports): the same owner splitting a word
        across two lines, and two CO-LOCATED owners (a room and a scenery
        thing standing in it) sharing a word. Deliberate reuse across
        DISJOINT rooms stays quiet, as documented."""
        owners = {}
        for name, obj in self.world.objects.items():
            owners[name] = obj.grains
        for kname, kind in self.world.kinds.items():
            owners.setdefault(kname, []).extend(kind.grains)
        claimed = {}  # word -> (owner, line) that first claimed it, per owner
        for owner, grains in owners.items():
            seen = {}  # word -> the line that first claimed it
            for g in grains:
                for w in g.words:
                    key = w.lower()
                    if key in seen and seen[key] != g.line:
                        print(
                            f"arcc: note: line {g.line}: '{owner}' already "
                            f"answers \"{w}\" with the grain on line "
                            f"{seen[key]}, and a word answers with ONE grain, "
                            f"so this line never runs. Put the verbs on one "
                            f"line (examine, touch \"{w}\" say ...), or use a "
                            f"`scenery` thing with its own handlers if the "
                            f"answers differ per verb.",
                            file=sys.stderr,
                        )
                    else:
                        seen.setdefault(key, g.line)
                    claimed.setdefault(key, []).append((owner, g.line))
        # The cross-owner collision: the same word on two owners whose home
        # rooms overlap. Where both are in scope the first declared answers
        # and the other grain is dead there, with nothing to say so at
        # runtime.
        for word, sites in claimed.items():
            distinct = []
            for owner, line in sites:
                if not any(o == owner for o, _l in distinct):
                    distinct.append((owner, line))
            if len(distinct) < 2:
                continue
            for i in range(len(distinct)):
                for j in range(i + 1, len(distinct)):
                    a, la = distinct[i]
                    b, lb = distinct[j]
                    shared = self._grain_home_rooms(a) & self._grain_home_rooms(b)
                    if shared:
                        where = sorted(shared)[0]
                        print(
                            f"arcc: note: line {lb}: '{b}' answers \"{word}\" "
                            f"with a grain, but '{a}' (line {la}) already "
                            f"does, and both are in scope in '{where}'. A "
                            f"word answers with ONE grain, the first "
                            f"declared, so '{b}'s never runs there. Put "
                            f"every verb for \"{word}\" on one grain line, "
                            f"or give the answers to a `scenery` thing's "
                            f"handlers.",
                            file=sys.stderr,
                        )

    def _lint_alter_without_continue(self) -> None:
        """`alter` REGISTERS a report that the library speaks at the action's
        success (docs/01). A handler that alters but never `continue`s dies at
        the handler level, the general handler design: the action is consumed
        here, the library's success site never runs, and the registered report
        can never fire. That combination is always a mistake and fails silently
        (no message, and the action itself does not happen), so say it, as a
        note, naming the alter's line and the cure. A `continue` inside the
        alter block does not count: that block is the report's text, not
        handler flow, so continues are collected from the handler body only,
        with the alter's own body skipped."""
        for h in self.world.all_handlers():
            alter_line = None
            has_continue = False

            def visit(node):
                nonlocal alter_line, has_continue
                if isinstance(node, ast.Alter):
                    if alter_line is None:
                        alter_line = node.line
                    return  # its body is the report, not handler flow
                if isinstance(node, ast.Continue):
                    has_continue = True
                    return
                if not dataclasses.is_dataclass(node):
                    return
                for f in dataclasses.fields(node):
                    v = getattr(node, f.name)
                    if isinstance(v, list):
                        for item in v:
                            if dataclasses.is_dataclass(item):
                                visit(item)
                    elif dataclasses.is_dataclass(v):
                        visit(v)

            for s in h.body:
                visit(s)
            if alter_line is not None and not has_continue:
                print(
                    f"arcc: note: line {alter_line}: this handler alters but "
                    f"never continues, so it consumes the action here and the "
                    f"altered report can never fire (nor does the action "
                    f"happen); add `continue` in the handler body, after the "
                    f"alter, to hand the action to the library",
                    file=sys.stderr,
                )

    def _lint_nautical_land_start(self) -> None:
        """A diagnostic for the shipped nautical granule (docs/01 chapter 22). Its
        `dirs_nautical` flag defaults to TRUE, meaning aboard: the four
        nautical directions are live and a bad one answers with the generic
        "no exit". A game that BEGINS ASHORE must set the flag false at the
        start, or the opening room silently gets that generic refusal instead
        of the nautical one (a field report). If the granule is in use, the
        start room declares no nautical exit (so it is likely dry land), and
        no `on start` rule already sets the flag, say so."""
        w = self.world
        if "dirs_nautical" not in w.globals or w.start_room is None:
            return
        start = w.objects.get(w.start_room)
        if start is None:
            return
        from . import objects as objmod
        eff = objmod._effective_props(w, start)
        if any(d in eff for d in ("fore", "aft", "port", "starboard")):
            return  # the start room IS nautical: the default (aboard) is right
        for h in w.free_handlers:
            if "start" in h.events and self._sets_flag(h.body, "dirs_nautical"):
                return  # the author already manages the flag at the start
        print(
            f"arcc: note: the nautical granule is summoned and the start room "
            f"'{w.start_room}' has no fore/aft/port/starboard exit. "
            f"dirs_nautical defaults to true (aboard), so a nautical direction "
            f"there answers 'no exit' rather than the nautical refusal. If the "
            f"start is dry land, set `change dirs_nautical to false` at the "
            f"start (an `on start` rule).",
            file=sys.stderr,
        )

    def _sets_flag(self, body, name: str) -> bool:
        """Does this statement body assign the named flag anywhere (a `change
        <flag> to ...`)? A generic dataclass walk, so nested ifs and loops
        are covered."""
        found = [False]

        def visit(node):
            if isinstance(node, ast.Change) and isinstance(
                getattr(node, "target", None), ast.Name
            ) and node.target.ident == name:
                found[0] = True
                return
            if not dataclasses.is_dataclass(node):
                return
            for f in dataclasses.fields(node):
                v = getattr(node, f.name)
                if isinstance(v, list):
                    for item in v:
                        if dataclasses.is_dataclass(item):
                            visit(item)
                elif dataclasses.is_dataclass(v):
                    visit(v)

        for s in body:
            visit(s)
        return found[0]


def analyze(
    program: ast.Program,
    env: Optional[prelude.Environment] = None,
    filename: str = "<source>",
) -> wm.World:
    world = Analyzer(program, env, filename).analyze()
    # The weight budget spells in units like the weight property does
    # (docs/01 chapter 6): under summon.carryweight a bare-integer
    # `constant weight_cap = 20` or `global carry_weight = 20` means
    # twenty whole units, stored as tenths, exactly like `weight 2`.
    # Pointed literals arrive as tenths already.
    if wm.has_summon(world, "carryweight"):
        for holder in (world.constants.get("weight_cap"),
                       world.globals.get("carry_weight")):
            v = getattr(holder, "value", None)
            if isinstance(v, ast.Number) and not v.tenths:
                holder.value = ast.Number(v.value * 10, v.line, tenths=True)
    return world
