# Arcturus: Project Roadmap

Status: design phase. This document is the project charter and index. It
records the locked decisions, the reference documents, and the milestones
from first spec to a finished game.

Name: Arcturus. The star, and the narrative arc that every work of
interactive fiction is built on, so the name points at the medium itself.
Compiler binary: arcturus (short form arcc), written in Python. Source file
extension: .storyarc, for example hibernated3.storyarc. The standard library
is named Cosmos: the cosmos in which a story plays.

## 1. Vision

Arcturus is a high-level, readable interactive-fiction language with its own
compiler that emits standard Z-machine version 5 story files. The language
is the authoring layer; everything below it is existing, mature
infrastructure. The compiler is written in Python.

Ultimate goal: write the final part of the Hibernated trilogy in Arcturus.
The reference material here must be detailed enough that Claude Code can
implement the toolchain and later assist in authoring the game.

## 2. Locked decisions

These are settled. The reasoning is recorded so it does not have to be
rediscovered.

- Target format: standard Z-machine version 5. z8 is a later build flag for
  large, modern-only releases; the instruction set is identical, only the
  version byte and packed-address multiplier differ. The z5 ceiling is 256K,
  which is comfortable: Hibernated 2 is 137K before abbreviation
  optimization.
- Smallest possible z-code is a primary objective of the compiler, not an
  afterthought. The compiler is judged on output size as much as
  correctness. The size levers are whole-program dead-code elimination,
  abbreviation-based text compression, and dense code generation. See
  section 5.
- No custom virtual machine. Games are conformant Z-machine version 5 and
  run on every existing interpreter: Frotz, Bocfel, and Ceres on the CoCo and
  Dragon. The one planned interpreter-side feature is graphics, a later
  milestone via the `arc_image` property: a capability-guarded additive layer
  using a custom EXT opcode that Arcturus-aware interpreters render and
  standard interpreters skip unread, so the story file stays conformant z5
  throughout (see section 6 and milestone B7). This extends an existing owned
  interpreter such as Eris; it is never a forked or new VM.
- No PunyInform as the runtime, and no transpile-to-Inform-6 step. The
  compiler emits z5 directly, in the spirit of Dialog's dialogc.
- The standard library is Cosmos, shipped as an editable template rather than
  an opaque library. Three layers: (1) the compiler and runtime core, (2)
  Cosmos, with the standard kinds, verbs, grammar, default messages, and the
  world model, written in Arcturus itself and forkable, (3) the author's
  game, which is only what differs from Cosmos.
- The compiler itself is written in Python. Story files are tiny, so compiler
  speed is irrelevant, and Python keeps iteration fast. The compiler's
  deliverable is a standard z5 story file; what happens downstream of that
  file is out of scope for this project.
- Surface syntax: indentation-based blocks, no braces and no "end".
  Declarative object and world model with imperative handlers. A small
  keyword set. String interpolation. No C-style punctuation.

The project ends at a correct, small z5 story file. Packaging and disk-image
distribution are handled separately, outside this project, on the BuildTools
side once Arcturus itself is done.

## 3. Reference document set

Produced in this order; dependencies flow downward. Documents 01 and 02 are
written here. Documents 03 to 05 move into the Claude Code phase: they are
implementation work guided by 00 to 02, produced as the compiler is built
rather than written in advance.

- 00-roadmap.md (this document): charter, decisions, milestones, index.
- 01-syntax-reference.md: the authoritative language definition. Grammar,
  every construct with semantics and examples, the standard vocabulary,
  idiomatic patterns, and errors. Strong enough for Claude Code to author
  from. Highest priority.
- 02-cosmos-and-parser.md: the runtime. The Cosmos library as editable
  template, the standard kinds and verbs, the parser, the action pipeline,
  the banner, scope and light, the turn loop, and the summonable optional
  features (conversations, localization, debug).
- 03-compiler-pipeline.md (Claude Code phase): lexer, parser, semantic
  analysis, world-model lowering, z-code generation, text compression, and
  story-file assembly, with the size levers marked.
- 04-codegen-mapping.md (Claude Code phase): the construct-to-z5 opcode
  reference.
- 05-conformance.md (Claude Code phase): the test plan, with the two example
  games as golden tests and a size regression baseline.

The two worked examples in 01, the Brass Lantern and Cloak of Darkness, are
the shared reference programs across all documents.

