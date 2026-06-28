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
| B2 | Semantic analysis and the world-model IR | done |
| B3 | Z-machine backend MVP (smallest valid story file) | done |
| B4 | Cosmos compiled: parser, turn loop, standard verbs | in progress |
| B5 | Size pass (dead-code elimination, abbreviations, codegen) | pending |
| B6 | Feature-complete for a real game | pending |
| B7 | Graphics via `arc_image` | pending |
| B8 | Write the target game in Arcturus | pending |

Not production-ready: the compiler generates valid z5 story files, and Cosmos
(dispatch, scope/light, the parser) is being built in Arcturus. The turn loop
and standard verbs (B4.5e) are not yet in place, so a full game is not yet
playable end to end.

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
- Done-test green: both example sources parse cleanly.
- `is`-as-property-test versus `is`-as-equality is deliberately left to B2.

### B2: semantic analysis and the world-model IR

- `arcturus/` gains `prelude` (the standard Cosmos environment as data,
  injected into the analyzer so nothing about Cosmos is hardcoded; it will be
  replaced by compiling real `.prelude` source in B4), `worldmodel` (the IR),
  `sema` (the analysis passes), and `irdump` (`arcc --dump-ir`).
- Passes: collect declarations, resolve kind chains, build the program-wide
  property table (one type per property, type-clash diagnostic, provisional
  attribute-vs-slot storage), then resolve bodies (name resolution, the
  `is`-test disambiguation, the boolean-condition check, declare-before-change,
  and handler event and operand validation).
- Done-test green: the world-model IR for both example games is correct. The
  CLI parses and checks by default.

### B3: the z5 backend MVP

- `arcturus/` gains `zstring` (the ZSCII / Z-string encoder), `storyfile` (the
  header and region assembler, with checksum and length), and `codegen` (lower
  the world model to a complete z5 image). `arcc -o game.z5` now writes a story
  file. The construct-to-opcode mapping is documented in
  docs/04-codegen-mapping.md.
- The smallest program (a `game` block, an `on start` with `say` lines, and one
  room) compiles to a valid z5 that prints the banner and the start text, then
  quits. The banner is emitted by the compiler as a provisional stand-in; it
  becomes Cosmos's job at B4, and the compiler still hardcodes nothing about
  the library.
- Done-test green: the generated story file runs on Frotz (verified with
  `dfrotz`; the test skips cleanly where no interpreter is present).

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
  extensions as `.granule`.

### Documentation policy

When a change affects anything the public-facing documentation describes, the
docs are updated in the same step. New conventions are recorded here as they
are introduced.

## In progress: B4 — Cosmos compiled by the compiler

The parser, turn loop, and standard verbs, written in Arcturus and compiled
together with the game. Done-test: both example games playable start to finish
on Frotz. Decisions settled: parser/scope/dispatch/loop/verbs live in Arcturus,
with the compiler providing only low-level intrinsics; the parser keeps a
language seam so a language pack can override grammar logic; the verb set for
B4 is what the two games exercise (the full set rounds out in B6).

Subgoals (each with its own done-test; the story file is handed off to run on
Frotz at each runnable step):

- [x] B4.1 - routines, locals, stack, CALL (the instruction assembler)
- [x] B4.2 - expressions, control flow, and the statement set
- [x] B4.3 - the object table (attributes, properties, tree, short names)
- [x] B4.4 - the dictionary and input tokenizing
- B4.5 - Cosmos in Arcturus (staged):
  - [x] B4.5a - compile all handlers and blocks to routines
  - [x] B4.5b - dispatch (Arcturus dispatcher + compiler-wired handlers)
  - [x] B4.5c - scope and light
  - [x] B4.5d - the parser
  - [ ] B4.5e - turn loop + standard verbs + banner
- [ ] B4.6 - integration, DCE-friendly structure, docs

B4.5 architecture (settled): the compiler provides reserved intrinsic built-ins
that lower to opcodes (read_line, peek/poke, parse-buffer access); dispatch is
model B (the compiler wires per-object/kind handler routines and Cosmos's
Arcturus dispatcher walks the chain, handlers returning 1 = handled / 0 =
continue); arcc auto-includes the bundled Cosmos unless an author forks a file.

### B4.5b work log (detailed, for resuming mid-stage)

Four pieces; the Frotz hand-off is at piece 4 (driven dispatch). Status:

