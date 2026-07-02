# Handover to Fable

Written 2026-07-02 by the outgoing model (Claude Opus 4.8), for Stefan, at the
point of switching to Anthropic's Fable model. This is an orientation and a
request: read it, read the authoritative documents it points to, then do an
independent assessment of the work so far and where it can be improved, before
we start milestone B8. Nothing here is binding on your judgement; where you find
this handover or the code wrong, say so.

## What Arcturus is

A high-level interactive-fiction language with its own compiler, written in
Python (standard library only), that emits standard Z-machine version 5 (and,
with `--zversion 8`, version 8) story files. The standard library is Cosmos,
written in Arcturus itself and shipped as an editable template. The end goal is
a complete, hackable IF toolchain, proven by porting three existing games. Full
charter and locked decisions are in `CLAUDE.md` (read it first) and the three
authoritative specs under `docs/` (00 roadmap, 01 syntax, 02 cosmos-and-parser).
When code and a document disagree, the document wins.

Author and decision-maker: Stefan Vogt (IF author: Hibernated, Ghosts of
Blackwood Manor). Expert register, no flattery. His `~/.claude` memory (loaded
as `MEMORY.md`) carries standing preferences; honor them.

## Where the project stands

Milestones B0 to B7 are complete. B8 is next.

| Milestone | Description | Status |
|-----------|-------------|--------|
| B0 | Project scaffold and VS Code extension | done |
| B1 | Lexer and parser to an AST, with unit tests | done |
| B2 | Semantic analysis and the world-model IR | done |
| B3 | Z-machine backend MVP (smallest valid story file) | done |
| B4 | Cosmos compiled: parser, turn loop, standard verbs | done |
| B5 | Feature-complete library and a fair benchmark | done |
| B6 | Size pass (DCE, abbreviations, dense codegen) | done |
| B7 | Language packs (Spanish, German) | done (native review pending) |
| B8 | Port Hibernated 2 (first full game, maturity milestone) | next |
| B9 | Port Ghosts of Blackwood Manor (text) | pending |
| B10 | The reference interpreter, Actaea | pending |
| B11-B12 | arc_image (modern, then retro) | pending |
| B13 | Port The Curse of Rabenstein (from DAAD) | pending |

Current facts: arcc 0.7.0, Cosmos 0.10.0. 273 tests pass (`python3 -m pytest`).
Working tree clean except untracked `actaea/` (an unrelated scratch dir; ignore
it). The living log with per-milestone detail and prior handover checkpoints is
`PROGRESS.md`.

## Holistic overview, component by component

### The compiler (`arcturus/`)
Python 3.11+, standard library only, zero runtime dependencies. Clean module
boundaries, in dependency order: `errors`, `tokens`, `ast`, `lexer`, `parser`,
`prelude` (built-in property/attribute/direction/particle tables), `worldmodel`
(the IR), `sema`, `zstring` (ZSCII text and the accent map), `abbrev`,
`storyfile`, `assembler`, `objects` (object table, attributes, gender), `dictionary` (vocabulary and
grammar bytes), `lower` (statements and
expressions to routines), `cosmos` (library loading, granules, language
selection), `codegen` (assembly, DCE, story build), `astdump`, `irdump`, `cli`.
The compiler is amalgamated for distribution into a single self-contained
`build/arcc` by `tools/amalgamate.py`; regenerate it at every milestone or
version bump (standing habit, see the memory of the same name). Design records:
`docs/03-compiler-pipeline.md`, `docs/04-codegen-mapping.md`.

### The Cosmos library (`cosmos/`)
Written in Arcturus, embedded into the compiler, and shipped as an editable
template (`--extract-library`, `--eject-granule`, `--eject-language`). Two
kinds of file: `.prelude` (always-on core) and `.granule` (summonable, pay for
use). Core preludes: `english.prelude` (the default language layer: verbs,
directions, particles, articles, and every message), `parser.prelude` (the
language-agnostic parser skeleton), `actions.prelude` (action behavior keyed by
action name, agnostic), `loop.prelude`, `dispatch.prelude`, `scope.prelude`,
`core.prelude`. Granules: `statusline`, `conversations` (menu-driven),
`extendedverbs`, `debug`, `verbose_exits`, plus the two language packs
`spanish.granule` and `german.granule`. Design record: `docs/05-granules.md`;
runtime and parser: `docs/02-cosmos-and-parser.md`; the verb and message
inventories are `docs/verb-set.md` and `docs/message-set.md`.

