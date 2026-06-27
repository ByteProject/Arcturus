# lower.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Lowering of Arcturus expressions, statements, and control flow to Z-machine
code within a routine (milestone B4.2).

The value model is stack-based and dense: an expression evaluates onto the
stack, a computing opcode stores its result wherever the destination asks
(the stack by default), and binary operands are pushed right-first so the
opcode reads them in source order. The one exception preserves source-order
side effects: when an operand contains a block call, the left operand is
evaluated into a temporary first. Conditions never materialize a boolean; they
branch directly, with short-circuit `and`/`or` and `not` folded into the
branch targets.

Object-touching constructs (property and attribute access, the tree
operations, `for each`, string switches, object and article printing) are
deferred to B4.3, where the object table exists; this module raises a clear
LowerError for them.
"""

from __future__ import annotations

from . import ast
from . import worldmodel as wm
from .assembler import Const, Routine, Variable, RoutineRef, STACK
from .errors import ArcError

_ARITH = {"+": "add", "-": "sub", "*": "mul", "/": "div", "mod": "mod"}
_MAX_LOCALS = 15

# Builtin references that hold an object number at run time (docs/02 section 2).
_OBJECT_BUILTINS = {"player", "here", "noun", "second", "self"}


class LowerError(ArcError):
    pass


class Context:
    """Per-routine state: the local-variable assignment and a temporary pool
    above the named locals."""

    def __init__(self, world: wm.World, globals_map: dict, params=(), layout=None):
        self.world = world
        self.globals = globals_map
        self.layout = layout
        self.named: dict[str, int] = {}
        slot = 1
        for p in params:
            self.named[p] = slot
            slot += 1
        self.temp_base = slot  # set properly after prescan
        self.temp_top = slot
        self.peak = slot - 1
        self._label_n = 0

    def prescan(self, body) -> None:
        names: list[str] = []
        _collect_lets(body, names)
        slot = len(self.named) + 1
        for name in names:
            if name not in self.named:
                self.named[name] = slot
                slot += 1
        self.temp_base = slot
        self.temp_top = slot
        self.peak = slot - 1

    def alloc_temp(self) -> int:
        slot = self.temp_top
        self.temp_top += 1
        if self.temp_top - 1 > _MAX_LOCALS:
            raise LowerError(
                "expression too deep: more than 15 locals needed (stack spill "
                "is a later milestone)"
            )
        self.peak = max(self.peak, self.temp_top - 1)
        return slot

    def free_temp(self, slot: int) -> None:
        self.temp_top = slot

    def new_label(self) -> str:
        self._label_n += 1
        return f"L{self._label_n}"

    def nlocals(self) -> int:
        return max(self.peak, len(self.named))

    def resolve_var(self, name: str, line: int) -> int:
        if name in self.named:
            return self.named[name]
        if name in self.globals:
            return self.globals[name]
        raise LowerError(f"unresolved name '{name}'", line)

    def is_object_name(self, name: str) -> bool:
        return self.layout is not None and name in self.layout.obj_number

    def obj_number(self, name: str) -> int:
        return self.layout.obj_number[name]

    def attr_number(self, name: str):
        return None if self.layout is None else self.layout.attr_number.get(name)

    def prop_number(self, name: str):
        return None if self.layout is None else self.layout.prop_number.get(name)


def _collect_lets(body, out: list) -> None:
    for s in body:
        if isinstance(s, ast.Let):
            out.append(s.name)
        elif isinstance(s, ast.If):
            for c in s.clauses:
                _collect_lets(c.body, out)
        elif isinstance(s, ast.While):
            _collect_lets(s.body, out)
        elif isinstance(s, ast.ForEach):
            out.append(s.var)
            _collect_lets(s.body, out)
        elif isinstance(s, ast.Switch):
            for c in s.cases:
                _collect_lets(c.body, out)


def _has_call(expr) -> bool:
    if isinstance(expr, ast.Call):
        return True
    for child in _children(expr):
        if _has_call(child):
            return True
    return False


def _children(expr):
    if isinstance(expr, (ast.Unary,)):
        return [expr.operand]
    if isinstance(expr, (ast.Binary, ast.Logic, ast.IsTest)):
        return [expr.left, expr.right]
    if isinstance(expr, ast.Call):
        return list(expr.args)
    return []


# --------------------------------------------------------------------------
# Expression evaluation
# --------------------------------------------------------------------------


def _is_leaf(ctx: Context, expr) -> bool:
    if isinstance(expr, (ast.Number, ast.Bool, ast.Nothing)):
        return True
    if isinstance(expr, ast.Name):
        return (
            expr.ident in ctx.named
            or expr.ident in ctx.globals
            or ctx.is_object_name(expr.ident)
        )
    return False


def _leaf_operand(ctx: Context, expr):
    if isinstance(expr, ast.Number):
        return Const(expr.value)
    if isinstance(expr, ast.Bool):
        return Const(1 if expr.value else 0)
    if isinstance(expr, ast.Nothing):
        return Const(0)  # the null object
    if isinstance(expr, ast.Name):
        if expr.ident in ctx.named or expr.ident in ctx.globals:
            return Variable(ctx.resolve_var(expr.ident, expr.line))
        if ctx.is_object_name(expr.ident):
            return Const(ctx.obj_number(expr.ident))  # an object number constant
        raise LowerError(f"unresolved name '{expr.ident}'", expr.line)
    raise LowerError("not a leaf expression", getattr(expr, "line", 0))


def _place(rt: Routine, value_operand, dest):
    if dest.value == STACK:
        rt.op("push", value_operand)
    else:
        rt.op("store", Const(dest.value), value_operand)


def eval_expr(rt: Routine, ctx: Context, expr, dest=None) -> None:
    """Compute expr's value into dest (a Variable; the stack by default)."""
    if dest is None:
        dest = Variable(STACK)

    if _is_leaf(ctx, expr):
        _place(rt, _leaf_operand(ctx, expr), dest)
        return

    if isinstance(expr, ast.Binary):
        if expr.op in _ARITH:
            _binop(rt, ctx, _ARITH[expr.op], expr.left, expr.right, dest)
            return
        # A comparison or tree test used as a value: materialize 0/1.
        _materialize_bool(rt, ctx, expr, dest)
        return

    if isinstance(expr, (ast.IsTest, ast.Logic)):
        _materialize_bool(rt, ctx, expr, dest)
        return

    if isinstance(expr, ast.Unary):
        if expr.op == "-":
            opb, t = _operand(rt, ctx, expr.operand)
            rt.op("sub", Const(0), opb, store=dest)
            if t is not None:
                ctx.free_temp(t)
            return
        _materialize_bool(rt, ctx, expr, dest)  # not
        return

    if isinstance(expr, ast.Call):
        _call(rt, ctx, expr, dest)
        return

    if isinstance(expr, ast.Dot):
        pnum = ctx.prop_number(expr.prop)
        if pnum is None:
            raise LowerError(
                f"cannot read property '{expr.prop}' as a value", expr.line
            )
        objop, t = _operand(rt, ctx, expr.obj)
        rt.op("get_prop", objop, Const(pnum), store=dest)
        if t is not None:
            ctx.free_temp(t)
        return

    if isinstance(expr, ast.DynDot):
        raise LowerError(
            "computed property access needs the parser (B4.5)", expr.line
        )

    raise LowerError("unsupported expression", getattr(expr, "line", 0))


