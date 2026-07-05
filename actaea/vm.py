# vm.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The executor (M3): the evaluation stack, call frames with their locals and
return addresses, and the run loop over decode.py's instructions.

This began as the computational machine (M3) and grew a milestone at a
time; with M10's save, restore, and restart the opcode set is complete.
An opcode with no handler is a loud VMError, never a silent no-op
(sound_effect is the one designed exception: docs/06 declares sound a
no-op forever).

Signedness discipline: memory hands out unsigned words; every opcode that
compares, multiplies, divides, or offsets goes through to_signed/from_signed
from memory.py. No ad-hoc sign arithmetic anywhere else."""

import random as _random

from .decode import LARGE, SMALL, VARIABLE, decode
from .errors import ActaeaError
from .dictionary import Dictionary, tokenise
from .memory import from_signed, to_signed
from .objects import ObjectTable
from .quetzal import QuetzalError
from . import quetzal
from .screen import ScreenModel
from .text import TextEngine


class VMError(ActaeaError):
    """The story did something no well-formed story does (divide by zero,
    call a non-routine, underflow its own stack). The address is included:
    this is Actaea playing fizmo's role, naming the fault instead of
    executing garbage."""


def _copy_frames(frames):
    out = []
    for f in frames:
        c = Frame(f.return_pc, f.store, list(f.locals), f.argc)
        c.stack = list(f.stack)
        out.append(c)
    return out


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
        self.objects = ObjectTable(self.mem, story.header.objects)
        self.text = TextEngine(self.mem, story.header)
        self.dictionary = Dictionary(self.mem, story.header.dictionary, self.text)
        # The entry point is a bare instruction stream, not a routine, so it
        # runs in a base pseudo-frame that nothing ever returns from.
        self.frames = [Frame(return_pc=0, store=None, locals_=[], argc=0)]
        self.halted = False
        self.rng = _random.Random()
        # In-memory undo: a stack of (dynamic memory, frames, pc, store var)
        # snapshots. save_undo pushes one and yields 1; restore_undo pops,
        # rewinds, and makes that save_undo yield 2 instead (S 15). The
        # file-based Quetzal save arrives with M10; undo needs no files.
        self.undo: list = []
        # Output streams (S 7): 1 is the screen, 2 the transcript (a flag
        # here; the harness keeps no file), 3 redirects into a memory table
        # and NESTS (a stack of up to 16 levels; while any level is open,
        # no other stream receives output), 4 is a commands file (ignored).
        self.screen_on = True
        self.transcript_on = False
        self.stream3: list = []
        # The window model (M8): screen.py owns the split, the upper
        # window's cell grid, and the cursor; lower-window text passes
        # through it to the io sink. Front-ends render the grid via its
        # on_change hook; headless sinks simply never look at it.
        self.screen = ScreenModel(io)
        self.font = 1  # the current set_font choice (1 normal, 4 fixed)
        # The terminating-characters table (S 10.7): ZSCII function-key
        # codes, beyond Enter, that end a read; 255 means all of them.
        self.terminators = frozenset()
        if story.header.terminating:
            codes = []
            addr = story.header.terminating
            while (c := self.mem.byte(addr)) != 0:
                codes.append(c)
                addr += 1
            self.terminators = frozenset(codes)
        # Stream 2, the transcript: a real file (M11). The handle opens on
        # first use and stays for the session (S 7.1.1.2: one file, however
        # often the game toggles); transcript_on mirrors Flags 2 bit 0.
        self.transcript = None
        # An input interrupt's return value lands here (see call_interrupt).
        self.interrupt_result = 0
        self._init_header()

    # -- the output funnel: every print opcode lands here ------------------------

    def _print(self, text: str) -> None:
        if self.stream3:
            table = self.stream3[-1][1]
            for ch in text:
                table.append(13 if ch == "\n" else self.text.unicode_to_zscii(ch))
            return
        if self.screen_on:
            self.screen.write(text)
        # The transcript records the lower window only (S 7.1.1): status
        # lines and quote boxes are screen dressing, not the story.
        if self.transcript_on and self.transcript and self.screen.window == 0:
            self.transcript.write(text)

    def _init_header(self) -> None:
        """The interpreter-set header fields (S 11): what this machine can
        do, stamped at boot (and again after restart/restore, S 6.1.6.2).
        The headless harness claims the text styles (the console prints
        anything) and no colour, pictures, sound, or timed input; the GUI
        front-end will raise its own flags when it exists."""
        m = self.mem
        flags1 = m.byte(0x01)
        # Bits 2..4: boldface, italic, fixed-space; bit 0: colours (M9: the
        # model carries them and the window renders them; a console simply
        # shows none, which the standard permits of any colour).
        flags1 |= 0x1D
        # Bit 7: timed input. Only a front-end with an event loop can run
        # input interrupts (the GUI); a blocking console honestly cannot.
        if getattr(self.io, "supports_timed", False):
            flags1 |= 0x80
        m.set_byte(0x01, flags1)
        m.set_byte(0x1E, 0)      # interpreter number: unspecified
        m.set_byte(0x1F, ord("A"))  # interpreter version: A for Actaea
        m.set_byte(0x20, 255)    # screen height in lines: 255 = "infinite"
        m.set_byte(0x21, 80)     # screen width in characters
        m.set_word(0x22, 80)     # screen width in units
        m.set_word(0x24, 255)    # screen height in units
        m.set_byte(0x26, 1)      # font width in units (v5 order)
        m.set_byte(0x27, 1)      # font height in units
        # Actaea's own screen is black on white paper (Stefan's ruling,
        # 2026-07-05): a game that wants a dark screen SETS its colours
        # (zcolor.background + the erase the compiler emits with it).
        # Declared here so games can read what "default" means (S 8.3.2).
        m.set_byte(0x2C, 9)      # default background: white
        m.set_byte(0x2D, 2)      # default foreground: black
        m.set_word(0x32, 0x0101)  # Standard revision 1.1

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
        if frame.store == -1:
            # An input interrupt's frame (call_interrupt): the value goes to
            # the interpreter, not to any variable.
            self.interrupt_result = value
        elif frame.store is not None:
            self._write_var(frame.store, value)

    def call_interrupt(self, packed: int) -> int:
        """Run an interrupt routine to completion NOW, mid-read (S 8.4.2:
        the timed-input routine), and return its value. The routine runs as
        a nested execution on the same frames: a frame with the sentinel
        store -1 is pushed and stepped until it returns, which delivers the
        value to interrupt_result instead of a variable. The read that is
        waiting resumes exactly where it was."""
        if packed == 0:
            return 0
        addr = self.mem.unpack(packed)
        nlocals = self.mem.byte(addr)
        if nlocals > 15:
            raise VMError(f"interrupt call to {addr:#07x}, not a routine")
        depth = len(self.frames)
        saved_pc = self.pc
        self.frames.append(
            Frame(return_pc=saved_pc, store=-1, locals_=[0] * nlocals, argc=0)
        )
        self.pc = addr + 1
        self.interrupt_result = 0
        while len(self.frames) > depth and not self.halted:
            self.step()
        return self.interrupt_result

    # -- the loop --------------------------------------------------------------

    def step(self) -> None:
        ins = decode(self.mem, self.pc)
        self.pc = ins.next
        handler = self._ops.get(ins.name)
        if handler is not None:
            handler(self, ins)
            return
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

    # The table opcodes compute array + index in 16-bit arithmetic, wrapping
    # (the address space they byte-address IS 16 bits): Inform emits negative
    # indexes freely, and Anchorhead reads below its array at boot. Every
    # reference interpreter wraps here; a range fault would be wrong.

    def _op_loadw(self, ins):
        array, index = self._values(ins)
        self._write_var(ins.store, self.mem.word((array + 2 * index) & 0xFFFF))

    def _op_loadb(self, ins):
        array, index = self._values(ins)
        self._write_var(ins.store, self.mem.byte((array + index) & 0xFFFF))

    def _op_storew(self, ins):
        array, index, value = self._values(ins)
        self.mem.set_word((array + 2 * index) & 0xFFFF, value)

    def _op_storeb(self, ins):
        array, index, value = self._values(ins)
        self.mem.set_byte((array + index) & 0xFFFF, value)

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

    # -- the object tree (M4; the table logic lives in objects.py) --

    def _op_jin(self, ins):
        a, b = self._values(ins)
        self._branch(ins, self.objects.parent(a) == b)

    def _op_test_attr(self, ins):
        obj, attr = self._values(ins)
        self._branch(ins, self.objects.test_attr(obj, attr))

    def _op_set_attr(self, ins):
        obj, attr = self._values(ins)
        self.objects.set_attr(obj, attr)

    def _op_clear_attr(self, ins):
        obj, attr = self._values(ins)
        self.objects.clear_attr(obj, attr)

    def _op_insert_obj(self, ins):
        obj, dest = self._values(ins)
        self.objects.insert(obj, dest)

    def _op_remove_obj(self, ins):
        (obj,) = self._values(ins)
        self.objects.remove(obj)

    def _op_get_parent(self, ins):
        (obj,) = self._values(ins)
        self._write_var(ins.store, self.objects.parent(obj))

    def _op_get_sibling(self, ins):
        # Stores AND branches: the branch is on the result being nonzero.
        (obj,) = self._values(ins)
        s = self.objects.sibling(obj)
        self._write_var(ins.store, s)
        self._branch(ins, s != 0)

    def _op_get_child(self, ins):
        (obj,) = self._values(ins)
        c = self.objects.child(obj)
        self._write_var(ins.store, c)
        self._branch(ins, c != 0)

    def _op_get_prop(self, ins):
        obj, prop = self._values(ins)
        self._write_var(ins.store, self.objects.get_prop(obj, prop))

    def _op_put_prop(self, ins):
        obj, prop, value = self._values(ins)
        self.objects.put_prop(obj, prop, value)

    def _op_get_prop_addr(self, ins):
        obj, prop = self._values(ins)
        self._write_var(ins.store, self.objects.get_prop_addr(obj, prop))

    def _op_get_prop_len(self, ins):
        (addr,) = self._values(ins)
        self._write_var(ins.store, self.objects.get_prop_len(addr))

    def _op_get_next_prop(self, ins):
        obj, prop = self._values(ins)
        self._write_var(ins.store, self.objects.get_next_prop(obj, prop))

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
        if self.transcript:
            self.transcript.flush()
        self.halted = True

    # -- text output (M5: the engine lives in text.py) --

    def _op_print_num(self, ins):
        (v,) = self._values(ins)
        self._print(str(to_signed(v)))

    def _op_print_char(self, ins):
        (c,) = self._values(ins)
        self._print(self.text.zscii_to_unicode(c))

    def _op_new_line(self, ins):
        self._print("\n")

    def _op_print(self, ins):
        # The inline string sits at the end of the instruction; the decoder
        # kept its span, so its address is the instruction end minus it.
        text, _ = self.text.decode(ins.next - len(ins.text))
        self._print(text)

    def _op_print_ret(self, ins):
        self._op_print(ins)
        self._print("\n")
        self._ret(1)

    def _op_print_addr(self, ins):
        (addr,) = self._values(ins)
        self._print(self.text.decode(addr)[0])

    def _op_print_paddr(self, ins):
        (packed,) = self._values(ins)
        self._print(self.text.decode(self.mem.unpack(packed))[0])

    def _op_print_obj(self, ins):
        (obj,) = self._values(ins)
        addr, _ = self.objects.name_addr(obj)
        self._print(self.text.decode(addr)[0])

    def _op_print_table(self, ins):
        vals = self._values(ins)
        addr, width = vals[0], vals[1]
        height = vals[2] if len(vals) > 2 else 1
        skip = vals[3] if len(vals) > 3 else 0
        # The honest headless rendering: rows as lines. On the cell grid
        # (M8) this draws at the cursor, row below row; the io pipe cannot
        # position, so a newline stands in for the cursor drop.
        for row in range(height):
            if row:
                self._print("\n")
            base = addr + row * (width + skip)
            self._print(
                "".join(self.text.zscii_to_unicode(self.mem.byte(base + i))
                        for i in range(width))
            )

    def _op_print_unicode(self, ins):
        (code,) = self._values(ins)
        self._print(chr(code))

    def _op_check_unicode(self, ins):
        # Python strings print anything and (from M7) input returns anything,
        # so both the can-print and can-read bits stand.
        (_,) = self._values(ins)
        self._write_var(ins.store, 3)

    # -- input (M6: the console harness's read; timed input is a front-end
    # capability and arrives with the GUI work) --

    def _sync_transcript(self) -> None:
        """Flags 2 bit 0 IS the transcript switch (S 7.3, 7.4): the game may
        flip the bit directly rather than calling output_stream, so the
        interpreter checks at every input, the turn boundary. Opening the
        file happens once per session; a refused file clears the bit again
        (S 7.1.1.1), which is how the game learns it did not happen."""
        want = bool(self.mem.word(0x10) & 1)
        if want and self.transcript is None:
            path = self.io.transcript_path("transcript.txt")
            if path:
                try:
                    self.transcript = open(path, "a", encoding="utf-8")
                except OSError:
                    path = None
            if not path:
                self.mem.set_word(0x10, self.mem.word(0x10) & ~1 & 0xFFFF)
                want = False
        self.transcript_on = want

    def _op_read(self, ins):
        # aread text parse [time routine] -> terminator. The text buffer is
        # byte 0 max letters, byte 1 the typed length, characters from byte 2,
        # lower-cased by the machine (S 15 read). Byte 1 nonzero on entry is
        # PRELOADED input (S 15, "left over"): the game printed it and the
        # line continues from there, so it goes to the front-end to make
        # editable and comes back as part of the line, never re-printed.
        vals = self._values(ins)
        text_addr, parse_addr = vals[0], vals[1] if len(vals) > 1 else 0
        time = vals[2] if len(vals) > 2 else 0
        routine = vals[3] if len(vals) > 3 else 0
        self._sync_transcript()
        max_len = self.mem.byte(text_addr)
        preload = "".join(
            self.text.zscii_to_unicode(self.mem.byte(text_addr + 2 + i))
            for i in range(self.mem.byte(text_addr + 1))
        )
        line, term = self.io.read_line(
            max_len, preload=preload, terminators=self.terminators,
            timeout=time / 10.0,
            on_timeout=(lambda: self.call_interrupt(routine) != 0)
            if time and routine else None,
        )
        line = line.lower()
        for i, ch in enumerate(line):
            self.mem.set_byte(text_addr + 2 + i, self.text.unicode_to_zscii(ch))
        self.mem.set_byte(text_addr + 1, len(line))
        if self.transcript_on and self.transcript:
            self.transcript.write(line + "\n")
        if term == 0:
            # Timed out: the routine asked for the input to end. What was
            # typed stays in the buffer as next time's preload (that is how
            # an interrupted command line survives); nothing is parsed.
            self._write_var(ins.store, 0)
            return
        if parse_addr:
            tokenise(self.mem, text_addr, parse_addr, self.dictionary)
        self._write_var(ins.store, term)

    def _op_read_char(self, ins):
        # read_char 1 [time routine] -> zscii. The first operand is always 1
        # (the keyboard). The io hands back a Unicode codepoint for
        # printables and ZSCII codes for the specials (13, 8, 27, and the
        # function keys, which have no Unicode anyway); the translation to
        # ZSCII happens here, where the text engine lives, so accented
        # input works whatever the front-end.
        vals = self._values(ins)
        time = vals[1] if len(vals) > 1 else 0
        routine = vals[2] if len(vals) > 2 else 0
        code = self.io.read_char(
            timeout=time / 10.0,
            on_timeout=(lambda: self.call_interrupt(routine) != 0)
            if time and routine else None,
        )
        if code >= 32 and not 129 <= code <= 154 and not 252 <= code <= 254:
            code = self.text.unicode_to_zscii(chr(code))
        self._write_var(ins.store, code)

    def _op_save_undo(self, ins):
        self.undo.append(
            (bytes(self.mem.mem[:self.mem.static_base]),
             _copy_frames(self.frames), self.pc, ins.store)
        )
        self._write_var(ins.store, 1)

    def _op_restore_undo(self, ins):
        if not self.undo:
            self._write_var(ins.store, 0)  # nothing to rewind: report failure
            return
        dyn, frames, pc, store = self.undo.pop()
        self.mem.mem[:self.mem.static_base] = dyn
        self.frames = _copy_frames(frames)
        self.pc = pc
        # Resume as if that save_undo had just returned 2 (S 15 save_undo).
        # The interpreter-set header fields survive the rewind (S 6.1.6.2).
        self._write_var(store, 2)
        self._init_header()

    # -- the file-based state trio (M10: Quetzal in quetzal.py, the file
    # channel through io.save_path/restore_path) --

    def _op_save(self, ins):
        # EXT:0. The game-state form has no operands; the auxiliary form
        # (save table bytes name) writes a raw memory region instead, which
        # no Arcturus game and none of the conformance set uses, so it
        # honestly reports failure rather than pretending.
        if ins.operands:
            self._values(ins)
            self._write_var(ins.store, 0)
            return
        # The saved PC points AT this instruction's store byte (the last
        # byte of the instruction), the Quetzal convention: restore writes
        # 2 through it and resumes at the byte after.
        data = quetzal.write(self.mem, self.frames, ins.next - 1)
        path = self.io.save_path("save.qzl")
        if not path:
            self._write_var(ins.store, 0)
            return
        try:
            with open(path, "wb") as f:
                f.write(data)
        except OSError:
            self._write_var(ins.store, 0)
            return
        self._write_var(ins.store, 1)

    def _op_restore(self, ins):
        # EXT:1. Failure stores 0 and play continues; success never stores
        # here at all, because execution resumes inside the save that wrote
        # the file, storing 2 there (S 15 restore).
        if ins.operands:
            self._values(ins)
            self._write_var(ins.store, 0)
            return
        path = self.io.restore_path("save.qzl")
        if not path:
            self._write_var(ins.store, 0)
            return
        try:
            with open(path, "rb") as f:
                dyn, frames, pc = quetzal.read(f.read(), self.mem)
        except OSError:
            self._write_var(ins.store, 0)
            return
        except QuetzalError as e:
            # The reason is player-facing: "a different story" deserves
            # better than a bare failure message from the game.
            self._print(f"[{e}]\n")
            self._write_var(ins.store, 0)
            return
        # The transcription and fixed-pitch bits of Flags 2 survive from
        # BEFORE the restore (S 6.1.6.1): they describe this session's
        # transcript, not the saved one's.
        flags2 = self.mem.word(0x10) & 0x3
        self.mem.mem[:self.mem.static_base] = dyn
        self.mem.set_word(0x10, (self.mem.word(0x10) & 0xFFFC) | flags2)
        self.frames = []
        for return_pc, store, locals_, argc, stack in frames:
            f = Frame(return_pc, store, locals_, argc)
            f.stack = stack
            self.frames.append(f)
        self.stream3 = []
        self.screen_on = True
        self._init_header()  # interpreter fields are stamped afresh (S 6.1.6.2)
        var = self.mem.byte(pc)  # the save's store byte
        self.pc = pc + 1
        self._write_var(var, 2)

    def _op_restart(self, ins):
        # Back to the pristine image, except the two Flags 2 bits that
        # describe the session (S 6.1.6.1), with the machine state and the
        # screen reset around it.
        flags2 = self.mem.word(0x10) & 0x3
        self.mem.reset()
        self.mem.set_word(0x10, (self.mem.word(0x10) & 0xFFFC) | flags2)
        self.frames = [Frame(return_pc=0, store=None, locals_=[], argc=0)]
        self.pc = self.story.header.initial_pc
        self.stream3 = []
        self.screen_on = True
        self.font = 1
        self.screen.set_style(0)
        self.screen.set_colour(1, 1)
        self.screen.erase_window(-1)  # unsplit and clear, back to the boot screen
        self._init_header()

    def _op_output_stream(self, ins):
        vals = self._values(ins)
        n = to_signed(vals[0])
        if n == 0:
            return
        if n == 3:
            if len(self.stream3) >= 16:
                raise VMError(f"output_stream 3 nested past 16 at {ins.addr:#07x}")
            self.stream3.append((vals[1], []))
        elif n == -3:
            if not self.stream3:
                raise VMError(f"output_stream -3 with none open at {ins.addr:#07x}")
            table, codes = self.stream3.pop()
            # The table gets its character count in the first word, the
            # ZSCII codes after it (S 7.1.2.1).
            self.mem.set_word(table, len(codes))
            for i, c in enumerate(codes):
                self.mem.set_byte(table + 2 + i, c)
        elif n in (1, -1):
            self.screen_on = n > 0
        elif n in (2, -2):
            # Stream 2 and Flags 2 bit 0 are one switch seen two ways
            # (S 7.1.1.1): selecting the stream sets the bit, and the sync
            # opens the transcript file on first use.
            f2 = self.mem.word(0x10)
            self.mem.set_word(0x10, (f2 | 1) if n > 0 else (f2 & 0xFFFE))
            self._sync_transcript()
        elif n in (4, -4):
            pass  # the commands file: nothing to record headless
        else:
            raise VMError(f"output_stream {n} at {ins.addr:#07x}")

    def _op_input_stream(self, ins):
        self._values(ins)  # stream 1 (a command file) never exists headless

    def _op_scan_table(self, ins):
        vals = self._values(ins)
        x, table, length = vals[0], vals[1], vals[2]
        form = vals[3] if len(vals) > 3 else 0x82
        words = bool(form & 0x80)
        step = form & 0x7F
        if step == 0:
            raise VMError(f"scan_table with zero entry length at {ins.addr:#07x}")
        found = 0
        for i in range(length):
            addr = table + i * step
            v = self.mem.word(addr) if words else self.mem.byte(addr)
            if v == x:
                found = addr
                break
        self._write_var(ins.store, found)
        self._branch(ins, found != 0)

    def _op_copy_table(self, ins):
        first, second, size = self._values(ins)
        n = to_signed(size)
        if second == 0:
            # Zero the first table (S 15 copy_table).
            for i in range(abs(n)):
                self.mem.set_byte(first + i, 0)
            return
        data = bytes(self.mem.mem[first:first + abs(n)])
        if n < 0:
            # Negative size: copy forwards regardless of overlap, exactly as
            # the standard demands (the game wants the smearing behavior).
            for i in range(abs(n)):
                self.mem.set_byte(second + i, self.mem.byte(first + i))
        else:
            # Positive: corruption-safe (copy from a snapshot).
            for i in range(n):
                self.mem.set_byte(second + i, data[i])

    def _op_set_text_style(self, ins):
        # The screen model is the one truth for the current look, in both
        # windows: cells record it, and the lower-window renderer reads it
        # at print time (M9).
        (style,) = self._values(ins)
        self.screen.set_style(style)

    def _op_split_window(self, ins):
        (lines,) = self._values(ins)
        self.screen.split(lines)

    def _op_set_window(self, ins):
        (w,) = self._values(ins)
        self.screen.select(w)

    def _op_erase_window(self, ins):
        (n,) = self._values(ins)
        self.screen.erase_window(to_signed(n))

    def _op_erase_line(self, ins):
        vals = self._values(ins)
        if vals and vals[0] == 1:  # operand 1 = "to end of line" (S 15)
            self.screen.erase_line()

    def _op_set_cursor(self, ins):
        vals = self._values(ins)
        row = to_signed(vals[0])
        col = vals[1] if len(vals) > 1 else 1
        self.screen.set_cursor(row, col)

    def _op_get_cursor(self, ins):
        (table,) = self._values(ins)
        row, col = self.screen.get_cursor()
        self.mem.set_word(table, row)
        self.mem.set_word(table + 2, col)

    def _op_buffer_mode(self, ins):
        # Whether the lower window buffers for word wrap (S 8.7.3.1): purely
        # a rendering policy. The console neither wraps nor unwraps; the cell
        # model takes this seriously at M8.
        self._values(ins)

    def _op_set_colour(self, ins):
        vals = self._values(ins)
        self.screen.set_colour(vals[0], vals[1] if len(vals) > 1 else 0)

    def _op_set_true_colour(self, ins):
        vals = self._values(ins)
        self.screen.set_true_colour(
            to_signed(vals[0]),
            to_signed(vals[1]) if len(vals) > 1 else -1,
        )

    def _op_set_font(self, ins):
        # Fonts 1 (normal) and 4 (fixed) are the same face in a monospace
        # interpreter, so both are "available"; 2 and 3 (character
        # graphics) are not. The store answers the PREVIOUS font on
        # success and 0 on refusal; 0 asks without changing (S 15 set_font).
        (n,) = self._values(ins)
        if n == 0:
            self._write_var(ins.store, self.font)
        elif n in (1, 4):
            self._write_var(ins.store, self.font)
            self.font = n
        else:
            self._write_var(ins.store, 0)

    def _op_tokenise(self, ins):
        vals = self._values(ins)
        text_addr, parse_addr = vals[0], vals[1]
        dict_addr = vals[2] if len(vals) > 2 else 0
        flag = vals[3] if len(vals) > 3 else 0
        d = self.dictionary if dict_addr == 0 else Dictionary(
            self.mem, dict_addr, self.text
        )
        tokenise(self.mem, text_addr, parse_addr, d, skip_unknown=bool(flag))

    def _op_encode_text(self, ins):
        text_addr, length, from_, dest = self._values(ins)
        word = "".join(
            self.text.zscii_to_unicode(self.mem.byte(text_addr + from_ + i))
            for i in range(length)
        )
        for i, b in enumerate(self.text.encode_word(word)):
            self.mem.set_byte(dest + i, b)

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
        "jin": _op_jin, "test_attr": _op_test_attr, "set_attr": _op_set_attr,
        "clear_attr": _op_clear_attr, "insert_obj": _op_insert_obj,
        "remove_obj": _op_remove_obj, "get_parent": _op_get_parent,
        "get_sibling": _op_get_sibling, "get_child": _op_get_child,
        "get_prop": _op_get_prop, "put_prop": _op_put_prop,
        "get_prop_addr": _op_get_prop_addr, "get_prop_len": _op_get_prop_len,
        "get_next_prop": _op_get_next_prop,
        "random": _op_random, "verify": _op_verify, "piracy": _op_piracy,
        "nop": _op_nop, "quit": _op_quit,
        "print_num": _op_print_num, "print_char": _op_print_char,
        "new_line": _op_new_line,
        "print": _op_print, "print_ret": _op_print_ret,
        "print_addr": _op_print_addr, "print_paddr": _op_print_paddr,
        "print_obj": _op_print_obj, "print_table": _op_print_table,
        "print_unicode": _op_print_unicode, "check_unicode": _op_check_unicode,
        "tokenise": _op_tokenise, "encode_text": _op_encode_text,
        "read": _op_read, "read_char": _op_read_char,
        "set_text_style": _op_set_text_style, "set_font": _op_set_font,
        "save_undo": _op_save_undo, "restore_undo": _op_restore_undo,
        "save": _op_save, "restore": _op_restore, "restart": _op_restart,
        "split_window": _op_split_window, "set_window": _op_set_window,
        "erase_window": _op_erase_window, "erase_line": _op_erase_line,
        "set_cursor": _op_set_cursor, "get_cursor": _op_get_cursor,
        "buffer_mode": _op_buffer_mode, "set_colour": _op_set_colour, "set_true_colour": _op_set_true_colour,
        "output_stream": _op_output_stream, "input_stream": _op_input_stream,
        "scan_table": _op_scan_table, "copy_table": _op_copy_table,
    }
