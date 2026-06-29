# Arcturus progress

A living log of where the project stands, maintained as work proceeds. The
authoritative plan is `docs/00-roadmap.md` (milestones B0 to B8); this file
tracks status against it and records decisions made during implementation.

Last updated: 2026-06-28.

## Status at a glance

| Milestone | Description | Status |
|-----------|-------------|--------|
| B0 | Project scaffold and VS Code extension | done |
| B1 | Lexer and parser producing an AST, with unit tests | done |
| B2 | Semantic analysis and the world-model IR | done |
| B3 | Z-machine backend MVP (smallest valid story file) | done |
| B4 | Cosmos compiled: parser, turn loop, standard verbs | done |
| B5 | Feature-complete library and a fair benchmark | in progress |
| B6 | Size pass (DCE, abbreviations, codegen) | pending |
| B7 | Language packs (Spanish, German) | pending |
| B8 | The reference interpreter, Actaea | pending |
| B9 | arc_image on modern systems (PNG) | pending |
| B10 | arc_image on retro systems | pending |
| B11 | Port Ghosts of Blackwood Manor (text) | pending |
| B12 | Port The Curse of Rabenstein (from DAAD) | pending |

Roadmap restructured 2026-06-28, renumbered 2026-06-29 (docs/00 section 7):
feature-complete library (B5) comes BEFORE the size pass (B6) so the PunyInform
benchmark is fair; then language packs (B7 Spanish + German), the Actaea
interpreter (B8), arc_image (B9 modern, B10 retro), and porting two games (B11
Ghosts, B12 Rabenstein). "Write Hibernated 3" is dropped as the project goal.
See memory [[roadmap-milestones]].

B4 is done: both example games (The Brass Lantern and Cloak of Darkness) compile
with the standalone arcc and are winnable start to finish on Frotz
(tests/test_examples.py). The full B4 work log is below; B5 progress is in the
"In progress: B5" section near the end of this file.

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
  - [x] B4.5e - turn loop + standard verbs + banner (both games winnable on Frotz)
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

### B4.5e plan (IN PROGRESS - turn loop, standard verbs, banner; the B4 done-test)

Goal: both example games (brass-lantern, cloak-of-darkness) playable start to
finish on Frotz.

Decisions (Stefan, this session):
- Multi-word verbs ("switch on", "take off") = PARTICLE in the language layer:
  the English layer recognizes a known particle after the verb and selects the
  combined action. Stays swappable.
