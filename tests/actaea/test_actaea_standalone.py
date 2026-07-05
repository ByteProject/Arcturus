# test_standalone.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Guards the standalone single-file build: tools/amalgamate_actaea.py must
produce an `actaea` script that runs on a bare interpreter, with no package
on sys.path, and plays a story headless. The story is an Arcturus example
compiled on the spot, so the whole toolchain meets itself in one test."""

import os
import subprocess
import sys

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def _amalgamate(dest):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import amalgamate_actaea
    finally:
        sys.path.pop(0)
    amalgamate_actaea.build(dest)


def test_standalone_plays_without_package(tmp_path):
    actaea = tmp_path / "actaea"
    _amalgamate(str(actaea))
    assert actaea.exists()

    src = open(os.path.join(ROOT, "examples", "cloak-of-darkness.storyarc")).read()
    story = tmp_path / "cloak.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(src)))))

    # Run from a directory with no access to the actaea package, and scrub
    # PYTHONPATH, so success proves the script is self-contained.
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(actaea), "--headless", str(story)],
        cwd=str(tmp_path), env=env,
        input="look\nquit\ny\n",
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "Opera House" in result.stdout

    version = subprocess.run(
        [sys.executable, str(actaea), "--version"],
        cwd=str(tmp_path), env=env, capture_output=True, text=True, timeout=30,
    )
    assert "Z-machine v5/8 interpreter" in version.stdout
    assert "Standard 1.1 conformant" in version.stdout
