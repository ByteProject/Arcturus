# decode.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The instruction decoder and the disassembler built alongside it (M2).

A Z-machine instruction is: an opcode in one of four forms (long, short,
variable, extended), operand type information packed into the opcode byte or
following it, the operands themselves, and then, depending on the opcode, a
store variable byte, a branch (one or two bytes), and inline text (print and
print_ret carry their string in the instruction stream). The decoder reads
one instruction at a given address and returns it fully parsed, with the
address of the next; it never executes anything, so the M3 executor and the
disassembler share it as their single source of instruction truth.

Form selection, from the first byte (Standard 1.1 section 4.3):
- 0xBE: extended form. The next byte is the opcode number in the EXT table,
  and an operand-types byte follows, exactly as in variable form.
- top bits 11: variable form. Bit 5 clear means the 2OP table (with up to 4
  operands), set means the VAR table. Bottom 5 bits are the opcode number.
  Two opcodes, call_vs2 and call_vn2, carry TWO type bytes (up to 8 operands).
- top bits 10: short form. Bits 4-5 are the single operand's type; type 11
  (omitted) makes it a 0OP instruction. Bottom 4 bits are the opcode number.
- anything else: long form, always 2OP. Bit 6 gives the first operand's
  type, bit 5 the second's: clear = small constant, set = variable.

Operand types (section 4.2): 00 large constant (a word), 01 small constant
(a byte), 10 variable (a byte: 0 = stack, 1-15 locals, 16-255 globals),
11 omitted.

Branches (section 4.7): bit 7 of the first byte = branch on true; bit 6 set
= the offset is the bottom 6 bits (0..63); bit 6 clear = a signed 14-bit
offset from the bottom 6 bits and a second byte. Offsets 0 and 1 mean
return false / return true rather than a jump."""

from dataclasses import dataclass, field
from typing import Optional

from .errors import ActaeaError

# Operand type codes, as in the standard.
LARGE, SMALL, VARIABLE, OMITTED = 0, 1, 2, 3


class DecodeError(ActaeaError):
    """An opcode or encoding the decoder cannot make sense of. A well-formed
    story never triggers one, so the address is always included: it is either
    a bug in the story's compiler or a walk into non-code bytes."""


# -- opcode tables -------------------------------------------------------------
#
# name, stores?, branches?, has inline text?
# One table per operand-count family, indexed by the opcode number the form
# selection extracts. Entries are for version 5 and 8 (identical opcode sets);
# names follow the standard's spellings. A None entry is an opcode number
# that is illegal in v5/v8 (e.g. 0OP save/restore died with v4), kept in the
# table so the decoder can name the fault precisely.


@dataclass(frozen=True)
class _Op:
    name: str
    stores: bool = False
    branches: bool = False
    text: bool = False


_2OP = {
    1: _Op("je", branches=True),
    2: _Op("jl", branches=True),
    3: _Op("jg", branches=True),
    4: _Op("dec_chk", branches=True),
    5: _Op("inc_chk", branches=True),
    6: _Op("jin", branches=True),
    7: _Op("test", branches=True),
    8: _Op("or", stores=True),
    9: _Op("and", stores=True),
    10: _Op("test_attr", branches=True),
    11: _Op("set_attr"),
    12: _Op("clear_attr"),
    13: _Op("store"),
    14: _Op("insert_obj"),
    15: _Op("loadw", stores=True),
    16: _Op("loadb", stores=True),
    17: _Op("get_prop", stores=True),
    18: _Op("get_prop_addr", stores=True),
    19: _Op("get_next_prop", stores=True),
    20: _Op("add", stores=True),
    21: _Op("sub", stores=True),
    22: _Op("mul", stores=True),
    23: _Op("div", stores=True),
    24: _Op("mod", stores=True),
    25: _Op("call_2s", stores=True),
    26: _Op("call_2n"),
    27: _Op("set_colour"),
    28: _Op("throw"),
}

_1OP = {
    0: _Op("jz", branches=True),
    1: _Op("get_sibling", stores=True, branches=True),
    2: _Op("get_child", stores=True, branches=True),
    3: _Op("get_parent", stores=True),
    4: _Op("get_prop_len", stores=True),
    5: _Op("inc"),
    6: _Op("dec"),
    7: _Op("print_addr"),
    8: _Op("call_1s", stores=True),
    9: _Op("remove_obj"),
    10: _Op("print_obj"),
    11: _Op("ret"),
    12: _Op("jump"),
    13: _Op("print_paddr"),
    14: _Op("load", stores=True),
    15: _Op("call_1n"),
}

