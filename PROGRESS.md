# Arcturus progress

A living log of where the project stands, maintained as work proceeds. The
authoritative plan is `docs/00-roadmap.md` (milestones B0 to B13); this file
tracks status against it and records decisions made during implementation.

Last updated: 2026-07-03.

Model handover: `HANDOVER.md` (repo root) is a holistic orientation written at
the switch to Anthropic's Fable model, with an assessment task to run before B8.
Read it alongside this log.

>>> B8 DAY-TWO HANDOVER CHECKPOINT (2026-07-03, written for compaction) <<<

WHERE WE ARE. Versions arcc 0.9.0 / Cosmos 0.12.0; 384 tests green; the size
gate must be GREEN before every commit; the amalgam (build/arcc) and the
vsix (editors/vscode/arcturus-0.9.0.vsix) are current; posada.z5/gasthaus.z5
rebuilt. The H2 SLICE (hibernated2/hibernated2.storyarc, GITIGNORED with the
game, NEVER COMMIT) covers all of Act I, walkthrough-verified end to end on
dfrotz (the quote-box keypress eats one piped line: feed a leading blank),
and now exercises EVERYTHING built today. Everything below landed TODAY, in
order, each with tests, docs, ceilings, and its own commit:

(1) COMMAND CHAINING (core): and/then/comma (y/luego, und/dann), stop on
`refused`, AGAIN = last segment, undo/ask/confirm kill the queued tail.
(2) DISAMBIGUATION (core): the scoring matcher (match_phrase, packs are thin
wrappers) + the interactive ask ("Which do you mean, ...?": answers weave in
at ask_at via the ASK_TEXT backup; verb-initial answers replace the command;
German ask declines accusative). (3) TAKEALL GRANULE (all-words, dict flag
0x01; per-item FULL TURNS, whole-sweep undo, sweep prints compact).
(4) PLURALS GRANULE (group words via the `plural` list property; THEM;
pronoun-them decl doubles as the any_plurals marker; two-noun slots never
sweep). (5) NOUN LISTS moved to CORE per Stefan (verb_fallback borrows the
previous chained verb; NOISE WORDS declaration, flag 0x03, articles known-
but-ignored; strict borrow: any unknown word refuses). (6) AMBIENCE GRANULE
(v1+v2 whole: about/every/in order/once headers, block and per-line when,
do-lines, ambience_rate dial, one line per turn; per-block routines + a live
table, __ambience__; driver in Arcturus in the granule). (7) SCOPE ROOM
(Stefan's design: `in scope` = backstage, seeded on demand, in_scope hook
folds; solves companion + unreachable-chip). (8) RECIPIENT DISPATCH (second's
handlers between noun's and room's). (9) TAG qualifier ("(full)" in listings;
show, not say, in tag blocks). (10) START TITLE skipped under a statusline.
(11) SCORING (Stefan's flagship: `scoring` meta = auto-pay rooms/takeables 5
on first visit/take, never start room/start inventory, `scored false` opts
out; `award N [for pool "label"]` pays once per site/pool, max of pool
counted once; MAX_SCORE SELF-SUMS, never typed; `ranks` ladder spreads over
max, pins `at N percent` / `at N points`; msg_score announces rank in three
languages; extendedverbs FULL prints the earned breakdown; ledger line shows
the whole plan). (12) THE DECLARATION TRIO: flag (false-start, true/false
enforced) / counter (0-start, x++ x-- via inc/dec) / global (values, object
refs, STRINGS: string globals were silently broken, now seeded + print as
text). Plus intrinsics clear_screen()/random(n)/print_packed etc., global
initializers seeded (latent bug: NOTHING was ever seeded before), print_name
and cosmos_banner flush the pending break (two paragraph-layer latents), the
two-noun boundary is joining-words only ("pick LOCK with nail" fixed), topic
once-vs-when-vs-reveal documented, conversations + extendedverbs docs/05
sections rewritten properly, VSCode grammar caught up (0.4-era to 0.9).

STANDING RULES REINFORCED TODAY (memory updated): core-touching decisions in
modular work are STEFAN'S; pitch byte costs and alternatives BEFORE building
("it's 75 here, 110 there"). Granule = zero cost unsummoned, fully folded.
Design forks: talk first, he backs vetoes both ways. Assert every scripted
edit (a silent no-op replace bit twice today).

NEXT, IN ORDER: (1) Stefan plays the slice; pending his native pass: the two
ask wordings (EN done, "?A cual te refieres...?" / "Was meinst du: den...?"),
the msg_score rank lines (ES/DE), G5 emphasis colour (say.yellow guess).
(2) H2 ACT II onward, region by region, walkthrough-driven (wilderness/
jungle/riverbank next; hull plate, razor vines + Vlad topic, statue slab;
watch arcc -s, globals 55/240 at the slice). (3) The QUALITY SWEEP list in
the slice header (oil-canister wording etc.) after functional porting.
(4) Someday: bit-packed flags if a game nears 240 globals; fullscore
anonymous-points line; ambience per-line dwell.

>>> END DAY-TWO CHECKPOINT <<<

THE POST-MORTEM, AND GHOSTS LEAVES THE ROADMAP (2026-07-04, Stefan's
blessing after playing H2 through; arcc 0.10.1 / Cosmos 0.14.1): a
`finish` banner is now followed by the FINAL SCORE (msg_score, rank and
all) and the classic prompt, "Would you like to RESTART, RESTORE a saved
game, or QUIT?" (msg_game_over, three languages), looping until answered.
The answers are matched BY ACTION against the pack's own
restart/restore/quit verb words, so every language pack works with zero
extra wiring; a failed restore reports msg_restore_failed and re-asks;
a successful restore resumes at the save point by the existing r==2
machinery. Wired in the finish lowering (call blk_game_over before quit;
a bare no-Cosmos build still just quits; games without a finish pay
nothing, DCE). H2's ending now reads: *** THE END *** / "You have scored
360 of a possible 360, in 119 turns, which earns you the rank of Savior
of the Universe." / the prompt. STEFAN'S PLAY-PASS VERDICT on the full
port: everything fine, and the build is SIX KILOBYTES SMALLER than the
PunyInform variant of the same game - the size charter proven on the
flagship. B9 (GHOSTS OF BLACKWOOD MANOR) IS DROPPED from the roadmap on
Stefan's call: it was the easier port, and with H2 complete its
sufficiency proof is redundant; the milestone number stays reserved so
B10-B13 keep their names (docs/00, README, CLAUDE.md, memory synced).
Flagged for later: an after-handler ordering oddity seen in a test
fixture (on take / continue + on after take looked like the after body
ran without the default completing); to investigate, not chased today.
NEXT: Stefan's word on next steps (quality sweep vs B10 Actaea).
400 tests; ceilings re-pinned (finish games pay ~250 for the post-mortem).


HIBERNATED 2: ALL FOUR ACTS PORTED, THE END REACHED (2026-07-04, Stefan's
"continue with the rest"): hibernated2/hibernated2.storyarc (gitignored,
NEVER COMMIT) now carries the COMPLETE game: Act III's City of Glass (the
chapter-gated Plaza; Science with the ring/axis/focus stellar-map puzzle
on two counters and Vlad's par.say.par callouts; the Temporal Lab's
frozen stabilizer freed by the resonance crystal; the Nexus shield and
hand-print slab; Genesis and the keycard; Residential with the chimes,
the toy's 1-0-4-4, and the Memory Core lore dump; Industrial with the
conduits and the three-ingredient fabricator manifest; the Council's
deadlocked vote with Vlad's ARCHIVE interception) and Act IV (the Apex
sync with the one-way teleport and the Keeper's -10 mercy rescue; the
five lunar rooms; keycard, frozen guards, shattered crystal, the
tried-and-whipped killswitch, the give-to-Vlad gate, and the final
attack into the six-beat epilogue and finish "*** THE END ***"). USE and
THROW are story verbs (the original's synonym routing) with the tools
answering by second noun; recipient dispatch carries the dais, the
fabricator manifest, and the reader. The walkthrough runs all four acts
to *** THE END *** at 360 of 360 SELF-SUMMED (30 anonymous award sites,
1 pool, 41 auto-scored: 27 rooms + 14 takeables, every point verified
reachable). THE POOL LESSON PAID FOR ITSELF: the stabilizer breaks the
nexus shield on two alternate paths, and the first build summed both
sites (max 365, reachable 360, the exact 355/350 failure class caught by
the ledger arithmetic in one read); `award 5 for nexus_field` on both
sites counts the event once. Rebased the .inf's axis counter (-3..0 ->
0..3, counters start at zero; same three pushes). NOT PORTED, deliberate:
the .inf's gravity topic (dead content, never activated), CREDITS/ABOUT/
HELP and the Puny-hack flavor overrides (quality sweep). GAP FLAGGED for
Stefan: our `finish` ends at the banner; Inform prints the final score
and a RESTART/RESTORE/QUIT prompt after "*** THE END ***". Artifact is
now hibernated2/h2-full.z5 (131104 bytes, 4400+ source lines); the slice
artifact retired. 399 tests untouched and green.


