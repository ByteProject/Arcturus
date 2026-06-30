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
from . import storyfile
from . import worldmodel as wm
from .assembler import Const, Routine, Variable, RoutineRef, StringRef, STACK
from .errors import ArcError
from .objects import REACT_PROP
from .prelude import _DIRECTIONS


def exit_directions(layout):
    """The standard directions that are actual properties in this program, in
    canonical order. The verbose_exits granule iterates these to list a room's
    live exits; the order is shared by the exit_prop/exit_name backing routines
    (codegen) and the exits_count intrinsic so indices line up."""
    if layout is None:
        return []
    return [d for d in _DIRECTIONS if d in layout.prop_number]

# Reserved intrinsic functions: calls that lower to opcodes, not a routine call.
# They are the low-level primitives Cosmos's parser and loop sit on (the bridge
# agreed for B4.5). read_line tokenizes a typed line; peek/poke access memory;
# word_* read the parse buffer; call_handler calls a routine by its address;
# handler_of reads an object's react routine address (for the dispatcher).
INTRINSICS = frozenset({
    "read_line", "peek_byte", "peek_word", "poke_byte", "poke_word",
    "word_count", "word_dict", "word_len", "word_pos", "call_handler",
    "handler_of", "parent_of", "words_addr", "words_count",
    # The turn loop fires life-cycle events: run_free runs the free rules for an
    # action, and ev_* name the event action numbers (start, enter, each_turn).
    "run_free", "ev_start", "ev_enter", "ev_each_turn", "action_id", "run_grain",
    # show prints without a trailing newline (say always adds one); print_name
    # prints an object's short name (so messages can name a passed-in object).
    "show", "print_name",
    # tick advances the turn counter, set_here updates the room (both globals are
    # read-only to author code, so the loop changes them through intrinsics).
    "tick", "set_here",
    # par requests a paragraph break before the next printed text (the library
    # controls vertical spacing; the print layer honors the flag).
    "par",
    # read_key reads a single keypress (no echo, no Enter) and returns its ZSCII
    # code, for the conversations menu's press-a-number selection.
    "read_key",
    # do_quit ends the session (the quit opcode); text_char reads a typed
    # character from the input buffer (for a yes/no confirmation). do_restart
    # restarts the story from the beginning (the restart opcode). do_save /
    # do_restore and do_save_undo / do_restore_undo are the v5 EXT save and undo
    # opcodes; each returns the opcode result (0 fail, 1 saved, 2 resumed).
    "do_quit", "text_char", "do_restart",
    "do_save", "do_restore", "do_save_undo", "do_restore_undo",
    # parse_addr / oops_addr give the live parse buffer and its oops backup, so
    # the language layer can snapshot a command and patch it for "oops".
    "parse_addr", "oops_addr",
    # exits_count / exit_prop / exit_name expose this program's direction
    # properties (count, the i-th property number, and printing its name), so the
    # verbose_exits granule can list a room's live exits. exit_prop/exit_name are
    # backed by routines codegen emits only when these intrinsics are used.
    "exits_count", "exit_prop", "exit_name",
    # Screen model (v5), for the statusline granule: the upper window, cursor,
    # text style, and the screen width from the header. Each lowers to an opcode,
    # so they cost nothing unless a granule calls them.
    "split_window", "set_window", "set_cursor", "set_style", "screen_width",
    "erase_window", "screen_height",
    # desc_addr / intro_addr give the address of an object's desc / intro
    # property (0 if absent), so the room describer can test for one.
    "desc_addr", "intro_addr",
    # Conversation topics, for the ask/tell and menu granules: how many a person
    # has, whether topic i is in view, printing its menu label, matching a subject
    # word against it, running its body, and retiring it (so the menu drops a
    # topic once it has been picked). Each calls a cosmos_topic_* backing routine
    # codegen emits only when one of these is used.
    "topics_count", "topic_visible", "topic_label", "topic_matches", "topic_run",
    "topic_retire",
})

_ARITH = {"+": "add", "-": "sub", "*": "mul", "/": "div", "mod": "mod"}
_MAX_LOCALS = 15

# Builtin references that hold an object number at run time (docs/02 section 2).
_OBJECT_BUILTINS = {"player", "here", "noun", "second", "self"}


class LowerError(ArcError):
    pass