### The language packs / translations
The language seam is built and documented (docs/02 section 14a, "Writing in
another language"). A pack is a granule with a `language "code"` marker,
selected only by `summon.language "code"`, which drops `english.prelude`. Four
seams: accents to ZSCII default set (`zstring`), articles and gender (packs own
`art_the`/`art_a`; `${the:acc noun}` carries case), localized directions and
verbs, and verb particles (`particle on "..."`, roles on/off/auf/zu). German
adds three-way gender via `der`/`die`/`das` object declarations (compiler maps
to feminine/neuter attributes), full case-inflected articles, and separable
verbs (`schalt ... an`, `schliess ... auf`). Both packs are functionally
complete and verified on Frotz.

  IMPORTANT, read this honestly: translation QUALITY is not certified. Spanish
  awaits native review by Pablo Martinez. German had one native pass by Stefan
  over the message table (17 corrections applied) and its example prose fixed,
  but a full native pass is still owed. The outgoing model's judgement of German
  idiom proved unreliable: it called calqued, obviously-wrong lines "natural."
  Do not trust any model's self-assessment of non-English idiom, including your
  own; defer to the native reviewer, and treat "the translation is fine" as
  unverified until a native speaker signs off. See the memories
  `translations-must-be-idiomatic` and `never-strip-accents`.

### Documentation and README
`docs/00-roadmap.md` (charter, locked decisions, milestones, size and graphics
strategy), `docs/01-syntax-reference.md` (the language, with the two conformance
example games), `docs/02-cosmos-and-parser.md` (the runtime), `docs/03` to
`docs/05` (pipeline, codegen mapping, granules), `docs/06-actaea-design.md` (the
future interpreter, B10), `docs/verb-set.md`, `docs/message-set.md`. `README.md`
is the public face (keep it and the docs in sync with any change they describe;
no AI-process framing in public docs). `docs/07-conformance.md` is named in
CLAUDE.md but not yet written; it is expected as conformance work proceeds.

### Examples (`examples/`)
The two conformance anchors: `brass-lantern.storyarc`, `cloak-of-darkness.
storyarc`. Feature showcases in `examples/features/` (containers, computed
properties, kinds-and-inheritance, doors-and-locks, spans, grains, on-other,
daemons-and-timers, introproperty). Granule showcases in `examples/granules/`
(conversations, extended-verbs, infocom-interrogation, statusline,
verbose-exits). Two full localized games: `ejemplo-espanol.storyarc` (Spanish,
"La Posada del Faro") and `beispiel-deutsch.storyarc` (German, "Das Gasthaus am
Leuchtturm"). Compiled localized artifacts live in the gitignored `build/`
(`posada.z5`, `gasthaus.z5`) for Stefan to hand to native reviewers.

### Tests and tooling
`tests/` holds 50 test files, 273 tests, run with `pytest` (dev-only
dependency). Many drive a real interpreter (dfrotz) end to end and skip if none
is on PATH. Tooling: `tools/amalgamate.py` (build the standalone `arcc`),
`tools/arcabbr.py`, `tools/build_vsix.py` (the VS Code extension under
`editors/vscode/`).

### Memory
The outgoing model kept file-based memories under
`~/.claude/projects/-Users-stefan-Fiction-Arcturus/memory/`, indexed by
`MEMORY.md`. They record who Stefan is, standing feedback (no em dashes ever,
never strip accents, translations must be idiomatic, never override git
identity, regenerate the amalgam at milestones, keep public docs in sync,
interpreter verification is a hand-off), and project decisions. Read the index;
honor them; correct any that have gone stale.

## Invariants to respect (from CLAUDE.md and the memories)

- Smallest possible z-code is a primary objective, judged alongside correctness.
- Compiler is Python, standard library only, zero runtime dependencies.
- The document wins over the code; if the document is wrong, fix it in the same
  commit as the code.
- Plain ASCII punctuation everywhere. No em dashes or en dashes, in code,
  comments, docs, messages, or chat. Hard rule.
- Non-English text keeps proper accents (they encode to the ZSCII default set
  and render on Stefan's retro interpreters); every typeable word also carries an
  ASCII fallback (oeffne beside oeffne), because 8-bit keyboards cannot type
  accents.
- Git: use plain `git commit` (repo identity is ByteProject <stefan@8-bit.info>);
  never override identity; ask before history operations. Commit per milestone
  with the done-test named. Co-author trailer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
  (update the attribution to your own identity going forward).
- Verify a built story on Frotz yourself, then hand the .z5 (with byte size) to
  Stefan to run before advancing a milestone.
- Regenerate `build/arcc` (`python3 tools/amalgamate.py`) at every milestone or
  version bump.

## Known limitations and open questions (facts, to seed your assessment)

These are stated as facts, not as the outgoing model's assessment, which is what
Stefan is asking you for. Verify each independently.

- Translation quality is unverified pending native review (Spanish: Pablo;
  German: a native pass still owed). See the honest note above.
- German separable lock verbs work only with the particle LAST ("schliess die
  Tuer mit dem Schluessel auf"); particle-before-noun for a two-noun base
  ("schliess auf Tuer") misparses because the leading particle becomes the
  phrase separator. One-noun verbs (switch) take the particle in either order.
- German gender declaration `der`/`die`/`das` is reserved project-wide as a
  gender marker; the compiler does not auto-derive gender for German (no reliable
  spelling rule), so an undeclared noun defaults masculine silently.
- `docs/07-conformance.md` is promised in CLAUDE.md but not yet written.
- There is a stale comment in `cosmos/german.granule` near `find_particle`
  (around line 69) claiming particles are "not wired ... stays inert"; that
  predates the separable-verb work and is now false. A small fix, left for you or
  a follow-up.
- Size: the outgoing model tracked byte sizes per build but there is no
  automated size-regression gate in the test suite; sizes are checked by hand.

## What Stefan is asking you to do first

Before B8, assess the work so far and identify room for improvement, across all
of the above: compiler correctness and clarity, Cosmos library design and
breadth, code size (the primary objective), documentation accuracy and sync,
example coverage, test coverage and its gaps, and the translations (with the
caveat that idiom is the native reviewer's call, not yours). Produce your own
independent read; do not take this handover's framing as settled. Verify claims
rather than trusting them, run the suite, build and play the examples, and bring
back a prioritized list of what to improve and what to leave.

## Then: milestone B8

B8 is porting Hibernated 2 (Stefan's game, written in PunyInform, released
commercially there first) to Arcturus, as the first large, real-world game in
the language. It targets z5 (retro systems, not z8). This is the maturity
milestone: a full-length game exercises save/restore, size behavior, and library
breadth far past any example, and surfaces the gaps only a real game finds. Full
description: `docs/00-roadmap.md` section 7, B8. Expect the assessment above to
feed directly into it: fix the cheap gaps while the language is still malleable,
before a large game locks assumptions in.

## Quick reference

- Compile: `arcc examples/brass-lantern.storyarc -o build/brass-lantern.z5`
  (z5 default; `--zversion 8` for v8). Or `python3 -m arcturus.cli ...`.
- Test: `python3 -m pytest`.
- Standalone build: `python3 tools/amalgamate.py` writes `build/arcc`.
- Verify: run the .z5 on dfrotz/frotz; the same file must also run on Stefan's
  retro interpreters for the 8-bit target.
- Localized games to hand to reviewers: `build/posada.z5` (Spanish),
  `build/gasthaus.z5` (German).
