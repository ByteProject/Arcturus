# test_input.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M11: the input machinery beyond a plain line. Preloaded input
(S 15 read, byte 1), the terminating-characters table (S 10.7), timed-input
interrupts (S 8.4.2) through a scripted stand-in for the GUI's timer loop,
and stream 2 as a real transcript file synced with Flags 2 bit 0."""

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM
from zasm import (
    NEWLINE, QUIT, RFALSE, L, S, SP, V, branch, build, long2, print_num,
    routine, short1, vop,
)

BUF = 0x400  # free dynamic scratch between the object area and the code


class TimedIO(CaptureIO):
    """The GUI's after()-loop, scripted: each read fires on_timeout up to
    five times; if the interrupt asks to end the input, the read aborts the
    way a real timer would (empty line / key 0)."""

    def read_line(self, max_len, preload="", terminators=frozenset(),
                  timeout=0.0, on_timeout=None):
        if timeout and on_timeout:
            for _ in range(5):
                if on_timeout():
                    return "", 0
        return super().read_line(max_len, preload)

    def read_char(self, timeout=0.0, on_timeout=None):
        if timeout and on_timeout:
            for _ in range(5):
                if on_timeout():
                    return 0
        return super().read_char()


def _buffer_setup(maxlen=40):
    return vop(0x02, L(BUF), S(0), S(maxlen))  # storeb BUF[0] = max letters


def _aread(*extra, store=SP):
    return vop(0x04, L(BUF), S(0), *extra, store=store)  # parse buffer 0


# The counting interrupt: increments G00, prints "T", returns true (end
# the input) once G00 passes 1, so it runs exactly twice per read.
def _interrupt_routine():
    return routine(
        0,
        short1(0x05, S(16))          # inc G00
        + vop(0x05, S(84))           # print_char 'T'
        + long2(0x03, V(16), S(1))   # jg G00, 1
        + branch(True, 1)            # ...past 1: return true
        + RFALSE,
    )


def test_preloaded_input_survives_into_the_line():
    # The game leaves "cat" in the buffer (as if a read was interrupted);
    # the player "types" s. The line is cats: length 4 in byte 1, and the
    # front-end echoed only what was typed.
    entry = (
        _buffer_setup()
        + vop(0x02, L(BUF), S(1), S(3))       # byte 1: three chars preloaded
        + vop(0x02, L(BUF), S(2), S(99))      # c
        + vop(0x02, L(BUF), S(3), S(97))      # a
        + vop(0x02, L(BUF), S(4), S(116))     # t
        + _aread(store=SP)
        + print_num(V(SP)) + NEWLINE          # terminator: 13
        + vop(0x10, L(BUF), S(1), store=SP, count_2op=True)  # loadb the stored length
        + print_num(V(SP))
        + QUIT
    )
    vm, io, _ = build(entry)
    io.script = ["s"]
    vm.run(max_steps=10000)
    assert io.text == "s\n13\n4"
    # The whole line, preload first, landed in the buffer.
    assert bytes(vm.mem.mem[BUF + 2:BUF + 6]) == b"cats"


def _build_timed(make_entry):
    """Two-pass build: the routine's packed address depends only on the
    entry's SIZE, which a placeholder LARGE(0) shares with the real
    operand, so the first build measures and the second is correct. The io
    is swapped for the timer-scripted one (screen sink included: the model
    passes lower-window text through to whatever the sink is)."""
    r = _interrupt_routine()
    _, _, packed = build(make_entry(0), r)
    vm, _, _ = build(make_entry(packed[0]), r)
    vm.io = vm.screen.sink = io = TimedIO()
    return vm, io


def test_timed_read_char_interrupts_then_aborts():
    vm, io = _build_timed(lambda p: (
        vop(0x16, S(1), S(10), L(p), store=SP)
        + print_num(V(SP))
        + QUIT
    ))
    vm.run(max_steps=10000)
    # Two ticks printed by the interrupt, then it ended the read: key 0.
    assert io.text == "TT0"


def test_timed_read_line_aborts_with_terminator_zero():
    vm, io = _build_timed(lambda p: (
        _buffer_setup()
        + _aread(S(10), L(p), store=SP)
        + print_num(V(SP)) + NEWLINE     # terminator: 0
        + vop(0x10, L(BUF), S(1), store=SP, count_2op=True)
        + print_num(V(SP))               # nothing was committed to the buffer
        + QUIT
    ))
    vm.run(max_steps=10000)
    assert io.text == "TT0\n0"


def test_transcript_via_output_stream(tmp_path):
    entry = (
        _buffer_setup()
        + vop(0x13, S(2))                # output_stream 2: transcript on
        + vop(0x05, S(72)) + vop(0x05, S(105))  # print Hi
        + _aread(store=SP)               # the player's line is transcribed
        + vop(0x13, L(0xFFFE))           # output_stream -2: off
        + vop(0x05, S(88))               # X, after the transcript closed
        + QUIT
    )
    vm, io, _ = build(entry)
    io.script = ["hello"]
    io.save_dir = str(tmp_path)
    vm.run(max_steps=10000)
    # The transcript holds the story text and the player's line; the X was
    # printed after the stream closed and reached the screen only.
    assert (tmp_path / "transcript.txt").read_text() == "Hihello\n"
    assert io.text == "Hihello\nX"


def test_transcript_via_the_flags2_bit(tmp_path):
    # The game flips Flags 2 bit 0 directly (S 7.3/7.4); the interpreter
    # notices at the next input, the turn boundary.
    entry = (
        _buffer_setup()
        + vop(0x02, S(0), S(0x11), S(1))  # storeb: transcription bit on
        + _aread(store=SP)
        + QUIT
    )
    vm, io, _ = build(entry)
    io.script = ["north"]
    io.save_dir = str(tmp_path)
    vm.run(max_steps=10000)
    assert (tmp_path / "transcript.txt").read_text() == "north\n"
    assert vm.transcript_on


def test_terminating_characters_table_is_read():
    vm, _, _ = build(QUIT)
    raw = bytearray(vm.mem.initial)
    raw[0x2E:0x30] = (0x400).to_bytes(2, "big")
    raw[0x400:0x404] = bytes((130, 132, 254, 0))
    vm2 = VM(load(bytes(raw)), CaptureIO())
    assert vm2.terminators == frozenset({130, 132, 254})
    # And absent, the set is empty: Enter alone ends a read.
    assert vm.terminators == frozenset()