def _operand(rt: Routine, ctx: Context, expr):
    """Return (operand, temp_or_None) for use as one operand of an opcode,
    evaluating complex expressions to the stack."""
    if _is_leaf(ctx, expr):
        return _leaf_operand(ctx, expr), None
    eval_expr(rt, ctx, expr, Variable(STACK))
    return Variable(STACK), None


def _two_operands(rt: Routine, ctx: Context, a, b):
    """Operands for a binary opcode, in source order. Returns (opa, opb, temp)."""
    a_leaf = _is_leaf(ctx, a)
    b_leaf = _is_leaf(ctx, b)
    if a_leaf and b_leaf:
        return _leaf_operand(ctx, a), _leaf_operand(ctx, b), None
    if a_leaf:
        eval_expr(rt, ctx, b, Variable(STACK))
        return _leaf_operand(ctx, a), Variable(STACK), None
    if b_leaf:
        eval_expr(rt, ctx, a, Variable(STACK))
        return Variable(STACK), _leaf_operand(ctx, b), None
    if _has_call(a) or _has_call(b):
        t = ctx.alloc_temp()
        eval_expr(rt, ctx, a, Variable(t))
        eval_expr(rt, ctx, b, Variable(STACK))
        return Variable(t), Variable(STACK), t
    # Both pure and complex: push right then left, read in source order.
    eval_expr(rt, ctx, b, Variable(STACK))
    eval_expr(rt, ctx, a, Variable(STACK))
    return Variable(STACK), Variable(STACK), None


