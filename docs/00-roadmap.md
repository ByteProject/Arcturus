# Arcturus: Project Roadmap

Status: living charter. This document is the project charter and index. It
records the locked decisions, the reference documents, and the milestones
from first spec to a finished toolchain; the milestone table in section 7
tracks what is done. The language, Cosmos, and the compiler shipped through
the Hibernated 2 port (B8); the Actaea reference interpreter (B10) and
arc_image on modern systems (B11) are complete. Next are the retro image
targets (B12).

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

Ultimate goal: a complete, hackable IF toolchain - a compiler, an editable
standard library (Cosmos), a modern reference interpreter, and an optional
graphics path (`arc_image`) reaching from modern systems down to the 8-bit
machines. Arcturus proves itself by porting existing games: Hibernated 2
(text, the maturity proof, complete) and The Curse of Rabenstein (from DAAD,
the graphics testbed, which also ships as a worked example). The
reference material here must be detailed enough to implement the toolchain from,
and to author games against once it is built.

## 2. Locked decisions

These are settled. The reasoning is recorded so it does not have to be
rediscovered.

- Target format: standard Z-machine version 5. z8 is available via the
  `--zversion 8` build flag for large, modern-only releases; the instruction set
  is identical, only the version byte, the file-length scale, and the packed-
  address multiplier (4 to 8) differ. The z5 ceiling is 256K, which is
  comfortable: Hibernated 2 is 137K before abbreviation optimization. z8 raises
  the ceiling to 512K.
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
  throughout (see section 6 and milestones B11 to B12). This extends an existing owned
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

Produced in this order; dependencies flow downward. Documents 00 to 02 are the
design record. Documents 03 to 05 belong to the implementation phase: they are
implementation work guided by 00 to 02, produced as the compiler is built
rather than written in advance.

- 00-roadmap.md (this document): charter, decisions, milestones, index.
- 01-syntax-reference.md: the authoritative language definition. Grammar,
  every construct with semantics and examples, the standard vocabulary,
  idiomatic patterns, and errors. Strong enough to author from. Highest
  priority.
- 02-cosmos-and-parser.md: the runtime. The Cosmos library as editable
  template, the standard kinds and verbs, the parser, the action pipeline,
  the banner, scope and light, the turn loop, and the summonable optional
  features (conversations, localization, debug).
- 03-compiler-pipeline.md (implementation phase): lexer, parser, semantic
  analysis, world-model lowering, z-code generation, text compression, and
  story-file assembly, with the size levers marked.
- 04-codegen-mapping.md (implementation phase): the construct-to-z5 opcode
  reference.
- 05-granules.md: the author-facing reference for the summonable granules
  (extendedverbs, statusline, verbose_exits, conversations, debug): how to summon
  each, what it adds, the blocks an author can override, and how to write your
  own granule.
- 06-actaea.md: the Actaea reference interpreter, the official documentation
  (milestone B10, complete; the design record is actaea/actaea-design.md).
- 07-arc-image.md: the author guide to pictures: the master art, the arcimg
  workflow down to every machine, and what plays where. (The conformance
  evidence needs no document: the suite enforces it every run, with the two
  example games as golden tests and the size-regression ceilings beside
  them in tests/test_sizes.py.)
- 08-arcimage-interpreters.md: the implementer's book for the arc_image
  retro targets, one proven chapter per machine (the probes live in
  arc_image/probes/, the design record in arc_image/reference/design.md).

The two worked examples in 01, the Brass Lantern and Cloak of Darkness, are
the shared reference programs across all documents.

## 4. Tooling

Built alongside the compiler, all in Python where a tool is involved:

