# Arcturus progress

A living log of where the project stands, maintained as work proceeds. The
authoritative plan is `docs/00-roadmap.md` (milestones B0 to B8); this file
tracks status against it and records decisions made during implementation.

Last updated: 2026-06-27.

## Status at a glance

| Milestone | Description | Status |
|-----------|-------------|--------|
| B0 | Project scaffold and VS Code extension | done |
| B1 | Lexer and parser producing an AST, with unit tests | done |
| B2 | Semantic analysis and the world-model IR | next |
| B3 | Z-machine backend MVP (smallest valid story file) | pending |
| B4 | Cosmos compiled: parser, turn loop, standard verbs | pending |
| B5 | Size pass (dead-code elimination, abbreviations, codegen) | pending |
| B6 | Feature-complete for a real game | pending |
| B7 | Graphics via `arc_image` | pending |
| B8 | Write the target game in Arcturus | pending |

Not production-ready: the compiler parses and reports today but does not yet
generate a story file.

## Toolchain

- Python 3.14.6 is the machine default (`python3`); the compiler targets 3.11+.
- Tests run with `python3 -m pytest` (pytest 9.1.1, a dev-only dependency). The
  compiler itself stays standard-library only.
- Frotz is installed for verifying built story files from B3 onward.

## Done

### B0: scaffold and VS Code extension

- Git initialized; the specs committed first.
- Repository layout, `pyproject.toml` (3.11+, zero runtime deps, pytest
  dev-only), `LICENSE` (MIT), `.gitignore`.
- The two reference games extracted verbatim into `examples/` (verified by diff
  against docs/01 sections 17 and 18).
- VS Code extension under `editors/vscode/`: TextMate grammar and language
  configuration, packaged as an installable `.vsix` (built by
  `tools/build_vsix.py`), covering `.storyarc`, `.prelude`, and `.granule`.

### B1: lexer, parser, AST

- `arcturus/` package: `lexer` (indentation-significant tokenizer, multi-line
  strings with whitespace collapse and `${...}` interpolation, UUID literals),
  `ast`, `parser` (recursive descent plus precedence climbing), `astdump`, and
  the `arcc` CLI.
- Done-test green: both example sources parse cleanly. 62 unit tests pass.
- `is`-as-property-test versus `is`-as-equality is deliberately left to B2.

### Distribution and housekeeping

- The compiler is developed as a modular package but shipped as a single
  standalone `arcc` script, built by `tools/amalgamate.py`, which embeds each
  module verbatim behind an in-memory loader. `tests/test_standalone.py` runs
  the generated script with no package on `sys.path` to prevent drift.
- Every Python source file carries a credit header. The `arcc` CLI prints an
  Inform-style banner and copyright. The compiler hardcodes nothing about the
  Cosmos library, including its version (the library will declare its own, used
  only for the in-game banner).
- File-extension conventions fixed: `.storyarc` (story), `.prelude` (Cosmos
  library file), `.granule` (extension). The specs were updated to match: the
  syntax reference (docs/01) now documents all three extensions, and the
  Cosmos/parser spec (docs/02) refers to library files as `.prelude` and
  extensions as `.granule`. Internal "Claude Code phase" framing in the specs
  was changed to "implementation phase" for public reading.

### Documentation policy

When a change affects anything the public-facing documentation describes, the
docs are updated in the same step. New conventions are recorded here as they
are introduced.

## Next: B2

Semantic analysis and the world-model intermediate representation: resolve
objects, kinds, the property/attribute storage choice, `is`-test
disambiguation, scope, verbs, and handlers. Done-test: the IR for both example
games is correct. A plan will be restated before implementation begins.