## 4. Tooling

Built alongside the compiler, all in Python where a tool is involved:

- arcabbr: an abbreviation optimizer in the spirit of zabbrv. It scans a
  program's text and computes a near-optimal abbreviation set for maximum
  compression, writing it to an abbreviations file the compiler then uses.
  The compiler ships a reasonable default abbreviation set; a project
  overrides it by summoning its own file (01, summon).
- The Arcturus VS Code extension: syntax highlighting for .storyarc. This is
  an early goal, not a finishing touch, because readable highlighted source
  speeds every later step. A TextMate grammar plus a minimal language
  configuration.

## 5. Size strategy

In priority order:

1. Whole-program dead-code elimination. The compiler sees the entire program
   and Cosmos together and emits only the kinds, verbs, properties, and
   routines that are reachable. Unused Cosmos verbs and unused properties
   never reach the story file.
2. Text compression by abbreviation. Most of a story file is text. The
   compiler builds an abbreviation table and packs strings against it. The
   default table is computed by arcabbr; a project may supply its own.
3. Dense code generation. Opcode-form selection, tight branch encoding, sane
   local and stack use, and a peephole pass.

## 6. Graphics (later milestone)

Once the language is stable, Arcturus gains optional graphics through the
`arc_image` property, designed so the story file never stops being conformant
z5. A room carrying `arc_image "cellar"` is invisible to a standard
interpreter, which simply ignores a property it does not read. On an
Arcturus-aware interpreter, Cosmos reads the property on room entry and passes
the name as a numeric resource id to a custom EXT opcode; the interpreter
loads the picture from disk in the machine's native format (.kla on C64, .iff
on Amiga, and so on) or in a trimmed, RLE-compressed format kept small for
8-bit targets.

Safe degradation is structural, not a special case. A Z-machine interpreter
only decodes bytes its control flow reaches. The custom opcode sits behind a
capability guard that Arcturus-aware interpreters stamp at startup; on Frotz
the guard branch is always taken around it, so those bytes are never decoded
and nothing crashes. Adding rendering to an owned interpreter such as Eris
extends a finished VM (its decode loop, memory model, and I/O are already
done); it is not a new interpreter. The per-platform artwork, hand-authored on
the 8-bit machines because of cell-attribute constraints, is an asset
pipeline, separate from this project.

## 7. Milestones

Track A is design, produced here. Track B is implementation in Claude Code.
Each milestone has a concrete done-test.

### Track A: design (reference material)

- A0: roadmap and locked decisions. Done when approved.
- A1: syntax reference. Done when both example games can be written in full
  against it with no undefined constructs.
- A2: Cosmos and parser spec. Done when every verb and behavior the two
  examples rely on is specified, including scope, light, and the turn loop.

### Track B: implementation (Claude Code)

- B0: project scaffold and the VS Code syntax-highlighting extension, so
  source is readable from the first line written.
- B1: lexer and parser produce an AST for the full syntax reference, with
  unit tests. Done when both example sources parse cleanly.
- B2: semantic analysis and the world-model IR (objects, kinds, properties,
  grains, verbs, handlers, scope). Done when the IR for both examples is
  correct.
- B3: z5 backend MVP. Emit a valid z5 file for the smallest program: one
  room, print, quit, plus a correct banner. Done when it runs on Frotz and
  on Ceres.
- B4: Cosmos compiled by the compiler: parser, turn loop, standard verbs.
  Done when both example games are playable start to finish on Frotz.
- B5: size pass. Dead-code elimination, the arcabbr abbreviation pipeline,
  and codegen tightening. Done when a representative game is at or below its
  PunyInform-equivalent size.
- B6: feature-complete for Hibernated 3. The summonable features
  (conversations, localization, debug), every z5 feature the game needs, and
  authoring ergonomics validated by porting a real scene.
- B7: graphics via `arc_image` (section 6). The capability guard and EXT
  opcode contract, the trimmed RLE image format, and rendering added to an
  owned interpreter such as Eris. Done when an Arcturus-aware build shows room
  art while the same story file still runs unchanged on Frotz.
- B8: write Hibernated 3 in Arcturus. The goal.

## 8. What is next

The handoff bridge: a CLAUDE.md and a handoff prompt that point Claude Code
at documents 00 to 02, fix the build method, and start it at B0 and B1.