def _binop(rt, ctx, opname, a, b, dest):
    opa, opb, t = _two_operands(rt, ctx, a, b)
    rt.op(opname, opa, opb, store=dest)
    if t is not None:
        ctx.free_temp(t)


def _call(rt, ctx, expr: ast.Call, dest):
    if expr.name not in ctx.world.blocks:
        raise LowerError(f"call to unknown block '{expr.name}'", expr.line)
    # Push arguments right-first so they pop in order behind the routine address.
    for arg in reversed(expr.args):
        eval_expr(rt, ctx, arg, Variable(STACK))
    operands = [RoutineRef("blk_" + expr.name)]
    operands += [Variable(STACK)] * len(expr.args)
    rt.op("call_vs", *operands, store=dest)


def _materialize_bool(rt, ctx, expr, dest):
    """Set dest to 1 if expr is true, else 0, via a branch."""
    true_l = ctx.new_label()
    end_l = ctx.new_label()
    cond_jump(rt, ctx, expr, true_l, True)
    _place(rt, Const(0), dest)
    rt.jump(end_l)
    rt.label(true_l)
    _place(rt, Const(1), dest)
    rt.label(end_l)


# --------------------------------------------------------------------------
# Conditions (branch directly, no boolean materialized)
# --------------------------------------------------------------------------


def cond_jump(rt: Routine, ctx: Context, expr, label: str, on_true: bool) -> None:
    if isinstance(expr, ast.Logic):
        if expr.op == "and":
            if on_true:
                skip = ctx.new_label()
                cond_jump(rt, ctx, expr.left, skip, False)
                cond_jump(rt, ctx, expr.right, label, True)
                rt.label(skip)
            else:
                cond_jump(rt, ctx, expr.left, label, False)
                cond_jump(rt, ctx, expr.right, label, False)
        else:  # or
            if on_true:
                cond_jump(rt, ctx, expr.left, label, True)
                cond_jump(rt, ctx, expr.right, label, True)
            else:
                skip = ctx.new_label()
                cond_jump(rt, ctx, expr.left, skip, True)
                cond_jump(rt, ctx, expr.right, label, False)
                rt.label(skip)
        return
    if isinstance(expr, ast.Unary) and expr.op == "not":
        cond_jump(rt, ctx, expr.operand, label, not on_true)
        return
    _emit_test(rt, ctx, expr, label, on_true)


def _emit_test(rt, ctx, expr, label, on_true):
    if isinstance(expr, ast.Binary) and expr.op in ("<", ">", "<=", ">="):
        op, t = expr.op, on_true
        if op == "<=":
            op, t = ">", not t
        elif op == ">=":
            op, t = "<", not t
        zop = "jl" if op == "<" else "jg"
        opa, opb, tmp = _two_operands(rt, ctx, expr.left, expr.right)
        rt.op(zop, opa, opb, branch=(label, t))
        if tmp is not None:
            ctx.free_temp(tmp)
        return
    if isinstance(expr, ast.IsTest):
        res = ctx.world.is_resolutions.get(id(expr))
        if res == wm.IS_PROPERTY:
            _attr_test(rt, ctx, expr, label, on_true)
            return
        t = not on_true if expr.negated else on_true
        opa, opb, tmp = _two_operands(rt, ctx, expr.left, expr.right)
        rt.op("je", opa, opb, branch=(label, t))
        if tmp is not None:
            ctx.free_temp(tmp)
        return
    if isinstance(expr, ast.Binary) and expr.op in ("holds", "in"):
        # holds: left holds right => right is in left; in: left is in right.
        if expr.op == "holds":
            child, parent = expr.right, expr.left
        else:
            child, parent = expr.left, expr.right
        opa, opb, tmp = _two_operands(rt, ctx, child, parent)
        rt.op("jin", opa, opb, branch=(label, on_true))
        if tmp is not None:
            ctx.free_temp(tmp)
        return
    # Any other expression: evaluate to a value and test against zero.
    op, t = _operand(rt, ctx, expr)
    rt.op("jz", op, branch=(label, not on_true))
    if t is not None:
        ctx.free_temp(t)