- arcabbr: an abbreviation optimizer in the spirit of zabbrv. It scans a
  program's text and computes a near-optimal abbreviation set for maximum
  compression. The compiler ships a standard abbreviation set, always applied;
  the same optimizer regenerates that default (tools/arcabbr.py) and backs the
  `arcc --make-abbreviations` pass, which writes a per-story abbreviations.granule
  a project summons by name to override the default (05, section 7).
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
z5. A room carrying `arc_image 8` (or `arc_image cellar`, a constant that folds
to the number) is invisible to a standard interpreter, which simply ignores a
property it does not read. The id is a resource slot, the one identifier every
target shares: on an Arcturus-aware interpreter, Cosmos reads the property on
room entry and passes the id to a custom EXT opcode, and the interpreter loads
picture id. There is no name manifest to translate down. Art is authored once
as PNGs in one of two picture shapes, both a whole number of text rows tall so
the status bar sits flush beneath the band: Infocom mode (320x72, 9 rows, the
upper third, the Arthur look) and DAAD mode (320x96, 12 rows, the upper half,
the Rabenstein look). On modern systems the PNG renders directly in the
reference interpreter, Actaea, which integer-scales it to the window, crisp for
pixel art (B11); the author tool `arcimg` prepares the art and packs it into an
`.arcres` file (a zip of the numbered PNGs) for distribution, the story kept
separate. For retro targets (B12) `arcimg` gains back-ends that convert each
PNG into the machine's own trimmed, RLE-compressed format (a custom format per
machine, sized to fit and not the full-screen .kla/.iff shapes, which cannot be
cropped to a band), kept small for 8-bit machines.

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

Track A is design. Track B is implementation. Each milestone has a concrete
done-test.

### Track A: design (reference material)

- A0: roadmap and locked decisions. Done when approved.
- A1: syntax reference. Done when both example games can be written in full
  against it with no undefined constructs.
- A2: Cosmos and parser spec. Done when every verb and behavior the two
  examples rely on is specified, including scope, light, and the turn loop.

### Track B: implementation

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
- B4: Cosmos compiled by the compiler: parser, turn loop, the verbs the two
  examples exercise. Done when both example games are playable start to finish
  on Frotz. (Done; finishing with the readability and meta-verb polish:
  library-controlled paragraph breaks, the unrecognized-verb reply, and quit.)
- B5: feature-complete library and a fair benchmark. The full standard verb
  set at parity with PunyInform (including flavor verbs like jump), the meta
  verbs (score, save, restore, restart, undo, again, oops, quit), and a fresh,
  distinctive standard message set - not Inform's or Dialog's. The summon loader,
  then the summonable features as embedded granules, built and tested one at a
  time: `summon.extendedverbs` (the extended flavor verb set; the Infocom-style
  ask/tell topic logic later became its own `summon.infocom_talking`),
  `summon.statusline` (an opt-in status line,
  the first of the window work), `summon.verbose_exits` (auto-listed exits),
  `summon.conversations` (a menu-driven talk system painted in the upper window,
  the talk_menu equivalent, with code-toggled topics and an easy authoring
  surface), and `summon.debug` (testing verbs, kept out of a release simply by not
  summoning them; Arcturus-named with Inform synonyms). Message and verb overrides
  without unpacking the library, via a same-named block in the game or a granule
  that wins over the Cosmos default (most-specific-wins, section 2). The
  single-file `arcc` embeds Cosmos and all shipped granules; `arcc
  --extract-library DIR` writes them out for wholesale hacking.
- B6: size pass. Dead-code elimination, the abbreviation pipeline, and codegen
  tightening. The compiler bakes in a standard abbreviation set used by default;
  a `--make-abbreviations <file.storyarc>` flag curates the string pool from the
  story plus its resolved granules (library and user), computes an optimized set,
  and writes a single `abbreviations.granule` in Arcturus syntax. The author
  summons it, and on recompile the encoder uses it instead of the baked-in set
  (a two-pass flow). Done when a representative game is at or below its
  PunyInform-equivalent size (Cloak of Darkness is 27K in PunyInform), measured
  with the full library in place.
