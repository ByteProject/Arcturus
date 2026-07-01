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

    def _error(self, message: str, line: int) -> ArcError:
        return ArcError(message, line, None, self.filename)

    # -- entry -------------------------------------------------------------

    def analyze(self) -> wm.World:
        self._collect()
        self._resolve_kinds()
        self._build_properties()
        self._resolve_bodies()
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
            # Rooms are lit by default; a dark room declares `lit false`. People
            # are animate by default. Both override per instance.
            if sk.name == "room":
                kind.props["lit"] = ast.PropertyDecl(name="lit", form=ast.PROP_BOOL)
            elif sk.name == "person":
                kind.props["animate"] = ast.PropertyDecl(name="animate", form=ast.PROP_BOOL)
            w.kinds[sk.name] = kind
        # Seed standard objects (player).
        for name, kind in self.env.objects.items():
            w.objects[name] = wm.Obj(name, "thing", kind, line=0)

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
                    decl=decl,
                    line=decl.line,
                )
            elif isinstance(decl, ast.VerbDecl):
                grammar = [wm.GrammarLine(g.action, g.items) for g in decl.grammar]
                w.verbs.append(wm.Verb(decl.words, grammar, decl.line))
            elif isinstance(decl, ast.GlobalDecl):
                self._seen(decl.name, decl.line)
                w.globals[decl.name] = wm.Global(
                    decl.name, self._value_type(decl.value), decl.value, decl.line
                )
            elif isinstance(decl, ast.ConstantDecl):
                self._seen(decl.name, decl.line)
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

        # Game property declarations on kinds and objects.
        for kind in w.kinds.values():
            if kind.decl is not None:
                self._collect_members(kind.decl.members, kind.name, kind.props, True)
        for obj in w.objects.values():
            if obj.decl is not None:
                self._collect_members(obj.decl.members, obj.name, obj.props, False)

    def _collect_members(self, members, owner, props_out, on_kind) -> None:
        w = self.world
        for m in members:
            if isinstance(m, ast.PropertyDecl):
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
                self._check_handler(m)
            elif isinstance(m, ast.GrainsBlock):
                for g in m.grains:
                    self._check_grain(g)

    def _check_handler(self, h) -> None:
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
                    self._check_operand(name, line)
        if when is not None:
            self._check_condition(when, set(), line)
        self._check_body(body, set())

    def _check_operand(self, name: str, line: int) -> None:
        w = self.world
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
        elif isinstance(s, ast.Say):
            self._check_expr(s.value, locals_)
        elif isinstance(s, (ast.Stop, ast.Continue)):
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
                self.world.is_resolutions[id(expr)] = wm.IS_PROPERTY
                return
            if right.ident in self.world.kinds:
                self.world.is_resolutions[id(expr)] = wm.IS_KIND
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


def analyze(
    program: ast.Program,
    env: Optional[prelude.Environment] = None,
    filename: str = "<source>",
) -> wm.World:
    return Analyzer(program, env, filename).analyze()