def _attr_test(rt, ctx, expr: ast.IsTest, label, on_true):
    prop = expr.right.ident
    attr = ctx.attr_number(prop)
    t = not on_true if expr.negated else on_true
    objop, tmp = _operand(rt, ctx, expr.left)
    if attr is not None:
        rt.op("test_attr", objop, Const(attr), branch=(label, t))
    else:  # a boolean stored as a slot property: read it and test against zero
        pnum = ctx.prop_number(prop)
        rt.op("get_prop", objop, Const(pnum), store=Variable(STACK))
        rt.op("jz", Variable(STACK), branch=(label, not t))
    if tmp is not None:
        ctx.free_temp(tmp)


# --------------------------------------------------------------------------
# Statements
# --------------------------------------------------------------------------


def compile_block(rt: Routine, ctx: Context, body) -> None:
    for stmt in body:
        compile_stmt(rt, ctx, stmt)


def compile_stmt(rt: Routine, ctx: Context, s) -> None:
    if isinstance(s, ast.Let):
        eval_expr(rt, ctx, s.value, Variable(ctx.resolve_var(s.name, s.line)))
    elif isinstance(s, ast.Change):
        _change(rt, ctx, s)
    elif isinstance(s, ast.Say):
        _say(rt, ctx, s.value)
    elif isinstance(s, ast.Return):
        if s.value is None:
            rt.op("rfalse")
        else:
            op, t = _operand(rt, ctx, s.value)
            rt.op("ret", op)
            if t is not None:
                ctx.free_temp(t)
    elif isinstance(s, ast.Finish):
        if s.message is not None:
            _say(rt, ctx, s.message)
        rt.op("quit")
    elif isinstance(s, ast.Stop):
        rt.op("rfalse")
    elif isinstance(s, ast.If):
        _if(rt, ctx, s)
    elif isinstance(s, ast.While):
        _while(rt, ctx, s)
    elif isinstance(s, ast.Switch):
        _switch(rt, ctx, s)
    elif isinstance(s, ast.ExprStmt):
        if isinstance(s.expr, ast.Call):
            _call(rt, ctx, s.expr, Variable(STACK))
            rt.op("pull", Variable(STACK))  # discard the result
        else:
            eval_expr(rt, ctx, s.expr, Variable(STACK))
            rt.op("pull", Variable(STACK))
    elif isinstance(s, ast.Now):
        _now(rt, ctx, s)
    elif isinstance(s, ast.Move):
        _move(rt, ctx, s)
    elif isinstance(s, (ast.Add, ast.Remove)):
        raise LowerError("list properties need the dictionary stage (B4.4)", s.line)
    elif isinstance(s, ast.Continue):
        raise LowerError("'continue' belongs to action dispatch (B4.5)", s.line)
    elif isinstance(s, ast.ForEach):
        raise LowerError("'for each' needs the object table (B4.3)", s.line)
    elif isinstance(s, ast.Schedule):
        raise LowerError("scheduling needs the turn loop (B4.5)", s.line)
    else:
        raise LowerError("unsupported statement in B4.2", getattr(s, "line", 0))


def _change(rt, ctx, s: ast.Change):
    if isinstance(s.target, ast.Name):
        eval_expr(rt, ctx, s.value, Variable(ctx.resolve_var(s.target.ident, s.line)))
        return
    if isinstance(s.target, ast.Dot):
        pnum = ctx.prop_number(s.target.prop)
        if pnum is None:
            raise LowerError(
                f"cannot change property '{s.target.prop}'", s.line
            )
        if isinstance(s.value, ast.StringLit):
            raise LowerError(
                "writing a text property needs string allocation (B4.5)", s.line
            )
        valop, tv = _operand(rt, ctx, s.value)
        objop, to = _operand(rt, ctx, s.target.obj)
        rt.op("put_prop", objop, Const(pnum), valop)
        if to is not None:
            ctx.free_temp(to)
        if tv is not None:
            ctx.free_temp(tv)
        return
    raise LowerError("unsupported change target", s.line)