- B7: language packs. Spanish and German Cosmos translations, each a granule
  selected by `summon.language` - a message table keyed by id, localized
  vocabulary (directions and verbs), and parser grammar overrides where an
  inflected language needs them (the language seam, section 8 of docs/02). Each
  pack curates its own abbreviations via the B6 pipeline. A large milestone in its
  own right; the language seam is designed but unbuilt.
- B8: port Hibernated 2 to Arcturus. Hibernated 2 is written in PunyInform and
  releases commercially there first; the Arcturus port follows at its own pace as
  the first large, real-world game in the language. It targets z5 (137K before
  abbreviation optimization, well under the 256K ceiling), because it is meant to
  play on retro systems, not z8. This is the maturity milestone: a full-length
  game exercises save and restore, size behavior, and library breadth far past
  what any example can, and it surfaces the gaps and missing polish only a real
  game finds (the same payoff the feature showcases gave, at scale). It ships as
  the flagship demonstration of what Arcturus can do, and porting real games
  before the interpreter and graphics keeps the language malleable while the bugs
  are cheap to fix.
- B9: DROPPED (2026-07-04, Stefan's call). Ghosts of Blackwood Manor was
  the easier port; with Hibernated 2 complete, all four acts at a
  self-summed perfect score, the sufficiency proof it would have added is
  already delivered. The number stays reserved so later milestones keep
  their names.
- B10: COMPLETE (2026-07-05). The reference interpreter, Actaea: a Standard
  1.1 conformant z5/z8 interpreter in Python under `actaea/`, playing any
  well-formed story file, with three front-ends on one headless core (tkinter
  window, curses terminal, headless pipe), Quetzal saves interoperating with
  Frotz both ways, and the conformance gate green (CZECH 406/406, Praxix,
  TerpEtude's text portions, real z5/z8 games). The testing ground for
  `arc_image`. docs/06-actaea.md is the documentation; actaea/actaea-design.md
  the design record (M1 to M11, all built).
- B11 (complete, 2026-07-07): `arc_image` on modern systems (section 6). The
  capability guard and the EXT opcode contract, resource ids written as
  constants and the mode carried in the opcode (`arc_mode`), room and scene art
  rendered from PNGs in Infocom and DAAD modes, the rendering capability added
  to Actaea, and the `arcimg` author tool preparing and packing the art into an
  `.arcres` file, with the same story file still running unchanged on Frotz.
- B12 (in progress; the approved charter, target ledger, and sub-milestones
  R0 to R6 are arc_image/reference/design.md): `arc_image` on retro systems,
  fourteen targets. The center of gravity is the conversion intelligence:
  one band-shaped master painting per image, `arcimg` deriving the ideal
  native version per machine (palette, resolution, attribute-clash solving),
  with hand-painted native art as an optional 1:1 path. Per-platform RLE
  formats sized to the band, per-target interpreter blueprints proven by
  emulator probes, and the public contract document third-party
  interpreters (Vezza) implement from.
- B13: port The Curse of Rabenstein from DAAD to Arcturus. Trivial as a port,
  it exercises the `arc_image` graphics path end to end (its art is ready for
  the retro targets) and ships as a worked example game.

Beyond the lettered milestones, far out and deliberately unscheduled
(Stefan's direction, 2026-07-19): a SECOND interpreter beside Actaea,
built for touch and point-and-click play of Z-machine games, on the Mac
and any regular computer, and on iPad, iPhone, and Android. Actaea stays
the reference and the keyboard home; this one reimagines how a parser
game is PLAYED, not what it is, and nothing about it starts until the
current milestones are long done.

## 8. Status

The design tracks (A0 to A2) are complete. Implementation stands at the end of
B11: the language, Cosmos, and the compiler shipped through the Hibernated 2
port (B8, all four acts at a self-summed perfect score); Actaea, the reference
interpreter, is complete and conformant (B10); and arc_image graphics render on
modern systems (B11), the mode carried in the opcode so it degrades to text
everywhere and extends to retro next. The project owns both ends of the
pipeline. Next are the retro image targets (B12) and the Rabenstein port (B13).
Current progress is tracked in PROGRESS.md.
