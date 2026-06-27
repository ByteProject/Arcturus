# assembler.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A Z-machine version 5 instruction assembler.

Routines accumulate instructions; the linker lays them out in high memory,
4-aligns each routine so its packed address (byte address / 4 in v5) is exact,
and backpatches call targets and branch offsets. Instruction encoding follows
the Z-machine standard 1.1, section 4: short form for 0OP and 1OP, long form for
2OP with small-constant or variable operands, variable form otherwise, and the
operand-type field for variable-form instructions.

This is the foundation the rest of code generation builds on; opcodes are added
to the table as later milestones need them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import zstring

# Operand type codes (standard 1.1, section 4.2).
LARGE = 0  # a 16-bit constant
SMALL = 1  # an 8-bit constant
VAR = 2    # a variable reference (0 stack, 1-15 local, 16-255 global)
OMITTED = 3

# Variable references.
STACK = 0


@dataclass
class Operand:
    kind: int
    value: int
    routine: Optional[str] = None  # set when this is an unresolved call target


def Const(v: int) -> Operand:
    """A constant, encoded small (one byte) when it fits in 0..255, else large."""
    v &= 0xFFFF
    return Operand(SMALL if v <= 0xFF else LARGE, v)


def LargeConst(v: int) -> Operand:
    return Operand(LARGE, v & 0xFFFF)


def Variable(n: int) -> Operand:
    return Operand(VAR, n & 0xFF)


def RoutineRef(name: str) -> Operand:
    """A call target: a large-constant placeholder, patched with the routine's
    packed address at link time."""
    return Operand(LARGE, 0, routine=name)


# Opcode table: name -> (form, code, stores, branches, has_text).
_OPCODES = {
    # 0OP
    "rtrue": ("0OP", 0x00, False, False, False),
    "rfalse": ("0OP", 0x01, False, False, False),
    "print": ("0OP", 0x02, False, False, True),
    "print_ret": ("0OP", 0x03, False, False, True),
    "new_line": ("0OP", 0x0B, False, False, False),
    "quit": ("0OP", 0x0A, False, False, False),
    # 1OP
    "jz": ("1OP", 0x00, False, True, False),
    "inc": ("1OP", 0x05, False, False, False),
    "dec": ("1OP", 0x06, False, False, False),
    "ret": ("1OP", 0x0B, False, False, False),
    "print_paddr": ("1OP", 0x0D, False, False, False),
    # 2OP
    "je": ("2OP", 0x01, False, True, False),
    "jl": ("2OP", 0x02, False, True, False),
    "jg": ("2OP", 0x03, False, True, False),
    "store": ("2OP", 0x0D, False, False, False),
    "and": ("2OP", 0x09, True, False, False),
    "or": ("2OP", 0x08, True, False, False),
    "add": ("2OP", 0x14, True, False, False),
    "sub": ("2OP", 0x15, True, False, False),
    "mul": ("2OP", 0x16, True, False, False),
    "div": ("2OP", 0x17, True, False, False),
    "mod": ("2OP", 0x18, True, False, False),
    # VAR
    "call_vs": ("VAR", 0x00, True, False, False),
    "call_vn": ("VAR", 0x19, False, False, False),
    "print_num": ("VAR", 0x06, False, False, False),
    "print_char": ("VAR", 0x05, False, False, False),
}


@dataclass
class _Fixup:
    offset: int  # byte offset within the routine's code
    kind: str  # "call" or "branch"
    target: str  # routine name or label name
    on_true: bool = True  # branch polarity
    wide: bool = True  # branch encoded in two bytes