class Context:
    """Per-routine state: the local-variable assignment and a temporary pool
    above the named locals."""

    def __init__(
        self,
        world: wm.World,
        globals_map: dict,
        params=(),
        layout=None,
        self_value=None,
        in_handler: bool = False,
        string_pool=None,
    ):
        self.world = world
        self.globals = globals_map
        self.layout = layout
        # Pool for strings allocated during lowering (e.g. a text-property
        # write); build_story lays them out and patches their packed addresses.
        self.string_pool = string_pool
        # What `self` resolves to in this routine: a constant object number for
        # an object/room handler, or the noun variable for a kind/free handler.
        self.self_value = self_value
        # In a handler, `stop` and `continue` return a dispatch code (1 = the
        # action is consumed, 0 = pass to the next handler). In a block they are
        # an ordinary return / an error.
        self.in_handler = in_handler
        # Locals currently known to hold an object (a `for each` over the tree),
        # so `say` prints the object's name rather than its number.
        self.object_locals: set = set()
        # When compiling a topic body: subject id -> table index, so `reveal`/
        # `hide` can address a sibling topic by index (empty elsewhere).
        self.topic_index: dict = {}
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

    def kind_attr(self, name: str):
        return None if self.layout is None else self.layout.kind_attr.get(name)

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
        if expr.ident == "self":
            return ctx.self_value is not None
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
        if expr.ident == "self" and ctx.self_value is not None:
            return ctx.self_value
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
        # obj.(expr): read the property whose number is computed at run time
        # (the turn loop uses here.(way) to follow the chosen direction).
        objop, to = _operand(rt, ctx, expr.obj)
        propop, tp = _operand(rt, ctx, expr.index)
        rt.op("get_prop", objop, propop, store=dest)
        if to is not None:
            ctx.free_temp(to)
        if tp is not None:
            ctx.free_temp(tp)
        return

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
    if expr.name in INTRINSICS:
        _intrinsic(rt, ctx, expr, dest)
        return
    if expr.name not in ctx.world.blocks:
        raise LowerError(f"call to unknown block '{expr.name}'", expr.line)
    # Push arguments right-first so they pop in order behind the routine address.
    for arg in reversed(expr.args):
        eval_expr(rt, ctx, arg, Variable(STACK))
    operands = [RoutineRef("blk_" + expr.name)]
    operands += [Variable(STACK)] * len(expr.args)
    rt.op("call_vs", *operands, store=dest)


