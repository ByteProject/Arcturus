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

import sys
from typing import Optional

from . import ast
from . import prelude
from . import worldmodel as wm
from .errors import ArcError


class Analyzer:
    def __init__(
        self,
        program: ast.Program,
        env: Optional[prelude.Environment] = None,
        filename: str = "<source>",
    ) -> None:
        self.program = program
        self.env = env if env is not None else prelude.standard_environment()
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
        self._build_properties()
        # After the members are collected: the automatic scored bits need
        # the real attributes (fixed blocks a thing, `scored false` opts
        # out), and the award scan feeds the compiler-summed max_score.
        self._auto_score()
        self._resolve_bodies()
        self._scan_awards()
        self._lint_unread_props()
        # A summoned abbreviations.granule (B6) is compile-time data, not runtime
        # blocks, so it rides on the program straight through to codegen.
        self.world.abbreviations = getattr(self.program, "abbreviations", None)
        return self.world

    # -- pass 1: collect ---------------------------------------------------

    def _seen(self, name: str, line: int) -> None:
        if (
            name in self.world.objects
            or name in self.world.kinds
            or name in self.world.globals
            or name in self.world.constants
            or name in self.world.blocks
        ):
            raise self._error(f"duplicate declaration of '{name}'", line)

    def _collect(self) -> None:
        w = self.world
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
        # Seed the scope room on demand (docs/01 section 5, Stefan's design):
        # `in scope` places an object BACKSTAGE, an invisible room whose
        # contents the parser always has in scope. Nothing is seeded, and
        # nothing costs a byte, unless some object asks for it.
        if any(
            isinstance(d, ast.ObjectDecl) and d.location == "scope"
            for d in self.program.decls
        ) and "scope" not in w.objects:
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
                    spans=list(decl.spans),
                    decl=decl,
                    line=decl.line,
                )
            elif isinstance(decl, ast.VerbDecl):
                grammar = [wm.GrammarLine(g.action, g.items, g.reverse) for g in decl.grammar]
                w.verbs.append(wm.Verb(decl.words, grammar, decl.line))
                # `verb ... meta`: its actions join the out-of-world band
                # (dispatched past every object handler, `on other` included).
                if decl.meta:
                    for g in decl.grammar:
                        w.meta_actions.add(g.action)
            elif isinstance(decl, ast.DirectionDecl):
                if not self.env.is_direction(decl.prop):
                    raise self._error(
                        f"'{decl.prop}' is not a standard direction property",
                        decl.line,
                    )
                for word in decl.words:
                    w.directions[word.lower()] = decl.prop
            elif isinstance(decl, ast.PlayerDecl):
                # Collected now, applied in the properties pass (below), where
                # types unify and the words lists merge.
                self._player_decls.append(decl.prop)
            elif isinstance(decl, ast.PronounDecl):
                if decl.role not in prelude._PRONOUN_ROLES:
                    roles = ", ".join(prelude._PRONOUN_ROLES)
                    raise self._error(
                        f"'{decl.role}' is not a pronoun role (use one of: {roles})",
                        decl.line,
                    )
                for word in decl.words:
                    w.pronouns[word.lower()] = decl.role
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
                w.constants[decl.name] = wm.Constant(
                    decl.name, self._value_type(decl.value), decl.value, decl.line
                )
            elif isinstance(decl, ast.BlockDecl):
                prior = w.blocks.get(decl.name)
                # A game or granule block overrides a library block of the same
                # name; any other repeat is a genuine duplicate.
                if prior is not None and prior.origin == "library" and decl.origin != "library":
                    pass
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

        # Actions: the standard set plus every action a verb grammar names.
        w.actions = set(self.env.actions)
        for verb in w.verbs:
            for line in verb.grammar:
                w.actions.add(line.action)

        # A verb whose grammar the flag model cannot represent gets a positional
        # grammar table (docs/02 section 8c). The table matcher walks each line
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
            # A spanned name is a declared room, or a room KIND (docs/01 section
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
                    player.props[m.name] = m

        # Game property declarations on kinds and objects.
        for kind in w.kinds.values():
            if kind.decl is not None:
                self._collect_members(kind.decl.members, kind.name, kind.props, True)
        for obj in w.objects.values():
            if obj.decl is not None:
                self._collect_members(obj.decl.members, obj.name, obj.props, False)

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
                if m.name == "arc_image":
                    m = ast.PropertyDecl(
                        name="arc_image",
                        form=m.form,
                        values=[ast.Number(self._image_id(m), m.line)],
                        line=m.line,
                    )
                    w.uses_images = True
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
                # Ambience blocks (docs/05) live on objects, not kinds, and
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
                w.objects[owner].ambiences.append(m)
            elif isinstance(m, ast.TopicDecl):
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
            self._check_body(blk.body, set(blk.params))
        # Attached grains and game start.
        for decl in self.program.decls:
            if isinstance(decl, ast.GrainsAttach):
                if decl.target not in w.objects:
                    raise self._error(
                        f"grains attached to unknown object '{decl.target}'",
                        decl.line,
                    )
                for g in decl.grains:
                    self._check_grain(g)
        if w.start_room is not None and w.start_room not in w.objects:
            line = w.game.line if w.game else 0
            raise self._error(
                f"game start room '{w.start_room}' is not defined", line
            )

    def _resolve_owner(self, members, on_kind: bool) -> None:
        for m in members:
            if isinstance(m, ast.PropertyDecl) and m.form == ast.PROP_BLOCK:
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
        locals_ = set(locals_)
        for s in stmts:
            self._check_stmt(s, locals_)

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
        elif isinstance(s, ast.If):
            for clause in s.clauses:
                if clause.cond is not None:
                    self._check_condition(clause.cond, locals_, clause.line)
                self._check_body(clause.body, locals_)
        elif isinstance(s, ast.While):
            self._check_condition(s.cond, locals_, s.line)
            self._check_body(s.body, locals_)
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
        # A bare identifier naming a boolean property is a property test; a kind
        # name is a kind-membership test; otherwise the comparison is an equality
        # (docs/01 section 9).
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
        self.world.is_resolutions[id(expr)] = wm.IS_EQUALITY
        self._check_expr(right, locals_)

    def _resolve_name(self, name: str, locals_: set, line: int) -> None:
        w = self.world
        if (
            name in locals_
            or name in w.objects
            or name in w.kinds
            or name in w.globals
            or name in w.constants
            or name in w.blocks
            or name in self.env.builtins
            or self.env.is_direction(name)
        ):
            return
        # A bare intrinsic name is a zero-argument call (print_banner,
        # read_key); lower resolves it after every data name.
        from .lower import INTRINSICS
        if name in INTRINSICS:
            return
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
        skip = {"tag"}  # the listing qualifier rides props but is not one
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


def analyze(
    program: ast.Program,
    env: Optional[prelude.Environment] = None,
    filename: str = "<source>",
) -> wm.World:
    return Analyzer(program, env, filename).analyze()
