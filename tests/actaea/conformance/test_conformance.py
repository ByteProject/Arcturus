# test_conformance.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M6, the conformance gate: CZECH and Praxix, headless, matched
against their references. These are the community's opcode checkers; docs/06
calls this the correctness milestone the whole build hangs on.

The story files are third-party works and stay out of the public repository
(actaea/conformance/ is local; *.z5 is gitignored), so these tests skip
where the files are absent and run everywhere Stefan runs them."""

import os

import pytest

from actaea.io import CaptureIO
from actaea.loader import load_file
from actaea.vm import VM

CONFORMANCE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "actaea", "conformance"
)


def _run(name: str, script=()) -> str:
    vm = VM(load_file(os.path.join(CONFORMANCE, name)), CaptureIO(script=list(script)))
    vm.run(max_steps=50_000_000)
    assert vm.halted
    return vm.io.text


def _without_header_block(text: str) -> str:
    """CZECH's header dump is explicitly '(No tests)': it reports the
    interpreter-set identity fields, which legitimately differ between
    interpreters (ours declares Standard 1.1 and a real screen where the
    reference terp declared none). Strip that block; everything else must
    match the reference byte for byte."""
    lines = text.splitlines()
    out = []
    skipping = False
    for line in lines:
        if line.startswith("Header (No tests)"):
            skipping = True
            continue
        if skipping:
            if line.strip() == "":
                skipping = False
            continue
        out.append(line)
    return "\n".join(out)


@pytest.mark.skipif(
    not os.path.exists(os.path.join(CONFORMANCE, "czech.z5")),
    reason="conformance stories not present (kept out of the public repo)",
)
def test_czech_matches_the_reference_transcript():
    out = _run("czech.z5")
    assert "Passed: 406, Failed: 0" in out
    ref = open(os.path.join(CONFORMANCE, "czech-reference.txt")).read()
    assert _without_header_block(out) == _without_header_block(ref)


@pytest.mark.skipif(
    not os.path.exists(os.path.join(CONFORMANCE, "praxix.z5")),
    reason="conformance stories not present (kept out of the public repo)",
)
def test_praxix_all_tests_pass():
    out = _run("praxix.z5", script=["all", "quit"])
    assert "All tests passed." in out
    assert "FAILED" not in out
    # Praxix prints a per-group verdict; count them so a silently skipped
    # group cannot masquerade as a pass.
    assert out.count("Passed.") >= 15