- Frotz hand-off = ONCE at the end (B4.5e.6); I verify each sub-step myself.
- GRAINS / scenery: for an action a grain does NOT handle (e.g. "take
  chandelier" when only `examine` is defined), the library prints a default,
  `msg_scenery()` = "Just some scenery. Don't worry about it." This is the
  grain's catch-all, in the swappable English layer. Lands in B4.5e.5.

Sub-step order (each ends green; one Frotz hand-off at .6):
.1 turn-loop spine + banner + on start + each_turn + room description + look  [DONE]
.2 movement (go + directions; DynDot here.(dir); on go <dir>; cant-go default)  [DONE]
.3 object verbs take/drop/inventory/examine + defaults + swappable messages  [DONE]
.4 multi-word (particle) + two-noun (put on/hang) + wear/take_off  [DONE - 4a/4b/4c]
.5 scenery grains (examine "string") + msg_scenery default + on enter wiring  [DONE]
.6 integrate both games end to end; B4 done-test on Frotz; hand off

Implementation notes discovered (B4.5e.1):
- Globals default to 0; nothing initializes here/player. Startup must set the
  here global = start room obj#, player global = player obj#, and player's tree
  parent = start room. Plan: initialize these in build_story / objmod.
- Events fire via react: add start/enter/each_turn to _action_numbers; include
  event handlers in react routines (with `when` guard support); emit
  react_free(action) for free handlers (on start, free each_turn, later
  defaults). Loop fires them via intrinsics (fire_start/fire_enter/fire_each_turn).
- `when` guard not yet compiled: a handler with `when` must skip (return 0) when
  the guard is false. Add to _compile_handler.
- __main__ becomes a thin shim: print banner, call blk_run_game (the loop) when
  Cosmos provides it; else old behavior (banner + on start) for unit tests.
- Pattern handlers (on go north, on examine "string") still skipped in react -
  operand-pattern dispatch is .2/.5 work.

B4.5e.1 done (committed). What landed:
- worldmodel.action_numbers + EVENT_NAMES (shared by codegen and lower); events
  start/enter/each_turn share the action-number space with verbs.
- react routines now include event handlers; `when` guards compiled (skip ->
  return 0); react_free(action) bundles free rules (always emitted).
- __main__ is a shim: banner, then call blk_run_game when Cosmos provides it.
- build_story bootstraps here = start room, player = player object.
- cosmos/loop.prelude (run_game, fire_turn, describe_room), cosmos/verbs.prelude
  (look + on look default), dispatch.prelude calls run_free last.
- New intrinsics: run_free, ev_start/ev_enter/ev_each_turn, show (no-newline
  print), print_name, tick (advance turns), desc_addr (skip missing desc).
- BUG FIXED (latent, important): the call-statement discard used
  `pull Variable(STACK)`, which is an INDIRECT pull (pops the var number, then
  the value = two pops) -> stack underflow. Now discards into a scratch temp.
  Also read_line now clears text-buffer byte 1 each read (v5 "inconsistent
  input buffer"). tests/test_loop.py. 164 tests pass.

B4.5e.2 done (committed). Movement:
- `way` global (chosen direction's property number; builtin, writable). DynDot
  here.(way) lowers to get_prop with a variable property operand. set_here
  intrinsic (here is read-only to authors).
- Direction words (north/n/.../in/out) added to the dictionary, flagged bit 6,
  data byte1 = go action, byte2 = the direction property number
  (dictionary._DIRECTION_WORDS, English -> language pack later). build_story
  passes dictionary.direction_props(layout).
- english.prelude find_direction (scans tokens for a direction word -> its prop);
  parser.prelude sets `way` each turn. verbs.prelude: go verb + default `on go`
  (follow the static exit, fire enter, reconcile here after a bounce, describe;
  else msg_cant_go / msg_no_direction). loop.prelude fire_enter block; run_game
  does `move player to here` at startup.
- Operand-pattern dispatch: `on go <direction>` handlers are now included in
  react, guarded by `way == <direction prop>` (codegen._is_dir_pattern;
  gen_react_routines/_gen_react take layout+gmap). Other operand patterns
  (noun/string) still deferred (.4/.5). Computed exits (block-valued directions,
  tier 2) and `on go other` (tier 4) deferred - examples do not use them.
- Verified on Frotz: brass north groped back to the hallway (enter bounce),
  south = can't go; cloak north = the foyer override, west = real exit.
  tests/test_movement.py. 166 tests pass.

B4.5e.3 done (committed). Object verbs:
- verbs.prelude: take/get/carry, drop, examine/x, inventory/i/inv with default
  free handlers; each runs last so an object handler (ruby on take, cloak on
  drop) overrides it. Messages live in english.prelude (msg_taken, msg_dropped,
  msg_fixed, msg_cant_see, msg_not_holding, msg_nothing_special, msg_carrying,
  msg_empty_handed, msg_dark_room) plus list_held.
- describe_room now checks is_lit(): a dark room prints msg_dark_room instead of
  its contents.
- ROOMS ARE LIT BY DEFAULT: the room standard kind seeds `lit` true
  (sema._collect), and a dark room overrides with `lit false`. (Updated
  tests/test_scope.py: its dark room now declares `lit false`.)
- Verified on Frotz: cloak examine/inventory; the cloak's on drop overrides the
  default; the dark bar shows "pitch dark" and its on each_turn fires. brass
  take/examine/inventory/drop all work. tests/test_verbs.py. 168 tests pass.
  (The brass walkthrough still needs "switch on" - a multi-word verb, B4.5e.4.)

B4.5e.4a done (committed 2f8d019). Multi-word verbs via particles:
- dictionary: particle words (on/off) flagged bit 5 with an id (_PARTICLE_WORDS;
  up/down/in/out stay direction words). action_id("name") intrinsic.
- english.prelude resolve_verb splits verb (128) / direction (64); find_particle
  + compound remap (switch+off -> switch_off, take+off -> take_off).
- verbs.prelude: switch/turn, wear/don, remove/doff + defaults. THE BRASS LANTERN
  PLAYS END TO END. tests/test_particle.py.

B4.5e.4b done (committed e1a5d10). Vocabulary + hidden:
- objects.object_words: explicit words + name words (rooms: explicit only); the
  object table emits a words array for every object; dictionary.collect_vocab
  uses the same merge. A named-but-wordless object (brass pedestal, lever) is now
  matchable.
- describe_room skips hidden/concealed; parser find_word skips hidden. The ruby
  is unseeable/untakeable until the lever clears its hidden flag.
- Brass plays to its full walkthrough. tests/test_vocab_scope.py. 172 tests pass.

REMAINING for B4.5e: two-noun grammar (put noun on noun / "hang cloak on hook" -
the Cloak win), then .5 grains (examine "chandeliers" + msg_scenery "Just some
scenery. Don't worry about it."), then .6 both games end to end (B4 done-test,
hand off). Brass is fully playable; Cloak needs the two-noun put-on.

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

## In progress: B5 - feature-complete library and a fair benchmark

Goal: the full standard verb set at PunyInform parity, the meta verbs, a fresh
standard message set, and the summonable granules, so the eventual size
comparison (B6) is honest. Memory: [[cosmos-distribution-and-hacking]],
[[punyinform-reference]], [[no-em-dashes-ever]], [[library-paragraph-breaks]].

DONE in B5 (committed):
- Override-by-block (91c95f6): a game or granule block beats a Cosmos library
  block of the same name (ast.BlockDecl.origin / wm.Block.origin; sema._collect;
  cosmos.combined_program tags library blocks). The author's way to reskin a
  message without unpacking the library. tests/test_override.py.
- --extract-library DIR and --eject-language [DIR] (e9d50ab): write the bundled
  library (or just english.prelude) out for hacking; compile against it with -L.
  tests/test_cli_extract.py. README documents them (aec6491).
- intro property + moved attribute (2a9faff): Inform's `initial`; an object shows
  its intro text in a room until taken (sets `moved`), static objects keep it.
  describe_room shows intro vs lists; take sets moved. tests/test_intro.py.
- Scenery + grains unified on msg_scenery (2cd623d): dropped msg_take_scenery;
  take of a scenery object gives the grain line; describe_room skips scenery from
  the listing (still examinable).
- The blessed message set in english.prelude (db8f580): all of docs/message-set.md
  in the agreed voice (warm-to-witty), using ${the noun}/${The noun}/${the
  second}. The wording is Stefan's; redlines applied (da473a2).
- Sensory + flavor verbs + the animate model (71c3fc4): touch, smell, taste,
  listen, eat, drink, attack, kiss, push, pull, turn, climb, read, talk, jump,
  wait, sing. New `animate` attribute, set by the person kind (sema seeds it like
  room+lit). talk to animate -> msg_no_talk; to an object -> msg_only_animate.
  `turn` is its own verb now; compound() is base-aware (switch/turn +on/off,
  take +off; everything else ignores particles so "put X on Y" stays put).
  tests/test_flavor.py.
- docs: 03-compiler-pipeline.md (ec53b55), verb-set.md (the S/E split, Stefan's),
  message-set.md (the blessed wording). docs/01 documents intro.

VERB SET PLAN: docs/verb-set.md has Stefan's standard/extended (S/E) split. The
sensory verbs stay Standard. ask/tell/answer/ask_for/shout are EXTENDED (the
Infocom topic system); talk stays Standard. kiss/sing/xyzzy Standard;
search/look_under/throw Extended. Look modes (verbose/brief/superbrief), notify,
sorry, and mild oaths are DROPPED entirely (full descriptions always). oops kept.

DONE in B5 (continued):
- Functional verbs with real state (B5.4c): open/close (openable; refuse locked;
  already-open/shut), lock/unlock (lockable + matching key; "lock noun with noun"
  puts the key in second, "lock noun" falls back to noun.key; close-first;
  wrong-key), enter/exit (onto a supporter / into an open container; exit back to
  the room; "not inside anything" in the open), give/show (need an animate
  recipient: "give noun to noun" -> noun=gift, second=recipient; non-animate gets
  msg_only_animate), insert (a sibling of put into an open container). Added
  `insert` to prelude._STD_ACTIONS. Messages were already in english.prelude.
  tests/test_functional.py (open/close/lock/unlock/insert/give/show/enter/exit on
  Frotz).
- Two-noun slot binding by position (folded into B5.4c): resolve_two_nouns now
  binds the first noun phrase (before the preposition) to `noun` and the phrase
  after it to `second`, instead of "first in-scope match wins, next distinct is
  second". This closes a real gap: with the gift out of scope, "give coin to
  guard" no longer slid the guard into the noun slot; the gift stays unresolved
  and the verb reports msg_cant_see. New dictionary preposition flag (0x08,
  dictionary._PREPOSITION_FLAG / _preposition_words) marks the grammar's literal
  "to"/"with"; on/in already carry a particle/direction flag, and the parser's
  is_separator treats any flagged word as the phrase boundary. tests/
  test_functional.py::test_two_noun_binds_by_position_on_frotz. (`after` is a
  reserved word - the boundary local is `past_prep`.)

DONE in B5 (continued):
- B5.4d.1 - turn control + parser can't-see + the no-opcode meta verbs: a meta
  action sets the meta_turn global so the loop skips the per-turn pulse and the
  turn count (fixes a cancelled quit costing a turn); the parser sets parse_fault
  when the player names an object out of scope (any unflagged dictionary word that
  no in-scope object answers to), and the loop reports msg_cant_see and skips the
  turn. This also closes the give/show recipient gap (the symmetric half of the
  position-binding fix): "give coin to wizard" with the wizard elsewhere now says
  can't-see instead of the only-animate nudge. Verbs: score (msg_score, prints
  ${score}/${max_score} via print_num), restart (msg_confirm_restart + yes_no +
  do_restart, the new restart 0OP opcode), xyzzy (msg_xyzzy; a normal turn, not
  meta). New globals parse_fault/meta_turn (codegen._BUILTIN_GLOBALS +
  prelude._BUILTINS). yes_no() factored out of confirm_quit and shared with
  restart. tests/test_meta.py. Grammar-named actions are auto-added to
  world.actions, so meta verbs need no _STD_ACTIONS entry.

- B5.4d.2 - save / restore / undo on the v5 EXT opcodes. Added the EXT
  instruction form to the assembler (0xBE + opcode byte + VAR-style types/operands
  via the new _encode_var_form; opcodes save/restore/save_undo/restore_undo) and
  the intrinsics do_save/do_restore/do_save_undo/do_restore_undo (each returns the
  opcode result: 0 fail, 1 saved, 2 resumed). The turn loop now factors each turn
  into run_turn(act): undo is intercepted before dispatch (do_undo -> restore_undo),
  and every non-undo turn takes an undo checkpoint (do_save_undo) first, so a later
  undo rewinds to just before the previous command (the PunyInform model: the undo
  command itself takes no checkpoint, and a save_undo result of 2 means the machine
  just resumed via restore_undo -> msg_undone + redescribe). save mirrors this: a
  successful restore resumes at the do_save point with result 2, so the save
  handler redescribes the room; the restore handler is reached only on failure.
  Messages msg_saved/save_failed/restore_failed/undone/cant_undo added. Verified
  headless on dfrotz incl. a full save/restore round-trip (dfrotz takes the save
  filename from stdin). tests/test_meta.py.

- B5.4d.3a - again: the turn loop remembers the previous non-meta command's
  resolved operands (last_act/last_noun/last_second/last_way/last_grain globals)
  and "again"/"g" replays it by restoring those and falling through to dispatch
  (intercepted in run_turn before dispatch, like undo; meta commands are not
  remembered). msg_nothing_again when there is nothing yet. tests/test_meta.py.

- B5.4d.3b - oops (full, committed): corrects the previous command's misspelled
  word. Cleaner than text-buffer surgery: the resolvers read only the parse
  buffer's dictionary addresses, so oops snapshots the failed command's parse
  buffer (note_oops, into a new reserved OOPS_PARSE region after the parse buffer;
  storyfile.OOPS_PARSE_ADDR), records the first unrecognized word's index
  (oops_word/oops_ready globals), and on "oops X" patches that word's dict-address
  slot with X's and re-resolves (fix_oops), returning the corrected action for
  run_turn to dispatch. No @tokenise needed. New intrinsics parse_addr/oops_addr;
  copy_bytes util in parser.prelude; msg_cant_oops. resolve_objects now resets
  parse_fault (fix_oops reuses it). tests/test_meta.py (typo corrected; nothing to
  correct). B5.4d COMPLETE: score, save, restore, restart, undo, again, oops,
  xyzzy, quit-no-tick, parser can't-see.
- oops now corrects a mistyped VERB too, not just a noun. note_oops scans from
  word 0, and the note_oops call moved from run_turn into the run_game loop so it
  also fires on the unknown-verb path (a bad verb returns act 0 and never reaches
  run_turn). oops takes a single replacement word ("oops take", not "oops take
  coin"), and must immediately follow the mistyped line. tests/test_meta.py
  (misspelled-verb correction).

ROADMAP RENUMBER (2026-06-29, Stefan): language packs become their own milestone
B7 (Spanish + German), pushing the rest down one: B8 Actaea, B9 arc_image modern,
B10 arc_image retro, B11 Ghosts, B12 Rabenstein. docs/00, README, CLAUDE.md and
[[roadmap-milestones]] updated to match.

BANNER SPACING FIX (2026-06-29): the opening screen showed TWO blank lines between
the banner and the first text (the banner string hardcoded a trailing blank AND
describe_room requested a par; dfrotz collapsed it but interactive frotz showed
both). Fixed by letting the paragraph model own it: banner_text ends on a single
\n, and run_game does par() before run_free(ev_start), collapsed with
describe_room's par -> exactly one blank, whether or not an `on start` prints.

GRANULE EXAMPLES (Stefan): each shipped granule gets a showcase game under
examples/granules/ (verbose-exits.storyarc is the first). These are demo/teaching
games, kept apart from the two conformance anchors (brass-lantern, cloak) which
stay in examples/.

REMAINING in B5 - the granules, built and tested one at a time (B5.5), then the
reference doc (B5.6). Full granule set settled with Stefan:
- B5.5a DONE (committed): the summon LOADER. cosmos.combined_program now takes
  lib_dirs + story_dir; _load_granules resolves every summon the game makes
  (transitively - a granule may summon another), parses each once, tags its
  BlockDecls origin "granule" (so it beats library, yields to game), and inserts
  them between library and game. Feature summons (summon.x) resolve to a bundled
  x.granule via granule_sources(); file summons ("path.granule") resolve story-dir
  then -L then cwd. language/abbreviations are recognized but not loaded as runtime
  blocks (B7/B6). Missing file or unknown feature is an ArcError. amalgamate now
  embeds .granule too (cosmos._bundled_sources filters _EMBEDDED by suffix). CLI
  passes its -L + the story dir. Unsummoned granules are never read, so never
  ship. tests/test_summon.py (override wins on Frotz; unknown-feature and
  missing-file errors).
- B5.5b: extendedverbs. NOT trivial - it carries the Infocom-style ask/tell/
  answer TOPIC conversation system plus search/look_under/throw etc. (the E side
  of docs/verb-set.md). The topic-driven conversation path lives here.
- B5.5c DONE (committed): verbose_exits. The granule overrides msg_cant_go to
  list the room's live exits ("You can only go north or east from here.") - no
  `on go other` needed after all, overriding the one message suffices. Three new
  intrinsics surface the compiler's existing direction data: exits_count(),
  exit_prop(i), exit_name(i) (lower.exit_directions gives the shared canonical
  order). exit_prop/exit_name are backed by two je-chain routines codegen emits
  ONLY when referenced (_references_routine gate in generate + gen_exit_routines),
  so an unsummoned verbose_exits adds zero bytes - proven: brass/cloak sizes
  unchanged (11120/11616). The granule reads here.(exit_prop(i)) via DynDot and
  keeps all phrasing in Cosmos (translatable). Heavily commented as a teaching
  example. tests/test_verbose_exits.py (lists exits on Frotz; default untouched
  without the summon).
- B5.5d: statusline. The window opcodes (split_window/set_window/set_cursor/
  set_text_style) - the start of the screen model, reused by conversations and
  later Actaea/B8.
- B5.5e: conversations. The MENU talk system (talk_menu equivalent): TALK TO
  <animate> paints a topic menu in the UPPER window (needs statusline's window
  work first), topics enabled/disabled from code by milestone/location. Puny's
  talk_menu setup is a nightmare; ours must be syntactic sugar. DESIGN the
  authoring surface WITH Stefan before coding. Non-trivial.
- B5.5f: debug. Testing verbs (tree, scope, teleport, fetch-distant-object, set
  prop, show state). NO release-exclude switch - opt-in via summon is the
  exclusion. Arcturus-named primaries with Inform synonyms (e.g. fetch/purloin,
  warp/gonear, inspect/showobj). Lock the names when building.
- B5.6: finalize the message/verb reference doc (docs/05) from message-set.md +
  verb-set.md once the set is complete. ALSO (Stefan, 2026-06-29): document every
  shipped granule for authors - how to summon it and what it does - so the
  summonable features are discoverable. Likely a dedicated granule reference in
  docs (and a README pointer), covering extendedverbs, statusline, verbose_exits,
  conversations, debug (and noting language/abbreviations as B7/B6). Reconcile
  docs/01 section 13 and docs/02 section 14 with what actually shipped.

ABBREVIATIONS (B6, before any size test; a compiler feature, not a runtime
granule): the compiler bakes in a standard abbreviation set (Inform's ceiling is
96 table entries) used by default. A `--make-abbreviations <file.storyarc>` flag
reads the story's strings, resolves the granules it summons (library + user
paths), pools all those strings, computes an optimized set, and writes ONE
abbreviations.granule in Arcturus syntax (declarations the compiler parses, so it
lexes like everything else and the VS Code extension highlights it). The author
summons it; on recompile the encoder intercepts that summon as compile-time data
(not runtime blocks) and uses it instead of the baked-in set. Two-pass flow.
Saner than zabbrv (no Inform transcript). docs/01 section 13 wording to be
reconciled when built.

KEY FACTS for resume:
- Verb pattern: declare `verb "x", "syn" \n x noun`, then a free `on x` default
  handler that speaks msg_x (noun-requiring ones check `if noun is nothing:
  msg_cant_see; stop`). Object/room handlers override via most-specific-wins
  (noun -> room -> free default). Defaults live in cosmos/verbs.prelude; messages
  in cosmos/english.prelude as overridable msg_* blocks.
- Sizes today (pre-DCE, bloated by ~70 message + ~45 verb routines, all shipped
  until B6 DCE): brass ~9.5K, cloak ~10K. Still far under Puny's 27K for Cloak.
- 218 tests; both example games still win. Run python3 -m pytest. Rebuild arcc
  with python3 tools/amalgamate.py build/arcc; rebuild the example .z5 via
  build/arcc after any cosmos/ change. Throwaway test .z5 go to the scratchpad,
  not build/ (build/ holds only arcc + the two example games).
- HARD RULE: never output em dashes anywhere ([[no-em-dashes-ever]]). Commit with
  git commit -F /dev/stdin <<'EOF' (heredoc) - backticks in -m are eaten by zsh.

## Later: B6 size pass

Dead-code elimination (unused Cosmos verbs/messages/properties never reach the
file), the arcabbr abbreviation pipeline, and codegen tightening. Target: a
representative game strictly under its PunyInform-equivalent size (Cloak is 27K
in Puny). Measured with the full library in place. See [[size-benchmark-puny]].
