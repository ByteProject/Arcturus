#!/usr/bin/env python3
# zed_publish.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Export the Zed extension and its Tree-sitter grammar into their
standalone publishing repositories.

Development lives HERE, in the Arcturus repository (editors/zed and
editors/tree-sitter-arcturus); the standalone repos are publishing
artifacts, refreshed by this tool:

    ../tree-sitter-arcturus   the grammar (Zed clones it by URL + rev)
    ../zed-arcturus           the extension (submoduled by Zed's registry)

The tool copies the sources over (preserving each target's .git), stamps
the extension's grammar reference with the LOCAL grammar repo's HEAD
commit, and copies the MIT LICENSE into both (the registry requires a
LICENSE at the extension path). It never commits or pushes: review the
diffs in each repo, commit there, and push. IMPORTANT: push the grammar
repo FIRST, so the rev the extension pins is public before the extension
referencing it.

Usage:
    python3 tools/zed_publish.py
"""

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAMMAR_SRC = ROOT / "editors" / "tree-sitter-arcturus"
EXT_SRC = ROOT / "editors" / "zed"
LICENSE = ROOT / "LICENSE"
GRAMMAR_DST = ROOT.parent / "tree-sitter-arcturus"
EXT_DST = ROOT.parent / "zed-arcturus"


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True,
                          text=True)


def refresh(src: pathlib.Path, dst: pathlib.Path, skip=()) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    if not (dst / ".git").exists():
        run(["git", "init", "-q"], dst)
    for item in dst.iterdir():
        if item.name == ".git":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    for item in src.iterdir():
        if item.name in skip:
            continue
        if item.is_dir():
            shutil.copytree(item, dst / item.name)
        else:
            shutil.copy2(item, dst / item.name)
    shutil.copy2(LICENSE, dst / "LICENSE")


GRAMMAR_README = '''# tree-sitter-arcturus

A Tree-sitter grammar for Arcturus, the high-level interactive-fiction
language for the Infocom Z-machine: `.storyarc` games, `.granule` library
extensions, and `.prelude` library sources.

Arcturus lives at https://github.com/ByteProject/Arcturus. This grammar is
developed there (editors/tree-sitter-arcturus); this repository is its
publishing home, referenced by the Zed extension
(https://github.com/ByteProject/zed-arcturus) and open to any editor that
speaks Tree-sitter.

The grammar is built for highlighting: declaration heads are structural
(names colour and outline), everything else is a plain identifier for the
consuming editor's queries to classify. It parses the entire Arcturus
corpus, every shipped example and the Cosmos standard library, without a
single error node.
'''


def main() -> int:
    # The grammar first: the extension pins its HEAD.
    refresh(GRAMMAR_SRC, GRAMMAR_DST)
    (GRAMMAR_DST / "README.md").write_text(GRAMMAR_README)
    status = run(["git", "status", "--porcelain"], GRAMMAR_DST).stdout
    if status.strip():
        print(f"{GRAMMAR_DST}: changes to review and commit")
    head = None
    try:
        head = run(["git", "rev-parse", "HEAD"], GRAMMAR_DST).stdout.strip()
    except subprocess.CalledProcessError:
        pass  # no commit yet: commit the grammar first, then re-run

    # The extension, with the grammar reference stamped. The dev README
    # stays in the Arcturus repo; the published one is written here.
    refresh(EXT_SRC, EXT_DST, skip=("README.md",))
    toml = EXT_DST / "extension.toml"
    text = toml.read_text()
    if head is not None:
        text = text.replace(
            'rev = "0000000000000000000000000000000000000000"',
            f'rev = "{head}"',
        )
    toml.write_text(text)
    (EXT_DST / "README.md").write_text(
        "# Arcturus for Zed\n\n"
        "Syntax highlighting for the Arcturus programming language\n"
        "(Infocom Z-machine): `.storyarc` games, `.granule` library\n"
        "extensions, and `.prelude` library sources, plus an outline of\n"
        "rooms, things, kinds, blocks, and topics.\n\n"
        "Arcturus is a high-level interactive-fiction language with its\n"
        "own compiler, standard library, and reference interpreter:\n"
        "https://github.com/ByteProject/Arcturus\n\n"
        "This extension is developed inside the Arcturus repository\n"
        "(editors/zed); this repository is its publishing home. The\n"
        "Tree-sitter grammar lives at\n"
        "https://github.com/ByteProject/tree-sitter-arcturus.\n"
    )
    status = run(["git", "status", "--porcelain"], EXT_DST).stdout
    if status.strip():
        print(f"{EXT_DST}: changes to review and commit")
    if head is None:
        print("NOTE: the grammar repo has no commit yet; commit it and "
              "re-run so the extension pins a real rev.")
    else:
        print(f"extension pins grammar rev {head[:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
