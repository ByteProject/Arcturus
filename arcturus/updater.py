# updater.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arcc --update: refresh the standalone builds in place.

The standalones ship as single files (build/arcc, build/actaea,
build/arcimg), and an author who is not tracking the repository has no
BuildTools updater to lean on; this is theirs. `arcc --update` replaces
the running arcc with the latest published build, and refreshes actaea
and arcimg when they sit in the same directory.

The rules:

- EXPLICIT ONLY. arcc never touches the network except on this command;
  there is no version phone-home, no passive check, nothing.
- Amalgam only. Running from the repository package, the answer is
  `git pull` and the command says so.
- Validated before it lands: a download must look like a standalone
  (shebang, plausible size), parse as Python, and carry a version
  string; only then does it atomically replace the file, mode preserved.
"""

from __future__ import annotations

import os
import re
import sys
import urllib.request

RAW_BASE = "https://raw.githubusercontent.com/ByteProject/Arcturus/main/build/"
SIBLINGS = ("actaea", "arcimg")

# The version constant every standalone carries in its embedded source, the
# Cosmos version arcc embeds (a real update may be Cosmos-only: same arcc
# version, new library, different bytes), and the build fingerprint that
# tells two builds at the same version apart.
_VERSION_RE = re.compile(r'__version__\s*=\s*(?:\\)?["\']([0-9][0-9.]*)(?:\\)?["\']')
_COSMOS_RE = re.compile(r'COSMOS_VERSION\s*=\s*(?:\\)?["\']([0-9][0-9.]*)(?:\\)?["\']')
_BUILD_RE = re.compile(r"_BUILD_ID\s*=\s*['\"]([0-9a-f]+)['\"]")


def _fetch(name: str) -> bytes:
    with urllib.request.urlopen(RAW_BASE + name, timeout=30) as r:
        return r.read()


def _version_in(source: str) -> str:
    m = _VERSION_RE.search(source)
    return m.group(1) if m else "unknown"


def _describe(name: str, source: str) -> str:
    """One binary's identity: version, the embedded Cosmos (arcc only), and
    the exact build, so a Cosmos-only or rebuild-only refresh reads as the
    real change it is rather than a puzzling v0.11.22 -> v0.11.22."""
    parts = []
    if name == "arcc":
        m = _COSMOS_RE.search(source)
        if m:
            parts.append("Cosmos " + m.group(1))
    b = _BUILD_RE.search(source)
    if b:
        parts.append("build " + b.group(1))
    tail = f" ({', '.join(parts)})" if parts else ""
    return f"v{_version_in(source)}{tail}"


def _print_header() -> None:
    import arcturus
    build = getattr(arcturus, "__build__", None) or "source"
    print(f"Arcturus {arcturus.__version__}  (build {build}) "
          "-- UPDATING SCRIPTS")
    print("Programming language and compiler for the Infocom Z-machine")
    print("Copyright (c) 2026, Stefan Vogt "
          "| https://github.com/ByteProject/Arcturus")
    print()


def _validate(name: str, data: bytes) -> str:
    """A downloaded standalone must be plausible before it replaces
    anything: returns the error, or an empty string when it passes."""
    if len(data) < 50_000:
        return f"{name}: implausibly small download ({len(data)} bytes)"
    if not data.startswith(b"#!/usr/bin/env python3"):
        return f"{name}: does not look like a standalone build"
    try:
        text = data.decode("utf-8")
        compile(text, name, "exec")
    except (UnicodeDecodeError, SyntaxError) as exc:
        return f"{name}: downloaded file does not parse ({exc})"
    return ""


def _replace(path: str, data: bytes) -> None:
    """Atomic in-place replacement, mode preserved (works on the running
    script: the inode swaps, the running process keeps its old image)."""
    mode = os.stat(path).st_mode
    tmp = path + ".new"
    with open(tmp, "wb") as f:
        f.write(data)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def run_update(fetch=_fetch) -> int:
    """The --update command. Returns the exit code."""
    import arcturus
    _print_header()
    if getattr(arcturus, "__build__", None) is None:
        print("arcc: --update refreshes the standalone build; you are "
              "running from the repository package. Use `git pull` and "
              "`python3 tools/amalgamate.py` instead.", file=sys.stderr)
        print()
        return 2

    me = os.path.realpath(sys.argv[0])
    home = os.path.dirname(me)
    targets = [("arcc", me)]
    for sib in SIBLINGS:
        p = os.path.join(home, sib)
        if os.path.isfile(p):
            targets.append((sib, p))

    failures = 0
    for name, path in targets:
        try:
            with open(path, "rb") as f:
                current = f.read()
        except OSError as exc:
            print(f"arcc: cannot read {path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        try:
            data = fetch(name)
        except Exception as exc:
            print(f"arcc: fetching {name} failed: {exc}", file=sys.stderr)
            failures += 1
            continue
        err = _validate(name, data)
        if err:
            print(f"arcc: {err}; keeping the current {name}",
                  file=sys.stderr)
            failures += 1
            continue
        old = _describe(name, current.decode("utf-8", "replace"))
        if data == current:
            print(f"{name}: already current, {old}")
            continue
        new = _describe(name, data.decode("utf-8"))
        try:
            _replace(path, data)
        except OSError as exc:
            print(f"arcc: cannot replace {path}: {exc} (permissions?)",
                  file=sys.stderr)
            failures += 1
            continue
        print(f"{name}: updated  {old} -> {new}")
    # One blank line after the output, the house rule for every tool.
    print()
    return 1 if failures else 0
