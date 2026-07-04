# test_quetzal.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M10: Quetzal saved games. The pure coding layer byte by byte
(CMem run-length XOR, the IFF container, story identification), then the
three opcodes driven through zasm programs: save stores 1, restore resumes
inside that save with 2 and the saved world, restart rewinds to the
pristine image except the two Flags 2 session bits. The other half of the
milestone, interoperating with a reference interpreter, lives in
tests/actaea/test_interop.py."""

import pytest

from actaea.quetzal import QuetzalError, compress, decompress, read, write
from actaea.vm import VM, Frame
from zasm import (
    NEWLINE, QUIT, S, SP, V, branch, build, ext, long2, print_num, short0,
    short1, vop,
)


# -- CMem coding --------------------------------------------------------------

def test_cmem_identical_memory_codes_to_nothing():
    image = bytes(range(256)) * 4
    assert compress(image, image) == b""
    assert decompress(b"", image, len(image)) == image


def test_cmem_round_trips_changes_and_long_runs():
    initial = bytes(1000)
    changed = bytearray(initial)
    changed[0] = 7          # a change at the very start
    changed[500] = 200      # one in the middle, after a run longer than 256
    changed[999] = 1        # and at the last byte, so nothing is dropped
    data = compress(bytes(changed), initial)
    assert decompress(data, initial, 1000) == bytes(changed)
    # The coding is compact: three changed bytes cost a handful of run
    # markers, not a kilobyte.
    assert len(data) < 20


def test_cmem_trailing_zeros_are_dropped():
    initial = bytes(1000)
    changed = bytearray(initial)
    changed[3] = 9
    data = compress(bytes(changed), initial)
    # Everything after the last change is omitted entirely.
    assert data == bytes((0, 2, 9))


def test_cmem_overrun_is_a_named_error():
    with pytest.raises(QuetzalError) as e:
        decompress(bytes(10), bytes(4), 4)
    assert "does not fit" in str(e.value)


# -- the container ------------------------------------------------------------

def _machine():
    """A tiny real story with a mutated world and a deep-ish stack, the
    state write() serializes."""
    vm, io, _ = build(QUIT)
    vm.mem.set_word(0x10 + 0x30, 0xBEEF)  # scribble in dynamic memory
    vm.frames[0].stack.append(11)
    inner = Frame(return_pc=0x1234, store=5, locals_=[1, 2, 0xFFFF], argc=2)
    inner.stack = [7, 8]
    vm.frames.append(inner)
    discard = Frame(return_pc=0x2345, store=None, locals_=[], argc=0)
    vm.frames.append(discard)
    return vm


def test_write_read_round_trip():
    vm = _machine()
    data = write(vm.mem, vm.frames, 0x0777)
    dyn, frames, pc = read(data, vm.mem)
    assert pc == 0x0777
    assert dyn == bytes(vm.mem.mem[:vm.mem.static_base])
    assert frames[0] == (0, None, [], 0, [11])          # the dummy frame
    assert frames[1] == (0x1234, 5, [1, 2, 0xFFFF], 2, [7, 8])
    assert frames[2] == (0x2345, None, [], 0, [])       # discarded store
    assert data[:4] == b"FORM" and data[8:12] == b"IFZS"


def test_a_different_story_is_refused():
    vm = _machine()
    data = write(vm.mem, vm.frames, 0x0777)
    other, _, _ = build(NEWLINE + QUIT)  # differs in code, hence checksum
    with pytest.raises(QuetzalError) as e:
        read(data, other.mem)
    assert "different story" in str(e.value)


def test_umem_is_read_too():
    # Rebuild the round-trip save with its CMem swapped for a raw UMem, the
    # uncompressed form other interpreters may write.
    vm = _machine()
    dyn = bytes(vm.mem.mem[:vm.mem.static_base])
    cmem_form = write(vm.mem, vm.frames, 0x0777)
    # Strip the FORM header, keep IFhd and Stks, replace CMem.
    ifhd = cmem_form[12:12 + 8 + 13 + 1]  # chunk head + 13 bytes + pad
    stks_at = cmem_form.find(b"Stks")
    stks = cmem_form[stks_at:]
    umem = b"UMem" + len(dyn).to_bytes(4, "big") + dyn \
        + (b"\x00" if len(dyn) & 1 else b"")
    body = b"IFZS" + ifhd + umem + stks
    data = b"FORM" + len(body).to_bytes(4, "big") + body
    got_dyn, frames, pc = read(data, vm.mem)
    assert got_dyn == dyn and pc == 0x0777 and len(frames) == 3


def test_garbage_is_not_a_save():
    vm = _machine()
    with pytest.raises(QuetzalError):
        read(b"this is not an IFF file at all", vm.mem)


# -- the opcodes --------------------------------------------------------------

G0, G1 = 16, 17  # global variables 0 and 1 as variable numbers


def test_save_restore_resume_with_result_2(tmp_path):
    # save -> G1 prints 1; the world changes (G0 = 42); restore never
    # returns on success but resumes INSIDE the save, which now yields 2,
    # with the world as it was saved (G0 back to 0).
    entry = (
        ext(0x00, store=G1)                    # save -> G1
        + print_num(V(G1)) + NEWLINE
        + long2(0x01, V(G1), S(2))             # je G1, 2 ?done
        + branch(True, 17)
        + long2(0x0D, S(G0), S(42))            # store G0 = 42        (3)
        + print_num(V(G0)) + NEWLINE           #                      (4)
        + ext(0x01, store=SP)                  # restore              (4)
        + print_num(V(SP)) + QUIT              # only on failure      (4)
        # done:
        + print_num(V(G0))                     # restored: 0
        + QUIT
    )
    vm, io, _ = build(entry)
    io.save_dir = str(tmp_path)
    io.script = ["state.qzl", "state.qzl"]
    vm.run(max_steps=10000)
    assert vm.halted
    # Filenames echo into the transcript between the numbers.
    assert io.text == "state.qzl\n1\n42\nstate.qzl\n2\n0"
    assert (tmp_path / "state.qzl").exists()


def test_restore_of_a_missing_file_reports_failure(tmp_path):
    entry = (
        ext(0x01, store=SP)                    # restore a file that is not there
        + print_num(V(SP))
        + QUIT
    )
    vm, io, _ = build(entry)
    io.save_dir = str(tmp_path)
    io.script = ["missing.qzl"]
    vm.run(max_steps=1000)
    assert io.text.endswith("0")


def test_restart_rewinds_except_the_session_bits():
    # First run: set the transcription bit (Flags 2 bit 0, the one bit a
    # game legitimately owns across restarts), set G0 = 5, restart. Second
    # run: the bit says we have been here, G0 is pristine again.
    entry = (
        long2(0x10, S(0), S(0x11), store=SP)   # loadb 0x11 (Flags 2 low byte)
        + short1(0x00, V(SP))                  # jz ?first-run (fall through)
        + branch(False, 15)                    # nonzero: to done
        + long2(0x0D, S(G0), S(5))             # store G0 = 5         (3)
        + print_num(V(G0)) + NEWLINE           # "5"                  (4)
        + vop(0x02, S(0), S(0x11), S(1))       # storeb: transcription (5)
        + short0(0x07)                         # restart              (1)
        # done:
        + print_num(V(G0)) + NEWLINE           # pristine again: "0"
        + long2(0x10, S(0), S(0x11), store=SP)
        + print_num(V(SP))                     # the surviving bit: "1"
        + QUIT
    )
    vm, io, _ = build(entry)
    vm.run(max_steps=10000)
    assert io.text == "5\n0\n1"


def test_restart_resets_the_screen_and_streams():
    vm, io, _ = build(QUIT)
    vm.screen.split(3)
    vm.screen.set_style(2)
    vm.stream3.append((0x100, []))
    vm.font = 4
    vm._op_restart(None)
    assert vm.screen.rows == 0        # the split is gone
    assert vm.screen.style == 0
    assert vm.stream3 == [] and vm.font == 1
    assert vm.pc == vm.story.header.initial_pc
    assert len(vm.frames) == 1 and vm.frames[0].stack == []