- [x] **Piece 1 - intrinsic built-ins** (committed). `lower.INTRINSICS` recognizes
  reserved calls and emits opcodes: `read_line` (aread), `peek_byte/word`,
  `poke_byte/word`, `word_count/word_dict/word_len/word_pos` (parse-buffer
  accessors), `call_handler(addr, action)` (call-by-address). Buffer-layout
  constants live in `storyfile` (TEXT_BUFFER_ADDR=544, PARSE_BUFFER_ADDR=606).
- [x] **Piece 2 - react routines + react-property wiring** (committed). As built:
  - `codegen._action_numbers` is the deterministic action->int map (sorted
    world.actions + `other`); the parser (B4.5d) reuses it.
  - `codegen._react_handlers` selects an object's pattern-less verb-action
    own-handlers (excluding events start/enter/each_turn and `other`; operand
    patterns / free rules / kind chains deferred to B4.5d/e).
  - `codegen.gen_react_routines` emits `react_<objname>(action)` (local 1 = the
    action number): a `je`-chain on the action that calls the handler routine(s)
    (the `h<n>` from B4.5a) and returns 1 the moment one returns 1, else 0.
  - `objects.REACT_PROP = 63` holds the react routine's packed address (user
    props capped at 62). build_layout takes `react_objects`; objects.py emits the
    react property (first, descending order) with a routine fixup in
    `layout.routine_fixups`; build_story patches it via the link packed map.
  - Verified on Frotz (tests/test_react.py): a harness reads object.react with
    get_prop(63) and call_handlers it - pull runs the body (1), pull again hits
    the stop guard (1), examine has no handler (0).