_0OP = {
    0: _Op("rtrue"),
    1: _Op("rfalse"),
    2: _Op("print", text=True),
    3: _Op("print_ret", text=True),
    4: _Op("nop"),
    # 5 save and 6 restore existed through v4; in v5 they are illegal (the
    # EXT forms replaced them). 12 show_status likewise died with v3.
    7: _Op("restart"),
    8: _Op("ret_popped"),
    9: _Op("catch", stores=True),
    10: _Op("quit"),
    11: _Op("new_line"),
    13: _Op("verify", branches=True),
    # 14 is the 0xBE extended-form marker, never a 0OP opcode.
    15: _Op("piracy", branches=True),
}

_VAR = {
    0: _Op("call_vs", stores=True),
    1: _Op("storew"),
    2: _Op("storeb"),
    3: _Op("put_prop"),
    4: _Op("read", stores=True),  # aread: stores the terminator in v5+
    5: _Op("print_char"),
    6: _Op("print_num"),
    7: _Op("random", stores=True),
    8: _Op("push"),
    9: _Op("pull"),
    10: _Op("split_window"),
    11: _Op("set_window"),
    12: _Op("call_vs2", stores=True),
    13: _Op("erase_window"),
    14: _Op("erase_line"),
    15: _Op("set_cursor"),
    16: _Op("get_cursor"),
    17: _Op("set_text_style"),
    18: _Op("buffer_mode"),
    19: _Op("output_stream"),
    20: _Op("input_stream"),
    21: _Op("sound_effect"),
    22: _Op("read_char", stores=True),
    23: _Op("scan_table", stores=True, branches=True),
    24: _Op("not", stores=True),
    25: _Op("call_vn"),
    26: _Op("call_vn2"),
    27: _Op("tokenise"),
    28: _Op("encode_text"),
    29: _Op("copy_table"),
    30: _Op("print_table"),
    31: _Op("check_arg_count", branches=True),
}

# The two VAR opcodes that carry a second operand-types byte (up to 8 args).
_DOUBLE_TYPE = {12, 26}

_EXT = {
    0: _Op("save", stores=True),
    1: _Op("restore", stores=True),
    2: _Op("log_shift", stores=True),
    3: _Op("art_shift", stores=True),
    4: _Op("set_font", stores=True),
    # 5-8 and 16-27 are v6 display opcodes; decoded if met (some tools emit
    # them) but the executor treats them as errors outside v6.
    5: _Op("draw_picture"),
    6: _Op("picture_data", branches=True),
    7: _Op("erase_picture"),
    8: _Op("set_margins"),
    9: _Op("save_undo", stores=True),
    10: _Op("restore_undo", stores=True),
    11: _Op("print_unicode"),
    12: _Op("check_unicode", stores=True),
    13: _Op("set_true_colour"),
    16: _Op("move_window"),
    17: _Op("window_size"),
    18: _Op("window_style"),
    19: _Op("get_wind_prop", stores=True),
    20: _Op("scroll_window"),
    21: _Op("pop_stack"),
    22: _Op("read_mouse"),
    23: _Op("mouse_window"),
    24: _Op("push_stack", branches=True),
    25: _Op("put_wind_prop"),
    26: _Op("print_form"),
    27: _Op("make_menu", branches=True),
    28: _Op("picture_table"),
    29: _Op("buffer_screen", stores=True),  # Standard 1.1 addition
    # Arcturus's own extended opcode (arc_image, B11), at EXT:0x80, in the
    # 128-255 range the Standard reserves for unofficial/private extensions
    # (never collides with a future official opcode; also ignorable per S 14.2).
    # draw_image id mode draws a room picture; a text-only interpreter never
    # reaches it (the compiler guards it behind pictures-available).
    0x80: _Op("draw_image"),
}


@dataclass
class Instruction:
    """One decoded instruction. `operands` pairs each value with its type so
    the executor can tell a variable NUMBER from a constant that happens to
    be small; `store` is the destination variable number or None; `branch` is
    (on_true, offset) with offsets 0/1 meaning return-false/return-true;
    `text` is the raw encoded span of an inline string (decoded by text.py,
    which is M5's module, not the decoder's business)."""

    addr: int
    form: str                     # "long" | "short" | "var" | "ext"
    count: str                    # "0OP" | "1OP" | "2OP" | "VAR" | "EXT"
    opnum: int
    name: str
    stores: bool
    operands: list = field(default_factory=list)   # [(type, value), ...]
    store: Optional[int] = None
    branch: Optional[tuple] = None                 # (on_true, offset)
    text: Optional[bytes] = None
    next: int = 0                 # address of the following instruction