def _intrinsic(rt, ctx, call: ast.Call, dest):
    name, args = call.name, call.args
    parse = Const(storyfile.PARSE_BUFFER_ADDR)

    if name == "read_line":
        # Clear the count of pre-existing input (text buffer byte 1) before each
        # read; v5 aread leaves it set to the prior line's length, and a stale
        # count makes interpreters try to redisplay old input ("inconsistent
        # input buffer").
        rt.op("storeb", Const(storyfile.TEXT_BUFFER_ADDR), Const(1), Const(0))
        rt.op("aread", Const(storyfile.TEXT_BUFFER_ADDR), parse, store=dest)
    elif name == "word_count":
        rt.op("loadb", parse, Const(1), store=dest)  # parse[1] = the word count
    elif name == "peek_byte":
        op, t = _operand(rt, ctx, args[0])
        rt.op("loadb", op, Const(0), store=dest)
        _free(ctx, t)
    elif name == "peek_word":
        opa, opb, t = _two_operands(rt, ctx, args[0], args[1])
        rt.op("loadw", opa, opb, store=dest)
        _free(ctx, t)
    elif name == "poke_byte":
        # storeb(addr, 0, v): push v then addr so addr is read first.
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("storeb", Variable(STACK), Const(0), Variable(STACK))
        _place(rt, Const(0), dest)  # poke returns nothing useful
    elif name == "poke_word":
        eval_expr(rt, ctx, args[2], Variable(STACK))
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("storew", Variable(STACK), Variable(STACK), Variable(STACK))
        _place(rt, Const(0), dest)
    elif name == "word_dict":
        # parse buffer word i: dict-address word at word index 1 + 2*i.
        _word_index(rt, ctx, args[0], scale=2, base=1)
        rt.op("loadw", parse, Variable(STACK), store=dest)
    elif name == "word_len":
        _word_index(rt, ctx, args[0], scale=4, base=4)  # byte 2 + 4*i + 2
        rt.op("loadb", parse, Variable(STACK), store=dest)
    elif name == "word_pos":
        _word_index(rt, ctx, args[0], scale=4, base=5)  # byte 2 + 4*i + 3
        rt.op("loadb", parse, Variable(STACK), store=dest)
    elif name == "call_handler":
        # call_handler(addr, action): call the routine at addr with one argument.
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vs", Variable(STACK), Variable(STACK), store=dest)
    elif name == "handler_of":
        # handler_of(obj): the object's react routine address, or 0 (the property
        # default) if it has none.
        op, t = _operand(rt, ctx, args[0])
        rt.op("get_prop", op, Const(REACT_PROP), store=dest)
        _free(ctx, t)
    elif name == "parent_of":
        # parent_of(obj): the object's parent in the tree (0 if detached).
        op, t = _operand(rt, ctx, args[0])
        rt.op("get_parent", op, store=dest)
        _free(ctx, t)
    elif name == "run_free":
        # run_free(action): run the free rules for an action (react_free).
        op, t = _operand(rt, ctx, args[0])
        rt.op("call_vs", RoutineRef("react_free"), op, store=dest)
        _free(ctx, t)
    elif name == "run_grain":
        # run_grain(id, action): route a matched scenery grain to its routine.
        eval_expr(rt, ctx, args[1], Variable(STACK))  # action (local 2)
        eval_expr(rt, ctx, args[0], Variable(STACK))  # id (local 1)
        rt.op("call_vs", RoutineRef("grain_dispatch"),
              Variable(STACK), Variable(STACK), store=dest)
    elif name in ("ev_start", "ev_enter", "ev_each_turn"):
        # The event's action number, so the loop can fire it through react.
        evname = name[3:]
        _place(rt, Const(wm.action_numbers(ctx.world)[evname]), dest)
    elif name == "action_id":
        # action_id("take_off"): the action number for a named action, so the
        # parser can remap a particle verb (switch + off -> switch_off).
        text = "".join(p.text for p in args[0].parts if isinstance(p, ast.StringText))
        num = wm.action_numbers(ctx.world).get(text)
        if num is None:
            raise LowerError(f"action_id: unknown action '{text}'")
        _place(rt, Const(num), dest)
    elif name == "show":
        # show(text): print without a trailing newline (for prompts and for
        # building a sentence around a named object).
        _say(rt, ctx, args[0], newline=False)
        _place(rt, Const(0), dest)
    elif name == "print_name":
        # print_name(obj): the object's short name, no newline.
        op, t = _operand(rt, ctx, args[0])
        rt.op("print_obj", op)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "tick":
        # tick(): advance the turn counter (the loop owns turns).
        slot = Variable(ctx.globals["turns"])
        rt.op("add", slot, Const(1), store=slot)
        _place(rt, Const(0), dest)
    elif name == "set_here":
        # set_here(room): the loop owns the here global (read-only to authors).
        op, t = _operand(rt, ctx, args[0])
        rt.op("store", Const(ctx.globals["here"]), op)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "par":
        # par(): mark a pending paragraph break; the print layer flushes it as a
        # single blank line before the next text, collapsing repeats.
        slot = ctx.globals.get("par_pending")
        if slot is not None:
            rt.op("store", Const(slot), Const(1))
        _place(rt, Const(0), dest)
    elif name == "read_key":
        # read_key(): read one keypress, returning its ZSCII code. The first
        # read_char operand is the input device, always 1 in v5.
        rt.op("read_char", Const(1), store=dest)
    elif name == "do_quit":
        # do_quit(): end the session.
        rt.op("quit")
        _place(rt, Const(0), dest)
    elif name == "do_restart":
        # do_restart(): restart the story from the beginning (never returns).
        rt.op("restart")
        _place(rt, Const(0), dest)
    elif name == "do_save":
        # do_save(): save the game. Stores 0 (failed), 1 (saved, original pass),
        # or 2 (execution resumed here after a matching restore).
        rt.op("save", store=dest)
    elif name == "do_restore":
        # do_restore(): restore a save. On success execution jumps back to the
        # do_save point (so this only returns 0 on failure).
        rt.op("restore", store=dest)
    elif name == "do_save_undo":
        # do_save_undo(): checkpoint for undo. Stores -1 (no undo), 0 (failed),
        # 1 (saved), or 2 (resumed here via restore_undo).
        rt.op("save_undo", store=dest)
    elif name == "do_restore_undo":
        # do_restore_undo(): undo to the last checkpoint. On success jumps back to
        # the do_save_undo point (so this only returns 0 on failure).
        rt.op("restore_undo", store=dest)
    elif name == "parse_addr":
        # parse_addr(): the address of the live parse buffer.
        _place(rt, Const(storyfile.PARSE_BUFFER_ADDR), dest)
    elif name == "oops_addr":
        # oops_addr(): the address of the parse-buffer backup kept for oops.
        _place(rt, Const(storyfile.OOPS_PARSE_ADDR), dest)
    elif name == "exits_count":
        # exits_count(): how many directions are properties in this program.
        _place(rt, Const(len(exit_directions(ctx.layout))), dest)
    elif name == "exit_prop":
        # exit_prop(i): the property number of the i-th direction (0 out of range).
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vs", RoutineRef("cosmos_exit_prop"), Variable(STACK), store=dest)
    elif name == "exit_name":
        # exit_name(i): print the i-th direction's name (no newline).
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vn", RoutineRef("cosmos_exit_name"), Variable(STACK))
        _place(rt, Const(0), dest)
    elif name == "split_window":
        # split_window(n): reserve n lines for the upper window.
        op, t = _operand(rt, ctx, args[0])
        rt.op("split_window", op)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "set_window":
        # set_window(n): select window 0 (main) or 1 (upper).
        op, t = _operand(rt, ctx, args[0])
        rt.op("set_window", op)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "set_cursor":
        # set_cursor(line, column): move the upper-window cursor (1-based).
        opa, opb, t = _two_operands(rt, ctx, args[0], args[1])
        rt.op("set_cursor", opa, opb)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "set_style":
        # set_style(s): text style bits (0 normal, 1 reverse, 2 bold, 4 italic).
        op, t = _operand(rt, ctx, args[0])
        rt.op("set_text_style", op)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "erase_window":
        # erase_window(n): clear window n (1 = upper) so the menu repaints clean;
        # -1 unsplits and clears the whole screen.
        op, t = _operand(rt, ctx, args[0])
        rt.op("erase_window", op)
        _free(ctx, t)
        _place(rt, Const(0), dest)
    elif name == "screen_width":
        # screen_width(): the screen width in characters (header byte 0x21).
        rt.op("loadb", Const(0), Const(0x21), store=dest)
    elif name == "screen_height":
        # screen_height(): the screen height in lines (header byte 0x20), so the
        # menu can cap the upper window to what fits.
        rt.op("loadb", Const(0), Const(0x20), store=dest)
    elif name == "text_char":
        # text_char(i): the i-th character typed on the last input line. In v5 the
        # text buffer holds the characters from byte 2 onward (byte 1 is the count).
        op, t = _operand(rt, ctx, args[0])
        rt.op("add", Const(storyfile.TEXT_BUFFER_ADDR + 2), op, store=Variable(STACK))
        rt.op("loadb", Variable(STACK), Const(0), store=dest)
        _free(ctx, t)
    elif name == "words_addr":
        # words_addr(obj): the address of the object's words array (0 if none).
        op, t = _operand(rt, ctx, args[0])
        rt.op("get_prop_addr", op, Const(_words_prop(ctx)), store=dest)
        _free(ctx, t)
    elif name in ("desc_addr", "intro_addr"):
        # desc_addr(obj)/intro_addr(obj): the address of the object's desc or
        # intro property (0 if it has none), so the room describer can tell
        # whether one is present before printing it.
        prop = name[:-5]  # "desc" or "intro"
        op, t = _operand(rt, ctx, args[0])
        pnum = ctx.prop_number(prop)
        if pnum is None:
            raise LowerError(f"{name} needs a {prop} property")
        rt.op("get_prop_addr", op, Const(pnum), store=dest)
        _free(ctx, t)
    elif name == "words_count":
        # words_count(obj): how many words the object has (the array length / 2).
        op, t = _operand(rt, ctx, args[0])
        rt.op("get_prop_addr", op, Const(_words_prop(ctx)), store=Variable(STACK))
        rt.op("get_prop_len", Variable(STACK), store=Variable(STACK))
        rt.op("div", Variable(STACK), Const(2), store=dest)
        _free(ctx, t)
    elif name == "topics_count":
        # topics_count(person): how many topics the person has (0 if none).
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vs", RoutineRef("cosmos_topics_count"), Variable(STACK), store=dest)
    elif name == "topic_visible":
        # topic_visible(person, i): 1 if topic i is in view (not hidden/retired,
        # `when` satisfied).
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vs", RoutineRef("cosmos_topic_visible"),
              Variable(STACK), Variable(STACK), store=dest)
    elif name == "topic_label":
        # topic_label(person, i): print topic i's menu label (no newline).
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vn", RoutineRef("cosmos_topic_label"),
              Variable(STACK), Variable(STACK))
        _place(rt, Const(0), dest)
    elif name == "topic_matches":
        # topic_matches(person, i, word): 1 if topic i lists the dictionary word.
        eval_expr(rt, ctx, args[2], Variable(STACK))
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vs", RoutineRef("cosmos_topic_matches"),
              Variable(STACK), Variable(STACK), Variable(STACK), store=dest)
    elif name == "topic_run":
        # topic_run(person, i): run topic i's exchange (retires it if `once`).
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vn", RoutineRef("cosmos_topic_run"),
              Variable(STACK), Variable(STACK))
        _place(rt, Const(0), dest)
    elif name == "topic_retire":
        # topic_retire(person, i): retire topic i now, so the menu drops it once
        # it has been picked (the ask/tell path does not call this, so typed
        # topics stay re-askable unless `once`).
        eval_expr(rt, ctx, args[1], Variable(STACK))
        eval_expr(rt, ctx, args[0], Variable(STACK))
        rt.op("call_vn", RoutineRef("cosmos_topic_retire"),
              Variable(STACK), Variable(STACK))
        _place(rt, Const(0), dest)


