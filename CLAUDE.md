# Arcturus

Arcturus is a high-level interactive-fiction language with its own compiler,
written in Python, that emits standard Z-machine version 5 story files. The
standard library is named Cosmos. The end goal is a complete, hackable IF
toolchain - compiler, editable library, a modern reference interpreter, and an
optional `arc_image` graphics path down to 8-bit machines - validated by porting
three existing games to Arcturus: Hibernated 2 (text, the first large real-world
game and the maturity milestone), Ghosts of Blackwood Manor (text), and The Curse
of Rabenstein (from DAAD, the graphics testbed). Hibernated 2 releases first in
its PunyInform build; the Arcturus port follows. Writing Hibernated 3 stays
Stefan's own goal, pursued separately; this project stays focused on Arcturus
itself.

This file is the standing context for the project. Read it first, then the
three specifications under docs/, which are authoritative.

## Authoritative documents

- docs/00-roadmap.md: charter, locked decisions, milestones, the size
  strategy, and the graphics plan.
- docs/01-syntax-reference.md: the language. Grammar, every construct, and two
  worked example games that are the conformance anchors.
- docs/02-cosmos-and-parser.md: the runtime. Cosmos as an editable library,
  the parser, the action pipeline, the banner, scope and light, the turn loop,
  and the summonable features.

When code and a document disagree, the document wins: fix the code, or if the
document is wrong, propose the change and update the document in the same
commit.

## Locked decisions

- Target: conformant Z-machine version 5. A --v8 build flag is a later option
  for large modern-only releases; same codegen, two header values differ.
- Smallest possible z-code is a primary objective, judged alongside
  correctness. Levers in order: whole-program dead-code elimination,
  abbreviation-based text compression, dense codegen (docs/00 section 5).
- The compiler is Python with zero runtime dependencies, so `arcturus` runs on
  a bare interpreter. Tests may use pytest as a dev-only dependency.
- Cosmos is the standard library, written in Arcturus itself and shipped as an
  editable template, not a black box. Overriding is ordinary handler
  resolution: most specific wins, `continue` defers to the next.
- No custom virtual machine, no transpile-to-Inform-6, no PunyInform runtime.
  The compiler emits z5 directly.
- Source extension .storyarc. Compiler binary `arcturus`, short form `arcc`.

## Repository layout

```
CLAUDE.md
docs/            00-02 specs (authoritative); 03-05 produced as you build
arcturus/        the compiler package (lexer, parser, ast, sema, codegen, cli)
cosmos/          the Cosmos library in .prelude (english = language layer, actions,
                 parser, scope, dispatch, loop, core) plus the .granule features
tools/           arcabbr.py and other Python tools
examples/        brass-lantern.storyarc, cloak-of-darkness.storyarc
tests/           unit and golden tests
editors/vscode/  the syntax-highlighting extension
pyproject.toml
```

## Build, run, test

- Compile: `arcc examples/brass-lantern.storyarc -o build/brass-lantern.z5`
  (z5 by default; `--v8` for version 8).
- Test: `pytest`.
- Verify a built story on a reference interpreter (Frotz or Bocfel); the same
  file must also run on Ceres for the 8-bit target.

## Coding standards

- Python 3.11 or later. Standard library only for the compiler runtime.
- Clear module boundaries: lexer, parser, AST, semantic analysis and the
  world-model IR, codegen, z5 story-file assembly, CLI.
- Plain ASCII punctuation in all generated code, comments, and documents. No
  em dashes; use commas, colons, semicolons, parentheses, or shorter
  sentences.
- Every milestone lands with tests and a green done-test before the next.

## Non-goals (do not build these here)

- Disk-image building or BuildTools integration. The project ends at a z5
  file; packaging is handled separately, later, elsewhere.
- A custom VM for running Arcturus games. They emit standard z5 and run on any
  conformant interpreter, so the compiler never ships a runtime. (The Actaea
  reference interpreter and arc_image graphics are their own later milestones,
  B10 to B12, built here but not during the language and library work.)

## Method

- git first: initialize the repo before writing code, and commit per milestone
  with the done-test named in the message.
- Use subagents for tool installation (pytest, a z-machine interpreter for
  testing) so the main thread stays on design and code.
- Work milestone by milestone from docs/00 section 7 (B0 to B13). Each has a
  concrete done-test; do not advance until it passes.
- Produce docs/03-compiler-pipeline.md, docs/04-codegen-mapping.md,
  docs/05-granules.md, and docs/07-conformance.md as the matching work is done,
  so the design record stays current.

## Conformance

The two example games are the golden tests. The Brass Lantern and Cloak of
Darkness (docs/01 sections 18 and 19) must compile, run correctly on Frotz,
and run on Ceres, and their story files are tracked for size regression
against a PunyInform-equivalent build.

## Actaea (milestone B10): the reference interpreter

Actaea is a Standard 1.1 conformant Z-machine interpreter for versions 5 and 8,
written in Python with a tkinter GUI, built in this repo under `actaea/`. It
plays any well-formed story file, not only Arcturus output. docs/06-actaea-
design.md is authoritative for it.

- Scope: z5 and z8 only; full text styles and colours; a true monospace cell
  grid for the upper window; Quetzal save and restore with in-memory undo and
  restart. No sound. No arc_image.
- arc_image is not part of Actaea. It is built later, in this same project, as
  milestones B11 and B12. Actaea only keeps the cell model decoupled so that work
  is an extension. Nothing in Actaea's M1 to M11 touches graphics.
- Architecture: a headless VM core with a hard boundary to the tkinter front-
  end. The core passes conformance through a console harness before the GUI
  exists.
- Conformance: CZECH and Praxix headless (the M6 gate), and TerpEtude for the
  screen and input features.
- Milestones M1 to M11 in docs/06 are the breakdown of B10. Headless through M6,
  GUI from M7, the cell grid its own milestone (M8) with a visible done-test.