class Routine:
    """A routine (or the entry stub). `entry` routines are placed at the initial
    program counter with no routine header; ordinary routines get a header and
    are reachable by packed address."""

    def __init__(self, name: str, nlocals: int = 0, entry: bool = False) -> None:
        self.name = name
        self.nlocals = nlocals
        self.entry = entry
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[_Fixup] = []

    # -- instruction emission ----------------------------------------------

    def op(
        self,
        name: str,
        *operands: Operand,
        store: Optional[Operand] = None,
        branch: Optional[tuple] = None,  # (label, on_true)
        text: Optional[str] = None,
    ) -> None:
        form, code, stores, branches, has_text = _OPCODES[name]
        self.code += self._encode(form, code, list(operands))
        if has_text:
            assert text is not None
            self.code += zstring.encode(text)
        if stores:
            assert store is not None
            self.code.append(store.value & 0xFF)
        if branches:
            assert branch is not None
            self._emit_branch(branch[0], branch[1])

    def label(self, name: str) -> None:
        self.labels[name] = len(self.code)

    # -- encoding ----------------------------------------------------------

    def _encode(self, form: str, code: int, operands: list[Operand]) -> bytes:
        if form == "0OP":
            return bytes([0xB0 | code])
        if form == "1OP":
            op = operands[0]
            self._note_routine_ref(op, len(self.code) + 1)  # opcode byte precedes operand
            return bytes([0x80 | (op.kind << 4) | code]) + self._operand_bytes(op)
        if form == "2OP":
            return self._encode_2op(code, operands)
        if form == "VAR":
            return self._encode_var(0xE0 | code, operands)
        raise ValueError(form)

    def _encode_2op(self, code: int, operands: list[Operand]) -> bytes:
        a, b = operands
        # Long form requires both operands to be small constants or variables.
        if a.kind in (SMALL, VAR) and b.kind in (SMALL, VAR):
            bit6 = 0x40 if a.kind == VAR else 0
            bit5 = 0x20 if b.kind == VAR else 0
            return bytes([bit6 | bit5 | code, a.value & 0xFF, b.value & 0xFF])
        # Otherwise encode in variable form (0xC0 | opcode number).
        return self._encode_var(0xC0 | code, operands)

    def _encode_var(self, opbyte: int, operands: list[Operand]) -> bytes:
        out = bytearray([opbyte])
        types = 0
        for i in range(4):
            kind = operands[i].kind if i < len(operands) else OMITTED
            types |= kind << ((3 - i) * 2)
        out.append(types)
        base = len(out)
        for i, op in enumerate(operands):
            # Record a call-target fixup at the position this operand will occupy.
            self._note_routine_ref(op, len(self.code) + base + self._span(operands[:i]))
            out += self._operand_bytes(op)
        return bytes(out)

    @staticmethod
    def _span(operands: list[Operand]) -> int:
        return sum(2 if o.kind == LARGE else 1 for o in operands)

    def _operand_bytes(self, op: Operand) -> bytes:
        if op.kind == LARGE:
            return bytes([(op.value >> 8) & 0xFF, op.value & 0xFF])
        return bytes([op.value & 0xFF])

    def _note_routine_ref(self, op: Operand, offset_in_code: int) -> None:
        if op.routine is not None:
            self.fixups.append(_Fixup(offset_in_code, "call", op.routine))

    def _emit_branch(self, label: str, on_true: bool) -> None:
        # Reserve two bytes; resolved at link time (we always use the wide form
        # for simplicity in B4.1, tightened to one byte where it fits in B5).
        self.fixups.append(_Fixup(len(self.code), "branch", label, on_true, True))
        self.code += b"\x00\x00"


def link(entry: Routine, routines: list[Routine], base_addr: int) -> tuple[bytes, int]:
    """Lay out the entry stub and routines in high memory starting at base_addr.
    Returns the high-memory blob and the initial program counter."""
    blob = bytearray()
    starts: dict[str, int] = {}

    # The entry stub is placed first, with no routine header.
    starts[entry.name] = base_addr
    entry_code_start = 0
    blob += entry.code

    packed: dict[str, int] = {}
    code_starts: dict[str, int] = {entry.name: entry_code_start}
    for r in routines:
        while (base_addr + len(blob)) % 4 != 0:
            blob.append(0)
        addr = base_addr + len(blob)
        starts[r.name] = addr
        packed[r.name] = addr // 4
        blob.append(r.nlocals & 0xFF)  # v5 header: local count, no init words
        code_starts[r.name] = len(blob)
        blob += r.code

    # Backpatch each routine's (and the entry's) fixups.
    for r in [entry] + routines:
        cs = code_starts[r.name]
        for fx in r.fixups:
            pos = cs + fx.offset
            if fx.kind == "call":
                if fx.target not in packed:
                    raise KeyError(f"call to unknown routine '{fx.target}'")
                value = packed[fx.target]
                blob[pos] = (value >> 8) & 0xFF
                blob[pos + 1] = value & 0xFF
            else:  # branch
                target = r.labels[fx.target]
                # New PC = address-after-branch-data + offset - 2, so for a
                # destination at code offset `target`, offset = target - fx.offset.
                offset = target - fx.offset
                word = offset & 0x3FFF
                hi = word >> 8
                if fx.on_true:
                    hi |= 0x80  # branch when the condition is true
                # bit 6 = 0 selects the two-byte (wide) form
                blob[pos] = hi
                blob[pos + 1] = word & 0xFF

    return bytes(blob), base_addr + entry_code_start