def _words_prop(ctx) -> int:
    if ctx.layout is None or "words" not in ctx.layout.prop_number:
        raise LowerError("words_addr/words_count need the object table with a words property")
    return ctx.layout.prop_number["words"]


def _word_index(rt, ctx, expr, scale, base):
    """Leave base + scale*expr on the stack (the parse-buffer index for word i)."""
    op, t = _operand(rt, ctx, expr)
    rt.op("mul", op, Const(scale), store=Variable(STACK))
    rt.op("add", Variable(STACK), Const(base), store=Variable(STACK))
    _free(ctx, t)


def _free(ctx, temp):
    if temp is not None:
        ctx.free_temp(temp)


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
        if res == wm.IS_KIND:
            _kind_test(rt, ctx, expr, label, on_true)
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


def _kind_test(rt, ctx, expr: ast.IsTest, label, on_true):
    # `obj is <kind>`: test the kind's attribute (set on every instance of the
    # kind, B4.5c).
    att = ctx.kind_attr(expr.right.ident)
    t = not on_true if expr.negated else on_true
    objop, tmp = _operand(rt, ctx, expr.left)
    rt.op("test_attr", objop, Const(att), branch=(label, t))
    if tmp is not None:
        ctx.free_temp(tmp)


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
    elif isinstance(s, ast.Line):
        _line(rt, ctx, s)
    elif isinstance(s, ast.TopicToggle):
        _topic_toggle(rt, ctx, s)
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
        # In a handler, stop consumes the action (return 1); elsewhere it is a
        # plain return.
        rt.op("ret", Const(1)) if ctx.in_handler else rt.op("rfalse")
    elif isinstance(s, ast.If):
        _if(rt, ctx, s)
    elif isinstance(s, ast.While):
        _while(rt, ctx, s)
    elif isinstance(s, ast.Switch):
        _switch(rt, ctx, s)
    elif isinstance(s, ast.ExprStmt):
        # A discarded expression: store its value into a scratch local and free
        # it. (We cannot "pull" into the stack to drop a value: `pull` with a
        # variable operand is an indirect store and would pop twice.)
        t = ctx.alloc_temp()
        if isinstance(s.expr, ast.Call):
            _call(rt, ctx, s.expr, Variable(t))
        else:
            eval_expr(rt, ctx, s.expr, Variable(t))
        ctx.free_temp(t)
    elif isinstance(s, ast.Now):
        _now(rt, ctx, s)
    elif isinstance(s, ast.Move):
        _move(rt, ctx, s)
    elif isinstance(s, (ast.Add, ast.Remove)):
        raise LowerError("list properties need the dictionary stage (B4.4)", s.line)
    elif isinstance(s, ast.Continue):
        if not ctx.in_handler:
            raise LowerError("'continue' is only valid in a handler", s.line)
        rt.op("ret", Const(0))  # pass the action to the next handler
    elif isinstance(s, ast.ForEach):
        _for_each(rt, ctx, s)
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
            # A text-property write stores the packed address of a new string.
            if any(isinstance(p, ast.StringInterp) for p in s.value.parts):
                raise LowerError(
                    "interpolated text in a property write is not supported", s.line
                )
            if ctx.string_pool is None:
                raise LowerError("no string pool available", s.line)
            text = "".join(
                p.text for p in s.value.parts if isinstance(p, ast.StringText)
            )
            sid = ctx.string_pool.add(text)
            objop, to = _operand(rt, ctx, s.target.obj)
            rt.op("put_prop", objop, Const(pnum), StringRef(sid))
            if to is not None:
                ctx.free_temp(to)
            return
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


