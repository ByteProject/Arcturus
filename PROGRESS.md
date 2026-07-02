# Arcturus progress

A living log of where the project stands, maintained as work proceeds. The
authoritative plan is `docs/00-roadmap.md` (milestones B0 to B13); this file
tracks status against it and records decisions made during implementation.

Last updated: 2026-07-02.

Model handover: `HANDOVER.md` (repo root) is a holistic orientation written at
the switch to Anthropic's Fable model, with an assessment task to run before B8.
Read it alongside this log.

## Status at a glance

| Milestone | Description | Status |
|-----------|-------------|--------|
| B0 | Project scaffold and VS Code extension | done |
| B1 | Lexer and parser producing an AST, with unit tests | done |
| B2 | Semantic analysis and the world-model IR | done |
| B3 | Z-machine backend MVP (smallest valid story file) | done |
| B4 | Cosmos compiled: parser, turn loop, standard verbs | done |
| B5 | Feature-complete library and a fair benchmark | done |
| B6 | Size pass (DCE, abbreviations, dense codegen) | done |
| B7 | Language packs (Spanish, German) | done (native review pending) |
| B8 | Port Hibernated 2 (first full game, maturity milestone) | pending |
| B9 | Port Ghosts of Blackwood Manor (text) | pending |
| B10 | The reference interpreter, Actaea | pending |
| B11 | arc_image on modern systems (PNG) | pending |
| B12 | arc_image on retro systems | pending |
| B13 | Port The Curse of Rabenstein (from DAAD) | pending |

Roadmap restructured 2026-06-28, renumbered 2026-06-29, and again 2026-07-01
(docs/00 section 7): the feature-complete library (B5) comes before the size
pass (B6) so the PunyInform benchmark is fair; then language packs (B7). Real
games are now ported before the interpreter and graphics, so the language stays
malleable while bugs are cheap: Hibernated 2 (B8, the maturity milestone) and
Ghosts of Blackwood Manor (B9), then the Actaea interpreter (B10), arc_image
(B11 modern, B12 retro), and The Curse of Rabenstein (B13). Three game ports are
the proving ground; "write Hibernated 3" is not a project goal. See memory
[[roadmap-milestones]].

Since B6, a round of language and library polish has landed (all committed, 252
tests pass): kinds and inheritance with kind-level handler dispatch and universal
kind defaults, the `character` kind (animate agents: people, animals, robots),
computed properties, daemons and timers, the container knowledge model with
lidless containers, doors that default openable and fixed, two-sided doors and
multi-room `spans` scenery (both pay-for-use, elided when unused), and `constant`
lowering. B7 is well along: the Spanish and German packs have both landed as
first passes (below), each pending native review.

>>> B7 UPDATE (2026-07-02): German landed <<<

The German pack (`cosmos/german.granule`, informal du) is complete as a first
pass and verified on Frotz. It needed two compiler seams beyond the Spanish ones,
both built and tested:
  - GENDER FROM THE ARTICLE. The author declares der/die/das on the object; sema
    (`prelude._GENDER_ARTICLES`, `_collect_members`) maps die->feminine,
    das->neuter, der->masculine (default). New standard attribute `neuter` beside
    `feminine`. Spanish's -a spelling guess is gated off for German
    (`objects._spelling_gender_language`, denylist `_NO_SPELLING_GENDER`), so a
    masculine -a noun stays masculine.
  - CASE AT THE CALL SITE. `${the:acc noun}` / `${a:dat noun}` pass a case as a
    third arg to art_the/art_a. Parsed by peeling article+`:case` off the interp
    source with a regex (`parser._ARTICLE_CASE_RE`), since the colon is not a
    lexer token; `ast.StringInterp.case`; `lower._CASE_NUMBERS` (nom0 acc1 dat2
    gen3). No tag -> two args, so an uninflected art_the is called exactly as
    before; English/Spanish untouched, zero size cost.
German art_the/art_a print the capital once (every definite article starts d,
every indefinite e) then the gender x case tail. Predicate adjectives do NOT
inflect in German ("die Kiste ist offen"), so unlike Spanish there are no
per-gender message variants. Example: `examples/beispiel-deutsch.storyarc`
("Das Gasthaus am Leuchtturm"). Docs: docs/01 s.16 (case tag), docs/02 s.14a
(der/die/das). 270 tests pass.

PARTICLE-WORDS SEAM (done, 2026-07-02): the particle words are no longer hardcoded
in the compiler. A `particle on "..."` / `particle off "..."` declaration lives in
the language layer (ast.ParticleDecl, parser.parse_particle, sema -> world.particles,
dictionary._particle_words + fixed _PARTICLE_IDS {on:1,off:2}). english.prelude
declares `particle on "on"` / `off "off"` (behaviour identical, just moved where the
old code comment said it belonged); Spanish declares none (dedicated verbs); German
declares `particle on "an", "ein"` / `off "aus", "ab"` with a base `verb "schalt",
"schalte"`, so "schalt die Lampe an", "... ein", "schalt an Lampe" (loose), plus the
joined einschalten/anmachen all route right (verified on Frotz, test_language). "an"
is both a particle and the give/show preposition; the any-tag-is-a-boundary rule in
is_separator handles the double duty.

SEPARABLE LOCK/UNLOCK (done, 2026-07-02): the natural German is the separable
"schliess die Tuer mit dem Schluessel auf/ab/zu", NOT verb-first entriegeln (which
is stiff; nobody says "Hast du die Haustuer verriegelt?"). Added two particle roles,
auf(3) and zu(4), to prelude._PARTICLE_ROLES (now {on:1,off:2,auf:3,zu:4}; shared by
dictionary and sema). The German base `verb "schliess","schließe",...` has grammar
close / lock noun mit noun / lock noun / unlock noun mit noun / unlock noun (first
line close = base action; _verb_arity takes the max so arity is 2), and compound()
maps close+auf -> unlock, close+zu/ab -> lock. "ab" is the switch-off particle AND
the lock particle; compound() keys on the base verb so it is unambiguous. Dedicated
entriegeln/verriegeln kept as one-verb synonyms. All of the user's forms verified on
Frotz (test_language.test_german_separable_lock_verbs). LIMIT: particle-before-noun
for a two-noun base ("schliess auf Tuer") misparses (the leading particle becomes
the phrase separator); the user's forms all put the particle last, so this is not a
requested form.

