# test_standalone.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Guards the standalone single-file build: tools/amalgamate.py must produce an
`arcc` script that runs on a bare interpreter, with no package on sys.path, and
parses the example games. This keeps the distributable artifact from drifting
away from the package source."""

import os
import re
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


def test_standalone_version_names_the_build(tmp_path):
    # --version carries a baked content fingerprint, so two amalgams at the
    # same __version__ but different source are told apart (the tester-
    # confusion fix). The standalone shows a 7-hex id, never "source".
    arcc = tmp_path / "arcc"
    _amalgamate(str(arcc))
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    out = subprocess.run(
        [sys.executable, str(arcc), "--version"],
        cwd=str(tmp_path), env=env, capture_output=True, text=True,
    ).stdout
    m = re.search(r"\(build ([0-9a-f]{7})\)", out)
    assert m, out
    assert m.group(1) != "source"
    # The block is the verbose one: the tagline and the embedded library
    # version are both present.
    assert "compiler for the Infocom Z-machine" in out
    assert "Cosmos standard library" in out


def test_standalone_build_id_is_deterministic_and_content_bound(tmp_path):
    # Same source, same id (a rebuild is reproducible). A changed source byte
    # changes the id: the fingerprint tracks content, not the version string.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import amalgamate
    finally:
        sys.path.pop(0)
    pkg = os.path.join(ROOT, "arcturus")
    init = amalgamate._read(pkg, "__init__")
    mods = {n: amalgamate._read(pkg, n) for n in amalgamate._MODULE_ORDER}
    cos = {"x.prelude": "// stub\n"}
    a = amalgamate._fingerprint(init, mods, cos)
    b = amalgamate._fingerprint(init, mods, cos)
    assert a == b and re.fullmatch(r"[0-9a-f]{7}", a)
    tweaked = dict(mods)
    first = amalgamate._MODULE_ORDER[0]
    tweaked[first] = mods[first] + "\n# a change\n"
    assert amalgamate._fingerprint(init, tweaked, cos) != a