def _flush_par(rt, ctx):
    """Emit a pending paragraph break: if par_pending is set, print one blank
    line and clear it. Runs before any text output so the library can request a
    break without the author managing newlines."""
    slot = ctx.globals.get("par_pending")
    if slot is None:
        return
    skip = ctx.new_label()
    rt.op("jz", Variable(slot), branch=(skip, True))
    rt.op("new_line")
    rt.op("store", Const(slot), Const(0))
    rt.label(skip)


def _say(rt, ctx, value, newline=True):
    _flush_par(rt, ctx)
    _emit_say(rt, ctx, value)
    if newline:
        rt.op("new_line")


def _emit_say(rt, ctx, value):
    """Print a say value (a string with interpolation, or a bare expression)
    with no paragraph flush and no trailing newline. _say wraps it with both;
    _line wraps it with a speaker prefix and quotation marks."""
    if isinstance(value, ast.StringLit):
        for part in value.parts:
            if isinstance(part, ast.StringText):
                if part.text:
                    rt.op("print", text=part.text)
            else:  # StringInterp
                if part.article is not None:
                    _say_with_article(rt, ctx, part.article, part.expr)
                else:
                    _say_value(rt, ctx, part.expr)
    else:
        _say_value(rt, ctx, value)


def _line(rt, ctx, s: ast.Line):
    """A conversation line: `you "..."` is the player, `reply "..."` is the
    person being spoken to (`self`). The compiler owns only the structure - open
    framing, the line's text (interpolation and all), close framing - while the
    wording lives in Cosmos: line_you / line_reply / line_end print the speaker
    label, separator, and quotation marks. That keeps the framing overridable and
    translatable and, crucially, reachable for the ask/tell path, which runs
    without the conversations granule."""
    _flush_par(rt, ctx)
    if s.who == "reply":
        speaker = ctx.self_value if ctx.self_value is not None else Const(0)
        rt.op("call_vn", RoutineRef("blk_line_reply"), speaker)
    else:  # "you": the player's own line
        rt.op("call_vn", RoutineRef("blk_line_you"))
    _emit_say(rt, ctx, s.text)
    rt.op("call_vn", RoutineRef("blk_line_end"))


