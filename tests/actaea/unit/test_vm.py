# test_vm.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M3: the execution core, driven by hand-assembled routines. The
tiny encoder here is deliberately independent of both the decoder under test
and the Arcturus compiler's assembler, so the instruction encodings are
cross-checked by a second implementation.

The story image: a v5 header, the globals table at 0x40, code from 0x220
(the entry stream first, routines 4-aligned after it), length and checksum
filled in honestly so verify has something to verify."""

import pytest

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM, UnimplementedOpcode, VMError

# -- a second, test-side instruction encoder ------------------------------------

LARGE, SMALL, VAR = 0, 1, 2


def L(v):
    return (LARGE, v)


def S(v):
    return (SMALL, v)


def V(n):
    return (VAR, n)


def _types_byte(ops):
    b = 0
    for i in range(4):
        t = ops[i][0] if i < len(ops) else 3  # 3 = omitted
        b |= t << (6 - 2 * i)
    return b


def _operand_bytes(ops):
    out = bytearray()
    for t, v in ops:
        if t == LARGE:
            out += bytes([(v >> 8) & 0xFF, v & 0xFF])
        else:
            out.append(v & 0xFF)
    return bytes(out)


def branch(on_true, offset):
    """A branch in the two-byte form (offset 0/1 = rfalse/rtrue, else the
    signed 14-bit jump the decoder computes against)."""
    raw = offset & 0x3FFF
    return bytes([(0x80 if on_true else 0) | (raw >> 8), raw & 0xFF])


def vop(opnum, *ops, store=None, count_2op=False):
    """A variable-form instruction (VAR count unless count_2op)."""
    first = (0xC0 if count_2op else 0xE0) | opnum
    out = bytes([first, _types_byte(ops)]) + _operand_bytes(ops)
    if store is not None:
        out += bytes([store])
    return out


def vop2(opnum, *ops, store=None):
    """call_vs2/call_vn2: the double-type-byte encoding, up to 8 operands."""
    b1 = 0
    b2 = 0
    for i in range(4):
        t = ops[i][0] if i < len(ops) else 3
        b1 |= t << (6 - 2 * i)
    for i in range(4):
        t = ops[i + 4][0] if i + 4 < len(ops) else 3
        b2 |= t << (6 - 2 * i)
    out = bytes([0xE0 | opnum, b1, b2]) + _operand_bytes(ops)
    if store is not None:
        out += bytes([store])
    return out


def long2(opnum, a, b, store=None):
    """Long-form 2OP: operands are small constants or variables only."""
    first = opnum
    if a[0] == VAR:
        first |= 0x40
    if b[0] == VAR:
        first |= 0x20
    out = bytes([first, a[1] & 0xFF, b[1] & 0xFF])
    if store is not None:
        out += bytes([store])
    return out


def short1(opnum, op, store=None):
    out = bytes([0x80 | (op[0] << 4) | opnum]) + _operand_bytes([op])
    if store is not None:
        out += bytes([store])
    return out


def short0(opnum):
    return bytes([0xB0 | opnum])


def ext(opnum, *ops, store=None):
    out = bytes([0xBE, opnum, _types_byte(ops)]) + _operand_bytes(ops)
    if store is not None:
        out += bytes([store])
    return out


# Named shorthands for readability in the tests.
QUIT = short0(0x0A)
RTRUE = short0(0x00)
RFALSE = short0(0x01)
NEWLINE = short0(0x0B)
SP = 0  # variable number 0: the stack


def print_num(op):
    return vop(0x06, op)


def routine(nlocals, *code):
    return bytes([nlocals]) + b"".join(code)


# -- the story builder ---------------------------------------------------------

GLOBALS = 0x40
CODE = 0x220  # 0x40 header + 0x1E0 globals; 4-aligned


ENTRY_AREA = 64  # the entry stream's fixed slot, so routine addresses never
                 # depend on the entry's length (several tests build twice:
                 # once with a placeholder entry to learn the packed layout,
                 # then for real)


def build(entry: bytes, *routines: bytes):
    """A runnable story: returns (vm, io, packed) with packed[i] the packed
    address of routines[i]."""
    assert len(entry) <= ENTRY_AREA, "entry stream outgrew its fixed slot"
    body = bytearray(entry) + bytes(ENTRY_AREA - len(entry))
    packed = []
    for r in routines:
        while (CODE + len(body)) % 4:
            body.append(0)
        packed.append((CODE + len(body)) // 4)
        body += r
    img = bytearray(CODE) + body
    while len(img) % 4:
        img.append(0)
    img[0x00] = 5
    img[0x04:0x06] = CODE.to_bytes(2, "big")   # high memory base
    img[0x06:0x08] = CODE.to_bytes(2, "big")   # initial PC: the entry stream
    img[0x0C:0x0E] = GLOBALS.to_bytes(2, "big")
    img[0x0E:0x10] = CODE.to_bytes(2, "big")   # static base: globals stay writable
    img[0x1A:0x1C] = (len(img) // 4).to_bytes(2, "big")
    img[0x1C:0x1E] = (sum(img[0x40:]) & 0xFFFF).to_bytes(2, "big")
    io = CaptureIO()
    return VM(load(bytes(img)), io), io, packed


def run(entry: bytes, *routines: bytes) -> str:
    vm, io, _ = build(entry, *routines)
    vm.run(max_steps=10000)
    return io.text


# -- arithmetic -----------------------------------------------------------------

def test_signed_arithmetic_and_wrapping():
    out = run(
        long2(0x14, S(200), S(100), store=SP)   # add -> 300
        + print_num(V(SP)) + NEWLINE
        + vop(0x16, L(300), L(300), store=SP, count_2op=True)  # mul wraps
        + print_num(V(SP)) + NEWLINE
        + vop(0x15, L(5), L(12), store=SP, count_2op=True)     # sub -> -7
        + print_num(V(SP))
        + QUIT
    )
    # 300 * 300 = 90000; 90000 mod 2^16 = 24464 (positive as signed).
    assert out == "300\n24464\n-7"


def test_division_truncates_toward_zero():
    neg7 = 0x10000 - 7
    neg2 = 0x10000 - 2
    out = run(
        vop(0x17, L(neg7), L(2), store=SP, count_2op=True) + print_num(V(SP)) + NEWLINE
        + vop(0x17, L(7), L(neg2), store=SP, count_2op=True) + print_num(V(SP)) + NEWLINE
        + vop(0x18, L(neg7), L(2), store=SP, count_2op=True) + print_num(V(SP)) + NEWLINE
        + vop(0x18, L(7), L(neg2), store=SP, count_2op=True) + print_num(V(SP))
        + QUIT
    )
    # Truncating pair: -7/2 = -3 rem -1; 7/-2 = -3 rem 1 (sign of dividend).
    assert out == "-3\n-3\n-1\n1"


def test_division_by_zero_is_a_named_fault():
    vm, io, _ = build(vop(0x17, L(1), L(0), store=SP, count_2op=True) + QUIT)
    with pytest.raises(VMError) as e:
        vm.run(max_steps=10)
    assert "division by zero" in str(e.value)


def test_bitwise_and_shifts():
    out = run(
        vop(0x09, L(0x0FF0), L(0x00FF), store=SP, count_2op=True)  # and
        + print_num(V(SP)) + NEWLINE
        + ext(0x02, L(0x8000), L(0xFFFF), store=SP)  # log_shift >> 1: zero-fill
        + print_num(V(SP)) + NEWLINE
        + ext(0x03, L(0x8000), L(0xFFFF), store=SP)  # art_shift >> 1: sign-extend
        + print_num(V(SP)) + NEWLINE
        + vop(0x18, L(1), store=SP)                  # VAR:24 not 1 -> 0xFFFE
        + print_num(V(SP))
        + QUIT
    )
    # and: 0x00F0 = 240. log 0x8000>>1 = 0x4000 = 16384.
    # art 0x8000>>1 = 0xC000 = -16384. not 1 = -2.
    assert out == "240\n16384\n-16384\n-2"


# -- branches and loops -----------------------------------------------------------

def test_je_multiway_and_signed_compares():
    # je 5,1,9,5: three-way equality, taken on the last; jl is signed, so
    # 0xFFFF (-1) < 1 must take the branch where an unsigned compare would not.
    out = run(
        vop(0x08, L(0xFFFF))                      # push -1 for the jl below
        + vop(0x01, S(5), S(1), S(9), S(5), count_2op=True)
        + branch(True, +6)                        # skip print_num(S)+quit: 3+1 bytes
        + print_num(S(0)) + QUIT                  # 4 bytes, skipped
        + long2(0x02, V(SP), S(1))                # jl -1 < 1
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + print_num(S(1)) + QUIT
    )
    assert out == "1"


def test_loop_with_inc_chk_and_jump():
    # G00 counts 1..5, printing each: inc_chk branches out once past 5, and
    # a backward jump re-runs the body. Byte math: inc_chk(3)+branch(2),
    # print_num(3)+new_line(1), jump(3). A jump lands at next+offset-2, so
    # jumping back over 12 bytes needs offset -10.
    code = (
        long2(0x05, S(16), S(5))                  # inc_chk G00 > 5 ?
        + branch(True, 2 + 4 + 3)                 # out: to just after the jump
        + print_num(V(16)) + NEWLINE
        + short1(0x0C, L((2 - 12) & 0xFFFF))      # jump back to the inc_chk
        + print_num(V(16))                        # the final value, 6
        + QUIT
    )
    out = run(code)
    assert out == "1\n2\n3\n4\n5\n6"


def test_dec_chk_test_and_jz():
    out = run(
        vop(0x08, L(2))                       # push 2
        + long2(0x04, S(0), S(2))             # dec_chk [sp] < 2: 1 < 2, taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + long2(0x07, S(0x0F), S(0x05))       # test 0b1111 has 0b0101: taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + short1(0x00, S(0))                  # jz 0: taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + print_num(V(SP))                    # the decremented top of stack
        + QUIT
    )
    assert out == "1"


# -- load, store, arrays, the stack ------------------------------------------------

def test_global_and_array_access():
    out = run(
        vop(0x0D, S(17), L(1234), count_2op=True)   # store G01, 1234
        + print_num(V(17)) + NEWLINE
        + vop(0x0F, L(GLOBALS), S(1), store=SP, count_2op=True)  # loadw globals[1]
        + print_num(V(SP)) + NEWLINE
        + vop(0x01, L(GLOBALS), S(3), L(0xBEEF))     # storew globals[3]
        + print_num(V(19))                           # read it back as G03
        + QUIT
    )
    assert out == "1234\n1234\n-16657"  # 0xBEEF signed


def test_byte_access_and_negative_index():
    out = run(
        vop(0x02, L(GLOBALS + 4), S(0), S(0xAB))            # storeb g+4[0]
        + vop(0x02, L(GLOBALS + 4), L(0xFFFF), S(0xCD))     # storeb g+4[-1]
        + vop(0x10, L(GLOBALS + 4), S(0), store=SP, count_2op=True)   # loadb
        + print_num(V(SP)) + NEWLINE
        + vop(0x10, L(GLOBALS + 4), L(0xFFFF), store=SP, count_2op=True)
        + print_num(V(SP))
        + QUIT
    )
    assert out == "171\n205"


def test_indirect_stack_semantics():
    # S 6.3.4: an indirect reference to variable 0 works on the TOP of the
    # stack in place. load must peek (not pop), store must replace (not push),
    # inc must bump in place, pull into a variable pops.
    out = run(
        vop(0x08, L(41))                      # push 41
        + short1(0x0E, S(0), store=17)        # load [sp] -> G01: peeks 41
        + short1(0x05, S(0))                  # inc [sp]: top becomes 42
        + vop(0x0D, S(0), L(100), count_2op=True)  # store [sp], 100: replaces
        + print_num(V(17)) + NEWLINE          # 41 (the peek survived the pop-less read)
        + print_num(V(SP))                    # pops: 100, stack now empty
        + QUIT
    )
    assert out == "41\n100"


def test_stack_underflow_is_a_named_fault():
    vm, io, _ = build(print_num(V(SP)) + QUIT)
    with pytest.raises(VMError) as e:
        vm.run(max_steps=10)
    assert "underflow" in str(e.value)


# -- calls and returns ---------------------------------------------------------------

def test_call_returns_and_argument_passing():
    # A routine with three locals adds its two arguments (the third local
    # stays 0 and is added too, proving locals default to 0).
    adder = routine(
        3,
        long2(0x14, V(1), V(2), store=SP),    # add L00 + L01
        long2(0x14, V(SP), V(3), store=SP),   # + L02 (defaults 0)
        short1(0x0B, V(SP)),                  # ret sp
    )
    _, _, packed = build(QUIT, adder)
    vm, io, packed = build(
        vop(0x00, L(packed[0]), S(7), S(5), store=SP)  # call_vs adder(7, 5)
        + print_num(V(SP))
        + QUIT,
        adder,
    )
    vm.run(max_steps=100)
    assert io.text == "12"


def test_call_vs2_seven_args_and_check_arg_count():
    # The callee sums locals 1..7 and reports whether argument 8 was given.
    summer = routine(
        8,
        long2(0x14, V(1), V(2), store=SP),
        long2(0x14, V(SP), V(3), store=SP),
        long2(0x14, V(SP), V(4), store=SP),
        long2(0x14, V(SP), V(5), store=SP),
        long2(0x14, V(SP), V(6), store=SP),
        long2(0x14, V(SP), V(7), store=SP),
        vop(0x1F, S(8)) + branch(True, +8),   # check_arg_count 8?
        short1(0x0B, V(SP)),                  # no 8th arg: ret the sum
        short0(0x08),                         # ret_popped (never reached here)
    )
    vm, io, packed = build(QUIT, summer)
    entry = (
        vop2(0x0C, L(packed[0]), S(1), S(2), S(3), S(4), S(5), S(6), S(7), store=SP)
        + print_num(V(SP))
        + QUIT
    )
    vm, io, packed = build(entry, summer)
    vm.run(max_steps=100)
    assert io.text == "28"


def test_call_address_zero_yields_false():
    out = run(
        vop(0x00, L(0), store=SP)   # call_vs 0
        + print_num(V(SP))
        + QUIT
    )
    assert out == "0"


def test_call_1n_and_frames_isolate_stacks():
    # The callee tries to pop the caller's stack: each frame owns its own,
    # so that is an underflow fault, not a theft (S 6.3.2).
    thief = routine(0, short1(0x0B, V(SP)))  # ret sp: pops its OWN empty stack
    vm, io, packed = build(QUIT, thief)
    entry = (
        vop(0x08, L(99))                 # caller pushes
        + short1(0x0F, L(packed[0]))     # call_1n thief
        + QUIT
    )
    vm, io, _ = build(entry, thief)
    with pytest.raises(VMError) as e:
        vm.run(max_steps=100)
    assert "underflow" in str(e.value)


def test_catch_and_throw_unwind():
    # entry calls A; A catches, calls B(catch); B calls C(catch); C throws 42
    # to the caught frame: A returns 42 at once, B and C evaporate, neither
    # of the sentinel prints ever runs. Routine sizes do not depend on the
    # addresses, so build once with placeholders to learn the layout, then
    # for real.
    def make(pB=0, pC=0):
        C = routine(1, vop(0x1C, L(42), V(1), count_2op=True))   # throw 42, L00
        B = routine(1, vop(0x19, L(pC), V(1)) + print_num(S(0)) + RTRUE)
        A = routine(
            1,
            short0(0x09) + bytes([1])         # catch -> L00
            + vop(0x19, L(pB), V(1))          # call_vn B(L00)
            + print_num(S(0)) + RTRUE,
        )
        return C, B, A

    C, B, A = make()
    _, _, p = build(QUIT, C, B, A)
    C, B, A = make(pB=p[1], pC=p[0])
    entry = vop(0x00, L(p[2]), store=SP) + print_num(V(SP)) + QUIT
    vm, io, _ = build(entry, C, B, A)
    vm.run(max_steps=200)
    assert io.text == "42"


# -- the rest -------------------------------------------------------------------------

def test_random_seeded_is_reproducible():
    seedneg = 0x10000 - 7
    code = (
        vop(0x07, L(seedneg), store=SP) + print_num(V(SP)) + NEWLINE  # seed: 0
        + vop(0x07, S(100), store=SP) + print_num(V(SP)) + NEWLINE
        + vop(0x07, S(100), store=SP) + print_num(V(SP))
        + QUIT
    )
    a, b = run(code), run(code)
    assert a == b
    lines = a.split("\n")
    assert lines[0] == "0"
    assert all(1 <= int(x) <= 100 for x in lines[1:])


def test_verify_and_piracy_branch():
    out = run(
        short0(0x0D)                     # verify: checksum is honest, taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + short0(0x0F)                   # piracy: gullible, taken
        + branch(True, +6)
        + print_num(S(0)) + QUIT
        + print_num(S(1)) + QUIT
    )
    assert out == "1"


def test_branch_offsets_zero_and_one_return():
    # A routine whose branch offset 1 means "return true from here".
    r = routine(
        0,
        short1(0x00, S(0))               # jz 0: always true
        + bytes([0x80 | 0x40 | 1])       # short branch, on true, offset 1: rtrue
        + RFALSE,
    )
    vm, io, packed = build(QUIT, r)
    entry = vop(0x00, L(packed[0]), store=SP) + print_num(V(SP)) + QUIT
    vm, io, _ = build(entry, r)
    vm.run(max_steps=50)
    assert io.text == "1"


def test_print_char_and_unimplemented_are_loud():
    out = run(
        vop(0x05, S(72)) + vop(0x05, S(105)) + vop(0x05, S(13))  # H i newline
        + QUIT
    )
    assert out == "Hi\n"
    # print (inline text) is real but belongs to M5: loud, with the milestone.
    vm, io, _ = build(bytes([0xB2, 0x91, 0x11]) + QUIT)
    with pytest.raises(UnimplementedOpcode) as e:
        vm.run(max_steps=10)
    assert "M5" in str(e.value)


def test_quit_halts():
    vm, io, _ = build(QUIT + print_num(S(9)))
    vm.run(max_steps=10)
    assert vm.halted and io.text == ""


def test_recursion_factorial():
    # F(n): n == 0 -> 1, else n * F(n - 1). Eight frames deep at the peak;
    # the branch's offset-1 encoding doubles as the base case's return true.
    def make(pF=0):
        return routine(
            1,
            short1(0x00, V(1))                    # jz L00 ?rtrue (returns 1)
            + bytes([0x80 | 0x40 | 1])
            + long2(0x15, V(1), S(1), store=SP)   # sub n, 1 -> sp
            + vop(0x00, L(pF), V(SP), store=SP)   # call_vs F(sp) -> sp
            + long2(0x16, V(1), V(SP), store=SP)  # mul n * F(n-1) -> sp
            + short1(0x0B, V(SP)),                # ret sp
        )

    _, _, p = build(QUIT, make())
    F = make(pF=p[0])
    entry = vop(0x00, L(p[0]), S(7), store=SP) + print_num(V(SP)) + QUIT
    vm, io, _ = build(entry, F)
    vm.run(max_steps=1000)
    assert io.text == "5040"