OPEN X WITH KEY (done, 2026-07-02, AGNOSTIC): "open the door with the key" now
unlocks a locked thing with the named key and then opens it, in one command. The
change is in the shared `on open` action (actions.prelude): if the noun is locked
and a `second` (key) was given, it checks second against noun.unseal_with, unlocks
(msg_unlocked), and falls through to open (msg_opened); a locked thing with no key
named is still refused, and a wrong key gives msg_wrong_key. Each pack's open verb
gained the two-noun grammar line so the key binds: English `open noun with noun`,
German `open noun mit noun`, Spanish `open noun con noun`. Verified on Frotz in all
three (EN Unlocked+Open, DE Aufgeschlossen+Geoeffnet, ES Abres+Abierta with gender
agreement), plus the wrong-key path. test_twonoun.test_open_with_key_unlocks_then_
opens. Common form (the user notes it is less common in English but valid there).

KNOWN FIRST-PASS LIMITS FOR NATIVE REVIEW (both packs): give/show use `an` for the
recipient (gib X an Y); typing the bare article "ein" in a two-noun command can
misparse since "ein" is a particle (rare; German IF players omit articles). Spanish
`salir` collides (get-out vs quit); quit is fin/terminar. Versions still arcc 0.6 /
Cosmos 0.9 in the banner; a bump is due when B7 closes.

>>> B7 HANDOVER CHECKPOINT (2026-07-02, written for compaction) <<<

WHERE WE ARE. B7 is language packs. The Spanish pack is COMPLETE and verified on
Frotz; German is the NEXT piece of B7 and has NOT been started. 268 tests pass
(`python3 -m pytest`). Working tree clean except untracked `actaea/` (ignore it).
The Spanish deliverable for native review is `build/posada.z5` (14836 bytes) +
`examples/ejemplo-espanol.storyarc`; Pablo Martinez is the native gatekeeper and
Stefan will hand it off. Versions NOT bumped this session (still arcc 0.6 / Cosmos
0.9 in the banner); a bump is due but was deferred, do it when B7 closes with German.

THE ARCHITECTURE (four seams, all built and reusable for German).
1. ACCENTS (arcturus/zstring.py). Accented chars map to the ZSCII default set
   (Standard 1.1 s.3.8.5, codes 155-223) via `_UNICODE_TO_ZSCII`, built from the
   69-char `_DEFAULT_ZSCII` string; `_char_to_zchars` does
   `z = _UNICODE_TO_ZSCII.get(c, ord(c))`. Anchor asserts pin ae=155, ss=161,
   a-acute=169, n-tilde=206, inverted-! =222, inverted-? =223. German ss/ae/oe/ue
   are ALREADY in this set (they anchor it) - no zstring change needed for German.
2. ARTICLES + GENDER (arcturus/objects.py + cosmos article blocks). `${the noun}`
   / `${a noun}` lower (arcturus/lower.py `_say_with_article`) to calls to the
   pack's `art_the(obj,cap)` / `art_a(obj,cap)` blocks, so a pack OWNS its article
   words and agreement. Spanish uses gender model A (AUTO): objects.py
   `_derive_feminine` sets the `feminine` attribute from the HEAD noun (first word
   of `name`) - ends in -a or a reliably-feminine suffix
   (`_SPANISH_FEMININE_SUFFIXES`: cion/sion/dad/tad/tud/umbre) => feminine; author
   declares `feminine` only for spelling-opaque exceptions (la llave). GERMAN NEEDS
   A DIFFERENT MODEL: three-way der/die/das with NO spelling rule, so it needs an
   explicit gender property (masculine/feminine/neuter) the author declares per
   object, NOT auto-derivation. That is the FIRST German design decision (mirrors
   how the Spanish tu/usted register was settled up front). See [[kind-model]] notes.
3. DIRECTIONS (cosmos `direction` declarations + arcturus/parser.py
   parse_direction). Direction PROPERTY names stay English in exits (`east puerta`);
   the pack's `direction` decls map the English property to the player's typed words
   (norte/sur/...). German: norden/sueden/osten/westen/... plus accentless siblings.