def _topic_toggle(rt, ctx, s: ast.TopicToggle):
    """`reveal <id>` / `hide <id>`: set or clear the HIDDEN bit in a sibling
    topic's live-state byte. The subject resolves to a table index at compile
    time (topics only ever reveal/hide siblings on the same person, `self`), so
    this is a direct poke with no runtime lookup."""
    from .objects import TOPIC_REC, TOPIC_HIDDEN

    if s.target not in ctx.topic_index:
        raise LowerError(f"reveal/hide names an unknown topic '{s.target}'", s.line)
    if ctx.self_value is None:
        raise LowerError("reveal/hide is only valid inside a topic body", s.line)
    tp = ctx.prop_number("topics")
    if tp is None:
        raise LowerError("reveal/hide needs the topics property", s.line)
    idx = ctx.topic_index[s.target]
    state_off = 2 + idx * TOPIC_REC + 9  # table header + record + state byte
    # rec-state address = topics-table address + state_off.
    rt.op("get_prop", ctx.self_value, Const(tp), store=Variable(STACK))
    addr = ctx.alloc_temp()
    rt.op("add", Variable(STACK), Const(state_off), store=Variable(addr))
    rt.op("loadb", Variable(addr), Const(0), store=Variable(STACK))
    if s.reveal:
        rt.op("and", Variable(STACK), Const(0xFF ^ TOPIC_HIDDEN), store=Variable(STACK))
    else:
        rt.op("or", Variable(STACK), Const(TOPIC_HIDDEN), store=Variable(STACK))
    rt.op("storeb", Variable(addr), Const(0), Variable(STACK))
    ctx.free_temp(addr)


