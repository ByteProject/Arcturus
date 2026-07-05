# test_terpetude.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M11: TerpEtude's text portions, headless (docs/06 section 11;
the styled/coloured/timed sections need a screen and eyes, and are the GUI
half of the milestone). Like CZECH and Praxix, the story file is
third-party and local-only, so these skip where it is absent."""

import os

import pytest

from actaea.io import CaptureIO
from actaea.loader import load_file
from actaea.vm import VM

ETUDE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "actaea", "conformance",
    "etude.z5",
)

pytestmark = pytest.mark.skipif(
    not os.path.exists(ETUDE),
    reason="conformance stories not present (kept out of the public repo)",
)


def _run(script):
    vm = VM(load_file(ETUDE), CaptureIO(script=list(script)))
    try:
        vm.run(max_steps=10_000_000)
    except IndexError:
        pass  # script exhausted mid-menu: everything printed so far counts
    return vm.io.text, vm.halted


def test_header_flags_analysis():
    out, _ = _run(["3", "."])
    assert "revision 1.1 of the Z-Spec" in out
    assert "colored text IS available" in out
    assert "emphasized (bold) text IS available" in out
    assert "italic (or underlined) text IS available" in out
    assert "fixed-width text IS available" in out
    assert "sound effects ARE NOT available" in out
    assert '"undo" IS available' in out
    # Headless there is no event loop, so the claim is honestly OFF; the
    # GUI front-end claims it (io.supports_timed) and runs the timers.
    assert "timed input IS NOT available" in out


def test_signed_multiplication_division_modulo():
    out, _ = _run(["6", "."])
    assert out.count("(ok)") == 12
    assert "(WRONG" not in out
    assert "appears to behave according to spec" in out


def test_multiple_undo():
    out, _ = _run(["13", "u", "u", ".", "."])
    assert "Undo succeeded (undid second move)." in out
    assert "Undo succeeded (undid first move)." in out
    assert "it supports multiple \"undo\"" in out


def test_preloaded_input_line():
    # The word Given appears ONCE (printed by the game, absorbed by the
    # read) and the typed text continues it, lower-cased by the machine.
    out, _ = _run(["12", "hello", "", "."])
    assert 'You just typed "givenhello".' in out


def test_line_input_character_codes():
    out, _ = _run(["9", "Hello!", "", "."])
    # The machine lower-cases the stored line (S 15 read).
    assert "code=104: ASCII character 'h'" in out
    assert "code=33: ASCII character '!'" in out
    assert "code=72" not in out  # no upper-case H survived


def test_closing_text_before_quit():
    out, halted = _run(["14", "y"])
    assert halted
    assert "This is a final line of text. Goodbye." in out
