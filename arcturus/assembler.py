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
    string: Optional[str] = None  # set when this is an unresolved packed-string ref


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


def StringRef(sid: str) -> Operand:
    """A reference to a packed string (by id): a large-constant placeholder,
    patched with the string's packed address at link time."""
    return Operand(LARGE, 0, string=sid)


# Opcode table: name -> (form, code, stores, branches, has_text).
_OPCODES = {
    # 0OP
    "rtrue": ("0OP", 0x00, False, False, False),
    "rfalse": ("0OP", 0x01, False, False, False),
    "print": ("0OP", 0x02, False, False, True),
    "print_ret": ("0OP", 0x03, False, False, True),
    "new_line": ("0OP", 0x0B, False, False, False),
    "quit": ("0OP", 0x0A, False, False, False),
    "restart": ("0OP", 0x07, False, False, False),
    # 1OP
    "jz": ("1OP", 0x00, False, True, False),
    "get_sibling": ("1OP", 0x01, True, True, False),  # stores the sibling, branches if it exists
    "get_child": ("1OP", 0x02, True, True, False),  # stores the child, branches if it exists
    "get_parent": ("1OP", 0x03, True, False, False),
    "inc": ("1OP", 0x05, False, False, False),
    "dec": ("1OP", 0x06, False, False, False),
    "get_prop_len": ("1OP", 0x04, True, False, False),  # length of a property from its data address
    "remove_obj": ("1OP", 0x09, False, False, False),
    "print_obj": ("1OP", 0x0A, False, False, False),
    "ret": ("1OP", 0x0B, False, False, False),
    "print_paddr": ("1OP", 0x0D, False, False, False),
    # 2OP
    "je": ("2OP", 0x01, False, True, False),
    "jl": ("2OP", 0x02, False, True, False),
    "jg": ("2OP", 0x03, False, True, False),
    "jin": ("2OP", 0x06, False, True, False),
    "test_attr": ("2OP", 0x0A, False, True, False),
    "set_attr": ("2OP", 0x0B, False, False, False),
    "clear_attr": ("2OP", 0x0C, False, False, False),
    "store": ("2OP", 0x0D, False, False, False),
    "insert_obj": ("2OP", 0x0E, False, False, False),
    "loadw": ("2OP", 0x0F, True, False, False),
    "loadb": ("2OP", 0x10, True, False, False),
    "get_prop": ("2OP", 0x11, True, False, False),
    "get_prop_addr": ("2OP", 0x12, True, False, False),  # data address of a property (0 if absent)
    "and": ("2OP", 0x09, True, False, False),
    # set_colour fg bg (v5): 0 = no change, 1 = the interpreter default, 2-9 the
    # standard colours. The zcolor statement and say.<colour> lower to this.
    "set_colour": ("2OP", 0x1B, False, False, False),
    "or": ("2OP", 0x08, True, False, False),
    "add": ("2OP", 0x14, True, False, False),
    "sub": ("2OP", 0x15, True, False, False),
    "mul": ("2OP", 0x16, True, False, False),
    "div": ("2OP", 0x17, True, False, False),
    "mod": ("2OP", 0x18, True, False, False),
    # VAR
    "call_vs": ("VAR", 0x00, True, False, False),
    "storew": ("VAR", 0x01, False, False, False),
    "storeb": ("VAR", 0x02, False, False, False),
    "aread": ("VAR", 0x04, True, False, False),  # read+tokenize; v5 stores the terminator
    # read_char reads a single keypress (no echo, no Enter), storing its ZSCII
    # code. The first operand is the input device, always 1 in v5. Used by the
    # conversations granule for press-a-number menu selection.
    "read_char": ("VAR", 0x16, True, False, False),
    "call_vn": ("VAR", 0x19, False, False, False),
    "print_num": ("VAR", 0x06, False, False, False),
    "print_char": ("VAR", 0x05, False, False, False),
    "push": ("VAR", 0x08, False, False, False),
    "pull": ("VAR", 0x09, False, False, False),
    "put_prop": ("VAR", 0x03, False, False, False),
    # Screen-model VAR opcodes (v5): the upper window and cursor, used by the
    # statusline granule. split_window reserves N upper lines; set_window selects
    # window 0 (main) or 1 (upper); set_cursor moves within the upper window;
    # set_text_style sets reverse/bold/etc; erase_window clears one (or all).
    "split_window": ("VAR", 0x0A, False, False, False),
    "set_window": ("VAR", 0x0B, False, False, False),
    "erase_window": ("VAR", 0x0D, False, False, False),
    # buffer_mode 0/1: suspend or resume the lower window's word-wrap buffering.
    # Upper-window drawing (the status line, the quote box) must run unbuffered,
    # or interpreters like Frotz reorder the writes around set_cursor.
    "buffer_mode": ("VAR", 0x12, False, False, False),
    # tokenise text parse: re-tokenize the text buffer into the parse buffer,
    # after library code has patched the text (the Spanish infinitive retry).
    "tokenise": ("VAR", 0x1B, False, False, False),
    # random n: 1..n uniformly (n > 0); the interpreter owns the generator.
    "random": ("VAR", 0x07, True, False, False),
    "set_cursor": ("VAR", 0x0F, False, False, False),
    "set_text_style": ("VAR", 0x11, False, False, False),
    # EXT (v5+). save/restore store a result (0 fail, 1 the original pass, 2 the
    # post-restore resume); save_undo/restore_undo behave the same for undo.
    "save": ("EXT", 0x00, True, False, False),
    "restore": ("EXT", 0x01, True, False, False),
    "save_undo": ("EXT", 0x09, True, False, False),
    "restore_undo": ("EXT", 0x0A, True, False, False),
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
        # Canonical returns (B6.3 peephole): `ret 0` and `ret 1` are the two-byte
        # 1OP form; rfalse and rtrue are the one-byte 0OP equivalents. Emit the
        # short form so every "return 0/1" site costs one byte instead of two.
        if name == "ret" and len(operands) == 1:
            o = operands[0]
            if o.kind == SMALL and o.routine is None and o.string is None:
                if o.value == 0:
                    name, operands = "rfalse", ()
                elif o.value == 1:
                    name, operands = "rtrue", ()
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

    def jump(self, label: str) -> None:
        """Unconditional jump (1OP:jump) to a label. Its operand is a signed
        offset, resolved at link time."""
        self.code.append(0x8C)  # 1OP, large-constant operand, opcode 0x0C
        self.fixups.append(_Fixup(len(self.code), "jump", label))
        self.code += b"\x00\x00"

    # -- encoding ----------------------------------------------------------

    def _encode(self, form: str, code: int, operands: list[Operand]) -> bytes:
        # The top two bits of the first byte choose the instruction form
        # (standard 1.1, section 4.3). Short form (10xxxxxx) covers 0OP and 1OP;
        # the next two bits give the single operand's type (11 = none, i.e. 0OP).
        if form == "0OP":
            # 1011xxxx: operand type 11 (none), opcode in the low four bits.
            return bytes([0xB0 | code])
        if form == "1OP":
            # 10ttxxxx: tt is the operand type, opcode in the low four bits.
            op = operands[0]
            self._note_ref(op, len(self.code) + 1)  # operand follows the opcode byte
            return bytes([0x80 | (op.kind << 4) | code]) + self._operand_bytes(op)
        if form == "2OP":
            return self._encode_2op(code, operands)
        if form == "VAR":
            # Variable form, true VAR opcode: 111xxxxx = 0xE0 | opcode number.
            return self._encode_var(0xE0 | code, operands)
        if form == "EXT":
            # Extended form (v5+): the byte 0xBE, then the EXT opcode number, then
            # a VAR-style types byte and operands. Used for save/restore and the
            # undo opcodes (and later the v5 graphics/window extras).
            return self._encode_var_form(bytes([0xBE, code]), operands)
        raise ValueError(form)

    def _encode_2op(self, code: int, operands: list[Operand]) -> bytes:
        a, b = operands
        # Long form (0xxxxxxx) is the compact two-operand encoding but can only
        # carry small constants and variables: bit 6 is operand 1's type and bit
        # 5 operand 2's type (0 = small constant, 1 = variable), opcode in the
        # low five bits. One operand byte each (standard 1.1, section 4.4.1).
        if a.kind in (SMALL, VAR) and b.kind in (SMALL, VAR):
            bit6 = 0x40 if a.kind == VAR else 0
            bit5 = 0x20 if b.kind == VAR else 0
            return bytes([bit6 | bit5 | code, a.value & 0xFF, b.value & 0xFF])
        # A large constant cannot fit long form, so fall back to the variable
        # form of the same 2OP opcode: 110xxxxx = 0xC0 | opcode number.
        return self._encode_var(0xC0 | code, operands)

    def _encode_var(self, opbyte: int, operands: list[Operand]) -> bytes:
        # Variable form: the opcode byte, then a types byte and operands.
        return self._encode_var_form(bytes([opbyte]), operands)

    def _encode_var_form(self, prefix: bytes, operands: list[Operand]) -> bytes:
        # `prefix` is the leading opcode byte(s) (one for VAR, two for EXT). Then a
        # types byte gives the type of each of up to four operands in two-bit
        # fields (high field first), 11 marking an omitted operand, then the
        # operands themselves.
        out = bytearray(prefix)
        types = 0
        for i in range(4):
            kind = operands[i].kind if i < len(operands) else OMITTED
            types |= kind << ((3 - i) * 2)
        out.append(types)
        base = len(out)  # operands begin after the opcode and types bytes
        for i, op in enumerate(operands):
            # A call target or string address is not known yet: record where its
            # two placeholder bytes sit so the linker can patch the packed value.
            self._note_ref(op, len(self.code) + base + self._span(operands[:i]))
            out += self._operand_bytes(op)
        return bytes(out)

    @staticmethod
    def _span(operands: list[Operand]) -> int:
        return sum(2 if o.kind == LARGE else 1 for o in operands)

    def _operand_bytes(self, op: Operand) -> bytes:
        if op.kind == LARGE:
            return bytes([(op.value >> 8) & 0xFF, op.value & 0xFF])
        return bytes([op.value & 0xFF])

    def _note_ref(self, op: Operand, offset_in_code: int) -> None:
        if op.routine is not None:
            self.fixups.append(_Fixup(offset_in_code, "call", op.routine))
        elif op.string is not None:
            self.fixups.append(_Fixup(offset_in_code, "strref", op.string))

    def _emit_branch(self, label: str, on_true: bool) -> None:
        # Reserve two bytes for the wide form; relax() later rewrites the branch to
        # the one-byte short form where the offset fits (B6.3).
        self.fixups.append(_Fixup(len(self.code), "branch", label, on_true, True))
        self.code += b"\x00\x00"

    def relax(self) -> None:
        """Tighten this routine's intra-routine control flow (B6.3, the dense-
        codegen size lever, docs/00 section 5), then settle every branch and jump
        offset, leaving only the inter-routine call and string-ref fixups for
        link(), repositioned to match the shortened code. Three peepholes apply:

        - Short-form branches: a forward branch whose offset fits 2..63 takes the
          one-byte form instead of the two-byte wide form.
        - Branch-to-return: a branch whose target is a bare rfalse / rtrue returns
          directly through the short-form offset 0 / 1, never reaching the label.
        - One-byte jumps: a forward jump whose offset fits 2..255 uses the one-byte
          small-constant operand (opcode 0x9C) instead of the two-byte form (0x8C).

        Sizing is a fixpoint: shortening one element pulls every element that spans
        it closer to its target, which can bring another into range. Shrinking only
        shortens distances, and a forward offset bottoms out at its short-form
        minimum of 2, so it never reaches the 0/1 the machine reads as a return,
        and the iteration converges. Offsets here are PC-relative within the
        routine, so this is independent of where the linker places it."""
        branches = [f for f in self.fixups if f.kind == "branch"]
        jumps = [f for f in self.fixups if f.kind == "jump"]
        if not branches and not jumps:
            return  # nothing intra-routine to settle; calls/strrefs stay for link

        # A branch whose target is a bare return (rfalse 0xB1 -> 0, rtrue 0xB0 -> 1)
        # returns directly via the short offset; it is always one byte.
        retval: dict = {}
        for f in branches:
            b = self.code[self.labels[f.target]]
            if b == 0xB1:
                retval[id(f)] = 0
            elif b == 0xB0:
                retval[id(f)] = 1

        # Each relocatable element: a branch is two bytes at f.offset; a jump is
        # three bytes starting at its opcode (f.offset - 1). `size` is the chosen
        # encoded length, `start` the element's first byte, `span` its original.
        start: dict = {}
        span: dict = {}
        size: dict = {}
        for f in branches:
            start[id(f)] = f.offset
            span[id(f)] = 2
            size[id(f)] = 1 if id(f) in retval else 2
        for f in jumps:
            start[id(f)] = f.offset - 1
            span[id(f)] = 3
            size[id(f)] = 3
        elems = branches + jumps

        def shift(old_p: int) -> int:
            return sum(span[id(f)] - size[id(f)] for f in elems if start[id(f)] < old_p)

        def newpos(old_p: int) -> int:
            return old_p - shift(old_p)

        changed = True
        while changed:
            changed = False
            for f in branches:
                if size[id(f)] != 2 or id(f) in retval:
                    continue
                off1 = newpos(self.labels[f.target]) - newpos(f.offset) + 1
                if 2 <= off1 <= 63:
                    size[id(f)] = 1
                    changed = True
            for f in jumps:
                if size[id(f)] != 3:
                    continue
                off = newpos(self.labels[f.target]) - newpos(start[id(f)])
                if 2 <= off <= 255:  # one-byte small-constant operand (forward only)
                    size[id(f)] = 2
                    changed = True

        by_pos: dict = {}
        for f in branches:
            by_pos[f.offset] = ("branch", f)
        for f in jumps:
            by_pos[f.offset - 1] = ("jump", f)
        for f in self.fixups:
            if f.kind in ("call", "strref"):
                by_pos[f.offset] = ("keep", f)

        new_code = bytearray()
        new_fixups: list[_Fixup] = []
        old = 0
        n = len(self.code)
        while old < n:
            entry = by_pos.get(old)
            if entry is None:
                new_code.append(self.code[old])
                old += 1
                continue
            kind, f = entry
            if kind == "branch":
                if id(f) in retval:
                    off = retval[id(f)]  # 0 = rfalse, 1 = rtrue, as a short-form offset
                elif size[id(f)] == 1:
                    off = newpos(self.labels[f.target]) - newpos(f.offset) + 1
                else:
                    off = newpos(self.labels[f.target]) - newpos(f.offset)
                if size[id(f)] == 1:
                    if not (0 <= off <= 63):
                        raise AssertionError(
                            f"short branch offset {off} out of 0..63 in "
                            f"{self.name} -> {f.target}"
                        )
                    b = 0x40 | (off & 0x3F)  # short form: bit 6 set, 6-bit offset
                    if f.on_true:
                        b |= 0x80
                    new_code.append(b)
                else:
                    if not (-8192 <= off <= 8191):
                        raise AssertionError(
                            f"long branch offset {off} out of signed 14 bits in "
                            f"{self.name} -> {f.target}"
                        )
                    word = off & 0x3FFF
                    hi = word >> 8
                    if f.on_true:
                        hi |= 0x80
                    new_code.append(hi)
                    new_code.append(word & 0xFF)
                old += 2
            elif kind == "jump":
                op_new = newpos(start[id(f)])
                target_new = newpos(self.labels[f.target])
                if size[id(f)] == 2:
                    off = target_new - op_new  # short jump: PC after = opcode + 2
                    new_code.append(0x9C)  # 1OP, small-constant operand, jump
                    new_code.append(off & 0xFF)
                else:
                    off = (target_new - op_new - 1) & 0xFFFF  # wide: operand is opcode+1
                    new_code.append(0x8C)  # 1OP, large-constant operand, jump
                    new_code.append((off >> 8) & 0xFF)
                    new_code.append(off & 0xFF)
                old += 3
            else:  # keep: an inter-routine fixup, repositioned, bytes copied as placeholder
                new_fixups.append(_Fixup(len(new_code), f.kind, f.target, f.on_true, f.wide))
                new_code.append(self.code[old])
                new_code.append(self.code[old + 1])
                old += 2
        self.code = new_code
        self.fixups = new_fixups
        self.labels = {}


def link(entry: Routine, routines: list[Routine], base_addr: int, scale: int = 4):
    """Lay out the entry stub and routines in high memory starting at base_addr.
    Returns the high-memory blob, the initial program counter, and the list of
    (absolute-offset-in-blob, string-id) packed-string references still to be
    resolved once the strings are laid out (by the caller, in build_story).

    `scale` is the packed-address unit: a routine's packed address is its byte
    address / scale, so each routine is aligned to a scale-byte boundary. It is 4
    for z5 and 8 for z8 (the only difference the larger version needs here)."""
    blob = bytearray()
    starts: dict[str, int] = {}

    # Settle each routine's intra-routine branches and jumps first (and shorten the
    # branches that fit), so the code is at its final size before it is placed.
    entry.relax()
    for r in routines:
        r.relax()

    # The entry stub is placed first, with no routine header.
    starts[entry.name] = base_addr
    entry_code_start = 0
    blob += entry.code

    packed: dict[str, int] = {}
    code_starts: dict[str, int] = {entry.name: entry_code_start}
    for r in routines:
        while (base_addr + len(blob)) % scale != 0:
            blob.append(0)
        addr = base_addr + len(blob)
        starts[r.name] = addr
        packed[r.name] = addr // scale
        blob.append(r.nlocals & 0xFF)  # v5 header: local count, no init words
        code_starts[r.name] = len(blob)
        blob += r.code

    # Backpatch each routine's (and the entry's) fixups. String references are
    # collected for the caller, which knows the string addresses.
    strrefs: list[tuple[int, str]] = []
    for r in [entry] + routines:
        cs = code_starts[r.name]
        for fx in r.fixups:
            pos = cs + fx.offset
            if fx.kind == "strref":
                strrefs.append((pos, fx.target))
                continue
            if fx.kind == "call":
                if fx.target not in packed:
                    raise KeyError(f"call to unknown routine '{fx.target}'")
                value = packed[fx.target]
                blob[pos] = (value >> 8) & 0xFF
                blob[pos + 1] = value & 0xFF
            elif fx.kind == "branch":
                target = r.labels[fx.target]
                # New PC = address-after-branch-data + offset - 2, so for a
                # destination at code offset `target`, offset = target - fx.offset.
                offset = target - fx.offset
                if not (-8192 <= offset <= 8191):
                    raise AssertionError(
                        f"branch offset {offset} out of signed 14 bits in "
                        f"{r.name} -> {fx.target}"
                    )
                word = offset & 0x3FFF
                hi = word >> 8
                if fx.on_true:
                    hi |= 0x80  # branch when the condition is true
                # bit 6 = 0 selects the two-byte (wide) form
                blob[pos] = hi
                blob[pos + 1] = word & 0xFF
            else:  # jump: a signed 16-bit offset operand
                target = r.labels[fx.target]
                offset = (target - fx.offset) & 0xFFFF
                blob[pos] = (offset >> 8) & 0xFF
                blob[pos + 1] = offset & 0xFF

    return bytes(blob), base_addr + entry_code_start, strrefs, packed