def _is_object_expr(ctx, expr) -> bool:
    if isinstance(expr, ast.Name):
        return (
            ctx.is_object_name(expr.ident)
            or expr.ident in _OBJECT_BUILTINS
            or expr.ident in ctx.object_locals
        )
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


def _say_with_article(rt, ctx, article, expr):
    """Print the article then the object's name. Two refinements over a literal
    article: a `named` object (Linda, Excalibur) takes no article at all; and the
    indefinite article auto-picks "a" vs "an" from the object's `an` attribute
    (which the compiler derived from the name). So ${The noun} reads "The sword"
    or "Linda", and ${a noun} reads "a coin" or "an apple"."""
    op, t = _operand(rt, ctx, expr)
    named_attr = ctx.attr_number("named")
    has_named = ctx.layout is not None and ctx.layout.has_named
    skip = None
    if named_attr is not None and has_named:
        skip = ctx.new_label()
        rt.op("test_attr", op, Const(named_attr), branch=(skip, True))  # named: none
    if article.lower() in ("a", "an"):
        _print_indefinite(rt, ctx, op, article[0].isupper())
    else:
        rt.op("print", text=article + " ")
    if skip is not None:
        rt.label(skip)
    rt.op("print_obj", op)
    if t is not None:
        ctx.free_temp(t)


def _print_indefinite(rt, ctx, op, cap):
    """Print "a "/"an " (capitalized when `cap`), choosing by the object's `an`
    attribute. The author wrote ${a obj} or ${an obj}; the actual choice is the
    object's, so the article is always right regardless of which was typed."""
    a_word = "A " if cap else "a "
    an_word = "An " if cap else "an "
    an_attr = ctx.attr_number("an")
    if an_attr is None:
        rt.op("print", text=a_word)
        return
    use_an = ctx.new_label()
    done = ctx.new_label()
    rt.op("test_attr", op, Const(an_attr), branch=(use_an, True))
    rt.op("print", text=a_word)
    rt.jump(done)
    rt.label(use_an)
    rt.op("print", text=an_word)
    rt.label(done)


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


def _is_list_source(ctx, source) -> bool:
    if isinstance(source, ast.Dot):
        p = ctx.world.properties.get(source.prop)
        return p is not None and p.type == "list"
    return False


def _for_each(rt, ctx, s: ast.ForEach):
    """`for each x in <object>` walks the object's tree children with
    get_child / get_sibling. (List iteration and `for each ... of <kind>` over
    instances are not lowered yet.)"""
    if s.relation == "of":
        raise LowerError(
            "'for each ... of <kind>' over instances is not supported yet", s.line
        )
    if _is_list_source(ctx, s.source):
        raise LowerError("list iteration is not supported yet", s.line)
    xslot = ctx.resolve_var(s.var, s.line)
    objop, t = _operand(rt, ctx, s.source)
    body = ctx.new_label()
    done = ctx.new_label()
    # x = first child; if none, skip the loop.
    rt.op("get_child", objop, store=Variable(xslot), branch=(body, True))
    rt.jump(done)
    rt.label(body)
    had = s.var in ctx.object_locals
    ctx.object_locals.add(s.var)  # the loop var holds an object
    compile_block(rt, ctx, s.body)
    if not had:
        ctx.object_locals.discard(s.var)
    # x = next sibling; loop while one exists.
    rt.op("get_sibling", Variable(xslot), store=Variable(xslot), branch=(body, True))
    rt.label(done)
    _free(ctx, t)


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
