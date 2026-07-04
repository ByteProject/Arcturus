# vm.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The executor (M3): the evaluation stack, call frames with their locals and
return addresses, and the run loop over decode.py's instructions.

This milestone implements the computational machine: arithmetic and logic,
comparisons and branches, load and store, the whole call/return family,
catch/throw, random, and the numeric prints that make results observable
through the io.py boundary. Objects and properties arrive with M4, Z-string
text with M5, reading input with the harness and GUI milestones; touching
one of those opcodes now raises UnimplementedOpcode naming the milestone,
which is a deliberate loud failure, never a silent no-op (sound_effect is
the one designed exception: docs/06 declares sound a no-op forever).

Signedness discipline: memory hands out unsigned words; every opcode that
compares, multiplies, divides, or offsets goes through to_signed/from_signed
from memory.py. No ad-hoc sign arithmetic anywhere else."""

import random as _random

from .decode import LARGE, SMALL, VARIABLE, decode
from .errors import ActaeaError
from .memory import from_signed, to_signed


class VMError(ActaeaError):
    """The story did something no well-formed story does (divide by zero,
    call a non-routine, underflow its own stack). The address is included:
    this is Actaea playing fizmo's role, naming the fault instead of
    executing garbage."""


class UnimplementedOpcode(ActaeaError):
    """A real opcode whose milestone has not landed yet."""


# Opcodes that exist but belong to later milestones; the error names where
# each will arrive so a premature integration test explains itself.
_LATER = {
    "jin": "M4", "test_attr": "M4", "set_attr": "M4", "clear_attr": "M4",
    "insert_obj": "M4", "remove_obj": "M4", "get_prop": "M4",
    "get_prop_addr": "M4", "get_next_prop": "M4", "get_prop_len": "M4",
    "get_sibling": "M4", "get_child": "M4", "get_parent": "M4",
    "put_prop": "M4", "print_obj": "M4",
    "print": "M5", "print_ret": "M5", "print_addr": "M5", "print_paddr": "M5",
    "tokenise": "M5", "encode_text": "M5", "print_unicode": "M5",
    "check_unicode": "M5", "print_table": "M5",
    "read": "M6", "read_char": "M6",
    "split_window": "M8", "set_window": "M8", "erase_window": "M8",
    "erase_line": "M8", "set_cursor": "M8", "get_cursor": "M8",
    "buffer_mode": "M8", "set_text_style": "M9", "set_colour": "M9",
    "set_true_colour": "M9", "set_font": "M9",
    "save": "M10", "restore": "M10", "save_undo": "M10",
    "restore_undo": "M10", "restart": "M10",
    "output_stream": "M11", "input_stream": "M11", "copy_table": "M11",
    "scan_table": "M11",
}


class Frame:
    """One routine activation. Each frame owns its slice of evaluation
    stack, exactly the shape Quetzal's Stks chunk wants back at M10."""

    __slots__ = ("return_pc", "store", "locals", "stack", "argc")

    def __init__(self, return_pc, store, locals_, argc):
        self.return_pc = return_pc
        self.store = store          # caller's store variable, None for call_*n
        self.locals = locals_
        self.stack = []
        self.argc = argc


