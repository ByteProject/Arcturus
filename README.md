# Arcturus

Arcturus is a high-level interactive-fiction language with its own compiler,
written in Python, that emits standard Z-machine version 5 story files. The
standard library is named Cosmos. The end goal is to write the final part of
the Hibernated trilogy in Arcturus.

See `CLAUDE.md` for project context and the authoritative specifications under
`docs/`:

- `docs/00-roadmap.md`: charter, locked decisions, milestones, size strategy.
- `docs/01-syntax-reference.md`: the language.
- `docs/02-cosmos-and-parser.md`: the runtime.

## Repository layout

```
arcturus/        the compiler package (lexer, parser, ast, cli, ...)
cosmos/          the Cosmos library in .storyarc
tools/           arcabbr.py and other Python tools
examples/        brass-lantern.storyarc, cloak-of-darkness.storyarc
tests/           unit and golden tests
editors/vscode/  the syntax-highlighting extension
```

## Build, run, test

The compiler uses the Python standard library only and targets Python 3.11+.

### For distribution: one standalone script

The shipped compiler is a single self-contained file with no dependencies and
no installation. Build it from the package, then run it on a bare interpreter:

```
python3 tools/amalgamate.py build/arcc
python3 build/arcc examples/brass-lantern.storyarc
```

`build/arcc` is the artifact the interactive-fiction community downloads and
runs directly (`./arcc game.storyarc`). The `arcturus/` package is the
development source of truth; `arcc` is generated from it verbatim, so the two
never differ.

### For development: the package

```
python3 -m arcturus examples/brass-lantern.storyarc
python3 -m pytest
```

During the early milestones the CLI parses and reports on a source file; code
generation arrives later:

```
python3 -m arcturus examples/brass-lantern.storyarc --check
python3 -m arcturus examples/brass-lantern.storyarc --dump-ast
```