def _table(count: str):
    return {"0OP": _0OP, "1OP": _1OP, "2OP": _2OP, "VAR": _VAR, "EXT": _EXT}[count]


def decode(mem, addr: int) -> Instruction:
    """Decode the instruction at `addr` in `mem` (anything with byte()/word();
    reads may run past 0xFFFF, code lives in long-address space)."""
    start = addr
    first = mem.byte(addr)
    addr += 1
    types: list

    if first == 0xBE:
        form, count = "ext", "EXT"
        opnum = mem.byte(addr)
        addr += 1
        addr, types = _read_type_bytes(mem, addr, 1)
    elif first & 0xC0 == 0xC0:
        form = "var"
        count = "VAR" if first & 0x20 else "2OP"
        opnum = first & 0x1F
        nbytes = 2 if (count == "VAR" and opnum in _DOUBLE_TYPE) else 1
        addr, types = _read_type_bytes(mem, addr, nbytes)
    elif first & 0xC0 == 0x80:
        form = "short"
        t = (first >> 4) & 0x3
        opnum = first & 0x0F
        if t == OMITTED:
            count, types = "0OP", []
        else:
            count, types = "1OP", [t]
    else:
        form, count = "long", "2OP"
        opnum = first & 0x1F
        # In long form the type bits mean: clear = small constant, set =
        # variable. Large constants cannot appear here at all.
        types = [
            VARIABLE if first & 0x40 else SMALL,
            VARIABLE if first & 0x20 else SMALL,
        ]

    op = _table(count).get(opnum)
    if op is None:
        raise DecodeError(
            f"illegal opcode {count}:{opnum} at {start:#07x} (form {form})"
        )

    operands = []
    for t in types:
        if t == LARGE:
            operands.append((t, mem.word(addr)))
            addr += 2
        else:  # SMALL and VARIABLE are one byte each
            operands.append((t, mem.byte(addr)))
            addr += 1

    store = None
    if op.stores:
        store = mem.byte(addr)
        addr += 1

    branch = None
    if op.branches:
        b = mem.byte(addr)
        addr += 1
        on_true = bool(b & 0x80)
        if b & 0x40:
            offset = b & 0x3F  # short form: unsigned 0..63
        else:
            raw = ((b & 0x3F) << 8) | mem.byte(addr)
            addr += 1
            offset = raw - 0x4000 if raw >= 0x2000 else raw  # signed 14-bit
        branch = (on_true, offset)

    text = None
    if op.text:
        # An encoded Z-string: words until one with the top bit set. Kept raw;
        # rendering belongs to text.py (M5).
        tstart = addr
        while True:
            w = mem.word(addr)
            addr += 2
            if w & 0x8000:
                break
        text = bytes(mem.mem[tstart:addr])

    return Instruction(
        addr=start, form=form, count=count, opnum=opnum, name=op.name,
        stores=op.stores, operands=operands, store=store, branch=branch,
        text=text, next=addr,
    )


def _read_type_bytes(mem, addr: int, nbytes: int):
    """Operand types packed two bits each, high bits first, terminated by the
    first 'omitted'; with two type bytes (call_vs2/call_vn2) the second is
    read even if the first ended early, per the standard's layout."""
    types = []
    done = False
    for _ in range(nbytes):
        b = mem.byte(addr)
        addr += 1
        for shift in (6, 4, 2, 0):
            t = (b >> shift) & 0x3
            if t == OMITTED:
                done = True
            elif not done:
                types.append(t)
    return addr, types


# -- the disassembler -----------------------------------------------------------
#
# Recursive descent from the initial PC: decode a routine at a time, follow
# every branch inside it, and queue every routine reached by a call with a
# constant packed address. Computed calls (an address from a variable) cannot
# be followed statically; for compiler output that only hides routines that
# are also reachable through tables (Arcturus' react handlers, for instance),
# so the walker also accepts extra roots from the caller.

_CALLS = {
    "call_vs", "call_vs2", "call_vn", "call_vn2",
    "call_2s", "call_2n", "call_1s", "call_1n",
}

# Instructions after which execution never falls through.
_TERMINAL = {"ret", "rtrue", "rfalse", "ret_popped", "print_ret", "quit",
             "restart", "throw", "jump"}