class VM:
    """The headless machine: step() executes one instruction, run() loops
    until quit (or a fault). The only paths out are the io object and the
    memory it mutates."""

    def __init__(self, story, io):
        self.story = story
        self.mem = story.memory
        self.io = io
        self.pc = story.header.initial_pc
        self.globals_addr = story.header.globals_
        # The entry point is a bare instruction stream, not a routine, so it
        # runs in a base pseudo-frame that nothing ever returns from.
        self.frames = [Frame(return_pc=0, store=None, locals_=[], argc=0)]
        self.halted = False
        self.rng = _random.Random()

    # -- variables ----------------------------------------------------------

    def _read_var(self, n: int) -> int:
        """Variable 0 pops the stack; 1..15 are locals; 16..255 globals."""
        f = self.frames[-1]
        if n == 0:
            if not f.stack:
                raise VMError(f"stack underflow at {self.pc:#07x}")
            return f.stack.pop()
        if n < 16:
            if n > len(f.locals):
                raise VMError(f"read of local {n} of {len(f.locals)} at {self.pc:#07x}")
            return f.locals[n - 1]
        return self.mem.word(self.globals_addr + 2 * (n - 16))

    def _write_var(self, n: int, value: int) -> None:
        value &= 0xFFFF
        f = self.frames[-1]
        if n == 0:
            f.stack.append(value)
        elif n < 16:
            if n > len(f.locals):
                raise VMError(f"write to local {n} of {len(f.locals)} at {self.pc:#07x}")
            f.locals[n - 1] = value
        else:
            self.mem.set_word(self.globals_addr + 2 * (n - 16), value)

    # Indirect variable references (inc, dec, inc_chk, dec_chk, load, store,
    # pull): the standard's quirk that a reference to variable 0 reads or
    # writes the TOP of stack in place, without popping or pushing (S 6.3.4).

    def _read_indirect(self, n: int) -> int:
        f = self.frames[-1]
        if n == 0:
            if not f.stack:
                raise VMError(f"indirect read of an empty stack at {self.pc:#07x}")
            return f.stack[-1]
        return self._read_var(n)

    def _write_indirect(self, n: int, value: int) -> None:
        f = self.frames[-1]
        if n == 0:
            if not f.stack:
                raise VMError(f"indirect write to an empty stack at {self.pc:#07x}")
            f.stack[-1] = value & 0xFFFF
        else:
            self._write_var(n, value)

    # -- operands, stores, branches --------------------------------------------

    def _value(self, operand) -> int:
        t, v = operand
        if t == VARIABLE:
            return self._read_var(v)
        return v  # LARGE and SMALL carry the value itself

    def _values(self, ins) -> list:
        return [self._value(o) for o in ins.operands]

    def _branch(self, ins, condition: bool) -> None:
        on_true, offset = ins.branch
        if condition != on_true:
            return
        if offset == 0:
            self._ret(0)
        elif offset == 1:
            self._ret(1)
        else:
            # New PC = address after the branch data + offset - 2.
            self.pc = ins.next + offset - 2

    # -- calls and returns --------------------------------------------------------

    def _call(self, ins, stores: bool) -> None:
        vals = self._values(ins)
        if not vals:
            raise VMError(f"call with no routine operand at {ins.addr:#07x}")
        packed, args = vals[0], vals[1:]
        if packed == 0:
            # Calling address 0 is legal and does nothing but yield false.
            if stores:
                self._write_var(ins.store, 0)
            return
        addr = self.mem.unpack(packed)
        nlocals = self.mem.byte(addr)
        if nlocals > 15:
            raise VMError(
                f"call to {addr:#07x} which claims {nlocals} locals; "
                f"not a routine (from {ins.addr:#07x})"
            )
        locals_ = [0] * nlocals
        # Arguments land in the first locals; extras are thrown away (S 6.4.4).
        for i, a in enumerate(args[:nlocals]):
            locals_[i] = a
        self.frames.append(
            Frame(return_pc=self.pc, store=ins.store if stores else None,
                  locals_=locals_, argc=len(args))
        )
        self.pc = addr + 1

    def _ret(self, value: int) -> None:
        if len(self.frames) == 1:
            # Returning from the entry stream: Arcturus and Inform entries end
            # in quit, but a bare return here means the story is done.
            self.halted = True
            return
        frame = self.frames.pop()
        self.pc = frame.return_pc
        if frame.store is not None:
            self._write_var(frame.store, value)

    # -- the loop --------------------------------------------------------------

    def step(self) -> None:
        ins = decode(self.mem, self.pc)
        self.pc = ins.next
        handler = self._ops.get(ins.name)
        if handler is not None:
            handler(self, ins)
            return
        later = _LATER.get(ins.name)
        if later is not None:
            raise UnimplementedOpcode(
                f"{ins.name} at {ins.addr:#07x} arrives with milestone {later}"
            )
        if ins.name == "sound_effect":
            return  # the designed no-op (docs/06: no sound, forever)
        raise VMError(f"no handler for {ins.name} at {ins.addr:#07x}")

    def run(self, max_steps: int = 0) -> None:
        """Run until quit. max_steps is a test harness guard against a loop
        that never ends; 0 means no limit."""
        steps = 0
        while not self.halted:
            self.step()
            steps += 1
            if max_steps and steps >= max_steps:
                raise VMError(f"still running after {max_steps} steps")

    # -- opcode implementations ---------------------------------------------------
    # Each takes (self, ins). Grouped as the standard groups them.

    def _op_add(self, ins):
        a, b = self._values(ins)
        self._write_var(ins.store, from_signed(to_signed(a) + to_signed(b)))

    def _op_sub(self, ins):
        a, b = self._values(ins)
        self._write_var(ins.store, from_signed(to_signed(a) - to_signed(b)))

    def _op_mul(self, ins):
        a, b = self._values(ins)
        self._write_var(ins.store, from_signed(to_signed(a) * to_signed(b)))

    def _op_div(self, ins):
        a, b = self._values(ins)
        if b == 0:
            raise VMError(f"division by zero at {ins.addr:#07x}")
        # Signed division truncates toward zero (S 15, div); Python's //
        # floors, so go through int() truncation.
        self._write_var(ins.store, from_signed(int(to_signed(a) / to_signed(b))))

    def _op_mod(self, ins):
        a, b = self._values(ins)
        if b == 0:
            raise VMError(f"modulo by zero at {ins.addr:#07x}")
        sa, sb = to_signed(a), to_signed(b)
        # The remainder keeps the dividend's sign (truncating division pair).
        self._write_var(ins.store, from_signed(sa - int(sa / sb) * sb))

    def _op_or(self, ins):
        a, b = self._values(ins)
        self._write_var(ins.store, a | b)

    def _op_and(self, ins):
        a, b = self._values(ins)
        self._write_var(ins.store, a & b)

    def _op_not(self, ins):
        (a,) = self._values(ins)
        self._write_var(ins.store, (~a) & 0xFFFF)

    def _op_log_shift(self, ins):
        a, places = self._values(ins)
        p = to_signed(places)
        # Left for positive places, LOGICAL right (zero-fill) for negative.
        value = (a << p) & 0xFFFF if p >= 0 else (a & 0xFFFF) >> -p
        self._write_var(ins.store, value)

    def _op_art_shift(self, ins):
        a, places = self._values(ins)
        p = to_signed(places)
        # Left as log_shift; ARITHMETIC right (sign-extending) for negative.
        value = (a << p) & 0xFFFF if p >= 0 else from_signed(to_signed(a) >> -p)
        self._write_var(ins.store, value)

    # -- comparisons and jumps --

    def _op_je(self, ins):
        vals = self._values(ins)
        if len(vals) < 2:
            raise VMError(f"je with {len(vals)} operand(s) at {ins.addr:#07x}")
        self._branch(ins, vals[0] in vals[1:])

    def _op_jl(self, ins):
        a, b = self._values(ins)
        self._branch(ins, to_signed(a) < to_signed(b))

    def _op_jg(self, ins):
        a, b = self._values(ins)
        self._branch(ins, to_signed(a) > to_signed(b))

    def _op_jz(self, ins):
        (a,) = self._values(ins)
        self._branch(ins, a == 0)

    def _op_test(self, ins):
        bitmap, flags = self._values(ins)
        self._branch(ins, bitmap & flags == flags)

    def _op_jump(self, ins):
        (offset,) = self._values(ins)
        self.pc = ins.next + to_signed(offset) - 2

    def _op_inc_chk(self, ins):
        # The FIRST operand is a variable NUMBER (an indirect reference).
        var = self._value(ins.operands[0])
        value = self._value(ins.operands[1])
        x = from_signed(to_signed(self._read_indirect(var)) + 1)
        self._write_indirect(var, x)
        self._branch(ins, to_signed(x) > to_signed(value))

    def _op_dec_chk(self, ins):
        var = self._value(ins.operands[0])
        value = self._value(ins.operands[1])
        x = from_signed(to_signed(self._read_indirect(var)) - 1)
        self._write_indirect(var, x)
        self._branch(ins, to_signed(x) < to_signed(value))

    # -- load and store --

    def _op_store(self, ins):
        var = self._value(ins.operands[0])
        self._write_indirect(var, self._value(ins.operands[1]))

    def _op_load(self, ins):
        var = self._value(ins.operands[0])
        self._write_var(ins.store, self._read_indirect(var))

    def _op_inc(self, ins):
        var = self._value(ins.operands[0])
        self._write_indirect(var, from_signed(to_signed(self._read_indirect(var)) + 1))

    def _op_dec(self, ins):
        var = self._value(ins.operands[0])
        self._write_indirect(var, from_signed(to_signed(self._read_indirect(var)) - 1))

    def _op_loadw(self, ins):
        array, index = self._values(ins)
        self._write_var(ins.store, self.mem.word(array + 2 * to_signed(index)))

    def _op_loadb(self, ins):
        array, index = self._values(ins)
        self._write_var(ins.store, self.mem.byte(array + to_signed(index)))

    def _op_storew(self, ins):
        array, index, value = self._values(ins)
        self.mem.set_word(array + 2 * to_signed(index), value)

    def _op_storeb(self, ins):
        array, index, value = self._values(ins)
        self.mem.set_byte(array + to_signed(index), value)

    def _op_push(self, ins):
        (value,) = self._values(ins)
        self.frames[-1].stack.append(value)

    def _op_pull(self, ins):
        var = self._value(ins.operands[0])
        f = self.frames[-1]
        if not f.stack:
            raise VMError(f"pull from an empty stack at {ins.addr:#07x}")
        self._write_indirect(var, f.stack.pop())

    # -- calls, returns, catch and throw --

    def _op_call_s(self, ins):
        self._call(ins, stores=True)

    def _op_call_n(self, ins):
        self._call(ins, stores=False)

    def _op_ret(self, ins):
        (value,) = self._values(ins)
        self._ret(value)

    def _op_rtrue(self, ins):
        self._ret(1)

    def _op_rfalse(self, ins):
        self._ret(0)

    def _op_ret_popped(self, ins):
        f = self.frames[-1]
        if not f.stack:
            raise VMError(f"ret_popped from an empty stack at {ins.addr:#07x}")
        self._ret(f.stack.pop())

    def _op_catch(self, ins):
        # The current frame count; throw hands it back to unwind to here.
        self._write_var(ins.store, len(self.frames))

    def _op_throw(self, ins):
        value, frame_count = self._values(ins)
        if not 1 <= frame_count <= len(self.frames):
            raise VMError(
                f"throw to frame {frame_count} of {len(self.frames)} "
                f"at {ins.addr:#07x}"
            )
        # Unwind so the catching routine is current, then return from it
        # with the given value, exactly as if it had done `ret value`.
        del self.frames[frame_count:]
        self._ret(value)

    def _op_check_arg_count(self, ins):
        (n,) = self._values(ins)
        self._branch(ins, self.frames[-1].argc >= n)

    # -- the rest of the computational set --

    def _op_random(self, ins):
        (n,) = self._values(ins)
        sn = to_signed(n)
        if sn > 0:
            self._write_var(ins.store, self.rng.randint(1, sn))
        else:
            # Negative seeds predictably; zero reseeds from the clock. Both
            # store 0 (S 15, random).
            if sn < 0:
                self.rng.seed(-sn)
            else:
                self.rng.seed()
            self._write_var(ins.store, 0)

    def _op_verify(self, ins):
        self._branch(ins, self.story.checksum_ok())

    def _op_piracy(self, ins):
        self._branch(ins, True)  # gullible, as the standard suggests

    def _op_nop(self, ins):
        pass

    def _op_quit(self, ins):
        self.halted = True

    # -- numeric output (the full text engine is M5; these two make the
    # computational machine observable and are complete as they stand) --

    def _op_print_num(self, ins):
        (v,) = self._values(ins)
        self.io.print_text(str(to_signed(v)))

    def _op_print_char(self, ins):
        (c,) = self._values(ins)
        # ZSCII 13 is newline; 32..126 match ASCII. The rest of ZSCII (the
        # extra characters table) arrives with text.py in M5.
        if c == 13:
            self.io.print_text("\n")
        elif 32 <= c <= 126:
            self.io.print_text(chr(c))
        else:
            raise UnimplementedOpcode(
                f"print_char of ZSCII {c} at {ins.addr:#07x} needs M5's tables"
            )

    def _op_new_line(self, ins):
        self.io.print_text("\n")

    _ops = {
        "add": _op_add, "sub": _op_sub, "mul": _op_mul, "div": _op_div,
        "mod": _op_mod, "or": _op_or, "and": _op_and, "not": _op_not,
        "log_shift": _op_log_shift, "art_shift": _op_art_shift,
        "je": _op_je, "jl": _op_jl, "jg": _op_jg, "jz": _op_jz,
        "test": _op_test, "jump": _op_jump,
        "inc_chk": _op_inc_chk, "dec_chk": _op_dec_chk,
        "store": _op_store, "load": _op_load, "inc": _op_inc, "dec": _op_dec,
        "loadw": _op_loadw, "loadb": _op_loadb,
        "storew": _op_storew, "storeb": _op_storeb,
        "push": _op_push, "pull": _op_pull,
        "call_vs": _op_call_s, "call_vs2": _op_call_s, "call_2s": _op_call_s,
        "call_1s": _op_call_s,
        "call_vn": _op_call_n, "call_vn2": _op_call_n, "call_2n": _op_call_n,
        "call_1n": _op_call_n,
        "ret": _op_ret, "rtrue": _op_rtrue, "rfalse": _op_rfalse,
        "ret_popped": _op_ret_popped,
        "catch": _op_catch, "throw": _op_throw,
        "check_arg_count": _op_check_arg_count,
        "random": _op_random, "verify": _op_verify, "piracy": _op_piracy,
        "nop": _op_nop, "quit": _op_quit,
        "print_num": _op_print_num, "print_char": _op_print_char,
        "new_line": _op_new_line,
    }
