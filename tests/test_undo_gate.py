# test_undo_gate.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The undo handshake (the Canopus and Haumea field reports, 2026-08-01).

The Standard gives an interpreter two ways to say "I cannot undo": clear
Flags 2 bit 4 (S 11.1, the static veto), or answer -1 from save_undo
(S 15, the opcode's own report). Cosmos used to ignore both, offer UNDO
at the death prompt, and translate the failed restore into "There's
nothing to take back.", a false sentence on any 8-bit machine without
the memory for snapshots. Now both channels latch undo_off: the UNDO
verb and the death prompt answer with the truth and never attempt a
restore into the void, while capable interpreters play exactly as
before.
"""

import os
import subprocess
import sys

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = """
game
    title "Undogate"
    author "pytest"
    start cell

room cell
    name "Padded Cell"
    desc "Soft walls. A single red button juts from the floor."

thing button in cell
    name "red button"
    words red, button
    fixed
    on push
        death "*** You have pushed the wrong button ***"
"""


def _compile(tmp_path):
    src = tmp_path / "undogate.storyarc"
    src.write_text(GAME)
    story = tmp_path / "undogate.z5"
    subprocess.run(
        [sys.executable, "-m", "arcturus.cli", str(src), "-o", str(story)],
        capture_output=True, text=True, check=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    return story.read_bytes()


def _play(data, script, patch_save_undo=None):
    io = CaptureIO(script=list(script))
    vm = VM(load(data), io)
    if patch_save_undo is not None:
        # The dispatch table maps names to functions at class level, so an
        # instance copy carries the stub without leaking across tests.
        vm._ops = dict(vm._ops)
        vm._ops["save_undo"] = (
            lambda self, ins: self._write_var(ins.store, patch_save_undo))
    try:
        vm.run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted
    return "".join(io.output)


def test_capable_interpreter_unchanged(tmp_path):
    data = _compile(tmp_path)
    out = _play(data, ["undo", "look", "undo", "push button", "undo"])
    # Empty history on a capable terp keeps the honest old line.
    assert "There's nothing to take back." in out
    # A real move undoes.
    assert "Taken back." in out
    # The death prompt offers UNDO and it works: after the fatal push the
    # prompt names UNDO, the last scripted undo takes the push back.
    assert "UNDO the last command" in out
    assert "This interpreter can't take commands back." not in out


def test_header_veto_gates_everything(tmp_path):
    data = bytearray(_compile(tmp_path))
    data[0x11] &= ~0x10  # the interpreter's veto: Flags 2 bit 4 cleared
    out = _play(bytes(data), ["undo", "look", "undo", "push button", "undo", "quit", "y"])
    # The verb answers the truth, both before and after a real move.
    assert out.count("This interpreter can't take commands back.") >= 3
    assert "There's nothing to take back." not in out
    # The death prompt never offers what the machine declined.
    assert "UNDO the last command" not in out
    assert "RESTART" in out


def test_save_undo_minus_one_latches(tmp_path):
    data = _compile(tmp_path)
    out = _play(data, ["look", "undo", "push button", "undo"],
                patch_save_undo=0xFFFF)
    # After the first checkpoint answered -1, the verb and the death
    # prompt both speak the unavailable truth.
    assert "This interpreter can't take commands back." in out
    assert "UNDO the last command" not in out
    assert "There's nothing to take back." not in out