GAIN JOINS TELEPORT, AND THE OVERHAUL BUMP (2026-07-04, Stefan's
blessing; arcc 0.10.0 / Cosmos 0.14.0 / vsix 0.10.0, the minor bump
marking the day's fundamentals overhaul): gain(obj) is a standard Cosmos
block, teleport's sibling: the acquisition without TAKE pays a scored
thing's points exactly once (any_scored fold), marks it moved and seen,
then moves it to the player. THE TAKE HANDLER ITSELF FUNNELS THROUGH
GAIN, so there is exactly one acquisition path (symmetric with go
funnelling through arrive); cost ~12 bytes per game for the call frame,
H2 got smaller (its two sites now share). DOCUMENTED AGAINST MOVE, hard,
per Stefan: Arcturus's `move` is the silent tree operation, Inform's
"move lamp to player" idiom is our gain; docs/01 section 5 carries a
CAREFUL-INFORM-HANDS warning box (gain when the player RECEIVES,
teleport when the player ARRIVES, move for silent stage management), the
scoring section and docs/02's teleport passage cross-reference it. H2's
story-local gain block deleted (the Cosmos one serves). HIGHLIGHTING:
block calls with arguments render the callee in its own scope
(entity.name.function) with the arguments left to the value scopes, per
the screenshot ruling; bare zero-arg calls are lexically plain names and
stay unscoped. tests: gain pays once, re-take after gain pays nothing.
399 tests; ceilings re-pinned; all artifacts + amalgam at 0.10.0; H2
130/130 "in 51 turns".

THE FUNDAMENTALS SESSION: PARENS EARN THEIR KEEP (2026-07-04, Stefan's
course correction on readability drift, "not the vision I had for this
language"; arcc 0.9.3 / Cosmos 0.13.4 / vsix 0.9.3): four rulings, all
landed. (1) BARE ZERO-ARG CALLS: print_banner, describe_room, let k =
read_key, if any_scored is 1 - a bare name resolves as a call only after
every data name (story names win), a block that takes values errors with
a pointer at the (...) form, and _static_value learned bare names so the
any_X FOLDS still fold (the first sweep grew every game ~1K until that
lesson: fold recognition must see both spellings). (2) IS [NOT] IN: the
tree test with the copula (chip is in scope); parent_of(x) is y sites
swept to it (identical strict-parent semantics; Stefan's caution heeded,
only literal parent-is tests rewritten). (3) PAR.SAY: the leading-
paragraph say for reveal paragraphs; composes fully (par.say.yellow,
par.say.par). THE BANNER manages its own space now: pending-break flush
before, pending-break mark after, and at start under a status bar the
title sits DIRECTLY below the bar (better than Inform's stray blank; the
leading newline that protected the title from the bar overlay moved to
the start path, conditional on status_bar). H2 has ZERO par() calls.
(4) THE STYLE SWEEP: not (x is y) -> x is not y and NAME() -> NAME
across every prelude, granule, example, H2, and the docs snippets;
byte-neutral once the fold fix landed (slightly negative). HIGHLIGHTING
POLICY (the screenshot): dot-chains render three scopes - keyword (say,
zcolor, par, summon), modifier chain (.par, .yellow, .font, one scope),
trailing value (the colour word) - grammar reworked, vsix 0.9.3.
tests/test_sugar.py pins bare calls, is-in, par.say spacing, and the
banner-under-bar; 398 tests; H2 130/130 "in 51 turns" unchanged.
PENDING STEFAN: the gain() promotion question (name and blessing).

SAY.PAR: THE PARAGRAPH RIDES THE SAY (2026-07-04, Stefan's sugar order,
"as little internal-cosmos blocks as possible" in author code; arcc
0.9.2): `say.par "..."` prints the text and marks the library's pending
paragraph break, so consecutive prose paragraphs are one line each with
no par() between them. Modifiers are a composable dot-chain in any
order, Stefan's addendum: say.yellow.par and say.par.yellow are the
same coloured paragraph (one colour per say, one par, enforced with
clear parse errors). Lowering is the same par_pending store the par()
intrinsic makes, inline, so the sugar is byte-neutral-or-better (H2
62996 -> 62880: the statement form skips the intrinsic call's value
plumbing). The H2 port swept: 38 say+par() pairs merged; the four
surviving par() calls are genuine standalone breaks (before text, not
after) and stay. docs/01 sections 16 and 16a, the VSCode grammar (the
say/zcolor rule now matches chained modifiers), and the vsix updated to
0.9.2 (repackaged directly, no node on PATH). 394 tests; H2 130/130.

CLOAK IS A 1:1 PORT, AND THREE SEMANTICS IT FORCED (2026-07-04, Stefan:
the benchmark game had grown extras from its first-example days and the
27K comparison deserved identical content; arcc 0.9.1 / Cosmos 0.13.3):
examples/cloak-of-darkness.storyarc is now a faithful port of Firth's
reference implementation, ../PunyInform/cloak.inf, THE size benchmark
build itself: the "cheap demo game" intro restored, grains and extra
vocabulary gone, "Foyer bar" lowercase, every wording matched, release 3
serial 221116, and the parts we had silently dropped or simplified put
back: MAX_SCORE 2 (award 1 on the first hang, paid once by award's own
semantics where Firth needed a flag; award 1 on the winning read),
event-driven bar light (after take darkens, after drop/put in the
cloakroom relights), and the TWO-TIER dark rules (wrong-way go = +2
"Blundering", any other action = +1 "In the dark?", look/inv free, metas
immune). One knowing divergence, documented in the file: an action aimed
at something unseen in the dark disturbs here (truer to Firth's spec
than to his code, where the parser rejected it first). THE PORT FORCED
THREE CORE SEMANTICS, each tiny: (1) OUT-OF-WORLD DISPATCH: score, save,
restore, restart, quit never reach object/recipient/room handlers (Puny
marks the same verbs meta); the compiler numbers meta actions last and
dispatch routes them to the free rules on one meta_floor() compare
(~10 bytes/game). (2) ON OTHER FIRES ONLY FOR UNADDRESSED ACTIONS: a
specific handler that ran and continued climbs the chain, it never falls
into the same object's catch-all ("on look / continue" = pass through);
an all-direction-guarded group that never ran still reaches the
catch-all. (3) DIRECTION NAMES ARE VALUES: `if way is not north`
compares the chosen direction, resolved last so story names win, zero
bytes. Cloak 1:1 = 14840 bytes, genuinely apples-to-apples at ~55% of
Puny's 27K, and it now demos award/self-summed max/status-bar score in
nine lines. docs/01 s19 listing replaced whole, the on-other and
pipeline docs updated, docs/02 s16 reconciliation rewritten; Cloak tests
now pin the original's scoring, both endings, the two-tier dark rules,
and meta immunity. 392 tests; H2 130/130 unchanged.

A SCORELESS GAME SAYS SO (2026-07-04, Stefan's observation playing the
German game; Cosmos 0.13.2): "Du hast 0 von 0 Punkten erreicht" was
awkward, and the status bar's permanent "Punkte: 0" doubly so. Both now
key on the any_awards fold, so the choice is made at compile time and
neither kind of game pays for the other's behavior: (1) SCORE in a game
that scores nothing answers "This game does not keep score." / "Este
juego no lleva puntuación." / "Dieses Spiel zählt keine Punkte."
(2) THE STATUS BAR of a scoreless game shows the move count alone
("Moves: n" / "Turnos: n" / "Züge: n"), both screen widths; a scored
game keeps the full Score/Moves side. Beyond-Inform convenience per
Stefan: the author declares nothing, the game simply knows whether it
keeps score. Scoreless builds SHRANK (Cloak 14952 -> 14732: the score
interpolation machinery folds out with the branch). Verified live in
all three languages (gasthaus bar reads "Züge: 1"); H2's scored bar and
130/130 unchanged. Statusline tests split scoreless/scored fixtures;
390 tests; ceilings re-pinned; docs 02/05/message-set synced.

ASKING IS TALKING UNTIL A GRANULE SAYS OTHERWISE (2026-07-04, Stefan's
byte challenge on the 340; Cosmos 0.13.1): the standard ask/tell/answer
cost too much because the base seams REFERENCED the three flavor
defaults, which pinned the strings in every game past DCE. His ruling:
elevated conversation belongs to the granules alone; with neither
summoned, every conversation verb defaults to the one talk brush-off. So
the base ask_to/tell_to/answer_to now simply hand over to talk_to (which
also made conversations' ask_to override redundant: overriding talk_to
was already enough), and msg_ask/msg_tell/msg_answer are called ONLY
from infocom_talking, so DCE keeps them for infocom games alone. answer
gained its seam and guard on the way. Standard cost drops 340 -> 268
per game (Cloak 15028 -> 14952; the floor is dictionary words, grammar,
and the guard, which is what "the verbs parse at all" costs); menu games
shed the strings too. Extendedverbs-only games now answer "ask guard
about pebble" with "doesn't seem up for a conversation", by design.
388 tests; ceilings re-pinned; docs synced; H2 130/130 unchanged.

THE CONVERSATION ABSTRACTION, PUT RIGHT (2026-07-04, Stefan's redesign
after catching English verb words in the conversations granule; Cosmos
0.13.0): the granule had been built string-free and word-free, everything
player-facing in the packs, and the ask/tell convergence pass violated
that by declaring `verb "ask"`/`verb "tell"` inside it. Stefan's ruling
went deeper than the fix: the Infocom ask/tell never belonged to
extendedverbs at all. THE NEW SHAPE: (1) ASK, TELL, ANSWER are STANDARD
verbs, as in PunyInform (verified in ../PunyInform/lib/grammar.h: both
outside the extended ifdefs), words and grammar in the packs (EN
ask/interrogate/query + about/for; ES pregunta/dile + sobre/por/de; DE
frag/erzähl/sag + nach/von/über; Stefan approved the words, no native
pass needed), flat "stays mum"-class defaults in the packs, guards in
actions.prelude ending in two seam blocks ask_to/tell_to. (2)
infocom_talking.granule is NEW and holds ONLY logic: converse() and
subject_typed() moved out of extendedverbs; it overrides the seams with
the topic dispatch; fully translatable by construction. (3) conversations
is word-free again: it overrides ask_to -> talk_to (asking IS talking)
and tell_to -> the use-TALK hint; tell_hint died. (4) extendedverbs shed
its whole conversation section and is the pure flavor/idle verbset. (5)
conversations + infocom_talking is a COMPILE ERROR (matched by granule
filename so forks count): structural exclusivity replaced the behavioral
priority dance, and menu_owns_talk plus the whole convergence machinery
from the morning was DELETED, the design is simpler than before the day
started. COSTS, honest: standard ask/tell/answer put ~340 bytes into
every game (Cloak 14684 -> 15028, still ~55% of Puny's 27K which carries
the same verbs, so the benchmark stays apples-to-apples); the
infocom-interrogation example SHRANK 2.7K (17964 -> 15308, dispatch
without the flavor verbset) and extended-verbs shrank 400. Verified: DE
"frag wirtin" opens the menu, "sag wirtin" hints "SPRICH MIT der Wirtin"
(dative), ES "pregunta posadera"/"dile posadera" likewise; H2 unchanged
at 130/130 "in 51 turns". OOPS aside for the record: DE answers to
ups/hoppla/korrigiere, ES ups/corregir; adding literal "oops" to both
packs offered to Stefan, pending his word. 388 tests; amalgam and all
artifacts rebuilt; docs 01/02/05, verb-set, message-set synced.

ASK/TELL CONVERGE IN ANY SUMMON ORDER (2026-07-04, Stefan's fix order on
reviewing the ask mapping; Cosmos 0.12.3): the first ASK-is-talk pass left
a silent summon-order dependence: with both conversation granules loaded,
whichever declared `verb "ask"` LAST owned the dictionary word, so one
order opened the menu and the other still lectured. Authors must never
need to know the right granule order (Stefan). The fix is convergence,
not priority: extendedverbs' ask handler now calls talk_to(noun) when the
menu owns talking (instead of lecturing), so BOTH owners of the word end
at the same menu; and TELL gets the same treatment via the granule's own
action name (conversations declares verb "tell" -> tell_hint, answering
msg_use_talk), so telling hints at TALK TO in a menu-only game, with both
granules, in either order. msg_use_talk moved from extendedverbs into the
LANGUAGE LAYER (EN/ES/DE; the DE line uses the dative and names SPRICH
MIT, ES names HABLA CON; native pass pending), since menu-only games need
it and packs must translate it. Three-way test coverage (both orders +
menu-only) via a shared helper; 387 tests; ceilings re-pinned
(conversations games pay ~100 for the tell verb + hint; extendedverbs
games unchanged). H2 rebuilt (62736): TELL VLAD hints, ASK VLAD opens the
menu, the walkthrough closes at 130/130 "in 51 turns". Native pass: the
ES/DE msg_use_talk lines, and whether the packs should declare their own
ask/tell words (pregunta/frag) for menu games; the granule's verbs are
English words, flagged as a language leak to resolve with Pablo/Stefan.

SCORE IS THE ONE SCORE VERB + TELEPORT + ASK IS TALK (2026-07-04, Stefan's
blessing after stopping the "full score" phrase work; Cosmos 0.12.2): FULL
died the same day it went standard. The Infocom way, not the Inform way:
SCORE now prints score, max, turn count ("in 1 turn" singular), and the
rank when a ladder is declared, one line, three languages (DE score verb
is now "punkte"/"punktzahl"; "bilanz" died with FULL). msg_fullscore,
line_fullscore_pool, the fullscore handler, and the pool TABLE are gone:
a pool's label is author documentation (source + ledger) and no longer
reaches the story file; pools_table() folds to 0 (a future breakdown
granule would revive it). Every ceiling dropped (Cloak 14764 -> 14684;
the scoring example 15336 -> 15104). TELEPORT(dest) joined the standard
blocks: the cutscene arrival (crash, pod, trapdoor) that pays a scored
room exactly once, marks visited, and describes; the go handler funnels
through the same arrive(), so the payout rule lives once; teleport does
NOT fire on enter (walking's event); unused it folds away. The H2 port's
go_to() retired in its favor (5 call sites; story keeps only gain() for
the TAKE-bypassing plate and slab). ASK IS TALK in menu games (Stefan:
"TELL holds no right to exist but ASK shall be mapped to talk"): the
conversations granule declares verb "ask" -> talk noun / talk noun about,
so ASK VLAD (and "ask vlad about the vines") opens the menu instead of
lecturing; the about-literal grammar line matters, it puts "about" in the
dictionary as a phrase boundary, or the matcher spans "vlad ... vines"
into a disambiguation ask (caught live in the H2 walkthrough). H2 verifies
130/130 "in 50 turns, which earns you the rank of Savior of the Universe."
385 tests; amalgam + all artifacts rebuilt. Native pass items: the ES/DE
score lines reworded (turns clause), the DE ask wording, ranks.

FULLSCORE GOES STANDARD, THE PORT GOES LEAN (2026-07-04, Stefan's ruling
on the Act II review): score reporting belongs to the score mechanic, so
FULL/FULLSCORE moved from the extendedverbs granule into the standard meta
verbs. The agnostic handler (actions.prelude) walks the labelled pools
through the new language hook line_fullscore_pool; msg_fullscore gained a
singular branch ("in 1 turn"); the whole pool walk folds under any_awards,
so a game with no award statement pays only the verb, the stub, and the
message: ~150 bytes (Cloak 14612 -> 14764), while the extendedverbs and
interrogation examples SHRANK. ES gets "desglose"/"logros", DE "bilanz"
(both flagged for the native pass). Cosmos 0.12.1, amalgam regenerated,
ceilings re-pinned, scoring example no longer summons a verbset for FULL,
384 tests. AND THE PORT DROPPED summon.extendedverbs (Stefan: importing a
verbset for three verbs is not memory efficient; his .inf defined them in
code and so does the port): CUT is a single story verb (the vines answer,
elsewhere "nothing here needs cutting"), SEARCH is grammar-mapped straight
onto examine, SWIM answers at the riverbank with Vlad's wading line, BURN
is out of the game. h2-slice.z5 65904 -> 62832 bytes; walkthrough still
130/130, FULL says "in 50 turns". ASK/TELL are not in the H2 build (menu
game); noted in the port header as a sweep item awaiting Stefan's call.

H2 ACT II PORTED WHOLE (2026-07-03, Stefan's go): the Alien Wilderness
through the Hidden Station, ending at the pod's arrival in the Plaza of
Reflections (the Act III boundary stub). Verbatim prose from the .inf; the
full walkthrough for Acts I+II runs end to end on dfrotz and finishes at
130 OF A POSSIBLE 130, Savior of the Universe, with the max self-summed
(12 award sites + 14 auto-scored; the ledger agrees). ZERO compiler or
Cosmos changes were needed: the whole act is story-level Arcturus. What
the act exercises: summon.extendedverbs joins the port (the original is
OPTIONAL_EXTENDED_VERBSET + FULL_SCORE; CUT/BURN/SEARCH/SWIM answer, FULL
prints "in N turns"); the hull plate and power cell (off-stage things via
plain parentless declarations, custom take refusal while shut in); the
razor vines and the pod as Vlad topic unlocks (examine-hint and try-enter
set the gate flags, exactly the Inform status-30 flips); the statue slab
handing the shard straight to the player; the riverbank pedestal as a
RECIPIENT-dispatch put; the phase-threshold planet puzzle, eight planets
carrying a LIVE `orbit` number property (change p.orbit swaps neighbours,
planet_at() walks the hologram's children, print_order() recites the
system, is_aligned() opens the door): a mutable-array puzzle with no
arrays, properties did it; the Keeper's ten-beat conversation chain as
`when`-gated topics reproducing the talk array's relative activations
(branches show as 2- and 4-option menus, walkthrough stays all-1s); the
sanctum's sealed exits; the pod's one-way ride with the spray-oil
softlock guard. SCORING HONESTY: story code that bypasses GO/TAKE (crash,
plate, slab, pod) pays through story-local go_to()/gain() blocks that
mirror the Cosmos payouts; this also fixed the SLICE's crash landing,
which had seeded `visited` without paying the wilderness (an unreachable
5, the exact 355/350 failure class), and the holographic star needed
`fixed` or it auto-scored as takeable while refusing TAKE. Three .inf
typos fixed in the port and noted in its header ("TThe pod's", the
"tortureous screech", the missing period after "gardener in the sector").
Harness lore: the intro now overflows dfrotz's default height, so pipe
with -h 5000 AND two leading blank lines (quote box + press-any-key each
eat one). Ledger at Act II: 54 objects, 61 grains, 15 topics, globals
78/240, story 65904 bytes. NEXT: Act III, the City of Glass, chapter by
chapter (Science District first: stellar map, temporal lab, nexus slab,
Genesis; needs a USE verb for "use X on Y" per the walkthrough's synonym
note). The quality-sweep list in the slice header still stands.

EXAMPLES SPEAK THE TRIO (2026-07-03, Stefan's call before Act II): the sweep
after the declaration trio landed. Every shipped example that still said
`global` for a flag or a counter now declares its role: Cloak's `disturbed`
is a `counter` with `disturbed++` in the bar's each_turn (docs/01 section 19
listing and the docs/02 note synced in the same commit), and `polished`
(computed-properties), `door_open` (scoring), and `content` (ambience) are
`flag`s with true/false and bare truthy tests. No other example declared a
global; brass-lantern, posada, and gasthaus were already clean. The VSCode
grammar needed nothing: `flag`/`counter` heads and the `++`/`--` operators
went in with the trio commit and the 0.9.0 vsix already carries them. All
four examples recompiled, 384 tests green.

THE DECLARATION TRIO (2026-07-03, from Stefan misreading a counter beside
booleans in the slice, then the design talk): story state now declares its
ROLE. `flag x` (boolean, starts false, no initializer written; `= true` for
the rare pre-set one; only ever true/false, enforced at compile time),
`counter x` (a number that counts, starts 0; the mechanics `x++` / `x--`
belong to counters alone, lowered to the Z-machine's own inc/dec, two
bytes), and `global` stays the general drawer (values, object references,
strings). `=` appears ONLY at the declaration; play-time assignment remains
the one way, `change x to v` (his own design principle, re-confirmed when he
floated `x = 14` as a statement). All three are Z-machine globals underneath;
the head is for the reader and the compiler, which can bit-pack flags later
WITHOUT source changes (Puny's ext_flags idea absorbed as a future
transparent optimization; packing saves no file size, the globals region is
fixed 480 bytes, it only relieves the 240 count, so: later, if ever). FOUND
AND FIXED ON THE WAY: string globals were accepted but silently broken
(never seeded, printed as a number); a text global now holds its packed
string address (seeded via the layout string pool) and ${motto} prints as
text. The H2 slice's state block reads `flag`/`counter` now, with
grill_pushes++ in the grill handler. docs/01 section 4 rewritten around the
trio; extension grammar and vsix updated. 384 tests (test_globals.py 5).

VERSION 0.9 / COSMOS 0.12 + THE VSCODE EXTENSION CAUGHT UP (2026-07-03,
Stefan's call after the scoring round). The extension grammar (0.4-era,
predating B7) now knows everything since: the language-pack declarations
(direction/particle/pronoun/chain/noise/all/language), player.-forms, the
bare der/die/das gender lines, `in scope`, ranks and ambience heads with
their modifiers (about/order/at/percent/points/turns), the award statement
with its pool, zcolor targets and say.<colour>, the scoring and banner
metas, the new attributes (an/feminine/neutral/scored) and properties
(article/indefinite/tag/plural), and the author-facing builtins (way, grain,
refused, ambience_rate). arcturus-0.9.0.vsix rebuilt; the old 0.4 vsix
removed. Also this round: the scoring showcase (The Apprentice's Trial,
examples/features/scoring.storyarc: auto-pay with every exclusion visible,
a grain-body award, the two-way vault-door pool, mixed rank pins; max 38,
never typed) and A REAL MATCHER FIX it uncovered: the two-noun phrase
boundary split at ANY flagged word, so "pick LOCK with nail" emptied its
own phrase ("lock" is also a verb); the boundary is now only the joining
words (prepositions and the in/on/an/auf class), regression-pinned with
"unlock lock with key". Rank pins gained explicit units the same day
("at 17 percent" / "at 320 points"; the bare form read wrong). 379 tests.

SCORING: SCORE JUST WORKS (2026-07-03, Stefan's vision after rejecting my
Inform-shaped scored attribute and then my hand-typed plan table; his words:
in Inform score is the single biggest burden, he never once shipped a game
with max_score right, "355/350" was a YouTube title). THE DESIGN, ruled
through three rounds: `scoring` in the game block turns it on; EVERY room
pays 5 on first visit and EVERY takeable thing 5 on first take,
automatically, EXCEPT the start room and start inventory (nothing is earned
by beginning) and anything a plain take refuses (fixed/scenery/animate/
doors); `scored false` opts one out; `award N` (a statement, legal anywhere)
covers events and PAYS ONCE PER SITE by construction; `award N for pool
"label"` makes alternative branches one pool, paid once, counted once at its
MAXIMUM. MAX_SCORE COMPUTES ITSELF from all of it and is never typed. RANKS:
a bare list of titles spreads evenly across the summed max (pins as percent:
"Slayer of the Prime Unit" at 90); msg_score announces the rank in all three
languages (ES/DE wordings pending native pass). FULL SCORE (extendedverbs)
prints the Infocom breakdown from pool labels, reporting what the
PLAYTHROUGH earned (the earned byte stores the awarded points, not a flag).
The compile ledger prints the whole plan: "scoring 6 award sites, 0 pools,
6 auto-scored; max_score 60, 7 ranks". MECHANICS: sema pre-scans every body
for award sites (pools/anon registries), the auto-scored bits are set after
member collection (an early-pass bug let `fixed` slip; caught by tests),
earned bytes live in a dynamic table (__awards__), the rank ladder and
labelled pools are layout tables with string fixups, thresholds patched in
build_story once max is known. `change score` stays as the documented
off-road escape. The H2 slice: `scoring` + 6 awards + the original's 7-rank
ladder pinned at its Inform thresholds; auto-max 60 for Act I; the hand-set
355 is GONE, which is the entire point. docs/01 has the new Scoring section
(6a). 377 tests (test_scoring.py 7).

THE SLICE-REVIEW BATCH (2026-07-03, Stefan: "All of them. When we encounter
something, we fix it. That was the deal."). Five rulings, five features, one
commit. (1) THE SCOPE ROOM, his design: `thing vlad of character in scope`
places an object BACKSTAGE, an invisible seeded room whose contents are in
scope everywhere (in_scope hook + scope_room()/any_scoperoom() fold, zero
unused); `move x to scope` stages at run time. Replaces the spans hack for
Vlad and his parts, and closes gap G4: examining the droid reveals the chip
backstage, so TAKE CHIP gets Inform's honest "no chance to reach it". Never
listed; backstage objects defend themselves in handlers. (2) G6 RESOLVED,
RECIPIENT DISPATCH: dispatch consults the SECOND noun's handlers between the
noun's and the room's, so "give chip to vlad" runs Vlad's own on give (the
H2 handler moved back where it belongs) and "put chip in reservoir" gets the
reservoir's refusal. ~40 bytes core. (3) SCORED: the attribute + room_score/
object_score knobs (default 5, core.prelude, retunable); a scored room pays
on first visit (incl. the start room; run_game now marks the start room
visited, a latent double-pay bug), a scored thing on first take; folds to
zero unscored. The slice's manual awards became attributes. (4) THE TAG:
a `tag` text property (usually `tag block`, print with show) appended in
listings and inventory via the shared show_tag hook in all three packs:
"a fluid canister (full)", closing gap G2 without touching print_obj.
(5) START TITLE: with the statusline summoned the opening description skips
its title line (title_in_bar seam, hide_title), the Puny start-screen
convention Stefan screenshot-diffed. Batch cost ~84-88 bytes per game
(recipient dispatch + title seam + tag hook; scored and scope room fold).
369 tests (test_worldfeatures.py, 7). The slice uses all five; its gap list
is now: G6 resolved, G4 resolved, G2 resolved, G1/G3 resolved earlier; only
G5 (emphasis colour yellow, Stefan's eye) and the quality-sweep list remain.

THE AMBIENCE GRANULE (2026-07-03, Stefan approved the proposal whole and
ordered v2 in v1, "I hate the idea of touching it again"): summon.ambience.
An `ambience` block on a room plays while the player is there, on a thing
while it is in scope (companions, radios). Header modifiers in topic style:
`about N turns` (living odds: silence shortens them, a fired line resets,
the Inform probability-ramp as one word), `every N turns` (strict clock),
`in order` (recites, cycles), `in order once` (exhausts itself), `when`
(live block guard). Lines are strings or `do <block>` (computed), each with
an optional trailing per-line `when`. One line at most per turn. The dial:
ambience_rate (default cadence; 0 mutes everything, runtime-changeable).
MECHANICS: compiler emits per-block play/guard/line-guard routines (rooted
via the topic-table fixup pattern) plus a live table in the object-table
blob (__ambience__ global seeds the base); the driver is ~100 lines of
Arcturus IN THE GRANULE (ambience_pulse/amb_try) walking the table with
peek_word/call_handler. No-repeat relaxes after three draws so a block whose
only eligible line was just told repeats rather than dying. TWO LATENT
COMPILER BUGS FOUND: global INITIAL VALUES were never seeded (every global
ever written started 0 by luck; ambience_rate = 8 was the first nonzero
initializer; build_story now seeds numbers/bools/object refs), and ambience
`when` guards needed the sema is-test resolution that topic guards never
exercised. DOCS carry Stefan's boundary rule: one line firing until a
condition flips is a plain daemon, no granule; ambience is for shuffled,
breathing texture (NPC behavior, layered room mood). The H2 slice's
hand-rolled vlad_ambience is GONE: the three rooms carry the FULL seven-line
Inform vlad_msg lists as ambience blocks now. Showcase: The Last Ferry
(examples/granules/ambience.storyarc: jetty on living odds, waiting room in
order once with a do-line, a thing-mounted purring cat gated on mood, WAKE
CAT turns the dial). Zero ceiling drift: unsummoned games are
byte-identical. 362 tests. Also this session, from Stefan's slice review:
booleans confirmed first-class (the slice's flags rewritten true/false; the
1/0 style was the porter's, not the language's), clear_screen() and
random(n) intrinsics, the topic once-vs-when-vs-reveal doc passage, and the
H2 prelude now clears on a keypress like the original. STILL AWAITING
RULINGS: the scope room (his design, proposal costed), scored property,
G6 recipient dispatch, the listing tag ("(full)").

THE H2 VERTICAL SLICE (2026-07-03, checkpoint item 3, DONE): all of Act I,
ported verbatim from the Inform source into hibernated2/hibernated2.storyarc
(GITIGNORED with the game; only core fixes and this log are committed). The
slice: the Sagan quote box, the full pregame prose, white/cyan zcolors,
banner false with print_banner() fired mid-launch, Olivia's player.desc and
player.words, Vlad as a spanning scenery character whose TALK menu topics
are when-guarded on story flags (the Inform talk-array statuses map 1:1 to
`when` guards; topic bodies carry change/score statements and it all just
compiled), three rooms with computed desc/intro blocks (a `briefed` custom
attribute delivers the first-visit Vlad line after the room desc), the
cheap-scenery lists as grains, the fill/oil custom verbs, the whole cradle
puzzle chain, and the crash into a stub Alien Wilderness. THE WALKTHROUGH
RUNS END TO END on dfrotz with the exact Act I commands (plus one leading
blank line: the quote box keypress eats a piped line; a human is fine).
Score 55, ledger at the slice: 29/48 attributes, 22/62 properties, 55/240
globals, 33.4K raw (abbreviations untuned). TWO CORE BUGS FOUND AND FIXED:
print_banner() mid-handler burst the pending paragraph break into the
headline line (cosmos_banner now flushes first, the print_name lesson
again), and one design gap worked around in the port. THE GAP LIST for
Stefan, from a real game: (G6, the big one) DISPATCH NEVER CONSULTS THE
SECOND: "give chip to vlad" cannot be answered by Vlad's own handler, only
by the chip's (Inform asks the recipient's life). Design question: should
give/show (all two-noun verbs?) consult second's handlers after noun's?
(G1) no clear_screen() intrinsic (H2 clears after the prelude and elsewhere;
erase_window is already used inside quotes). (G3) no random() intrinsic
(Vlad's ambience is probabilistic with a no-repeat buffer, save-quips
random; slice rotates deterministically). (G2) no computed short names (the
canister's "(full)/(empty)", Inform short_name; print_obj is static; would
need name-via-routine printing). (G4) an unreachable-but-visible object
(chip in the droid) has no scope story: Arcturus tree scope hides it wholly.
(G5) emphasis colour guessed as yellow pending Stefan's eye. NEXT: Stefan
plays the slice; rulings on G6/G1/G3 (G2/G4/G5 can wait); then Act II
onward, region by region, walkthrough-driven.

NOUN LISTS TO CORE + THE GATING FINISHED (2026-07-03, Stefan's rulings after
his cost review). THE PROCESS RULING FIRST, standing and recorded in memory:
core-touching decisions in modular work are HIS to make; talk any parser
baggage through with him before building (he backs vetoes both ways; what he
cannot accept is deciding without the talk). Then the two orders, both done:
(1) THE GATING: the sweep hand-off consumption in run_turn no longer uses
unguarded locals; the flags are cleared in the undo-rewind branch instead
(guarded, folding), so a game summoning neither granule now carries only the
matcher's plural_ok argument (~25-30). (2) NOUN LISTS ARE CORE, his ruling: a
player expectation in every language, wrongly squeezed into plurals (nobody
expects lists from a granule named plurals). verb_fallback and the chain_prev
bookkeeping moved into the skeleton unguarded; "take lamp and box" now works
in EVERY game, every language (the list words are the localized chain words),
refusal and turn rules identical to chains; a bare noun on its own line is
still no command. The plurals granule is now group words + THEM only. Lists needed one more
core piece, found by the Spanish check ("coge la lampara y la llave" refused
on the ARTICLE): the packs now declare NOISE WORDS (`noise "the", "a", ...`;
el/la/los...; der/die/den...; dictionary flag 0x03, exempt in is_separator),
and the borrow rule is strict: every word in a list leg must be KNOWN and one
noun-like, so "take lamp and the box" lists while "take lamp and frobnicate
box" honestly refuses (the typo-swallow the pinned test caught). Net core
growth for lists + noise, ~68-116 bytes per game (packs with more articles
pay more), the reclaimed gating netted against it; ceilings re-pinned. 355
tests; docs 01/02 (8b documents lists as core, the old v1-misparse note gone,
the Tokenizing noise-word line is now true), 05, and the showcase header
synced. Versions bumped the same day: arcc 0.8.0 / Cosmos 0.11.0.

THE TWO GRANULES (2026-07-03, Stefan's reframe: the library is the product,
H2 the proof, so library feature-completeness comes first and the granules
land BEFORE the H2 slice). Both are pay-for-use and English-worded with the
fork as the translation route (his ruling, reinforced: granules are a
sophisticated starting point, not a maintenance program; extendedverbs and
verboseexits set the precedent). (1) SUMMON.TAKEALL: TAKE ALL / DROP ALL /
TAKE ALL FROM <container>. New `all "all", "everything"` declaration (last
free dictionary flag bit, 0x01); the parser hands a command carrying an
all-word to the granule's run_all with a bound noun as the source, so the
FROM form needed no grammar. Every swept item is a FULL TURN (daemons and
clock per item; HIS anti-Inform ruling: doing three things costs three
turns); a custom `on take` refusal prints after the item's name and the
sweep continues; UNDO takes the whole sweep back (one typed command); empty
sweeps and "eat all" refuse (chain stops). The sweep prints compactly (the
pending per-item break is dropped). Also fixed: print_name was the one text
output bypassing the paragraph flush (a latent bug; the only cost,
~52-60 bytes, non-summoning games otherwise fold to zero). (2)
SUMMON.PLURALS, all three ruled parts: GROUP WORDS (new `plural` list
property, emitted like words; a group word matching several in-scope objects
sweeps them via the shared sweep_one, matching one binds singular, the
singular vocabulary still asks); NOUN LISTS ("take lamp and box": a
verb-less chained segment borrows the previous verb, verb_fallback; the list
words ARE the localized chain words so forks get lists free; the noun phrase
starts at word 0 when word 0 is no verb); THEM (pronoun them "them", which
DOUBLES as the compile-time marker any_plurals() folds on; THEM re-runs the
last group word, so it covers what remains in scope; a Spanish fork should
OMIT it, clitic plurals already serve). Two-noun slots pass plural_ok 0 (no
sweeping into "put coins in box" second slots, v1). Unfolded residue in
plain games ~72-76 bytes. Showcases: examples/granules/take-all.storyarc
(The Collector's Study) and plurals.storyarc (The Numismatist); docs 01/02/05
and message-set updated; 352 tests (test_takeall.py 8, test_plurals.py 8).
Stefan considers the library FEATURE-COMPLETE with disambiguation done;
further parser features need a byte-cost pitch first (see memory). NEXT: the
H2 vertical slice (checkpoint item 3). A VERSION BUMP is proposed: the B8
preludes are effectively closed.

DISAMBIGUATION (2026-07-03): item (2) of the checkpoint queue is DONE, both
stages, Stefan's ruling ("I want both now", B first then A). STAGE 1, THE
SCORING MATCHER: match_phrase (parser.prelude, agnostic, single copy; the
packs' match_noun/resolve_two_nouns/named_unseen are thin calls) scores every
in-scope object by how many typed words of the noun phrase its `words`
contain and binds the unique best; "gold coin" beats "coin", adjectives
narrow per slot in two-noun commands (the phrase boundary is the first
separator), and a TIE is parse_fault 3 instead of silently taking the first
object in scope order (the coin hole is closed). The container knowledge
("open the chest first"), pronouns, spans, and the grain fallback ride along.
TWO REGRESSIONS the suite caught, both fixed: the noun phrase must slice at
grammar PREPOSITIONS only (flag 8), not any flagged word ("ask guard about
pebble" was tying guard with pebble), and scoring must test vocabulary
membership regardless of flags (a person named Pat survives "pat" the verb;
"talk to pat" broke first). STAGE 2, THE ASK: an ambiguity now asks "Which do
you mean, the gold coin or the silver coin?" (list_which, framing per pack:
line_which_open/or/item/end; German declines the accusative, "den Hammer oder
den Meissel", via the ${the:acc} tag; Spanish "?A cual te refieres...?",
WORDING PENDING NATIVE BLESSING both). The answer is read through the shared
text buffer after saving the command to a new 62-byte backup region
(ASK_TEXT_ADDR, ask_addr() intrinsic): a verb- or direction-initial answer
REPLACES the command (change of mind); anything else is woven into the saved
line right after the ambiguous phrase (ask_at) and the whole line re-parses,
so "gold" resolves exactly like "take gold coin" typed whole; still-tied
re-asks with the grown line; empty or unweavable answers fall back to
msg_be_specific. The ask is a mid-turn read, so a queued chain tail dies with
it (safe, documented). COST, flagged for Stefan: chaining plus both stages is
about 1.7K per game total (Cloak 12532 -> 14232, still well under Puny 27K);
the ask alone is ~900. Docs/02 section 8 now describes the real matcher (and
marks multi/all as NOT BUILT, ruled a someday-granule); message-set gained the
line_which rows. 334 tests (test_disambiguation.py: 12, including the German
accusative ask and answer-weave round trips). NEXT: checkpoint item (3), the
H2 vertical slice.

COMMAND CHAINING (2026-07-03): item (1) of the checkpoint queue below is DONE,
to Stefan's rulings. "take the lamp and open the door then go north" runs as
three full turns; the separators are the language layer's new `chain`
declaration (",", "and", "then" / "y", "luego" / "und", "dann"; a run of them
chains once, a trailing one is harmless). The split is buffer surgery in the
agnostic skeleton (parser.prelude chain_split/chain_next): the typed length
byte is cut at the chain word (dictionary flag 0x02), the tail stays in the
text buffer, and after a successful turn the consumed part is blanked and the
line re-tokenized; nothing is copied. THE CHAIN STOPS AT A FAILURE via the new
author-visible `refused` global: every library refusal path (actions.prelude,
extendedverbs, the generated grain scenery default, msg_open_first) sets it,
and run_chain (loop.prelude) stops the line; a story handler refuses the same
way (`change refused to 1`, docs/02 section 8b). ONE JUDGMENT CALL OF MINE FOR
STEFAN TO VETO: an outcome that ALREADY HOLDS ("you already have it", "it's
already open", "already worn") does NOT stop the chain, only genuine can't/
won't refusals do; one-line reverts per site if he wants strict. AGAIN repeats
only the LAST command of a chained line (Option B, his ruling; falls out of
the per-turn last_* replay). Safety: undo, restore, and any mid-turn line read
(quit/restart confirmations share the text buffer, killed in the read_input
seam) drop the queued tail, so a rewound state never replays it. Known v1
limit, ruled acceptable: "take lamp and box" misparses (noun lists are the
plural-model granule, someday); "take lamp and take box" works and is pinned
in the tests. Cost ~570-640 bytes per game, ceilings re-pinned. 321 tests
(test_chaining.py: EN incl. grain-refusal stop and Option B, ES, DE); Frotz
verified in all three languages, pronoun-in-chain included ("nimm die lampe
und untersuche sie, dann geh nach osten"). Amalgam and posada/gasthaus.z5
rebuilt. NEXT: checkpoint item (2), disambiguation.

Pre-B8 assessment rulings (2026-07-02, Stefan): capacity hardening (attribute
spill, a capacity report) waits until B8 itself surfaces the need; the ports
exist to teach us where the system lacks. The synthetic scale smoke test is
step zero of B8. Landed now instead: the size-regression gate
(tests/test_sizes.py, a byte ceiling per example plus the PunyInform benchmark
check; 293 tests) and docs/07-conformance.md (the conformance claim, the
interpreter-driven evidence, the size record: the 11792-byte Cloak is to our
knowledge the smallest runnable Cloak registered to date). Also cleared: the
README em dashes and the stale find_particle comment in german.granule. Next:
an idiom-focused review of both translations (Stefan's request; German got his
native pass already, Spanish still gated on Pablo), then B8.

>>> B8-PRELUDES HANDOVER CHECKPOINT (2026-07-03, written for compaction) <<<

WHERE WE ARE. B8 (the Hibernated 2 port) is open; its source and walkthrough
sit in hibernated2/ (GITIGNORED, unreleased, never commit; 4082 lines of
Inform, 115 objects, 61 game globals, 557-line walkthrough = the future
automated port verifier). The toolchain enablers the port needed are ALL DONE
and verified: scale smoke (tools/scalegen.py, green), zcolor + say.<colour> +
zcolor.statusline/input (Flags 2 bit 6 announced; guard degrades colourless),
the quotes granule (Trinity box), banner false + print_banner(), arcc verbose
CLI (banner + stats ledger default, -q for scripts), buffer_mode + the
pending-break HOLD discipline in all upper-window granules (real-frotz
verified via the pty harness; dfrotz proves logic, NOT rendering), grain
chains (same word, many rooms; any_grains fold), open-with-key, per-object
articles (article/indefinite; capitalization-at-sentence-start LIMIT
backlogged, stream-3 capture is the fix), state qualifiers ("(closed)", with
Spanish gender agreement), the Spanish infinitive retry (-r) and CLITICS
(-lo/-la/-le/-les/-te + accent fold; NOT dictionary words, pending-slot
design; PunyInformES reconciled, its -les bug reported to Pablo and CONFIRMED,
he is fixing), pronouns part 1 (it/him/her slots; English animacy, German
grammatical gender es/ihn/sie; them AWAITS A PLURAL MODEL), and the player
object (standard self-words per pack, player.words ADDS, player.desc plain or
block, msg_examine_self in Stefan's wording, take-self ordering fixed, words
lists accept reserved words). Both language packs carry native passes (German
Stefan, Spanish Pablo Martinez, credited in README/granule headers).

VERSIONS arcc 0.7.0 / Cosmos 0.10.0 (a bump is due when B8 preludes close).
311 tests pass; the size gate (tests/test_sizes.py ceilings) must be GREEN
before any commit (one slip happened, amended). Artifacts current: build/arcc
(amalgam; regenerate at every milestone), build/posada.z5 + build/gasthaus.z5.
The pty harness lives in the scratchpad (drive*.py, render.py + pyte venv);
REBUILD IT after compaction if upper-window/colour work recurs.

NEXT, IN ORDER (all RULED by Stefan 2026-07-03, implement one by one after
compaction): (1) COMMAND CHAINING: separators and/then/comma (Spanish y/luego,
German und/dann), STOP the chain on a failed segment, AGAIN repeats only the
LAST segment (Option B, his ruling: our again machinery already stores the
resolved command, and whole-line replay re-fires side effects); v1 accepts
that noun lists misparse ("take lamp and box"), because "take lamp and take
box" works. (2) DISAMBIGUATION, a real hole found 2026-07-03: two objects
sharing a word ("gold coin"/"silver coin", both `words coin`): "take coin"
SILENTLY takes the first in scope order; msg_be_specific exists but nothing
fires it. Design an ask ("Which do you mean, the gold coin or the silver
coin?") or at least a "be more specific" refusal on ambiguous matches.
(3) then the H2 vertical slice (opening through the first walkthrough
checkpoint), watching arcc -s (globals tightest, ~197 of 240 expected).
GRANULES SOMEDAY, ruled: the plural model (English-only granule, authors of
other languages fork it; most games do not need it: Stefan's Ghosts slabs
trick, one object dividing on take, covers the common case) and TAKE ALL
(separate granule; the core deliberately omits it: it flattens scenes into
transactional loot runs). BACKLOG unchanged: article capitalization at
sentence start, dative-safe player name, docs/07 as evidence grows.

MSG_EXAMINE_SELF ROUND (2026-07-03): "x me" with no player.desc used to fall
to the object message (EN wrong voice, DE doubly broken: dative "an DIR
selbst", ES lowercase-broken); now a dedicated msg_examine_self in Stefan's
wording ("Are we going to admire ourselves for a while or do we play an
adventure game?"), DE/ES siblings pending native blessing.

THE PLAYER OBJECT (2026-07-03, Stefan's design): every game answers to the
standard self-words with no author code: me/myself/self/yourself/you (EN),
mich/dich/selbst (DE), yo/mismo plus the -te clitic (ES), declared by each
language pack with the new top-level `player.` syntax. A game augments the
seeded player the same way: `player.words olivia, lund` ADDS to the standard
words (they accumulate, never overwrite, per Stefan's spec), `player.desc`
sets the description plain or as a computed block (`player.desc block`), and
any player property can be set (name, custom flags; last wins). Packs also
give the player a printable name (yourself / dich selbst / ti mismo) plus
`named`, which closes the "El  no tiene nada" artifact from the clitic round.
Two collaterals fixed on the way: `words` lists now accept RESERVED words as
vocabulary (words self, you: the player types them without knowing our
keywords), and take-self answers its own message before the animate refusal
("take me" said "yourself has other ideas"). docs/01 section 5a, docs/02 14a;
test_player.py; 310 tests pass.

PUNYINFORMES RECONCILIATION (2026-07-03, subagent over
github.com/Kozelek/PunyInformES): Pablo's translation.h/parser.h confirmed our
architecture point for point (clitics before the -r retry, unknown-words-only
guard, space-over-r, articles protected). Adopted from his code: -le (leismo,
taken as masculine), -les (plural), -te (reflexive, the player: "examinate"),
and his ProcessChars ACCENT FOLD: the Spanish pack now de-accents the typed
buffer (a/e/i/o/u/u-diaeresis/n-tilde, ZSCII 169-173/157/206) and re-tokenizes
before any lookup, so "cógela" typed with its tilde works (verified with
UTF-8 input on dfrotz). NOT adopted: his hyphen-word trick (we use the pending
slot instead, no dictionary pollution, no "-lo" leaking into error messages
as it does in Puny's MSG_PARSER_NO_IT). FIXED relative to his code: his
'-les' maps to the feminine SINGULAR referent (la_obj), almost certainly a
bug; ours maps -les to the plural slot. STEFAN: worth relaying to Pablo, plus
his own "! TODO terminaciones" comment suggests he knows the area is
unfinished. Also surfaced: the default player object has no name, so
"examinate" prints "El  no tiene nada de particular."; players deserve a
default name and desc, backlogged. The retry chain was also rewritten as one
shared split path after the branch-per-suffix shape hit the 15-local ceiling
in resolve_verb (the compile sat exactly at the cliff).

PRONOUNS, PART 2, THE SPANISH CLITICS (2026-07-03): "cogela" works. An
unknown first word ending in -lo/-la/-los/-las splits its clitic off in the
typed text (the same buffer surgery as the infinitive retry), the verb
re-resolves, and the pending clitic (a granule global, `clitico`) becomes the
command's noun in the Spanish resolve_objects, read from the part-1 referent
slots (lo -> him, la -> her, los/las -> them). Chains with the -r retry:
"cogerlo" -> "coger" (la pending... el pending) -> "coge". THE KEY DESIGN
POINT: the clitics are NOT dictionary pronoun words, because bare la/los/las
are the ARTICLES; "coge la lampara" must keep resolving the lampara, and does
(pinned in the test). Out-of-scope referents and the empty plural slot fall
into the honest "No ves nada de eso por aqui." docs/02 8a updated; +424 bytes
on Spanish games only (pay-for-use holds). A PunyInformES reconciliation pass
(github.com/Kozelek/PunyInformES, via subagent) follows to compare suffix
coverage (le/les?) and any guards Pablo uses that we lack.

PRONOUNS, PART 1 (2026-07-03): Arcturus has pronouns. Four canonical referent
slots (it/him/her/them, prelude._PRONOUN_ROLES, the particle-roles pattern);
a pack declares its words (`pronoun her "sie"`) and a note_pronouns(obj) rule
deciding which slot a resolved noun fills: English by animacy (character ->
him/her by gender, else it), German by GRAMMATICAL gender (die Lampe -> sie,
der Schluessel -> ihn, das Buch -> es; accusative forms, the object of a
command), Spanish fills the slots silently for the clitics (part 2, from
github.com/Kozelek/PunyInformES). Mechanics: dictionary flag 0x04 carries the
role id; scope_match resolves a flagged word to its slot's referent IF still
in scope (else the honest "you see nothing of the sort"); is_separator exempts
the flag, so a pronoun binds in either noun slot ("put coin in it"); the
skeleton's parse() notes the noun after each command (never the player); the
referents are the pron_* builtins, library-visible. docs/02 section 8a.
Verified on Frotz in both languages, two-noun binding and out-of-scope
honesty included; 308 tests pass. NEXT: part 2, the Spanish clitics
(cogelo/cogela/cogelos/cogelas by suffix-stripping, studying PunyInformES
first), then the command-chaining discussion.

PABLO'S ROUND, ITEMS 3-5 (2026-07-03, Stefan's ruling: 3-5 now, pronouns
next, clitics from github.com/Kozelek/PunyInformES, chaining discussed after):
(3) THE INFINITIVE RETRY, Spanish only: an unknown first word ending in -r
loses the -r in the typed text itself and the command re-tokenizes (new
text_addr/retokenize intrinsics on the tokenise opcode, VAR:0x1B), so a
regular infinitive finds its imperative: "comer pan" reaches "come". The
recursion terminates because the word shrinks. (4) STATE QUALIFIERS: a closed
openable announces itself in listings, per pack with its own agreement: "Ves
un cofre de roble (que está cerrado)." / "... (que está cerrada)." (gender),
"(closed)", "(geschlossen)" (predicative, invariant). Composes with the
knowledge model: "a wooden box (closed) (contains a gold coin)". (5) ARTICLE
OVERRIDES: `article` and `indefinite` text properties print verbatim over the
derived article (las tijeras, el agua, English "some water"), with new
article_addr/indefinite_addr intrinsics riding the desc_addr lowering. KNOWN
LIMIT, backlogged: a stored article cannot capitalize itself at a sentence
start ("el agua no tiene..."); the clean fix is runtime capitalization via
output_stream 3 capture, a candidate to ride the pronoun work. NEXT: pronoun
support part 1 (general "it", no pronouns exist in Arcturus at all yet), then
part 2, the Spanish clitics (cogelo/cogela) from PunyInformES.

SPANISH PASSES (2026-07-03): Pablo Martinez (the maker of PunyInformES)
returned his native review in under two hours: "very impressive", and his pass
on spanish.granule amounted to a single edit, dropping the trailing "aqui"
from object listings ("Ves un cofre de roble."), now applied; the granule
header records his pass. B7 IS NOW FULLY CLOSED: both language packs carry a
native pass. He also caught a game bug (the posada description said "una
puerta cerrada" forever; now neutral) and left a feature backlog worth its
own consideration, recorded here for prioritization:
- per-object article overrides (instead of the derived el/la un/una);
- the PunyInformES infinitive trick: an unknown word ending in "r" retries
  with the "r" stripped, so "comer" finds "come";
- state qualifiers in listings, Puny-style: "Ves un cofre de roble (que esta
  cerrado).";
- Spanish clitic pronouns as the "it" equivalent: cogelo/cogela/cogelos/
  cogelas (Pablo offers his PunyInformES code for this);
- command chaining ("y"/comma) is silently ignored; a GENERAL parser gap,
  affects English too ("take lamp and go north");
- (done) the aqui listing edit and the example's door description.

THE FROTZ TRUTH (2026-07-03): Stefan compiled the colour example on real
frotz and saw no colour; the quote box drew distorted. Both correct. Driving
curses frotz through a pty (pyte rendering the actual screen) found three real
bugs invisible to dfrotz: (1) the story never announced colour use in Flags 2
bit 6, which frotz requires before enabling colour at all (now set whenever a
program uses colours, plus the undo bit the Standard asks for); (2) upper
window drawing ran buffered; a correction from Stefan: the status bar DID
always render on his frotz (the earlier "never rendered" claim came from a
faulty capture tool), but the missing buffer_mode dance is real and bites
stricter interpreters: a user reported exactly this statusline breakage on
Gargoyle (new buffer_mode intrinsic; status line, menu, and box draw
unbuffered, the Inform/Puny dance);
(3) the paragraph layer's pending newline flushed INTO the box's first row
(the distortion), fixed by flushing it into the old screen before drawing.
Also added, Puny parity per Stefan: zcolor.statusline and zcolor.input (cyan
bar, cyan typed text, via a read_input() seam all input paths share). All
verified end to end on real frotz via pty capture. And the CLI is verbose by
default now (banner always, statistics after every compile, -q for scripts;
the old -s is gone), Stefan's rule. LESSON, standing: dfrotz proves logic, not
rendering; anything that touches the upper window or colours must be verified
against curses frotz via the pty harness (scratchpad drive/render scripts).

B8 ENABLERS (2026-07-03): opening the real H2 source surfaced three Cosmos
gaps, all closed the same day. (1) Z-MACHINE COLOURS as syntactic sugar,
Stefan's design: `zcolor.font white` / `zcolor.background black` set the base
colours (background repaints the screen), and `say.yellow "..."` prints one
passage in a colour and restores the base BY ITSELF, replacing Puny's
switch-print-switch-back sandwich. Every colour op checks the interpreter's
colour bit at run time, so it all degrades to plain text with no author guard.
set_colour opcode added (2OP:27); __zcfont__ reserved global; docs/01 s.16;
The Observatory showcase; the amalgam module order fixed (prelude before
parser). (2) BANNER CONTROL: the banner sits in its own routine; `banner
false` stops the automatic print and print_banner() shows it when the author
wants (H2's Initialise returns 2 to do this in Inform). The docs/02 "banner
event" claim was false and is gone. (3) THE QUOTES GRANULE (summon.quotes):
the centered reverse-video quote box, Trinity-style, H2's Sagan opening.
quote(lines, width) / quote_line() + show(...) / quote_done() (keypress,
clear); centered from the reported screen width for the 40-column targets; no
output_stream needed (full reverse row first, overprint via set_cursor); no
words of its own, so language-independent. Ad Astra showcase demos the classic
quote-keypress-banner order. 304 tests pass.

B8 OPENS (2026-07-02). The Hibernated 2 source and walkthrough live in
hibernated2/ (gitignored and never committed: the game is unreleased and this
repository is public; the real source is 4082 lines of Inform, 115 objects, 61
game globals, and a 557-line walkthrough that will later drive automated
verification of the port). STEP ZERO, the scale smoke test, is done and green:
tools/scalegen.py deterministically generates a synthetic game at H2 scale
(138 objects, 40/48 attributes, 177/240 globals, 100 verbs, 104 actions, 499
dictionary words, 192 grains with the shared-word chains stressed across all
64 rooms, 24 topics, 3 timers, 469 routines). Results: compile 0.31s; story
90788 bytes with the default abbreviations, 47488 with a tuned set
(--make-abbreviations takes 6.8s at this text volume; the synthetic prose
flatters the ratio); scripted Frotz walk green end to end (movement across the
grid, grains answering per room, container, locked door via open-with-key,
custom verbs, the conversations menu, daemons, save/restore round trip); no
Z-machine ceiling approached, per-turn response instantaneous. Conclusion: the
toolchain is ready for the port; nothing needs hardening first.

B7 closes (2026-07-02): GERMAN IS ACHIEVED. Stefan gives the German pack a full
native pass; further feedback comes from the community. Spanish is complete on
our side and with Pablo Martinez for the native gate; his changes will be
incorporated when they arrive. Last pre-B8 tool: `arcc -s/--stats` prints the
compile-statistics ledger (used/ceiling for attributes, properties, globals,
abbreviations, readable memory, story size; counts for the rest), Stefan's ask
after seeing Inform's -s output for Hibernated 2. H2's real Inform numbers, the
first pitch for B8: 126 objects, 31 attributes, 31 common props, 175 globals,
102 verbs, 239 grammar lines, 904 dictionary entries, 64 abbreviations, 134.5K
z5. Our bare-Cosmos baseline (28/48 attributes, 19/62 properties, 22/240
globals) leaves room for all of it.

Second polish round (2026-07-02, Stefan's rulings): (1) GRAIN CHAINS: a grain
word is no longer global; the dictionary entry points at a chain of (grain,
owner) pairs and find_scenery answers with the owner in scope, so the same
scenery word works in many rooms (Stefan: a modern language cannot accept the
old limit). Pay-for-use via the new any_grains() fold; grainless games SHRANK.
(2) LOCALIZED BANNER: line_by (" by "/" de "/" von ") and banner_headline (the
default headline) live in the language layer; codegen calls them with a bare-
build fallback. (3) TWO GATED DAEMONS in each localized game: the clock strikes
every 3 turns but only in the inn, whispers call every 3 turns but only at the
coast (both verified on Frotz: 3 strikes inside, none at the beach). (4)
Comment polish in the translated files; the mangled 8-bit comment in
german.granule fixed; German header now records Stefan's native pass. (5)
Pablo Martinez credited in spanish.granule and the example (his edits),
posada.z5/gasthaus.z5 rebuilt for his review. 294 tests pass.

Post-playtest polish (2026-07-02, from Stefan's German playthrough + the idiom
pass): (1) IDIOM. Sixteen Spanish fixes applied (the example carried the exact
calques Stefan had caught in German, never back-ported: camino roto, la llave
abre el patio, la silueta apagada; plus a real agreement bug, msg_no_switch "de
los que" with feminine nouns) and the German "zum Klettern" capitalization.
(2) UP/DOWN VOCABULARY. German up/down now hoch/rauf/hinauf/aufwaerts/oben and
runter/hinunter/hinab/abwaerts/unten; bare "auf" is deliberately absent (it is
the unlock particle, one dictionary role per word; bare "ab" is not German).
Spanish adds sube/subir, baja/bajar. "nach oben"/"hacia arriba" work via a
resolve_verb fallback (no verb at word 0, but a direction anywhere -> go), and
has_extra_words for go now only asks whether a direction is present, so "geh
nach oben" tolerates the filler "nach". (3) COHERENCE QA on all four games:
described-but-silent scenery got grains (steps in brass; walls in cloak;
hogar/barra/macetas/grillo/faro/rocas in Spanish; Herd/Tresen/Waende/Grille/
Steine/Leuchtturm/Felsen in German) and described verticality got exits (brass
down/up; patio-playa and hof-strand down/up). The faro/Leuchtturm grains close
Stefan's "how do I reach the lighthouse" confusion narratively: the sea took
the path. (4) DISCOVERY: a grain WORD is global to the game (dictionary maps
word -> one grain+owner; a second room's same-word grain silently steals it).
Documented in docs/01 section 14; watch it in B8, real games repeat scenery
words across rooms. (5) _STD_ACTIONS in prelude.py now carries the full
standard verb-set action names (touch/smell/listen/... and the meta verbs), so
bare --no-cosmos analysis accepts the same handler and grain names as a Cosmos
build. Ceilings re-pinned; 293 tests pass.

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
| B7 | Language packs (Spanish, German) | done (German passed; Spanish with Pablo) |
| B8 | Port Hibernated 2 (first full game, maturity milestone) | in progress |
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

## CHECKPOINT 2026-07-04 (evening): the size-triggered crash, mid-hunt

Compaction checkpoint requested by Stefan mid-debugging. THE TREE IS DIRTY ON
PURPOSE: everything below the crash section is finished work waiting on the bug,
because committing it means re-pinning ceilings and rebuilding artifacts and we
do not ship a compiler state that miscompiles a 132K game. Stefan is installing
fizmo so we have a second, stricter interpreter to interrogate the crash with.

### Uncommitted, finished, blocked only by the crash

- H2 meta trio (in hibernated2/hibernated2.storyarc, gitignored as always):
  ABOUT (turnless via meta_turn = 1), HELP/HINT/HINTS, CREDITS (van Gogh
  say.yellow lines; the tool credit ADAPTED for Arcturus, the Dialog line
  dropped: STEFAN MUST VETO THE WORDING before this counts as done), plus a
  custom free `on xyzzy` rule.
- Free-handler origin ranking (arcturus/ast.py, worldmodel.py, sema.py,
  cosmos.py, codegen.py): Handler.origin None=game < "granule" < "library",
  sorted in _free_react_handlers/_free_other_handlers. Fixes a LATENT bug:
  a story's free `on xyzzy` never overrode the Cosmos default.
- Dual-role dictionary flag 136 (dictionary.py: a word both verb and
  preposition keeps both bits; english/spanish/german packs: resolve_verb,
  arity check, is_separator accept 128 or 136; parser.prelude: the two-noun
  slicing and phrase-end scan test 8 or 136 via `let ef`). Fixes H2's ABOUT
  destroying the ask-about grammar.
- Assembler range asserts on BOTH branch encoders (relax/shrink pass and
  link() fixup): short 0..63, long signed 14-bit. Added while hunting the
  crash; they never fire, which is evidence (see below), and they stay.
- tests: 400 pass; the ~25 size ceilings in test_sizes.py are NOT re-pinned
  yet (the 136 flag + origin sort grew files slightly). Deliberate: re-pin is
  part of the post-fix commit, not before.

### THE CRASH (open, blocking)

Symptom: the full H2 build with the meta trio executes a clean @quit on FIRST
ARRIVAL at a late room. No error, exit 0, silent even under `dfrotz -Z 3`.
The room description prints in full, then the session ends where the next
output (an object intro listing) should begin.

Bisection (all artifacts in the session scratchpad, h2*.storyarc + .z5;
scratchpad dir: /private/tmp/claude-501/-Users-stefan-Fiction-Arcturus/
99e02c7e-2a33-4251-b17d-482d99262bb8/scratchpad, walkthrough wtfull.txt,
crash repro = head -128 of it):

| build   | contents              | bytes   | result |
|---------|-----------------------|---------|--------|
| h2strip | no trio               | 131,400 | OK     |
| h2about | about only            | 131,916 | OK     |
| h2help  | help only             | 131,896 | OK     |
| h2cred  | credits only          | 132,072 | OK     |
| h2ah    | about+help            | 132,244 | OK     |
| h2hc    | help+credits          | 132,400 | CRASH  |
| h2ac    | about+credits         | 132,420 | CRASH  |
| h2trio  | all three             | 132,572 | CRASH (Fabrication Hall) |
| h2pad   | h2strip + INERT padding | 133,112 | CRASH (Silent Dwellings) |

h2pad is the smoking gun: the working build plus meaningless padding code
crashes too, and at a DIFFERENT room. Pure code-size threshold between
132,244 and 132,400 total file bytes; code ends ~123.4K (code_bytes ~107.5K,
strings run from there to EOF). The crash room varies with layout, not with
turn count (WAITing instead of walking west does not crash; walking west
does, so it is the room-arrival code path of whatever routine lands past the
boundary).

RULED OUT so far:
- Branch offset overflow: asserts on both encoders, never fire.
- 16-bit set_word overflow: monkeypatch spy over a crash build, clean.
- Word/action renames, specific verbs: contents do not matter, size does.
- Interpreter strictness: dfrotz -Z 3 reports nothing (frotz/dfrotz/sfrotz
  are all we have; hence fizmo).

LIVE LEADS, in order:
1. link() jump fixups: `offset = (target - fx.offset) & 0xFFFF` is masked
   with NO range assert (the one encoder still uninstrumented). Add the
   assert (jump target = PC + offset - 2, signed 16-bit), recompile h2trio.
2. Routine address map diff: dump name -> byte address for h2ah (ok) vs h2ac
   (crash); look at what crosses which boundary near 123.4K / 128K. Note
   0x20000/4 = 0x8000: a PACKED address crosses the signed-16-bit line at
   file offset 131,072, which sits EXACTLY inside the ok/crash gap. Anything
   that stores a packed routine address into a signed context (jl/jg
   compares, a signed table lookup) breaks precisely there. PRIME SUSPECT.
3. fizmo (Stefan installing) and/or bocfel: strict terps that report wild
   jumps/calls instead of silently quitting.
4. The relax/shrink pass newpos bookkeeping; initial-PC and other 16-bit
   header fields; print_paddr of computed values.

### After the fix, in ONE commit series
re-pin the ~25 ceilings, full suite green, full wtfull.txt walkthrough
(expects 360/360, *** THE END ***, post-mortem prompt), rebuild build/arcc +
example artifacts, then commit compiler+cosmos work (origin ranking, flag
136, asserts, the fix). H2 source itself stays gitignored, as ever.

### Parked (do not lose)
- Stefan's CREDITS wording veto (see above).
- after-handler ordering oddity noticed in the post-mortem fixture (an
  `after take` seemed to run when the default was cut short; not chased).
- inline emphasis colour (show.<colour>) idea; quality-sweep leftovers (save
  quips, custom smell/listen flavor, Vlad inventory line); "next steps"
  discussion (B10 Actaea vs quality sweep) once the crash is dead.

### RESOLVED same evening: the crash was the print-or-run signed compare

fizmo (Stefan installed it mid-hunt) named what dfrotz swallowed: "More than
15 locals are not allowed" at the exact crash point. Diagnosis: computed text
properties discriminate string-vs-routine by comparing the stored packed
address against the __strings__ threshold with jl, and jl is SIGNED. A string
laid past file offset 0x20000 has a packed address >= 0x8000, reads as
negative, flips the test, and the string is CALLED as a routine: its first
ZSCII byte becomes the local count (fizmo errors, dfrotz executes garbage and
lands on a clean @quit). Pure size threshold, room-specific, content-blind:
every bisect fact matched, including h2pad's inert padding.

Fix (lower.py + codegen.py): the classic sign bias, since the Z-machine has
no unsigned compare and no xor. codegen stores __strings__ pre-biased
(+0x8000 mod 2^16, top bit flipped); the print-or-run site adds 0x8000 to the
property value into a scratch temp (v stays unbiased for print_paddr and
call_vn) and jl orders the biased pair as the unsigned originals. Cost: one
add per print-or-run site (+8 bytes on computed-properties and scoring, the
only two examples on that path; re-pinned). Regression test pins the stored
global's bias (test_intro.py::test_strings_threshold_global_is_sign_biased);
the walkthrough truth is H2 at 132,768 bytes running to *** THE END *** at
360/360 on BOTH dfrotz and fizmo-console.

Landed in one series with the blocked work: origin-ranked free handlers,
dual-role dictionary flag 136 + pack/parser updates, assembler branch range
asserts (they stay; they ruled paths out). arcc 0.10.2 / Cosmos 0.14.2,
amalgam and example artifacts rebuilt, 401 tests green. Still parked:
Stefan's CREDITS wording veto, the after-handler ordering oddity, the
next-steps discussion (B10 Actaea vs quality sweep).

## 2026-07-04 (late): the after phase existed only on paper; now it exists

Stefan's go-ahead: fix the broken-and-unimplemented before Actaea. The flagged
"after-handler ordering oddity" turned out to be the whole feature missing:
Handler.after was parsed, threaded through sema, printed by irdump, and never
consumed by codegen. `on after X` compiled as a plain `on X`: it ran in the
MAIN chain and, on ending, consumed the action, so the default never ran.
Cloak's hang-cloak-on-hook never actually moved the cloak (inventory kept it;
the walkthrough won anyway because only bar.lit mattered). docs/02 s.9 step 6
always specified the real thing; the document wins.

The implementation (arcc 0.10.3 / Cosmos 0.14.3):
- worldmodel: every action with an `on after` handler anywhere (object, kind,
  free) gets a synthetic after action, "after:<name>", numbered in a band
  between the world actions and the metas; after_floor() marks the band. The
  colon keeps the name out of the author namespace.
- codegen react: after handlers key their groups on the synthetic number, so
  they never answer the main pass. The `on other` catch-all skips the after
  band (one jl against after_floor, emitted only when the program has after
  handlers). after_map(action) -> after number (or 0) is emitted beside
  react_free, only when needed.
- lower: any_after (static fold + eval), after_of (calls after_map).
- Cosmos: dispatch itself is UNCHANGED (its early returns stay); the after
  phase sits inline at the two dispatch call sites in loop.prelude (run_turn
  and sweep_one), gated `if any_after is 1 / if grain is 0 / if refused is 0
  / let aft = after_of(act) / if aft is not 0 / dispatch(aft)`. Inline
  because a wrapper block costs its call layer even unused: the first cut
  (+12 bytes on EVERY after-free game) violated pay-for-use; this shape is
  BYTE-IDENTICAL for after-free games (audited across all 24 pinned
  examples; H2 unchanged at 124,244). Cloak pays 68 bytes for what it uses.
- Semantics pinned in docs/02: completed = refused still 0 (every library
  refusal sets it; story refusals should too); an instead handler still
  completes; grain turns take no after pass; after handlers may continue;
  on-other never answers the after pass.
- tests/test_after.py: order (default before after), refusal gates it,
  instead still fires it, free after rules, when guards, and the catch-all
  staying out of the after pass. 407 tests green. Cloak re-pinned 15220
  (z8 15688); the walkthrough now shows the cloak REALLY leaving the
  player's hands ("You're carrying precisely nothing" after the hang).

ALSO this session, before the fix: H2 compiled with custom abbreviations
(--make-abbreviations, summon abbreviations.granule): 132,768 -> 124,244,
8,524 bytes saved (6.4%), ~10K under the Inform build; full walkthrough to
THE END at 360/360 on fizmo-console. And the sign-bias crash fix landed as
5d4ca1b (see above). fizmo-console is now the debugging interpreter of
record (fizmo/ncursesw for colours); memory updated.

NEXT: Actaea (B10). Plan confirmed by Stefan (module map per docs/06 s.4,
io.py boundary, conformance harness under tests/actaea/). Story files for
conformance live in actaea/conformance/ (CZECH, TerpEtude, H2, Ghosts,
deseos for accents, Calypso, Anchorhead, Jigsaw for z8). Update docs/06 +
the handoff prompt to B10/B11/B12 numbering in the scaffold commit (Stefan
approved). Parked: CREDITS wording veto, inline emphasis colour, H2 quality
sweep list.

## 2026-07-04 (night): Actaea begins; M1 green

B10 opened per the handoff prompt (plan restated and confirmed by Stefan).
The package skeleton under actaea/ holds the M1 modules: errors.py (the
ActaeaError family; MemoryFault's docstring carries the fizmo lesson),
memory.py (the flat map with the dynamic write barrier, bounds-checked
byte/word access, packed-address unpack x4/x8, the pristine image for
restart, and to_signed/from_signed as THE one signedness conversion the
whole interpreter must route through), loader.py (the Standard 1.1 header
map in exactly one file; validates version 5/8, length claims, static base;
checksum verify), and __main__.py (`python3 -m actaea <story> --header`,
the console entry that grows into the M3+ runner and M6 harness).

M1 done-test PASSED: brass, cloak, CZECH (terminating chars + header
extension present and parsed), Jigsaw.z8 (packed x8, 304,184 bytes,
checksum verified), and H2 all load and report correctly; a non-story is
rejected cleanly with exit 2 ("version 60 story; Actaea plays versions 5
and 8"). tests/actaea/unit/test_loader.py (11 tests) builds its probe
stories with the Arcturus compiler in-process, so no binaries are checked
in; conformance-file tests skip when the directory is absent.

Conformance assets (actaea/conformance/, LOCAL ONLY, *.z5/*.z8 gitignored;
third-party copyrighted works stay out of the public repo): czech.z5 +
czech-reference.txt (the v5 reference transcript), praxix.z5 (fetched from
the IF Archive; no reference transcript exists, it self-reports), etude.z5,
ghosts.z5, deseos.z5 (accents), calypso.z5, anchor.z8, Jigsaw.z8, and H2
via hibernated2/. Praxix source praxix.inf available if wanted.

NEXT: M2, the instruction decoder and disassembler (all four forms,
extended opcodes, store/branch/inline-text flags), done when it
disassembles a real story without error and the decode unit tests pass.

TODO (Stefan, 2026-07-04): ABBREVIATION QUALITY INVESTIGATION, not now. Data
point: the Inform/Puny H2 compiles to 137K plain and 123K after Henrik
Asman's zabbrv; our build is 132.7K plain and 124,244 with the custom
granule. So our CUSTOM pass buys us less than zabbrv buys Inform (8.5K vs
14K), while our plain build already beats Inform's plain by 4K, which
suggests our BAKED-IN standard set is doing part of zabbrv's work up front
and the distorted baseline hides how good or bad the custom optimizer
really is. To investigate later: compare the two abbreviation SETS head to
head, check ours for wasted slots (96 entries, are all earning?), and see
whether zabbrv's selection algorithm (or a better one) beats
tools/arcabbr.py on the same corpus. Credits wording: Stefan writes it by
hand, off the list.

## 2026-07-04 (night, cont.): Actaea M2 green, the decoder and disassembler

decode.py is the single source of instruction truth the M3 executor and the
disassembler share: all four forms (long, short, variable, extended), the
four operand types, the double type byte of call_vs2/call_vn2, store bytes,
short and signed-14-bit long branches (offsets 0/1 = rfalse/rtrue), and
inline text kept as a RAW span (rendering is text.py's business, M5).
Opcode tables carry name/stores/branches/text per count family; illegal-
in-v5 numbers (0OP:5 old save, 0OP:12 show_status) stay in the map as named
faults with the address. The disassembler is recursive descent: the v5+
entry point is a headerless instruction stream, routines are queued from
constant-operand calls, a frontier of forward branch/jump targets decides
where a routine really ends. Output is txd-style (sp/Lnn/Gnn, -> stores,
?~target branches).

M2 done-test PASSED: cloak (202 routines), czech (68), praxix (27), etude
(3; honest recursive-descent behavior, TerpEtude dispatches through
computed calls static walking cannot follow), Hibernated 2 (387), and
Jigsaw.z8 (129) all disassemble to exit 0. The Cloak entry stub reads
`call_vn 0x0303 / quit`, the very quit the 128K crash hunt kept landing
in. 26 actaea tests (12 new decode units); 433 total. actaea 0.2.0.

NEXT: M3, the execution core: stack, call frames, locals, arithmetic and
logic, branches, load and store, call and return, jump; done when
computational test routines produce correct results headless. The io.py
interface sketch should land with it (print callbacks needed the moment
print_num works).

## 2026-07-04 (night, cont.): Actaea M3 green, the execution core

vm.py runs the computational machine over decode.py's instructions: the
evaluation stack (per-frame, exactly the shape Quetzal's Stks chunk wants
back at M10), call frames with locals/return-pc/store-target/argc, and the
run loop. Implemented: signed arithmetic with truncating div/mod, bitwise
ops and both shifts, all comparisons (je's multi-way form, signed jl/jg),
inc_chk/dec_chk, jump, load/store/loadw/loadb/storew/storeb, push/pull,
the Standard 6.3.4 indirect-variable quirk (a reference to variable 0
works on the TOP of stack in place: load peeks, store replaces, inc bumps;
pull pops), the whole call family (vs/vs2/2s/1s and the _n forms, address
0 yields false, extra args discarded, locals default 0), ret/rtrue/rfalse/
ret_popped, catch/throw (frame-count semantics, unwind then return),
check_arg_count, random (seeded = reproducible), verify (against the real
checksum), piracy (gullible), nop, quit, and the numeric outputs
(print_num/print_char/new_line) through io.py.

io.py landed as the core-world boundary of docs/06 s.4: IOSystem (loud
NotImplementedError defaults), ConsoleIO for the harness, CaptureIO for
tests and transcript comparison. Screen-model calls will speak to
screen.py's cell model, NOT this interface (front-ends render core-owned
truth; only boundary-crossing events live in io.py).

Unimplemented opcodes raise UnimplementedOpcode NAMING THE MILESTONE
(objects M4, Z-string text M5, read M6, screen M8, styles M9, saves M10,
streams M11); sound_effect is the designed no-op. Faults are named with
addresses (division by zero, stack underflow, call to a non-routine),
Actaea playing fizmo's role by construction.

M3 done-test PASSED: 22 hand-assembled computational tests produce correct
results headless, driven by a test-side encoder deliberately independent
of both the decoder and the compiler's assembler (the encodings are cross-
checked by a second implementation). Highlights: recursive factorial
F(7)=5040 eight frames deep; frames isolate their stacks (a callee popping
its caller's stack is an underflow fault, S 6.3.2); catch/throw across
three frames returns the thrown value and neither sentinel prints. 48
actaea tests; 455 total. actaea 0.3.0.

NEXT: M4, the object tree (48 attributes, properties with one/two-byte
size forms, the 63-entry defaults table, parent/sibling/child and all
their opcodes). After that M5 text and the machine starts talking.

## 2026-07-04 (night, cont.): Actaea M4 green, the object tree

objects.py owns the v4+ table (S 12.1-12.4): the 63-word defaults table,
14-byte entries (48 attribute bits, parent/sibling/child words, the
property-table pointer), and property tables with both size forms (one
byte, bit 6 = length; two bytes, bit 7 set in BOTH, second's low six bits
the length, 0 meaning 64). insert makes first-child and stitches the old
chain; remove keeps children and is a quiet no-op on a parentless object;
object 0 ("nothing") faults by name rather than reading bytes belonging to
no object. get_prop reads bytes/words and falls back to the defaults;
longer reads fault (S 15); put_prop writes 1/2 bytes and faults on absent;
get_prop_len(0)=0; get_next_prop(_, 0) gives the first and faults when
asked after a property the object lacks. All writes ride Memory's dynamic
barrier. VM wiring: jin, test/set/clear_attr, insert/remove_obj,
get_parent (store), get_sibling/get_child (store AND branch on nonzero),
get_prop/put_prop/get_prop_addr/get_prop_len/get_next_prop. print_obj
stays in M5 with the text engine.

The test-side encoder moved to tests/actaea/unit/zasm.py (shared by
test_vm and test_objects); its builder grew an object-table area at 0x220
with a declarative objtable() helper. One real fix out of the tests: the
two-byte size form needs bit 7 set in the SECOND byte too, which is
exactly the bit get_prop_len reads back. 10 new tests; 58 actaea, 465
total. actaea 0.4.0.

NEXT: M5, the text engine and dictionary: ZSCII, the three alphabets and
the custom alphabet table, abbreviations, encode and decode, the Unicode
translation table, dictionary lookup, and the print family (print,
print_ret, print_addr, print_paddr, print_obj, print_table, tokenise,
encode_text). After M5 the machine talks and CZECH comes within reach.

## 2026-07-04 (night, cont.): Actaea M5 green, the machine talks

text.py: Z-string decode (three alphabets, custom alphabet tables with
A2's fixed escape/newline, abbreviations from the doubled word addresses,
10-bit ZSCII escapes spanning word boundaries, nested abbreviations a
named fault per S 3.3), ZSCII<->Unicode both ways (the Standard 1.1
default extra table 155..223; a custom Unicode translation table from
header extension word 3, loaded BEFORE the alphabet table since a custom
alphabet may name extra characters), and encode_word (the v4+ 9-z-char
dictionary form). dictionary.py: separators/entry-len/count parsing,
linear lookup (correct for sorted and unsorted alike), and the v5
tokeniser (spaces vanish, separators split AND stand, skip_unknown
leaves the address slot untouched for two-pass merging). VM: the whole
print family (print, print_ret, print_addr, print_paddr, print_obj,
print_table as honest headless rows, print_char via the full tables,
print_unicode, check_unicode -> 3), tokenise, encode_text.

THE CROSS-CHECK: the round-trip tests encode with the ARCTURUS COMPILER's
zstring and decode with Actaea, two independent implementations meeting
in the middle, accents included (Mañana, señor Müller está aquí; the
[[never-strip-accents]] rule as an executable test). encode_word matches
zstring.encode_dict_word byte for byte.

M5 done-test PASSED, and it is the project's photograph: a real Arcturus
game (compiled in-process by the real compiler with the real Cosmos)
BOOTS AND TALKS on Actaea: banner with title/serial/Arcturus/Cosmos
lines, room description, object intro listing, the > prompt, halting at
`read at 0x0214c arrives with milestone M6`. Every routine on that path
(the loop, the banner, the describer, dispatch, the after phase, the
paragraph machinery) executed on our interpreter. 74 actaea tests, 481
total. actaea 0.5.0.

NEXT: M6, the conformance gate: aread/read_char through io.py, then
CZECH and Praxix headless with output matched against the references
(actaea/conformance/ holds czech.z5 + czech-reference.txt + praxix.z5).
This is the correctness milestone the whole build hangs on.

## 2026-07-04 (late night): operand patterns were documented fiction; now they dispatch

An early adopter's stop/continue question led into docs/01 section 12, and
the probe found that `on put ruby in chest` NEVER FIRED: codegen's react
collector silently skipped every handler with a non-direction pattern (the
"still deferred" comment), for objects, kinds, AND free rules, main and
after phase alike. The worked examples in the syntax reference were
documented fiction; nothing shipped used patterns (H2 included), so no
test ever caught it. The document wins: the code got fixed (arcc 0.10.4).

Implementation: _guard_plan generalizes the direction-guard machinery.
A pattern compiles to react-side tests BEFORE the handler call: `way`
against the direction's property number (exactly the old emission, byte-
identical), `noun` (and, past a preposition, `second`) against object
numbers, `or` alternatives side by side in multi-operand je's (the
assembler's 2OP encoder now takes je's 3- and 4-operand variable form,
which `or` lists lean on; >3 alternatives chain je's). The keyword `noun`
in a pattern leaves its slot unconstrained. A failed guard means the
object never addressed the action, so an all-guarded group still reaches
`on other` (the direction-guard rule, now uniform). Kinds in patterns are
an explicit CodegenError pointing at a body test, not a silent drop.
Free patterned rules dispatch too (react_free now takes layout/gmap).
Patterns compose with when guards, comma verb lists, and the after phase.

tests/test_patterns.py pins it: exact pairing replaces the default,
mismatch falls through to the default, or-alternatives, the catch-all
interaction, after+pattern, free patterned rules. 488 tests; the pinned
example sizes are UNCHANGED (guards cost only games that use patterns).

Also this stretch: the arcc bare call printed its version block twice
(header + banner-that-contains-the-header); fixed, one banner. docs/01
handler endings rewritten in Arcturus's own terms (end = your lines are
all that happens; continue = your lines then the normal action; on after
= your lines once it really happened; stop = the early exit, redundant on
the last line) after Stefan vetoed the Inform-analogy framing, and `on
after` got its own full docs section (header features, the two firing
rules, the after-pass resolution order). Adopter questions answered:
unreachable scenery = on other + on examine continue; proper names =
the `named` attribute; stop-vs-nothing = identical on the last line.

## 2026-07-05 (small hours): Actaea M6 GREEN, the conformance gate

THE GATE: CZECH passes 406/406 with the output matching the reference
transcript byte for byte outside the untested header-identity block (where
Actaea now reports MORE than the reference terp did: Standard 1.1 declared,
a real screen size). Praxix runs "all" to "All tests passed.", every group.
And the flagship proof beyond the gate: HIBERNATED 2 PLAYS START TO THE END
ON ACTAEA, 360/360 in 128 turns to the post-mortem, statusline, menus,
quote boxes, undo checkpoints and all; Cloak of Darkness wins likewise.
The compiler, the library, and the interpreter are now one toolchain,
end to end, all three ours.

What the gate demanded beyond M5 (actaea 0.6.0):
- read (v5 aread: lower-cased into the text buffer, tokenise into the
  parse buffer, echo with newline, terminator 13 stored; a time/routine
  pair accepted and ignored headless) and read_char, both through io.py.
- verify FIXED to checksum the story file AS STORED (memory.initial),
  never live memory; CZECH 404 exists to catch exactly the mutated-memory
  mistake and did.
- Interpreter-set header fields stamped at boot and re-stamped after
  restore_undo (S 11 / 6.1.6.2): flags1 styles-available bits, screen
  dimensions, default colours, interpreter id 0/'A', Standard 0x0101.
- In-memory undo (save_undo/restore_undo): a snapshot stack of dynamic
  memory + frames + pc + store var; restore resumes as if save_undo had
  returned 2. Multi-level, exactly as Praxix drills it. File-based
  Quetzal stays M10.
- Output streams (S 7): screen toggle, transcript flag, stream 3 memory
  redirect NESTING to 16 levels through a single _print funnel every
  print opcode now uses (count word + ZSCII bytes on close; while open,
  nothing else receives output), stream 4 accepted.
- scan_table (form byte, word/byte, custom step), copy_table (zero-fill,
  corruption-safe forward, deliberate smearing on negative length).
- set_text_style/set_colour/set_true_colour/buffer_mode as io HINTS: a
  style-less colourless console is a legitimate interpreter (its flags
  say so); the GUI renders them at M9. The headless WINDOW model:
  window 1 output discarded, cursor ops accepted, get_cursor says 1,1;
  what a dumb terminal honestly does, replaced by the real cell grid at
  M8 (screen.py).
- The CLI plays stories now: python3 -m actaea <story> runs on ConsoleIO
  (EOF on the input pipe = normal end for walkthrough play); --header
  and --disasm remain.

tests/actaea/conformance/test_conformance.py holds the gate: CZECH vs the
reference (header block normalized on both sides), Praxix all-pass with a
group-count floor. The M5 boot showpiece upgraded: the probe game now
PLAYS (examine, a refused take, quit with confirmation) instead of
stopping at read. 490 tests green.

NEXT: M7, the tkinter shell: the lower window with scrolling, word wrap,
line/char input, stream 1; done when both example games play start to
finish in the window. Then M8, the cell grid, its own visible done-test.

## 2026-07-05 (small hours, cont.): Actaea M7, the window

The tkinter shell (actaea/gui/app.py, actaea 0.7.0): one window, the
scrolling lower text area with word wrap, and INLINE input, the way
interpreters have looked since the eighties: the player types at the
story's prompt in the story's own text flow. The Text widget is read-only
outside the live input region (an input mark separates story text from
the player's line; backspace cannot eat the prompt), Return completes a
read, any key completes a read_char. Input blocks WITHOUT threads: the VM
runs on the tkinter thread and read_line/read_char spin the event loop
with wait_variable until a key event flips the flag; single-threaded, no
locks, the window painting and scrolling the whole way. A closed window
unblocks any pending wait and unwinds the run loop via EOFError. Story
end prints [The story has ended.] and leaves the transcript up.

The echo contract moved to where it belongs: the io.read_line
implementations own input echo (the widget shows typing live; a piped
console echoes for readable transcripts, a tty console does not since
the terminal already shows keystrokes; CaptureIO echoes into the
transcript), and the VM never echoes.

CLI: python3 -m actaea <story> opens the WINDOW when the session is
interactive and tkinter exists; the console when input is piped, when
--console asks, or when tkinter is absent. TOOLING: brew python-tk@3.14
installed (Tk 9.0) since Homebrew Python ships without _tkinter.

Hard-won platform fact, pinned in the test docstring: Tk 9.0 on macOS
dies with SIGTRAP when a SECOND Tk root is created in a process that
then spins wait_variable. One root per process; the app itself is the
display probe (TclError = skip). The smoke test drives the widget like a
player (scripted lines typed into the Text at its prompts, pumped via
after-callbacks) through boot, look, and a confirmed quit. 491 tests.

M7 DONE-TEST = Stefan's turn: both example games playable start to
finish in the window, plain text. Hand-off made. Then M8, the cell grid.

## 2026-07-05 (small hours, cont.): Actaea M8, the cell grid

screen.py owns the upper window now, as the honest thing docs/06 demanded:
a true rows-by-columns buffer of CELLS (char + style + colours from day
one, so M9 and the arc_image milestones never need a second data path),
renderer-agnostic, notifying front-ends through on_change and never letting
them hold screen state. Semantics per the Standard: v5 split keeps
contents; a cursor stranded outside a shrink homes to 1,1; selecting the
upper window homes its cursor; the upper window never scrolls and never
wraps (overruns clip); erase_window 1/0/-1/-2 with the lower clear routed
through the sink's erase_lower (a scrolling console keeps its transcript;
the GUI wipes its text area); erase_line to end of row. The VM's window
opcodes all delegate to the model; set_text_style accumulates style bits
into it (style 0 clears, others OR, per S 8.7.1); get_cursor answers from
truth. The M6 dumb-terminal stubs are gone.

The tkinter side renders the grid on a Canvas above the text area: exact
cell geometry from a measured monospace font, repaints coalesced per idle
cycle, run-length segments per row, reverse video inverted (full styles
and colours are M9's), shown only while a split is open. The Canvas is
the surface arc_image will draw onto; cell geometry is exact from day one
for that reason.

Proofs, headless (the model IS the truth): 8 unit tests (clipping, split
keep + cursor homing, select homing, all erase variants, style travel,
change-signal discipline) plus Cosmos's own statusline driving the grid
through the real opcodes: one row split held open through play, the
current room on the left, Score/Moves right, reverse-video cells. And the
flagship again: HIBERNATED 2's FULL WALKTHROUGH over the live model, THE
END at 360/360, quote boxes growing the split to 9 rows and folding back,
finishing with a single status row reading The Throne Room / Score: 360
Moves: 119. One fix on the way: a blank scripted keypress means Enter
(the dfrotz walkthrough convention; H2's press-any-key intro found it).
499 tests. actaea 0.8.0.

M8's VISIBLE done-test is Stefan's turn: H2 in the window (the status
line correct and stable, quote boxes rendering cleanly over real play).
Then M9: styles and colours rendered, set_font, true colour.

## 2026-07-05: Actaea M9, styles and colours

The screen model is now the ONE truth for the current look in both
windows: set_text_style accumulates bits (0 returns to roman, S 8.7.1),
set_colour speaks the standard numbers (0 keeps, 1 default), and Standard
1.1 set_true_colour stores 15-bit words as precomputed #rrggbb (-1 keeps,
-2 default), with the Standard's recommended true colours (S 8.3.7) as
the palette for the standard set. Cells already carried the look; now
the lower window does too: the GUI reads the model at print time and
tags the inserted text (bold/italic/bold-italic font variants, reverse
swapping fg/bg, colours resolved through one helper), and the grid
renderer draws cell colours and styled fonts. Roman-default text carries
no tag at all, so plain prose costs nothing. The io hint methods are
GONE: state lives in the model, io carries events (text, keys, clears);
one truth, no second path. set_font landed too (1 and 4 are the same
face in a monospace terp, both available, previous font stored; 2 and 3
refused with 0), and flags1 now claims colour alongside the styles.

Proofs: model colour/style semantics unit-tested, the opcodes driven
through zasm (set_colour, true colour with keep/default, set_font
prev/refuse/query = "104"), an Arcturus say.yellow game plays with the
colour path live, and H2's full walkthrough still reaches THE END at
360/360 with the model's colours flowing (final state: white on default,
roman). 503 tests. actaea 0.9.0.

M9's visible half is Stefan's: H2 in the window shows the coloured
banner, say.yellow callouts, and the quote box in proper dress. Then
M10: Quetzal save/restore interoperating with a reference interpreter
both ways, plus restart.

## 2026-07-05 (cont.): the light interpreter ruling + direction or-lists

Stefan's ruling on M9's look: Actaea's own screen is BLACK ON WHITE
PAPER; a game that wants a dark screen SETS its colours. H2 not setting
a background was a bug in the game, now fixed in its source
(zcolor.background black). The dark-interpreter commit is reverted the
right way: header default colours declare white paper/black ink
(S 8.3.2), and the WINDOW BACKGROUND IS DYNAMIC: erase paints the screen
in the game's current background (S 8.7.3.3), which is exactly the
moment zcolor.background takes the whole window (the compiler emits
set_colour + erase_window -1 as a pair). The look-tag cache resets on a
repaint since cached tags resolved the old paper.

And the compile error Stefan hit exposed the next pattern gap (arcc
0.10.5): `on go south or up` (an or-list of DIRECTIONS) fell into the
object branch of _guard_plan and errored. The classifier now handles
direction operands generally: all-direction or-lists guard `way` against
the property numbers (single directions compile byte-identically to
before; sizes unchanged), mixed direction/object operands are a named
error, directions demand the go action (only go sets `way`), and the
old silent H2 shape `on go south, up` (comma parsed as a bogus
preposition, handler never fired) is now a NAMED error pointing at
'or'. H2's line fixed accordingly; the game recompiles (124,380) and
walks to THE END at 360/360 with the model ending white-on-black as
its zcolor declares. 505 tests.

## CHECKPOINT 2026-07-05: compaction point; M10 is next

State: CLEAN TREE, everything committed through 4ffd34e. arcc 0.10.5 /
Cosmos 0.14.3 / actaea 0.9.0 / 505 tests green. Actaea M1-M9 are DONE and
Stefan-verified in the window (H2 screenshot: cyan bar, dark screen, the
whole toolchain in one picture).

### The M9 verification round (all committed)
- Stefan's ruling, now doctrine: Actaea is a LIGHT interpreter (black on
  white paper, declared in header 0x2C/0x2D); a game that wants a dark
  screen SETS its colours. H2 lacking zcolor.background was a GAME bug;
  Stefan fixed it in the (gitignored) H2 source. The window background is
  DYNAMIC: erase repaints in the game's current background (that is how
  zcolor.background = set_colour + erase_window -1 takes the screen).
- The typed line wears the game's input colour (Cosmos sets zcolor.input
  right before every read; the input region takes a look-tag at read
  start, swept per keystroke, caret matches). H2's input is cyan.
- No scrollbar (native = unstyleable white strip; wheel/trackpad + the
  unread-return cover it). Window exactly 80 cells wide, ~30 lines.
- Compiler 0.10.5 out of the same round: direction OR-LISTS in patterns
  (`on go south or up` guards way; single dirs byte-identical), mixed
  direction/object operands and non-go direction patterns are named
  errors, and `on go south, up` (comma = bogus preposition, silently
  dead until now, H2 had one at line 739) is a named error pointing at
  'or'. H2's line fixed; H2 = 124,380 bytes, walks to THE END 360/360.

### M10 NEXT: Quetzal save/restore + restart (docs/06 s.9, s.13)
Done-test: a save made in Actaea loads in Frotz and the reverse; undo
and restart behave. What exists already: in-memory undo (snapshot stack
in vm.undo; save_undo/restore_undo work, Praxix-drilled); Frame objects
deliberately Quetzal-shaped (per-frame stacks); memory.initial (pristine
image) for restart and CMem XOR. To build:
- actaea/quetzal.py: IFF reader/writer; IFhd (release/serial/checksum/PC),
  CMem (XOR-vs-initial run-length, or UMem), Stks (frames: return PC,
  flags/locals count, store var, argc mask, eval-stack words). Mind the
  details: PC in IFhd is the byte address of the INTERRUPT/branch point
  (for save: the save instruction's store-byte address per spec usage),
  Stks frame flags bit 4 = no-store, argc as a bit mask, dummy first
  frame for the entry stream.
- vm: _op_save/_op_restore (EXT:0/1, store 1/0 on save, 2-via-restore
  like undo; restore re-stamps interpreter header fields per S 6.1.6.2),
  _op_restart (reset memory from initial EXCEPT flags2 transcription
  bits S 6.1.6.1, reset frames/pc/streams/screen model).
- io: save/restore need FILE CHANNELS through the boundary: ConsoleIO
  prompts for a filename (dfrotz-style, so scripted walkthroughs can
  feed it), GuiIO opens tk file dialogs, CaptureIO uses a temp dir.
- Interop test: dfrotz IS on PATH; drive dfrotz save -> Actaea restore
  and Actaea save -> dfrotz restore inside pytest (tmp_path, scripted).
- Cosmos already funnels save/restore through do_save with the result-2
  resume path (test_save_restore_roundtrip_on_frotz shows the flow).
After M10: M11, the last sweep (TerpEtude text portions, transcript
stream 2 to a file?, timed-input degrade, v8 checks with Jigsaw/anchor,
real games end to end) and then B10 IS COMPLETE.

### Standing context worth carrying
- Conformance dir (LOCAL ONLY, gitignored): czech.z5 + reference,
  praxix.z5, etude.z5, ghosts.z5, deseos.z5, calypso.z5, anchor.z8,
  Jigsaw.z8; H2 at hibernated2/h2-full.z5; walkthrough wtfull.txt in the
  session scratchpad (161 lines, blank lines = keypresses).
- One Tk root per process (Tk 9.0 SIGTRAP); the GUI smoke test is the
  only Tk test and flashes a real window during the suite.
- python-tk@3.14 installed via brew (Tk 9.0).
- fizmo-console = debugging terp of record; pytest harness = dfrotz.
- H2 source NEVER committed (gitignored); compiler work commits fine.
- Parked: H2 quality-sweep list (top of hibernated2.storyarc), the
  abbreviation-quality TODO (zabbrv comparison), inline emphasis colour
  (show.<colour>), B10 docs debt: docs/06 M-numbering says "milestone
  B7" fixed but double-check section 13 wording when B10 closes; write
  arc_image/reference/design.md-actaea notes? (docs/06 is authoritative; PROGRESS carries the
  build record.)

## 2026-07-05: Actaea M10, Quetzal save/restore and restart

The last file-shaped hole in the machine: quetzal.py writes and reads
Quetzal 1.4 (IFF/IFZS). IFhd identifies the story by release, serial,
and checksum FROM THE PRISTINE IMAGE (a game can scribble on its own
dynamic header) and carries the resume PC, which by the v5 convention
points AT the save instruction's store byte: restore writes 2 through
it and resumes at the next byte. CMem is dynamic memory XORed against
memory.initial with zero runs coded 0x00+(n-1) and trailing zeros
dropped (an early save is a few hundred bytes); UMem is read too.
Stks writes the frames exactly as M3 shaped them, dummy entry-stream
frame first, discard bit, argument mask, per-frame stacks. Unknown
chunks skip. The module is pure data: no VM import, no files.

The VM grew the trio and lost the last _LATER scaffolding: save (the
aux-table form honestly refuses), restore (failure stores 0 and play
continues; a QuetzalError's reason prints, so "this save belongs to a
different story" reaches the player), restart (pristine image except
the two Flags 2 session bits per S 6.1.6.1, frames and streams reset,
erase_window -1 puts the screen back to boot). Both restore and undo
re-stamp the interpreter header fields (S 6.1.6.2). The io boundary
gained the file channels as pure "where" questions: save_path and
restore_path. ConsoleIO prompts dfrotz-style so scripted play keeps
working, GuiIO opens native tk dialogs, CaptureIO resolves script-fed
names into a test's tmp_path.

Proofs, per the done-test "a save made in Actaea loads in Frotz and
the reverse; undo and restart behave": tests/actaea/test_interop.py
compiles an Arcturus game on the spot and round-trips it BOTH ways
against dfrotz inside pytest, plus a foreign-save refusal and a
confirmed restart reboot; test_quetzal.py drills the coding layer and
the opcodes through zasm (restore resumes inside the save with 2 and
the saved world; restart preserves exactly the transcription bit). On
the real game: H2 walks to THE END 360/360 on the M10 build, an
Actaea save at 43 turns resumes in dfrotz at 105/360, and a dfrotz
save at the same depth resumes in Actaea, room, score, and inventory
intact. Every interop failure along the way was the test harness, not
the format (dfrotz pagination without -h 8000, a stale file's
overwrite prompt, H2's intro keypresses eating script lines): worth
recording, because the pytest interop test avoids all three by
construction. 521 tests. actaea 0.10.0.

Next: M11, the final sweep (TerpEtude's applicable portions, stream 2
as a real transcript?, timed-input degrade, v8 checks with Jigsaw and
anchor, real games end to end), and B10 is complete.

## 2026-07-05: Actaea M11, the conformance sweep

The input machinery grew its last limbs. Preloaded input (S 15 read,
byte 1): the game's part-typed line goes to the front-end and comes
back as part of the whole line, never re-printed; the GUI absorbs the
printed characters into the editable region (TerpEtude 12 now reads
"givenhello", matching dfrotz exactly). The terminating-characters
table (S 10.7) parses at boot and the GUI ends a read on any listed
function key, returning its code; read_char now hands the game cursor
keys, F1..F12, and the keypad, and accented keys translate through
the text engine, not ord(). Timed input is REAL in the window: the
VM's call_interrupt runs the routine as a nested execution mid-read
(a sentinel frame delivers the return value to the interpreter), the
GUI's after() loop fires it every time/10 seconds, its printing lifts
the typed line and puts it back (S 8.4.2), and a true return ends the
read with terminator 0, the typed text surviving as next time's
preload, which is exactly Border Zone's flow. Headless front-ends
ignore the pair and honestly leave the header's timed-input bit off;
the GUI claims it (io.supports_timed).

Stream 2 is a real transcript file: one file per session, opened on
first use through io.transcript_path (console prompt, tk dialog,
scripted tmp dir), lower-window text only, player lines included,
synced BOTH ways with Flags 2 bit 0 at every input (a game flipping
the bit directly is obeyed; a refused file clears the bit, S 7.1.1.1).

The real-game sweep earned two machine fixes: Anchorhead reads below
an array at boot, so the four table opcodes now compute their
addresses in wrapping 16-bit arithmetic like every reference
interpreter; Jigsaw asks for the children of "nothing" at boot, so
the tree READS on object 0 answer 0 while mutations stay hard errors.
Both z8 games now boot and play headless, alongside Ghosts, Calypso,
and deseos (whose "¿Quieres color?" pins the accent path end to end).

Proofs: TerpEtude's text portions asserted headless (header analysis,
signed mul/div/mod all ok, multiple undo, preload, lower-casing,
closing-text-before-quit); timed reads, preload, terminators, and
both transcript switches drilled through zasm; the five-game sweep in
tests/actaea/conformance/test_games.py; CZECH still matches the
reference byte for byte; H2 to THE END 360/360. 538 tests.
actaea 0.11.0.

The GUI half of M11 is the visible verification: TerpEtude 4/5 (styles
and colours), 7 (accents), 8 (arrows and function keys reported), 10/11
(the countdown ticking mid-input), 12 (editing the preloaded line), and
a transcript written through the file dialog. Then B10 is complete.

## 2026-07-05 (cont.): the M11 polish, Stefan's five

Stefan's list after playing the sweep build, all landed:

1. THE TERMINAL FRONT-END (his "most important"): --console is now a
   real playing interpreter in the fizmo-ncursesw manner, on the
   STANDARD LIBRARY's curses (the zero-dependency rule holds; tkinter
   and curses both ship with CPython). actaea/console.py is the third
   front-end on the same headless core and the proof of the io
   boundary: the game-drawn status bar renders live from the cell grid
   (curses even diffs it, repainting single cells as the move counter
   ticks), z-colours map to the terminal's, styles to A_BOLD/A_ITALIC/
   A_REVERSE, the lower window word-wraps at the terminal width and
   pages with [MORE], input is edited inline in the game's input
   colour, timed input runs on getch timeouts, erase paints the
   game's background, and the final screen holds for a key. --headless
   is the dumb-frotz pipe, unchanged, for debuggers and the BuildTools;
   the default ladder is window, then terminal, then pipe, each step
   announced. Native Windows (no stdlib curses) degrades to headless
   with a note.
2. THE STANDALONE: tools/amalgamate_actaea.py builds build/actaea, one
   self-contained file in the arcc manner. The embedded modules load
   through a real import hook (lazily, exactly like the package), so
   the single file still plays headless on a Python without tkinter or
   curses. Guarded by tests/actaea/test_actaea_standalone.py: the
   amalgam plays a freshly compiled Cloak with no package on sys.path.
3. THE BANNER: one identity block in actaea.banner(), shown by --help,
   --version, --header, --disasm, and both About panels.
4. MENUS AND SETTINGS (GUI): About Actaea (in the app menu on macOS,
   Help elsewhere), Text Size, Screen Height, and a Game Colours
   toggle (off = black-on-white with styles kept; the look caches
   drop and the paper repaints on toggle).
5. THE MACOS NAME: the bold menu-bar name belongs to the hosting
   bundle, which bare Python cannot rename; when pyobjc is installed
   the NSBundle name becomes Actaea, and either way the app menu's
   About is ours (tkAboutDialog). A true .app is packaging, out of
   scope per the roadmap.

Proofs: the curses front-end drives through a REAL PTY in pytest
(status bar from the statusline granule, ANSI colour on the wire,
[The story has ended.] hold), the standalone plays packageless, and
the suite stands at 540. The basename lesson repeated itself
(test_standalone.py collided across dirs; renamed). actaea 0.12.0,
build/actaea regenerated.

## 2026-07-05 (cont.): polish round two, from Stefan's screenshots

Stefan played the polish build and sent three findings, all fixed:

- THE CONSOLE FILL: --console showed the terminal's own background
  where the game's black should be; only text carried its colour. The
  escape stream told the story: the erases ran with reset attributes,
  because erase_lower set the window background AFTER erasing. curses
  fills a cleared window with its background attribute, so the order
  is the whole fix: bkgd first, then erase (and the window is born
  with the game's background in _make_lower, so scrolled-in lines and
  split rebuilds wear it too). The erase-line sequences now carry
  bg-black on the wire, verified through the pty. The terminal
  tab/window also takes the story's name (the xterm title sequence)
  instead of saying Python.
- THE ABOUT PANEL: the raw banner line-wrapped badly in a messagebox;
  it is now a laid-out panel (name large, version, the facts in their
  own lines, the repository clickable, Return/Escape dismiss).
- FONTS AND MEMORY: View -> Font offers the monospace families the
  system actually has (a curated list intersected with tkinter's
  families), and ALL the View settings persist: family, text size,
  screen height, and the Game Colours toggle land in
  ~/.config/actaea/settings.json (XDG_CONFIG_HOME honoured) and come
  back at the next launch. Settings save only on deliberate menu
  changes, never at boot; the GUI smoke test isolates itself with
  XDG_CONFIG_HOME so it neither reads the player's settings nor
  leaves its own.

540 tests. actaea 0.12.1, build/actaea regenerated.

## 2026-07-05 (cont.): polish round three, the terminal emulator round

Stefan's next screenshots named four bugs; a pyte terminal emulator in
the test pty (dev-only, scratchpad venv) made them reproducible as
data instead of pixels:

- CONSOLE, the vanished room text: when Cosmos redraws its status bar
  around an input, the split changes AFTER the turn's text printed;
  _make_lower recreated the window and swallowed the description
  ("font still not painted" = text gone, not miscoloured). The split
  now RESIZES AND MOVES the window (_resplit), content anchored to
  the bottom where the story scrolls, with a redrawwin to squash
  physical-screen leftovers. The emulator shows the description
  standing and every row black.
- CONSOLE, the unpainted half screen: blank grid cells carry the
  default colour pair and rendered as the terminal's own background
  (Stefan's wallpaper) instead of the game's paper; same for the strip
  right of the 80-column grid on wider terminals. The console now
  remembers the paper (the background the last erase painted, the
  GUI's _window_bg counterpart) and paints default-bg cells and the
  strip with it.
- GUI, the five-font menu: the curated-intersection list was the
  wrong idea; the Font menu now scans EVERY family tkinter reports,
  keeps the fixed-pitch ones (Font.metrics("fixed")), and builds
  lazily on first open, so the whole system library is offered.
- GUI, colours toggle-on losing the text: toggling deleted the look
  tags, stripping existing story text to the widget default, black on
  the game's black paper. The tags are now RECONFIGURED in place from
  their names (style-fg-bg), so the text re-dresses instantly in
  either direction.

540 tests. actaea 0.12.2, build/actaea regenerated.

## 2026-07-05 (cont.): polish round four, the top-fill

GUI: all resolved (Stefan). Console: colours resolved; one layout bug
left, the room text sitting in the bottom half of a fresh screen with
a void above it. Cause: the erase anchored the cursor to the BOTTOM
row (a scrollback habit); real terminal terps fill a cleared screen
from the top and only scroll when the text reaches the bottom. The
erase and the window's birth now home to the top-left, and _resplit's
scroll logic follows: a growing bar clips the BOTTOM (scrolling only
if the cursor would fall off), a shrinking bar adds blank rows below
without moving the text. Emulator-verified: the description starts
under the bar, turns append downward, every row black through
multiple turns. actaea 0.12.3, build/actaea regenerated.

## 2026-07-05 (cont.): polish round five, the CLI house style

Stefan: console layout confirmed; two CLI gaps remained from his
banner request. A bare `actaea` (the argparse usage error) showed no
banner, and no output left a blank line before the next shell prompt.
A small ArgumentParser subclass is now the house style: format_help
and format_usage lead with the banner (so help, the bare-invocation
error, and every usage error wear it), error() ends with the blank
line, a custom --version action prints banner-plus-blank (argparse's
own version action strips trailing whitespace), the load-failure path
prints banner, error, blank, and --header/--disasm close with the
blank line too. Every tool-facing shape verified byte-exact: all end
"\n\n", all start with the banner. Play modes stay clean (a piped
--headless transcript carries no banner; debuggers and BuildTools
parse game text, not stationery). actaea 0.12.4, build/actaea
regenerated. 540 tests.

## 2026-07-05: B10 COMPLETE. Actaea 1.0.0.

Stefan's green light on the last polish closes the milestone. The
documentation pass that closes it, per his direction:

- The design document moved home: docs/06-actaea-design.md is now
  actaea/actaea-design.md, the design record living beside the code it
  describes, its head updated to say so (status: complete, M1 to M11
  all built).
- docs/06-actaea.md is NEW: the official Actaea documentation. What it
  is, the standalone and the package, the three ways to play (window,
  --console, --headless) and where each degrades, the tools (--header,
  --disasm, the banner house style), Quetzal saves and undo and
  transcripts, the full input story (preload, terminating characters,
  timed input), the conformance record, the two deliberate leniencies,
  and the arcc-to-actaea loop for Arcturus authors.
- Every pointer updated: CLAUDE.md's Actaea section (now "complete",
  three front-ends, distribution note beside the arcc amalgam habit),
  docs/00-roadmap.md (status head, docs index, B10 marked COMPLETE
  2026-07-05, section 8 rewritten to the true present: the project owns
  both ends of the pipeline, next is B11), README (the Actaea bullet
  flips to Done with the full feature story, docs/06 joins the docs
  list), actaea/__init__.py, the handoff prompt, HANDOVER.md. No
  dangling references to the old path outside this build log.
- Version: 1.0.0. The design doc's own words: after M11 Actaea is a
  finished Standard 1.1 interpreter. It is. build/actaea regenerated,
  540 tests green, the banner says v1.0.0.

The B10 arc, in one paragraph for the record: eleven milestones from
loader to conformance sweep (M1 loader/memory, M2 decoder, M3
executor, M4 objects, M5 text, M6 the CZECH/Praxix gate, M7 the
window, M8 the cell grid, M9 styles and colours with the
light-interpreter ruling, M10 Quetzal, M11 the sweep: preload,
terminators, timed input, transcript, the z8 leniencies), then
Stefan's polish rounds (the curses console, the standalone, the
banner, menus and persistent settings, the About panel, the console
paper and top-fill, the CLI house style). Three front-ends, one
headless core, zero dependencies. Next: B11, arc_image on modern
systems, extending the cell model M8 built for exactly this.

## 2026-07-07: B11 COMPLETE. arc_image on modern systems.

Optional graphics land, and the story file never stops being a conformant
z5. A room carries an `arc_image` picture; an aware interpreter draws it,
every standard interpreter ignores it, and the same file plays text-only on
Frotz and in Actaea's console and pipe modes.

The design, settled with Stefan across the milestone:

- The picture id IS the resource slot. The author writes it as a number, or,
  for readability, a constant that folds to one (`arc_image scene_path`,
  `constant scene_path = 8`). The interpreter loads `<id>.png`; a retro build
  will load slot `<id>`. No name manifest to translate down: the number is
  the one identifier every target shares. (This replaced the first-seen
  name-to-id table and the JSON sidecar of the early phases.)
- The mode travels in the opcode, not the pixels. A game sets `constant
  arc_mode = 9` (Infocom, 320x72, the upper third) or `12` (DAAD, 320x96,
  the upper half); it folds by ordinary name resolution, defaulting to 9
  when absent. The interpreter sizes the band from the mode (mode * cell_h),
  so it lays out the screen without loading a picture, the property an 8-bit
  target needs. Stefan caught the original pixel-inference as the wrong
  architecture; this is the fix.
- The draw is one custom extended opcode, `draw_image id mode`, at EXT:0x80,
  in the 128-255 range the Standard reserves for private extensions (so it
  never collides with a future official opcode). Fredrik Ramsberg (Ozmoo,
  PunyInform) pointed out the range; it started at 0x20.
- The guard is the capability handshake: a graphics interpreter sets Flags 1
  bit 1 (the v6 "pictures available" bit) at boot, the library reads it at
  run time (`pictures_available`), and only issues the draw when set. On
  Frotz the branch is never taken, so the bytes are never decoded. Belt (the
  guard) and suspenders (the ignorable EXT range, S 14.2). Pay-for-use: a
  game with no picture is byte-identical to one that never had the feature
  (the `any_images` compile-time fold plus DCE).

The pieces:

- Compiler: arc_image as a numeric value property, arc_mode folded and
  validated (9 or 12), the draw_image opcode, the pictures-available guard,
  no sidecar written.
- Cosmos: `draw_room_image` reads the room's picture behind the guard, dedups
  on a `shown_image` global (a re-LOOK never reloads, so a retro target never
  re-decompresses), and passes `arc_mode` as the opcode's mode operand.
- Actaea: the window renders the band, integer-scaled to the 80-cell width
  (crisp for pixel art), sized from the mode, the status bar flush beneath.
  It finds the pictures in a `--images` directory or a sibling `.arcres`
  pack. Console and pipe report no picture support.
- arcimg, the third standalone tool (build/arcimg, its own banner and build
  fingerprint): `pack` numbered PNGs into an `.arcres` (a zip), `prep` a
  source to a mode (Pillow only when it must resize or convert, with a guided
  install), `info` a PNG or pack.
- examples/arc_image: a two-room Rabenstein walk, heavily commented, with its
  `.arcres`. The VS Code extension highlights `arc_image` (0.11.0).

Versions at close: arcc 0.10.9, Cosmos 0.14.4, Actaea 1.0.3, arcimg 1.0.1.
Both amalgams regenerated, 565 tests green. Docs: docs/01 section 6b (the
language and the arcimg synopsis), docs/06 section 2 (rendering) and 3 (the
tool), docs/00 graphics plan. Next: B12, the same numbered pictures converted
to each retro machine's own trimmed RLE format, and the Rabenstein port (B13).

## 2026-07-07: the positional grammar layer (arcc 0.11.0, Cosmos 0.15.0)

Between B11 and B12, working through early-adopter feedback, one report
outgrew the bug-fix batch: a verb declared as `dig in noun with held` did not
parse (`DIG IN SAND WITH SHOVEL` fell into disambiguation, `DIG IN SAND`
bound no noun). The cause was structural, not a bug: the runtime parser was
flag-driven, reducing every verb to a noun arity plus its preposition words
and splitting a two-noun command at the first separator, so a grammar line's
SHAPE was never consulted. A leading literal on a two-noun verb could not
work, and neither could wording that selects the action (LOOK UNDER vs LOOK
BEHIND). Falling short of Inform on grammar expressiveness was ruled a real
minus for the language, so this was done properly rather than patched: a
checkpoint note captured the verified model and its limits, and the overhaul
landed the same day.

The design that landed, and why:

- The surface syntax never changed. A grammar line's first name has always
  been its action, and its literal positions were already parsed and stored;
  only the backend threw the shape away. Everything below is compiler and
  library.
- TWO grammar models behind one `verb` syntax, and the compiler picks per
  verb (worldmodel.needs_table). The flag model is exact for every standard
  verb in all three language packs, including leading literals on one-noun
  verbs (LOOK AT CLOAK, the phrase matcher skips) and particle-decided
  actions (switch on/off), so those verbs stay on it, byte for byte. A verb
  earns a positional TABLE only when the flags are lossy: a literal before
  the first slot of a two-noun verb, or different actions on different line
  shapes. "Subsume the flag model" was considered and refused on size
  grounds; tables for the standard verbs would cost every game ~600 bytes
  for nothing.
- The table sits in static memory with the grain chains: per line an action
  byte, one byte per token, literal tokens carrying their dictionary address
  (backpatched like object words); the tabled verb's dictionary entry holds
  the table address in its data bytes (flags 0x90, 0x98 with the preposition
  bit). Lines are emitted most-literals-first, then fewest-tokens among the
  literal-free, so a bare `dig noun` cannot swallow a wording a more
  specific line spells out.
- The matcher (grammar_match/try_line, parser.prelude) is language-agnostic;
  each pack's resolve_verb/resolve_objects branch to it on the tabled flags,
  Spanish keeping its pending clitic as the noun. Slots resolve through the
  same scoring matcher as everything else, so ties still ask, a
  named-but-unresolved slot is still rejected, an empty slot lets the action
  ask its own question, and no line fitting is the honest extra-words
  refusal. Disambiguation answers, pronouns, chaining, AGAIN, and OOPS work
  unchanged on tabled verbs.
- Pay-for-use holds exactly: the whole path folds behind `any_tables`, and
  every pre-existing example compiled to its old byte size (all ceilings
  unchanged). The new features/grammar.storyarc showcase pays the full
  price, 14340 bytes against the ~13400 feature baseline.
- Fallout fixed along the way: quoted grammar literals (`dig "in" noun`)
  used to crash the compiler and are now the bare word; the German pack's
  schliesse block dropped its aspirational lock/unlock lines (they never
  dispatched, the particles decide) for an honest `close noun mit noun`,
  behavior unchanged.

Sema checks a positional verb honestly: two slots per line at most, a
literal word between two slots (the adjacent-noun form belongs to `reverse`,
which stays a flag-model feature), single-word synonyms, no `direction`
slot. Authors extend grammar per game: new verbs, new words feeding standard
actions (`verb "peruse"` with `examine noun`), or a standard verb redeclared
with richer lines, the later declaration winning for its words (docs/01
section 10).

Versions at close: arcc 0.11.0, Cosmos 0.15.0. Amalgam regenerated, 602
tests green (tests/test_grammar_tables.py holds the acceptance cases, the
tabling rule, and the zero-tabled-packs proof; test_sizes.py pins the
zero-cost claim). Docs: docs/01 section 10 (positional grammar and the
extension patterns), docs/02 section 8c (the model and the matcher), docs/02
section 15 (grammar overriding), docs/04 section 7 (the table encoding),
examples/features/grammar.storyarc. The checkpoint note that scoped the
overhaul was deleted once it landed; this entry is the record. Verified on
fizmo-console and handed off. Next: B12 stays next.

## 2026-07-07: B12 R0 COMPLETE. The retro arc_image charter and roadmap.

B12 opened with its roadmap, not with code: arc_image/reference/design.md,
drafted from a four-way research sweep over the fourteen target machines
(Commodore, Sinclair/Amstrad, MSX/Atari/Apple, and the 16-bits) and
approved by Stefan the same day, every open decision ruled.

The reframe that shaped it: B12's center of gravity is the CONVERSION
INTELLIGENCE, not the file format. One band-shaped master painting per
image (320x72 or 320x96, the author provides the right shape; ST-class 16
colors the expected common denominator), and arcimg derives the ideal
native version for every target: palette, geometry, attribute-clash
solving, detail reduction. Hand-painted native art stays as an optional
1:1 lint-and-encode path. The blueprints (format, converter, interpreter
contract, verification probe) are written so interpreters that do not
exist yet can be built from the documents alone, and Vezza announced it
will implement the same public contract.

The research validated B11's bets outright: the 72/96-pixel bands align
exactly with the 8-pixel text rows of every one of the fourteen machines,
and every machine wants its payload in native memory order, so the loader
on a 1 MHz CPU is a dumb RLE-unpack. Targets fall into three conversion
classes: quantize (Amiga, ST, DOS, CPC, MSX2, Next, MEGA65), cell (C64,
Spectrum +3, Plus/4, MSX1, C128 VDC; the per-cell solvers are the real
work), and signal (Apple II, NTSC-modeled).

Rulings at R0: waves ordered Eris-first (Amiga/ST/DOS end to end, the
contract's reference implementation) with C64 leading wave 2; DOS is VGA
mode 13h only (Infocom's MCGA precedent); file naming <id>.<TAG>;
band-shaped masters; Colodore as the C64 reference palette; the C128 VDC
blueprint is written even though its interpreter fate is decided later;
ST text reserves palette indices 0 and 15 (to be verified against Eris's
ST screen layer in R2); probe-disk building is IN scope (the FictionTools
builders on the Linux side: dsktool, idsk, c1541, mkatr, adf.py,
gemdos.py), game-disk packaging stays out.

Next: R1, the format spec and the shared RLE codec.

## 2026-07-07: B12 R1 COMPLETE. The .arc container and the format layer.

The retro image format exists and proves itself. arc_image/reference/design.md section 10 holds
the specification: a 16-byte big-endian header (magic, version, target id,
mode, geometry, image id), a section table, and per-section RLE streams in
a shared PackBits-shaped scheme whose decoder is a few dozen bytes on a
6502 or Z80, with 0x80 as an end sentinel so a streaming loader needs no
length counter. Sections carry the payload in each machine's NATIVE memory
order (the Spectrum thirds, the CPC sub-blocks and Mode 0 bit shuffle, the
C64 cell order, the Amiga row-interleaved planes, the ST word interleave,
the Next column-major layer), palettes in native hardware encoding, so
every loader is a dumb unpack.

arcimg 1.1.0 implements the whole family: pack/unpack/render for all
fourteen targets, `arcimg targets` (the ledger as a command), and `arcimg
render` (any .arc back to a PNG through the target's reference palette,
via a stdlib PNG writer, no Pillow). The done-test is
tests/test_arcformat.py: the RLE codec's edges, container fault handling,
and for every target in both modes a legal native test image (cell
matrices and registers included) that packs, writes, reads, unpacks to the
identical native image, and re-encodes bit-identically; plus a render
smoke test per target and the golden-corpus check (the Rabenstein masters,
320x96, the conversion acceptance material for the waves). 50 new tests;
the suite stands at 659.

Deviations noted: compressed sizes join the ledger per wave (they need
real conversions to mean anything), and the TED, GTIA, and Apple II
preview palettes are marked approximations until their waves freeze
measured values. Next: R2, wave 1 (Amiga, ST, DOS converters and probes,
and the Eris reference implementation of the interpreter contract).

## 2026-07-08: B12 R2 COMPLETE. Wave 1: Amiga, Atari ST, DOS, proven.

The quantize wave is done end to end: converters, corpus, probes,
chapters. arcimg grew the master pipeline (stdlib PNG reader, median cut
with a k-means polish so small loud regions keep their palette entries,
gun-depth snapping before mapping, and gradient-gated ordered dithering,
Bayer 8x8 after Stefan's eye caught the 4x4's cross artifacts, amplitudes
halved on his "less is more"). The 21-master corpus converts bit-exact on
AST and DOS and snap-only on AMI; the stresstest pair (two gradient
paintings, 17-19 thousand colors) is what the dithering machinery was
tuned on, and it is the machinery waves 2 and 3 inherit.

Three probes, written from the blueprint alone and each verified by
Stefan in both band modes: DOS (nasm .COM, mode 13h, palette-first
section walk, DOSBox-X), Atari ST (vasm TOS .PRG, Setpalette verbatim,
decode to Physbase, Hatari), Amiga (a raw bootblock trackload, no
Workbench, a copper list displaying the interleaved planes in place,
FS-UAE on Kickstart 1.3). The probes paid for real lessons, all recorded
in docs/08: the 68000 dbra counter trap, odd-length .arc alignment, the
copper one-frame-wonder (the band-bottom plane switch needs its top-of-
frame restore), DOS square-pixel presentation (CRT aspect correction
makes eggs of suns), and the text-color contract (luminance-sorted
palettes, darkest as stable paper, guaranteed-readable ink) after the
below-band background flipped colors between pictures.

The implementer handover exists NOW, not at R6 (Stefan's ruling:
documents AND content): docs/08-arcimage-interpreters.md carries the
contract (including the Z-machine colours clause: art palettes are never
modified, text colours are per machine: DOS's reserved system range, the
Amiga's per-frame copper reload, the STF's declare-or-approximate
choice), the format with reference RLE decoders (x86, 68k), and one
verified chapter per target; arc_image/probes/ holds the reference
loaders and the two-mode test assets. Next: R3, the cell class: C64,
Spectrum +3, CPC.

## 2026-07-08/09: B12 R3, the conversion gate. The codec era.

Wave 2's converters (C64 multicolor, Spectrum attribute cells, CPC mode
0) were built and then refined through seven review rounds under
Stefan's pixel-artist eye, with his own hand-painted Spectrum Rabenstein
as training data. What the rounds taught, all recorded in the design
record: luminance-dominant matching with a saturation term, greedy
error-minimizing cell colors, protected palette extremes (the swallowed
moon), the salient-disc hint sidecar (author states the moon once, every
target keeps it, connected-from-crown so a low moon never mirrors into
the ground), BRIGHT IS THE CANVAS on the Spectrum (dark cells only where
D7 grey earns them), best-16-of-27 ink election with a chroma-dumping
penalty on the CPC, and flat fields with dither only at band transitions
(Stefan: replace the color, sprinkle the seams). The gate passed
2026-07-08: C64 and CPC approved and frozen; the Spectrum ruled ~90%
with the ship framing (full confidence, minor polish per image) and a
first-class polish loop: arcimg scr/unscr round-trips a conversion
through any .scr editor, hand-authored results stamped in the header
(byte 15) so convert never overwrites them, band mode auto-detected.

The codec era arrived mid-milestone. Measured on the corpus against
LZSA1/2, Exomizer, and RLE, ZX0 was ruled the .arc codec for the 8-bit
targets (arcimg carries a pure-Python packer validated byte-identical
against the reference, plus the spec-ported decoder that doubles as the
interpreters' executable spec); the 16-bit trio took LZSA2 for pack
speed, first via Emmanuel Marty's tool, then, after Stefan's no-binaries
ruling for the BuildTools 4.0 direction, with a built-in pure-Python
greedy packer (8% over optimal, seconds, dependency-free) behind
$ARCIMG_LZSA and PATH. Regens dropped from twenty minutes to ~75 seconds
(parallel conversion, make-style skipping). arcimg reached 1.7.0.

## 2026-07-09/11: The adopter wave. Cosmos 0.15 to 0.23.

Early adopters arrived ahead of any announcement and drove the busiest
library stretch of the project: Charles Moore Jr. (improvmonster, now
credited in the README and a Discord contributor), Shawn Sijnstra
announcing Vezza adoption across targets, Ichiro Ota porting his
PunyInform game. Shipped from their reports, each with tests, docs, and
the pay-for-use fold discipline (byte-identical when unused):

- The room title and status bar say where the player stands ("Crypt (on
  the altar)"), line_nested worded per language, German in the dative.
- Component objects: `component` on a thing placed in another makes it
  part of the whole (Dialog's #partof with the tree carrying the
  relation): scope through plain things, part-of take answers, no
  contents listing, parts follow their whole; player components are not
  luggage.
- perform("take", book): programmatic actions, the full pipeline,
  compile-checked names, direction rides the way slot (and the `in`
  direction stands wherever a value can; `way is in` disambiguates from
  the copula by lookahead).
- appearance: the paragraph an object always owns in a room description
  (Inform's describe), computed by state, beside intro's until-moved
  rule.
- worn_count/list_worn (the punctuated outfit), convey (a vehicle
  carries the player; here refreshes; the vehicles example), drop lands
  where the player is with the destination worded (the Hibernated 2
  manner), scenery_contents = 1 lists scenery holders' contents (the
  Puny bridge, the arc_mode constant manner), the is-predicate form
  (`if lamp is visible` reads any one-parameter block), reachable
  honoring its documented contract (take through closed glass fixed).
- Parser honesty: an unresolved noun never dispatches (noun is nothing
  now MEANS a bare verb), typos are spelled back and OOPS corrects them,
  all three language layers.
- Diagnostics born from confusion: the fork trap note (a dotted summon
  beside an edited granule), the unread-property note (stale binaries
  and typos tell on themselves), kind-as-value and change-on-boolean
  errors that teach the right syntax, sema resolving player-block
  bodies (the was_read hole).
- arcc --update: the standalone refreshes itself and its siblings from
  the published build, validated before replacement, explicit-only
  networking; the answer to three stale-binary hunts in three days.

arcc ended the stretch at 0.11.20, Cosmos at 0.23.0, the suite at 774;
the VS Code extension (0.12.1) learned the week's language and the
examples grew components, appearance, perform, and vehicles (fresh
scenes only: adopter code stays private, the field-kit lesson).

## 2026-07-10: The documentation shelf, reorganized.

Stefan's ruling: docs/ is for authors and interpreter authors. The
arc_image design record moved to the engine room
(arc_image/reference/design.md), the interpreter book renumbered to
docs/08, a new author guide docs/07-arc-image.md (masters, workflow,
polish loop, the honest what-plays-where table), 07-conformance retired
as a stale snapshot the test suite outlives, message-set and verb-set
deleted as work docs, every cross-reference rewritten, the README's
what's-new five rotated forward (retro arc_image, perform/appearance,
the typo-naming parser).

## 2026-07-10: B12 R3 COMPLETE. Six machines, six proven blueprints.

The wave-1 probes were backported to LZSA2 (Marty's 8088 decompressor
verbatim; a shared 68000 decompressor written from the spec and proven
byte-exact under vamos before any emulator) and re-verified. The wave-2
probes landed: C64 (ACME, bitfire's ZX0 decoder verbatim, proven through
VICE's remote monitor before Stefan's visual pass), Spectrum +3 and CPC
(sjasmplus snapshots sharing the 68-byte ZX0 decoder, verified in
ZEsarUX through ZRCP injection after the snapshot-machine lesson).
Chapters C.4-C.6 carry the paid-for lessons: the type-4 attribute
number, own-your-stack and own-your-CRTC, the 27-cube ink indexing
against the firmware-numbering trap, the CPC split-screen clause (mode 0
band, mode 1 text, one raster write, pens reloaded per region) that
feeds Haumea, and the Z-colours answers per machine (Haumea's four
concurrent text pens the only real design point; MSX2 noted as the CPC's
colour cousin with the V9938 line interrupt). One apology recorded in
standing notes: ZEsarUX persists CLI flags into its config and display
flags wrecked Stefan's setup once; machine, snap, and remote-protocol
flags only, forever. The R3 checkpoint file was deleted as always
promised. Next: the adopter support queue (Shawn's target spec for
Vezza's machine awaited; Charles ongoing; Ichiro porting), then R4
(Atari 8-bit, MSX1/2, Plus/4).

## 2026-07-11: The support week continues. Directions, transcripts, and a keeper.

Housekeeping first: scenery_contents got its worked example (The
Chandlery, whose drawer keeps its secret until opened) and its docs/02
paragraph, and the sweep found Bumble, an adopter's character, in the
README, docs/01, a compiler comment, and a test; all four now use the
appearance example's own lighthouse keeper. Adopter names stay private,
everywhere public. The scoring chapter (01 6a) was rewritten on Stefan's
review: it had grown by accretion, vehicles and perform wedged between
the automatic rules and award; now 6a tells scoring end to end and the
movers (teleport, gain, convey, perform) live in section 7 beside move.
Actaea 1.0.4 gives the terminal its name back on exit (the xterm title
stack; Stefan's own observation).

Then Charles's next pair, both shipped in arcc 0.11.21 / Cosmos 0.24.0.
The `direction` grammar slot: a line may end in `direction` (swim
direction, push noun direction), so SWIM SOUTH and PUSH CRATE WEST
parse; the direction rides `way`, GO's own slot, and perform("go", way)
hands the move to the walking machinery whole. Always tabled (the flag
model's arity byte cannot say it); byte-identical when unused; The Ford
is the worked example. And TRANSCRIPT/SCRIPT with TRANSCRIPT OFF and
UNSCRIPT, ruled core by Stefan (a player right, worth +416 per game):
output stream 2, with the library reading Flags 2 bit 0 back so a
cancelled file prompt never claims a recording, and the closing line
printed before the stream shuts so it lands in the file. Actaea's
handler verified spec-exact. Found en route and fenced: a block with
more than 15 locals compiled into an illegal routine header and crashed
mid-game; it is a named compile error now (try_line itself sat at
exactly 15, hence dir_scan).

Cosmos 0.25.0 closed the day with Stefan's fallback ruling: the English
meta words (QUIT, SCORE, SAVE, RESTORE/LOAD, UNDO, AGAIN, OOPS,
TRANSCRIPT and kin) answer in every language pack, replying natively,
because a player who guesses the localized session verb wrong must
never be locked out of the session. Spanish gained its first particles
for it (no/on/off); the TRANSCRIPCION NO wording is flagged for Pablo's
native pass. Shawn's palette question was answered along the way (the
Rabenstein masters are 16 colours by DAAD heritage, Degas PI1's
ceiling, not by rule; masters are truecolor and the converters quantize
per target) and his Agon-class plan confirmed against the design:
masters are 320 across precisely so a double-width VDP scales for free.
His target spec is awaited without a queue slot; Ichiro's port is
resolved. 791 tests. More Charles bombs incoming, by his own promise.

## 2026-07-12: The language grows where the ports press on it.

The adopter wave turned from bugs to language. pluribus (arcc 0.11.25,
Cosmos 0.27.0), Stefan's name by way of e pluribus unum and Vince
Gilligan: grammatical number joins gender in the language model, one
attribute driving the articles ("some scissors"; German's bare
indefinite plural and its die/die/den/der case column; Spanish
los/las, unos/unas), the new ${is x} copula tag in the article family
(is/are, ist/sind, esta/estan), and number branches through the core
messages of all three packs, every one behind the any_pluribus fold
(byte-identical unmarked; the fold needed its _static_value entry,
caught when the ceilings briefly moved). The nautical granule (0.11.26,
0.28.0): FORE, AFT, PORT, STARBOARD as standard direction properties
with the words opt-in, the Hibernated problem solved the way Hibernated
solved it, and verbose_exits taught to list only LIVE directions.
String constants for Ichiro Ota (0.11.27): a constant stands for its
text in desc and say alike, identical strings now pool once in the
story file (smallest possible z-code, made true when the docs sentence
claiming it was found false), and interpolation dropped in a plain
property string gets a teaching note. Verbs learned `meta` for Charles
(0.11.28): the out-of-world band opened to declaration, the debug
tools and TRANSCRIPT routed past every on other. And the endings split
on Stefan's ruling (0.11.29, 0.29.0): finish stays final, death offers
UNDO and rewinds the fatal command; any_death folds the machinery away
from games that never die (brass-lantern shrank, cloak honestly pays),
and the abbreviation harvest stopped counting text DCE prunes, exposed
by the twin dead prompts. Earlier the same day: AGAIN re-checks scope
(the immortal lantern), locks demand their key in hand, three refusals
got three answers (the bare verb asks with its verb echoed, the
unbound pronoun found msg_no_it, wired at last), the held tiebreak
settles what one hand already answers, roomness flows through the kind
chain, and the updater learned its manners (header, Cosmos version,
the house blank line) after Stefan caught the amalgam shipping without
updater.py at all. 824 tests. Charles holds the Epic Bughunter title
on the Discord; the queue stays warm.

## 2026-07-12, later: catalogs. Dialog's lists, without Dialog's heap.

Charles and Ichiro asked for the same thing from two sides (list data;
list access), Stefan asked what every Dialog list feature does in plain
words and drew the line himself: the requested five plus membership,
last, and random, none of the rest, because the rest (append, reverse,
collect) are exactly the features that need a runtime heap, the Dialog
trap this language exists to refuse. Then he named it: a star catalog,
of course. `catalog last_letter` declares a fixed ordered collection
one value per line, one type per catalog; calculate folds to a constant
at compile time, entry and last are one loadw, dice rides random,
position scans (and `in` branches on the same block: membership costs
no new vocabulary), `for each` iterates, a catalog passes to a block as
its offset, and `change entry(...) to` rewrites one entry in place with
a single storew, because the tables live in dynamic memory and there is
no allocator anywhere. quote_catalog draws a whole letter as
a box in one call, frame sized from compile-time header words. Found
under it and fixed: quote_done unsplit the whole screen, so the first
line printed after a mid-game box vanished beneath the statusline's
repaint. The Inquest is the worked example; every ceiling except the
repaired quotes example stands untouched, the byte-identical proof.
arcc 0.11.32, Cosmos 0.31.0, highlighter 0.13.0, 832 tests.

## 2026-07-12, evening: the seams a big port finds.

The day's second half belonged to one adopter's large multi-file game
and the seams it pressed on. Nautical went 3D on Stefan's correction (a
vessel is a volume: ALOFT and BELOW ride up and down) and learned the
shore with dirs_nautical, the flag ruled over the automatic room-probe
that could not tell a crow's nest from a tavern; verbose_exits proved
composed on both sides of the gangplank. Stefan's one question ("he has
to type way is aft, and not way is aft or north?") dissolved the
or-list ambiguity: bare-constant operands were always-true bugs, never
working code, so the is-list sugar claims exactly that territory (`way
is aft or north`, the negated form meaning neither) and no legal
program changes meaning. The multi-file mystery cracked the same way:
`summon messages.storyarc` had loaded the game's own chapters at
granule rank, so overriding a granule message was a same-rank duplicate
however arranged; a summoned .storyarc now ranks as GAME, the lattice
complete (a late less-specific block loses silently), the structure
never designed for made official. And the report seam closed with
`alter`, Stefan's name: speak the action's report yourself, one line or
a composed body, continue into untouched mechanics, the default's
success line silent, refusals never fooled, the flavor say still
stacking, every guard behind the any_alter fold with the ceilings
standing as proof. The catalogs announcement scrub also happened, and
is recorded where it belongs: in the memory that says adopter snippets
are adopter content. arcc 0.11.36, Cosmos 0.33.0, 850 tests.

## 2026-07-12, night: checkpoint. Two of three Dialog features down.

Since the evening entry: alter settled its final shape on Stefan's
coherence ruling (`alter block` for the composed body, rhyming with
desc block, the bare-newline form kept beside it by his call, both
proven byte-identical) and got its worked example, The Reliquary, all
four behaviors in one scene. Then Dialog feature two of Charles's
three: `beyond`, Stefan's name and his reasoning (a light bulb without
a ladder is not distant, but it is beyond) after his plane-landing
insight settled implement-over-recipe: visible and examinable, every
touching action refusing "beyond your reach" (three languages,
pluribus-aware), conversation crossing the gap, throwing-at
deliberately legal, and the whole thing STATE, toggled with now. The
grain division is doctrine now: static faraway decoration is a grain's
job; beyond is distance that matters to the model. Guards at 23 sites
behind any_beyond, folded AT THE CALL SITE after the first pass paid
the call everywhere (the lesson now twice-learned). The Larder is the
example, and it exposed a general gap Stefan ruled on whole: ENTER, GO
ON, and CLIMB all board a supporter now, climb through the full enter
pipeline in the agnostic layer, GO ON/GO IN as English idioms beside
the GET family, native packs untouched. README's vsix section
un-rotted (version-agnostic). State: arcc 0.11.38, Cosmos 0.34.1,
highlighter 0.13.3, 855 tests, all committed. Open: Charles's THIRD
Dialog feature (Stefan holds it, guessed granule-shaped); Shawn's
Agon-class target spec (Australia lag); then B12 R4.

## 2026-07-12, late: catalogs travel through properties (arcc 0.11.39)

Ichiro's field report, a classic silent-zero trap: a kind handler read
a catalog through self.<prop> and got the FIRST catalog for every
object. The property value named a catalog, sema typed any name value
as object, the fill found no such object and stored 0, and 0 is the
first catalog's word offset, so every readable in his game showed the
same text with no error anywhere. Three-line fix in the right places:
sema types a catalog-naming property value as number (a catalog value
IS its word offset), the layout computes catalog offsets BEFORE the
object table is emitted (they follow from declaration order alone; the
region itself still lands at the end, the corruption lesson stands),
and _fill_property stores the offset. Now `writing plaque_text` on an
object (or a kind default) reads back through entry(self.writing, 1),
calculate, quote_catalog, all of it, per object. Regression test with
invented content (a crypt, a plaque, a stone), docs/01 catalogs
section notes the pattern. Ceilings untouched: the precompute emits
identical bytes. State: arcc 0.11.39, Cosmos 0.34.1, 856 tests,
amalgam regenerated. Open: Charles's third Dialog feature (parked for
discussion, Stefan's call), Shawn's spec (not yet arrived), and B12 R4
resumes next.

## 2026-07-13: the flat-base architecture, Stefan's ruling after the wall

Five A8 rounds hit the wall and Stefan called it: something fundamental.
The answer was in his own history. The well-regarded Rabenstein 8-bit
ports were Dylan Barry's CPC originals fed through Pixel Polizei
(Markku Reunanen's checker: plain nearest, frequency, local fixes, no
dither, no optimizers); Stefan only repainted Spectrum and the 16-bits.
Our pipeline did the opposite, painterly masters into constraint
solvers, each stage manufacturing what the next fought. Blessed and
built: the FLAT BASE (master -> 160-wide, 27-cube, 16 inks by
frequency, no blending, no dither) with the CPC converter now being the
base itself, the C64 by Polizei's recipe (Pepto, amending R0's
Colodore) from the base, the A8 riding the C64 as before, hand-authored
.C64 as the whole family's source (arcimg convert --c64), PP source
stashed uncommitted at arc_image/reference/ppolizei. design.md amended
(section 4 rewritten, 8a amendments, perceptual clause retired).
Corpus previews are the gate for Stefan's eye. Known open: the
gradient-class stress beach greys under Pepto (its approved ancestor
was Colodore-rendered and vivid; Pepto is muted by design and has no
teal or hot pink; a metric cannot conjure colors a palette lacks), and
one dumping-metric attempt at the Pepto mapping made it worse and was
reverted, the plain Polizei manner stands. Dylan Barry passed away
early this year; his CPC art remains the reference this architecture
is built on. arcimg 1.9.0, 866 tests.

## 2026-07-13, later: the cube middleman was the grey, C64 direct is the base

Stefan's two corrections landed the architecture. One: the C64 shall
be the base of everything (his original words, mis-implemented as a
CPC-cube intermediate). Two: the grey-sky mystery, finally traced,
was NOT palettes: the invented 27-cube middleman has no dark purple,
so every soft master color greyed BEFORE any machine saw it; Polizei
maps each machine direct from the source and always did. Rebuilt:
C64 direct from master (Polizei recipe, Colodore reaffirmed after
the one-day Pepto experiment, Pepto has no teal and no hot pink),
CPC direct with R3's chroma-dump metric restored at weight 4 (at 3
the grey beat the dusk purple by four percent), A8 riding the C64
through a Colodore-GTIA injective table. The beach is back on all
three: purple sky to the top, golden sun, no grey anywhere. Corpus
sheets reviewed complete for C64/CPC/A8; A8 keeps mild full-width
compromises on the two busiest scenes (the honest 4-per-line cost).
design.md 8a records the detour and its lesson honestly. Awaiting
Stefan's gate on the three rebuilt sets. arcimg 1.9.0 (build
5ed93db), 866 tests.

## 2026-07-13, the beach gate: spice, inheritance, de-grey (arcimg 1.10.0)

Stefan's beach-first discipline paid. Rounds on one image, fast, no
corpus churn between tweaks, and every fix landed as doctrine. THE
SPICE (his ruling, all 8-bit targets, C64 the proving ground): flat
conversion first, then in-cell dither against the master reference,
firing only at smooth seams in the 0.40 midband, where the purple of
the clouds meets the pink; his verdict "amazing, exactly how it
should be". THE INHERITANCE, asked twice and finally heard: the CPC
derives from the C64 by recolor, pixels and dither verbatim, so
nothing is ever dithered twice. THE DE-GREY, born from his
observation that C64 grey is absorbed by Colodore but jars
elsewhere: siblings re-read every grey C64 pixel through the
master's hue (the CPC in its own cube space, keeping the shimmer
weave alive; salient discs exempt, their promotion is deliberately
anti-master). The A8 got its defenses PRICED INSIDE the segment
optimizer (bright star, dark anchor, neutral-first victims,
symmetric chroma penalty: grey rock goes to black, never sea-blue),
which healed the grey bar and moved the brown split to where light
would fall; Stefan reads the cliff as sun above, shadow below, and
gate-approved all three machines. Corpus regenerated once, sheets
swept. design.md section 4 rewritten to the final architecture.
arcimg 1.10.0 (build da4a1f1), 866 tests.

## 2026-07-13, later: alter learns to wait (arcc 0.11.40, Cosmos 0.35.0)

Charles's second alter report cut deep and true: the custom narration
fired at handler time, before validation, so the drunk staggered west
and then hit "there is no exit". Stefan probed whether a before-slot
was needed; the honest answer settled it (before-text that only prints
on success is the success slot wearing a different name), and he ruled:
do it. alter now REGISTERS instead of prints: the body hoists into its
own routine at compile time (codegen._hoist_alters), its packed address
rides the altered global with self captured into altered_self, and the
library's 36 report sites (actions.prelude and extendedverbs.granule)
call it instead of the default line, only on success. Refusals discard
the registration unfired, GO fires it after the move and before the
room description, perform saves and restores it around nested actions,
and handler locals stay out of the deferred body (no closures on the
Z-machine). Three slots, each with one owner: say = the attempt,
alter = the report, on after = the coda. Syntax unchanged, all three
forms; a game without alter stays byte-identical (ceilings prove it;
the alter example's own ceiling raised with the dated note). Suite 867.

## 2026-07-13, late: beyond carries its why (arcc 0.11.41, Cosmos 0.36.0)

Charles again, and Stefan endorsed on sight: the beyond refusal should
say WHY the thing is out of reach, per object, the desc-block shape.
Built exactly so: `beyond "Without the ladder, the top shelf might as
well be the moon."` speaks your line instead of the generic
msg_beyond; `beyond block` opens a computed body worded by state; bare
`beyond` keeps the pack's message. Under the hood sema splits the
valued form into the bool attribute plus a beyond_why text property
(computed under the block form, the desc machinery unchanged), the
guards test presence via beyond_why_addr (absent property folds to
nothing, a beyond game without whys pays only the test), and both
noun and second slots speak it. Only the beyond example's ceiling
moved, dated. Suite 868.

## 2026-07-13, night: say way speaks the word (arcc 0.11.42)

Charles could not print the direction he had just parsed (way holds a
property number; way.name is nothing). Now `say way` and ${way} speak
the direction's canonical word through cosmos_dir_name, a je-chain
over the live directions keyed by property number, emitted only when
referenced (the exit_name gating extended); way 0 prints nothing. One
compiler change, no Cosmos bump, ceilings untouched. Suite 869.

## 2026-07-13, night: particles chain with or (arcc 0.11.43)

Charles: INTO and ONTO forced new grammar lines. Now `put noun in or
into noun` on one line, the is-list `or` (his earlier lesson applied
to the surface): the parser expands alternatives into sibling grammar
lines at parse time, so the dictionary, both grammar models, and the
matcher never learn a new shape, and it costs exactly what writing
the lines out costs. Slots refuse to be alternatives with a clear
error. Suite 870.

## 2026-07-13, checkpoint for the next session (Opus pickup)

State of the repo: arcc 0.11.43 (amalgam build 82a3549), Cosmos
0.36.0, arcimg 1.10.0 (build da4a1f1), Actaea 1.0.4, highlighter
0.13.3 (current; no grammar changes needed today). HEAD f7fd9a4,
870 tests green, all amalgams regenerated and committed. Stefan
pushed through arcc 0.11.40; EVERYTHING SINCE (0.11.41 beyond-why,
0.11.42 say-way, 0.11.43 or-particles, the Larder example) awaits
his push, so arcc --update lags until then.

THE ADOPTER WAVE, all Charles Moore Jr., all shipped today with
tests, docs, and Discord replies delivered in-thread: (1) alter
REGISTERS and fires only on success, at the report site, instead of
the default line (codegen._hoist_alters routines, altered +
altered_self globals, run_alter intrinsic at 36 library sites, GO
fires before the room description, perform saves/restores, handler
locals cannot cross into the deferred body); say = attempt, alter =
report, on after = coda. (2) beyond carries its why: beyond "..." /
beyond block (sema splits into the attribute + beyond_why text prop,
guards test presence via beyond_why_addr, generic msg_beyond stays
the fallback; The Larder shows both forms). (3) say way / ${way}
speaks the direction's canonical word (cosmos_dir_name je-chain over
live directions, emitted only when referenced). (4) grammar
particles chain with or (put noun in or into noun; parse-time
expansion into sibling lines, no new matcher shape).

ARC_IMAGE, where it stands. The architecture is settled and
design.md section 4 is the authoritative record: C64 direct from
master by Pixel Polizei's recipe on Colodore, THE SPICE (seam-only
in-cell dither, 0.40 midband, smooth-mask gated, discs solid), C64
is the base of the deriving family, CPC = recolor of C64 pixels
with cube-space de-grey (keeps the dither weave; grey-axis ban),
A8 = segment solve over the C64's 8-line cell rhythm with defenses
priced inside seg_pick (bright star, dark anchor, neutral-first
victims, symmetric chroma penalty), the DE-GREY re-reads C64 greys
through the master's hue everywhere (salient discs exempt). PP
source stashed UNCOMMITTED at arc_image/reference/ppolizei
(gitignored). BEACH GATE PASSED on C64+CPC+A8 (commit 0740b58);
Stefan explicitly deferred the corpus review ("I will check the
corpus later"): the corpus and stress sets on disk are current with
the final code, sheets swept clean by Fable, but STEFAN'S CORPUS
VERDICT IS THE OPEN GATE before anything is frozen.

R3 corrections status: C64 and CPC are REBUILT (this supersedes
their R3-frozen converters) and are part of that pending corpus
verdict. The Spectrum keeps its R3 solver untouched: it cannot
consume the 160-wide base geometrically; its re-gate is pending
alongside, with Stefan's crop note on record (crop the RIGHT side
off for 256-wide targets, never center; suspected old ZX hurt).

R4 state per machine (the per-machine rule stands: converter +
design.md + docs/08 chapter + probe complete before the next
machine): A8 converter is beach-gate-passed, corpus pending, then
its PROBE (atari800; Stefan has not yet answered whether/where it
is installed, ask before launching anything) which includes
freezing the MEASURED GTIA table (the formula in _gtia_color is an
approximation at sat 0.21; preview and selection share it so errors
cancel in preview but not on hardware), then docs/08 C.7 written
probe-fresh. MSX1, MSX2, Plus/4 NOT STARTED; each decides its
source (C64-derived or direct) at its own round; A8 luma freedom
(same hue, GTIA luma refinement) stays STAGED behind the corpus
gate. Blocked/parked: Charles's THIRD Dialog feature (Stefan holds
it, wants discussion first, likely granule-shaped); Shawn
Sijnstra's Agon-class target spec (not yet arrived); B12 R5/R6
after R4.

Working habits the next model must keep: beach-only tuning, ONE
corpus pass after a gate; never run the full pytest suite in a
detached background shell (the curses console test blocks without a
TTY); adopter content never reaches public artifacts; design-level
changes are discussed BEFORE implementation; every ceiling raise
carries a dated note; regenerate and commit amalgams at every bump
and keep the README version table current; memory files under
~/.claude carry the standing rulings (b12-charter-and-rulings above
all; READ arc_image/reference/design.md before any B12 work).

## 2026-07-14: alter without continue draws a compiler note (arcc 0.11.44)

Charles Moore Jr. could not get alter to fire on a camel he boards
(`on climb, enter` with an alter block, no continue). Not a bug: the
handler dies at the handler level (the general design), consuming the
action, so the library's success site never runs and the registered
report can never fire, nor does the boarding. The deferred timing is
right; the action simply never succeeds. Reproduced with a porch
swing (invented), confirmed one `continue` at the handler indent
fixes it (message + boarding both). Because alter-without-continue is
ALWAYS dead and fails SILENTLY, Stefan ruled a compile note:
sema._lint_alter_without_continue walks each handler, and when it
holds an alter but no continue (the alter's own body skipped, since a
block is the report's text not handler flow) it names the alter's
line and the cure. The misplaced-continue error (continue inside the
block) now guides placement too (ctx.in_alter_block marker). docs/01
states the continue requirement as a rule. Compiler-only, Cosmos
unchanged. Suite 872.

## 2026-07-14: kinds are effectively unlimited (arcc 0.12.0)

Charles Moore Jr. hit the 48-attribute wall porting a 200K Dialog
game, "out of kinds and attributes". Root: a kind is Arcturus sugar,
not a Z-machine concept (Stefan's framing: Inform's classes are just
objects and cost nothing), yet every kind unconditionally burned one
of the 48 attributes so `obj is <kind>` could be a one-byte
test_attr. Three tiers, built together (minor bump for the
capability):
- Lever 1: a kind gets a runtime attribute ONLY when the program
  tests `obj is <kind>`. Spanning (Charles's most-used feature)
  expands to concrete rooms at compile time and never tests the kind,
  so scenery-organizing kinds now cost ZERO. sema counts test sites
  (world.kind_tests).
- Attribute-back the tested kinds busiest-first from the slots real
  attributes leave free (flags... no, genuine object attributes come
  first, they cannot spill).
- Catalog spill: overflow tested kinds get a synthesized extent
  catalog (transitive instances) and `obj is <kind>` becomes a
  membership scan; kinds uncapped. Verified on the VM incl. transitive
  membership through a spilled parent. Reuses the catalog feature
  (Stefan's call: our own architecture, not Inform's ofclass); the
  scan reads resident dynamic memory, no Ozmoo disk paging.
The only real ceiling is now 48 genuine ATTRIBUTES, and the error
names them honestly (kinds never count). `arcc -s` shows
"attributes N/48, kinds M (K spilled to catalogs)" so the author sees
the true budget. NOTE: a mid-build misstep renamed the stat to
"flags" -- reverted, because Arcturus HAS a distinct `flag` feature
(a global boolean); calling attributes flags would have been wrong.
Suite 879.

## 2026-07-14: nautical land-start note (arcc 0.12.1)

Charles Moore Jr. (self-resolved, shared for review): a nautical game
that begins ASHORE got "no exit" instead of the nautical refusal for
FORE/AFT/PORT/STARBOARD in the opening room. Not a bug: dirs_nautical
defaults to true (aboard), so the opening room treats nautical
directions as live until the flag is set false; a step-off handler
can reach every land room EXCEPT the start. The fix is guidance made
loud: the compiler now notes it when the nautical granule is summoned,
the start room has no nautical exit, and no on-start rule sets the
flag (sema._lint_nautical_land_start, scoped to the shipped granule
via the dirs_nautical signal). Fires for a land start, silent for The
Cormorant (ship start) and for an author who sets it in on start.
Granule comment and docs/05 gained the land-start guidance. Suite 882.

## 2026-07-14: purloin detaches a component (Cosmos 0.36.1)

Charles Moore Jr.: PURLOIN (the debug fetch verb) "doesn't work" on an
item that is a COMPONENT of a character (a hat, say). Root: fetch did
`move noun to player` but left the `component` mark set, so the item
became a component OF THE PLAYER, held in the tree but invisible in
the inventory listing (a component never lists as contents). It said
"Fetched X." and then nothing was carried. Fetch now clears the mark
first (guarded by any_components, so it folds away without
components), and the object lands as an ordinary carried thing. Plain
(non-component) fetch unchanged; a game with no components compiles
identically. Regression test on the VM. Suite 883.

## 2026-07-14: search works on any object (Cosmos 0.36.2)

Charles Moore Jr.: SEARCH only worked on containers and supporters,
not NPCs. Stefan's redesign (discussed live): SEARCH works on ANY
object, sense or not (the story's call). No auto-listing of contents
anymore; the default is a neutral "A close search reveals nothing you
did not already know." A shut/closed/locked container keeps the funny
Schroedinger's-loot message (Stefan liked it, kept for exactly the
sealed case; a locked container is not open, so one check covers all
three). The old search_contents block survives as an AUTHOR HELPER,
DCE'd unless called: `on search` / `search_contents(self)` on a
character makes a frisk reveal what they carry, which is the original
request handed back as author control. msg_search_closed reworded-in;
docs/05 updated. Suite 884.

## 2026-07-14: search_contents removed, search reveals by reachability (Cosmos 0.36.4)

Following the search redesign, Stefan questioned search_contents at
the root: why list contents at all? For a container it is redundant
(the room listing already shows "(contains a red apple)" and the
contents are in scope), and for a character it is incoherent (naming
items that are not in scope: verified you cannot examine or take the
guard's key after "You find a brass key"). So the helper had no honest
use case and is deleted. SEARCH is now: neutral cheeky default,
Schroedinger for a shut container, author override for anything real.
The override reveals by making something REACHABLE (the IF idiom):
`on search / move key to here` spills an NPC's item into the room so
it is takeable, or `now note is not hidden` for a note living in the
room. docs/05 and the tests updated to the reachability pattern
(verified: frisk -> take key -> Got it.). Suite 884.

## 2026-07-14: search reads the object; a living thing rebuffs (Cosmos 0.36.5)

The SEARCH design, finished properly after Stefan pulled me back from
iterating in code (discuss-first). The default now reads the noun: a
LIVING thing (animate) gets a cheeky social rebuff ("${The noun} gives
you a look that says, plainly: whatever it is you are about to try,
stop it."), because frisking a person is a social act, not a
discovery; a SHUT container keeps its Schroedinger secret; everything
else gets the neutral "nothing new". A corpse is not animate, so it
drops past the rebuff to the neutral case and an `on search` override
turns out its loot. Ordering: shut-container refusal first (no alter),
then alter, then animate rebuff, then neutral. A real search reveals
by REACHABILITY (move to room / un-hide a room note), never by naming
the untouchable. Design and wording pre-approved by Stefan this time.
Suite 884.

## 2026-07-14: move-to-scope seeds the backstage room (arcc 0.12.2)

A mechanical bug found while validating the search-reveal idiom for
Charles: `move x to scope` failed with "unknown name 'scope'" unless
some object was declared `in scope`, because the backstage room was
seeded only by a placement. docs/01 already promised move-to-scope
worked. Fixed: sema now also seeds the scope room when any
`move ... to scope` appears in the code (sema._moves_to_scope, a
generic AST walk). Still zero cost when neither `in scope` nor
move-to-scope is used (verified: no backstage room seeded). This
makes move-to-scope the clean frisk reveal (item reachable, not
listed on the floor). Compiler-only; Cosmos unchanged. Suite 886.

## 2026-07-14: swap() for object replacement, AGAIN follows (Cosmos 0.36.6)

Charles Moore Jr.: AGAIN "squirrely" when an action swaps one object
for another (attack Bob -> unconscious_bob); AGAIN answered "you see
nothing of the sort here". Root: AGAIN replays resolved operands (fast,
NOT Inform re-parse, deliberately), and the handler moved the object
away without updating `noun`, so last_noun pointed at the departed
object. Stefan ruled: no parser surgery, stay in the operand model.
Solution: `swap(old, new)` in core.prelude, moves new into old's place,
removes old, and re-points every live binding the turn holds (noun,
second, pronouns it/him/her/them, universal-safe: Spanish leaves
it/them at nothing so the check no-ops). AGAIN then replays the
replacement and "examine him" follows. Verified on the VM (attack ->
again -> "Doesn't seem sporting"; x him -> the sleeper's desc). DCE'd
when uncalled (byte-identical). docs/01 section 9 documents it; VSIX
0.13.4 adds swap to the services list. Suite 888.

## 2026-07-15: lock/unlock is a real state machine now (Cosmos 0.37.0)

Charles Moore Jr.: "you can unlock a lock by not providing a second is
still there." Root: a lockable+locked thing with NO unseal_with
unlocked bare-handed (the old "keyless bolt" shortcut). Stefan reframed
it as a logic problem, not mechanics, and specified the full state
machine. Built: LOCK/UNLOCK now read the object. UNLOCK: not lockable
-> just open it; not locked -> open it instead; locked -> needs the
unseal_with opener HELD, and a keyless lock (no opener) REFUSES (fixes
the bug; the story springs it with `now x is not locked`, the crowbar
use case Stefan named). LOCK is the mirror (already-locked, close-first,
opener-held, keyless-refuses). Messages rewritten in the library's
cheeky voice AND mechanism-agnostic (a key, a keycard, a code):
"You don't have whatever ${the noun} wants...", "${The noun} is
entirely unimpressed by ${the second}.", "Already locked. Thoroughly.
Smugly, even.", "${The noun} doesn't lock, and shows no ambition to
start." Two new blocks (msg_already_locked, msg_not_locked) added to
all three packs (German/Spanish functional, flagged for Stefan's
idiomatic+cheeky pass). Redirect via perform("open"). Size grew ~284
bytes/game -- Stefan: the cost is the ADDED MECHANIC that was missing,
not the words, and it is worth it; 35 ceilings raised, dated. Suite
891.

## 2026-07-15: a silent appearance leaves no blank line (arcc 0.12.3)

Charles Moore Jr.: an `appearance` block that opts out (prints nothing
while the player rides the object) still emitted a blank line in the
room description. Root: `say obj.<computed>` flushed the pending
paragraph break BEFORE running the block, so a block that returned
without printing left an orphan break for text that never came. Fix in
lower.py: defer the flush INTO print-or-run -- the plain-string branch
flushes (a string always prints), the block branch does NOT, leaving
the break pending for the block's own say/show/print_name to flush when
(and only when) it actually prints. A silent block leaves the break for
the next object to coalesce, so the paragraph spacing stays correct
either way. Byte-neutral: the flush moved, it was not added. Covers
`intro` and every computed-text property, not just `appearance`. New
VM-harness test (test_silent_appearance_leaves_no_blank_line). Suite
892.

## 2026-07-15: perform keeps its noun when the game uses alter (arcc 0.12.4)

Charles Moore Jr.: `perform("enter", noun)` gave "Mount what?" and
`perform("go", up)` gave "Which way?" -- the nested action lost its
operand. Root: perform saves the enclosing handler's `altered`
registration around the nested call so the inner action does not fire
the outer handler's report. That save used a PUSH onto the stack -- but
perform had already marshalled its operands onto that same stack, so the
`push altered` slid under the two Variable(STACK) reads in the call. The
nested action received the saved altered (0) as its noun/direction and
the real operand as `second`. Only triggered with an `alter` anywhere in
the game (any_alter on), which is why the lock redesign's own
perform("open") calls, and every alter-free game, never saw it. Fix in
lower.py: save `altered` into a temp local instead of the stack, out of
the operands' way. Byte-neutral (push/pull -> store/store, same two
ops), any_alter only. New VM-harness test pairs perform with alter.
Suite 893.

## 2026-07-15: matrix Phase 1, the mutable sibling of catalog (arcc 0.13.0, Cosmos 0.38.0)

Charles Moore Jr. asked for a mutable, indexable array (the Inform
array he reaches for). Stefan's design: a NEW summoned feature named
`matrix`, catalog's mutable sibling, kept strictly out of the base
language (summon.matrix required, zero bytes un-summoned); docs lead
with "you almost always want a catalog, not this." Phase 1 (1D, the
whole of Charles's request) shipped: declaration `matrix m capacity N
[of object|byte] [checked]` with optional seed values; reads reuse the
catalog verbs unchanged (entry, calculate, last, dice, position, in,
for each) with the count read at runtime as the LIVE length; mutators
append / remove (order-preserving shift AND O(1) swapping) / insert /
clear / load-from-catalog, which are also expressions returning a
success flag (`if append clue to clues is 0`). A matrix shares the
catalog region and base, header [count, capacity, cells] (the unused
catalog `widest` word repurposed to the capacity so every granule call
stays within the Z-machine's 3-argument limit); the mutator logic lives
in editable cosmos/matrix.granule (peek_word/poke_word, no heap, no
allocator), overridable by same-named block. Numeric only (number /
object / byte), never text; text stays a catalog's job. Pay-for-use
proven: un-summoned games are byte-identical. `arcc -s` reports
matrices and their dynamic bytes. 18 new tests; suite 911. DEFERRED to
Phase 2 (with the 2D table work, which shares the layout machinery):
true byte PACKING, so `of byte` currently range-checks 0..255 and is
correct but still word-backed (no memory halving yet).

## 2026-07-15: matrix Phase 2, two-dimensional tables + byte packing (arcc 0.14.0)

The 2D form and the worked example, on top of Phase 1. `matrix m R by
C` is a fixed grid (a table), no length and no mutators, only cell
access: entry(m, r, c) reads and change entry(m, r, c) to v writes,
rows(m) / columns(m) give the dimensions, all compile-time constants;
literal indices are bounds-checked against the shape. A 2D grid is flat
R*C cells row-major with NO header (dimensions fold as constants), so
the table is exactly its cells: entry lowers to one loadw at off +
(r-1)*C + (c-1). `of byte` packs a 2D grid one cell per byte (loadb/
storeb at byte offset off*2 + ...), half the memory, so a 16x16 map is
256 bytes not 512 -- the case where packing actually earns its
complexity. This is the thing Inform makes you hand-roll (arr-->(y*w+x),
no shape, no bounds safety); here it is a declared, checked construct.
Byte packing on 1D matrices is deliberately NOT done (poor cost/benefit
-- 1D arrays are small and carry mutators/position/for-each that would
all need byte variants); `of byte` on a 1D matrix constrains values to
0..255 and stays word-backed, documented as such. Worked example
examples/features/matrix.storyarc (a botanist's vasculum: a 1D object
matrix you gather into and a 2D byte planting bed), README What's new
entry, docs/01 section 4a extended. 7 new tests; suite 919.

## 2026-07-15: Actaea record / replay / check (Actaea 1.1.0)

Multiple adopters (improvmonster, Garry, Ichiro Ota) asked for Inform's
RECORDING/REPLAY to step through walkthroughs. Stefan's ruling: do it
"the Actaea way", in the interpreter, not as Cosmos verbs -- it costs
the story nothing, works on any file, and Arcturus writes the script.
Three flags over one plain-text file (actaea/session.py, a SessionIO
wrapper at the io boundary so it wraps any front-end):
  --record FILE  play, saving commands AND the game's replies as a
                 readable transcript (> command lines, replies beneath).
  --replay FILE  run the commands, then hand over the keyboard (skip
                 ahead); with --headless, run and stop.
  --check FILE   re-run against the current game and report in PLAIN
                 words whether it still plays the same, stopping at the
                 first divergence (state has moved, the rest is noise);
                 exit 0 matched, 1 diverged, so a build can gate on it.
Author-friendly per Stefan's steer (these are authors, not shell-diff
experts): no diff tool, no jargon, the tool names the command and shows
before/now. Commands are the editable spine, so a hand-added command
with no recorded reply is run and counted as NEW, never a failure;
append freely, insert-in-the-middle correctly flags because state
diverges. --replay IN --record OUT extends a walkthrough. Session modes
run on the plain console (a debugging activity), not the window. Docs/06
section 3, and pointers from docs/05 debug + debug.granule for anyone
hunting Inform-style REPLAY. 10 unit tests; suite 929. Decisions from
Stefan: flags only, record raw typed lines, no output-stream-4
conformance.

## 2026-07-15: computed exits, the documented feature made real (arcc 0.15.0, Cosmos 0.39.0)

An adopter hit `error: computed value property is not supported yet` on a
computed exit (`north block / if portcullis is open / return inner_hall /
return nothing`) that docs/02 section 11a documents with a worked example.
docs/04 flatly contradicted docs/02, calling it a compile error. Stefan's
call: implement it, directions only. A general computed value property
stays unsupported (a read cannot tell an arbitrary value from a routine
address), but a computed EXIT is the safe case: a destination is a room
OBJECT NUMBER (small), so it never collides with the block routine's large
packed address. Built: codegen relaxes the raise for direction props and
generates the value-returning routine; a new __routines__ threshold global
(the lowest packed routine address, pre-biased +0x8000 like __strings__);
an exit_dest(room, dirprop) intrinsic that mirrors "print or run" as "read
or run" -- compare against __routines__, call the block if at/above, else
use the value. Cosmos reads every exit through exit_dest now (the go
handler and the verbose_exits scan, so a blocked computed exit is not
listed). Pay-for-use: exit_dest folds to a plain get_prop when the program
has no computed exit, so a static-exit game is byte-identical (size gate
green, untouched); __routines__ claims a fixed global slot only, no bytes.
docs/01, docs/02, docs/04 reconciled. 6 new tests; suite 936.

## 2026-07-15: chapters rank as game for EVERY declaration, verbs included (arcc 0.15.1)

Charles Moore Jr.: a `verb "stand"` redefined in a summoned chapter
(grammar.storyarc) still gave extendedverbs' "You're already on your
feet." Root: the 0.11.35 "chapters rank as game" fix tagged only chapter
BLOCKS and HANDLERS with origin="game" (for the block override lattice);
it never reordered the decls, so a chapter's VERB still rode at its
granule-tier summon position, and verb resolution (dictionary last-wins
by world.verbs ORDER) let a later-summoned granule (extendedverbs) win
the word. So message overrides worked but verb overrides did not -- the
same root, two resolution mechanisms, only one fixed. Completed it in
combined_program: summoned .storyarc chapters now load in the GAME tier
(library -> granules -> chapters -> main file), so EVERY chapter
declaration (verbs, objects, kinds, not only blocks/handlers) ranks as
game and overrides a granule in any summon order; the main file stays
most specific. Verified on Charles's exact structure (chapter verb,
extendedverbs summoned after -> "Done." not "feet"). Immediate
workaround (summon library granules first) no longer needed. docs/01
s.13, docs/05 s.1, combined_program docstring updated. 1 new multifile
test; suite 937.