def _now(rt, ctx, s: ast.Now):
    attr = ctx.attr_number(s.prop)
    objop, t = _operand(rt, ctx, s.target)
    if attr is not None:
        rt.op("clear_attr" if s.negated else "set_attr", objop, Const(attr))
    else:
        pnum = ctx.prop_number(s.prop)
        if pnum is None:
            raise LowerError(f"unknown property '{s.prop}'", s.line)
        rt.op("put_prop", objop, Const(pnum), Const(0 if s.negated else 1))
    if t is not None:
        ctx.free_temp(t)


def _move(rt, ctx, s: ast.Move):
    if isinstance(s.dest, ast.Nothing):
        objop, t = _operand(rt, ctx, s.obj)
        rt.op("remove_obj", objop)
        if t is not None:
            ctx.free_temp(t)
        return
    opa, opb, tmp = _two_operands(rt, ctx, s.obj, s.dest)
    rt.op("insert_obj", opa, opb)
    if tmp is not None:
        ctx.free_temp(tmp)


def _say(rt, ctx, value):
    if isinstance(value, ast.StringLit):
        for part in value.parts:
            if isinstance(part, ast.StringText):
                if part.text:
                    rt.op("print", text=part.text)
            else:  # StringInterp
                if part.article is not None:
                    # The a/an choice by sound is a Cosmos refinement (B4.5);
                    # for now the typed article is printed as written.
                    rt.op("print", text=part.article + " ")
                    _say_object(rt, ctx, part.expr)
                else:
                    _say_value(rt, ctx, part.expr)
    else:
        _say_value(rt, ctx, value)
    rt.op("new_line")


def _is_object_expr(ctx, expr) -> bool:
    if isinstance(expr, ast.Name):
        return ctx.is_object_name(expr.ident) or expr.ident in _OBJECT_BUILTINS
    return False


def _say_value(rt, ctx, expr):
    if _is_object_expr(ctx, expr):
        _say_object(rt, ctx, expr)
        return
    if isinstance(expr, ast.Dot) and ctx.world.properties.get(
        expr.prop
    ) and ctx.world.properties[expr.prop].type == "text":
        # A text property holds a packed string address.
        op, t = _operand(rt, ctx, expr)  # get_prop is handled by eval via _operand
        rt.op("print_paddr", op)
        if t is not None:
            ctx.free_temp(t)
        return
    op, t = _operand(rt, ctx, expr)
    rt.op("print_num", op)
    if t is not None:
        ctx.free_temp(t)


def _say_object(rt, ctx, expr):
    op, t = _operand(rt, ctx, expr)
    rt.op("print_obj", op)
    if t is not None:
        ctx.free_temp(t)


def _if(rt, ctx, s: ast.If):
    end = ctx.new_label()
    for clause in s.clauses:
        if clause.cond is None:
            compile_block(rt, ctx, clause.body)
        else:
            nxt = ctx.new_label()
            cond_jump(rt, ctx, clause.cond, nxt, False)
            compile_block(rt, ctx, clause.body)
            rt.jump(end)
            rt.label(nxt)
    rt.label(end)


def _while(rt, ctx, s: ast.While):
    top = ctx.new_label()
    end = ctx.new_label()
    rt.label(top)
    cond_jump(rt, ctx, s.cond, end, False)
    compile_block(rt, ctx, s.body)
    rt.jump(top)
    rt.label(end)


def _switch(rt, ctx, s: ast.Switch):
    t = ctx.alloc_temp()
    eval_expr(rt, ctx, s.subject, Variable(t))
    end = ctx.new_label()
    else_body = None
    for case in s.cases:
        if not case.values:
            else_body = case.body
            continue
        body_l = ctx.new_label()
        nxt = ctx.new_label()
        for v in case.values:
            if not isinstance(v, ast.Number):
                raise LowerError(
                    "string switches need the dictionary (B4.4)",
                    getattr(v, "line", s.line),
                )
            rt.op("je", Variable(t), Const(v.value), branch=(body_l, True))
        rt.jump(nxt)
        rt.label(body_l)
        compile_block(rt, ctx, case.body)
        rt.jump(end)
        rt.label(nxt)
    if else_body is not None:
        compile_block(rt, ctx, else_body)
    rt.label(end)
    ctx.free_temp(t)