4. LANGUAGE SWAP (arcturus/cosmos.py). `summon.language "spanish"` DROPS
   english.prelude and loads `spanish.granule`. A pack self-identifies with a
   top-level `language "spanish"` marker (ast.LanguageDecl, parsed by
   parse_language_decl); combined_program validates the marker (else "not a language
   pack") and STRIPS it before sema. A plain `summon spanish.granule` is a compile
   error (guard in `_load_granules`: a granule carrying the marker tells you to use
   summon.language "<stem>"). `_resolve_language` finds `<code>.granule` in
   story_dir -> -L dirs -> bundled, so forks work.

THE LOCALIZATION SPLIT (the rule that governs everything). CODE identifiers stay
English; only PLAYER-FACING words/text localize. Author writes `east puerta` (exit
property English), grain writes `examine "mar"` (action name English), attributes
are `openable`/`feminine` (English). The player TYPES este/examinar; the game SHOWS
Spanish. German follows this verbatim.

THE 8-BIT TYPING RULE (never violate; memory [[never-strip-accents]]). Display is
ALWAYS accented (8-bit/Amiga/ST Z-machine interpreters render accents fully). But
every TYPEABLE word also carries a tilde-free sibling because 8-bit keyboards
cannot type accents: verbs `oir, oir-without-accent`; object `words lampara,
lampara-with-accent`. German: every verb/word with ss/ae/oe/ue needs an ASCII
sibling (oeffnen/o-umlaut-ffnen, schliessen with ss). NEVER ship an accent-stripped
game; that was a hard correction this session.

OTHER LOCKED FACTS FOR GERMAN.
- VERB -> ONE ACTION. A verb word maps to exactly one action (no overloading:
  abrir could not be both open+unlock). Spanish used dedicated trancar/destrancar
  for lock/unlock. German needs dedicated verbs for lock/unlock too.
- STRINGS ARE NOT FIRST-CLASS. You cannot pass a string literal to a block, so
  gender/number agreement is INLINED per message (`if noun is feminine ... else
  ...`) inside the granule, not factored into a helper. German's 3-way agreement
  will be more inlined branches; that is expected and fine.
- ABBREVIATIONS (arcturus/codegen.py `_abbreviations_for` / `_non_default_language`).
  The baked-in DEFAULT_ABBREVS is English-tuned; a non-English game gets NO default
  set (returns []), because English abbreviations cost bytes on foreign text. Authors
  run `--make-abbreviations` (language-aware, uses the translated combined_program).
  No per-language standard set is baked in. Same policy for German.
- PAY-FOR-USE. Article/gender/spans/door code is elided by the static-if fold
  (arcturus/lower.py `_if` + `_static_cond`) when a game does not use the feature
  (`any_named()`/`any_spans()`/`any_doors()` fold to layout flags). Keep German
  feature code behind the same guards.

WHAT TO BUILD FOR GERMAN (the mechanical checklist, mirrors spanish.granule).
Create `cosmos/german.granule` with: the `language "german"` marker; translated
verbs (each with an ASCII sibling for ss/ae/oe/ue); `direction` decls
(norden/sueden/osten/westen/nordosten/... + siblings); `art_the`/`art_a` reading a
three-way gender attribute (der/die/das, ein/eine/ein, plus case if we decide to -
DECIDE SCOPE with Stefan: nominative-only vs full case is a real question);
~90 translated messages with inline gender agreement; localized granule wording
(statusline Punkte/Zuege, conversations header). Then a full-featured German
example like `examples/beispiel-deutsch.storyarc` mirroring the Spanish one
(statusline + conversations + daemon + grains + spans + container + two-sided door +
character), rich natural accented German prose, at least one object showing the
`words ascii, accented` 8-bit pattern. Build a throwaway .z5 to the scratchpad to
verify on Frotz; hand the real artifact to Stefan for a native reviewer.

OPEN DECISIONS TO SETTLE WITH STEFAN BEFORE CODING GERMAN.
1. Register: formal Sie vs informal du (Spanish chose informal tu). ASK.
2. Case handling: nominative-only articles, or decline for accusative/dative in
   messages? IF messages ever say "you open THE box" in a case-marked slot this
   matters. Recommend nominative-only to start, note the limitation.
3. Gender declaration syntax: a single `gender` property with masculine/feminine/
   neuter, or reuse attributes. Recommend an explicit per-object declaration since
   there is no spelling rule.

KEY FILES (all current). arcturus/zstring.py (accents), arcturus/objects.py
(_derive_feminine, gender bit emit, _emit_spans), arcturus/lower.py
(_say_with_article, any_named, static-if fold), arcturus/cosmos.py (language
machinery: _language_choice/_resolve_language/_language_marker/combined_program/
_load_granules), arcturus/parser.py (parse_language_decl, parse_direction),
arcturus/ast.py (LanguageDecl, DirectionDecl, ObjectDecl.spans),
arcturus/codegen.py (_abbreviations_for, _non_default_language). Library:
cosmos/english.prelude (art_the/art_a, line_talk_*/msg_*/line_status_score, the 12
direction decls), cosmos/spanish.granule (the full model to copy), examples/
ejemplo-espanol.storyarc (the example to mirror). Docs: docs/02 section 14a
"Writing in another language" is the central reference for foreign-language authors
(read it before German - it states Spanish AND German are official/supported).

>>> B6 HANDOVER CHECKPOINT (2026-06-30, written for compaction) <<<

WHERE WE ARE. B5 is complete: the library is feature-complete and both example
games win on Frotz. 247 tests pass (`python3 -m pytest`). Versions bumped this
session: Cosmos 0.8, compiler 0.5. NEXT IS B6, the size pass, in three parts (do
them in this order): DCE, then abbreviations, then codegen tightening. Target: a
representative game strictly UNDER its PunyInform-equivalent size (Puny's Cloak is
27K, standard-only). [[size-benchmark-puny]]

WHAT LANDED IN B5 (this session, all committed). The whole topic/conversation
arc: the `topic` construct (docs/01 s.15) + runtime topic table + you/reply/say/
reveal/hide lowering; ask/tell topic dispatch in extendedverbs; the conversations
MENU granule (numbered list pinned in the upper window, statusline-aware, divider,
no residue, adaptive height); mutual exclusion (menu wins, ask/tell redirect via
menu_owns_talk). The debug granule (tree/scope/fetch/purloin/warp/gonear/inspect/
showobj) reaching out-of-scope objects through a reach_unscoped parser seam. The
give/show "To whom?" fix. The THREE-FORM summon model (summon.x = bundled always;
summon x.granule = story dir -> -L (absolute) -> bundled with a notice; summon
"path" = explicit file) + --extract-library now writes granules + --eject-granule.
Docs: docs/05-granules.md (new), the verb/message reference verified against the
library (docs/verb-set.md, docs/message-set.md), docs/01/02/03 and README synced.

THE B6 BASELINE (current sizes, pre-DCE, the full library is shipped into every
game): brass 12228, cloak 13084, statusline 11528, conversations 13492,
extended-verbs 15032, infocom-interrogation 17252.

B6 PART 1 - DCE: DONE (committed). codegen._prune_unreachable runs a whole-program
reachability sweep over the routine call graph right before build_story and drops
every routine the running story can never enter. Roots = __entry__ + every routine
the object/topic table names (layout.routine_fixups: react_<obj>, topic bodies,
when-guards) - these are called by ADDRESS from data, so a follow-the-calls sweep
would never see them; mark transitively over `call` fixups only. Sound: a kept
routine's call targets are kept (followed) and its data refs are roots (kept), so
the linker never dangles. SAVINGS (pre-abbrev): brass 12228->11892 (-336), cloak
13084->12752 (-332), statusline -332, conversations -368, extended-verbs -372,
interrogation -316. MODEST BY DESIGN: the standard verb set is always reachable via
react_free (JUMP/LISTEN work in every game, handler or not - the always-on baseline
the Puny comparison is measured against), so DCE only reclaims the genuinely-dead
tail (line_*/seam blocks, unused message blocks, uncalled pattern handlers). The
bulk size win is Part 2 (abbreviations). All 247 tests pass; both example
walkthroughs still win on Frotz (test_examples) and the topic/menu granule examples
verified by hand on dfrotz (ask/tell dispatch, the conversations menu, reveal/once,
the statusline coexistence all intact). docs/04 section 9 + docs/03 step 6 record it.

B6 PART 1 - DCE (the original plan, now done above; kept for the detail).
- THE GAP: codegen.build_routines (arcturus/codegen.py, `for blk in
  world.blocks.values()`) compiles EVERY block unconditionally. Most are dead in
  a given game (the ~70 msg_* + ~45 verb-default blocks, the conversation framing,
  the seam blocks). Need a reachability sweep over the routine call graph: mark
  from the entry, drop any routine nothing reaches.
- THE SUBTLETY (do not get this wrong): handlers and react routines are NOT
  reached by direct call fixups from __main__. Dispatch is INDIRECT -
  call_handler(handler_of(noun)) reads a react routine address out of the OBJECT
  TABLE (objects.py routine_fixups), and react_<obj> calls the handler routines
  (h<n>) by name (the registry from build_routines). A naive "follow RoutineRef
  calls from main" would mark all handlers/react routines dead. SEED reachability
  with: __entry__, __main__, every react_<obj>/react_free/grain<i>/topic_<obj>_<i>/
  topicwhen_<obj>_<i> routine AND the handlers they dispatch to, then sweep
  transitively. The dead candidates are unreferenced blk_<name> blocks.
- ALREADY PARTIALLY DONE (the pattern to extend): compiler-emitted routines are
  reference-gated - codegen._references_routine + the gates for cosmos_topic_*
  (_TOPIC_HELPER_NAMES), cosmos_exit_* (gen_exit_routines), and topic body/when
  routines (emitted only when topics exist). B6 generalizes this to a transitive
  block sweep.
- NO DOUBLE-COMPILE: an overridden library block is NOT compiled twice - sema
  w.blocks[name] holds only the winning (override) version (last-wins), so the
  library version is already gone. DCE only needs the unreferenced-prune.
- CONCRETE DEAD CASES (verified): line_you/line_reply/line_end (english.prelude,
  ~64 bytes, dead without conversations); status_bar/status_lines/menu_owns_talk
  (loop.prelude, dead without conversations - this is why we used a library seam +
  DCE rather than a compile-time summoned() check, Stefan's call). EXCEPTION:
  reach_unscoped (english.prelude) is ALWAYS referenced (resolve_objects calls it),
  a tiny `return nothing` wrapper DCE keeps - the one irreducible seam residue,
  accepted.

B6 PART 2 - ABBREVIATIONS: baked-in default DONE (committed ec0d533); opt-in
--make-abbreviations still to do. zstring.encode now emits references (bank shift
1-3 + index 0-31, 96 entries); the module-state set is installed once per compile
in generate() and reset after (so driven tests encode literally); build_story lays
the 96-word table + the abbreviation strings at the start of static memory.
arcturus/abbrev.py has the greedy optimizer + the baked-in DEFAULT_ABBREVS,
regenerated by tools/arcabbr.py from tools/corpus.storyarc (a representative
standard-only story). KEY FINDING (settled with the data, supersedes the "64/96"
expectation for the DEFAULT): because every standard verb handler is always live,
the library's whole message set is harvested from ANY game, and the pure library
text only yields ~47 universal abbreviations - that is the natural default size.
Filling more of the 96 slots only pays for a specific game's own prose (measured:
a prose-rich corpus gave 96 but every example got ~100 bytes BIGGER, because the
non-universal entries waste a stored string each). So the default is ~68 (terse
standard corpus); the 96 ceiling is for the per-game --make-abbreviations pass.
Sizes with B6.1+B6.2: brass 11572, cloak 12336, statusline 10952, conversations
12772, extended-verbs 14196, interrogation 16296 (576-956 under B5).

  NASTY BUG FOUND + FIXED (committed f585f00, a real latent correctness bug the
  abbrev table exposed): _emit_property_table never wrote the v5 property-list
  terminator (a 0 size byte). get_prop_addr for an ABSENT property (desc_addr on a
  descless object -> examine) walked off the object's table into following memory.
  It "worked" only because the object table was trailed by the all-zero abbrev
  table, whose first zero ended the walk. Filling the abbrev table removed the free
  terminator -> examine of a descless object printed garbage. Fix: terminate each
  property list (+1 byte/object). This was masked for the ENTIRE project.

  STILL TO DO for Part 2 (the opt-in 2-pass, the slow zabbrv-style route Stefan
  wants for speed-vs-quality choice): a `--make-abbreviations <file>` CLI flag that
  harvests the story + its summoned granules, runs abbrev.compute to the full 96,
  and writes ONE abbreviations.granule (Arcturus syntax); the encoder intercepts a
  summoned abbreviations.granule as compile-time data (codegen._abbreviations_for
  already checks world.abbreviations - the override hook is stubbed, nothing sets
  it yet). zstring.encode + the optimizer are reused as-is.

B6 PART 3 - codegen tightening: DONE (committed). Five tightenings, docs/04 s.11:
(1) canonical returns - emit rfalse/rtrue for ret 0/ret 1 (op-level; biggest, every
handler/react/helper ends on return 0/1). (2) short-form branches - assembler.
Routine.relax() rewrites a forward branch to the 1-byte form when its offset fits
2..63. (3) branch-to-return - a branch whose target is a bare rfalse/rtrue returns
via short offset 0/1. (4) one-byte jumps - a forward jump with offset 2..255 uses
the small-const operand (0x9C). 2-4 are one fixpoint in relax() (shrinking one
element pulls others into range; converges since offsets bottom out at 2, never the
0/1 return range); branch+jump offsets are PC-relative/intra-routine so relax runs
per routine before link, leaving only call/strref fixups. (5) dead code - lowering
compile_block returns whether a statement list unconditionally terminates (return/
stop/finish/continue, or if/else all-terminating); stops emitting after a
terminator, _if drops the dead jump-to-end, codegen omits the default return after
a terminating body. CUMULATIVE B6.3: cloak 12528->11324 (~11.3K), brass 11768->10620,
interrogation 16480->15092 (~1.2K/game). All 247 tests pass; cloak reaches "*** You
have won ***" on Frotz, topic/menu examples verified by hand.

B6 COMPLETE. The opt-in --make-abbreviations pass landed (committed 6780d8c): arcc
--make-abbreviations game.storyarc harvests the story + its summoned granules
(codegen.harvest_strings, abbreviations off so raw text), runs abbrev.compute to 96,
writes abbreviations.granule beside the story. Summoned BY NAME (summon
abbreviations.granule); cosmos.combined_program intercepts it, lexes out the string
literals (extract_abbreviations, not runtime blocks), threads them via
ast.Program.abbreviations -> sema -> wm.World.abbreviations -> codegen
_abbreviations_for. Round-trips exactly (4 string escapes; a whitespace-run entry is
dropped, not corrupted). MODEL CORRECTION (Stefan): text compression is NOT a dotted
feature - the standard set is always applied; `summon.abbreviations` removed and now
errors with a hint. docs/05 s.7 is the dedicated abbreviations entry; docs 00/01/02/
03/04 + README aligned. 252 tests (tests/test_make_abbreviations.py). Tuned vs default
example deltas are modest (~100-200 B) since the default already covers universal
text; the tuned set pays off on large prose-heavy games. B6 benchmark met: cloak
11324 (~11.3K) << Puny 27K, < NAIL 12.5K.

BUILD/TEST + HARD RULES (carry these): rebuild amalgam `python3
tools/amalgamate.py build/arcc`; rebuild example .z5 after any cosmos/ change;
throwaway .z5 -> scratchpad, not build/ (build/ is gitignored, holds arcc + the
example .z5). Never em dashes [[no-em-dashes-ever]]. Commit with `git commit -F
/dev/stdin <<'EOF'` heredoc (zsh eats backticks in -m); never amend/rewrite history
[[never-override-git-identity]]; co-author trailer "Co-Authored-By: Claude Opus 4.8
(1M context) <noreply@anthropic.com>". Interpreter verification is a hand-off
[[interpreter-verification-is-handoff]]: build the .z5, verify on Frotz yourself,
hand off with the size, PAUSE before advancing a milestone. The actaea/ dir stays
UNTRACKED (Stefan's working file). The override/seam model DCE must respect:
prelude blocks overridable, granule blocks forked; seams compose optional features
[[cosmos-library-structure]]. WORK STYLE (Stefan, reinforced repeatedly this
session): TALK THROUGH any design fork BEFORE implementing - do not build off a
discussion until told to proceed.

The ">>> RESUME POINT <<<" block below (topic system sub-step 2) is COMPLETE and
superseded by this checkpoint; it remains as history.

>>> END B6 HANDOVER CHECKPOINT <<<

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

## In progress: B4: Cosmos compiled by the compiler

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

NAMED OBJECTS DONE (6cc1790 + rename): the `named` standard attribute (renamed
from `proper` per Stefan, to drop the Inform-ism) is honored by ${the noun}/${The
noun} - a named object (Linda, Excalibur) prints with no article ("Linda holds
firm.", not "The Linda"). lower._say_with_article skips the article when the
object is `named`; the runtime check is gated on layout.has_named (no named object
-> no check emitted, examples byte-identical). tests/test_named.py.
ARTICLES (settled with Stefan): definite `the` done. Indefinite a/an = AUTO (low
burden): compiler picks a/an by the name's first letter, `named` objects get
none, with a per-object override for edge cases (an hour, a unicorn). Listings
(room, inventory, AND container contents) all use articles: "You can see a gold
coin here.", "box (contains a coin, an apple and a cookie)". (NEXT, before the
container model.)

CONTAINER SCOPE AND KNOWLEDGE MODEL (settled with Stefan, 2026-06-29; a core
parser/world-model improvement, NOT a granule - "better than Inform" for
containers). Two layers:
- Layer 1, SCOPE: DONE (committed). scope_match now recurses via scope_match_in +
  see_into (english.prelude), matching the in_scope rule: an object inside a
  container is reachable iff the container is in scope AND (it is `open` OR
  `clear`); a supporter's contents are reachable when the supporter is. New
  standard attribute `clear` (Inform's `transparent`, renamed). Fixes the
  coin-in-an-open-box matching; closed opaque containers shield their contents.
  find_word removed (scope_match_in subsumes it). tests/test_container_scope.py
  (open/closed/clear/supporter). brass +84 bytes for the recursion.
- Layer 2, KNOWLEDGE: DONE (committed). New `seen` attribute, set when an object
  is shown (an open container's listed contents, take, examine, reveal_contents on
  open). A container/supporter names its contents when listed -
  "a wooden box (contains a gold coin and an apple)" (list_contents +
  content_listable in english.prelude, using auto a/an and X-Y-and-Z); an open/
  clear/supporter shows all, a closed opaque box shows only the seen ones (memory).
  Opening a box reveals its contents at once (reveal_contents). The OPEN-FIRST
  REDIRECT (option b): scope_match falls through to shut_search, which finds a
  seen content in a closed opaque container, sets the shut_in global, and the loop
  answers msg_open_first ("You'll have to open the X first.") instead of can't-see;
  a never-seen content stays unknown (no x-ray). tests/test_container_scope.py
  (remember + redirect), test_functional updated. SIZE: the whole container model
  added ~840 bytes to brass (always-on; B6 DCE/abbrev will trim).
- LISTING FORMAT (Stefan, article-free): `box (contains coin, grandma's teeth and
  sugarcookkie)` - no a/an/the, the word "contains", list as "X, Y and Z". Applies
  to inventory and room listings. We have `${the noun}` (definite, literal "the");
  automatic a/an is NOT implemented and articles are deliberately avoided here.
  Broader article/pronoun question (a robot referred to as "it") is deferred.
- SEQUENCING: TBD with Stefan - do it before or after the conversation topic
  system. (It is foundational; the topic system's "ask about <thing>" benefits.)

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
- B5.5b v1 DONE (committed): extendedverbs. The plain E verbs - search, throw,
  rub, squeeze, tie, cut, fill, burn, blow, set, empty, buy, consult, dig, wave,
  sit, stand, sleep, swim, swing, think, pray, shout, ask, tell, answer,
  fullscore - each a verb decl + free `on <action>` default speaking a granule
  msg_* (the sensory pattern). search lists a container/supporter's contents;
  fullscore prints a breakdown (meta, no tick); ask/tell need an animate target.
  All wording in the granule (overridable); zero cost unsummoned (brass byte-
  identical). An object overrides any default (most-specific-wins). NOTE: handling
  an E verb (e.g. guard `on rub`) without summoning extendedverbs is a clean compile
  error - you can't react to a verb you didn't bring in. tests/test_extendedverbs.py;
  examples/granules/extended-verbs.storyarc. WORDING IS DRAFT - hand to Stefan to
  redline (like the standard message set).
  DEFERRED to v2 / parser refinement: multi-word forms (look under, look in, get
  up, sit on) need the compound/particle system extended; ask vs ask_for by
  preposition (about/for) needs action-by-preposition in the parser (v1 folds both
  into ask); and noun matching is SHALLOW (objects nested in an open container are
  not matched by the parser yet - affects all verbs, not just these).
  v2 = the ask/tell TOPIC dispatch on the conversation model below.

CONVERSATION MODEL (settled with Stefan, 2026-06-29; the spec for B5.5b v2 +
B5.5e). Studied Puny's ext_talk_menu.h (../PunyInform/lib) - powerful but a
NIGHTMARE: positional flat talk_array rows, hand-managed integer topic IDs,
trailing-int follow-up lists, a separate hand-numbered ext_flags system, and
imperative ActivateTopic/InactivateTopic + a TalkRoom class. We keep the
capability, drop the bookkeeping, because we own the compiler. The Arcturus model:
- One unified `topic` declaration per person (Option A), feeding BOTH presentations:
  `topic <subject> "<menu label>" [words a, b] [when <cond>] [once] [hidden]` with
  a body. <subject> is a barename id; the string is the menu label; `words`
  (OPTIONAL) are the ask/tell match words - only needed for the Infocom path, a
  conversations-only topic needs none.
- Visibility GATES BOTH ask/tell and the menu (Stefan: gate both). Mechanisms:
  `when <cond>` (live, declarative - replaces Puny's IDs+flags+ActivateTopic for
  milestone/location/state); `hidden` initial + `reveal <topic>` / `hide <topic>`
  by NAME (the explicit-unlock case); `once` retires after use. Both `when` and
  reveal/hide are offered.
- Body lines: `player "..."` and `reply "..."` AUTO-QUOTE and AUTO-ATTRIBUTE with
  a speaker prefix - `You: "..."` / `<NPC name>: "..."` (Puny TMPrintLine style,
  best for following long exchanges; labels/format overridable). `say "..."` =
  plain stage direction. Mix freely. (Auto-quoting fixes Stefan's long-standing
  Puny annoyance of having to override the extension just to get quotes.)
- MUTUAL EXCLUSION: ask/tell (extendedverbs) and conversations are two
  presentations of the same topics; they must NEVER both be live. If both are
  summoned, conversations WINS and ask/tell topic dispatch is OFF; ask/tell then
  give a redirect ("To speak with Linda, just TALK TO her."), not a flavor fail.
- Complexity lives in the COMPILER: `topic` is a NEW construct (token, parser,
  ast.TopicDecl, sema, a per-person topic table the granules walk at runtime);
  the screen opcodes from statusline paint the menu in the upper window.
- BUILD ORDER: extendedverbs v1 (plain verbs) -> the topic construct + model +
  conversations menu -> ask/tell topic dispatch (extendedverbs v2) -> mutual-
  exclusion wiring.

>>> RESUME POINT (after compaction) <<<
TOPIC SYSTEM is mid-build. Sub-steps:
- [x] 1. PARSE + COLLECT + COMPILE INERT (committed 5594a5e). The `topic`
  construct parses end to end and topics collect onto wm.Obj.topics /
  wm.Kind.topics; codegen ignores them so a game with topics compiles inert.
  Done: tokens (keywords topic/you/reply/reveal/hide), ast.TopicDecl (a Member)
  + ast.Line(who="you"|"reply", text) + ast.TopicToggle(reveal, target),
  parser.parse_topic (header modifiers words/when/once/hidden in any order) +
  _parse_line + _parse_topic_toggle (registered in _STMT_KEYWORDS),
  sema._collect_members appends TopicDecl. NOTE: the player's line keyword is
  `you` NOT `player` (player is the reserved player-object keyword). docs/01
  appendix A reserved words updated. tests/test_topics.py.
- [x] 2. THE RUNTIME (done, this commit). Each person with topics carries a
  `topics` property (a standard T_LIST prop, objects.py) pointing at a runtime
  topic table in dynamic memory: a count word, then a fixed TOPIC_REC=10-byte
  record per topic [+0 body routine, +2 menu label, +4 when-guard (0 if none),
  +6 match-word sub-array ptr (0 if none), +8 static flags (ONCE 0x01, HIDDEN
  0x02), +9 mutable state (RETIRED 0x01, HIDDEN 0x02)], then the per-topic
  match-word sub-arrays (count word + dict addrs). All wired by the existing
  object-table fixups (routine/string/word/prop-pointer). codegen.gen_topic_
  routines emits topic_<obj>_<i> body routines (self = the person) and
  topicwhen_<obj>_<i> guards (return 1/0); these are ALWAYS emitted when topics
  exist (the table references them). codegen.gen_topic_helpers emits the
  cosmos_topic_* backing routines (count/rec/label/visible/run/matches) only
  when referenced (gated like the exit routines), so topics-without-granule pays
  only the table+bodies. lower.py: ast.Line (you/reply - the COMPILER owns only
  the structure: it calls Cosmos blocks line_you / line_reply(self) / line_end for
  the framing and emits the text in between via _emit_say. The wording - speaker
  label, separator, auto-quote marks - lives in cosmos/english.prelude
  (overridable + translatable, reachable by the ask/tell path which runs WITHOUT
  conversations.granule; deliberately NOT in the granule, where ask/tell users
  could not reach it). ast.TopicToggle (reveal/hide flips the sibling's HIDDEN
  state bit; subject -> index resolved at COMPILE time via ctx.topic_index, a
  direct poke, no runtime lookup), and the topic_* intrinsics. SUBJECT
  ADDRESSING: reveal/hide always target a sibling on self, so the compiler knows
  the index; once-retirement folded into cosmos_topic_run. Proven on Frotz
  (tests/test_topics.py test_topic_runtime_on_frotz: visibility gating by
  hidden/when, auto-quote+attribute, reveal unhides, once retires). Examples
  +64 bytes (12132/12980) for the three always-on line_* prelude blocks (dead in
  non-conversation games, dropped by B6 DCE). docs/04 section 8 + message-set.md
  record the lowering and the overridable blocks.
- [x] 3. ask/tell dispatch (extendedverbs v2) DONE (this commit). In
  cosmos/extendedverbs.granule: ask/tell are now ONE noun + a trailing preposition
  (`ask noun about` / `ask noun for` / `tell noun about`), NOT two nouns - the
  subject is a topic word, not an object, so a second-noun slot would set
  parse_fault on it and the turn would abort before the handler ran. The handler
  calls converse(noun): block converse scans the person's topics in declaration
  order, and for each visible one (topic_visible) checks if the player typed a
  word it answers to (block subject_typed -> topic_matches over word_dict); the
  first match runs (topic_run, which retires `once`). ask and tell SHARE converse
  (a topic matches on its subject words, not on the verb). No match -> the flat
  default (msg_ask "stays mum on the subject" / msg_tell). Proven on Frotz
  (tests/test_topics.py test_ask_tell_dispatch_on_frotz: hidden topic -> default,
  ask runs+reveals+retires, retired -> default, tell reaches the revealed topic,
  unknown subject -> default). Example sizes unchanged (dispatch is in the
  granule). docs/verb-set.md conversation rows updated. STILL TODO in sub-step 5:
  gate converse OFF when conversations is summoned (redirect to TALK TO).
- [x] 4. conversations granule DONE (+ examples/granules/conversations.storyarc,
  the Seer's Tent showcase). cosmos/conversations.granule: TALK TO a person paints
  their visible topics as a NUMBERED menu held STATIC in the upper window while the
  conversation scrolls below; press the number (read_key -> the new read_char VAR
  opcode 0x16) to run one, it drops off (topic_retire), and the menu repaints with
  any topics revealed. 0/ENTER folds it away. STEFAN'S CORRECTION: Puny's talk menu
  is bad as an IMPLEMENTATION experience (talk_array/flags/IDs), but its VISUAL is
  the good part - static menu, conversation scrolls beneath. First pass wrongly did
  a scrolling inline menu; reworked to the upper window. ADAPTIVE SIZING (Stefan:
  this is where we improve on Puny's fixed half-screen) - h = status_lines + count
  + 3, sized to the topics in view; double-erase around the resize kills shrink
  residue; a dashes divider at the bottom border. STATUSLINE COEXISTENCE: factored
  the bar into status_bar() (lib no-op, statusline overrides) + status_lines() (0
  or 1); the menu paints the bar at row 1 when present and reclaims row 1 when not.
  SEAM for talk: base `on talk` -> block talk_to(person) (default msg_no_talk);
  conversations overrides talk_to -> run_talk. NEW intrinsics: read_key, topic_retire
  (+ cosmos_topic_retire), erase_window, screen_height. Proven on Frotz
  (tests/test_conversations.py). DIRECTIVE [[demos-include-statusline]]: demos/
  examples summon.statusline by default, must also work without.
- [x] 5. mutual exclusion DONE (this commit). Library-default block
  menu_owns_talk() (loop.prelude) returns 0; conversations overrides it to 1.
  extendedverbs' on ask/on tell check `if menu_owns_talk() is 1` BEFORE converse
  and redirect (msg_use_talk: "To get anywhere with X, just TALK TO X.") instead
  of dispatching topics. So: extendedverbs alone -> ask/tell run topics;
  conversations alone -> talk opens the menu; BOTH -> menu wins, ask/tell defer.
  The seam is a LIBRARY block both granules reference (a granule cannot override
  another granule's block); like status_bar it is dead-stripped by B6 DCE when
  unused. Proven on Frotz (tests/test_conversations.py test_menu_wins_over_ask_
  tell_on_frotz: ask redirects and does NOT run the topic; the menu still runs it).
  THE TOPIC/CONVERSATION ARC IS COMPLETE (sub-steps 1-5 + both showcases:
  infocom-interrogation.storyarc for ask/tell, conversations.storyarc for the menu).
KEY FILES for the runtime: objects.py (emit a per-object topic table like the
words array), codegen.py (gen topic body routines like react/grain routines),
lower.py (lower ast.Line / ast.TopicToggle), cosmos/extendedverbs.granule (ask/
tell v2), a new cosmos/conversations.granule. The CONVERSATION MODEL spec is the
block just below.
>>> END RESUME POINT <<<
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
- B5.5d DONE (committed): statusline. A reverse-video bar painted before every
  prompt: room name left, score/moves right, updating each turn. REDRAW HOOK =
  the granule OVERRIDES prompt() (Cosmos calls prompt() before every command,
  including the first after the opening room), so NO turn-loop change and zero
  cost when unsummoned (examples byte-identical). New screen-model VAR opcodes in
  the assembler (split_window 0x0A, set_window 0x0B, erase_window 0x0D, set_cursor
  0x0F, set_text_style 0x11) and intrinsics split_window/set_window/set_cursor/
  set_style/screen_width (screen_width reads header byte 0x21). The bar wording
  lives in the granule (overridable/translatable). dumb-mode frotz reconstructs
  the upper window, so it is checkable headless. tests/test_statusline.py;
  examples/granules/statusline.storyarc (awards a point for the coin to show
  score change). The screen opcodes also feed Actaea (B8) and conversations.
  WIDTH-ADAPTIVE FORMAT (Stefan, like Puny): draw_status reads screen_width() and
  switches automatically - >= 54 columns prints the full "Score: n   Moves: n";
  narrower (40-col C64, 53-col Spectrum) prints the compact "Score: score/turns"
  so it still fits. Right-aligned via status_digits. Cloak now summons statusline
  (it is the apples-to-apples feature for
  the B6 Puny benchmark - Puny's Cloak has one); brass-lantern deliberately does
  NOT, with a header note. Both examples/cloak and docs/01 section 18 updated in
  sync (test_examples decl count 11 -> 12). Cloak with statusline is ~11.9K.
  The statusline showcase's `on take` guards scoring on `not moved` (award the
  point once; dropping and re-taking does not re-score).
- B5.5e: conversations. The MENU presentation of the CONVERSATION MODEL above:
  TALK TO <animate> paints the person's visible topic labels as a numbered menu
  in the upper window (reuses statusline's screen opcodes), selection runs the
  topic body, the menu redraws as topics reveal/hide/retire, until exit. Built on
  the shared topic table; wins over ask/tell when both summoned.
- B5.5f: debug DONE (cosmos/debug.granule). Verbs: tree (the whole object tree),
  scope (what is reachable here), fetch/purloin (pull any object to you),
  warp/gonear (teleport to an object's room), inspect/showobj (location +
  attributes set). Opt-in via summon; not summoned = absent (no release switch).
  KEY MECHANISM: fetch/warp/inspect reach OUT-OF-SCOPE objects, which the parser
  normally aborts on ("you can't see that"). Added a parser seam reach_unscoped()
  in english.prelude (library default `return nothing`, called by resolve_objects
  after scope matching fails); debug overrides it to match the typed word against
  EVERY object (find_any scans object numbers 1..object_count() via has_word - a
  new object_count() compile-time intrinsic), but only for the debug verbs
  (checked by action). The seam default is the one thing left in the core without
  debug (a tiny `return nothing` the parser references, so DCE keeps it - decided
  with Stefan, cheaper/cleaner than overriding named_unseen). Proven on Frotz
  (tests/test_debug.py: fetch reaches an object in another room). NOT YET: set
  prop / clear attr (Stefan's "set prop" - deferred; the 5 verbs are the core set).
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
- 221 tests; both example games still win. Run python3 -m pytest. Rebuild arcc
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

- [ ] DCE MUST prune UNREFERENCED PRELUDE BLOCKS (reachability sweep over the
  call graph from the entry, drop any block nothing reaches). Today codegen
  compiles every world.blocks entry unconditionally, so feature-only wording that
  correctly lives in english.prelude still ships into games that never touch the
  feature. Concrete first case: line_you / line_reply / line_end (the you/reply
  topic framing) cost ~64 bytes on brass/cloak even though those games have no
  conversations. ALSO status_bar / status_lines (loop.prelude): the seam blocks
  the conversations menu calls and statusline overrides; they are unreferenced
  (and so strippable) in any game without conversations - this is why we did NOT
  add a compile-time summoned() check, DCE handles it (Stefan, decided here, same
  call as the line_* placement). The placement is right (a granule can only
  override a LIBRARY block); the gap is only that unreferenced library blocks are
  not yet stripped. This sweep also trims the ~70 message + ~45 verb routines
  currently shipped wholesale.

ASK/TELL CONVERSATION EXAMPLE: DONE - examples/granules/infocom-interrogation.storyarc
(a detective leaning on the suspect Victor Crale; deliberately not Linda/Paris,
which were Puny's). It showcases the full topic feature set on the ASK path:
`words` matching, the reveal chain (alibi -> ticket -> confession), `once`
retirement, a `when player holds opener` guard (the murder weapon can only be
raised while held), you/reply auto-quote+attribution, and `say` stage directions
mixed in. The suspect's own `on tell` is the manual escape hatch beside the
sugar: ASK runs topics, TELL he handles himself. TWO AUTHOR LESSONS (Stefan's
redirect, do not regress): (1) Infocom conversation REPLACES generic chatter -
the suspect's `on talk` does NOT list topics; it turns TALK TO him into a redirect
("be specific: ask him about something, or tell him what you've got"), so there is
no dead "nothing to say" path and the player learns ask/tell. (2) Guidance is the
detective's INNER VOICE, not a menu: a free `on start` opens on the first thread
("...The alibi."), and every topic body ENDS with an unquoted line of internal
monologue naming the next thread to pull (alibi -> "push him on the ticket" ->
"take the opener, make him look at it" -> "go for the truth"). NO topics_count/
topic_label listing in this example (that introspection belongs to sub-step 4's
menu). Verified on Frotz. Like the other examples/granules/*.storyarc it is an
untested showcase artifact (behavior covered by test_ask_tell_dispatch_on_frotz).