- [x] **Piece 3 - Cosmos-compilation pipeline** (committed). cosmos.py loads
  cosmos/*.prelude (or the embedded copies in the single-file arcc) and
  combined_program prepends their decls to the game's; the CLI compiles game +
  Cosmos by default (--no-cosmos opts out). amalgamate embeds the .prelude
  sources. cosmos/core.prelude is a minimal marker for now; prelude.py still
  seeds the standard kinds/properties until they move into Cosmos source.
- [x] **Piece 4 - Arcturus dispatcher** (committed). cosmos/dispatch.prelude
  walks noun.react -> here.react (free rules + default join in B4.5e) via the
  handler_of + call_handler intrinsics. Done-test on Frotz: dispatch(pull) with
  noun = red/blue routes to each object's own handler ("Red pulled." /
  "Blue pulled."). B4.5b complete.

### B4.5c work log (done, committed)

Scope and light. Three sub-steps:
- `for each x in <object>` lowers to a get_child / get_sibling loop (lower.py
  `_for_each`); the loop var is object-typed (`ctx.object_locals`) so `say`
  prints names. List iteration and `for each ... of <kind>` are still deferred.
- Kinds-as-attributes: each kind gets an attribute, set on every instance in its
  chain (`objects.Layout.kind_attr`); `obj is <kind>` resolves to `IS_KIND`
  (sema) and lowers to `test_attr` (lower `_kind_test`). docs/01 section 9 done.
- `cosmos/scope.prelude`: `is_lit`, `in_scope`, `visible`, `reachable` in
  Arcturus; new `parent_of` intrinsic (get_parent). tests/test_scope.py.

### B4.5d work log (done, committed)

The parser, split along the language seam.
- `objects.py`: `words` is now a numbered property holding an array of
  dictionary addresses (two-byte size form; `layout.word_fixups` backpatched in
  build_story with the absolute dict address). Only `name` stays special.
- `dictionary.build(world, action_numbers)`: single-word verb entries set data
  byte 0 bit 7 (verb flag) and data byte 1 (action number). Multi-word verbs
  ("take off") deferred to B4.5e.
- assembler: `get_prop_addr` / `get_prop_len`. lower intrinsics: `words_addr`,
  `words_count` (use `layout.prop_number["words"]`).
- `cosmos/parser.prelude` (skeleton, language-agnostic): `parse()` reads a line,
  resolves the verb, resolves the noun, sets the noun global, returns the action.
- `cosmos/english.prelude` (SWAPPABLE language layer): `resolve_verb`,
  `has_word`/`find_word`, `match_noun`. tests/test_parse_command.py.

### B4.5e plan (NEXT - turn loop, standard verbs, banner; the B4 done-test)

Goal: both example games (brass-lantern, cloak-of-darkness) playable start to
finish on Frotz.

- Turn loop (`cosmos/loop.prelude`, called from the entry instead of the current
  banner+on-start main): describe the room on entry (name, desc via print_paddr,
  list contents, fire `on enter`); print the prompt; `parse()`; `dispatch(action)`;
  `on after`; fire active `on each_turn` (room + in-scope) subject to `when`;
  scheduled events; increment `turns`; if `finish` ended the game, print and stop.
- Events fired by the loop, not verb dispatch: `on start`, `on enter`,
  `on each_turn`. The compiler must wire these (event routines the loop calls,
  e.g. per-room enter/each_turn). `on start` currently runs inside main - move it
  into the loop's startup.
- Dispatch chain completion: dispatch.prelude currently does noun.react ->
  here.react. B4.5e adds free-standing rules and the Cosmos default handlers to
  the chain. The Cosmos default verbs (take/drop/examine/...) are themselves
  handlers; decide how defaults plug in (likely a per-action default routine the
  dispatcher calls last, or Cosmos `on <verb>` free rules).
- Standard verbs the two games need (Cosmos Arcturus + defaults + messages):
  look, examine (x/read), take (get), drop, put-on (hang), wear, take_off,
  inventory, go (+ `on go <direction>` operand-pattern dispatch, `on go other`,
  directions as room properties read via here.(dir) -> needs DynDot lowering,
  still deferred), switch_on/off, pull. Multi-word verbs (take off, switch on)
  and two-noun grammar + prepositions (put noun on noun) get wired here.
- Banner: move into Cosmos (`cosmos/banner.prelude`), reading the game metadata.
  The compiler still injects metadata; Cosmos declares its own version for the
  banner. The provisional compiler banner (`codegen.banner_text`) retires.
- MESSAGES ARE SWAPPABLE (decided with Stefan): do NOT inline `say "Taken."` in
  verb code. Verbs reference messages by id/block in the English layer (e.g.
  `msg_taken()`), and the English strings live in the swappable layer alongside
  the parser routines + standard vocabulary, so `summon.language "Spanish"`
  swaps parser logic + vocabulary + messages in one move. Verb LOGIC stays
  language-agnostic; verb TEXT lives in the swappable layer.
- Likely still-needed compiler work for B4.5e: DynDot lowering (here.(dir)) for
  directions; operand-pattern dispatch (`on go north`, `on put x in y`) so react
  routines guard on the matched noun/second/direction; two-noun grammar in the
  parser (second noun + prepositions); contents-listing.
- Done-test: both games playable on Frotz, handed to Stefan. This is also the B4
  done-test (B4.5 and B4 complete together).

### Resume state (key facts to recall after a context reset)

- Milestones B0-B3 done; B4.5a-d done; **B4.5e is next** (above). HEAD is the
  B4.5d commit; working tree clean except this PROGRESS update.
- Test count ~162 (`python3 -m pytest`); Frotz tests use `dfrotz` and skip if
  absent. Run tests with `python3 -m pytest` (Python 3.14 default).
- Cosmos is real source under `cosmos/`: core, dispatch, scope, parser, english
  (.prelude). `arcc` auto-includes them (`cosmos.combined_program`); the
  standalone build embeds them (`tools/amalgamate.py` sets `cosmos._EMBEDDED`).
  prelude.py still SEEDS the standard kinds/properties (provisional); they move
  into Cosmos source incrementally.
- Compiler intrinsics (lower.INTRINSICS, lower to opcodes): read_line, peek_byte,
  peek_word, poke_byte, poke_word, word_count, word_dict, word_len, word_pos,
  call_handler, handler_of, parent_of, words_addr, words_count.
- Dispatch model B: `codegen.gen_react_routines` -> react_<obj>(action); react
  address in property 63 (`objects.REACT_PROP`); `cosmos/dispatch.prelude` calls
  it via handler_of + call_handler. Action numbers: `codegen._action_numbers`.
- Driven-harness test pattern (tests/test_dispatch.py, test_scope.py,
  test_parse_command.py): `analyze(cosmos.combined_program(parse(GAME)))`, then
  `build_routines` + `gen_react_routines`, then a hand-assembled `__main__`
  Routine that sets globals via `store Const(gmap[name]) Const(value)` and calls
  Cosmos blocks `blk_<name>`, then `build_story`. dfrotz fed input via stdin.
- Standing rules (see memory): never set git identity (plain `git commit`,
  ByteProject <stefan@8-bit.info>); interpreter verification is Stefan's hand-off
  (build the .z5, give size + run command, PAUSE, don't advance until he's run
  it); comment the arcane code for humans; keep public docs in sync; commit each
  sub-step with a clear message.

## Next: B5

The size pass: dead-code elimination, the arcabbr abbreviation pipeline, and
codegen tightening. Target: a representative game at or (per the project bar)
under its PunyInform-equivalent size.
