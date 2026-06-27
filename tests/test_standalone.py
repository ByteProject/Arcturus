# test_standalone.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Guards the standalone single-file build: tools/amalgamate.py must produce an
`arcc` script that runs on a bare interpreter, with no package on sys.path, and
parses the example games. This keeps the distributable artifact from drifting
away from the package source."""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _amalgamate(dest):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import amalgamate
    finally:
        sys.path.pop(0)
    amalgamate.build(dest)


def test_standalone_runs_without_package(tmp_path):
    arcc = tmp_path / "arcc"
    _amalgamate(str(arcc))
    assert arcc.exists()

    example = os.path.join(ROOT, "examples", "brass-lantern.storyarc")
    # Run from a directory with no access to the arcturus package, and scrub
    # PYTHONPATH, so success proves the script is self-contained.
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(arcc), example],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "checked cleanly" in result.stdout
