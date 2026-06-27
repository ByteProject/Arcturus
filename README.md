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

```
arcc examples/brass-lantern.storyarc -o build/brass-lantern.z5
pytest
```

During early milestones the CLI parses and reports on a source file:

```
arcc examples/brass-lantern.storyarc --check
arcc examples/brass-lantern.storyarc --dump-ast
```
