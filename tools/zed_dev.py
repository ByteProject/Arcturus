#!/usr/bin/env python3
# zed_dev.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Assemble an installable DEV bundle of the Zed extension under build/.

Zed loads a grammar from a git repository (a URL plus a commit), even for a
local dev extension, so this tool copies the grammar into an untracked git
repository under build/, commits it, and writes a dev copy of the extension
with the grammar reference pointing there. The tracked sources under
editors/zed and editors/tree-sitter-arcturus stay clean.

Usage:
    python3 tools/zed_dev.py

Then, in Zed: open the command palette, run "zed: install dev extension",
and select build/zed-dev. Re-run this tool and use "zed: rebuild dev
extension" (or reinstall) after changing the grammar or the queries.
"""

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXT_SRC = ROOT / "editors" / "zed"
GRAMMAR_SRC = ROOT / "editors" / "tree-sitter-arcturus"
BUNDLE = ROOT / "build" / "zed-dev"
GRAMMAR_REPO = ROOT / "build" / "zed-dev-grammar"


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def main() -> int:
    for path in (BUNDLE, GRAMMAR_REPO):
        if path.exists():
            shutil.rmtree(path)

    # The grammar as a throwaway git repository: Zed clones it by rev.
    shutil.copytree(GRAMMAR_SRC, GRAMMAR_REPO)
    run(["git", "init", "-q"], GRAMMAR_REPO)
    run(["git", "add", "-A"], GRAMMAR_REPO)
    run(["git", "-c", "user.name=zed-dev", "-c", "user.email=dev@localhost",
         "commit", "-q", "-m", "dev grammar"], GRAMMAR_REPO)
    rev = run(["git", "rev-parse", "HEAD"], GRAMMAR_REPO).stdout.strip()

    # The extension, with the grammar reference rewritten to the local repo.
    shutil.copytree(EXT_SRC, BUNDLE)
    toml = BUNDLE / "extension.toml"
    text = toml.read_text()
    text = text.replace(
        'repository = "https://github.com/ByteProject/tree-sitter-arcturus"',
        f'repository = "file://{GRAMMAR_REPO}"',
    )
    text = text.replace(
        'rev = "0000000000000000000000000000000000000000"',
        f'rev = "{rev}"',
    )
    toml.write_text(text)

    print(f"wrote {BUNDLE}")
    print(f"grammar at {GRAMMAR_REPO} ({rev[:10]})")
    print('in Zed: "zed: install dev extension" -> select build/zed-dev')
    return 0


if __name__ == "__main__":
    sys.exit(main())