@dataclass
class Routine:
    addr: int                     # header address (the locals count byte)
    nlocals: int
    instructions: list


def walk_routine(mem, addr: int) -> Routine:
    """Decode one routine: the locals-count header byte, then instructions
    until every branch target seen so far is covered and the flow has ended.
    The stop rule mirrors how compilers lay routines out: linear code where
    the only way past a terminal instruction is an earlier forward branch."""
    nlocals = mem.byte(addr)
    if nlocals > 15:
        raise DecodeError(
            f"routine at {addr:#07x} claims {nlocals} locals (limit 15); "
            "not a routine"
        )
    pc = addr + 1
    instructions = []
    frontier = pc  # the farthest forward-branch target seen
    while True:
        ins = decode(mem, pc)
        instructions.append(ins)
        if ins.branch is not None and ins.branch[1] not in (0, 1):
            target = ins.next + ins.branch[1] - 2
            frontier = max(frontier, target)
        if ins.name == "jump":
            # jump's operand is a signed word offset from the next instruction.
            t, v = ins.operands[0]
            if t != VARIABLE:
                sv = v - 0x10000 if v >= 0x8000 else v
                target = ins.next + sv - 2
                frontier = max(frontier, target)
        pc = ins.next
        if ins.name in _TERMINAL and pc > frontier:
            break
    return Routine(addr, nlocals, instructions)


def walk_story(mem, initial_pc: int, roots=()) -> dict:
    """Disassemble every routine reachable from the entry point (and any
    extra roots, byte addresses): {routine_addr: Routine}. The entry is a
    special case: v5+ stories begin execution at a raw instruction address,
    not inside a routine with a header, so the entry 'routine' is decoded
    from the PC itself with no locals byte."""
    routines: dict = {}
    queue = list(roots)

    # The entry stub: instructions from the initial PC, following calls.
    entry_ins = []
    pc = initial_pc
    while True:
        ins = decode(mem, pc)
        entry_ins.append(ins)
        _queue_calls(ins, mem, queue)
        pc = ins.next
        if ins.name in _TERMINAL or ins.name == "quit":
            break
    routines[initial_pc] = Routine(initial_pc, 0, entry_ins)

    while queue:
        addr = queue.pop()
        if addr in routines or addr == 0:
            continue
        r = walk_routine(mem, addr)
        routines[addr] = r
        for ins in r.instructions:
            _queue_calls(ins, mem, queue)
    return routines


def _queue_calls(ins: Instruction, mem, queue: list) -> None:
    if ins.name in _CALLS and ins.operands:
        t, v = ins.operands[0]
        if t in (LARGE, SMALL) and v:
            queue.append(mem.unpack(v))


# -- formatting ------------------------------------------------------------------

def _var_name(n: int) -> str:
    if n == 0:
        return "sp"
    if n < 16:
        return f"L{n - 1:02d}"
    return f"G{n - 16:02d}"


def format_instruction(ins: Instruction) -> str:
    parts = []
    for t, v in ins.operands:
        if t == VARIABLE:
            parts.append(_var_name(v))
        elif t == LARGE:
            parts.append(f"{v:#06x}")
        else:
            parts.append(str(v))
    s = f"{ins.addr:#07x}  {ins.name}"
    if parts:
        s += " " + ", ".join(parts)
    if ins.store is not None:
        s += f" -> {_var_name(ins.store)}"
    if ins.branch is not None:
        on_true, off = ins.branch
        cond = "" if on_true else "~"
        if off == 0:
            s += f" ?{cond}rfalse"
        elif off == 1:
            s += f" ?{cond}rtrue"
        else:
            s += f" ?{cond}{ins.next + off - 2:#07x}"
    if ins.text is not None:
        s += f" <text: {len(ins.text) // 2} words>"
    return s


def format_routine(r: Routine, entry: bool = False) -> str:
    head = (
        f"entry point {r.addr:#07x}:"
        if entry
        else f"routine {r.addr:#07x} ({r.nlocals} locals):"
    )
    return "\n".join([head] + ["  " + format_instruction(i) for i in r.instructions])


def disassemble(story) -> str:
    """The whole reachable program, entry first, routines in address order."""
    routines = walk_story(story.memory, story.header.initial_pc)
    out = [format_routine(routines[story.header.initial_pc], entry=True)]
    for addr in sorted(routines):
        if addr == story.header.initial_pc:
            continue
        out.append(format_routine(routines[addr]))
    return "\n\n".join(out)
