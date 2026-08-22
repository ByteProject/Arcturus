# Arcturus progress

A living log of where the project stands, maintained as work proceeds. The
authoritative plan is `docs/00-roadmap.md` (milestones B0 to B13); this file
tracks status against it and records decisions made during implementation.

How this project is governed, so the log reads in context: every design,
naming, wording, and scope decision in Arcturus is made by Stefan Vogt.
AI is used as the implementing engineer under those rulings, on a standing
mandate for the adopter support queue (diagnose against invented content,
fix, test, ship) and on explicit instruction for everything else; design
questions end in a discussion and wait for Stefan's ruling before a line
of code moves. Entries below record both the rulings, in Stefan's voice
where possible, and the engineering that followed them. Where an entry
names a decision, it is his.

Last updated: 2026-07-18.

Model handover: `HANDOVER.md` (repo root) is a holistic orientation written at
the switch to Anthropic's Fable model, with an assessment task to run before B8.
Read it alongside this log.

>>> B8 DAY-TWO HANDOVER CHECKPOINT (2026-07-03, written for compaction) <<<

WHERE WE ARE. Versions arcc 0.9.0 / Cosmos 0.12.0; 384 tests green; the size
gate must be GREEN before every commit; the amalgam (build/arcc) and the
vsix (editors/vscode/arcturus-0.9.0.vsix) are current; posada.z5/gasthaus.z5
rebuilt. The B8 game (gitignored, NEVER COMMIT) verifies end to end on dfrotz
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

>>> END DAY-TWO CHECKPOINT <<<

THE POST-MORTEM, AND GHOSTS LEAVES THE ROADMAP (2026-07-04, Stefan's
blessing after playing the B8 game through; arcc 0.10.1 / Cosmos 0.14.1): a
`finish` banner is now followed by the FINAL SCORE (msg_score, rank and
all) and the classic prompt, "Would you like to RESTART, RESTORE a saved
game, or QUIT?" (msg_game_over, three languages), looping until answered.
The answers are matched BY ACTION against the pack's own
restart/restore/quit verb words, so every language pack works with zero
extra wiring; a failed restore reports msg_restore_failed and re-asks;
a successful restore resumes at the save point by the existing r==2
machinery. Wired in the finish lowering (call blk_game_over before quit;
a bare no-Cosmos build still just quits; games without a finish pay
nothing, DCE). STEFAN'S PLAY-PASS VERDICT on the full
B8 port: everything fine, and the build is SIX KILOBYTES SMALLER than
the PunyInform variant of the same game - the size charter proven on
the flagship. B9 (GHOSTS OF BLACKWOOD MANOR) IS DROPPED from the roadmap on
Stefan's call: it was the easier port, and with B8 complete its
sufficiency proof is redundant; the milestone number stays reserved so
B10-B13 keep their names (docs/00, README, CLAUDE.md, memory synced).
Flagged for later: an after-handler ordering oddity seen in a test
fixture (on take / continue + on after take looked like the after body
ran without the default completing); to investigate, not chased today.
NEXT: Stefan's word on next steps (quality sweep vs B10 Actaea).
400 tests; ceilings re-pinned (finish games pay ~250 for the post-mortem).


GAIN JOINS TELEPORT, AND THE OVERHAUL BUMP (2026-07-04, Stefan's
blessing; arcc 0.10.0 / Cosmos 0.14.0 / vsix 0.10.0, the minor bump
marking the day's fundamentals overhaul): gain(obj) is a standard Cosmos
block, teleport's sibling: the acquisition without TAKE pays a scored
thing's points exactly once (any_scored fold), marks it moved and seen,
then moves it to the player. THE TAKE HANDLER ITSELF FUNNELS THROUGH
GAIN, so there is exactly one acquisition path (symmetric with go
funnelling through arrive); cost ~12 bytes per game for the call frame,
the B8 game got smaller (its two sites now share). DOCUMENTED AGAINST MOVE, hard,
per Stefan: Arcturus's `move` is the silent tree operation, Inform's
"move lamp to player" idiom is our gain; docs/01 section 5 carries a
CAREFUL-INFORM-HANDS warning box (gain when the player RECEIVES,
teleport when the player ARRIVES, move for silent stage management), the
scoring section and docs/02's teleport passage cross-reference it. the B8
game's story-local gain block deleted (the Cosmos one serves). HIGHLIGHTING:
block calls with arguments render the callee in its own scope
(entity.name.function) with the arguments left to the value scopes, per
the screenshot ruling; bare zero-arg calls are lexically plain names and
stay unscoped. tests: gain pays once, re-take after gain pays nothing.
399 tests; ceilings re-pinned; all artifacts + amalgam at 0.10.0; the
B8 walkthrough unchanged.

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
the start path, conditional on status_bar). The B8 game has ZERO par() calls.
(4) THE STYLE SWEEP: not (x is y) -> x is not y and NAME() -> NAME
across every prelude, granule, example, the B8 game, and the docs snippets;
byte-neutral once the fold fix landed (slightly negative). HIGHLIGHTING
POLICY (the screenshot): dot-chains render three scopes - keyword (say,
zcolor, par, summon), modifier chain (.par, .yellow, .font, one scope),
trailing value (the colour word) - grammar reworked, vsix 0.9.3.
tests/test_sugar.py pins bare calls, is-in, par.say spacing, and the
banner-under-bar; 398 tests; the B8 walkthrough unchanged.
PENDING STEFAN: the gain() promotion question (name and blessing).

SAY.PAR: THE PARAGRAPH RIDES THE SAY (2026-07-04, Stefan's sugar order,
"as little internal-cosmos blocks as possible" in author code; arcc
0.9.2): `say.par "..."` prints the text and marks the library's pending
paragraph break, so consecutive prose paragraphs are one line each with
no par() between them. Modifiers are a composable dot-chain in any
order, Stefan's addendum: say.yellow.par and say.par.yellow are the
same coloured paragraph (one colour per say, one par, enforced with
clear parse errors). Lowering is the same par_pending store the par()
intrinsic makes, inline, so the sugar is byte-neutral-or-better (the B8 game
shrank: the statement form skips the intrinsic call's value plumbing,
and its say+par() pairs merged in the sweep). docs/01 sections 16 and 16a, the VSCode grammar (the
say/zcolor rule now matches chained modifiers), and the vsix updated to
0.9.2 (repackaged directly, no node on PATH). 394 tests; the B8 walkthrough unchanged.

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
and meta immunity. 392 tests; the B8 walkthrough unchanged.

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
all three languages (gasthaus bar reads "Züge: 1"); the B8 game's scored bar and
walkthrough unchanged. Statusline tests split scoreless/scored fixtures;
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
388 tests; ceilings re-pinned; docs synced; the B8 walkthrough unchanged.

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
(dative), ES "pregunta posadera"/"dile posadera" likewise; the B8 walkthrough unchanged. OOPS aside for the record: DE answers to
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
games unchanged). The B8 game rebuilt; its walkthrough closes unchanged (TELL hints,
ASK opens the menu). Native pass: the
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
NOT fire on enter (walking's event); unused it folds away. The B8 port's
go_to() retired in its favor (5 call sites; story keeps only gain() for
the TAKE-bypassing plate and slab). ASK IS TALK in menu games (Stefan:
"TELL holds no right to exist but ASK shall be mapped to talk"): the
conversations granule declares verb "ask" -> talk noun / talk noun about,
so ASK VLAD (and "ask vlad about the vines") opens the menu instead of
lecturing; the about-literal grammar line matters, it puts "about" in the
dictionary as a phrase boundary, or the matcher spans the phrase
into a disambiguation ask (caught live in the B8 walkthrough), which
verifies unchanged.
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
384 tests.
AND THE B8 PORT went lean the same day (Stefan: importing a verbset
for three verbs is not memory efficient; his .inf defined them in code
and so does the port); details in the port's own log.

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
text. The B8 game's state block reads `flag`/`counter` now. docs/01 section 4 rewritten around the
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
off-road escape. The B8 game: `scoring` plus its award sites and the original's rank
ladder pinned at its Inform thresholds; the hand-set max is GONE, which
is the entire point. docs/01 has the new Scoring section
(6a). 377 tests (test_scoring.py 7).

THE SLICE-REVIEW BATCH (2026-07-03, Stefan: "All of them. When we encounter
something, we fix it. That was the deal."). Five rulings, five features, one
commit. (1) THE SCOPE ROOM, his design: `thing vlad of character in scope`
places an object BACKSTAGE, an invisible seeded room whose contents are in
scope everywhere (in_scope hook + scope_room()/any_scoperoom() fold, zero
unused); `move x to scope` stages at run time. Replaces the spans hack for the B8 companion and his parts, and closes
gap G4: a visible-but-unreachable thing gets Inform's honest "no chance
to reach it". Never
listed; backstage objects defend themselves in handlers. (2) G6 RESOLVED,
RECIPIENT DISPATCH: dispatch consults the SECOND noun's handlers between the
noun's and the room's, so a give runs the recipient's own on give (the B8 handler moved back
where it belongs) and a put gets the container's refusal. ~40 bytes core. (3) SCORED: the attribute + room_score/
object_score knobs (default 5, core.prelude, retunable); a scored room pays
on first visit (incl. the start room; run_game now marks the start room
visited, a latent double-pay bug), a scored thing on first take; folds to
zero unscored. The B8 game's manual awards became attributes. (4) THE TAG:
a `tag` text property (usually `tag block`, print with show) appended in
listings and inventory via the shared show_tag hook in all three packs:
closing gap G2 without touching print_obj.
(5) START TITLE: with the statusline summoned the opening description skips
its title line (title_in_bar seam, hide_title), the Puny start-screen
convention Stefan screenshot-diffed. Batch cost ~84-88 bytes per game
(recipient dispatch + title seam + tag hook; scored and scope room fold).
369 tests (test_worldfeatures.py, 7). The B8 game uses all five; its gap list
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
breathing texture (NPC behavior, layered room mood). The B8 game's hand-rolled ambience is GONE: its rooms carry the full
Inform message lists as ambience blocks now. Showcase: The Last Ferry
(examples/granules/ambience.storyarc: jetty on living odds, waiting room in
order once with a do-line, a thing-mounted purring cat gated on mood, WAKE
CAT turns the dial). Zero ceiling drift: unsummoned games are
byte-identical. 362 tests. Also this session, from Stefan's slice review:
booleans confirmed first-class (the B8 game's flags rewritten true/false; the
1/0 style was the porter's, not the language's), clear_screen() and
random(n) intrinsics, the topic once-vs-when-vs-reveal doc passage, and the
B8 prelude now clears on a keypress like the original. STILL AWAITING
RULINGS: the scope room (his design, proposal costed), scored property,
G6 recipient dispatch, the listing tag ("(full)").

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
the B8 port the proof, so library feature-completeness comes first and
the granules land BEFORE it). Both are pay-for-use and English-worded with the
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
B8 port (checkpoint item 3). A VERSION BUMP is proposed: the B8
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
B8 port.

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

WHERE WE ARE. B8 (the Hibernated 2 port) is open; its working material
sits in hibernated2/ (GITIGNORED, unreleased, never commit). The toolchain enablers the port needed are ALL DONE
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
(3) then the B8 port's first slice, watching arcc -s.
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

B8 ENABLERS (2026-07-03): opening the real B8 source surfaced three Cosmos
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
wants (the Inform way is Initialise returning 2). The docs/02 "banner
event" claim was false and is gone. (3) THE QUOTES GRANULE (summon.quotes):
the centered reverse-video quote box, Trinity-style, the B8 opening's manner.
quote(lines, width) / quote_line() + show(...) / quote_done() (keypress,
clear); centered from the reported screen width for the 40-column targets; no
output_stream needed (full reverse row first, overprint via set_cursor); no
words of its own, so language-independent. Ad Astra showcase demos the classic
quote-keypress-banner order. 304 tests pass.

B8 OPENS (2026-07-02). The port's working material lives in
hibernated2/ (gitignored and never committed: the game is unreleased
and this repository is public). STEP ZERO, the scale smoke test, is done and green:
tools/scalegen.py deterministically generates a synthetic game at the B8 game's scale
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
after seeing Inform's -s output for the B8 game, whose real Inform-build
numbers fit comfortably inside our ceilings; the bare-Cosmos baseline
(28/48 attributes, 19/62 properties, 22/240 globals) leaves room for
all of it.

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

B6 PART 2 - ABBREVIATIONS: baked-in default DONE (committed 8e702fd); opt-in
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

  NASTY BUG FOUND + FIXED (committed 7cf0aba, a real latent correctness bug the
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

B6 COMPLETE. The opt-in --make-abbreviations pass landed (committed be01390): arcc
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

B4.5e.4a done (committed 6011098). Multi-word verbs via particles:
- dictionary: particle words (on/off) flagged bit 5 with an id (_PARTICLE_WORDS;
  up/down/in/out stay direction words). action_id("name") intrinsic.
- english.prelude resolve_verb splits verb (128) / direction (64); find_particle
  + compound remap (switch+off -> switch_off, take+off -> take_off).
- verbs.prelude: switch/turn, wear/don, remove/doff + defaults. THE BRASS LANTERN
  PLAYS END TO END. tests/test_particle.py.

B4.5e.4b done (committed 78e75bb). Vocabulary + hidden:
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
- Override-by-block (18584c5): a game or granule block beats a Cosmos library
  block of the same name (ast.BlockDecl.origin / wm.Block.origin; sema._collect;
  cosmos.combined_program tags library blocks). The author's way to reskin a
  message without unpacking the library. tests/test_override.py.
- --extract-library DIR and --eject-language [DIR] (522d87a): write the bundled
  library (or just english.prelude) out for hacking; compile against it with -L.
  tests/test_cli_extract.py. README documents them (9d734dd).
- intro property + moved attribute (d181a44): Inform's `initial`; an object shows
  its intro text in a room until taken (sets `moved`), static objects keep it.
  describe_room shows intro vs lists; take sets moved. tests/test_intro.py.
- Scenery + grains unified on msg_scenery (43585f8): dropped msg_take_scenery;
  take of a scenery object gives the grain line; describe_room skips scenery from
  the listing (still examinable).
- The blessed message set in english.prelude (8782082): all of docs/message-set.md
  in the agreed voice (warm-to-witty), using ${the noun}/${The noun}/${the
  second}. The wording is Stefan's; redlines applied (75c8e6d).
- Sensory + flavor verbs + the animate model (79142b4): touch, smell, taste,
  listen, eat, drink, attack, kiss, push, pull, turn, climb, read, talk, jump,
  wait, sing. New `animate` attribute, set by the person kind (sema seeds it like
  room+lit). talk to animate -> msg_no_talk; to an object -> msg_only_animate.
  `turn` is its own verb now; compound() is base-aware (switch/turn +on/off,
  take +off; everything else ignores particles so "put X on Y" stays put).
  tests/test_flavor.py.
- docs: 03-compiler-pipeline.md (ed29740), verb-set.md (the S/E split, Stefan's),
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

NAMED OBJECTS DONE (6b3f0b8 + rename): the `named` standard attribute (renamed
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
- [x] 1. PARSE + COLLECT + COMPILE INERT (committed 03de1d9). The `topic`
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

- Free-handler origin ranking (arcturus/ast.py, worldmodel.py, sema.py,
  cosmos.py, codegen.py): Handler.origin None=game < "granule" < "library",
  sorted in _free_react_handlers/_free_other_handlers. Fixes a LATENT bug:
  a story's free `on xyzzy` never overrode the Cosmos default.
- Dual-role dictionary flag 136 (dictionary.py: a word both verb and
  preposition keeps both bits; english/spanish/german packs: resolve_verb,
  arity check, is_separator accept 128 or 136; parser.prelude: the two-noun
  slicing and phrase-end scan test 8 or 136 via `let ef`). Fixes a game's ABOUT
  destroying the ask-about grammar.
- Assembler range asserts on BOTH branch encoders (relax/shrink pass and
  link() fixup): short 0..63, long signed 14-bit. Added while hunting the
  crash; they never fire, which is evidence (see below), and they stay.
- tests: 400 pass; the ~25 size ceilings in test_sizes.py are NOT re-pinned
  yet (the 136 flag + origin sort grew files slightly). Deliberate: re-pin is
  part of the post-fix commit, not before.

### THE CRASH (open, blocking)

Symptom: the full B8 build with the meta trio executes a clean @quit on FIRST
ARRIVAL at a late room. No error, exit 0, silent even under `dfrotz -Z 3`.
The room description prints in full, then the session ends where the next
output (an object intro listing) should begin.

Bisection (all artifacts in the session scratchpad, probe builds;
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
re-pin the ~25 ceilings, full suite green, the full B8 walkthrough, rebuild build/arcc +
example artifacts, then commit compiler+cosmos work (origin ranking, flag
136, asserts, the fix). The B8 source itself stays gitignored, as ever.

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
the walkthrough truth is the B8 game running to its ending on BOTH
dfrotz and fizmo-console.

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
  examples; the B8 game unchanged). Cloak pays 68 bytes for what it uses.
- Semantics pinned in docs/02: completed = refused still 0 (every library
  refusal sets it; story refusals should too); an instead handler still
  completes; grain turns take no after pass; after handlers may continue;
  on-other never answers the after pass.
- tests/test_after.py: order (default before after), refusal gates it,
  instead still fires it, free after rules, when guards, and the catch-all
  staying out of the after pass. 407 tests green. Cloak re-pinned 15220
  (z8 15688); the walkthrough now shows the cloak REALLY leaving the
  player's hands ("You're carrying precisely nothing" after the hang).

ALSO this session, before the fix: the B8 game compiled with custom
abbreviations (--make-abbreviations, summon abbreviations.granule):
8,524 bytes saved (6.4%), ~10K under its Inform build; full walkthrough
to the ending on fizmo-console. And the sign-bias crash fix landed as
104016b (see above). fizmo-console is now the debugging interpreter of
record (fizmo/ncursesw for colours); memory updated.

NEXT: Actaea (B10). Plan confirmed by Stefan (module map per docs/06 s.4,
io.py boundary, conformance harness under tests/actaea/). Story files for
conformance live in actaea/conformance/ (CZECH, TerpEtude, the B8 game, Ghosts,
deseos for accents, Calypso, Anchorhead, Jigsaw for z8). Update docs/06 +
the handoff prompt to B10/B11/B12 numbering in the scaffold commit (Stefan
approved). Parked: CREDITS wording veto, inline emphasis colour, the B8 quality
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
checksum verified), and the B8 game all load and report correctly; a non-story is
rejected cleanly with exit 2 ("version 60 story; Actaea plays versions 5
and 8"). tests/actaea/unit/test_loader.py (11 tests) builds its probe
stories with the Arcturus compiler in-process, so no binaries are checked
in; conformance-file tests skip when the directory is absent.

Conformance assets (actaea/conformance/, LOCAL ONLY, *.z5/*.z8 gitignored;
third-party copyrighted works stay out of the public repo): czech.z5 +
czech-reference.txt (the v5 reference transcript), praxix.z5 (fetched from
the IF Archive; no reference transcript exists, it self-reports), etude.z5,
ghosts.z5, deseos.z5 (accents), calypso.z5, anchor.z8, Jigsaw.z8, and the B8 game
via hibernated2/. Praxix source praxix.inf available if wanted.

NEXT: M2, the instruction decoder and disassembler (all four forms,
extended opcodes, store/branch/inline-text flags), done when it
disassembles a real story without error and the decode unit tests pass.

TODO (Stefan, 2026-07-04): ABBREVIATION QUALITY INVESTIGATION, not now. Data
point: the B8 game's Inform build compiles to 137K plain and 123K after Henrik
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
computed calls static walking cannot follow), the B8 game (387), and
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
documented fiction; nothing shipped used patterns (the B8 game included), so no
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
flagship again: the B8 game's FULL WALKTHROUGH over the live model to
its ending, quote boxes growing the split to 9 rows and folding back,
finishing with a single status row. One fix on the way: a blank scripted keypress means Enter
(the dfrotz walkthrough convention; the B8 intro found it).
499 tests. actaea 0.8.0.

M8's VISIBLE done-test is Stefan's turn: the B8 game in the window (the status
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
colour path live, and the B8 walkthrough still reaches its ending
with the model's colours flowing (final state: white on default,
roman). 503 tests. actaea 0.9.0.

M9's visible half is Stefan's: the B8 game in the window shows the coloured
banner, say.yellow callouts, and the quote box in proper dress. Then
M10: Quetzal save/restore interoperating with a reference interpreter
both ways, plus restart.

## 2026-07-05 (cont.): the light interpreter ruling + direction or-lists

Stefan's ruling on M9's look: Actaea's own screen is BLACK ON WHITE
PAPER; a game that wants a dark screen SETS its colours. The B8 game not setting a background was a bug in the game, now fixed
in its (gitignored) source. The dark-interpreter commit is reverted the
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
old silent shape `on go south, up` (comma parsed as a bogus
preposition, handler never fired) is now a NAMED error pointing at
'or'. The B8 game's line fixed accordingly; it recompiles and walks
to its ending with the model ending white-on-black as its zcolor
declares. 505 tests.

## CHECKPOINT 2026-07-05: compaction point; M10 is next

State: CLEAN TREE, everything committed through 3afbc3d. arcc 0.10.5 /
Cosmos 0.14.3 / actaea 0.9.0 / 505 tests green. Actaea M1-M9 are DONE and
Stefan-verified in the window (his screenshot: cyan bar, dark screen,
the whole toolchain in one picture).

### The M9 verification round (all committed)
- Stefan's ruling, now doctrine: Actaea is a LIGHT interpreter (black on
  white paper, declared in header 0x2C/0x2D); a game that wants a dark
  screen SETS its colours. the B8 game lacking zcolor.background was a GAME
  bug; Stefan fixed it in the (gitignored) source. The window background is
  DYNAMIC: erase repaints in the game's current background (that is how
  zcolor.background = set_colour + erase_window -1 takes the screen).
- The typed line wears the game's input colour (Cosmos sets zcolor.input
  right before every read; the input region takes a look-tag at read
  start, swept per keystroke, caret matches). The B8 game's input is cyan.
- No scrollbar (native = unstyleable white strip; wheel/trackpad + the
  unread-return cover it). Window exactly 80 cells wide, ~30 lines.
- Compiler 0.10.5 out of the same round: direction OR-LISTS in patterns
  (`on go south or up` guards way; single dirs byte-identical), mixed
  direction/object operands and non-go direction patterns are named
  errors, and `on go south, up` (comma = bogus preposition, silently
  dead until now) is a named error pointing at 'or'. The B8 game's
  line fixed; it walks to its ending.

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
  Jigsaw.z8; the B8 game via hibernated2/.
- One Tk root per process (Tk 9.0 SIGTRAP); the GUI smoke test is the
  only Tk test and flashes a real window during the suite.
- python-tk@3.14 installed via brew (Tk 9.0).
- fizmo-console = debugging terp of record; pytest harness = dfrotz.
- The B8 source NEVER committed (gitignored); compiler work commits fine.
- Parked: the B8 quality-sweep list (in the gitignored source), the
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
the real game: the B8 game walks to its ending on the M10 build, an
Actaea save resumes in dfrotz mid-game, and a dfrotz save at the same
depth resumes in Actaea, room, score, and inventory intact. Every interop failure along the way was the test harness, not
the format (dfrotz pagination without -h 8000, a stale file's
overwrite prompt, the B8 intro's keypresses eating script lines): worth
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
reference byte for byte; the B8 game to its ending. 538 tests.
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
  where the player is with the destination worded (the flagship's
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
0.13.3 (current; no grammar changes needed today). HEAD 4b69210,
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
(gitignored). BEACH GATE PASSED on C64+CPC+A8 (commit 4139ce5);
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

## 2026-07-16: enter/exit report on/in vs off/out (Cosmos 0.40.0)

Field request (via Charles): the flat "Done." on a successful ENTER/EXIT
said the same for a supporter and a container. Now the report is worded
by the world model: get ON a supporter / get INTO a container, get OFF a
supporter / get OUT OF a container; both directions, since a game that
says "get off the stool" but only "Done." on the way up reads lopsided
(Stefan: do both, plain wording, movement messages were never cheeky).
The world-model choice (supporter vs container) is made in agnostic
board_report / leave_report (actions.prelude); the wording is four new
language-layer blocks (msg_get_on / msg_get_in / msg_get_off /
msg_get_out) in all three packs (German with cases: auf/in Akkusativ,
von/aus Dativ; Spanish flagged for Pablo on the de+el contraction). The
bare EXIT captures the thing left before the move and points noun at it
so the report can name it. NOT gated on any_enterable: that estimate is
kind-only and misses supporter/container set as a bare attribute or at
runtime, so gating it (my first cut) broke boarding those; the report
blocks are always compiled instead, ~156 bytes/game, all ceilings
raised with a dated note. 4 new tests + updated get-idioms/perform/
multifile assertions; suite 941.

## 2026-07-16: beyond points both ways, the player-beyond mount (arcc 0.15.2, Cosmos 0.41.0)

Charles: mounted on a horse, TAKE KEY on the ground should refuse with
"You can't reach that from the horse"; no place to hang a handler (room
moves with the mount, the horse is not consulted, per-object is absurd,
in_scope is a 1/0 predicate that cannot veto with a message). Stefan's
ruling: NOT a reach-seam hook and NOT a receiver -- the Arcturus way is
the beyond property pointing the other way. `now player is beyond` puts
the PLAYER out of everything's reach; only the arm's bubble stays
touchable: self, held, and the enclosure with everything it carries
(at_hand walks the parent chain past player or parent_of(player)).
Un-nested it collapses to self+held (hands bound, free). Sight and
speech cross as object-beyond already ruled; EXIT is never gated, so
dismount always works. Author surface: `on after enter mare / now
player is beyond`, mirror on after exit (the after phase, or the flag
blocks its own mount -- the before-phase trap is documented). The
refusal speaks player.beyond_why, runtime-settable per Stefan's spec:
`change player.beyond_why to "..."` wins, `to nothing` reverts to the
pack's msg_beyond; sema allocates the player's slot invisibly for any
game that writes it (a put_prop on a missing property HALTS the
Z-machine, so requiring a declaration first was a trap). The any_beyond
fold now also flips on a runtime `now ... is beyond` (sets_beyond scan)
so a game that declares beyond nowhere still compiles the guards. Bonus
fix both directions: PUT and INSERT move their noun without a hold
check and had no noun guard, so a beyond chandelier could ride into a
sack and a mounted player could fish the ground into the saddlebag;
both now carry beyond_guard + beyond_guard_second, folded as ever. No
pack work needed (msg_beyond reused; agnostic blocks in actions).
docs/01 beyond entry extended; beyond.storyarc gains the delivery-yard
vignette (cart seat, strongbox, horseshoe). Only the beyond example's
ceiling moved (+796 incl. the new scene), every other game untouched:
the fold proven. 8 new tests; suite 949. PARKED per Stefan: handlers
example + richer handler docs (after the upcoming handler bug), and the
enclosure receiver ("the more Arcturus way", own design round; note the
second-noun receiver already exists in dispatch and needs docs/02
verification).

## 2026-07-16: on after other joins the after band (arcc 0.15.3)

Charles Moore Jr.'s handler bug: `on after other` pasted next to `on
after go` fired DURING the main dispatch -- before the action's own
report ("AFTER OTHER" then "Got it."), on refused actions (south with
no exit), and never in the actual after pass. Root: the react-routine
builder grouped specific `on after <verb>` handlers under their
synthetic after numbers, but the catch-all collectors
(_other_handlers/_free_other_handlers) took ANY handler with "other" in
its events without checking h.after, so `on after other` rode the PLAIN
catch-all list, main band. Fixed as the mirror it should be: the plain
`on other` answers only the main band, `on after other` is the after
band's own catch-all (afloor <= action < meta_floor) inside the react
routines; after_map gains a fallback so any world action WITHOUT a
specific after takes the synthetic after:other (metas excluded -- the
main loop's after site is not meta-gated and relies on the map
returning 0). Shadowing mirrors the main pass: a specific `on after go`
silences the catch-all for go; refusals silence everything (the
existing refused gate). Codegen only, no Cosmos changes; games without
`on after other` are byte-identical (no ceilings moved). docs/01
handler section and docs/02 s.9 step 6 rewritten (docs previously said
`on other` never answers the after pass, which implied the after
catch-all did not exist; now it does, properly). 7 new tests; suite
956. NEXT per Stefan: the dedicated handlers example + richer handler
docs now unblocked.

## 2026-07-16: handlers presented as the heart, not a byproduct

Stefan's directive after the after-other fix: handlers are Arcturus's
real strength (the general feedback) and were documented too thin, with
no dedicated example. Two deliverables. (1) docs/01 section 12 rebuilt
around the mental model: a new opening that leads with the DISPATCH
CHAIN (noun -> second/recipient -> room -> free rules -> library
default, continue as the thread) instead of diving into header syntax;
a new "The second object answers too" subsection finally documenting
the recipient dispatch in the language reference (it existed since the
recipient work and was only in docs/02 s.9); a free-standing-rules
paragraph (the game-wide layer, scene rules via when, overriding
library defaults). (2) examples/features/handlers.storyarc, "The
Clockmaker": a fresh two-room scene exercising every form in one
playthrough - kind default, instance override with continue (the chain
made audible: both listen lines print), when-guarded take and go with
proper `change refused to 1` (the example itself first forgot it and
on after take spoke over the refusal - kept as a teaching comment),
object on-other, room on-after-other (the freshly fixed catch-all,
watching over spectacles), recipient on give coin, specific on after
take shadowing the catch-all, a free on sing, and the on enter arrival
event. Verified end to end on the VM; in the size gate (16536). Suite
957. No compiler or Cosmos change, no version bump.

## 2026-07-16: the run-time property read documented (here.(way))

Charles Moore Jr.'s documentation request: he lost time discovering
that `here.way` does not work while `here.(way)` does, for the common
"which room lies that way" test. He was right that it was undocumented:
the form appeared exactly once in docs/01, inside a block example,
never explained. Now docs/01 section 9 teaches it next to the plain dot
read: the dot's name is fixed at compile time, the parenthesized form
evaluates an expression and reads the property it names, and the reason
`here.way` fails is part of the lesson (it would look up a property
literally named "way"; the error says "cannot read property 'way' as a
value"). The recipe also points at the TOTAL form, exit_dest(here,
way), which runs a computed exit's block when one stands there and
folds to the plain read otherwise -- previously only in docs/04, now
author-facing in 01 s.9 and 02 s.11a, with a pointer from the handler
section where `way` is introduced. Verified both claims compile-side
and play-side before writing them. Docs only; no version bump.

## 2026-07-16: the self-perform loop, named at compile time (arcc 0.15.4)

Charles Moore Jr.: perform("burn", noun, second) "just dies with a
command prompt". Two-noun perform itself is fine (tested; his earlier
alter-clobber was the last real perform bug). The reproduction: his
`on burn` CALLS perform("burn", ...) expecting the library default, the
Inform <<burn>> mental model -- but perform is by design the FULL
pipeline, this handler included, so the unguarded self-perform
dispatches back into itself forever (3M steps in the VM harness; a real
interpreter hangs or dies to the prompt, his symptom). The Arcturus
word for "my checks ran, now do the normal thing" is `continue`. Added
_lint_self_perform: a compile note on the unguarded shape (no when, no
operand pattern) naming the cure; a `when` guard or pattern exempts it,
since the re-entry can fail those (the legitimate re-dispatch), and an
`on after <verb>` performing its own verb notes too (its after pass
re-enters the same way). Cross-action performs (unlock's open, climb's
enter) stay silent. docs/01's perform section names the trap with the
continue recipe. 4 new tests; suite 961.

## 2026-07-16: directions in matrices ride free; switch takes any value (arcc 0.15.5)

Charles Moore Jr., building maze routes and NPC patrols: thought
directions could not go into a matrix, then hit "@get_child called with
object 0" iterating one. Three findings. (1) Directions in matrices
ALREADY WORK (a direction is its property number, an ordinary cell):
append north to route, compare with `if d is north`. Documented now.
(2) The real crash: `for each d in m` where m is a BLOCK PARAMETER falls
through to object-tree iteration (a local cannot be told from an object
at compile time, same documented named-in-place rule catalogs carry) --
the matrix docs did not restate it. Documented, with the recipe:
calculate/entry/last/dice all work on a parameter (the shared header
makes the runtime-offset paths correct), so a helper walks by index.
(3) Fixed for real: switch cases accepted only literal numbers and
strings; now a case is any compile-time value -- a direction, an object,
a declared constant -- folding through the leaf read, so `switch d /
case north` reads like `if d is north` (the maze shape); a variable
case stays an error with a clear message. docs/01 switch + matrix
sections updated. 3 new tests; suite 964.

## 2026-07-16: vary, prose that varies by itself (arcc 0.16.0)

Charles Moore Jr.'s "would die for" feature: Dialog's (select) / I7's
[one of], the per-site text variation both systems count among their
best design. Stefan's rulings: keyword `vary`; policies renamed to his
scheme -- `sequence` (advance once, stick on the last), `loop`
(round-robin), `mutate` (random, never twice running), `dice` (the
honest roll, the catalogs' word for real random); text-first with
statements allowed; the A+B surface (each bare string line is its OWN
variant, an implicit say -- the catalog-taught form -- and an `or` line
at the vary's level opens a statement-group variant; the two mix, and
mixing WITHIN a segment errors with the cure named). It is a statement,
and all dynamic prose in Arcturus flows through statement contexts, so
it plugs in anywhere text is made: desc/appearance/intro blocks, any
handler, alter report bodies, each_turn, msg overrides, reply bodies --
the documentation carries all of these as worked context examples
(Stefan: solid gold, save them). Implementation: parser (contextual
head, claimed only before a policy word; a block named vary still
calls); sema stamps each stateful site a slot; the state words close
the catalog region (one word per site, dice keeps none), so save/undo/
restart correctness is free; lowering per policy is a loadw/storew plus
the switch je-chain, native z-ops, no library -- the efficiency answer
to the I7/Dialog bloat concern, and a game that never varies is
byte-identical automatically (no fold even needed; ceilings untouched).
mutate avoids immediate repeats by shifting one place on a re-roll
collision (uniform over the others, branch-cheap). docs/01 section 16
(the vary subsection with the context examples), Appendix A, README
What's new, VSCode highlighting. 10 new tests; suite 974.

## 2026-07-16: the 1.x era (arcc 1.0.0, Cosmos 1.0.0, VSIX 1.0.0)

Stefan's ruling with the vary announcement: the language has matured
into 1.x. arcc 0.16.0 -> 1.0.0, Cosmos 0.41.0 -> 1.0.0; the VSCode
extension, stuck at 0.13.4 through every language addition, rebuilt as
arcturus-1.0.0.vsix (manifest + package bumped, the current grammar
with vary/matrix/sequence/mutate/loop inside). README reshaped for the
era: the wiki promise removed (the docs ARE the documentation); the
intro now states the positioning plainly -- highly optimized Z-code for
classic 8-bit hardware WITH the advanced features Inform 6 and ZIL
never had (self-varying prose, computed exits, container knowledge,
kinds without a practical ceiling), possible because the compiler is
multi-pass with whole-program folding and strict DCE; standard-
compliant images in z5/z8 with the honest trick explained (ignored
extension opcode + capability flag only picture-aware interpreters
raise); Actaea plays v5/v8 with images today and retro arc_image
interpreters are in the making; the language-agnostic parser with
ejectable language granules. What's new trimmed to the agreed five
(catalogs and SWIM/TRANSCRIPT retired; kinds, matrices, vary,
arc_image-retro, perform+appearance stay). Suite 974 at 1.0.0.

## 2026-07-17: put and insert honor alter, the receiver's report speaks (Cosmos 1.0.1)

Charles Moore Jr.: "any_alter() doesn't seem to be reaching a SECOND
I've added an alter block to." Root: PUT and INSERT were the only
success paths in the library whose report sites lacked the alter dance
-- three bare msg_done sites (put-on-supporter, put-in-container,
insert-in-container). A receiver's handler (on put noun in self, the
second-noun dispatch) registered its report and continued; the default
put succeeded and spoke msg_done over it. All three sites now carry
`if any_alter is 1 / if altered is 0 / msg_done / else run_alter`,
folded behind any_alter as everywhere: games without alter are
byte-identical (only the alter example's ceiling moved, +40, dated).
2 new tests (receiver container, supporter); suite 977.

## 2026-07-17: ZX0W, the one-page-ring codec (arcimg 1.11.0; proposal 8b)

Shawn Sijnstra's field problem, and our own design debt in one: LZ
decoders copy from previously decompressed OUTPUT, which fails where
video memory cannot be read back (TRS-80 Model 4's port-addressed
board, Agon's serial VDP), and our existing probes dodge it by staging
-- compressed source AND the full 7680-byte band both in RAM, which a
64K machine running the interpreter cannot afford (Stefan's deeper
point). Implemented: codec 3 ZX0W -- a standard ZX0 bitstream whose
match offsets are CAPPED at 256 by the packer (zx0_compress gained an
offset_cap; zx0w selectable as --codec zx0w). The codec id is the
contract that one page-aligned ring in main RAM suffices: emits go
straight to the screen through a per-row address mapper (port, serial,
or interleaved alike) and back-references read the ring; the staging
band disappears on every machine, decode footprint = source + 256
bytes + decoder. Corpus-measured: 104.6% of full-window ZX0 on the C64
sections (1bpp, the TRS-80 shape), 121.9% on the 4bpp CPC sections;
RLE is 127%/171.5%. Tests: a ring decoder limited to 256 readable
bytes (a faithful port of our dzx0) round-trips zx0w output and
REFUSES plain zx0 (the counter-proof); codec registered end to end.
Design record 8b written as a proposal pending Stefan's ruling on
per-target mandates (TRS-80/Agon chapters; whether 64K profiles of
existing targets retire their staging bands). Suite 980.

## 2026-07-17: the window guarantee ruled, codec 3 retired (arcimg 1.12.0, R5)

Stefan's ruling after the curve measurement: W=2048 is FREE (byte-
identical per-picture averages vs the old 2176 quick window on C64,
CPC, and ZX3; 1024 would cost CPC 3.5%, 512 costs 17.7%). So codec 1
itself now carries the guarantee: arcimg packs every ZX0 stream with
offsets capped at 2048 (_ZX0_MAX_OFFSET), and codec 3 ("ZX0W", 256) is
retired unreleased; ratio is the budget that matters and the ring idea
lives better as a guarantee on the one codec. docs/08 part B rewritten:
the window contract plus the TWO decode memory models (staging for the
RAM-rich, ring for 64K profiles and write-only video: 2K ring + per-
byte emit straight to the native screen, streamed source, no staging
band). Design record 8b is the R5 ruling with an honest status: the
probe rebuilds (CPC first) and the reference ring decoders are the
open work; a first Z80 ring decoder draft was pulled unshipped when
review found the end-marker and reservoir bugs a naive re-plumb of
dzx0 invites, so the correct decoders land WITH the probes, emulator-
verified (Stefan's pass). Tests rewritten around the guarantee: packed
streams fit a 2K ring (instrumented ring decoder), an uncapped stream
provably does not, container round-trip. Suite 979.

## 2026-07-17 (evening): the CPC ring probe, dzx0r machine-verified (R5 build 1)

The first ring-architecture probe is built. dzx0r_z80.asm (~110 bytes)
is the ring decoder: the smallest possible delta on dzx0_standard (only
the two LDIR copy paths re-plumbed into ring+emit byte loops; the Elias
gamma reader, negative-offset bookkeeping, and end-marker detection
carried verbatim, because the pulled first draft proved those are what
a rewrite gets wrong). It is EXECUTED, not reviewed: tests/test_dzx0r.py
assembles it with sjasmplus (skipped if absent) and runs it on a strict
mini-Z80 core (exactly the decoder's opcode set, raises on anything
else) against real CPC/C64/ZX3 corpus sections and the synthetic edges
(offset exactly 2048, overlapping runs, long literals, tiny inputs),
byte-identical to zx0_decompress throughout. The CPC probe is rebuilt
on it: staging band deleted, emit vectored per section (screen
sub-block walker with the rows*10 block hop; 17-byte buffers for
palette/registers), ring 2K-aligned and asserted at assembly;
probe.bin + probe.sna regenerated. The committed codec-1 corpus was
repacked under the 2048 guarantee (39 of 84 files changed; C64/CPC/ZX3
/A8) and a corpus-contract test ring-decodes every committed file
forever after. docs/08: part B points at dzx0r as the ring reference,
C.6 is the ring loader chapter (64K posture: ring + 17 bytes, source
streamable). Suite 984. Pending: Stefan's ZEsarUX pass (ZRCP route),
then ZX3, then C64 + the 6502 ring decoder.

## 2026-07-17 (night): CPC ring probe VERIFIED on ZEsarUX, byte-exact (R5)

Live verification, and a near-miss caught by Stefan's question. The
first ZEsarUX run showed a handful of corrupt bytes in late screen
blocks; the deterministic reproduction (the mini-Z80 now runs the WHOLE
probe end to end with stubbed I/O and a scripted keypress) confirmed it
was not the decoder: the probe's embedded test images live in
arc_image/probes/ and had MISSED the corpus repack ("did you recreate
the corpus or is this still using the old image?" - exactly that). They
still carried 2176-era offsets (2096, 2172: precisely the forbidden
gap) which alias in a 2048 ring. Probe assets repacked (+3 bytes each),
probe reassembled, and verified byte-exact: ZEsarUX CPC 464, ZRCP
injection, frozen screen blocks and palette buffer read back and
compared against the expected decodes; PIXEL-EXACT for both images
(mode 9 and mode 12, keypress cycling confirmed live). The contract
test now covers arc_image/probes/ so probe assets can never drift from
the guarantee again. docs/08 C.6 verification note updated; design 8b
records the lesson: the window guarantee is only as good as its
enforcement surface. Suite 984.

## 2026-07-17 (later): current-pipeline assets, the Mac is the conversion home

Stefan caught the deeper staleness: the probe assets were not just
2176-packed, they were OLD CONVERSIONS from a retired pipeline; the
byte-exact loader proof said nothing about conversion currency, so an
eyeball pass would have judged outdated art. Root cause chased to the
environment: Pillow existed on the Mac historically but vanished when
Homebrew moved python3 from 3.13 to 3.14 (site-packages do not
migrate), which also explains the leftover python@3.13. Fixed: Pillow
12.3.0 installed for 3.14 (user site), python@3.13 removed (zero
dependents), and, checked at Stefan's request: Pillow was NEVER
installed on the orb Debian machine; FictionTools' environment is
clean (the instruction held). The beach pair was regenerated natively
on the Mac with arcimg 1.12.0: the fresh mode-12 render is
PIXEL-IDENTICAL to the approved previews/stress/beach-CPC.png ground
truth; the fresh mode-9 differs in composition from the old band9
preview (today's prep shows more scene, the old crop more sky),
Stefan's aesthetic gate at the emulator. CPC + ZX3 + C64 probe pairs
all regenerated; CPC and ZX3 probes reassembled (C64's needs acme,
absent here; flagged for its wave, its .prg still embeds old art).
Live: ZEsarUX CPC 464, fresh probe injected, byte-exact again
(PIXEL-EXACT bitmap + palette), left running for Stefan's eyes.

## 2026-07-17 (night II): the ZX3 ring probe, verified byte-exact (R5)

The second ring probe, and the pattern is now routine: the ULA's
third/line/char-row interleave is exactly a ring loader's shape
(linear rmax*32 runs, a $100 page hop per line-in-char, an $800 hop
per third; attributes straight to $5800 through the buffer emit). The
3072-byte staging buffer is gone; decode working set = the 2K ring.
The full-probe simulation (mini-Z80, scripted keypress, ULA oracle in
Python) was PIXEL-EXACT first try; the live pass on ZEsarUX (+3 ROM
4.1, machine-exact ZRCP injection) byte-exact for both images, bitmap
and attribute file, mode 9 and mode 12. docs/08 C.5 rewritten as the
ring chapter (verification note, sections, MEMORY: 2K ring, source
streamable) plus the change-log entry; design 8b updated. Suite 984.
Next: C64 with the 6502 ring decoder (acme via the orb Debian).

## 2026-07-17 (night III): the band modes are lines, prep crops from the top (arcimg 1.12.1)

Stefan's eyeball on the +3 caught it: the two band shapes read as
different pictures. Root: prep's _crop_to_ratio centre-anchored its
height trim, so a mode-9 prep of the 320x96 master dropped 12 rows top
AND bottom, recomposing the image. The doctrine, now ruled and coded:
band modes think in interpreter lines; mode 9 of a mode-12 master is
the SAME image ending at 72 rows, a top-anchored identity crop (width
trims stay centred; rescale only for foreign-shaped sources). The
proof of the circle: the regenerated 90 renders are pixel-identical to
the ORIGINAL approved band9-ZX3 and band9-CPC previews, so every probe
asset is once again exactly a corpus-gate image. All three probe pairs
regenerated; CPC + ZX3 reassembled and re-verified (sims pixel-exact,
+3 live byte-exact both modes); C64 probe.prg rebuilt via Debian acme.
Also opened: the ZX3 solver re-gate (the +3 art IS the approved art,
but the Spectrum kept its R3 solver when the Polizei family was
rebuilt; rework pending Stefan's call). Regression test on the crop;
suite 985.

## 2026-07-17 (night IV): the test pair is 9 and 12; Spectrum parked for Plus/4

Stefan's rulings. The standard test assets are named for the band
modes they carry: 9.<TAG> (infocom, 72 rows) and 12.<TAG> (DAAD, 96
rows), header ids matching; the undocumented 90/100 block convention
is retired. Regenerated for all seven targets and EVERY probe rebuilt
with the renamed assets: CPC + ZX3 (sjasmplus, sims pixel-exact
unchanged), C64 (acme on the Debian, its intended home), DOS (nasm),
AST (Eris's vasm), AMI (build_adf via the same vasm); stress-out
refreshed (A8 derived from the fresh C64 pair; medieval keeps 101
pending a naming ruling). docs/08 renamed throughout with a change-log
entry. And the Spectrum direction is settled as a ruling: the ZX3
SOLVER rework is parked until Plus/4 lands as a target, Plus/4 goes
HIRES (Stefan confirmed the historical Rabenstein Spectrum art was
100% based on the Plus/4 versions: near-mono dithered form, few
deliberate accents, dark/bright pairs of one colour for highlights),
C64 stays 160-wide multicolor (a hires experiment noted as an itch),
and looks are PREDEFINED per machine, never an author option (the
Rick Rubin principle). Suite 985.

## 2026-07-17 (night V): the C64 ring probe, the 8-bit cell trio complete

The third and last ring probe of the trio. dzx0r_6502.asm is a clean
transcription of the reference state machine (~230 bytes), NOT a
bitfire re-plumb (bitfire's self-modifying speed structure is welded
to a readable linear destination); machine-verified like its Z80 twin:
tests/test_dzx0r6502.py assembles it via the Debian acme (skips when
orb is unreachable) and executes it on a strict mini-6502 against
corpus sections and the edges; all four tests passed FIRST RUN. The
probe's one emit is a linear store, since every C64 section is
contiguous native memory. Two lessons banked in docs/08 C.4 and the
design record: the LAYOUT RULE (the bitmap decodes into $2000-$3FFF,
so the embedded images park at $4000; the first build let the bitmap
overwrite its own yet-undecoded color stream, caught by the full-probe
simulation), and VICE's autostart RUN keystrokes lingering in the
KERNAL buffer (clear $C6). Verified: the full-probe sim byte-exact on
bitmap+matrix+colram+background for both images; live on VICE x64sc
with matrix and color RAM byte-exact over the remote monitor and both
images approved on screen by Stefan. docs/08 C.4 is the ring chapter
(codec, layout rule, MEMORY: 2K ring, source streamable) with its
change-log entry. Suite 989. The ring family: CPC, ZX3, C64, done.

## 2026-07-17 (night VI): TRSM4, the fifteenth target (arcimg 1.13.0)

Shawn Sijnstra's request, Stefan's rulings: tag TRSM4, target id 15,
and the target is FIRST-CLASS arc_image even though its interpreter
lives outside the family (do not conflate the two; the target,
blueprints, and assets are ours, the Model 4 engine is Shawn's).
Geometry: the 320-wide master doubles horizontally to 640x72/96
because the hi-res board's 640x240 pixels are half as wide as tall,
so the doubling restores aspect AND doubles the dither grid, the
whole quality budget of a monochrome target. Conversion: luminance,
percentile-anchored contrast stretch (the difference between gray
mush and a blazing sun on the beach test), Bayer at the full 640
grid. One bitmap section, 80 bytes/row, bit 7 leftmost (Shawn's
spec), ring-decoded; on this machine the ring is the ONLY model
(port-addressed memory, no read-back). docs/08 chapter C.7; ledger
row; full corpus (21) + stress pair converted; contract test covers
arc_image/trsm4. Suite 992.

## 2026-07-17 (night VII): the TRSM4 probe, whole-way (no half measures)

Stefan's challenge stood: the doctrine is PROVEN blueprint, external
interpreter or not. The fifteenth target got its probe: a /CMD load
module for LS-DOS 6 (build_cmd.py), dzx0r_z80.asm carried UNCHANGED
with the emit as a port write plus a column counter and row
re-address; the first target where the ring model is the ONLY model
(port-addressed board, no read-back), which is fitting, since this is
the machine the whole architecture was built for. trs80gp 2.5.7
installed (launch: trs80gp -m4 -gt -vs probe.cmd; the bare launch
defaults to Model 3 with CRT blur). The port 131 option byte is
undocumented in the emulator manual, so it ships as the one CTRL
equate (graphics on + X auto-inc on write), Shawn asked to confirm.
Verified per the agreed division: the full-probe simulation with a
port model of the board (Shawn's spec) shows both images BYTE-EXACT
in modeled graphics RAM with the below-band area clean; the screen
itself is Stefan's eyes. docs/08 C.7 carries the probe section.

## 2026-07-17 (night VIII): TRSM4 probe calibrated on trs80gp, one open question

Stefan's eyes caught the first build's shear; the deep-test authority
passed to the harness (his ruling: sim + his eyes, screenshots only
when he spots errors). The option register was calibrated by VRAM
readback (-ig): bit7 = write-clock axis (the shear was Y-stepping),
bit2/bit3 = X/Y direction, bit6 = addressing-mode switch, 4-5 inert;
CTRL=$83. Result: image 12 BYTE-EXACT in the emulator's VRAM on every
run; image 9 byte-exact except EXACTLY ONE dropped write (row 0 col
14), boot-phase-locked, surviving DI, real speed, input-auto-turbo
off, and every option bit; the CMD loader cleared by round-trip
parse. The verdict needs hardware truth (does the real board hold
/WAIT in the video fetch window?): asked of Shawn, documented in C.7
and the design record rather than guessed. The probe ships.

## 2026-07-17 (night IX): direction catalogs; the matrix count documented (arcc 1.1.0)

Charles Moore Jr.'s pair. (1) A catalog now holds DIRECTIONS: each
entry is the direction's property number, the matrix precedent (a
fixed maze route or patrol path beside the matrix's mutable one);
`for each d in route / switch d / case north` and `entry`-comparisons
work unchanged, story names win over direction names as everywhere,
mixing objects and directions is refused, and the unknown-name error
now says "not an object or a direction". Direction properties are
standard pack properties, numbered whether or not any room declares
that exit, so the encoding is total. Zero cost to games without one
(sema classification + a cell-writer branch; every ceiling
unchanged). (2) The matrix count semantics are documented in docs/01
4a after his report: change entry rewrites but never grows; entries
live up to the count; append, a declaration seed, or load create
them. Verified the behavior first: the write lands in the
pre-allocated cell, the count stays 0, so count-driven reads see an
empty matrix. 4 new catalog tests; suite 1001.

## 2026-07-17 (night X): the instance catch-all beats kind specifics (arcc 1.1.1)

Charles Moore Jr.'s snippet cracked the "kind beats thing" mystery: his
instance handler was `on other`, the catch-all, and the kind's specific
verb pierced it. BOTH documents already mandated the opposite (docs/01
s12: the object's default runs before the action climbs to the kind;
docs/02 s9: own `on other` above the kind chain, each level's specific
before that level's other), so this was a pure code bug under the
charter rule that the document wins. The react dispatcher is now
OWNER-BANDED: band 0 = the object's own handlers with its own catch-all
at the band's tail, then each kind's band the same way, nearest first;
within a band the old rules hold exactly (specifics first, consumed
ends, continued falls onward, a band that addressed the action skips
its own catch-all), and the afloor/mfloor after-band logic holds per
band. Life-cycle events stay a single merged fire-all step. Emission
kept the old byte shape for single-band objects: only the two
kind-handler examples moved (+8, +12; dated), every other ceiling
byte-identical. 2 new tests (the exact field shape; catch-all continue
falls to the kind); suite 1003 with the whole precedence matrix green.

## 2026-07-18: directions say their words (arcc 1.2.0)

Charles Moore Jr.'s encore after direction catalogs landed: he could
store directions but not print their names. The answer was symmetry
already in the language: an object entry says its NAME, so a direction
entry now says its WORD, the same voice as `say way`, through the
cosmos_dir_name backing routine that already existed (emitted only
when referenced: unaffected games byte-identical, every ceiling
unchanged). `say "${entry(route, 1)}"` speaks north; the for-each loop
variable speaks it too. And the matrix joins fully: `matrix patrol
capacity 4 of direction` is the mutable route, seeds and appends by
direction name, cells validated ("'wibble' is not a direction"), say
speaking the word, the catalog symmetry complete on both the static
and mutable sides. docs/01 updated (including retracting the
hours-old "compare it, do not say it" note). 3 new tests; suite 1006.

## 2026-07-18 (later): globals alias matrices truly; the let error teaches (arcc 1.2.1)

Charles Moore Jr.'s pair. (1) A REAL BUG: a catalog or matrix name in
a global initializer fell through the seeding SILENTLY, the global
stayed 0, and 0 aliased the region's FIRST occupant, so with two
matrices the wrong one answered (his exact "entry(A,1) does not equal
entry(B,1)"). Global initializers now resolve catalog and matrix
names to their region word offsets (the same value the name means in
any expression) and direction names to their property numbers. (2)
`let` is block-scoped by design: a let inside an if branch ends with
the branch, which is correct and stays; what changed is the error,
which now teaches the shape ("declare it before the block, change it
inside the branches") when the unknown name was an expired let, and
docs/01 states the scoping beside let itself. 2 new tests; suite 1008.

## 2026-07-18 (later II): bare directions speak; the bar rises before start
   (arcc 1.3.0, Cosmos 1.1.0)

Charles Moore Jr.'s late-night pair. (1) `say north` and say
"${north}" as BARE literals now speak the word (his on-start case):
the same cosmos_dir_name voice, resolved last so story names win,
mirroring _leaf_operand exactly. His other likely case documented in
the reply: a plain matrix stays numeric; `of direction` types it. (2)
The statusline start overlap was real: the bar split at the FIRST
PROMPT, so any `on start` text landed on row 1 and the split painted
over it. The fix grew a language feature: blocks may have EMPTY
bodies (seams), and a statement-call to a block whose final body is
empty emits NOTHING, making seams free. The loop gained
`screen_ready` (empty seam, called before ev_start); the statusline
granule claims it with draw_status, so its window is up before the
first word. The old protective new_line before the banner then became
a visible blank and was REMOVED outright: `say` already leaves a
pending paragraph break, so start text separates from the banner
automatically and a silent start puts the title directly under the
bar (the sugar layout test agrees). Statusline games pay +12 for the
early bar; everyone else is byte-identical (the fold at work), and
all ceilings were retightened to actuals. Suite 1008.

## 2026-07-18 (later III): the cave rule (Cosmos 1.2.0)

Charles Moore Jr. noticed examine and read lacked light checks; Stefan
researched the field convention (Inform 6/7, PunyInform, Dialog all
agree) and ruled the Inform 7 way: INVENTORY works in darkness (you
can feel what you carry well enough to count it), EXAMINE refuses
without light, and READ follows examine for free since the verb maps
onto it. One guard in the examine default (is_lit, the existing scope
block; msg_too_dark, the existing message in all three language
packs). Author flexibility needs no new option: stricter darkness is
one free rule, `on inventory when is_lit is 0`, documented in docs/02
section 6 with Stefan's own wording as the example, and pinned in the
tests. Every game pays a few bytes for the guard (ceilings
retightened, dated); 4 new tests; suite 1012.

## 2026-07-18 (later IV): direction matrix seeds compile (arcc 1.3.1)

Charles Moore Jr.'s report, and Stefan called the category in advance:
an incomplete implementation surfacing as the next field report. The
matrix SEED writer never learned the direction cell kind (the catalog
writer did, the say paths did, sema's validation did): a seeded
`matrix ... of direction` fell into the number branch, which did
.value on a Name and crashed raw with no line number. One branch added
(a direction seed is its property number, as everywhere); his full
scenario (seed, dice from a direction catalog, change entry, for-each
speaking the words) is the regression test. A raw Python traceback
from arcc is always our bug, never the author's. Suite 1013.

## 2026-07-18 (later V): clear containers reveal nothing on open (Cosmos 1.2.1)

Charles Moore Jr.: opening a CLEAR container fired "Inside you find",
announcing contents that were never hidden (the knowledge model lists
through the glass, docs/02 5a). One language-agnostic guard at the
call site (`if noun is not clear`), so all three language packs are
fixed at once; opaque containers keep the reveal. Regression test
covers both kinds; ceilings retightened (one attribute test on the
open path). Suite 1014.

## 2026-07-18: the rulings-and-documents day (the entries that nearly slipped)

A batch of decisions and document work that PROGRESS missed while the
feature entries were being written; consolidated here, Stefan's catch.

- THE TRSM4 /WAIT QUESTION, ANSWERED (via Shawn and trs80gp's author):
  real Tandy boards never drop writes, they insert wait states, so
  interpreters need NO pacing; the single dropped byte in verification
  is a trs80gp 2.5.7 emulation bug, reported upstream with a
  byte-exact repro. RULED: the probe stays PURE, no workaround (an
  interpreter decodes at arbitrary moments, so the boot-phase-locked
  flaw is emulator-only); a provenance note sits in the probe source.
  Stefan's visual verdict: "it looks brilliant"; TRSM4 fully closed.
- THE DARKNESS SECTION IN STEFAN'S OWN WORDING (docs/02): addresses
  readers from Inform 6/PunyInform/Dialog directly, explains the cave
  rule before naming it, names Inform 7 as the analog. The comparative
  claims were VERIFIED from the Dialog standard library source: Dialog
  checks light for READ but not for EXAMINE (its own comment confirms
  look-relations are its only visibility refusal), so only Inform 7
  matches our behavior, and ours is the more coherent since read maps
  onto examine.
- READABILITY RULINGS: author-facing docs and examples compare flags
  with `is true` / `is false` (perform results, append/remove
  results); genuine numbers (counts) stay numeric; Cosmos internals
  keep bare numbers by explicit ruling.
- WHATSNEW.md BECAME "WHAT'S NEW + FEATURE ROADMAP": five refreshed
  entries (darkness, directions as values, the hardened dispatch
  chain, the ring architecture, TRSM4) and nine ruled roadmap items
  (inference, pathfinding with player travel and NPC movement as one
  engine's consumers, the NPC engine granule, light topology, darkness
  furniture, LOOK <direction>, the verbs overhaul with per-verb
  requirements / two-noun lists / DROP ALL / maybe CONSULT, question
  preservation with likelihood hints). Dropped by ruling: fungibles,
  NPC commanding, VERBOSE/BRIEF. Verified gap recorded: "put coin and
  nail in box" fails today; single-noun lists work.
- THE CLEAR/OPAQUE RULING, for the permanent record: Stefan's intended
  container design was INVERSE polarity (contents visible by default,
  authors declare `opaque` to hide, a deliberate departure from
  Inform/Dialog); an earlier session implemented `clear` with classic
  polarity without asking. RULED 2026-07-18: it STAYS as implemented,
  permanently, because five or six real adopters will not be made to
  rewrite every container. The word "opaque" in comments and docs is
  prose for the default state, not an attribute; no future work may
  rename or flip this. The container KNOWLEDGE model (seen-memory
  through closed boxes, listing through glass) remains the area's
  differentiator.
- A CLIENT DATA-LOSS INCIDENT cost Stefan half an hour of roadmap
  commentary (an accidental paste swallowed the input and the chat
  panel truncated at 50,000 characters before anything was persisted;
  full forensics done, nothing recoverable). His opening "I have a
  good idea" was never recovered; ask him. The roadmap verdicts were
  re-given in shorthand and are folded in above.

## 2026-07-18: CHECKPOINT before compaction

State: HEAD 28375fd, all committed, suite 1014 green. arcc 1.3.1,
Cosmos 1.2.1, Actaea 1.1.0, arcimg 1.13.0, VSIX 1.0.0. Amalgams and
README table current. WHATSNEW.md is "What's new + feature roadmap"
(5 fresh entries, 9 ruled roadmap items).

Next, in Stefan's ruled order:
1. THE INTFICTION ANNOUNCEMENT POST, co-written WITH Stefan (never
   draft-and-ship). Showcases set aside: the cave-rule inventory
   recipe (I7's rule as one handler header), read/examine darkness
   coherence (verified: Dialog checks light for READ but not EXAMINE;
   only I7 matches us), the public feature roadmap, 15 retro picture
   targets from one master. Only VERIFIED comparative claims; his
   voice; ask his shape (length, venue section, loudness) first.
   Stefan's lost message opened with "I have a good idea": the idea
   was never recovered from the truncation accident; ask him.
2. PLUS/4 WAVE (R4): hires TED bitmap, 320 wide; conversion philosophy
   ruled: near-monochrome dithered form, few colour accents,
   dark/bright pairs (the Rabenstein lineage). arcimg target P4 (id 5)
   is registered but has NO converter yet (_CONVERTERS lacks "P4").
   Probe: 6502, acme on the orb Debian (~/FictionTools/acme),
   dzx0r_6502 machine-verified, ring model, VICE xplus4 to verify.
   Plus/4 unblocks the ZX3 solver rework (parked) and the MSX1 base
   ruling (Stefan decides at MSX1 start).
3. Then MSX1 and A8 probes to close R4 (atari800/openMSX: ask Stefan
   before installing or launching any emulator).

Open externals: trs80gp dropped-write bug reported upstream via Shawn
(byte-exact repro delivered); TRSM4 complete, probe stays pure
(ruled). Expected Charles report: noun-AND-noun lists in two-noun
actions ("put coin and nail in box" fails; verified gap, roadmapped
under the verbs overhaul).

Parked: roadmap implementation (until the sea is calmer); the
enclosure receiver design discussion.

Environment: trs80gp wrapper at ~/.local/bin/trs80gp (a symlink breaks
its resource lookup; the wrapper execs the bundle binary); Pillow on
the Mac python 3.14 user site; sjasmplus ~/.local/bin; nasm brew; vasm
in Eris/tools/bin; acme on the orb Debian. Emulators: always ask
before new ones.

## 2026-07-18: locals carry the direction type (arcc 1.3.2)

Charles's follow-up on direction values: `let d = north` then
`say "${d}"` still printed the property number. The typed-say machinery
existed (for-each variables over a direction catalog already speak the
word); locals assigned by `let` and `change` did not feed it. Under
Stefan's standing support mandate this is a bug against the shipped
model ("directions are values everywhere", his approved wording), not a
design question: fixed by assignment dataflow on locals, in statement
order. Assigning a value with a known element type (a direction
literal, an entry/last/dice read from a typed catalog or matrix,
another typed local, `way`) tags the local so say speaks it in its own
voice; assigning a plain number or anything unknowable clears the tag.
Covers the `let d = 0` + `change d to entry(...)` shape our own
teaching error steers authors to. Text and object entries read into a
local gained the same voice for free. Games without typed locals stay
byte-identical (ceilings untouched). docs/01 updated in the same
commit; suite 1016.

## 2026-07-18: bold banner and location titles (arcc 1.3.3, Cosmos 1.2.2)

Stefan's polish ruling, from comparing his announcement screenshots
against Jigsaw running in Actaea: classic library output prints the
game's title and the location headers in bold, Cosmos did not, and on
a style-capable interpreter that reads as less polished. Ruled scope,
his words: the banner title and the location title, nothing else. The
banner title bolds in the compiler's banner emitter (both the Cosmos
path and the bare fallback); the location title bolds in
describe_room's two header paths, with the nested "(in the chair)"
suffix staying roman. set_text_style is v5 core and an interpreter
without styles must ignore it, so text-only output is unchanged
everywhere. Four style ops, +16 to +20 bytes per game; all 38 ceilings
raised with the dated note in the same commit. Suite 1017.

## 2026-07-18: the ambience deck, and the cadence calibrated (arcc 1.3.4, Cosmos 1.2.3)

Stefan caught both, from his own screenshot sessions of the B8 port.
First: a companion's random flavor events repeated, where his original
design (one central NPC logic over per-room message properties in the
Inform build) fires each event once per room visit, then goes quiet
until the player returns. The ambience granule had no such mode, and a
bare `once` on a random block even parsed and was silently dropped.
Discussed first, at his instruction; options weighed included building
on `vary` (rejected: vary has no such mode either, deliberately, since
a room description may never print nothing, and vary cannot own
cadence). RULED (Stefan): ambience is its own thing and gets the
sibling mode; `once` is the mode word; re-arm on re-entry, matching
his original; the five-deep cross-room history is not needed. Bare
`once` now deals the lines like a shuffled deck: each fires once in
random order, then silence; out of play re-deals. One word in the
header fixes all such blocks in the B8 port. Capped at 15 lines
(the fired-lines bitmask is one word; sema teaches the cure). The
whole deal path folds away behind any_ambience_once: every other
example is byte-identical, verified by the untouched ceilings.

Second: "about 7 turns" fired every 4. The breathing countdown from N
fires uniformly across 1..N, average (N+1)/2, half the promised rate.
RULED (Stefan): "if the author defines every 7 turns and it actually
fires every 4 turns then this is considered a bug." The countdown now
seeds at 2N-1, same breathing feel, true average N; measured 7.5 over
80 firings against the old 3.9.

Found along the way: a block call with four arguments compiles to
garbage (the assembler has no call_vn2, so the arity cap is three, and
nothing enforces it); noted for a compile-time arity check. docs/05
and the ambience showcase (a new boathouse room deals a once-deck)
updated in the same commit; the VSIX already highlights `once`, no
rebuild needed. Suite 1021.

## 2026-07-18: block calls up to seven arguments (arcc 1.3.5)

The follow-up to yesterday's find, on Stefan's explicit go after the
design question was settled in discussion: the three-argument cap on
block calls was an accident of implementation (the assembler lacked
the long-call pair), not a Z-machine limit, and it was unenforced, so
a fourth argument compiled to garbage silently. Now call_vs2 (the
instruction set's only double-types-byte encoding) carries four to
seven arguments; seven is the Z-machine's own ceiling and both sides
of it are enforced with teaching errors (a call with eight, a block
declaring eight). The long call is emitted only when a call actually
exceeds three arguments, so every existing game is byte-identical
(the untouched ceilings prove it). docs/01 states the ceiling. Suite
1024.

## 2026-07-18: the 15-locals doc discrepancy, ruled onto the roadmap

Flagged under the doc-wins rule: docs/01 claimed the compiler spills
excess locals to the stack, but the compiler actually refuses a block
over 15 locals with a teaching error (spill was deferred long ago).
RULED (Stefan): automatic local spill goes on the feature roadmap as a
later milestone, flagged in WHATSNEW.md; docs/01 now states what the
compiler really does and points at the roadmap. His note for the
record: 15 is a lot, but someone will hit it sooner or later.

## 2026-07-18: dir_name, the explicit speak (arcc 1.3.6)

Charles's follow-up: his shared helper read a route through a block
parameter, and there static typing genuinely ends (a parameter is just
a value; the compiler cannot know it holds a direction matrix, the
same boundary for-each has always had). Discussed the three options
with Stefan: a runtime speak function, parameter type annotations
(rejected: breaks "parameters are values and need no annotation"), or
ruling it a documented boundary. RULED (Stefan): the function, named
dir_name. `say "${dir_name(d)}"` speaks any direction value at
runtime through the same routine `say way` uses; it prints in place
and is refused as a value with a teaching error. Emitted only when
referenced. docs/01 documents the boundary and the ask. Suite 1026.

## 2026-07-18: the reversed dative takes pronouns (Cosmos 1.2.4)

Charles's report: GIVE COIN TO HIM worked, GIVE HIM COIN did not (and
GIVE HER COIN worse). Diagnosed against invented content: the reverse
probe scores only vocabulary words, so a typed pronoun never counted
as a noun phrase, the split never happened, and the whole-phrase
matcher's pronoun short-circuit then swallowed "him brooch" wholesale
(the pronoun's referent bound BOTH slots and the gift was dropped).
Fixed in the shared skeleton, one branch in probe_noun: a one-word
phrase that is a pronoun resolves to its remembered referent, so
English and German heal together; an unbound pronoun now faults
honestly ("say what you mean") instead of misbinding. The branch
ships wherever the reverse grammar does (all English games), so the
ceilings moved a few bytes each, noted. Suite 1027.

## 2026-07-19: clear_screen puts the furniture back (arcc 1.3.7)

Charles's report: with the status bar summoned, the first line of his
intro still hid under the bar. The screen_ready seam was working as
built (verified in order on dfrotz and fizmo), but his game, like the B8
game's own prelude, CLEARS the screen in `on start`, and erase_window -1
unsplits: the bar died with the split, the intro printed from row 1,
and the first prompt's bar redraw painted over it. Stefan pointed the
diagnosis at the intro shape. Fixed in the clear_screen lowering: after
the erase, the compiler re-runs the screen_ready seam, so whatever
granule owns the screen furniture puts it back before the next word
prints; emitted only when the seam has an owner, so a bar-less game is
byte-identical (asserted in the test). The B8 game rebuilt; suite 1029.

## 2026-07-19: --seed, the reproducible session (Actaea 1.2.0)

Charles asked whether Actaea can start with a fixed random seed. It
could not; discussed, and Stefan ruled: build it, and the seed stays
EXPLICIT everywhere (--check does not imply one). --seed N seeds the
generator at boot in every front end, and RESTART rewinds it with the
machine, so a session replays identically end to end. The real win is
the pairing with record/replay/check: a walkthrough of a game with
random flavor (dice, shuffled ambience) becomes deterministic, which
the check workflow could not promise before. docs/06 covers it beside
the record loop; suite 1031.

## 2026-07-19: search searches for real (Cosmos 1.2.5)

Charles's report: a lootable knocked-out guard took a hand-rolled
listing loop, near-verbatim the library's own reveal idiom, and (as
the diagnosis showed) his version even left the loot unreachable,
since scope never descends into a plain thing. Discussed at length at
Stefan's direction: helper vs default vs both, the alter integration
he called out as the point ("the author has no control over the
response" killed the helper-only shape), the blast radius (revised
down: only authors can seed contents into plain things, so every
yield is a staged cache), and the animate gate as the consciousness
model. RULED (Stefan): the default searches for real. Search tells
you what is there and makes findable what wasn't: living rebuffs,
sealed refuses, open containers and supporters list, and a plain
thing's cache lists, marks seen, and spills to the floor; alter
rewords while the mechanics run; the engine is public as
search_yields(self) for the compliant frisk of a still-animate
character. The granule's header finally matches its behavior (it had
promised listing since B5.5b and never did it). One ceiling moved
(the extended-verbs showcase); everything else untouched. Suite 1032.

## 2026-07-19: search_loot (Cosmos 1.2.6)

The engine's public name, Stefan's call before anything shipped to an
adopter: search_yields becomes search_loot, granule, tests, and docs
in one sweep.

## 2026-07-19: the touch interpreter, parked far out (Stefan's direction)

Recorded in docs/00 beyond the lettered milestones, deliberately
unscheduled: a second interpreter beside Actaea for touch and
point-and-click play of Z-machine games, on the Mac, any regular
computer, iPad, iPhone, and Android. In the design record rather than
the feature roadmap because it concerns the toolchain's future, not
the language; nothing about it starts until the current milestones
are long done.

## 2026-07-19: the touch interpreter rides web technology (Stefan's ruling)

The parked second interpreter gains its one settled decision: web
technology, the broader term ruled deliberately, not native apps. One
codebase for every screen, no store between the game and the player,
and the single self-contained file ethos carries over (interpreter,
story, and art bundled into one). The idea itself came as feedback
from the German IF forum; the scheduling stays far out.

## 2026-07-19: search leaves components alone (Cosmos 1.2.7)

Charles's follow-up exposed two things. His actual symptom (the
default still speaking the nothing-line over a stocked body) does not
reproduce on the current build, handler-continue shape and all: he is
running a pre-1.2.5 toolchain, and since arcc --update serves GitHub
main, the fix reaches him only once the day's commits are pushed. But
his `component` experiment caught a real bug in the new engine: a
component was listed as loot and yielded to the room, where it
answered "that's part of the Dock" on take. A component is an
attached part, not loot; search now neither lists nor moves one (the
search_lootable filter: not hidden, not component). Suite 1033.

## 2026-07-19: the self-perform note, narrowed (arcc 1.3.8)

Charles pushed back on the perform re-entry note: redirecting an
action onto another object is his everyday shape and the note nagged
it. Analyzed and presented; he was half right. An INSTANCE handler
re-performing its own action at an explicit different object can
never re-enter itself (it only runs when its own object is the one
acted on), so the note there was spurious; but the same code in a
kind, room, or free handler loops for real (those run for any noun),
which is the shape behind the original dead-at-the-prompt field
report, and a dynamic target is unprovable. RULED (Stefan): narrow
it, so it does not fire for him but keeps its purpose. The note now
exempts exactly the provably-safe shape and still speaks for the rest.
Suite 1035.

## 2026-07-19: SIT is standard, and it means enter (Cosmos 1.2.8)

Charles's request, Stefan's go ("he is right with this one"): SIT was
an extendedverbs stub while SIT ON X is everyday IF currency. Now
`sit`/`rest` live in the standard English set mapped straight onto
enter: SIT ON THE CHAIR boards it, SIT IN THE TUB climbs in (the
particle machinery swallows ON/IN the way GET ON always did), a bare
SIT asks for its noun, and a non-enterable refuses through enter's
ordinary path. The granule's stub and message retired. The byte pitch,
per the standing rule: +16 to +20 per game for two dictionary words
and a grammar row; extendedverbs games get 64 back from the retired
stub, ceilings moved both ways with the note. Suite 1036.

## 2026-07-19: STAND completes the pair (Cosmos 1.2.9)

Stefan's go on the flagged symmetry: STAND joins SIT in the standard
set, riding exit. Bare STAND and STAND UP leave the seat (the UP line
is its own grammar row with the literal word), STAND ON THE STOOL
boards it like SIT ON, and standing on solid ground gets exit's
ordinary "you aren't inside anything". The granule's stand stub and
message retired; ceilings moved both ways with the note. Suite 1037.

## 2026-07-19: STAND redone on the flag model (the doctrine catch)

The first STAND landed with literal-word grammar lines, which are
lossy for the flag model: the whole positional matcher tabled into
EVERY game (~700 bytes each), the exact breach the grammar-table
tests pin, and the suite said so while the commit went in anyway; the
ceilings were even raised over the failure. Caught on the next run
and redone properly: one flag-model line (`exit noun`; the noun slot
carries the particle form and lets STAND UP's direction ride `way`,
which exit ignores) plus exit+on in compound(), the same particle
door GET ON uses. Same player surface, byte cost back to the two
dictionary words and a grammar row. The lesson stands in the log:
the size gate is part of the done-test, not an after-the-fact chore.
Suite 1037, all green this time.

## 2026-07-19: Blorb, on the community's ask (arcimg 1.14.0, Actaea 1.3.0)

The announcement thread produced interpreter authors willing to
implement arc_image, Chris Spiegel (Bocfel) among them, on one
condition: Blorb as the resource container. Stefan ruled the shape:
`pack --blorb` writes a pictures-only .blorb, `pack --zblorb STORY`
writes the merged single file (the story as a parameter, arcimg's
first), `.arcres` stays the default, and, his condition in turn,
Actaea itself must read both, "that's the only way". Done end to end:
the Blorb writer in arcimg (IFF FORM/IFRS, RIdx first, picture id N =
Pict N with the master PNG bytes verbatim, the story as Exec 0 in a
ZCOD chunk), and Actaea opens a .zblorb as the story and serves its
pictures from it, resolves a sibling .blorb after .arcres, and the
GUI reads Pict resources beside the zip path. Blorb has no filenames
inside, resources ARE numbers, so the arc_image model maps with zero
translation; nothing about the opcode, the flag, the band, or the
dedup changes. Also ruled: master resolution is flexible at the band
aspect (40:9 / 10:3); 320 is the reference the retro conversions
derive from, not a ceiling, and Actaea's rational scaler already
handled it. docs/06, 07, and 08 updated together. Suite 1039.

## 2026-07-19: presentation latitude for modern interpreters (Stefan's ruling)

auraes (a French developer already rendering arc_image in his own z5
interpreter, pictures flowing INLINE with the transcript rather than
in a fixed band) surfaced a contract question: the interpreter book's
Part A pinned the band to the top of the screen, so his lovely
storybook-flow presentation was, as written, non-conformant. RULED
(Stefan): the fixed band is the contract only for fixed-screen
interpreters; presentation on modern systems is the interpreter
author's discretion. Part A point 3 rewritten to permit
transcript-flow and other modern presentations, holding only the
invariants (mode aspect, the picture tied to its moment, id 0
clears); the C.0 modern chapter's RENDERING note and the change log
match. Rationale for the log: presentation pluralism is what drew
three interpreters in a week; the same draw_image stream must be free
to drive a pinned band on an 8-bit and a flowing gallery in a browser.
Docs only, no code.

## 2026-07-19: infocom ask/tell scans the subject, not the listener (Cosmos 1.2.10)

Charles: the Infocom-style conversation was "badly broken", the first
topic's response no matter what he asked. Reproduced against invented
content: subject_typed scanned EVERY typed word, the NPC's own name
included, so a topic whose match-words overlapped the character's name
(a "tell me about yourself" topic with the name as a word, the common
case) fired for every ASK, and the first such topic always won. Fixed:
scan only the subject phrase, the words after the about/for separator
(is_separator, cross-language); the listener's name sits before it and
is no longer scanned. Chose the positional split over skipping the
person's whole vocabulary precisely so ASK JACK ABOUT JACK still
reaches the self topic (the second "jack" is the subject). +68 bytes
on the two games that summon the granule, ceilings noted. Suite 1042.

Charles's ORIGINAL question, the per-NPC fall-through default, is left
for Stefan: a game-wide custom default works today (redefine msg_ask,
most-specific-wins), but there is no clean PER-NPC default nor a
wildcard/fallback topic. That is a design question, not a bug, and
waits for a ruling (a fallback topic, a per-person default hook, or
"the global reskin is enough").

## 2026-07-20: the idle topic, a per-NPC conversation default (arcc 1.3.9, Cosmos 1.2.11)

Discussed with Stefan before building (his two awareness points settled
first: the subject-fix did not touch the menu, verified on Frotz; and a
default is meaningless in the menu, so it must be ask/tell-only). RULED:
NPCs need a per-person default answer; keyword `idle`; one idle serves
both ASK and TELL; it is an ordinary topic in every way but the match.
Built: `topic <id> "<label>" idle` marks the ask/tell fallback (no
words, matches on "nothing else did"); infocom_talking runs the first
visible idle topic when no worded topic matched, in place of the flat
msg_ask/msg_tell; `once` gives a one-time "that is all I know", `when`
a scene-dependent brush-off; several allowed, first in view wins. The
conversations menu ignores idle topics entirely (Stefan's point 2): a
new menu_visible seam skips them, so one declared in a menu game is
inert. Sema refuses `idle` + `words` (contradictory) with the cure. New
TOPIC_IDLE flag bit, cosmos_topic_idle helper, topic_idle intrinsic,
any_topic_idle compile-time fold. Pay-for-use: the idle machinery DCEs
away with no idle topic (ask/tell and non-conversation games
byte-identical, confirmed); menu games pay +20 for the menu_visible
seam, ceilings noted. docs/01, docs/05, the VSIX (idle keyword, 1.0.1)
all updated. Suite 1047.

## 2026-07-20: the ARCI declaration chunk, mandatory in Blorb (arcimg 1.14.1, Actaea 1.3.1)

Chris Spiegel (Bocfel) asked for the Blorb declaration chunk to be
MANDATORY rather than optional: with it optional, absence tells an
interpreter nothing and it must support arc_image speculatively for
every game; mandatory makes "does this game want a picture band" a
decidable question before a single instruction runs. I had advised
optional an hour earlier and revised: the scope is narrow (a Blorb
packaging rule, not a runtime one), arcimg is the only packer so it
always writes it, and the burden on authors is zero. RULED (Stefan):
mandatory, implement it.

Built: every Blorb arcimg writes carries `ARCI` (2 bytes: extension
version, band mode 9/12, or 0 when the art declares none). The chunk
sits between RIdx and the resources, so its size folds into the
absolute resource offsets, the one place a slip corrupts every pointer
silently; a test parses the Blorb back and asserts every RIdx offset
still lands on a real chunk header. Actaea reads it (blorb_arc_image).
Written into docs/08 with the part that matters most: ABSENCE IS
MEANINGFUL, a Blorb without the chunk promises no arc_image graphics,
and that is a guarantee interpreters may rely on. Part A and the bare
z5-plus-pack path are untouched, and the chunk is never a second source
of truth: the mode operand stays authoritative per call.

Also: THE RETURN TO RABENSTEIN, a second arc_image demo shipping four
scenes in a .blorb (the first ships an .arcres), so both containers
have a worked example and the Blorb path is exercised end to end in
Actaea. Suite 1049.

## 2026-07-20: the interpreter book overhauled (Stefan's review)

Stefan reviewed docs/08 as an outside implementer would read it and
called it complicated and inhuman in places. Overhauled on his list:
the opening rewritten in plain language (the design-record pointer
dropped as irrelevant to an implementer, and the modern path now
correctly says .arcres AND .blorb, not just the zip); the modes given
the explanation they deserved (mode 9 is Arthur mode, 9 rows and 72
pixels; mode 12 is DAAD mode, 12 rows and 96, with where the names come
from and why both land on whole text rows); the modern chapter retitled
".arcres and .blorb path"; and the stiff constructions he pointed at
("a hard promise of the format, not a hint", "verified behavior, not
aspiration", "produces the ground-truth PNG") rewritten as things a
person would say.

Also his ruling on dates: a spec is not a log. Every "Verified: <emulator>,
both modes, <date>" line is gone from the target chapters, along with the
dated rulings scattered through Part B and C; a machine simply has a
chapter once its reference loader works, and the rest are on the roadmap.
The whole 113-line change log went with them: it was project history in a
document handed to outside implementers, and it lives in PROGRESS and git
where it belongs. Kept, because they help an implementer rather than
narrating us: the ZEsarUX CPC snapshot caveat, and the TRS-80 write-pacing
answer (restated as advice instead of a dated Q&A). Nothing technical was
changed, only how it reads. docs/01 lost its "(a field report)" aside for
the same reason. Suite 1049.

## 2026-07-20: a word answers with one grain, and the compiler says so (arcc 1.3.10)

Forum report: two grain lines for the same word in one room, `examine
"junk"` then `touch "junk"`, with TOUCH falling through to the scenery
default. Reproduced: find_scenery returns the first grain whose owner is
in scope without consulting the action, so the examine grain answers
everything and the second line is dead.

Stefan's call, and he was right to push back on my first framing: that
form was never documented. The documented shape is one line carrying all
the verbs (`examine, touch "junk" say ...`), and the moment the answers
must differ per verb the author has described an object, not cheap
scenery, so a `scenery` thing with its own handlers is the tool. Grains
keep their shape; the parser's noun-resolution path stays untouched.

What was indefensible was the SILENCE, and that is fixed: a second grain
line for a word already claimed by the same owner now gets a compile
note naming both cures. Cross-room reuse (the documented case) stays
quiet, as does the one-line multi-verb form. docs/01 states the rule
where an author meets it. Suite 1052.

OPEN, for Stefan: there is no way to read the CURRENT action in author
code (action_id("take") gives the number, but nothing to compare it
against; `on other` has the same blind spot). He asked whether Arcturus
has Inform's `if (action == ##take)`. It does not. Proposal put to him,
not built.

## 2026-07-20: `action`, and the bare-name sugar (arcc 1.3.11, Cosmos 1.2.12)

Stefan's go, after the grains thread turned up the real gap. A forum
reader wanted per-verb answers from one grain and reached for an
undocumented second grain line; another offered `let act = resolve_verb`
inside the body, which works but reaches into an internal parser block
and is not something to spread as an idiom. Underneath both was a
genuine hole: author code had no way to read the action being
dispatched. `action_id("touch")` gave a number with nothing to compare
it against, and `on other` had the same blind spot, answering a dozen
verbs unable to name one.

Built: `action` reads the action the turn is running, and Stefan's
syntactic sugar compares it against a bare action name, `if action is
touch`, the same shape `way` has for directions. Resolved last, so a
story's own name still wins (an object called `touch` keeps the name).
The dispatcher is the one place every action passes, so one store there
serves handlers, grains, and any block they call, and it survives
command chaining because each chained command is its own dispatch.
Pay-for-use holds: any_action_read folds the store away when nothing
reads it, and Cloak of Darkness compiles byte-identical at 18032.

This is now the sanctioned answer for the case that started it: keep
the one grain line with all its verbs and branch on `action` inside.
docs/01 documents it in both places an author meets it, the grains
chapter and `on other`. Suite 1057.

## 2026-07-20: AGAIN replays a conversation topic (arcc 1.3.12, Cosmos 1.2.13)

Two reports from Charles, one bug and one that answered itself.

THE BUG: "ask NPC about topic" worked, and an immediate AGAIN gave the
flat default. Root cause: AGAIN replays a command by restoring its
RESOLVED operands (act, noun, second, way, grain) and re-dispatching,
but never the typed words, and a topic's subject lives in the words,
not in noun/second. So the replay scanned "again", found no subject,
and fell through. Fixed by treating the topic as the operand it is: the
granule remembers what a person last answered and repeats it on a
replay, with a new core `replaying` flag saying that the words must not
be trusted this turn. The memory clears whenever an exchange matches
nothing, so a stale topic can never be replayed, nor fired at a
different person. Guarded by a new any_topics fold, so a game without
conversation is byte-identical (Cloak unchanged at 18032); the five
conversation examples pay it.

ASK vs TELL: Charles is right that they are different encounters, and
Stefan's guess that TELL was a synonym for TALK was not the cause;
TELL is its own verb and action, but both route to the same topic body,
which is deliberate (a topic is one SUBJECT, and both verbs raise it).
No redesign needed, because yesterday's `action` already distinguishes
them from inside the body: `if action is tell`. Documented in docs/05
with the example. Suite 1060.

## 2026-07-20: shared conversation subjects (arcc 1.3.13, VSIX 1.0.2)

Charles's authoring complaint: several NPCs answer about the same thing,
and each needed its own topic with its own copy of the vocabulary, which
is both repetitive to write and duplicated in the story file. Dialog
declares NPC-agnostic topics; Inform has a topic grammar token. Stefan
ruled the Arcturus shape and the name (`subject`), and said yes to all
three open questions: a subject may carry a default reply, a character
may override the label, and (for ask_for, when it lands) operands
normalise.

Built: `subject <id> "<label>" words a, b` at file level, with an
optional indented body as the DEFAULT exchange. A character writes
`topic <id>` and supplies only its reply; it inherits the words and the
label, may override the label, may take the default by writing no body,
and keeps its own once/when/hidden/idle and reveal state, because the
subject supplies vocabulary and wording, never behaviour. Sema refuses a
subject-naming topic that redeclares `words` (edit the subject), and
still requires a label on a topic that names no subject.

The byte payoff is real and general: identical match-word lists are now
emitted ONCE and every record points at the shared array, so a cast of
five discussing one villain carries five records and one vocabulary. It
paid for the feature outright, no ceiling moved. docs/01 and docs/05
document it; the VSIX highlights `subject`. Suite 1066.

STILL OPEN for Charles: ASK NPC FOR X. Three attempts tonight
(particle role, tabled verb, minimal grammar) each proved insufficient,
and the third showed why: the positional matcher cannot express "and
then free text I should not resolve", so a tabled ask falls back to a
greedy one-noun match and asks "which do you mean". The real missing
piece is a TOPIC SLOT in grammar lines (Inform's topic token), which
also gives ask_for both a noun line and a topic line and so removes the
scope problem. That is the next milestone and the first stone of the
verbs overhaul. Stefan's note for the record: he called grammar the
biggest issue from the outset, and the three cheap attempts were
patchwork that should not have been tried first.

## 2026-07-20: the text slot, and ASK FOR (arcc 1.3.14, Cosmos 1.2.14)

The last of Charles's five, done the way Stefan said to do it from the
start: at the grammar, not around it. Three earlier attempts tonight
(a particle role, a tabled verb with two noun slots, a minimal grammar
tweak) each failed, and the third showed why: the positional matcher
consumed every typed word, so `ask noun about` could not account for
its trailing subject and fell back to a greedy one-noun match ("which
do you mean, the honey jar or the keeper?"). The missing piece was
never the action split; it was a way to say AND THEN WORDS I MUST NOT
RESOLVE.

Built: the `text` grammar slot, which absorbs words and hands them on
as a range (topic_lo/topic_hi) instead of matching them against
objects. The slot code already existed in the emitter, unimplemented in
the matcher. English ask now reads:

    ask noun
    ask noun about text
    ask_for noun for text

so the wording selects the act, and both subjects are text, which is
what they always were: you ask ABOUT the old mine, and you ask FOR a
drink the barkeeper has and you do not, so neither can be resolved
against scope. That also dissolves the scope problem that made the
object-binding designs unworkable. Requests route through the same
topics via a new ask_for_to seam, and a topic tells question from
request with `action is ask_for`.

RULED (Stefan): spend the bytes, grammar correctness outranks the
ceiling. English games pay +828 for the matcher and the ask table, and
Cloak is 18860 against PunyInform's ~28K, so the margin he cited holds.
German and Spanish pay ~100: they phrase a request with their own verb
(BITTE, PIDE) and table nothing. ASK is now the one standard verb on
the table, recorded in the doctrine test that used to assert none was.

The conversation layer reads the range when a text slot supplied one
and keeps the old separator scan otherwise, so the packs still on the
flag model are untouched.

Charles's list is closed but for NPC commands, which Stefan parked with
the NPC engine. Suite 1066.

## 2026-07-21: a fork cannot see that it has aged

Field report, Charles Moore Jr.: SEARCH still does nothing, with the
handler pasted as proof. The handler was real, and it was Cosmos
0.36.5, three releases behind. He had forked extendedverbs.granule
weeks earlier, a fork always beats the bundled copy, and so every
improvement since had landed in a file his compiler never opened. He
found it himself an hour later ("forgot i forked extendedverbs").

The support answer took two tries and the first one was wrong. I sent
him `alter` + `continue` for frisking an NPC without running it; on a
character who is still `animate` the library refuses first and the
alter is never spoken, so he got a rebuff and concluded the feature did
not exist. The suite did not catch it because both halves are tested,
each in its own game, and their crossing was not. The rule that follows
from that: anything recommended to an author becomes a test in the same
commit, and no snippet ships without the transcript that produced it.

RULED (Stefan): the living-character rebuff stays as it is, and wins
over an author's alter. Searching a conscious person should almost
always fail, so the default is right to speak; the compliant frisk is
the exception and `search_loot(self)` is how you ask for it. Pinned by
test, and stated in docs/05 rather than fixed in code.

RULED (Stefan): forks get a staleness warning, but never a false one.
His objection killed the obvious design: compare version numbers and
you call a fork of an unchanged file outdated, which is most forks most
of the time, and a warning that fires on healthy code gets ignored. So
every file arcc writes out carries the FINGERPRINT of the source it
came from, and the check compares that against the bundled copy now.
Base unchanged, silence, however old the stamp reads and however
heavily the fork was edited. Base moved, one note naming both versions
and the command to diff against. Unstamped forks get a softer note;
deleting the stamp line opts out. `--library-status` audits a directory
at once.

The gap was ours, not his. We shipped hackability as a headline feature
and gave forks no way to age. Suite 1079.

The suite went parallel the same day: 1079 tests in 141s serially, 25 to
30s across the cores of a MacBook Pro. Almost every test compiles a whole
game against the library (117ms each, 300 of them), so the work is
CPU-bound and independent, which is the ideal shape for it. The tkinter
and curses tests are pinned to one worker, since two front-ends
contending for a display is how a test stops failing and starts hanging.

RULED (Stefan): the console tests stay inside the parallel run. Under
xdist they warn that forkpty in a threaded worker can deadlock; splitting
them into a serial pass would remove that risk and cost 9 seconds, a
third of the win, for something that has warned but never fired. If it
ever bites, the split is a two-minute change.

## 2026-07-21: the screen a game is told it has

Field report, Charles Moore Jr.: in Actaea's terminal mode the status bar
stops short of the right edge, with a notch in the corner, and a resize
scrambles the screen. Screenshot attached, 103 columns wide, bar 80.

Actaea was stamping 80 into the header's screen-width byte at boot,
regardless of the screen it actually had, and never touching it again.
Every game that lays anything across the screen reads that byte, so the
bar was correct code drawing on a lie. Cosmos was not at fault: its bar
reads the width on every paint and always did.

The io boundary now carries the screen size, each front-end answering for
itself: the terminal its real geometry, the window its 80 cells (that
window IS an 80-cell screen by construction, so 80 is the truth there,
not a default), the pipe 80 by "infinite". A resize re-stamps the header
and resizes the cell grid, keeping what the rows already hold. Verified
by asking a game what it sees: 103x30 before a resize, 120x45 after,
and the bar measured full width at 60, 103 and 120 columns.

RULED (Stefan): adapt upward as well as downward. A status bar is written
once and has to fit a 40-column home computer and a 132-column terminal
alike, and an interpreter that under-reports its screen breaks the wide
end of that range silently. He named the Amstrad PCW under Vezza as the
case that would have shown it next.

The last column is now painted too (curses refuses a plain write to the
final cell, so it is inserted instead), which is what the notch in the
screenshot was. Suite 1086.

## 2026-07-21: the terminal keeps its screen

The second half of the same field report: resizing Actaea's terminal
emptied the screen, and the text trickled back only as play continued.
A curses window holds no history, so the resize handler built a fresh
blank window and there was nothing to repaint from.

The console now keeps its own scrollback: what the story printed, as
LOGICAL lines (unwrapped, with attributes), bounded at 400 lines. A
resize re-wraps that to the new width and repaints. Widen and the text
is simply still there; narrow and it re-flows, verified by watching a
60-character banner line break in two on a 50-column screen. A screen
the story cleared on purpose stays cleared: the erase drops the history
with it.

Two curses traps cost real time, both worth recording. A repaint while
the game is blocked on input needs its own refresh, since nothing else
is due to draw. And the repaint must NOT refresh the window itself:
that clears the touched-line flags, so the refresh that follows (after
the grid repaints stdscr, blanking the region) copies nothing back and
the screen stays empty. The window held the right text the whole time
while the terminal showed none of it.

Method note: every measurement in both halves of this fix was taken by
reading the actual screen through a small terminal emulator over a pty,
never by reasoning about the code. The first three attempts at the
repaint all looked right in the source and all left the screen blank.

Suite 1088.

## 2026-07-21: two assistants, one record

DECIDED (Stefan): from today the project is worked with two models rather
than one. Fable takes the hardest problems, the ones it was built for;
Opus takes the general run of the work, of which today is a fair sample
(an interpreter bug from a field report, diagnosed, fixed, tested,
documented, shipped). The arrangement is permanent rather than an
experiment with a deadline, which is what makes it worth building a
method around instead of improvising per session.

What that changes here: this file is now the hand-off. It was already
the place where rulings live, and it now has to carry enough state that
either assistant can pick the work up cold. So every session ends with
where the tree stands, what shipped, what was ruled, and what is open,
in the same commit as the work. Anything that only lives in one
assistant's head, or in one assistant's private notes, does not count as
recorded.

The reason it matters beyond convenience: the whole point of this log is
to show that the decisions in Arcturus are Stefan's. Two assistants make
that MORE important, not less. A ruling recorded here is a ruling
whichever model was in the room when it was made, and neither of them
gets to quietly re-decide something the other was told.

Checkpoint at this entry. HEAD on main, tree clean, suite 1088 green in
about 30 seconds (the suite went parallel today). arcc 1.3.15, Cosmos
1.2.14, Actaea 1.3.3, arcimg 1.14.1, VSIX 1.0.2; both standalones
regenerated and the README version table current.

Shipped today: the fork stamp (arcc tells a forked library file when its
base has moved on, comparing the file rather than version numbers, plus
--library-status); the living-character rebuff pinned by test and
documented; Actaea reporting its real screen size and following a
resize; the terminal keeping its screen across a resize; the test suite
parallelised.

Open: NPC commands, parked with the NPC engine on pathfinding. The verbs
overhaul, of which the text slot is the first piece. The Plus/4 wave
(R4) and the MSX1 and A8 probes. Actaea does not run Beyond Zork, known
and ruled not serious.

Dropped today (Stefan): arc_image in the terminal. Half-block cells are
the only rendering that works in every terminal, and a debugging view
that shows a different picture from the one the artist painted is worse
than none. The window stays the one front-end that shows pictures.

DECIDED (Stefan), later the same day and superseding the entry above:
one assistant works the project by default after all, not two. What
survives from the co-assistant plan is the discipline it forced: this
file carries enough state that any session picks the work up cold, and
when a hand-over does happen, a checkpoint is written on request. The
rulings recorded here bind whoever reads them, which was always the
point.

## 2026-07-21: darkness gets a picture, and the contract gets its fixed-screen rules

The first fixed-screen implementation of arc_image is in progress
outside the family (Shawn Sijnstra's TRS-80 Model 4 engine), and his
questions found the places Part A had only ever been exercised by a
resizable window. Meanwhile Gargoyle has shipped arc_image on the
modern side and further maintainers have committed: the spec is now a
semi-standard with living implementations, which reframed everything
below as either contract (binds the ecosystem) or Cosmos (binds us).

RULED (Stefan), contract, all additive, ARCI version stays 1: on a
fixed screen a clear (id 0) blanks the band and KEEPS the layout, the
band never collapses mid-game; the band appears at the first non-zero
draw, and the interpreter re-bases then, scrolling the already-printed
banner down rather than covering it, no advance declaration needed or
provided; and the operand widths are stated plainly (id is a word by
format, mode fits a byte). Written into docs/08 Part A. Policy ruled
with it: docs/08 is a normative spec now, changes are additive and
dated, and anything a shipped interpreter could notice bumps the ARCI
version byte.

RULED (Stefan), Cosmos: darkness is a scene too. A game with pictures
and reachable darkness must declare `constant arc_image_dark = <id>`
(Stefan's name), the picture the band shows in the dark; the compiler
refuses to build without it. This replaced the auto-clear design and
killed a real bug: describe_room used to return at the dark gate
before the draw, leaving the previous room's picture hanging over the
darkness. "Black with two red eyes" is the canonical example.

Conditional images (a field question from Garry, the door that shows
open or closed): no new syntax at all. `arc_image` was already an
ordinary value property, so `change gatehouse.arc_image to door_open`
was the whole feature; what was missing was the repaint moment, and
the turn loop now re-checks the wanted picture at end of turn, so the
band follows the scene live instead of waiting for a LOOK. Computed
arc_image blocks were declined (assignment covers the need), as was
author-controlled band placement (presentation is the interpreter's).

The rewind family was quietly wrong and is now honest: UNDO, RESTORE,
and RESTART all rewind shown_image without touching the physical band,
so the dedup could strand a stale picture. Each path now clears and
repaints from truth.

Stefan's bonus ruling: the status bar stops naming a room the player
cannot see. In the dark it says "In the dark" (Im Dunkeln / A oscuras,
each pack's own idiomatic line), behind the same any_dark fold, +40
bytes only in games where darkness is reachable.

The size gate earned its keep again, before the commit this time: the
first build grew 25 always-lit examples by 60 bytes each, because
any_dark was missing from the static-fold whitelist and the guard
compiled as a runtime test. The gate refused, the fold landed, and the
always-lit examples came back byte-identical; only Cloak (z5 and z8)
and beispiel-deutsch grew their +40, which IS the feature. Ceilings
raised with dated notes in the same commit.

arcc 1.3.16, Cosmos 1.2.15. Suite 1097.

## 2026-07-22: the verbs and grammar overhaul begins; phase 1, the honest matcher

The overhaul moved forward on the roadmap on the strength of the week's
field reports, and the design was settled in discussion before a line
was written. DECIDED (Stefan), the shape of the whole thing:

- Validation becomes declarative: verbs state what they need
  (`requires noun carried`, `requires second animate`, Stefan's
  spellings), compiled onto the ACTION so the language packs inherit
  them, enforced BEFORE dispatch so an author's `on give,show` override
  owns the response and can never again accidentally own the holding
  check (the field report: a handler firing on gibberish and on gifts
  the player did not hold).
- Inference is renamed FORESIGHT (Stefan's pick over initiative,
  courtesy, obliging) and is a summonable granule, off by default,
  Stefan's own taste included in the reasoning. Its design kills the
  Inform blemish he named: a side-effect-free probe, factored FROM the
  take's own guard chain so the two can never drift, decides whether
  the repair can realistically succeed BEFORE the parenthetical prints.
  "(taking the sun first) The sun is beyond your reach." cannot happen
  here: the sun case prints the plain refusal and no promise. The
  irreducible residue, an author's own `on take` in the path, falls
  back to print-then-run, and that boundary is a theorem (the outcome
  of author code is unknowable without running it), not a shortcut.
- `requires` failures stay library-owned, no author hook: foresight is
  about to turn the failure path into a repair path, and handing
  authors the old failure semantics would break under it.
- Pay-per-verb via summon selection: `summon.extendedverbs squeeze,
  burn, search` takes exactly those verb families (a family is one verb
  and its synonyms, never a cluster), the bare form keeps meaning all
  of it, and the same selection works on a fork (`summon
  extendedverbs.granule squeeze, burn, search`). Scoped to
  extendedverbs first, deliberately: Stefan wants forks of the one
  canonical verb library, which the fork stamp watches, not a dozen
  bespoke verb granules.
- Grammar surgery: `enhance verb` appends lines and synonyms,
  `redefine verb` replaces wholesale and says so out loud.
- `carried` covers worn (one word, one meaning; a strict in-hand word
  can be added the day someone asks, and GIVE CLOAK while wearing it is
  future foresight food: "(taking off the cloak first)").
- Phases: 1 the matcher bug below, 2 requires, 3 foresight, 4 summon
  selection, 5 enhance/redefine, 6 breadth (noun lists in two-noun
  actions, CONSULT ABOUT, the new verbs). Each with its own done-test
  and size gate.

Phase 1 shipped. The field report's mechanism: the scoring matcher
crowned the best-scoring object even when the phrase held a word the
dictionary never heard of, so GIVE MERCHANT THE XYZZYPLUGH resolved to
the merchant and the garbage vanished (the same word before a
preposition was already caught; the trailing reversed-dative slot
leaked). match_phrase now refuses a phrase with a genuinely unknown
word, naming it, in every position. Two idioms had been leaning on the
tolerance: TAKE ALL FROM (takeall's "from") and GET OUT OF ("of"),
neither word in any dictionary. They are declared noise words now,
"of" in the English layer, "from" in the takeall granule that needs it
(pay-for-use, to retire when the breadth phase makes it a real
separator). Known-word dilution (articles, a stray adjective) is
untouched. Every game pays 24 to 36 bytes for the check; ceilings
raised with the dated note.

arcc 1.3.17, Cosmos 1.2.16. Suite 1103.

## 2026-07-22: phase 2, the verb contract

(improvmonster of the phase 1 report is Charles Moore Jr., for the
record: one field reporter, two channels.)

`requires` is live. A verb states what it demands of its operands, the
declaration compiles onto the ACTION (requires_map, the after_map
manner), and the loop enforces it BEFORE dispatch: a failing turn is
refused with the library's own line and no handler of any kind sees
it. Two forms, per the design: free-standing `requires give noun
carried` (language-agnostic, what actions.prelude uses, so the packs
inherit contracts they never mention) and the in-body sugar `requires
noun carried` bound to the declaring verb's actions. Two kinds ship,
carried (worn included, per the ruling) and animate; the encoding has
room for the rest. Empty slots pass through to the handlers' own asks;
perform bypasses the contract entirely, an author performing an action
means it.

GIVE and SHOW declare a carried noun and an animate second. The
carried requirement is NEW validation, not relocation: the old default
handlers never checked holding at all, which is why Charles's override
answered for unheld gifts. The animate checks moved out of the
handlers into the contract. Charles's battery, all six shapes,
verified end to end; his handler now fires exactly on valid turns and
his code did not change.

Cost, measured and then earned honestly: the first cut was +204 to
+228 per game, because check_requires compiled all four requirement
branches whether or not any verb declared them. Per-bit folds (req_*,
the any_X discipline applied inside one routine) halved it: +104 to
+128 in every game, the price of give/show carrying a contract, and a
requirement kind no verb declares now costs nothing, its message
included. Ceilings raised with the dated note.

Seven pre-contract tests gave things away without holding them; each
was updated to hold the gift first, preserving its original intent,
and one (the failed-guard catch-all) now proves its point through a
second character, since a give to a ring is no longer a turn any
catch-all will ever see. That is the contract working.

arcc 1.3.18, Cosmos 1.2.17. Suite 1112.

## 2026-07-22: phase 3, foresight

The granule is live: summon.foresight repairs a failed carried
requirement with an implicit take. The probe rule held all the way to
code, and the sun case now reads exactly as ruled:

    > give sun to stacy
    The sun is beyond your reach.

No promise, no disappointment. The certain path (no author take
handler on the object or the room) probes first and only then prints
"(taking the apple first)", running the take's own bookkeeping (gain:
score, moved, seen) silently, because the player asked for the give,
not for a "Got it.". The residue is exactly as designed: an object
with its own take handler gets promise-then-run, and the author's
prose lands between the promise and the outcome. A free-standing `on
take` rule is not consulted by the certain path, documented in the
granule and docs/05; a game gating all taking through free rules
should not summon this.

The no-drift ruling has a price tag, and it is the honest one: the
default take now refuses THROUGH the probe (take_probe +
speak_take_refusal in actions.prelude, one guard chain, used by the
handler and the repair alike), so every game carries the factored
routines, +152 to +328 (mostly +244), foresight summoned or not. The
alternative was a granule that duplicates the take's guards and
drifts, which the design forbids. The granule itself costs only its
summoners. Ceilings raised with the dated note.

The parenthetical is the language layer's line_foresight_take:
English "(taking the apple first)", German "(nimmst zuerst den
Apfel)", Spanish "(primero coges la manzana)"; the pack wordings are
mine and await Stefan's native pass.

arcc 1.3.19, Cosmos 1.2.18. Suite 1119.

## 2026-07-22: phase 4, verbs by the slice

Summon selection is live, exactly as Stefan drew it: the bare
summon.extendedverbs keeps meaning everything (no adopter's game
changes), a selection takes named families only, and the same slice
works on a fork. A family is one verb and its synonyms, per the
ruling: search brings "frisk", never dig. The filter runs at load
(the unselected verbs' words never reach the dictionary, which is the
byte win DCE alone could never deliver), an unknown name errors with
the granule's actual offer, and a selection on a verbless granule is
refused with the reason. Three families of the full set: 1888 bytes
saved on the spot.

Selection is a loader feature, so Cosmos itself did not change and no
game that ignores it moved a byte: the suite's size gate stayed green
through the whole phase, the first phase of the overhaul that cost
nothing.

arcc 1.3.20, Cosmos 1.2.18 unchanged. Suite 1126.

## 2026-07-22: phase 5, grammar surgery said out loud

enhance verb and redefine verb are live, Stefan's spellings. Enhance
appends lines and synonyms to an existing family (a body is optional
when only synonyms join); redefine replaces the family whole, and a
synonym the redefinition does not restate leaves the dictionary, which
the old way never managed: a plain redeclaration shadows word by word
and quietly leaves the family's OTHER synonyms on the old grammar
("give" redeclared, "feed" still meaning the old thing). That trap is
now a compile note naming both honest forms; the plain form still
works, unchanged, for the code that exists.

The action's contract survives a redefine on purpose: requires lives on
the action and is wording-independent, so replacing GIVE's grammar does
not shed the carried/animate rules, pinned by test.

Converting the shipped examples turned up their own history: brass
lantern's pull and cloak's read were declared before those verbs joined
the standard set, and had been silently shadowing identical standard
declarations ever since. The relics were deleted; the grammar showcase
now teaches `enhance verb "look"` (its look_under/look_behind lines
join the standard LOOK instead of restating it), direction-grammar
enhances push (press survives now, where the shadow had orphaned it),
catalogs redefines read, and the matrix example redefines the whole
inventory family onto its journal so I, INV, and INVENTORY finally
agree with each other.

arcc 1.3.21, Cosmos unchanged. Suite 1134.

## 2026-07-22: phase 6 begins; noun lists in two-noun actions

"put coin and nail in box" works, the way the roadmap bullet always
promised. The mechanism honors every convention already in the house:
the second binds once, each listed item runs as its own FULL TURN
through sweep_one (the takeall report style, "gold coin: Done."), the
list stops at the first refusal exactly as a chained line does, and
the verb contract guards every item ("give coin and gem to bob" stops
at the gem you are not carrying).

The disambiguation between list and chain is the part worth recording:
an "and" inside a two-noun verb's first slot is a LIST exactly when no
verb follows it and the separator still lies ahead; a verb after the
"and" chains ("take gem and put coin in box"), a one-noun verb chains
with the borrow as before, and an "and" after the separator was always
the chain's business. Single-noun lists are untouched.

The price is the largest single line-item of the overhaul after the
ask table: +508 to +636 per game (mostly +604), measured and broken
down honestly: the list-aware splitter (+188), the runner and
sweep_one now living in every game (+312), the resolve hook (+104).
Core grammar with no fold to hide behind, since put/give/show are
standard. Presented to Stefan for blessing with the phase.

arcc 1.3.22, Cosmos 1.2.19. Suite 1141.

## 2026-07-22: phase 6 continues; the reference book and the typed answer

RULED (Stefan) on the breadth roster: LIGHT in (the lamp-game phrasing,
a switch_on synonym); typed YES/NO in (a real request from Ghosts of
Blackwood Manor: a game asks, `on yes` / `on no` with a `when` guard
answers, flat classic flavor untended, and never meta, because
answering is speech); WAKE out; VERBOSE/BRIEF/SUPERBRIEF out ("always
gives me Inform vibes"); FULLSCORE stays out per the standing ruling.
The +604 noun-list ceiling was blessed with the margin named out loud:
Cloak compiles to 19.6K against PunyInform's 28K after the whole
overhaul.

CONSULT landed as approved: `consult noun about text` on the consult
family, the subject riding the ASK text slot, answered by the OBJECT'S
own inline topics. Topics were already legal on any object (the parse
gate was a myth; only my test's syntax was wrong), so the compiler
needed one honest change: a text slot forces the grammar table, since
the flag model cannot absorb a subject. The scanner (subject_typed)
moved from the infocom_talking granule to core so consult and the
ask/tell presentation share one path that can never drift; DCE drops
it in games with neither. A reference book works with either
conversation granule summoned or neither, pinned by test.

All three languages carry the new words and lines natively (ja/nein,
sí/no, zünde/entzünde an, prender), my wordings, awaiting Stefan's
native pass. +160 to +228 per game (the YES/NO handlers are
data-rooted, so they are real bytes); ceilings dated.

Still open in phase 6: the pushable attribute's name (vectorable vs
shiftable, Stefan's answer pending), and rulings on pick up, notify,
version, and the profanity responses.

arcc 1.3.23, Cosmos 1.2.20. Suite 1149.

## 2026-07-22: shiftable, and the everyday take

RULED (Stefan): the attribute is `shiftable` (the -able family argument
carried), PICK UP is in, and notify/profanity wait on plain-language
explanations before he rules (version still pending with them).

PUSH THE CRATE NORTH is live: a shiftable thing rolls through the exit
with the player, doors respected, the same arrival a walk gets, the
whole path folding away in games with nothing shiftable. The first cut
put `push noun direction` into the standard grammar and the size gate
plus the doctrine test caught what that really meant: a direction slot
always tables its verb, so the positional matcher (~740 bytes) landed
in every English game, ASK stopped being the one tabled standard verb,
and the tabled push stole a game's own "shove" redeclaration out of
the dictionary. The line was unnecessary all along: `way` binds from
anywhere in the command and the matcher ignores a known direction word
in the phrase, so push stays on the flag model and the doctrine holds.
The lesson mirrors the STAND breach from the other direction: this
time the gate did its job BEFORE the commit.

PICK UP THE LAMP and PICK THE LAMP UP are the everyday take now, with
one remap rule keeping them off the boarding path (an up-direction
with a noun is a take, never an enter; climbing still goes through
CLIMB and GET ON). German picked up heb/hebe (aufheben), Spanish
recoger/recoge, both riding their own particle machinery.

+12 to +24 per game. VSCode grammar knows shiftable (sources at 1.0.3;
no vsce on this machine, so the .vsix rebuild is Stefan's or a tooled
session's).

arcc 1.3.24, Cosmos 1.2.21. Suite 1155.

## 2026-07-22: the roster closes; the verbs overhaul's phases are complete

RULED (Stefan): notify in, with the coupling he designed on the spot:
off by default, the author enables it (change notify to true, usually
in on start), and enabling it ANYWHERE brings the player verb along
automatically, never independently. The implementation honors that to
the letter: a game that never writes the global has no bracket lines,
no NOTIFY verb, no handler, and no dictionary word, checked by test.
The watch is one compare per turn at the loop's tail, which catches
every score change from any source (award sites and gain alike) in one
place. VERSION in, the no-brainer, always available: the bug-report
verb. The profanity responses in, the `swear` family in extendedverbs,
one dry reskinnable line. ABOUT clarified as documentation's example
of an author-declared meta verb, not a standard verb; a standard
ABOUT-with-banner-default is one ruling away if ever wanted.

The .vsix is rebuilt by tools/build_vsix.py (no vsce needed; the tool
was there all along): editors/vscode/arcturus-1.0.3.vsix, shiftable
highlighted, the 1.0.2 package retired.

+12 to +20 for VERSION in every game (one grower is the notify-enabled
scoring example... there is none yet; the +160 outlier is the German
example, which carries the new pack verbs). All three languages carry
notify and version words and lines, my wordings, native pass pending.

With this the six phases Stefan drew on 2026-07-22 are all landed:
the honest matcher, the verb contract, foresight, verbs by the slice,
enhance/redefine, and the breadth (noun lists, CONSULT, YES/NO, LIGHT,
PICK UP, shiftable, the session verbs). What remains on the overhaul's
horizon lives in the roadmap: doors and containers joining foresight's
repairs when travel meets them, and CONSULT-adjacent niceties as field
reports arrive.

arcc 1.3.25, Cosmos 1.2.22. Suite 1160.

## 2026-07-22: the gesture; arc_image for PunyInform

DECIDED (Stefan): with Fredrik Ramsberg committed to arc_image in
Ozmoo, something should travel the other way, and the something is an
official PunyInform library extension, written by Stefan in Fredrik's
own ext_* idiom and offered with no strings: whether it ever ships in
PunyInform is HIS decision, the gesture is the point ("he has it in
the drawer then"). It also serves the standard the way the fork stamp
and the normative docs/08 do: the spread is coming regardless, so the
author of the spec writes the reference client, and the provenance
paragraph sits in the header of the file everyone will copy from.

ext_arc_image.h is ~140 lines in the Puny voice: `arc_image N` on a
room, ArcImageUpdate() wired into NewRoom and LookRoutine, the dedup
the spec PROMISES interpreters built in and documented as
non-optional, ARC_IMAGE_DARK for darkness (our own darkness ruling
offered as practice, not contract), ArcImageReset for the undo/restore
staleness we fixed in Cosmos, and a v3 build that compiles to stubs so
one source serves every Puny target, warning-free both ways.

Verified the way everything is verified now: the demo game compiled
with pi6, its draw stream spied instruction-level through Actaea's VM
as the picture-aware interpreter (room picture, dark picture in the
unlit cellar, the cellar's own with the lamp lit, dedup on re-LOOK),
and dfrotz proving the text-only degradation. arcimg packs a Puny
game's pictures without caring who compiled the z-code, which is the
quiet point of the whole exercise.

The directory (arc_image/puny/) is gitignored by Stefan's choice: this
is a gift in a drawer, not yet a public artifact.

Postscript, same evening: the belt-and-braces check earned its keep.
The text-interpreter verification (zero draws expected with the
capability bit clear) caught the classic Inform 6 precedence trap in
the extension's guard: `(0->1) & 2 ~= 0` binds as `& (2 ~= 0)` and
tests the COLOURS bit, so the guard passed on any colour-capable text
interpreter and only the Standard's ignore-unknown-EXT rule (the
contract's second safety layer) kept dfrotz clean. Bracketed, rebuilt,
both streams verified: the full picture cycle with the bit set, zero
draws without it. The spec's two-layer design just proved itself in
its first external client, and the header now warns the next reader.

(And one methodology lesson under it: the "still failing" middle run
was the test harness reusing one loaded story across both VMs, so the
first run's capability bit rode into the second through shared memory.
Fresh story per run, both streams clean: the full cycle with the bit,
zero draws without it. Two real lessons from one gift.)

The drawer got fuller the same evening, per Stefan: the demo is now The
Puny Demo of Rabenstein, wearing the real art (masters 8, the night
path; 14, the hunter's lodge; 17, the shelved cellar; and a plain black
darkness card as 21, his call: darkness gets a card, not a collapse),
packed as an .arcres by arcimg so Fredrik can see the band in Actaea
the minute he compiles. The README now points at Actaea and the repo
properly. The full cycle is verified again on the rethemed game: path,
lodge, dark card, lit cellar, dark, lit, home; zero draws without the
capability bit.


## 2026-07-22: room to type, and a caret that stays home

Two field reports from Stefan's own German session, both fixed at the
source. The input wall was ours, not Actaea's: the compiler allocated a
60-character text buffer and a 12-word parse buffer, sizes from before
chained lines and noun lists made long commands ordinary, and his
three-command German chain died mid-word at exactly 60. The buffers are
120 characters and 24 words now (their oops and disambiguation shadows
grown with them, +216 dynamic bytes per game), and the exact chain from
the screenshot runs whole: oeffne die truhe dann nimm den
bronzeschluessel dann schliesse die tuer mit dem bronzeschluessel auf,
95 characters, three actions, one line. The interpreter always honored
whatever the game declared; the game now declares enough.

The wandering caret WAS Actaea's: the GUI let arrow keys walk the
insertion point up into the transcript. The caret is disciplined now:
Up and Down do nothing (until they mean history one day), page keys
scroll the view without moving the caret, Home means the start of the
input, Left stops at the prompt. Driven through the handlers in the
single-root GUI test, alongside an assertion that the compiled game
hands the read the new 120.

arcc 1.3.26, Actaea 1.3.4, Cosmos unchanged. Suite 1160.

## 2026-07-22: foresight's second act

Stefan's question ("will it also open doors and containers?") turned
out to be the design, already half-built by machinery that predates
the granule: the shut_in path knew "named but sealed away" and the
knowledge model already refused contents never seen. RULED (Stefan):
it has to be part of the granule, unlocked things only, and it is.

Three seams now, one discipline. The container repair: naming a KNOWN
thing in a closed, unlocked container opens it, "(opening the oak
chest first)", and the typed command continues; the contents become
seen silently, no listing, because the player asked for something
else. The door repair: a closed, unlocked door opens on the walk and
the walk goes on; the way back needs nothing, the door stays open.
The chain: GIVE PEARL TO BOB with the pearl behind glass runs open,
take, give, three promises deep, each step asked of open_probe first,
the default open's own factored guard chain (the take_probe
discipline, applied again). Locked stays an honest refusal in every
seam: unlocking is a decision, opening is mechanics. Author `on open`
handlers get promise-then-run, the residue, with a tri-state so their
refusal is never doubled by ours.

Found while testing, worth a line: the two-sided door idiom is `of
door in hall, yard`, both rooms in the placement; my first test
declared spans and walked through the door into the room it started
in. The example knew better than I did.

The seams cost every game 44 to 68 bytes (two small refusal blocks
and open_probe); the repairs cost only summoners. Suite 1167.

arcc 1.3.27, Cosmos 1.2.23.

## 2026-07-23: the probes resume; the Plus/4 converter

R4 begins where the checkpoint left it. The P4 target's pack, unpack,
render, and pattern had been sitting ready since the wave was ruled;
what was missing was the conversion intelligence, which is the
milestone. _convert_p4 implements the Rabenstein recipe as ruled:
hires TED, near-monochrome dithered form built from a per-pixel
TED-hue classification and a saturation-weighted vote (one dominant
hue, at most three accents past it, the sky-and-moon allowance), a
dark/bright luma pair per cell quantized onto the TED ladder with a
true-black paper drop for night floors, ordered dither between the
pair, and a cohesion pass that lets weakly-committed cells adopt
their neighbourhood's hue, turning flicker into regions ("one
dominant ink per region", the ruling's own words). The salient disc
stays bright, the R3 manner.

Whole corpus converts (21 of 21); the contract tests pin geometry,
the two-colours-per-cell invariant, the near-mono hue cap, and a
byte-exact pack/unpack round-trip; P4 rides ZX0 with the ring
guarantee like the rest of the 8-bit family. The night-lineage
renders (masters 8, 14, 17) carry the look; the daylight stress
master stays patchier, and per the predefined-over-choice ruling that
is the recipe working, not failing: the look IS the night lineage.
The renders now go to Stefan, whose eyes are the done-test for art;
the probe (acme on the orb, VICE xplus4 for verification) waits on
his verdict and his emulator answer.

arcimg 1.15.0. Suite 1169.

## 2026-07-23: training on the originals; the palette truth

Stefan's verdict on the first P4 renders split them: the hunter's
lodge genuinely good, the night path not, too much colour in the
trees, and he pointed at the training data: the original Plus/4 hires
PRGs from the Rabenstein source (Botticelli layout at $7800,
luminance, colour, bitmap, cell-interleaved, the top 96 rows the
band, confirmed by the repo's own sc2daad build script). The renders
also go to arc_image/preview/ from now on, his call.

Decoding the originals settled two truths at once. First, THE PALETTE
TABLE WAS WRONG: the preview-grade _TED_HUES had hues pointing the
wrong way (hue 14 rendered green; his sky is violet). The table now
follows the documented TED hue order, calibrated by eye against his
own screenshot, still preview-grade until the wave-3 addendum
freezes measured values. Second, THE MEASURED RULE: scene 8 is 94%
achromatic with exactly one colour family (the sky, hues 13/14 at
lumas 5-7), but the corpus median runs 35-60% achromatic with five
to nine hues; 8 is the extreme, as Stefan said himself. His reduction
is scene-dependent judgment, not one threshold.

Tonight's rule search, honestly reported: luminance-weighted chroma
(a dark violet tree reads black to the artist) fixed the trees but
not the bright lavender clearing; peak-relative and Otsu splits each
fix scene 8 and over-grey the colour-rich scenes. No single statistic
learned his eye, and the next step is the honest one: a per-cell
calibration harness, every master against its original's measured
hue map, scoring candidate rules by cell-level agreement with the
artist. The interim converter ships the corrected palette order, the
luminance weighting, and the achromatic base with a permissive cell
rule: the lodge holds, the night path is still too colourful, and
the harness is the named next step. These P4 reductions later seed
the Spectrum solver rework, per the lineage ruling, so the training
pays twice.

arcimg 1.15.0 (interim). Suite 1169.


## 2026-07-23: the colour budget

Stefan corrected my reading of the training data before it went
wrong: the greenish sky in the master IS the conversion target; his
violet was artistic freedom, and a tool must not chase freedom. The
renderer fix stands (his own PRGs and screenshot prove the documented
TED hue order), but the originals now train STRUCTURE, not hue: no
clashes, subtle dark tones inside larger monochromatic forms, and
less colour is more. Fredrik's full-bitmap call for Ozmoo needed no
reply, his curiosity only; for the record the contract blesses it by
design, and Ozmoo's disk-paging architecture makes a raster split
unworkable there anyway.

RULED (Stefan): the colour budget. Implemented as: the scene's
lit-pixel brightness sets how many cells may take colour at all
(night spends colour on a few strong zones, a lit scene keeps the
lodge richness he praised); within the budget, colour goes to the
strongest-chroma cells first, ranked, which is less-is-more made
mechanical; and colour comes in ZONES, never speckles: a coloured
cell without two coloured neighbours goes grey, two sweeps, so thin
chains collapse. The floor, the luminance-weighted chroma, and the
cohesion pass stand beneath it.

Measured against his originals: 8 at 76% achromatic (his 94, the
extreme he named as such), 17 at 89 (his 61), 14 at 70 (his 42), 12
at 41 (his 48). The renders in arc_image/preview/ (gitignored, his
chosen spot) carry the look: the grey forest with the greenish sky
on 8, the lodge still warm, the garden calmed. His eyes are the
done-test; the numbers only steer.

Suite 1169; converter behavior only, no version bump until his
verdict ships it.


## 2026-07-23: checkpoint (pre-compaction)

State: HEAD on main at the colour-budget commit, tree clean, suite
1169 green in ~34s. arcc 1.3.27, Cosmos 1.2.23, Actaea 1.3.4, arcimg
1.15.0, VSIX 1.0.3 (built by tools/build_vsix.py, in-repo). Both
amalgams and the README table current. Everything since Stefan's
last push is committed locally; he pushes himself.

Shipped this stretch, newest first:
- The P4 (Plus/4) converter in arcimg: hires TED, the documented hue
  order (calibrated against the Rabenstein originals), luminance-
  weighted chroma, achromatic base, and the colour budget as ruled:
  brightness-scaled allowance, strongest-chroma-first ranking, colour
  in zones never speckles. Renders in arc_image/preview/ (gitignored)
  AWAIT STEFAN'S VERDICT: 8 at 76% achromatic (his 94), 14 the lodge
  anchor, 17 mono-blue, 12 calmed. Known blemish: a few edge speckles
  on 8. The PRG training set lives in ~/Downloads/Rabenstein-master
  (Botticelli at $7800, cell-interleaved, top 96 rows; the crossB
  nibble convention decodes it). Open offer: move the PRGs into a
  gitignored repo dir so the harness outlives Downloads.
- Foresight act two: doors and containers repair (unlocked only),
  chained open-take-give, open_probe shared with the open handler.
- Input buffers 120 chars / 24 words; the GUI caret disciplined.
- The verbs and grammar overhaul, complete: honest matcher, verb
  contract (requires; carried covers worn), foresight granule with
  the probe rule, summon selection on extendedverbs, enhance/redefine
  verb, noun lists in two-noun actions, CONSULT reaching any object's
  topics via the core scanner, typed YES/NO, LIGHT, PICK UP,
  shiftable push-travel, VERSION, coupled NOTIFY, the swear family.
- The PunyInform gesture: arc_image/puny/ (gitignored) holds
  ext_arc_image.h with provenance header (no Parchment/Ozmoo mentions;
  Ozmoo work is SECRET until Fredrik ships), The Puny Demo of
  Rabenstein wearing masters 8/14/17 + black card 21 as an .arcres,
  and the README for Fredrik. Handed when Stefan chooses.

Standing facts for a cold start: xplus4 is on PATH on this Mac (just
type xplus4), Stefan's answer of 2026-07-23. acme lives on the orb
Debian in ~/FictionTools. openMSX/atari800: ask before any install
or launch. dfrotz exists; fizmo-console is the debug interpreter of
record; pi6 wraps inform6 with the Puny lib (~/Fiction/PunyInform).


## 2026-07-23: the verdict on the renders; dithering leaves the Plus/4

VERDICT (Stefan, on the colour-budget renders): 14 stays great (the
first version was also good), 17 is great, 8 is on the border of
okay'ish, and 12 is not okay: random colour clashes, grey dots in a
cloud that was otherwise one colour, a background tree silhouette
that is three cell-rows in three different hues, and dithering
artifacts breaking the sky and the statue's right arm. RULED: no
dithering for these images; the originals are flat art and we said
we do not want it. Also his housekeeping: the render folder is
arc_image/scratchpad/ now, because "preview" collided with the
previews directory the conversion pipeline already owns.

Engineering that followed, in his order of complaint:
- Dithering is out of the P4 converter entirely. The in-cell mapping
  is flat: each pixel takes whichever of the cell's two lumas it is
  nearer to. The sky is smooth, the statue's arm is whole.
- One dominant ink per region, taken literally. Each coloured cell
  adopts the strongest hue among its 5x5 neighbours of SIMILAR
  brightness, iterated until the bands converge. The luminance gate
  is also the accent guard: a moon or a lit window is brighter than
  everything around it, votes alone, and keeps its colour with no
  magic threshold. The three-hue tree silhouette collapses to one;
  the foreground patchwork calms; the cloud reads as one thing.
- A relative floor beneath the budget: colour must earn its place
  against the scene's own strongest chroma, so faint wash tint dies
  while deliberate accents stand.

The corpus study that fed it: his own PRGs rendered side by side
with the masters (the graveyard, the chapel, the night forest). The
finding worth recording: his heavy reductions are SEMANTIC. The
chapel's orange master walls went mid-grey; the night forest's blue
master trees went grey ladder; and no scalar the tool can measure
(brightness, chroma ubiquity, blanket coverage) separates the scenes
he stripped from the scenes he kept rich, because the knowledge is
"night trees are grey" and "chapel walls are stone", not a number.
The converter is the strong starting point; the last ten percent of
his minimalism on a scene like 8 is his eye. The hint sidecar
(8.hint already exists for the moon) is the designed channel if he
wants a per-image dial; that is a design question awaiting his call,
not built.

Measured after the fixes: 8 at 70% achromatic (his 94), 12 at 34
(his 48), 14 at 56 (his 42), 17 at 80 (his 61). The four renders sit
in arc_image/scratchpad/ for his next look. arcimg 1.15.1, the
standalone regenerated, README table synced, suite 1169 green.


## 2026-07-23: the region model; the conversion perspective changes

RULED (Stefan), after the zone-vote build made every image worse and
lost the moon: the per-cell perspective is fundamentally wrong. His
words carry the design: the converter must understand, per cell,
"what happens with the surroundings if I add another colour here,
and if the answer is it spills colour clashes, we don't add it". A
sky must not be five colours. A region takes ONE colour and a shadow
colour and sticks with it; less sometimes is more. And the reason
Pixel Polizei sits in our reference was never its conversions (he
believes we can genuinely beat it there): it is that PP KNOWS the
clashes: it shows where they are, on the picture, and fixes them
only with a colour that is free to use in that cell (black, or one
already allowed there). Per-platform constraint knowledge, clash
location, and legal-fix resolution are a FUNDAMENTAL missing aspect
of our logic. Ruled path: pilot the region model on the Plus/4,
get it right, then go back over the R3 targets; the foundation is
platform-independent (hires or multicolour, the constraints and the
clash logic per platform are what change). The hint sidecar stands
condemned by the same ruling: per-image fix-up files break "place
your master and the tool does the rest"; salience must emerge from
the model. The pilot ignores 8.hint, and 8 keeps its moon.

The pilot, in arcimg 1.16.0 (P4 only; other targets untouched):
- Segment first: cells classify by scene-relative brightness band
  and hue family, connected components seed regions, fragments are
  absorbed, near-identical neighbours collapse (the five-hue sky
  becomes one region HERE), and the count converges to what a
  describer would name aloud (cap ten).
- One colour and a shadow per region, fitted to the region's own
  dark and body poles; weak-chroma regions take the grey ladder; at
  most six chromatic regions (the near-mono contract holds).
- Accents under the spill test: solidly bright cells (a moon, a lit
  window; never lit-twig noise) brighten the region's own colour
  while KEEPING the region's shadow, so no neighbour can show a
  clash edge by construction. This is what replaces the hint.
- Boundary pairs, the PP fix rule at generation time: a cell may
  wear only colours already legal around it: its own pair, an
  adjacent region's pair, or black. A thin dark feature crossing a
  bright zone (the statue against the sky) borrows black for its
  dark pole and stays a clean silhouette; no cell ever invents a
  colour that could clash with its neighbours.
- Dither serves the pair: busy master pixels dither (texture,
  darkening), smooth master pixels map flat.

Honest state at handover to his eyes: 12 has one sky, a whole
statue, grey stones, one vegetation green; 8 keeps the moon with
the hint file ignored; 14 and 17 are coherent and clash-free with
a different character than the graded per-cell builds. Known gaps:
the violet mountain ridge of 12 still merges into a neighbour (thin
pastel strips fragment before regions form; a similarity-absorb
attempt made everything worse and was reverted the same hour), and
a barely-tinted slab can take a fully saturated TED hue. The four
renders are in arc_image/scratchpad/. Suite 1169 green; standalone
and README synced at 1.16.0.

His verdict on the pilot (same day, second round): FAILED. The edge
and tint fixes read as no change to his eye; the sky stayed broken,
the moon stayed eaten, blue spilled over 8's ground. RULED: reboot.
He put seven of his own Ghosts of Blackwood Manor conversions on
the table (Amiga original through ST, CPC, C64, MSX, Spectrum, BBC;
all machine-generated in the Photoshop manner, untouched by hand)
and named the lesson: those use MUCH more dither than expected and
look good anyway; analyse how. His chain was Amiga -> ST (16-colour
reduction) -> CPC -> C64, the MSX/Spectrum branch uncertain; and
the dithers use no Bayer crosses (error diffusion, not ordered).
The files live in arc_image/Training/Ghosts/.

What the measurements said: ST 14 colours; CPC the same palette
re-expressed in the CPC's 27-cube (his chain confirmed in the
data); Spectrum just FOUR colours, the palette shrinking as the
per-cell constraint tightens. The dither is diffusion: sparse even
dots drifting with gradients, flat where the palette matches, and
one uniform texture everywhere. The failed builds' converse lesson,
owned in the record: selective dither reads as damage because every
flat-to-dithered seam is itself an artifact; and per-cell or
per-region colour DECISIONS are where clashes are born, while a
global palette denies them existence.

The rebuilt pipeline (arcimg 1.17.0, P4 only): one adaptive palette
for the whole image drawn from the TED's 121 (the master's own
most-used colours snapped plainly, never median-cut averages: the
masters are already-reduced flat art and averaging their extremes
makes mud); Floyd-Steinberg serpentine diffusion of the whole
master against it (_map_pixels_diffusion, the diffusion counterpart
to the ordered _map_pixels the other targets keep); then the
hardware constraint solved LAST, per cell, in the ZX3 solver's
manner (frequency candidates plus the pivot pair), pixels assigned
by their diffused colour so the texture survives. The brightest
cluster is protected into the palette (_protect_extremes), which
is the moon without a hint. Compressed sizes stayed in budget
(2-3K per picture; the ordered-vs-diffusion RLE fear did not bite).

THE DECISIVE EXPERIMENT: a 320x96 band of his GoBM Amiga original
through this exact pipeline converts BEAUTIFULLY: organic diffusion
sky, clean silhouettes, moon glow, no quilting, the manner of his
ST/CPC references in TED violet. The same pipeline on the
Rabenstein masters quilts and shrieks, because those masters are
themselves CPC-derived flat art in saturated primaries: every
colour is loud, so every cell fights. The pipeline is right; the
Rabenstein masters are the variable. The open question handed to
Stefan: whether Rabenstein's retro path needs a tonal pre-stage
(re-entering conversion-intelligence land), or the Rabenstein P4
leans on his own hand-painted originals while the pipeline serves
what it is demonstrably right for: painted masters like GoBM's, the
general adopter case.

The earlier same-day verdict (before the reboot): right track, not there yet.

His verdict on the first diffusion build: horrible, the worst yet;
flat coloured cells without detail, colours all over the place,
"certainly not how Photoshop does it". The reference experiment
that settled it: PIL's own adaptive-palette + Floyd-Steinberg
conversion (the literal Photoshop operation) on the SAME masters at
eight colours looks GOOD: detailed, coherent, no quilts. So the
"the masters are the variable" conclusion of the previous entry is
WITHDRAWN, on the record: the masters were never the problem; the
defect was the stage order. Snapping the palette to TED BEFORE
diffusing collapsed the master's distinct colours into TED's pastel
gamut (shared entries, dead detail, mud). The cascade itself had
shown the right order all along, measured in his own files: the ST
reduces and dithers in free space, and the CPC re-expresses that
palette one to one in its own cube.

arcimg 1.17.1 rebuilds the P4 in that order: free-space adaptive
palette (median cut + k-means polish + protected extremes),
Floyd-Steinberg diffusion against it, THEN each entry re-expressed
as its own distinct TED colour (usage-ordered, bijective, at most
six chromatic hues), and the per-cell pair solve last. Our zero-dep
median cut was verified equivalent to PIL's on these masters before
trusting it. All four scenes now carry detail, one consistent
diffusion texture, the moon without a hint, mountains and statue
present. Renders in arc_image/scratchpad/ await his eye; no claim
of done until it passes.


## 2026-07-23: the C64 speaks the diffusion pipeline; "genuinely perfect"

His verdict on the P4 diffusion build: not good, but better than
anything in a long time. He asked to see the logic on the C64, and
the scratch prototype (arc_image/scratchpad only, the shipped
converter untouched) ran the same four stages with the C64's facts
last: 160-wide fat pixels, free-space palette of eight, diffusion,
one-to-one Colodore expression, then one shared background and
three free colours per 4x8 cell.

VERDICT (Stefan): the C64 render of 8 is "genuinely perfect...
This is perfection... It's a picture I would replace my original
artwork with." The graveyard 12 genuinely good. Ghosts was mindset
training, never the deliverable. Two bugs he caught on the way,
both diffusion artifacts with one nature: FIREFLIES. Dark dots in
a bright sky (error tips a pixel to a distant dark entry), fixed
with a luminance window: a pixel may only take palette entries
within 40 luma of its source. And the reverse he predicted himself
on 12, bright speckles in the near-flat glow, fixed with a
DEADZONE: when the source already sits close to the chosen colour
the residual is dropped, not diffused, so near-flat fields go flat
while true transitions keep their full dither. 8 held its approved
character through both fixes.

RULED (Stefan): the Plus/4 abandons hires for MULTICOLOUR. His
reasoning: get the C64 right and the Plus/4 will look just as fine
through the same logic (TED palette, C64-style cell constraints).
This supersedes the hires recipe the P4 target was built on; the
probe consequences follow when the port is made. The Spectrum
problem stays open, deferred until the time is right.

State: all of this lives in the scratch prototype
(scratchpad/c64_diffusion.py in the session workspace, renders in
arc_image/scratchpad/). The shipped C64 and P4 converters are
untouched pending his go on the port order.


## 2026-07-23: the shared intermediate lands; the CPC expresses it first

Stefan's 12 verdict upgraded to "an amazing image as well" after
the deadzone fix. The order discussion settled the R3 return: he
asked whether to start with the CPC and derive the C64 from it; the
agreed refinement is THE SHARED REDUCTION INTERMEDIATE: one
free-space palette and one diffused index map per picture, every
machine expressing that same intermediate in its own colours and
solving its own constraint after. One gamut hop per machine, never
two; the family coherence of his cascade without generational loss.
RULED ORDER: CPC first (no cell constraint, the pure look for his
review), then C64 (cell solve; A8 keeps deriving), then Plus/4 as
multicolour, then MSX1, and the Spectrum last deriving from MSX1
(nearest palette kin, milder strip constraint). GO given.

CORPUS VERDICT (Stefan, same day): "We hit the jackpot with these."
Two minor catches in the whole lot of 21: purple dots across the
sky of 2, and 10's sky drifting into unnecessary purple. Both were
one blind spot: the diffusion window constrained luminance only, so
a purple entry at sky brightness stayed legal in a teal sky. The
third guard (arcimg 1.18.1): a CHROMA window beside the luma
window; an entry whose tint pulls against the source's tint is
excluded, same-family blends stay legal. Both scenes clean, the
approved anchors held, corpus at 83.6K. The stresstest beach
converted on request: the diffusion carries the water shimmer and
the sun's reflection lane; one honest note flagged for his eye,
the sun's core expressed pale green instead of white-yellow.

His 16-bit question, answered for the record: the AMI/AST/DOS trio
gains little today; their palettes mostly swallow the corpus
masters whole (near-lossless, flat art passes through undithered)
and their ordered dither rarely fires. The diffusion mechanics
would start paying there only for future soft-painted masters with
more gradient than 32 entries hold, GoBM-class art; noted as a
low-priority revisit for that day, not part of the R waves.

Landed (arcimg 1.18.0): _reduce_master and _express in arcimg; the
diffusion mapper carries both firefly guards permanently (luminance
window 40, deadzone 900 in _dist units); _convert_cpc rebuilt as
the first expression (16 cube inks, no cell work, hint sidecar not
consulted; salience is the intermediate's _protect_extremes); the
old C64-derivation path retired from the CPC. The P4 inherits the
guarded diffusion unchanged pending its multicolour rebuild. The
design record carries the dated doctrine change beside the
superseded recipes. Full corpus reconverted: 21 pictures, 85K
total (~4K each, budget held), previews in
arc_image/scratchpad/cpc/ AWAITING STEFAN'S CORPUS REVIEW, the
"family look" gate before the C64 port begins.


## 2026-07-23: the route experiment, and the four fixes land

Before ruling on the fixes, Stefan asked to see the CPC method on
the C64 (corpus + beach) and then a CPC derived from that C64, in
case the family route made the problems moot. The experiment
(scratch only) showed: the C64's designed palette cures the beach's
two ills for free (Colodore has the light blue and warm pastels the
27-cube lacks), but 2's dots persist on every route (born in the
intermediate), and a CPC derived from the C64 imports cell-solve
artifacts into the one machine that has no cell constraints.
RULED (Stefan): "CPC from C64 was a bad idea, CPC is almost there
already." Direct CPC with the four fixes first, then head-scratch
the next platform. On the way he noted the Plus/4 diffusion renders
look genuinely better than the C64's, a lot, likely the bigger
palette (121 vs 16); noted for the platform discussion. "We are
closer than ever."

The four fixes (arcimg 1.19.0), all verified on the corpus:
1. FREQUENCY SEEDING: a colour holding a hundredth of the picture
   is a paint, not a blend; paints seed the palette verbatim and no
   polish may move them (k-means had drifted 2's flat green sky
   into a teal centroid that matched nothing; the homeless sky then
   flickered magenta through the fallback). 2's sky is now the
   master's own green, dots gone.
2. FAIL-SAFE FALLBACK: when no tint-compatible entry exists, the
   pixel picks by its SOURCE, never the error-laden accumulator,
   and drops the residual. Deterministic, no flicker.
3. THE GREY-AXIS RULE in _express, the old CPC recipe's wisdom
   relearned: a chromatic entry never lands on mid-grey or white,
   and losing saturation costs. The beach's water shimmer expresses
   teal-blue instead of grey.
4. Merge threshold 4x -> 2.5x: the two sun-golds merge and the sun
   is yellow-white, not green.

Corpus and beach reconverted; previews in arc_image/previews/cpc/
and previews/stress/ for his re-review. The anchors held their
character with truer skies (exact paints).


## 2026-07-23: a step down owned; the jackpot base restored, surgically

His verdict on the four-fix corpus: a step DOWN, period. The
details had suffered everywhere his eye landed: the beach's back
water flattened to a single colour, yellow dots on the horizon,
and 2's church windows lost "every friggin detail", the exact
reason he was hesitant to touch a working thing. His sharp
observation cracked it: the C64 render sitting loose in the
scratchpad (his "brilliant and perfect") looked far better than
the same scene in the c64-diff folder. The differences: 8 palette
entries versus 16, and no chroma window versus one. The dither IS
the detail; every guard bought cleanliness by draining life.

A unification was proposed (guards fire only where the master is
smooth; busy areas get unguarded diffusion; palette eight; seeds
only for giant paints) and he approved the experiment. My own
verification killed it the same hour: 8's sky went olive, 10 lost
its approved balance; palette eight starved corpus scenes that
sixteen had carried to the jackpot. Withdrawn before it reached
his eyes, per the commitment to show failures, not claims.

What the full ledger of his verdicts actually proves: the jackpot
build (sixteen adaptive entries, GLOBAL guards, no seeding) was
never the problem. Its three real ills each have a surgical cure
that touches nothing else. arcimg 1.19.1 is exactly that: the
jackpot base, plus the fail-safe fallback (2's dots die without
costing detail; fallback pixels were noise by definition), plus
the grey-axis expression rule (the beach's water shimmers in
teal-blue, never grey), plus the 2.5x merge (the sun is yellow-
white). Seeding is retired with a dated note in the source; the
local-guards variant likewise. Verified per scene before handover:
8 and 10 byte-familiar to their approved jackpot selves, 2 with
glowing detailed windows AND no dots, 12 held, the beach keeping
its shimmer detail in the right colours. Corpus and beach in
arc_image/previews/cpc/ and previews/stress/ for his eye.

VERDICT (Stefan, same day): "CPC is perfect now. And I mean:
genuinely perfect." THE CPC GATE CLOSES: the family look is
approved on the constraint-free target, arcimg 1.19.1 is its
build, and the shared intermediate stands validated. His companion
observation: the regenerated C64 experiment under the same
machinery makes him doubt his earlier P4-over-C64 impression;
side-by-side says the C64 at sixteen entries is improved but still
short of his approved eight-entry render, and the emerging rule is
RESTRAINT RELATIVE TO GAMUT: the CPC sings at sixteen entries
against its 27-cube, the C64 at eight against its sixteen colours,
both about half the machine's gamut. Input for the platform
head-scratch that comes next.

RULED (Stefan, same day, on the proposal to unify the grey-axis
rule with a luminance weight): "maybe _express shouldn't be
shared. WE ARE NOT TOUCHING CPC AGAIN." THE CPC IS FROZEN. The
mechanism: golden digests now pin the CPC's exact output bytes on
representative corpus scenes (tests/test_arcconvert.py); any
change to the shared pipeline that would drift the CPC fails the
suite and must go into a target-private variant instead.
Expression policy is per target from here on: the C64 port gets
its own expression carrying the luminance-weighted grey rule (a
dark navy may read as grey, the night-tree eye; a lit blue or a
sunlit brown never loses its hue), and the CPC keeps, forever,
exactly the path its "genuinely perfect" verdict was given on.
The knob-isolation record behind the rule: the brown in the
C64-eight's trees was the flat grey-axis ban forcing a dark navy
off Colodore's grey; the beach's cliffs and water want the ban;
saturation-at-brightness separates the cases cleanly (7 vs 18-19
on the measured entries, threshold 12), the same principle the
P4 era proved twice.

Three faults named: the moon's rim eaten by dither, massive bluish
blocks sitting in 12's yellow glow "like a bug", and dither
shredding the lodge's ladder and the view out its door. Two fixes
followed (arcimg 1.16.1), one shared root: an EDGE is not texture.
A pixel already close to one of the cell's two tones now maps flat
always, so the meeting line of two flat things stays crisp (the
moon's rim, the ladder's rails), and only genuine midtones in busy
areas dither. And the pole picker now weighs the cell's own tint
direction alongside brightness when borrowing a legal colour, so a
sky-region cell stranded in the glow follows its own yellow lean
instead of stamping a blue block. The blocks dissolved, the ladder
is clean, the door view reads. Renders in arc_image/scratchpad/
await his next pass.

The R4 queue as ruled: P4 converter verdict (Stefan's eyes, now
pending) -> P4 probe (6502, acme on orb, dzx0r_6502 ring model,
verify in xplus4) -> ZX3 solver rework (inherits the P4 reductions,
the lineage ruling) -> MSX1 (Stefan's base ruling at its start) ->
A8 -> Agon Light RLE for Shawn (codec 0 exists; new target chapter).
Behind the wave: pathfinding + NPC engine, the IntFiction showcase
post (written WITH Stefan; the cave-rule recipe is the designated
showcase), and the Beyond Zork gap (ruled not serious, never start
unprompted).

Discipline reminders that bite: discuss designs first, build on the
explicit go; every adopter snippet ships with the transcript that
produced it and becomes a test in the same commit; size ceilings move
only with dated notes in the same commit; docs update in the same
step as what they describe; no em dashes anywhere; accents always
proper; PROGRESS is the hand-off and the human record both.

## 2026-07-23: the C64 ships the approved prototype, pixel for pixel

Stefan cut through the parameter questions: "Can't you make it so
that it EXACTLY creates the same image like C64-diff.png in
scratchpad again?" Done, and proven: the scratch prototype he
approved outright is transplanted verbatim into _convert_c64
(arcimg 1.20.0) as target-private code: _c64_diffuse (luminance
window and deadzone, deliberately NO chroma window; the approved
render predates it and the render is the specification) and
_c64_express (plain metric, merge at 4x, no grey-axis; Colodore is
a designed palette whose greys are art). Eight-entry intermediate,
Polizei background vote, multicolour cell solve last. The shipped
preview of 8 compares PIXEL-IDENTICAL to the approved scratch
render. The CPC goldens stayed green throughout: the freeze held.

The old hint-promotion tests died with their doctrine: the C64
does not consult the sidecar; _protect_extremes carries salience,
and the pinned invariant is DISTINCTNESS (the fixture disc renders
~85000 _dist units apart from its sky; floor 20000). The ZX3
keeps its hint behavior until its own round. The A8 still derives
from the C64, so its corpus is stale against the new base and gets
reconverted and reviewed at its own round. Corpus in arc_image/c64,
previews in previews/c64, awaiting Stefan's corpus review.

## 2026-07-24: the C64 is a child of the frozen CPC

Overnight review settled it. RULED (Stefan): "The derived route
without any alteration was already it": the from-CPC C64 corpus
was genuinely all good ("we cracked it"), and the cyan hue
experiment he asked for taught its lesson and died the same hour:
the beach with cyan "even doesn't look good", the hue-term corpus
neither, and the record shows why (teal-to-green was wrong on the
beach's water and right in 2's night sky: irreducibly contextual
taste; the narrow rule still moved approved scenes, and 2's sky
went purple through injective cascade). One-scene taste belongs to
the hand-polish loop, which has been first-class doctrine since R3
(a hand-authored .C64 is the source of the family when present).

Shipped (arcimg 1.21.0): _convert_c64 = _c64_from_cpc(_convert_cpc
(rows)). The frozen, golden-pinned CPC is the family reduction;
the C64 adds only the injective usage-ordered Colodore recolour
(plain metric) and the multicolour cell solve. Verified pixel-
identical to the approved from-CPC set on 8, 12, 2, 17; the C64 is
now golden-pinned too, same freeze mechanism as the CPC. The
direct-pipeline C64 of yesterday (private diffusion and expression)
served one day and lives in git history. The A8 derives from the
C64 as always and now stands on the frozen family base; its corpus
review comes at its own round, followed by the Plus/4 multicolour
rebuild from this same C64 logic, per the standing ruling.

## 2026-07-24: the Plus/4 goes multicolour, a sibling of the C64

Clarified by Stefan: the multicolour Plus/4 rebuild is what he
meant, it "cracked it as well", and it must exist first; then the
C64-from-Plus/4 experiment. Both delivered.

Shipped (arcimg 1.22.0): _convert_p4 = _p4_from_cpc(_convert_cpc
(rows)). The Plus/4 is a child of the frozen CPC exactly like the
C64: each CPC ink claims its own TED colour (injective, usage-
ordered; the 121-colour gamut fits all sixteen without merging),
then the TED multicolour cell solve: 160 fat pixels, per 4x8 cell
two private colours plus TWO global registers (one richer than the
C64), both registers elected by the Polizei clash vote. The .arc
P4 payload is multicolour now (2-bit codes, hue and luma matrices,
two register bytes as hue<<4|luma); the target ledger and its test
carry P4 at 160; the hires build lives in git history. Corpus in
arc_image/p4, previews in previews/p4, AWAITING STEFAN'S REVIEW.
The probe plan follows the multicolour layout when its round comes.

The experiment, second half: C64 derived from the multicolour
Plus/4 (scratchpad/c64-from-p4mc/). Verdict from the renders, same
as the hires attempt the day before: grey-brown mush; TED's pastel
gamut washes out the saturation the Colodore mapping needs. With
the C64-from-hires-P4 counter-example this closes the question
twice over: THE FAMILY TREE HAS THE CPC AS ITS TRUNK, the C64 and
the Plus/4 are siblings both deriving straight from it, and pastel
leaves make poor parents. The shipped C64 stays a child of the
CPC, golden-pinned, untouched by this round.

## 2026-07-24: P4 multicolour accepted; the A8 rides the frozen base

VERDICT (Stefan) on the multicolour Plus/4 corpus: "genuinely not
that bad, just little colours at times replaced by much grey."
Accepted for now; the grey note is the known lever for a later
polish round (the TED expression inherits the plain metric, and
TED's pastel gamut pulls mid-saturated cube inks toward its greys;
the cure would be a P4-private expression policy, the per-target
mechanism already ruled). "For now C64 stays as is."

Order ruled by discussion: the A8 review before the Plus/4 probe
(cheap debt first; the probe depends on the settled P4 format, not
its colours). The A8 corpus reconverted from the frozen C64 base,
previews in previews/a8 awaiting his eye. Honest note from the
spot-checks: 8 carries the night mood well; 12's lower half lost
green to blue in the per-line register solver, which was tuned
against the old flat C64 base and now consumes diffusion texture;
whether the A8 needs its own round is his call after review.

## 2026-07-24: process ruling; the new A8 renders go to review properly

RULED (Stefan, standing discipline from here on): official preview
directories are written ONLY when a corpus is settled by his
verdict. Experiments and review candidates go to the scratchpad,
SCALED like the other review renders, so he can judge properly.
The A8 reconversion violated that and is corrected: the new-base
renders sit scaled in arc_image/scratchpad/a8/ for his proper
feedback (his first look: "these don't go... not good pictures"),
and the official arc_image/a8 + previews/a8 are restored to the
approved pre-port state (regenerated from the 649e8b7 arcimg, the
last commit whose A8 chain was the reviewed one).

VERDICT (Stefan) on the new-base A8 review set: fails. Details lost
wholesale (18's portrait face a crippled remnant, 19's face almost
unrecognisable, 12's statue unrecognisable), colours off (1, 11),
purple line artifacts (4, and a thick one through 10). "This is not
it for Atari 8-bit." Diagnosis on record: the A8's constraint is
per SCANLINE (four registers per 160px row, switched per 8-line
segment), the one constraint shape in the family that flat zones
suit and diffusion weave starves; the purple lines are segment-
boundary register flips. The officials stay at the approved
pre-port state; the A8 round needs a ruling on its base.

## 2026-07-24: the A8 finds its own way; direct from the master

The A8 story of the day, compressed: the new-base review set failed
("this is not it for Atari 8-bit": faces crippled on 18 and 19,
colours off, purple segment lines), the flat-base set fell with it
("also horrible", first proper look), and the from-Plus/4
experiments taught brightness (structural luma carry) and hue (the
ruled TED->GTIA table, violet over the metric's pink bias) but kept
the lines and lost the portrait to the scratch solver. RULED
(Stefan): no parking, no deferring; "we cannot park any issue and
then finish with a bag full of issues." Idea 1 chosen from the
options: THE A8 CONVERTS DIRECT FROM THE MASTER, as the per-line-
palette machine it is.

The prototype (scratchpad/a8_direct.py, corpus scaled in
scratchpad/a8-direct/): each 8-line segment picks its own four GTIA
colours from its own strip of the master (median cut, polish, the
brightest-cluster defense per segment), neighbouring segments may
differ by AT MOST TWO registers (what a real DLI affords, and what
kills the boundary lines), and guarded Floyd-Steinberg flows across
the whole band with per-segment palettes so seams blend. First
results: 18's portrait face is back and recognisable, 19's faces
likewise, 12 keeps statue, pink mountains, and green grass, 8's
night carries no visible segment lines. The existing A8 .arc
payload (per-segment register table plus 2-bit pixels) already fits
this output shape, so the probe contract would hold. AWAITING
STEFAN'S CORPUS REVIEW.

VERDICT (Stefan) on the upgraded direct-A8 corpus: "Wow. these are
all great" with one wound left, the missing moon, and one wish,
slightly more luminance. The closing fixes, each one paid for by
his eye across the day: THE MOON RULE (the strip's brightest
cluster is a hard palette member, never merely priced; the disc
had been merging into its own protected glow), the GENTLE LIFT
(luminance scaled up 12 percent at black fading to nothing at
white, so mids brighten without washing highlights), continuity
demoted from law to price (the format replays all four registers
per segment anyway; the hard two-carry rule had flattened 8's
canopy when the moon slot squeezed the palette), and THE DARKEST
ANCHOR restored from the old solver's doctrine (losing black under
the luma-dominant metric painted the canopy flat navy; the shadow
mass now defends its slot). 8 closes with moon, textured trees,
and its night intact. Corpus in scratchpad/a8-direct/ for what
should be the closing review.

His crops named the last disease precisely: blue slabs "as if
something is defaulting to it", killing detail. One cause: dark
strips whose four slots lost BLACK snapped their base to GTIA navy,
and the deadzone painted slabs; neighbouring strips that kept black
dithered fine, so the failure read as alternating bands. The rule
that closes it, from the project's own night doctrine: BLACK IS
THE CANVAS. A strip whose shadow tenth is truly dark (p10 luma
under 25) carries black as a forced member, like the moon rule at
the other end of the ladder; navy becomes the texture partner,
never the base. Scene 2 transformed on the spot (glowing church
over black-textured village). Known remaining softness: 7's
blanket folds sit under the deadzone and render flat; a smaller,
separate question for his eye. Corpus regenerated in
scratchpad/a8-direct/.

His next pass: better, but some blues unfixed (different root
cause?) and the ask that white get the black treatment. Both
right. The 19 trace found the second root cause with data: the
master has NO blue band; the blue is the figure's hair. The band
was hue-blind darkness quantization: the dark PURPLE background,
with no dark-purple slot, landed on blue because darkness outbids
hue in plain distance. The cure was already house doctrine: the
CHROMA WINDOW (tint loyalty) joins the A8 diffusion, so dark
purple dithers toward purple and black, never blue. Landed with
it: WHITE IS A CANVAS TOO (his symmetric rule: a strip whose
bright tenth exceeds 215 carries white as a forced member), and
the dark deadzone (dark content dithers from 300, not 900, giving
7's blanket its folds back). 19's band dissolved into the purple
it always was; 7 textures; the corpus regenerated in
scratchpad/a8-direct/ for the pass that decides shipping.

## 2026-07-24: "nothing regressed. A8 is approved."

The A8 ships (arcimg 1.23.0). The approved scratch pipeline is
_convert_a8 verbatim: direct from the master, per-segment adaptive
GTIA palettes carrying the day's five earned rules (the moon rule,
black and white as forced canvases, the darkest anchor, region-
balanced luma-dominant scoring with continuity as a price, and
tint-loyal guarded diffusion with the dark deadzone and the gentle
lift). The retired doctrine died cleanly: the job wiring no longer
routes a hand-authored .C64 into the A8 (pinned in the negative by
test), the C64-taste and hand-polish-inheritance tests are
replaced by direct-doctrine ones, and the disc invariant is
re-measured and re-floored on the new chain. A8 goldens pinned on
the approved corpus, same freeze mechanism as the CPC and C64;
officials regenerated under the settled-only rule. The family
picture at end of day: the CPC is the trunk (frozen), the C64 and
the multicolour Plus/4 are its children (frozen and accepted), and
the A8 stands alone, direct from the master, approved. Next: the
Plus/4 probe, MSX1, and the Spectrum's turn at the end.

## 2026-07-24: the A8 probe, written and assembled

Ruled order: the A8 probe before the Plus/4's ("if you really mean
A8 then we should do that first"). Clarified on the way: the A8
.arc format never changed with the new converter (same linear
bitmap, same per-line register table); only the bytes inside got
better, so the probe targets the format as it always was.

Built: arc_image/probes/a8/probe.asm, the reference A8 loader
written from the blueprint alone. ANTIC mode E, a custom display
list with a DLI on the last line of each 8-line segment, the
compacted segment palettes replayed through the chain (pixel %00 =
COLBK, %01 = COLPF0, %10 = COLPF1, %11 = COLPF2), segment 0 armed
through the OS shadows, and a deferred VBI resting the chain
cursor each frame. The shared dzx0r_6502 ring decoder rides along
with its zero-page cells relocated to the FP scratch area (the C64
defaults are DOSVEC and POKMSK on the A8; the decoder file now
takes overridable cells, C64 behavior untouched). The beach pair
(9.A8 mode 9, 12.A8 mode 12, ZX0) is embedded; assembled clean
with acme on the orb (probe.xex, 8591 bytes). Verification in
atari800 pends Stefan's answer on the emulator (the ask-first
rule).

## 2026-07-24: the probe finds two truths; the A8 corpus reopens

The A8 probe ran on Altirra (his tool, via Wine; the atari800
assumption corrected). The road there paid twice: an acme
precedence trap (#>BMP + $0f parses as >(BMP+$0f); the runaway wipe
strafed POKEY for minutes, and Stefan's ear caught what I waved
away as drive noise: logged as the lesson that his ear was the
debugger), and then the probe's screen showed blue where arcimg
renders gold. The trace found THE GTIA WHEEL MIRRORED: arcimg's
hue circle runs backwards, with hue 5 purple at the fixed point
(why purple always matched). Confirmed on the metal: reconverted
beach assets under the mirrored wheel show warm and true in
Altirra. The wheel fix and its ruling (goldens, corpus, the C.7
addendum "measured from the probe emulator", now literally that)
wait behind the corpus work.

Because Stefan then ruled the deeper matter first: the A8 corpus
has a remaining bug, the grey disease he had called three times
("details missing... you are not capable to see it... did you
actually check the original?"). The honest answer was no: renders
had been compared to renders. Measurement discipline began there:
the beach master's cliffs measure warm (68,57,44) spread 24, the
true neutrals 9-13, my tint thresholds sat blind at 30, and the
protected blue sea (weight 478-521, the largest in its strips) was
being "housed" by equal-brightness greys 3832 close under the luma
metric, inside the 4000 radius. Two fixes, measured not guessed:
TINT LOYALTY IN THE HOUSING TEST (a chromatic cluster is not
housed by a grey; boundary 18 from the measurements) and the
TINT-LOYAL SNAP (_a8_snap: a warm source may only snap warm, cool
only cool, grey only for true neutrals). The beach now shows warm
salmon cliffs, blue sea, gold lane. A measurement-box lesson
rides along: crude regions that mix cliff face, shadow, and sea
average to grey and slander a good render; measure regions that
are one thing.

State: ALL UNCOMMITTED pending Stefan's corpus verdict (the
settled-only rule): the tint fixes sit in the working tree, the
A8 goldens intentionally fail, officials stay at the approved old
bytes, review corpus in scratchpad/a8-tintfix/, beach previews
beside it. After his verdict: commit + re-pin + officials, then
the probe's own display bugs (mid-scanline stripes, torn upper
rows), then the wheel-mirror ruling.

His next pass on the beach outlined the mid band: still half grey,
and his diagnosis was surgical: THE RIGHT COLOURS WERE ALREADY IN
THE LINE'S REGISTERS and the pixels reverted to grey anyway. The
mechanism was exactly that: the diffusion's chroma gate compared
tint MAGNITUDES, and the GTIA wheel holds only fully-saturated
chromatic entries, so every softly-tinted pixel failed the window
against the very register that was right for it, leaving only the
greys. The gate now compares DIRECTION: a tinted pixel may use any
entry on its own side of the wheel, the diffusion mixes it with
the greys to make the soft tone, opposing tints stay forbidden,
and near-neutral pixels keep the strict window so flat greys never
sprout specks. The beach's outlined region turned blue on the
spot. Corpus regenerated again (scratchpad/a8-tintfix/); still
uncommitted, still his verdict's to give.

"Whatever you did had zero effect": correct again, and the reason
was the second guard standing behind the first. The chroma gate
had opened, but the LUMA WINDOW still forbade the pairing: dark
warm stone (luma 58) against the line's only warm register, the
bright lane gold (luma 164), 106 apart against a 40 window. There
is no dark-warm register on a 4-slot line; soft warm reads ONLY as
a duty-cycle mix of bright gold and black, which is what the
diffusion accumulator exists to balance, and what the anti-firefly
window forbade. Now a SAME-DIRECTION chromatic entry bypasses the
luma window; greys and opposing tints keep every guard (flat
neutrals never speckle, blue water never catches fire). Verified
by pixel diff, not impression: 17.6 percent of the beach changed,
the cliff mass warm top to bottom, the sea blue through the mid
band. Corpus regenerated once more; uncommitted; his verdict.

The fourth beach round, his frustration earned and the words that
finally landed: "you are affecting what is INSIDE this grey but
never the grey itself." The BASE of the field was grey: the
per-pixel nearest-by-distance choice hands every soft-tinted field
to the achromatic register, because the wheel's chromatic entries
are saturated and numerically farther; blue only ever fired as
texture ON grey, base and accent inverted from the master. The
rule that closes it: THE FIELD BELONGS TO THE TINT. A tinted pixel
sees achromatic entries at distance scaled by its own tint
strength, so the majority of a blue sea is painted by the blue
register and grey becomes the texture, never the canvas. Measured
in his outlined region: the base flipped from grey to 62 percent
blue, grey down to 10, 23.3 percent of pixels moved, diff-verified.
Corpus regenerated; uncommitted; his verdict stands as the gate.

His Kopie comparison ruled the next correction: the pixel-gate
scaffolding (directional admission and luma bypass) had to go,
because with the field rule landed it only sprinkled dots into the
sky. The full revert overshot (the sea base fell back to grey at
33 percent: the field rule cannot paint what the strict windows
refuse to admit), and the honest middle is a STRONG-TINT bar: only
a strongly tinted pixel (tint magnitude 22 and up: the sea, the
deep stone) may take a same-direction chromatic register past the
windows; the sky's soft tint never crosses, so its field stays
clean. Measured both sides: sea base 63 percent blue, grey 9;
sky pure sky tones, no speckle. The A8 rule set as it now stands:
tint-loyal housing (18), tint-loyal snap, strict windows with the
strong-tint gate (22), the field belongs to the tint, and the
untouched foundations beneath (moon rule, canvases, darkest
anchor, continuity as price, dark deadzone, gentle lift).
Corpus regenerated; uncommitted; his verdict is the gate.

The round that ended the grey war was Stefan's own design, given
at the point of exhaustion and better than everything I had tried:
"the choice of the canvas being grey was wrong, and having it
light blue or something could have a positive effect. We never
tried that." Executed as THE CANVAS TAKES ITS USERS' TINT: every
pixel gate of the previous rounds reverted (the pixel stage is
byte-identical to the Kopie build he called right), and one
palette post-pass added: for each mid-grey register, gather the
strip pixels that would land on it, and if they are tinted one way
the register becomes their tint-loyal colour. True black and the
canvases stay; chromatic entries stay; skies never speckle because
no pixel gate exists to speckle them. Measured: the sea field's
base is the light blue he named, 46 percent of the region, grey
canvas dead, sky clean. The lesson over four failed rounds, his
words the whole time: the canvas was the decision, and the
decision lives in the palette, not the pixels.

VERDICT (Stefan) on the canvas-auto corpus: "basically that was it.
So simple. It all looks good now", with two notes he could live
with: black bars where the right colour already sat in the band
(2's sky top, 12's trees), and 14 refusing to translate, its
role as the session's own stress case. The black bars fell to the
same rule one register down: BLACK CANVASES JOIN the users'-tint
rule, with true darkness protected at the measured boundary (users
mean luma under 25 keep their black; the night of 8 is untouched,
verified). 2 came clean to the top; 12 cleaned through left and
center with its true-dark firs keeping night black. The canvas
contact-sheet toy exists in the scratchpad (auto, cyan, brighter,
navy, sky-echo; auto ruled genuinely good and stands).

The black-bar investigation closed by Stefan's instinct: "it might
as well be something else." It was. The state-sheet round first
exposed my broken variant harness (assertless replaces, three
identical panels), then the assert-checked numbers convicted the
two chasing rules as near-no-ops on their target (zero and 103
pixels on scene 4), and my earlier "duty flipped" claim as
confirmation bias. The ground truth ended it: scene 4's fir
interiors are near-black-blue IN THE MASTER, and the frozen
"genuinely perfect" CPC renders the same black masses with blue
rim-light; the A8's bar is the family's own darkness, rendered
with four registers where the CPC feathers with sixteen inks.
RULED: leave as is. Both chasing rules reverted; the shipped
state is exactly the approved canvas-auto build; the corpus
regenerated once, consistent. The Kopien measured 65 percent from
every state and turn out to predate the canvas rule entirely:
that diff was noise, logged as such.

## 2026-07-24: "We leave it as is. It's genuinely good." The A8 lands whole

The reopened A8 corpus closes on Stefan's verdict. Landed as one
state (arcimg 1.24.0): the direct-from-master pipeline with its
five foundation rules, plus the reopening's earned three: TINT-
LOYAL HOUSING (a chromatic cluster is not housed by a grey,
boundary 18, measured), the TINT-LOYAL SNAP (warm snaps warm, cool
snaps cool, grey only for true neutrals), and THE CANVAS TAKES ITS
USERS' TINT (Stefan's own design, the rule that ended the grey
war: each mid-grey register becomes the tint-loyal colour of the
pixels that land on it; the sea found its light blue by itself).
Goldens re-pinned on the approved corpus; officials regenerated
under the settled-only rule; suite 1182 green. The black bars
stand as the family's own darkness, ruled left as is.

The A8 conversion round is DONE. Remaining on the machine: the
probe's display bugs (mid-scanline stripes, torn upper rows,
assembly-side) and the wheel-mirror ruling the probe proved on
Altirra's metal (goldens and corpus shift when it lands: his
ruling to schedule). Then the Plus/4 probe, MSX1, the Spectrum
last, Agon RLE for Shawn.

## 2026-07-24: "Winner, winner chicken dinner." The probe's last line dies on the WSYNC edge

The line that survived every earlier fix (one boundary of the
mode-12 display wearing the previous segment's registers for
exactly one row) is dead, and the killer was measurement, not
theory. The session's instruments, in order: a two-tone marker
build (segment 10 pink, segment 11 green) that proved the chain's
geometry; VBLANK-safe seeding (a mid-frame seed had displaced the
chain per draw, the cause of the toggling states Stefan reported
across keypresses); then pixel-exact conformance sweeps of
screenshots against the decoded .A8 ground truth, which convicted
row 88 alone, stably, while my cycle model insisted the stores
were early by fifty cycles. The model was wrong and the machine
said so: a verdict build read VCOUNT at entry and counted the
distance to the next VCOUNT edge after the stores, and painted
its answer below the picture. BLUE: entry on time, stores one
scanline late. On a mode-E line ANTIC steals roughly every other
cycle, and the old prologue (three register saves, three staged
loads, 33 CPU cycles) rode the DMA-starved line to the WSYNC
deadline; the last fire tipped past it, and any added cycle
tipped them all (the +7-cycle instrumented build contaminated
every boundary, the accidental proof).

THE FIX, the paid-for lesson now in the probe's comments: the
pre-WSYNC path is a register save and ONE load, ten cycles; the
four colour stores stream out through the horizontal blank after
release, done before the new line's pixels; the bookkeeping saves
happen after, where timing is free. Stefan's sweep of the fixed
build: eleven of eleven boundaries on time, no contamination, no
flicker. "Winner, winner chicken dinner."

Process note, Stefan's ruling in spirit: he shoots the screen,
the analysis reads the file from his Desktop; my self-capture
fights cost more than they gave and are retired. The wheel-mirror
ruling stays queued; then the Plus/4 probe, MSX1, Spectrum last,
Agon RLE for Shawn.

## 2026-07-24: "Yes, give it to me." The wheel mirror lands (arcimg 1.25.0)

The ruling the probe earned: GTIA's hue wheel runs the opposite way
around the colour circle from arcimg's original model, mirrored
about hue 5 (the probe rendered gold as blue until the scratch fix;
four wheel points confirmed on Altirra, hue 5 the fixed point). The
fix is one line, mirrored = (10 - hue) % 15, and its elegance is
the proof of safety: the mirror permutes the same fifteen hue
angles, so the RGB set the optimizer picks from is unchanged and
the renders come out pixel-identical to the approved corpus. The
preview PNGs regenerated BYTE-identical across the re-pin; only the
native bytes re-encode, now correct for real hardware. Goldens
re-pinned (suite 57/57 on the conversion tests), the probe's
embedded assets regenerated from the shipped pipeline instead of
the scratch hack, probe.xex rebuilt, build/arcimg amalgam
refreshed at 1.25.0.

## 2026-07-24: "We leave it as is." The C64 challenger round closes on status quo

Stefan reopened the C64 with his gut ("deriving from CPC is not the
CLEAN way") and closed it the same day with his eye: the corpus
stays derived from the frozen CPC, without a change, for the moment.
Between those two rulings sat a full challenger round, and its
knowledge is banked:

A direct-from-master C64 engine (the A8's intelligence through
Colodore and the cell solve) was built in the scratchpad and
iterated nine times against the two weak scenes. It genuinely won
image 8 (colour and luminance back) and image 1 (the crowded sky
calmed), and lost scenes 2 and 12 to the unported protection layer
(the moon rule, the big-cluster defense: the statue's head, the
textbook case). Not corpus-ready; parked with its lessons: the
masters carry painting grain that a 16-colour gamut amplifies into
checker; out-of-gamut forced picks must not diffuse their error
(the sky-dots disease, cured the A8 way); an empty candidate window
is the loyalty rule's most important customer.

The diagnosis that outlives the round: image 8's odd moon is a
PIGEONHOLE truth, not a bug. The CPC spends more blue-family inks
than Colodore has blue slots, so the injective usage-ordered map
sends the sky-glow ink to purple and the aurora's green to grey;
nothing chose that moon, it is what was left in the bag. A
salient-gated celestial repaint (white dome, cyan rim, local cells
only) was built and REJECTED by Stefan: the silhouette lost its
details; the treeline through the moon is the picture. RULED: the
derived corpus stands as is; most genuinely stunning. The
challenger and the repaint stay in the scratchpad for the day the
clean doctrine gets its full round, with Rabenstein's real art as
the argument that day may come.

## 2026-07-25: "Finally. Approved." The Plus/4 comes back vivid (arcimg 1.26.0)

The night that began with "where are the P4 pictures I liked so much"
ends with the corpus Stefan approved at last, and the road between
was archaeology, a false trail, and two measurements.

The archaeology: the outstanding Plus/4 he remembered was a promise,
not a file. His multicolour ruling was born in the same breath as the
C64 diffusion verdict ("if we get C64 right, this will look just as
fine on the Plus/4"), and the implementation delivered the format but
wired the pipeline from the CPC with the colour soul left behind. The
acceptance was lukewarm ("just little colours at times replaced by
much grey") and the gap surfaced three days later as a memory nobody
could find on disk. Lesson, paid in full: review renders belong in
arc_image/scratchpad, and a promise inside a ruling is a deliverable.

The measurements, both his: image 8's "square cut out of the moon"
diagnosed as a bankrupt cell (the CPC paints the pond reflection with
seven inks; two private colours plus two dark globals cannot hold
it), and "the colours a bit washed away" diagnosed by the palette
staircase probe on xplus4. His screenshot of that staircase measured
the truth: TED's hue nibble 0 is black PLUS the grey ladder
(chromatics start at 1: the shipped model had every hue one nibble
off, the A8 wheel disease again), saturation on hardware runs two to
three times the retired formula, and the luma ladder tops out
brighter. The formula, preview-grade by its own comment since wave 3,
is retired by the measured table.

Landed as arcimg 1.26.0, all of it probe-proven or approval-gated:
the measured TED palette (table, not formula), globals re-elected in
measured space, and the cell solve earned cell by cell under Stefan's
eye: SEED-AND-GROW free election for bankrupt jewel regions, COHERENCE
RELAXATION so smooth regions share pairs and dither flows across cell
borders. Production output pixel-identical to the approval set,
21/21; goldens re-pinned twice in one day (the first pin caught the
freeze gap the drift scare exposed); suite green; amalgam refreshed.

The P4 probe (picture display still buggy, colour clashes) now has a
trusted corpus to verify against, exactly the order Stefan ruled:
"there is a reason why I am asking for a proper corpus first."

## 2026-07-25: ARC<id>.TR4; the Model 4 learns its own disk's rules (arcimg 1.27.0)

Shawn Sijnstra's report from the real machine: TRSDOS caps a file
suffix at three characters and a filename must begin with a letter,
so the family convention <id>.TRSM4 cannot exist on the disk it was
made for. Stefan's proposal lands verbatim: the Model 4 ships
ARC<id>.TR4 (ARC9.TR4, ARC12.TR4, ...). The change is one naming
seam in arcimg plus renames: the .arc header id is authoritative by
design (part B of docs/08), so no interpreter, packer, or other
target changes; the bytes and digests are untouched. Corpus, probe
assets, and docs C.7 renamed in the same step; suite 129 green.

## 2026-07-25: the Plus/4 probe proven; the palette measured twice (arcimg 1.28.0)

The morning the P4 display round became a masterclass in instruments.
The probe's first pictures were "colour clashes everywhere", and the
road to pixel-exact went through four purpose-built displays: the
palette staircase (which measured the TED gamut and, unknowingly, one
column off), the conventions quadrant probe (which proved the hues
read straight, the luminance nibbles read CROSSED, and the register
order), a hypothesis tournament scored against Stefan's screenshots
(hue minus one, the tell), and finally Stefan's own observation that
broke the case: "the clouds resolve into black instead of white.
That would need a massive hue shift and not just +1." It needed
none: hardware hue 0 is black at every luminance, so the staircase's
first column was invisible on the black canvas and the whole measured
table anchored one nibble left. Black on black is invisible: the
measurement lesson of the wave, paid in a corpus.

Landed as arcimg 1.28.0: the re-anchored table (nibble 0 black by
law, greys at 1, the documented order), the crossed luminance nibble
in pack and render (invariant renders, hardware-true bytes), corpus
reconverted 20/21 pixel-identical to the approved set (image 19
drifts 16 pixels), goldens re-pinned a third time in two days, and
the probe verified pixel-exact on VICE: mode 9 against its own truth
(fit 1.000 measured), mode 12 and picture 12 against the corpus by
Stefan's eye. docs/08 gains C.9 with every truth the probes paid
for, IN THE SAME ARC as the probe, the discipline his call-out
restored. Open items: the border register's byte order (unverified,
probe paints it black where both readings agree) and a waitkey
re-cycle check.

## 2026-07-25: "Identical now." The slice doctrine; a reopened close (arcimg 1.29.0)

I closed the P4 probe round on my own verdict and Stefan reopened it
within the hour, correctly and sharply: the mode-9 picture on screen
did not match mode 12, I had placed a "truth" render in his review
folder without showing him, and I had promoted "the probe matches the
file" into "the converter is right" without running the one
comparison that mattered. His words stand in the record: he is the
judge on visuals, P4 is done when he says so, and that close was not
professional. The measurement then vindicated his eye completely:
the independently-converted mode-9 test file elected the SAME two
global colours in OPPOSITE roles (his black-vs-blue canvas
observation from a day earlier, filed by me as cosmetic) and
brighter cell pairs around the moon and treetops.

RULED, both barrels: inherited consistency as converter doctrine (a
mode 9 that is a different version of the picture is a quality
issue) and the test pair rebuilt structurally: arcimg gains slice9,
which derives a mode-9 .arc as the TOP SLICE of the mode-12 native.
No second conversion happens, so nothing can diverge: registers
identical, every shared row and cell byte-identical, verified in
bytes and then on the emulator by Stefan: "identical now." The A8
and C64 test pairs await the same medicine on his go. Remaining
open on the P4 probe: the border register's byte order and a
waitkey re-cycle check, both logged in C.9.

## 2026-07-25: the slice doctrine goes family-wide (A8 and C64 pairs)

Stefan's word: the sliced pairs will be identical on the shared
pixels by construction, no re-evaluation needed. Done: 9.C64 and
9.A8 are now top slices of their mode-12 conversions, byte-verified
(registers, shared rows, attribute cells, the A8 line table). The
C64 pair was also STALE, predating the frozen from-CPC corpus; its
mode-12 asset is now the current corpus conversion of the same
picture. Both probe binaries rebuilt; screen re-verification
deferred per his ruling and will happen incidentally at next launch.

## 2026-07-25: the P4 residuals close; the register file speaks one language

The border register probe: display off, the whole screen is the
border, three planted values a keypress apart. Stefan's three words
(army green, white, salmon) decode unanimously as (luma << 4) | hue
on the measured table, so every TED colour register speaks the same
convention; and his "army green" quietly corrected the probe's own
prediction comment, which still carried a stale hue name from the
shifted table era. The earlier black-border anomaly in the staircase
build stays unexplained but superseded: a clean instrument outranks
a dirty data point. The waitkey wedge is closed as an artifact of
the corrupted test build: the cycle runs around cleanly on both the
border probe and the picture probe. The Plus/4 is whole: corpus,
codec, palette, probe, doctrine, chapter.

## CHECKPOINT: the MSX1 pickup point (written 2026-07-25, other work intervenes)

WHERE THE WAVE STANDS. Proven on their emulators with docs/08
chapters: DOS, ST, Amiga, C64 (C.4), ZX+3 blueprint in progress
(C.5 conversion ready, hand-polish loop first-class), CPC (C.6,
frozen trunk), TRS-80 Model 4 (C.7, ARC<id>.TR4 naming), Atari
8-bit (C.8), Plus/4 (C.9). Remaining: MSX1 (this pickup), MSX2,
then the Spectrum DERIVING FROM MSX1 (ruled; the historical
Rabenstein Spectrum art was Plus/4-based, and density wants a
richer parent), Agon Light RLE for Shawn, then Apple II / Next /
MEGA65 / VDC as their waves come.

MSX1 FACTS. Target id 7, tag MS1, 256 wide, modes 256x72 / 256x96.
The target class exists (pack/unpack/render/pattern); NO CONVERTER
YET (_CONVERTERS has no MS1 entry: the round builds it). Screen 2
of the TMS9918: fixed 15-colour palette plus transparent, and the
colour section pairs a foreground and background nibble PER 8x1
PIXEL ROW SLIVER, the tightest clash cell in the family. The
DERIVATION ROUTE IS UNDECIDED: from the frozen CPC like C64/P4, or
direct from master like the A8. Stefan rules at round start; the
gut precedents both exist (P4 loves its CPC parent, the A8 needed
the master).

THE EARNED WORKFLOW, instrument order, no step skipped:

1. PALETTE STAIRCASE FIRST, on a canvas that makes absences
   visible (hardware black on a black canvas anchored the first
   TED measurement one nibble off and cost a corpus). Validate the
   anchoring: count the ladders, demand the grey ladder climb,
   reject impostors (a constant white column once passed a weak
   validator). The emulator renders the truth; arcimg's model is
   preview-grade until measured. ASK STEFAN WHICH EMULATOR AND
   WHERE before launching anything.
2. CONVENTIONS PROBE SECOND: distinct values in every nibble
   position (the P4 quadrants: same-value nibbles are blind to
   order), registers planted with values whose candidate decodes
   differ loudly (army green / white / salmon named the border's
   convention in three words). For MSX1: the FG/BG nibble order in
   the colour table is exactly this class of question.
3. CONVERSION ROUND with the measured palette, corpus judged by
   STEFAN's eye scene by scene; his taste doctrines: many colours
   is the promise and grey is the disease; calm skies (the masters
   carry painting grain that coarse palettes amplify into checker;
   deadzones and guarded diffusion, never global smoothing); tint
   loyalty (chromatic content is not housed by grey); jewels need
   local intelligence (seed-and-grow), smooth regions need
   coherence (relaxation); protected clusters (the moon rule, the
   statue's head) are not optional.
4. PROBE LAST, against the trusted corpus only: sliced test pair
   (arcimg slice9: mode 9 IS the top slice of mode 12, Stefan's
   ruling: a different version is a quality issue), display memory
   ABOVE the program (two machines paid for that), conformance
   diffs with fit scores, and the docs/08 chapter lands IN THE
   SAME ARC as the probe.

THE PROFESSIONAL BASIS, restated because it was earned the hard
way: Stefan shoots the screenshots (they land as Desktop files I
read and measure); my eye gates nothing and closes nothing; a
round is done WHEN STEFAN SAYS SO; rulings and their reasons go
to PROGRESS in the same commit; goldens freeze what he approves,
immediately, so nothing can drift silently again.

## 2026-07-25: Shawn reads the blueprint closer than its author

Shawn Sijnstra, integrating the Model 4 loader, asked why probe.asm
stores the header height in `rows` and never reads it. He is right:
dead code from the sketch phase, in the reference blueprint of all
places. The honest answer went back through Stefan (the loader needs
no height: the ZX0 stream self-terminates, the probe pre-clears all
240 rows; an interpreter reads the header height for its SCREEN
MODEL, not its decode) and the probe source now says exactly that
where the dead store used to sit, with Shawn credited. Rebuilt with
sjasmplus, zero errors; re-verification on trs80gp rides the next
launch.

## 2026-07-25: Charles asks for varied replies; the compiler owed him a crash fix (arcc 1.3.28)

Charles Moore Jr.: "can we use VARY in a topic response?" The
language already said yes (a topic body is an ordinary statement
block, docs/01, and reply is a statement, so reply-framed variants
compose with vary's or-groups exactly as written), but the compiler
said TypeError: sema's owner walk checked property blocks, handlers,
grains, and ambiences, and never topic bodies, so a vary in a topic
never received its state slot and lowering crashed on the missing
offset. One branch in sema fixes it; the regression test asks a
lamp-keeper about bees three times and watches the loop wrap. Suite
1041 green; arcc 1.3.28; the answer to Charles is the syntax he
hoped for, no new feature needed.

## 2026-07-25: the example debt paid, and paying it found a Cosmos bug (Cosmos 1.2.24)

Stefan's call-out, deserved: vary and foresight shipped as
fundamentals with ZERO example code, against the standing practice
that every fundamental lands with examples. Paid today with four:
vary.storyarc (all four policies, or-groups, and varied replies in a
conversation topic, the form Charles asked for), foresight.storyarc
(the ferry fare: coin repair, door repair, the glass display case,
the honest lock, the knowledge rule), yes-no.storyarc (typed answers
with when-guarded questions, Ichiro's second feature), and
press-any-key.storyarc (read_key as the classic gate and as a value,
Ichiro's ask; READ and PRESS turned out to be standard synonyms and
the compiler's own notes taught the canonical form).

And the practice proved itself the day it was honored: WRITING the
foresight example exposed a real gap. The direct TAKE of a thing
visible in a closed CLEAR container refused ("You'll have to open it
first") while the give-chain repaired the identical shape. Root: the
opaque seen-memory path repairs at run_turn's shut_in seam, but clear
contents arrive through ordinary scope and hit the take handler's
why-4 branch, which had no seam at all. Fixed in the house pattern:
take_sealed_refused, a seam block whose default is the exact old
refusal and whose foresight override opens on the promise discipline.
Regression tests both ways; suite 1044 green; the size ledger pays
+44 to +48 everywhere for the seam, dated and reasoned, and the
completeness gate demanded the new examples join it, which they did.

## 2026-07-25: press_any_key, designed by Stefan; a process correction (Cosmos 1.2.25)

Ichiro Ota asked for a way to wait on a keypress, and I answered one
reading of an ambiguous question without waiting for Stefan: the
correction stands in the record. His reading, three manners: the
classic pacing gate between paragraphs (the flagship intro's manner),
the in-game custom prompt, and catching a SPECIFIC key with refusal
and re-ask. His design for the first: a proper library helper, his
Inform PressAnyKey brought home as `press_any_key` (core), with the
prompt living in the LANGUAGE LAYER, not the helper: default "[...]",
his own convention from his games, convenient and translation-free,
overridable per story or pack like any message block. The packs are
complete language layers, so all three carry it. The example grew to
all three manners (the panel now names A and B, takes exactly those,
refuses the rest and asks again), docs/02 documents the gate among
the standard responses, and the Ichiro reply is REWRITTEN with full
context and standard verbs, awaiting Stefan's approval before it is
anything.

## 2026-07-25: four more examples; a parser gap surfaces on the way

The remaining example debt from the verbs overhaul, paid:
shiftable.storyarc (the tar barrel, pushed north with the player
following, the crane refusing), enhance-redefine.storyarc (look
gains UNDER, roll joins push, and a declared verb is replaced whole
with a new synonym riding along), consult-about.storyarc (the mining
gazetteer: topics on a BOOK, hits, the honest miss, the no-subject
ask, and LOOK UP X IN Y riding the same grammar), and
session-verbs.storyarc (VERSION mid-game, the coupled NOTIFY
enabled in on start and toggled by the player, the swear family
answering dryly). All compile clean, all smoke-tested through
dfrotz, all in the size gate.

FOUND ON THE WAY, for Stefan's ruling, untouched: a CUSTOM verb
with noun grammar answers a bare command with SILENCE and a
consumed move, where a standard verb asks "Push what?". General,
not a redefine artifact (a plain fresh verb behaves the same); the
missing-noun ask is evidently standard-verb machinery only. Silence
that eats a turn sits poorly next to the house rule that everything
answers; his call whether this becomes a round.

## CHECKPOINT for compaction (2026-07-25, afternoon): the half-kept overhaul

IMMEDIATE RESUME POINT, ruled urgent by Stefan: "What you saw with
verbs needs urgently fixing, otherwise we kept only half of the
verbs overhaul." A CUSTOM verb with noun grammar answers a bare
command with SILENCE and a consumed move; a standard verb asks
"Push what?". General, not a redefine artifact.

Reproduction (scratch, one minute): a game with
    verb "wibble"
        wib noun
    thing stone ... on wib -> say
Typing WIBBLE alone: no output, Moves ticks. Typing PUSH alone in
any game: "Push what?".

Where to look, mapped before compaction: the ask text is built in
english.prelude around lines 1113-1128 (the "<Verb> what?" builder,
say " what?"); parser.prelude line ~238 documents the intent for
the positional path: "An EMPTY slot stays nothing and the action
asks its own question (dig what?)", which is exactly what does NOT
happen for custom verbs, so either the positional/table path skips
the ask seam standard verbs reach, or the flag-model grammar wires
the ask per standard action only. tests/test_missing_noun.py holds
the neighbouring coverage; the done-test is a bare custom verb
asking like a standard one, a regression test beside those, and the
enhance-redefine example regaining a bare-wave try line once the
ask lands.

STATE OTHERWISE: Ichiro's reply accepted and out; press_any_key
shipped (Cosmos 1.2.25) with the [...] prompt in all three language
layers; the sealed-take seam shipped (Cosmos 1.2.24); the example
debt is FULLY PAID, eight showcases, all in the size gate. The
retro wave rests at the MSX1 pickup checkpoint (commit 46018cf),
and PARKED IN CASCADE BEHIND IT, ruled today: the SPECTRUM (derives
from MSX1) and AGON LIGHT RLE for Shawn both wait on MSX1's round;
they are part of that checkpoint's order, not independent items.
The custom-verb fix comes first, then the cascade resumes at MSX1.

## The one honest ask (2026-07-26): the verbs overhaul made whole

Resumed exactly at the compaction checkpoint, and Stefan reshaped the fix
before a line was written. The bug was that a CUSTOM verb answered a bare
command with silence while a standard verb asked "Push what?"; his ruling
went deeper: the "what?" family itself is wrong. "Listen what?" is broken
English, and "Dance what?" guesses a role the grammar never promised, the
line could as well have wanted WITH WHOM or ON THE GRASS. His replacement,
a phrase crafted from years of developing player experience in IF: "The
verb dance requires you to be more specific." True for every incomplete
command, promising nothing it cannot know, and teaching the player exactly
what to do. Ruled to apply to partial fills too (PUT LAMP), and to every
existing plain-what ask in the library.

Two more rulings shaped the build. The echo must be the word AS TYPED, at
full length: "the verb disintegr wants..." (the dictionary's nine-character
cap) "is a bug, not going to be accepted, neither by me nor the community",
so the ask spells the verb from the text buffer, where the cap never shows.
And the seam is author-facing: the typed word is readable in handlers, so
one action family can answer each synonym in its own voice, named
verb_trigger by Stefan ("I don't want to be like Inform", against the
obvious verb_word).

What landed: the ask moved into the loop, one central refusal before any
handler, no move consumed, fed by the verb's own grammar (a new requirement
bit pair in the dictionary's grammar byte, and the empty-slot mark in the
positional matcher). Grammar now states what is complete: a verb with a
declared bare line owns its bare command (STAND gained the bare line its
handler always honored), everything else asks. The forty-odd per-handler
ask stanzas were deleted along with msg_put_where and msg_to_whom, and
every example shrank 260 to 444 bytes, repriced down in the size gate to
lock the win. All three language layers carry the new line natively (Das
Verb nimm verlangt eine genauere Angabe. / El verbo coge requiere más
precisión.). verb_trigger compares against a quoted verb word, checked at
compile time (an undeclared word is an error, not a test that can never be
true), survives AGAIN, reads 0 inside perform, and costs nothing in a game
that never reads it (the any_verb_read fold). arcc 1.3.29, Cosmos 1.2.26,
suite at 1204 green, the enhance-redefine example now shows both seams.

## Exits validated at compile time (2026-07-26): Ichiro's field report

Ichiro Ota asked whether it is expected that the compiler accepts an exit
naming a room that does not exist, failing only at runtime with "There's
no exit in that direction." It was not expected, and reproduction showed
the hole ran deeper than reported: an exit naming a plain THING (a
one-character typo away from any room name) compiled clean and walked the
player INSIDE the thing, a pitch-black soft-lock with no way out. The
cause was a silent fallback in the object-table fill (an unknown name
became 0, a known-but-wrong name became whatever object it was) with no
sema validation at all.

Stefan approved the proposed check as designed: every named exit target
is validated in sema, after the properties pass fills the rooms and the
kind chains resolve. Legal targets are exactly what the docs always
promised, a declared room, a door-kind thing (east oak_door), or a
computed exit block, with `nothing` staying legal as the explicit
no-exit. Everything else is a compile error naming the room, the
direction, and the offender ("room 'hall': exit 'south' points at 'lamp',
which is neither a room nor a door"). Sanctioned consequence, ruled by
Stefan with the proposal: any adopter abusing exit-to-enterable-thing as
a secret walk-in stops compiling; the blessed routes are enter or an
`on go` override. Compile-time only, zero story bytes. arcc 1.3.30,
suite at 1208 green.

## ENTER reaches the catch-all (2026-07-26): the one-word bug

A field report: a thing's `on other` never saw the ENTER action; the
library's "You can't get inside" answered first, while PUSH and CLIMB
were caught as documented. The cause was one identifier. `enter` is two
things sharing a name, the arrival event on a room and the ENTER verb on
a thing, and the react generator already computes the split per object;
its catch-all branch iterated the module-level event set instead of that
per-object one, so every catch-all skipped the enter action, things
included. The fix is the parameter that was already there (event_names
for _EVENT_NAMES), a room's arrival still bypasses its catch-all, and
the regression test pins both sides. arcc 1.3.31, suite at 1210 green.

## Restless, and the timers learn to stop (2026-07-26): Stefan's design

Charles asked for `on each_turn` to keep working out of scope (an NPC
acting in the background). My first answer proposed the classic daemon
as a second concept beside each_turn, the Inform 6 split; Stefan
rejected it on the ground statement: "Arcturus is not about 40 years of
lineage... the author expresses what they want to do and it works
magically and out of the box." His design, refined across the
discussion and better than the proposal it replaced: an object marked
`restless` is a background performer whose each_turn fires every turn
wherever it is, and the SYSTEM decides audibility. The principle in one
sentence, now in the docs verbatim: work follows the performer's
nature, prose follows scope.

What landed: the `restless` attribute (declare it, or arm and disarm at
runtime with `now guard is restless` / `not restless`, no declaration
needed, per Stefan's ruling that any library property works that way);
the performer walk in the turn loop; every restless firing buffered
through z-machine output stream 3 and replayed when the performer is in
scope at either end of its turn, so arrivals and departures are heard
and wholly-offstage turns are silence (the either-end rule fell out of
the example: a pre-firing snapshot swallowed arrival lines, and the
walkthrough caught it). Nothing fires twice, `when` guards still gate,
and a game with no restless object is byte-identical, mute buffer and
all.

The timers, from the same discussion: Stefan asked how a running timer
stops, proposed the spelled-out form, and ruled the full triple is the
identity when I suggested stopping by block name alone ("you could have
two timers running that make use of the same block. You need to be
specific"). So `stop after/every N turns do block` disarms exactly the
timer it names (the schedule now keeps the armed interval, a one-shot's
negated, so a half-burnt fuse still answers to its number), a mismatch
is a clean no-op, a stop for a block nothing ever arms gets a compile
note, and `stop all timers` (Stefan's addition) clears the stage for a
scene break. One engine fact surfaced during the build and flagged for
a later ruling if wanted: the schedule is one slot per block, so two
CONCURRENT timers on one block cannot exist today; re-arming resets,
never duplicates. The daemons-and-timers example gained the workshop,
the restless clockwork apprentice on its rounds, and TURN OFF CLOCK;
arcc 1.3.32, Cosmos 1.2.27, suite at 1216 green.

## The grain warning Charles never saw (2026-07-26): two real gaps

Stefan pressed the loose end from the grains discussion: Charles was on
arcc 1.3.27, a build that already carried the word-split note, and still
compiled in silence. The reconstruction of his pasted snippet warns
loudly on 1.3.27 itself (verified against the shipped binary from git),
so his real code has a different shape, and hunting for shapes that
escape found two genuine bugs.

First, the outside-body attach form (`foyer.grains`, documented in
docs/01 section 14) was DEAD: parsed and checked, never merged into the
owner, so the grains did not exist and their words never reached the
dictionary. Fixed with the one missing _add_grain call; attached grains
now behave exactly like an inline block's and fall under the lint.

Second, the lint was per-owner only, and the shape that reproduces
Charles's exact symptom is CROSS-owner: the room answering a word with
one grain and a scenery thing standing in that room answering it with
another. First declared wins, the second is dead where they share
scope, examine works and take falls to the scenery default, and nothing
said so. The lint now computes each owner's static home rooms (its own
room, the room its `in` chain reaches, its spans) and notes a shared
word wherever homes overlap, while the documented cross-room reuse
(steps in the hallway, steps in the cellar) stays quiet. arcc 1.3.33,
suite at 1220 green.

## The demo becomes the playground (2026-07-26): Shawn's request

Shawn Sijnstra's TRS-80 Model 4 interpreter drew the band this week, the
first adopter-built machine to take an .arc file to the glass, and his
request followed: the two-room demo proves an interpreter is off the
ground, but authors need "something bigger for more thorough testing".
Stefan's brief, from their exchange: everything arc_image is supposed to
do. Darkness and the black image, an event-driven picture change,
traversal, and Shawn's own addition, proof that the clear-with-0 works.

The Demo of Rabenstein is now a nine-room walk exercising the whole
contract: the Forsaken Path (8) to the Churchyard (1), a Burial Crypt
that is dark (the new all-black 21, converted for all nine proven
targets) until the storm lantern comes down and reveals the tombs (3),
the Manor Garden (12), an Open Lawn with NO picture so the band must
clear, the Stable (14), Manor Hall (16), the Library where CLOSE
CURTAINS repaints 17 to 20 in place (Stefan's pick), and the Bedchamber
where SLEEP swaps night (7) for morning (9) and back, repeatable. The
source header carries the tester's walkthrough with the expected
picture id at every step, and the suite now pins that exact draw
sequence, LOOK-adds-no-draws included, so the contract is enforced by
machine, not by eye. docs/07 names the demo as the interpreter author's
test game; the .arcres repacked with all eleven scenes; the build/
bundle refreshed. Suite at 1221 green.

## The demo diet (2026-07-26, addendum): the Director's Cut ruling

Stefan cut the nine-room walk down before it ever shipped wide: half the
Rabenstein corpus in a public demo would spend scenes he is saving for a
planned Curse of Rabenstein Director's Cut, and the brief (test every
feature) never needed the spectacle. The demo is four rooms now, and the
library carries three tests alone: dark until the lantern arrives (the
all-black 21), the reveal (17), and the curtains repainting 17 to 20 in
place, repeatably. Assets exposed: only 8 and 1 (public since the
two-room demo), the 17/20 pair, and the black 21; scenes 3, 7, 9, 12,
14, and 16 go back in the vault. The pinned draw-sequence test now reads
[0, 8, 1, 0, 21, 0, 1, 0, 17, 20, 17], LOOKs drawing nothing. Suite at
1221 green.

## The lawn, the bedchamber, and the discretion ruling (2026-07-26)

Stefan playtested the reshaped demo and closed the band-release debate
with a discovery: Actaea already does what he wanted. Enter the
pictureless lawn and the window gives the whole screen to prose; walk on
and the band re-bases. No new opcode, no placeholder machinery, no
GRAPHICS verbs needed to solve the space problem, and his C64 reasoning
sealed the retro side: a fixed-screen interpreter holds no text backing
store, so released rows would sit empty, and keeping the band is the
hardware's honest shape. The ruling, now in docs/08: what a clear MEANS
is fixed (id 0 takes the picture down, always); what it LOOKS like is
the interpreter author's discretion, blank reserved band on fixed
screens, released rows on modern windows, both conformant, and a game
must assume neither. Every shipped interpreter (Actaea, Shawn's Model 4,
Gargoyle, with Parchment in flight) is already correct under it.

His playtest also caught two demo sins: the lawn's description was a
misleading meta-tease (it read like a light puzzle), and the library's
picture shows daylight through the window in a game set at night. Both
fixed by taking the option Stefan had suggested in the first place: the
event room is the bedchamber, dark until the lantern arrives, and SLEEP
swaps night (7) for morning (9) and back, time passing being the one
event that makes a day-for-night change honest. The library pair 17/20
goes back in the vault for the Director's Cut; the pinned sequence is
now [0, 8, 1, 0, 21, 0, 1, 0, 7, 9, 7]. Blorbenstein (Stefan's name)
replaced return-to-rabenstein as the Blorb twin of the same demo. Also
on the board from the same session: Actaea does not scale the picture
when the window goes fullscreen (todo). Suite at 1221 green.

## The night ends properly (2026-07-27): three fixes from one playtest

Stefan's second pass over the demo produced three rulings, each landed.

The win state: sleep is the demo's last step, and walking back out into
a night you just slept away was a broken clock. Leaving the bedchamber
in the morning now ends the story ("You have survived the night of
Rabenstein"), the finish staying final as won games do. The night
description also tells the player SLEEP is the way out of it, since
nobody reads a demo's source header. And the darkness scene is dark
GREY now, not black, so the band stays distinguishable from a black
game background (grey 73, the ST-exact value, with one black paper
pixel and one white ink pixel in the corner so the Atari ST text
contract holds: slot 15 must carry readable ink even while darkness
shows); the ZX Spectrum and TRS-80, whose palettes hold no grey, keep
honest black.

The Cosmos bug he caught: LIGHT LANTERN in the dark answered only the
lantern's line, leaving the player to type LOOK for the room they could
suddenly see. The light watch fixes it: a turn that lifts darkness
without moving describes the room (picture and all), a turn that kills
the light says where that leaves you, doorways keep their single
description (arrive already speaks), and always-lit games stay
byte-identical, the snapshot riding the spent undo local behind the
any_dark fold. Cosmos 1.3.1.

The Actaea bug, fixed on his "fix now": the band scaled to the 80-cell
grid, never to the real window, so fullscreen left the picture small;
and the mode-rows clamp silently CROPPED the art's bottom at any font
whose cells are not 8-pixel squares. The band now scales to the
canvas's true width, keeps the picture's aspect (height follows, no
crop), centers it, and repaints on resize with the dedup keyed on
width. Actaea 1.3.5. Suite at 1224 green.

## The bar learns the window's width (2026-07-27): Actaea 1.3.6

Stefan's next catch: the GUI status bar stayed 80 cells wide in a
maximized window. The console front-end had this exact fix already (a
resize re-stamps the header and re-widths the cell grid; the game paints
its bar across the new width one command later, the v5 way, since v5 has
no resize interrupt); the GUI simply never called the same machinery and
reported a constant 80 columns. Now the window's real width drives the
column count on every resize, through the identical vm.screen_resized
path, and the grid and band repaint. His fullscreen eye is the final
gate, as ever.

## The welcome (2026-07-27): an intro instead of a layout tweak

Stefan noticed the banner sits flush under the status bar and asked
whether something broke. The A/B against the real arcc 1.3.27 binary
from git says no: the no-gap boot has been the behavior since the bar
learned to rise before on-start text (2026-07-18, his own
screenshot-diffed start-screen design). His fix is better than a
layout tweak anyway: the demo now opens with a short welcome that
tells the player what the walk shows and to SLEEP when offered a bed,
framed by breathing lines, so the screen reads bar, breath, welcome,
breath, banner, breath, room. One honest note for a later ruling: the
loop's comment claims on-start text leaves a pending break that the
banner flushes into a separating blank, and nothing actually does
that; the demo sets its own blanks, and making the comment true
globally would touch every game's boot, so it waits for Stefan.

## The mode 9 twin (2026-07-27): Cloak of Darkness dressed for arc_image

Shawn's other request: a game to test mode 9, the Arthur band. Stefan's
answer: Cloak of Darkness, whose plot IS the darkness test. The
conformance port stays untouched; a new examples/arc_image twin carries
Stefan's four 320x72 scenes (foyer, cloakroom, bar lit, bar dark), with
the bar's own dark painting standing as arc_image_dark, so carrying the
cloak into the bar shows the dark scene and hanging it on the hook
reveals the lit bar on the next visit. No new machinery: the game's own
light logic drives every draw. Ids numbered through arcimg prep from
Stefan's named masters; cloak-of-darkness.arcres beside the z5; retro
conversions for all nine proven targets under arc_image/cloak/ (Shawn's
TRSM4 files as ARC1..ARC4.TR4). The suite pins the walkthrough with the
mode on every draw: [(0,9),(1,9),(4,9),(1,9),(2,9),(1,9),(3,9)] and the
win. Between Rabenstein (mode 12) and this, an interpreter author
exercises both band shapes. Suite at 1225 green.

## The spacing rule (2026-07-27): nothing flush under the bar, ever

Stefan saw the cloak demo boot with the intro jammed against the status
bar and the banner jammed against the intro, and ruled the general law:
NOTHING starts flush under the status bar, and on-start text and the
banner breathe apart. Cosmos 1.3.2 makes it structural: two pending
paragraph marks in the boot sequence, one after screen_ready and one
after the on-start firing, and since par is a flag rather than a
counter they collapse to exactly one blank wherever text actually
follows. A silent start reads bar, breath, banner; an intro gets one
blank on each side; a bare screen simply leads with a blank. This
supersedes the July 18 flush-title look and finally makes true what a
loop comment had only claimed. The demo's hand-made blank lines came
out again (the library breathes now), +8 bytes per game repriced, and
two tests that had the old layout hard-coded (one of them as the
literal escape code for a cursor move to row 2) were updated to the
law rather than the layout. Suite at 1225 green.

## EXIT ENGINE (2026-07-27): the last undeclared line of the boarding family

Charles's report, and Stefan's exasperation with it ("how often do we
have to fix this stupid entering and leaving"): EXIT ENGINE and LEAVE
ENGINE answered "You lost me after that." The embarrassing part: the
exit handler has carried a full noun path all along, its own comment
citing "the author's exit noun grammar", but the STANDARD exit/leave
verb never declared that line, so only authors who declared their own
(stand did) ever reached it; GET OUT OF X only worked because it
arrives through the take_off remap instead. One grammar line in each
pack fixes it (German also gains verlasse/verlassen, its natural
transitive), and the structural answer to the exasperation is
tests/test_boarding_matrix.py: every way in crossed with every way out,
55 combinations pinned, so the next gap in this family fails a test
instead of reaching an adopter. Cosmos 1.3.3, suite at 1280 green.

## CHECKPOINT for compaction (2026-07-27): the queue is not drained

IMMEDIATE RESUME POINT: Charles's ORIGINAL ouch-but-true report. Stefan
has confirmed it IS true and that RESTLESS was not it; it has been
announced repeatedly across two days and never yet stated, and Stefan
pastes it right after this compaction. The support queue stays open;
Charles may also come back with the daemons-and-timers example result
Stefan asked him to run (if his test method was watching offstage prose,
the correct answer is the muting: work happens, prose only in scope, the
tally-counter snippet already drafted for him).

THEN, IN ORDER: the B8 polish block (the publisher deadline), three
steps ruled by Stefan and recorded in the port's own log. After B8:
the arc_image probe cascade at the MSX1 pickup checkpoint (commit
46018cf), then Spectrum deriving from MSX1, then the Agon Light RLE
for Shawn, in that order.

STATE: arcc 1.3.33, Cosmos 1.3.3, Actaea 1.3.6, arcimg 1.29.0, suite at
1280 green, everything pushed through d7ad697 (pushing after commit is
standing practice now). The last two days landed: the one honest ask
and verb_trigger (the verbs overhaul completed); exit-target validation
at compile time; ENTER reaching thing catch-alls; restless performers
with the mute buffer and the either-end rule; timer stops by exact
triple plus stop all timers; the grains outside-attach brought to life
and the co-located-owner lint; the Rabenstein demo as the interpreter
author's test game (win state, welcome intro, grey darkness 21 with the
ST ink contract, pinned draw sequences); Blorbenstein; the mode 9 Cloak
twin with assets under arc_image/cloak/; the id-0 discretion ruling in
docs/08; the boot spacing rule (nothing flush under the bar); the light
watch (light lifting darkness describes the room); EXIT ENGINE fixed
with the 55-combination boarding matrix pinned; Actaea fullscreen band
scaling and bar width. Stefan's eye still owed on the Actaea fullscreen
behavior and both demos on real glass; Shawn has the two-demos reply.
Parked ideas, not commitments: GRAPHICS ON/OFF verbs (superseded by the
discretion ruling unless Stefan revives them) and the --no-images
compiler switch (endorsed in discussion, unbuilt).

## Checkpoint addendum (2026-07-27): one answer, one new bug

Stefan asked whether RESTLESS works through kind inheritance. Verified:
yes, completely (kind-declared restless seeds the instance bit, offstage
work happens with prose muted, in-scope speech normal; a conditional
counter proved the offstage work). Charles's mover kind can carry it.

Found in the same dig, OPEN BUG for after compaction: ${name}
interpolation resolves differently than expressions. Repro: a global
written from a KIND handler (`change paces to paces + 1` in a kind's on
each_turn) reads correctly in expressions (`if paces > 1` is true) but
`say "${paces}"` prints EMPTY from a free handler. Suspicion: the
interpolation's name resolution prefers a property (of noun, which is
nothing) once the name has been seen in kind context, while expression
resolution finds the global. Also noted while probing: ${s} silently
means the direction word s (south), a trap when a local is named s.

## 2026-07-27: the ${} interpolation bug was a false alarm

Investigated first thing after compaction, at Stefan's call. The logged
"open bug" (a global written from a kind handler printing empty through
${...} while expressions read it fine) does not exist. Root cause: the
probe itself. The probe embedded the game source in a double-quoted
shell string, and the shell expanded ${paces} to an empty string before
the compiler ever saw it, so the game literally compiled say "count
end". Re-run with the source in a file, everything is correct:

- ${paces}, a global written from a kind's on each_turn, prints
  correctly from a free handler (interpolation and expression reads
  agree; there is one resolution path, not two).
- ${s} with a declared global named s prints its value.
- ${s} with no declaration is a clean compile error, "unknown name
  's'"; there is no silent fallback to the direction word s.

No compiler change, no version bump. The lesson is probe hygiene, not
language: never pass ${...} game source through a double-quoted shell
string; use a file or a single-quoted heredoc.

## 2026-07-27: the Arcturus Handbook (Stefan's ruling, Charles's report)

Charles's ouch-but-true report, confirmed by Stefan: the standard-verb
list in 02 section 11 promised "the action a handler matches" and then
never named one action; TAKE OFF's action is take_off but TALK TO's is
talk, so guessing is impossible and he had to dig through
actions.prelude. And the 01/02 split itself made him flip documents
constantly for information that is one subject to an author.

Stefan's ruling: merge. The way the Inform Designer's Manual reads,
syntax first, then the library; granules fold in too. The name is his:
the Arcturus Handbook. docs/01-arcturus-handbook.md now holds Part I
the language (the former 01), Part II Cosmos and the parser (the
former 02), Part III the granules (the former 05). Each part keeps the
section numbering of the document it absorbed, so every historic "02
section 8" citation maps one-to-one to "Part II section 8"; the
roughly 340 references across code comments, tests, examples, and
cosmos were swept in the same commit, and the old three files are
retired. 00, 03, 04, 06, 07, 08 stay separate: design records, not
the manual.

Part II section 11 is rewritten the way Charles needed it: every entry
leads with the action identifier a handler matches, the player words
follow, and the unguessables are called out (READ is examine, LIGHT is
switch_on, TALK TO is talk). Appendix B is regenerated faithfully from
english.prelude and is now complete (the old table was stale: it
listed verb words that do not exist, and missed half the standard
set). Accuracy findings fixed in the same pass: SEARCH was documented
as core but lives in extendedverbs (the doc now says so); the claimed
verbose-or-brief toggle does not exist in Cosmos and the claim is
dropped, WITH AN OPEN QUESTION for Stefan: was that a feature 02
promised that we should build, or a leftover to stay dropped?

arcc 1.3.34, Cosmos 1.3.4 (prelude comments now cite the handbook),
both amalgams regenerated, README quickstart table refreshed, suite
1280 green.

## 2026-07-27: verbose/brief ruled out (Stefan)

The open question from the handbook pass is closed: the old 02's
"verbose-or-brief toggle" was thrown out intentionally, not forgotten.
Stefan sees little value in it. The claim stays dropped; nothing gets
built.

## 2026-07-27: restless holds; the debug UNMUTE verb; voicing offstage

Charles pushed back on restless itself: he wants a raw daemon, each_turn
firing everywhere with prose unmuted, "up to the author to worry about"
the consequences. Stefan's ruling: no daemon route, we stand with our
design until proven wrong. The author is taken by the hand on purpose
(Rubin: the listener doesn't know what he wants), and the deeper reason
is narrative correctness, not just the C64: an object cannot narrate
itself from a place the player is not standing, because the right words
depend on where the player is. The design also feeds the future NPC
engine. What Charles missed is that each_turn already differs by
attachment, all three documented in the handbook (Part II section 13):
free rules fire every turn and always speak (the "daemon that voices"
he asked for already exists), a room's fires only while the player is
inside, an object's while in scope, with restless extending the WORK
globally while prose stays scoped.

Two things were genuinely owed and both landed:

- The debug granule's UNMUTE verb (Charles's practical point: muting
  eats the say lines you sprinkle through a handler while debugging).
  UNMUTE lets every offstage voice through, each pulse tagged
  [performer name] so you can tell who speaks from where; silent
  workers never print a bare tag; UNMUTE toggles back. Implemented as
  the granule overriding fire_restless (the same-name override chain
  working exactly as designed); zero cost unsummoned.
- The handbook teaches VOICING AN OFFSTAGE EVENT (Part II section 13):
  the performer does the work restless and silent, a free rule (the
  narrator, standing where the player stands) voices the state the
  work left behind. The belfry bell is the worked example.

Also triaged from the same exchange: "a catalog name cannot start with
a number" is not a bug. Names are identifiers, identifiers begin with a
letter (handbook Part I section 2), and the compiler already says it
cleanly and precisely: "error: expected a catalog name, got 3", with
file, line, and column, same wording as every declaration.

Open question held for Stefan: a mass stop for performers (the stop all
timers analogue). Claude's recommendation: not needed; performers are
named, declared state on visible objects (now X is not restless, one
per line, reads as prose), unlike the anonymous schedule slots that
made stop all timers necessary; a core sweep loop would cost every
game against pay-for-use. Skip until a real game asks.

arcc 1.3.35, Cosmos 1.3.5, amalgams regenerated, suite 1282 green.

## 2026-07-27: name_contents and the author's toolkit (Ichiro's report)

Ichiro Ota asked for PunyInform's PrintContents. The honest audit: Cosmos
had the whole listing family (the "(contains ...)" suffix, "Inside you
find ...", the scenery paragraph, all knowledge-model aware) but no bare
composable list, and none of it documented; the comma-and-"and" loop was
written out three times per language layer. And Charles's parent_of
question minutes earlier was the same story: of 151 intrinsics, 91
author-visible names appeared nowhere in the handbook, parent_of among
them, only readable in compiler source.

Landed, on Stefan's go (toolkit plus the primitive, formatted like
PunyInform's, which was verified against the Puny source first: articles,
commas, "and", prefix only when non-empty, the caller told the count):

- name_contents(holder): the bare composable list, "a sabre and an iron
  axe", knowledge-filtered, marks seen, returns the count; zero prints
  nothing so the author's own sentence frames emptiness. listable_count
  beside it. The same contract list_worn already had: an established
  Cosmos idiom, now for contents.
- All three framers in all three languages now speak through the one
  shared loop: both example games shrink 84 bytes.
- The German scenery paragraph said the NOMINATIVE ("siehst du ein
  Dolch") where "siehst du" governs the accusative; the shared loop
  fixes it to "einen Dolch", pinned by test.
- The handbook gains Part II appendix C, THE AUTHOR'S TOOLKIT: the
  callable names beyond a game's own declarations (parent_of,
  object_count, in_scope, see_into, set_here, describe_room, the
  naming and listing family, the screen and session calls), one list,
  never sorted by which layer a name lives in, because three reports
  in a row proved authors cannot tell and should not have to. The
  substrate names are listed honestly beneath, with --extract and the
  design records as their reference. parent_of also documented inline
  where the object tree is defined.

arcc 1.3.36, Cosmos 1.3.6, amalgam regenerated, suite 1287 green.

## 2026-07-27: custom directions ride the spare four (Charles's report)

Charles wanted four new direction properties; the compiler refused. The
finding: the recipe already existed and nobody had ever said so. A game
declares its own words onto the four spare standard properties
(direction fore "widdershins", "wid"), and everything a direction has
comes along: bare typed word, abbreviation, exits, on go handlers, way.
The nautical granule's own header spells out that the properties are
standard and cost nothing; only the words are the granule's.

What the dig exposed and this lands: output leaked the CARRIER NAME.
dir_name and exit_name are documented as speaking a direction's
canonical word but printed the property identifier, so a rebound game
heard "You can only go fore from here" for widdershins (invisible on
the compass, where word and property coincide; doc wins, code fixed).
The canonical rule is most-specific-wins with vocabulary preserved: the
first declaration words a property, the game's own redeclaration takes
the canonical, and a granule merely ADDING vocabulary (nautical's ALOFT
riding up) never steals it. DirectionDecl now carries origin like a
block. Pinned by tests; the recipe documented in the handbook where
direction declarations live.

Charles's edited report (enhance verb "go" with go_to) triaged in the
same sitting: `go_to to noun` via enhance ALREADY WORKS (GO TO CHAIR
fires on go_to with the noun bound; his handler was likely on go, which
never carries a noun because go's slot IS the direction). Bare GO CHAIR
stays with the direction machinery: the go family's "Which way?" ask
fires before an enhanced bare-noun line is tried. OPEN DESIGN QUESTION
for Stefan, not built: should a failed direction read fall through to
later grammar lines before asking?

arcc 1.3.37, amalgam regenerated, suite 1290 green.

## 2026-07-28: custom directions, ruled and real

Stefan stopped the carrier-rebind recipe cold: "I don't think this is
the solution." He was right; the probe had just shown the leak (a
nautical game rebinding a compass property keeps the English word as a
ghost, NORTH still walking the rebound exit). The ruling that followed:
an author should be able to BUILD custom directions, full stop; the
flag is that each one consumes a property from the same stock as
everything else, the author's discretion against the Z-machine's hard
ceiling; unused, no cost, no burden.

Landed: a `direction` declaration naming a property outside the
standard set now CREATES that direction, first-class. Bare typed word,
abbreviations, exits, on go handlers, `if way is`, computed exits,
direction catalogs, the exit list speaking the declared word: all of it
comes along, and custom coexists with nautical (the collision case is
the pinned test). Registered in a sema pre-pass so source order never
matters; the fixed-set assumptions swept out of sema, lower, codegen,
and objects (the direction set is per-program now); a declaration
naming an EXISTING direction still just adds vocabulary, which is what
the nautical granule does. The cost surfaces exactly where Stefan
wanted it flagged: the arcc -s stats line ("properties 32/62" with two
customs walked). The old refusal test now pins the creation; a standard
non-direction property (desc) still cannot become one.

The handbook's carrier-rebind passage is replaced by the true feature.
The rebind of the spare four keeps working mechanically (it is the
add-vocabulary form), but it is no longer the story we tell.

arcc 1.3.38, amalgam regenerated, suite 1294 green.

## 2026-07-28: Glulx considered, parked (a thought experiment)

With Inform 7 adopters arriving, Stefan floated Glulx as a third target
beside z5/z8, to overcome any limitation. The joint conclusion: not
now. I7 lives on Glulx because I7's codegen outgrew the Z-machine, not
because the games did; Arcturus games compile lean (the B8 flagship, a
full commercial game, well under z8's 512K roof), so the limitation
Glulx cures is one no adopter is near. The real walls a monster game
would hit first are the table ceilings (63 properties, 48 attributes,
240 globals), all visible in arcc -s long before they pinch. And a
Glulx backend is a second codegen plus Glk plus an Actaea core, while
quietly forking the identity: today every Arcturus game can in
principle reach a C64; a Glulx-only game cannot.

REOPEN TRIGGER, ruled data-driven: a real adopter game whose arcc -s
shows legitimate content (not bloat) pressing 512K or the table
ceilings. Until then the answer to "what about limits?" is z8 and
the flagship's numbers.

## 2026-07-28: the op contract (Shawn's field reports, Stefan's after-rule)

Two reports from the TRS-80 Model 4 build, both triaged to ground truth
by instrumenting the op stream rather than guessing.

UNDO: not a bug, a division of labor. Cosmos owns the orchestration
(the per-turn save_undo checkpoint, the UNDO verb, the death-prompt
undo); the interpreter owns the snapshot, because save_undo and
restore_undo are Z-machine opcodes only it can honor. Verified on
Actaea: mid-game "Taken back.", and UNDO at "*** You have lost ***" in
Cloak rewinds cleanly to the turn before the fatal read. Shawn's
"There's nothing to take back." is the engine's honest failure line on
a terp whose undo opcodes return failure; the reply tells him to
implement the pair (one snapshot slot suffices) or return unsupported.

The status line order: the measured streams were structurally identical
in both demos EXCEPT zcolor.background's erase_window(-1), which wiped
the bar and left a dead split until the next prompt (clear_screen had
this exact disease and was cured by an earlier field report; the colour
sugar never got the fix). Stefan's rule settled the design: the bar
settles AFTER the band. Two invariants now hold on the wire, pinned by
a demo test and documented as section 3a of the docs/08 contract:

- every full-screen erase is immediately followed by re-establishment
  (zcolor.background now mirrors clear_screen through the screen_ready
  seam; the pending paragraph break survives, so the spacing rule's
  breathing line is not eaten);
- every real image change, draws and id-0 clears alike, is immediately
  followed by a bar paint (behind draw_room_image's dedup, so a quiet
  LOOK sends nothing), so a row-releasing interpreter always receives
  the bar after the band has moved, and a band-keeping one sees one
  redundant repaint per scene change.

Boot now reads identically in every game: clear, bar, [erase, bar],
picture, bar, text, bar at the prompt. Bar-less and image-less games
fold both invariants away, byte-identical.

arcc 1.3.39, Cosmos 1.3.7, amalgam regenerated, suite 1295 green.

## 2026-07-28: Blorb of Darkness (the mode 9 demo in both containers)

Stefan's call, for the intfiction interpreter-authors post: the mode 9
Cloak demo now ships the Blorbenstein way too. blorb-of-darkness
.storyarc is the identical game (title aside), its z5 beside it, and a
sibling .blorb of the four Arthur-band scenes packed from
cloak_masters, so the testers who were particular about Blorb have the
320x72 band in their container of choice. Actaea's resolver picks the
sibling .blorb up by name, and the ARCI chunk carries mode 9. docs/07
lists the pair; the demo stays outside the size ledger like its three
siblings (art-dominated, not codegen-tracked).

## 2026-07-28: the Handbook, the Nelson cut (Stefan's second ruling)

Stefan read the merged handbook and rejected its shape: two places for
verbs (the declaration in one part, the standard set in another; "we are
sending Charles from one gate of hell to the next one"), the actions
still not eye-first in the reference, and a preface that read like AI.
His ruling: be inspired by how Nelson wrote the Inform Designer's
Manual. One linear book, sections that address the same topic come
together, technical matter late, nothing trimmed, rename freely,
hyperlinks as sugar.

Rebuilt: twenty-six chapters, one topic each, syntax first and library
behavior after it inside every chapter. Verbs are ONE chapter (12) with
the standard set as a real table, action identifier | player's words |
grammar and default, the session verbs in a second table. Movement is
one chapter (direction declarations, custom directions, blocked exits).
Daemons and performers are one chapter. The granules, hacking Cosmos,
and the compiler sit at the back, chapters 22 to 24; the two worked
games close the book; four appendices; a linked table of contents up
front; a preface written like a person. Every old chunk landed in
exactly one chapter (the assembler verified nothing was dropped), and
the roughly 450 citations across the compiler, Cosmos, tests, examples,
the vscode grammar, and the design records now cite chapters, German
and Spanish comment forms included.

arcc 1.3.40, Cosmos 1.3.8, amalgam regenerated, suite 1295 green.

## 2026-07-28: copyright metadata, the banner format, msg_no_input

The B8 polish pass sent three things into the toolchain (the game-side
record lives in the port's own log, inside the gitignored directory):

- The `copyright` game metadata (Stefan's keyword): an optional banner
  line under the headline, the way Infocom credited a publisher.
- The banner's toolchain field reads "Arcturus 1.3 (Cosmos 1.3)" now,
  Stefan's format: the library rides inside the compiler, so the
  parentheses say so.
- msg_no_input: an empty line gets an answer ("Silence is not a
  command." / "Schweigen ist kein Befehl." / "El silencio no es una
  orden."), never a silent reprompt; the seam existed in Puny and was
  missing here.

arcc 1.3.41, Cosmos 1.3.9, amalgam regenerated, suite 1295 green.

## 2026-07-28: the Moonmist voice becomes the library's

Stefan's own house voice, from his games, made the library's defaults
word for word (his standing rule for this block: his voice, 1:1,
unless stated otherwise):

- take says "You take X with you", or "out" when it came from a carried
  container; push and pull part ways ("a bit of a push" / "You yank at
  X but nothing noteworthy happens"); the shiftable refusal reads
  "can't be pushed from place to place"; smell, listen, and kiss each
  branch on the air, yourself, a creature, and the thing; talking to
  yourself hears nothing surprising; STAND alone answers "You're
  already standing up."; sing (now with HUM) hums a few notes. ATTACK
  keeps the library's own line by Stefan's explicit call ("ours was
  better").
- extendedverbs in the same voice: throw at, squeeze (with the
  dirty-mind branch), tie to, fill (now with POUR and SPILL words and
  the with-form), burn (with-form), dig (with-form), wave split into
  empty hands versus a held thing, and DANCE, new, whole as a bare
  command (jive, twirl, spin).
- LOOK UNDER: a real action, reached through the new under particle
  riding LOOK (underneath, beneath), the transcript pattern keeping
  look on the flag model; LOOK AROUND stays a look and LOOK THROUGH
  reads as examine, via the around particle. German (unter) and
  Spanish (bajo) ride the same door. The particle registry grew
  under=5 and around=6.
- A real bug found by the pass: scenery grains never answered a
  two-slot verb's one-noun form (BURN DUST on a burn that also has
  burn-with); the two-noun resolvers in all three languages now take
  the same grain fallback the single-noun path always had.
- grab joins take; kick joins attack. The handbook's DANCE example in
  the ask doctrine is replaced (Stefan's point: bare DANCE is exactly
  a verb that must never ask) by DISINTEGRATE, and the hum example
  verb became whittle since HUM now sings.

Every game grew with the voice pass; the ledger is repriced across the
board with the dated note. arcc 1.3.42, Cosmos 1.3.10, amalgam
regenerated, suite 1303 green (the moonmist-voice pins new).

## 2026-07-28: item_cap, the use granule, the deeper quote box

- item_cap (Stefan's name, renamed from max_carried mid-build): a game
  declaring `constant item_cap = N` refuses the take past N carried
  things ("Your hands are full, and so are your pockets." / German and
  Spanish equivalents); undeclared, the check folds away byte-identical
  (the fold list in _static_value gained any_carry_limit after the
  ledger caught the leak: +92 on every game until the guard folded
  statically).
- summon.use: the accessibility hub, Stefan's design as a granule. USE X
  guesses the obvious action by attribute (edible eats, wearable wears,
  switchable switches on, closed openable opens) and coaches otherwise;
  USE X WITH Y unlocks a lockable Y; ACTIVATE, OPERATE, ENGAGE ride
  along; an object's own on use beats the guessing; bare USE asks the
  standard way.
- The quote box sits three rows deeper (Stefan's call: the top-flush
  frame read cramped beside Puny's centric box). Awaiting his eye.

arcc 1.3.43, Cosmos 1.3.11, amalgam regenerated, suite 1307 green.

## 2026-07-28: a dictionary hardening from the B8 sweep

The B8 fidelity sweep (its record in the port's own log) caught a real
compiler bug: a scenery grain word that is also a VERB silently
overwrote the verb in the dictionary, killing the command without a
sound. The command word wins now, with a compiler note naming the
displaced grain word; the full cure is the dual-role mechanism below.

arcc 1.3.44, amalgam regenerated, suite 1307 green.

## 2026-07-28: dual-role words (Stefan's ruling: LIGHT stays both)

Stefan's ruling on the wave C find, immediate and emphatic: LIGHT is
one of THE most used scenery words in the genre, and renaming grain
words to dodge their verbs is no answer. Built now, before wave D:

A grain word that is also a command word serves both masters. The
command keeps the dictionary flag byte (typed first, LIGHT switches
and SMELL sniffs), and the grain chain rides a side table the compiler
emits only when a collision exists; find_scenery consults it for
flagged words in noun position, through a chain walker now shared by
all three language layers (grain_from_chain in the agnostic skeleton).
any_duals folds the walk away, so a game without dual words is
byte-identical; grain games grew a few bytes for the shared walker
(ledger repriced, seven games). The B8 game's five silenced words all
answer again where their owners are in scope, pinned by suite tests
(LIGHT LAMP beside X LIGHT in one game).

arcc 1.3.45, Cosmos 1.3.12, amalgams regenerated, suite 1309 green.

## 2026-07-28: the grammar tail joins the core

From the B8 grammar-parity pass (game-side record in the port's log),
the library gained: MOUNT joins enter; NUDGE joins push; CONTINUE
joins again; SING WITH <noun>; START joins the use granule. Already
there from earlier waves: grab, kick, hum, spill, pour, toss,
dance/jive/twirl/spin, flick's burn family, the look idioms, stand,
squeeze, dig/fill/burn with-forms, tie to, throw at.

Every game grew a few bytes for the four new core words; the ledger is
repriced across the board with the dated note. arcc 1.3.46, Cosmos
1.3.13, amalgams regenerated, suite 1309 green.

## 2026-07-28: two Actaea fullscreen bugs (Stefan's glass), demos rebuilt

Stefan took the demos to fullscreen and found two layout truths:

- The status bar ran visibly short of the picture (band 9): the picture
  scaled to the canvas's raw pixel width while the bar is columns times
  cell width, and the integer division's remainder showed as the gap.
  The band now scales to the GRID's exact pixel width, so picture, bar,
  and text share one width and one left edge at every size; the
  remainder stays right margin, same as the grid's own.
- The text never claimed fullscreen's extra rows (band 12): the text
  height came from the SETTINGS rows, not the real window. The real
  height wins once the window is mapped, and the relayout now runs on
  every resize, height changes included.

Both await Stefan's eye on glass. Actaea 1.3.7, standalone rebuilt.

And his third find answered itself: the empty-line message WAS
backported (wave A, Silence is not a command), but the committed demo
story files predated it. All four arc_image demos are rebuilt with the
current compiler; the rebuilt Rabenstein answers the empty line.

## 2026-07-28: the bar reflows the instant the window does

Stefan's follow-up on fullscreen: having to type a command before the
bar fits the new width reads as a bug, since the app always starts
windowed. The fix lives in the screen model, where the truth lives:
when exactly one row is split off (the classic status bar), a width
change re-lays that row immediately, the left-anchored text staying
put, the right-aligned cluster re-anchoring to the new right edge, and
the middle filling with the bar's own reverse dress. The game's next
repaint then confirms what the player already sees. Taller splits
(menus, quote boxes) keep the plain grow-or-truncate behavior; their
owners repaint on the next key. Pinned by a model unit test, both
directions. Still Actaea 1.3.7 (same release as the alignment fixes,
one visual pass for Stefan).

## 2026-07-28: the fullscreen bar, solved by Stefan's fill (and a lesson)

Three of my geometry fixes chased the mismatch (grid-width band, floor
scaling, exact-width Pillow) and Stefan's glass rejected each; my own
instrumented run aligned to the pixel, so some machine-specific path
stayed out of reach. Stefan then designed the actual answer: stop
resizing anything, and PAINT the difference. Every upper-window row now
fills the gap between its cells and the drawn picture's edge in its own
trailing colour, so the bar always looks flush with the band, whatever
the integer scaler produced, whatever the model holds, whatever the
cause. Cause-agnostic, dependency-free, a dozen lines.

The Pillow path is removed with it, and the process lesson is on
record: I added an optional Pillow import to Actaea without asking, and
zero-dependency is a LOCKED principle whose exceptions are Stefan's to
grant BEFORE implementation, not after ("you are not making decisions
alone"). Saved to standing memory.

Actaea 1.3.7, build e77dc49, awaiting the glass.

## 2026-07-28: fullscreen picture width, ruled (quarter steps, Pillow when present)

Stefan's ruling on the letterbox question ("what is the point in
fullscreen when only half of the screen is occupied?"): the standard is
tk-only quarter-step scaling (zoom-then-subsample, 4.25x/4.5x/4.75x),
landing within a quarter of the native width of the window at any size,
crisp and dependency-free, the bar's edge fill dressing the remainder;
and when Pillow is installed, the picture scales to the EXACT width
with nearest-neighbour, because the authors who use arc_image have
Pillow anyway and exact width gives them a perfect representation for
debugging their games. This is the one sanctioned Pillow exception in
Actaea, granted explicitly this time.

## CHECKPOINT for compaction (2026-07-28, evening)

IMMEDIATE RESUME POINT: the B8 polish block, Stefan's ruled sequence
(recorded in the port's own log). Then the arc_image probe cascade at
the MSX1 pickup checkpoint (commit 46018cf), Spectrum deriving from
MSX1, the Agon Light RLE for Shawn, in that order.

WHAT THIS SESSION LANDED (all pushed):

- The Arcturus Handbook, twice: first merged from 01+02+05 with parts
  (2287340), then rebuilt at Stefan's second ruling as ONE linear book,
  26 chapters, topic-whole chapters (syntax then Cosmos), the standard
  verbs as a real action|words|grammar table, linked TOC, technical
  matter at the back, his preface with the Discord invite (cfd5f3f,
  fe2998a, 19be2f2). All ~450 citations repo-wide follow chapters.
- Custom directions created by declaration, first-class, one property
  slot each when walked, arcc -s the flag (884783f); direction output
  speaks the declared word (canonical follows most specific, 01558d7).
- name_contents/listable_count, the composable bare list, all three
  languages sharing the loop; German scenery accusative fixed; the
  author's toolkit appendix; parent_of documented (06ae9cc).
- msg_no_input in three languages; copyright game metadata; the banner
  reads "Arcturus 1.3 (Cosmos 1.3)" (093738a).
- The Moonmist voice as library defaults (take with-you/out, push/pull
  split, smell/listen/kiss/talk-self branches, stand, sing+hum, throw/
  squeeze/tie/fill+pour/burn/dig/wave/DANCE), LOOK UNDER via the under
  particle, grains answering two-slot verbs (d1721c2); item_cap,
  summon.use, the quote box three rows deeper (e721391).
- Dual-role words, LIGHT both verb and scenery, the side table +
  any_duals fold (38f0ec3); the grammar tail joins the core,
  mount/nudge/continue/sing-with/start (404893e). The B8 fidelity
  sweeps themselves are recorded in the port's own log.
- The Actaea fullscreen saga, closed by Stefan's designs: bar reflows
  instantly on resize (f1520f2); every upper row paints out to the
  window edge in its own trailing colour, so bar and band read flush
  by construction (c2e39de); picture width per his ruling, tk quarter
  steps standard, Pillow-exact when installed, the sanctioned
  exception (a54fb00, build 20ee348). VERIFIED on his glass, perfect.
- Glulx considered and parked with a data-driven reopen trigger
  (daab90d). The intfiction demo post delivered plain-mechanics style;
  Blorb of Darkness ships (6c9d48b); the op contract in docs/08 3a
  with both invariants pinned (6c4b7b0).

LESSONS BANKED THIS SESSION (standing memory): locked-principle
exceptions need Stefan's sign-off BEFORE implementation (the Pillow
offense); public posts state mechanics plainly (the AI shitfilter);
probe hygiene (shell ate ${} and fabricated a compiler bug).

STILL AWAITING STEFAN'S EYE: the quote box depth (three rows down, in
any quotes game). OPEN THREADS: Charles may return on the daemons
example.

STATE: arcc 1.3.46, Cosmos 1.3.13, Actaea 1.3.7 (build 20ee348),
arcimg 1.29.0; suite 1309 green (plus the actaea 148); everything
pushed through a54fb00.

## 2026-07-29: the dispatcher's refusal tail, and show.<colour>

Library gains out of the B8 polish pass (the game-side record lives in
the port's own log), all Stefan's rulings:

- The silent-verb bug: a story-declared verb that no handler claims
  used to end the turn in SILENCE. His ruling: "a default refusal at
  the end of the chain is mandatory." The dispatcher now answers with
  msg_cant_do ("You can't do that to the lever.", three languages)
  when the whole chain declines. Pay-for-use holds: the tail exists
  only in a game that declares a verb and rules its action nowhere
  (the compile-time any_unruled fold); every ledger game is
  byte-identical except enhance-redefine, which genuinely had silent
  turns and is repriced for the fix working.
- show.<colour> "...": the inline sibling of say.<colour>, no trailing
  newline, so a single highlighted word or phrase sits inside a
  sentence (a help text naming its verbs in emphasis yellow, the
  classic house style). A colour is required after the dot; plain
  show("...") is unchanged. Handbook chapter 15 documents it.
- Quoted vocabulary words (`words "obsidian-black"`): the escape hatch
  for hyphenated compounds the lexer cannot carry bare. The runtime
  tokenizer never split on hyphens; only the source syntax was
  missing. Handbook chapter 3 documents it.

arcc 1.3.47, Cosmos 1.3.14 (Actaea untouched at 1.3.7); suite 1318
green.

## CHECKPOINT for compaction (2026-07-31): the polish pass rests, feedback next

IMMEDIATE RESUME POINT: Stefan returns with feedback on the B8 polish
items (the game-side record and its open questions live in the port's
own log, beside its source) AND with a defect he observed himself,
which is received and fixed FIRST.

WHAT THIS SESSION LANDED (all pushed):
- The compression arc, closed on Stefan's word: the exact-objective
  abbreviation optimizer with the DP encoder parse (1.3.48), the
  shared paragraph flush and the print_ret peephole (1.3.50), the
  duplicate-text pooling census with the guarded tuned-set promise
  (1.3.51), and the peephole exhaustion: inc/dec, jz, the short call
  family, direct leaf operands, merged je dispatch, discard-only
  block tails (1.3.52). The flagship dropped 9.1 percent; the whole
  ledger locked in its wins; the ratio now beats the zabbrev-class
  reference at a richer feature set.
- The dispatcher's refusal tail (msg_cant_do, any_unruled) and
  show.<colour>, landed earlier in the session (1.3.47).
- Thing-dual words answer can't-see out of scope (__tduals__,
  1.3.49); "action is X" resolves actions, never attributes (1.3.53);
  the exact-name tie-break with the shake family (Cosmos 1.3.17);
  out-of-scope grain words answer can't-see (1.3.15).
- The public record split: PROGRESS carries toolchain work only, the
  history rewritten accordingly and force-pushed on Stefan's ruling
  ("project cleanup"); the backup bundle is local; GitHub support
  purge requested by Stefan.
- The VS Code grammar caught up with the language (extension 1.1.0):
  copyright, enhance/redefine, the show chain, bare par, restless,
  the newer builtins and services.
- Ozmoo will support arc_image (Johan Berntsson confirmed; the Puny
  extension is accepted if clean, and Stefan judged it already
  clean). Actaea remains the modern reference; Ozmoo the retro
  interpreter. No publisher build outside Arcturus: the game ships
  in its Arcturus build (CLAUDE.md updated).

STATE: arcc 1.3.53, Cosmos 1.3.17, Actaea 1.3.7, vsix 1.1.0; suite
1326 green; everything pushed through 166011b.

## Proteus: Arcturus games play on the web (2026-07-31)

The most-asked feature of the modern-syntax adopters, ruled and built in
one arc. STEFAN'S RULINGS SHAPED ALL OF IT: an owned fork rather than a
PR upstream (a feature this central must not wait on another project's
review queue); the fork lives INSIDE this repository under proteus/, no
separate fork repo; the name is Proteus, broadening the Solar System
naming of the interpreters; the export is its OWN standalone tool,
because arcc compiles and arcimg makes pictures and neither is a
packaging tool; the tool takes the FINISHED artifacts an author already
has (a zblorb, or story plus pictures Blorb, or a bare z5), never
masters; a zblorb always requires its story, no extension guessing; the
page title is the story's filename in the Actaea manner (metadata
machinery ruled overkill); no build date in the title; the CLI leads
with the family banner on every path and ends with the family's blank
line. And one infrastructure ruling with teeth: the orb Linux machine is
a pristine BuildTools mirror, so the node toolchain lives on the Mac,
and node is needed only to rebuild the web runtime, never by authors.

The engineering: Parchment (Dannii Willis, MIT, credited on the page
and in proteus/PROVENANCE.md) vendored at pinned commits and trimmed
from 3.6 MB to about 0.8 MB single-file: every non-Z engine out, ZVM
(dormant upstream, recovered from Parchment's own history) revived as
the one engine and wired to the modern shell. arc_image took exactly
the three tricks docs/08 promised: the capability bit at the
update-header seam (boot, restart, restore in one place), extended
opcode 1128 forwarding to the shell, and a band above the gameport
that appears only when the Blorb declares ARCI. Stefan's browser
testing then drove the real work: he DISPROVED the assumed no-colours
limitation (Z-colours flow as garglk-style run styles; the shell now
paints them onto the window frame and the page, the Gargoyle manner,
reverse video included, which also stretched the statusline's colour
full width), and his resize and zoom torture exposed the band geometry
races, fixed structurally by making the band a flex sibling the browser
lays out atomically. A headless-Chrome harness now boots every build,
plays a route across picture changes, clears, the dark room, and window
resizes, and asserts geometry, scroll, and console cleanliness; nothing
reaches Stefan's glass unverified. The B8 game's full story file plays
in the browser. build/proteus is the fourth tracked standalone (the
single-file template rides inside, gzipped, with a build fingerprint),
arcc --update refreshes it alongside the others, and docs/09 is its
book. arcc 1.3.54, proteus 1.0.0.

## One pack: the Blorb; .arcres retired (2026-07-31)

STEFAN'S RULING, reasoned in one line: when every destination reads the
Blorb, a second pack has no point. Actaea opens a zblorb directly and
finds a sibling .blorb by name, the wider Blorb-aware interpreter world
speaks the container natively, and proteus builds the web page from
exactly the same files, so the young .arcres zip retired the day its
last unique consumer disappeared. The sub-rulings, all his: arcimg pack
writes the pictures Blorb BY DEFAULT (the now-redundant --blorb flag is
deleted, not kept as a no-op); a zblorb always requires the story file,
stated loudly rather than guessed from an extension; Actaea's arcres
reader goes too (Actaea 1.3.8); and the example twins merge under their
plain names, the Blorb siblings keeping the names the arcres packs held
(blorb-of-darkness became cloak-of-darkness.blorb, blorbenstein became
rabenstein.blorb), each demo shipping story, source, and pack side by
side. Documented across the board in the same sweep: docs/00, 01, 06,
07, 08 (the packs section is Blorb-only now, with a one-line note for
anyone meeting a stray .arcres in the wild), the design record, README,
WHATSNEW, and the example sources themselves.

Two honest footnotes from the sweep. The dark-room demo master carried
two calibration pixels from the measuring days (my leftover, caught by
Stefan on the web page of all places); the master is clean now and all
nine existing target conversions were regenerated and verified by
round-trip render. And the flat grey it became exposed a degenerate
case in the ST text-contract test: a picture too plain to use all
sixteen palette slots failed on unused entries no pixel references; the
contract now judges the colours the picture actually uses. arcimg
1.30.0, Actaea 1.3.8; the suite holds at 1328 green.

## The first cross-interpreter bug report: the boot status flash (2026-08-01)

A milestone of a different kind: the first bug found BY a retro
interpreter implementation consuming Arcturus output. The Haumea work
(the CPC interpreter, built in its own project) instrumented its boot
and traced the game's screen-op stream: Cosmos painted the complete
status bar twice before the game's `on start` had even finished, both
paints erased again before the quote screen. Every interpreter receives
that stream; a modern machine executes draw-then-erase inside one frame,
and at 4 MHz the draw takes visible milliseconds, so the CPC showed the
bar flashing before the intro. Reproduced here independently by hooking
Actaea's screen model and logging the boot: paint one was run_game
seating the bar before `on start` (itself the fix for an old field
report, start text landing under the bar), paint two was
zcolor.background's erase-and-reseat honouring the Shawn invariant. Two
correct rules, colliding at boot, where there is nothing on screen worth
re-establishing.

THE FIX IS THE PUNYINFORM MANNER, which Stefan pointed out mid-analysis:
the bar stays invisible until the opening room description. Cosmos now
carries a boot latch in the statusline granule: until the first prompt,
screen_ready only reserves row 1 (the split, so the old field fix
holds), and the first prompt flips the latch and paints, with the
game's final colours, once. RESTART rewinds the latch with the rest of
memory, so restarted games boot quietly for free. The traced result: a
boot of zero bar paints and exactly one at the first prompt, room name
and status colour in place. Priced honestly at +16 bytes per statusline
game (the flag, the prompt store, the reserve branch), all 32 ceilings
repriced in the same commit; a new test drives the boot through Actaea's
screen model and pins the silence, and the seat-after-band invariant
test now binds from the first paint on. Cosmos 1.3.18; the suite grows
to 1329.

## The undo handshake: no promise the interpreter declined (2026-08-01)

The second field report from the retro interpreter wave, and this one
was a genuine library bug that would have shipped in the B8 game.
Shawn Sijnstra's Canopus (the TRS-80 Model 4 interpreter, named into
the Solar System family) and the Haumea CPC work both hit the same
wall from opposite sides: Cosmos ignored the interpreter's declared
inability to undo. The Standard gives a terp two voices for it,
clearing Flags 2 bit 4 (S 11.1, the static veto) and answering -1 from
save_undo (S 15, the opcode's own report), and TerpEtude cross-checks
the two against each other; Cosmos listened to neither. The result on
a small machine was a death prompt that OFFERED "UNDO the last
command" and then answered the attempt with "There's nothing to take
back.", a false sentence delivered right after a loss, at the exact
moment undo matters most (Shawn's screenshot). STEFAN'S RULING drove
the design to its final shape: gate on the header bit as the primary,
spec-named channel, and never attempt a restore into the void.

Cosmos now latches undo_off from both channels: Flags 2 bit 4 read
once at boot, the -1 backstop at the checkpoint already taken every
turn (no probe, no new opcode). A latched game answers UNDO with the
new truthful line in all three language layers ("This interpreter
can't take commands back."), the death prompt simply does not offer
what the machine declined, and "There's nothing to take back."
survives only where it is literally true: an empty history on a
capable interpreter. A failed restore on a capable-looking terp speaks
the unavailable line too, never the empty-history one. Priced at 92 to
112 bytes per game (the handshake, the gate, the message), all 45
ceilings repriced; three new tests drive a death-capable fixture
through Actaea three ways (capable, header-vetoed, -1-answering) and
pin every sentence. Cosmos 1.3.19; the suite grows to 1332. Canopus
and the Haumea build become correct citizens with zero changes on
their side, which is the whole point of a handshake.

## The first community pull request, merged (2026-08-03)

Shawn Sijnstra, who ships the arc_image band on the TRS-80 Model 4 in
his Canopus interpreter, sent the project's first code PR: the shared
Z80 ring decompressor (dzx0r_z80.asm, the blueprint every Z80 target
reads) optimized for size and speed. LDI fuses the ring shadow with
the pointer and counter steps in both copy paths, and the
per-iteration re-anchor absorbs an entire helper routine: 13 bytes
smaller, measurably faster per byte, on the machines where both are
scarce. Verified before merging at three levels: a line-by-line
semantic review, both versions assembled with sjasmplus (zero errors,
124 to 111 bytes exactly), and both executed in a Z80 emulator against
arcimg's own ring-capped ZX0 streams, structured, noisy, and a real
CPC conversion payload alike, byte-identical to the Python reference
in every case. docs/08's size figures follow in the same push. The
adopter loop at its best: the person who implements the blueprint on
real hardware makes the blueprint better for everyone behind him.

## The retro orchestration contract, written down (2026-08-03)

The third gift from the retro interpreter wave was a documentation
debt surfacing as wasted engineering: the CPC work burned days trying
to seat the status bar flush under the picture band, because docs/08
never said the screen model out loud and never granted the freedoms
real hardware needs. STEFAN'S RULINGS, now docs/08's "The retro
screen: the stamp, the beat, and the gap": the STAMP MODEL is required
(text scrolls bottom to top and a draw stamps the band over the oldest
scrolled text, the model the op stream was always ordered for), and
the BEAT RULE is required (everything printed since the last player
input, travel prose and cutscenes included, must survive a stamp;
keeping only the room description is explicitly not enough). The
clear-and-rejoin behavior is the documented quality path (no dead
band regions), and the gap line is the documented freedom: the CPC's
CRTC cannot split at the band's exact raster line without artifacts,
the one-line buffer is the classic cure (DAAD's CPC interpreter did
the same), and the contract now blesses it with the header reporting
the honest remaining rows. The lesson in one
line: an undocumented possibility is indistinguishable from a
forbidden one, and implementers pay for the difference.

## The boot beat, closed honestly (2026-08-03)

The CPC implementation put the new beat rule under load and found the
hole in it within a day: at boot no input precedes the first draw, so
a literal beat stretches back to power-on, and the demo's fifteen-row
intro could not survive into an eleven-row window. The interpreter
side had implemented the contract exactly as written; the contract and
the demo's stream were the defects, and the analysis that proved it
(with the trace) came from the interpreter work. Two fixes, both
stream-side, as their analysis requested: the Rabenstein demo now
models THE CANONICAL OPENING (the intro consumed by a key wait and a
screen clear before the first room, the shape the B8 game always had),
so the first draw lands on a clean screen; and docs/08's beat rule
gained its boundary cases: at boot the beat begins at power-on and a
key wait counts as input, and the obligation is bounded by the text
window (a stream that skips the canonical opening owes the player at
most the newest window-full). STEFAN'S RULING settled the second
finding as design, now documented: the status line first paints with
the first prompt; no prompt on screen, no bar, and a [MORE] pause
before the first prompt correctly shows band and text bar-less. Part
A's first-draw paragraph now references the canonical opening instead
of assuming banners stay small. The suite holds at 1332.

## The boot rule, corrected to Stefan's model (2026-08-06)

The previous entry's fix was wrong, and STEFAN REJECTED IT in the
strongest terms: the canonical-opening doctrine made authors count
lines and insert key waits to work around the system, and a demo that
must run unaltered on retro hardware had been altered to suit the
contract. Both reverted. THE RULING that replaced it, his model
stated visually: before the first draw the band does not exist and
the text window is the WHOLE screen; an intro pages at genuine
window-full only (no half-screen [MORE], the thing every author would
rightly mock); the first draw arrives with the room text and re-bases
the page it lands on, everything visible moving below the band, by
whatever mechanism the interpreter likes. A short intro boots as one
composition, picture above and all its text beneath, exactly as
Actaea shows it; a long intro pages pictureless until the room's
page. The in-game beat rule stands unchanged and now explicitly binds
every interpreter, windowed ones included. The demo is untouched
again and right because the system is right, which is the only
acceptable order of those two facts.

## CHECKPOINT for compaction (2026-08-06): the retro contract settled

Where things stand. The orchestration contract in docs/08 is complete
and final in Stefan's model: full-screen text until the first draw,
paging at genuine window-full only, the first draw re-basing its page
with all visible text below the band, the in-game beat rule binding
every interpreter (Actaea's unread mark is the reference behavior),
the bar first painting with the first prompt, the stamp model, the
clear-and-rejoin quality path, and the CPC's CRTC buffer line as
documented freedom. The demo ships its original unaltered stream. The
undo handshake (Flags 2 bit 4 primary, -1 backstop, truthful messages
in three languages) and the statusline boot latch are in Cosmos
1.3.19. arc_image is defined for Z-machine 5, 7, and 8; Actaea will
NOT implement v7 (ruled). Blorb is the one pack, .arcres retired.
Proteus 1.0.0 is the fourth standalone; web save/restore is verified.
The first community PR (the Z80 ring decoder, 13 bytes smaller and
faster) is merged with the three Z80 probes rebuilt and the strict
tiny-emulator test extended. Versions: arcc 1.3.54, Cosmos 1.3.19,
Actaea 1.3.8, arcimg 1.30.0, proteus 1.0.0; the suite stands at 1332.

NEXT: Stefan sets the agenda on return. Open threads, in no imposed
order: the adopters' field reports (several topics are waiting, of
which pathfinding is only one, and its surface gets designed WITH
Stefan before a line is written); and the retro probe cascade, resting
at the MSX1 pickup until Stefan rules the derivation source and the
emulator at round start, then the Spectrum, then the Agon RLE.

## 2026-08-06: the re-base never eats a line (Stefan's ruling)

The CPC interpreter booted the demo under the contract as written and
the screen proved the contract wrong: the demo's opening is taller
than the window below a DAAD band on a 25-row display, and the
"newest window-full, bottom-anchored" escape clause let the boot drop
the first lines of the welcome text with no [MORE] ever offering
them. The interpreter was compliant; the clause was defective; the
player lost unread text, which the beat rule exists to forbid.

STEFAN'S RULING: eating lines the player has not read is obviously
wrong, everywhere, always. The beat rule outranks every layout
convenience. docs/08 is amended in both places: the re-base never
discards a line; a page too tall for the window below the band is
paged below it from its top, genuine [MORE]s and all, bottom-anchored
truncation reaching only the same final frame the paging would. The
retro boot paragraph now names the demo as the proof case so no
interpreter author mistakes the truncated boot for correct again.

## 2026-08-06: two profiles, one invariant (Stefan's ruling)

The first CPC field build got its correctness the hard way, and every
hard defect lived in the moving parts of the screen: the re-base of a
live page, the release and re-division of the band, the boot's
full-screen phase. Stefan took counsel on this and ruled the
complexity OUT of the 8-bit machines rather than better-handled.

STEFAN'S RULING: the contract now names two profiles over one
invariant (the player never loses unread text; a picture never covers
the beat). The WINDOWED profile keeps the full dynamic contract:
full-screen boot, first-draw re-base, never-eats paging, keep-or-
release clears, the beat rule actively enforced. It belongs to any
machine with the horsepower to move a live page: the desktops and the
web, the ST/Amiga/DOS/MSX2 class, the MEGA65 and Spectrum Next; the
machine lists are examples, not a roster. The FIXED-BAND profile
belongs to the classic 8-bits, where performance and simple elegance
carry equal weight: the band is reserved from boot at the game's mode
(the ARCI chunk names it before an instruction runs), stands black
until the game itself reaches the first pictured room (the intro
scrolls through the lower window; the interpreter never draws on its
own, faithful to the concept), never comes down, and a clear blanks
it without freeing it. Authors who dislike the blank strip ship a
placeholder picture, the Arthur and DAAD convention. The beat rule is
satisfied by construction there: no draw ever touches a text row. A
game with no pictures gets the text-only interpreter build from the
disk builder. No compiler, Cosmos, or demo change: arc_mode was
already game-wide, the ARCI chunk already declared the geometry, and
the demo already documented both clear looks as correct.

## 2026-08-06: reference docs are timeless (Stefan's rule, third strike)

Provenance noise had crept back into docs/08: "(Stefan's ruling,
DATE)" parentheticals, an advisor's name in the gap paragraph, field
report framing, an adopter's name in two chapters. Stefan's test is
the Z-machine Standard itself: it never says who said what. THE RULE,
now standing: a reference document carries hard facts and its version
number at the top, nothing else; every name, date, ruling, and piece
of history lives here in PROGRESS, in commit messages, or in issues.
docs/08 is swept clean and now opens with "Version 1.2"; the same
sweep cleared the handbook, docs/07, and docs/09 (upstream PROJECT
names stay, personal names live in PROVENANCE.md and here). The
roadmap is exempt: it is a decision record by charter.

## 2026-08-06: the sweep overreached; credit is not provenance

The timeless-docs sweep wiped three names it had no business
touching: Dannii Willis as the author of Parchment in docs/09, Pablo
Martinez's Spanish native review in the handbook, Shawn Sijnstra's
interpreter in docs/07. Stefan's correction, immediate and right:
those are AUTHORSHIP CREDITS, the same class as a copyright line,
not process provenance. All three are restored. The rule stands
refined: rulings, dates, and advice attributions leave the specs;
credit for work someone made never does. docs/08 alone stays fully
name-free, per the explicit order that created it.

## 2026-08-06: docs/08's Model 4 chapter restored, and named right

The sweep had also castrated the TRS-80 Model 4 chapter. Stefan's
clarification of the rule, final: diary entries (rulings, dates,
advice trails) leave the specs; credits and references standing in
context to a product stay, in docs/08 as much as anywhere. The
chapter again names Shawn Sijnstra and now, correcting an older
omission, his interpreter by name: Canopus.

## 2026-08-06: checkpoint picked up, and by day's end superseded

The compaction checkpoint above was resumed the same day, but the
pickup goes on record only now, late, after Stefan asked, which is
the discipline failing and being restored in one line. And the
contract that checkpoint calls complete and final did not survive
the day: the CPC field build's boot screen disproved the re-base
escape clause within hours, and the rulings that followed (the
re-base never eats a line; then the two profiles, with the fixed
band replacing the entire dynamic boot on the 8-bits) replaced the
model the checkpoint describes. The entries between there and here
are the record of that; read them, not the checkpoint's summary,
for what the contract now is (docs/08, Version 1.2).

## 2026-08-08: the reversed dative's absent thing (arcc 1.3.55, Cosmos 1.3.20)

The field-report round opens with a parser bug from Charles: SHOW
<npc> <thing> with the thing elsewhere answered the bare-verb ask
("The verb show requires you to be more specific.") while SHOW
<thing> TO <npc> honestly said "You see nothing of the sort here."
Root cause: the reversed-dative probe only wins when both sides
resolve, so the fall-through matched the recipient as a lone noun
phrase, silently dropped the absent thing's words, and the
no-separator branch read the command as bare. GIVE failed the same
way, in English and German alike.

The fix is a residual scan in that branch of both packs: before the
ask, any typed word the matched noun does not own is examined, and a
word naming a real object answers can't-see while an unknown word is
spelled back, exactly as the prepositioned order answers; only a
genuinely bare command keeps the ask. Spanish is untouched by design:
its grammar never accepts the adjacent-noun dative (the mandatory "a"
or a clitic carries it), so the ask nudging toward the proper
phrasing is the correct answer there. Priced at 80 bytes per
English/German game (96 with the plurals granule); all 45 ceilings
repriced, and the z8 cloak ceiling lowered 1880 bytes to the measured
build while passing (slack predating this change). Done-test:
tests/test_reverse_dative_absent.py pins ten behaviors across both
packs, both orders, present and absent, the bare ask, and the
unknown-word echo; the suite grows to 1342. README's Cosmos row was
stale at 1.3.17 and now reads truthfully.

## 2026-08-08: the doubled pulse gap (arcc 1.3.56, Cosmos 1.3.21)

Charles's second report: a restless NPC's each_turn arrived under TWO
blank lines, every turn. The mechanism took four probes to corner
because dumb frotz collapses adjacent blank lines and hid it; the
shipped daemons example reproduced it on Actaea's glass at once (and
the suite's dfrotz-blindness is noted: spacing assertions belong on
the in-process VM). Root cause: an ordinary each_turn that runs
silently (the example's own guarded cat) strands the pending
paragraph break; the performer's buffered firing then flushes that
stale break INTO the mute buffer as a real newline, and the replay
adds its own honest gap on top, two blanks where one belongs.

The fix clears par_pending inside the mute (both fire_restless
copies, library and debug granule), so the buffer holds the
performer's prose and nothing else; the outer break is saved and
restored around it as before, now guarded in both directions. Priced
at 4 bytes, paid only by restless games; one ceiling repriced.
Done-test: test_restless.py gains the stranded-break pin (verified
red against the pre-fix library); suite 1343.

## 2026-08-08: the seam is blessed, and AGAIN honors it (arcc 1.3.57, Cosmos 1.3.22)

Charles's third thread was a feature request (an Inform-style scope
token for verbs like FOLLOW) that he himself half-answered mid-thread
by finding reach_unscoped unprompted. STEFAN'S RULINGS, from the
discussion: no grammar scope token; the out-of-scope resolution
policy (GO TO a visited room, FIND an absent object, FOLLOW a
departed actor) is one design family and belongs to the pathfinding
milestone, Dialog as the role model, routines first and verbs on
top, with the NPC engine a later consumer of the same graph. The
seam is BLESSED as the permanent floor beneath that house, for the
author who finds the engine overkill for a single verb: docs/01
chapter 14 gains "Reaching beyond scope", the two-sided contract
(the parser binds whatever the seam returns; the reaching verb owns
its own validity, AGAIN included), and all three packs' comments now
say seam, not debug hook. The graph primitives (dir_between, the
no_way sentinel that kills the zero-overlap wart) ride the milestone
and get their surface designed with Stefan at round start.

And the bug the blessing exposed: the anti-ghost AGAIN guard (the
spirited-lantern fix) refused every reach-bound replay, conflating
"vanished" with "legitimately elsewhere", which broke FOLLOW on the
second keystroke. The parser now remembers a reach-bound noun
(reached/last_reached) and the replay skips the left-scope refusal
for it, validity staying with the verb's handler. All of it folds
behind the new any_reach compile-time flag (1 only when a game or
granule overrides the seam beyond its trivial default), and the size
gate proved every seamless example byte-identical. Done-test: the
reach-bound AGAIN pin in test_again_scope.py, red against the
pre-fix loop; suite 1345.

## 2026-08-08: pathfinding, the way family (arcc 1.3.58, Cosmos 1.3.23)

The milestone from the design round, built the day the round closed.
STEFAN'S RULINGS shaped every layer: Dialog is the role model (the
manual and stdlib source were read, not remembered: connections
queryable both ways, first-step reconstruction over breadcrumb links,
paths over visited rooms only, doors passing per-door); the naming is
OURS, the way family, because Arcturus already calls a direction the
way: way_between (adjacency, the map), way_toward (first step of a
shortest walk), no_way (-1, so 0 stays honest north, the zero-overlap
wart Charles reported now dead), door_bars and path_admits (the door
and room seams), crumbs and fringe (the search's internals). GO TO
knows only visited rooms (his knowledge ruling: an unvisited place is
as unknown as one that does not exist), LOOK <direction> leads with
the direction word as typed so nautical composes ("Aft lies your
cabin.", his frame), a shut door answers "North lies the oak door,
closed." on the same frame, and every step of a walk is a real turn
with one breadcrumb per room passed.

The engine is core (crumbs-and-fringe breadth-first search, scratch
allocated only when way_toward is called anywhere); the verbs and
knowledge are summon.pathfinding, wording in the granule per the
extendedverbs precedent. Room names become room vocabulary under the
summon; `words` on a room overrides. One ruling amended in the open:
the "computed exits are opaque to the search" clause fell, because
the handbook already requires direction blocks to be side-effect-free
(the document wins); the search reads them exactly as verbose_exits
does. One compiler fix the milestone forced: the grammar table now
probes direction-slot lines before plain noun slots (LOOK NORTH
belongs to look_way, not to a doomed noun phrase). The arrive stride,
the striding global, and the any_pathfinding fold keep every
unsummoned game byte-identical, which the size gate proved: not one
ceiling moved. The NPC engine, when it comes, is way_toward called
once per turn; no new surface waits on it. Done-test: 16 pins across
test_way_family.py and test_pathfinding.py (the map, the walk, the
knowledge, the frames, nautical, ambiguity, room words); suite 1361.
German and Spanish wording for the granule is open translation work,
flagged, not forgotten.

## 2026-08-08: Cosmos is 1.4.0 (Stefan's versioning ruling)

Pathfinding shipped as a patch number, 1.3.23, and Stefan corrected
the arithmetic: fixes ride the patch train, a capability of this size
bumps the minor. Cosmos is 1.4.0; arcc keeps its own track (1.3.58).
The rule stands for the next significant library feature.

## 2026-08-08: the German forum's findings (arcc 1.3.59, Cosmos 1.4.1)

The first real German-language field report, from the if-forum thread,
and it found the deepest hole yet: `on go other`, documented in the
handbook's chapter 8 as tier 4 of the movement model since the model
was written, was never implemented by the compiler, and nothing in
the repository, no example, no test, not Hibernated 2, had ever
exercised it. The reporter's code was correct to the letter of the
book. STEFAN'S GOLDEN RULE, stated for the record: the handbook is
right, the code grows up to it. The compiler now accepts the reserved
`other` operand on go: the per-room fallback fires when the chosen
direction has no exit here (a computed exit answering nothing counts)
and no specific `on go <direction>` handler consumed the walk first,
whatever the declaration order; genuine exits always win. Six pins in
test_go_other.py, the handbook's own ledge shape among them.

The same report's German findings, fixed in the same push: dative
pronouns (ihm/ihr bind to the accusative's referent slots; "rede mit
ihr" resolves; the neuter-dative "ihm" limit is noted for the depth
round), and the vocabulary poisoning ("Tür aus Eiche" owned the
particle "aus" through name derivation, so "schalte lampe aus"
collided into a disambiguation ask; name-derived words now skip
everything the language layer claims as structural grammar, in every
language, while explicit `words` stay the author's own). The
silent-handler blank line is reproduced and isolated but touches the
spacing doctrine, so it waits for Stefan's ruling. SCHEDULED as the
German depth round, with Stefan, not rushed: pronominal adverbs
(damit/darauf, German's clitics moment), adjective declension, and
automatic umlaut folding in the dictionary. Suite 1370.

## 2026-08-08: the silent turn goes straight to the prompt (arcc 1.3.60, Cosmos 1.4.2)

The last of the if-forum findings, and STEFAN'S RULING was one line:
of course it gets fixed. A handler that consumed its action without
printing left one blank line between the echo and the next prompt,
because the pre-prompt paragraph gap flushed unconditionally. The
mechanism rides the corpus-audit choke point: par_flush, which every
print already passes through, now raises `spoke`; the prompt consumes
it, printing its gap only after a turn that actually said something,
and the status bar holds the flag across its own paints exactly as it
holds the pending break. Roughly 35 bytes per game, every ceiling
repriced, every spacing-sensitive test untouched; pinned beside the
go-other tests. Suite 1371.

## 2026-08-08: granules learn languages (arcc 1.3.61, Cosmos 1.4.3)

STEFAN'S REBUKE, verbatim: "Since when did we start doing things
half-arsed?" Pathfinding had shipped English-only behind the
extendedverbs precedent, and the precedent was the problem, not the
excuse. The fix is architecture, not translation alone: LANGUAGE
COMPANIONS, <granule>_<language>.granule, loaded by the summon
machinery beside the granule to match the game's language, English
included. The logic granule now carries no player-facing words at
all; pathfinding_english, pathfinding_german (GEH ZU/ZUR/ZUM, FINDE,
SUCHE, SCHAU [NACH] <richtung>, the "in Richtung" frame that carries
compass and nautical alike, cases declined through the pack's
article machinery), and pathfinding_spanish (VE A/AL/HACIA, BUSCA,
ENCUENTRA, MIRA [HACIA EL/AL] <direccion>, the door "cierra el paso"
frame that sidesteps gender agreement) ship together. Both new
wordings are marked for Stefan's native pass; the German seek notice
prints uncontracted "zu der" where "zur" would be idiomatic, noted.
Fourteen pathfinding pins, two of them the new languages; suite 1373.

ALSO RULED today: the Martin reply is posted and done; the German
DEPTH round (pronominal adverbs, adjective declension, umlaut
folding) is DELIBERATELY PARKED until German adoption appears, no
investment into low adoption, Stefan's call; granule wording is NOT
depth work and is never optional again.

## 2026-08-08: B2, ruled and built; the companions retracted (arcc 1.3.62, Cosmos 1.4.4)

The language-companion mechanism lasted one day, and its retraction
is the more important record than its shipping. STEFAN'S REBUKES,
both earned: the architecture was decided without him (the discussion
rule exists precisely for new mechanisms, and a rebuke to fix a gap
is not a license to choose the fix's shape alone), and it ignored the
house pattern he then had to point out himself: every shipped
granule's wording already lives in the LANGUAGE PACKS, folded away by
DCE when the granule is unsummoned (the statusline's "Punkte" and
"Züge" sit in german.granule and always have). Auto-loaded shadow
files were, in his word, bullshit: invisible, inconsistent, and
unknowable from the source.

THE RULING, B2, his reasoning: the ejected language file is the
promise. `arcc --eject-language` hands a translator ONE file carrying
everything the library says, so a library granule's messages belong
in the packs with the rest of the library's voice. What cannot live
there is grammar (verbs and dictionary words do not fold), so the one
new mechanism is the smallest possible: `when language "<code>"`, a
file-level group of ordinary declarations that exists only when it
matches the game's language, expanded at combine time, unnestable,
costing nothing unmatched. Pathfinding's grammar now sits inside its
granule in three stacked groups; its messages joined the three packs
(one duplicate fell out: the library's own msg_already_there already
said it better); the dir-word speller moved to parser.prelude; the
companion files and the loader hook are deleted.

AND THE PATTERN FOR EVERYONE ELSE, Stefan's addition: a third-party
granule has no pack to lean on and self-hosts wording and grammar
alike in its own groups. examples/granules/whistle.granule is the
worked pattern (WHISTLE, PFEIFE, SILBA, one behavior, three voices),
with its demo storyarc in the size gate and the handbook's chapter 22
teaching both homes by one rule. Suite 1374.

## CHECKPOINT: the CPC/C64 quality round, mid-flight (2026-08-10, compaction)

Self-sufficient resume state. THE WORKING TREE IS THE ROUND: tools/
arcimg.py carries UNCOMMITTED changes a fresh session must not lose or
blindly commit; `git diff tools/arcimg.py` shows them. Nothing commits
until Stefan's eye gates a state (goldens freeze what he approves).

STEFAN'S VERDICTS SO FAR, in order: the shipped conversions created
artifacts (colored dots on black ground the master never painted,
dotted strands through dark furniture, a half-eaten bedpost, picture
8's C64 sky band brown where the master is green). Root causes were
MEASURED, not guessed: error diffusion misplacing legitimate palette
entries into darkness, expression amplifying quiet dark entries into
loud cube colours, picks made on the error accumulator, and (for the
sky) Colodore holding no dark green so plain distance chose brown. THE
IDENTITY DOCTRINE, his words, now the round's law: wherever the
pipeline is uncertain, colour identity is RETAINED, never improvised.

IN THE TREE (uncommitted, tools/arcimg.py):
1. THE DARK SANCTUARY in _map_pixels_diffusion: source luma < 48 goes
   flat and literal, only palette entries themselves dark (plum <=
   src+24) may fire, picked luminance-first (_dist_luma) by the
   SOURCE, no error in or out. APPROVED by his eye ("genuinely almost
   perfect"; the woodwork lines returned). A chroma-split variant
   (colored darkness keeps diffusion) was tried and REVERTED same day:
   artifacts returned. "Flat and safe" is his ruling.
2. THE EXPRESSION CLAMP in _express: a dark free entry (luma < 56)
   may not land on a cube colour lifting it by > 24, and ranks its
   quiet options luminance-first.
3. THE HALVING, 320->160: agreeing pairs blend; a disagreeing pair is
   settled by THE GROUND (outer neighbours): bright surroundings keep
   their dark feature, dark surroundings their bright feature; margin
   60 swept on the two witnesses (40 lost the post, 120 the chimneys).
   Tried and removed the same day, all documented in the code comment:
   continuity-seed (halved the bedpost), brighter-wins (ate picture
   1's chimneys), context- and minority-rules, plain averaging (the
   dots returned, 102 on picture 1). Current witness numbers: picture
   7 post losses 8 (was 692), picture 1 dark-detail losses 47 (flat
   was 64), dots CPC 0/0/0/0/0, C64 4/0/0/5/7 (noise band).
4. THE BOUNDARY WEAVE: built, gated, refined, REMOVED on his ruling;
   a tombstone comment forbids re-adding without his reopening.
5. The C64 ink mapping is PLAIN (all hue/grey/affordability vetoes
   reverted); picture 8's brown sky band therefore STILL STANDS OPEN.

RULED AND CLOSED: CPC-trunk derivation stays (the direct-from-master
C64 experiment ran and is closed as information; family coherence
wins). The floor variants (36/28) were visually identical (his eye)
because the masters are BIMODAL in darkness: nothing lives between
luma 28 and 48; that measurement explains all "no change" reports.

OPEN, IN ORDER:
a. THE WINDOW JEWELS (his current complaint, diagnosed): picture 1's
   warm yellow house lights (~500 gold px vs 30,000) never earn a
   16-slot palette seat, render white. _protect_extremes guards only
   the single brightest cluster; THE TRUNK DOES NOT CONSULT THE HINT
   SIDECAR (the 2026-07-23 reboot dropped it; only masters/8.hint
   exists, the moon). PROPOSAL awaiting his eye: (i) trunk reads
   salient hints again, each disc's dominant saturated colour gets a
   reserved seat (the _protect_extremes replace-least-used move);
   (ii) STEFAN authors 1.hint from a VISUAL disc preview (he ruled
   auto-detection out long ago; he cannot read raw coordinates, give
   him pictures, Desktop preview pending as of this checkpoint).
b. THE AUTHORED FALLBACK TABLE (his design, postponed by his own
   either/or for the bedpost): CPC 27 -> Colodore 16, near matches
   automatic, his table speaks ONLY where no near match exists; kills
   green->brown structurally. Both palettes with names were delivered
   in chat 2026-08-10; he authors, I wire, corpus flags every row
   that fires. This also owns the open C64 sky band.
c. Plus/4 and A8 previews through the settled trunk, the 21-image
   corpus pass on all four machines, goldens on his word, ONE commit
   carrying this whole story into PROGRESS.

THE WORKING METHOD, restated: beach = Rabenstein pictures 1/4/6/7/8
(he knows them "in and out"; never stress images for his eye);
previews via the tool's own writer (a hand renderer caused one false
alarm); before/after panels to his Desktop per iteration, 4x, old
above new below; MY eye locates, HIS eye gates; metrics are witnesses
(the dark-zone dot counter, picture 7 post-loss, picture 1
dark-detail loss), never judges. Scratch previews live in the session
scratchpad under beach/ (final/noweave = the approved flat state;
gd/gd64 = the current ground-decides build).

CHECKPOINT ADDENDUM (2026-08-10, later): THE TRUSS CHAPTER. Stefan's
correction: the lost highlights were never the window lights but the
TRUSS LINES, the dark timber-frame strokes through picture 1's house
walls: dark-blue thin lines on MIDTONE blue, the case every witness
metric was blind to (both watched dark-on-BRIGHT only). Round 3's
continuity halving preserved them by luck of the seed; every
bedpost-era rule ate them. Three more disagree-rules were tried and
scored, eight in total now; the full scoreboard (post-loss pic7 /
dark-details pic1 / truss-region texture / dots):
  continuity 692/64/581/0 (his woodwork praise, his half bedpost),
  brighter-wins 0/91/-/0, ground-decides@60 8/47/599/0 (IN THE TREE
  NOW), neighbours 119/49/701/0, support-counting 320/32/674/0,
  averaging 0/73/-/102-dots-DISQUALIFIED.
No single horizontal rule wins all three witnesses. VISUAL EVIDENCE:
arcimg-truss-compare.png on the Desktop (master/round3/gd/support at
8x): round 3 and support keep the truss strokes, ground-decides thins
them. PROPOSED FOR THE RESUMED SESSION, undecided: partition by
black-involvement: a disagreeing pair with a near-black member (the
bedpost against the void) resolves by ground-decides; without one
(truss on wall) by support-counting; chimneys land at ground-decides'
47. Also still open, unchanged: the window-light JEWELS (a REAL but
SECONDARY finding: warm lights render white; the hint-sidecar revival
proposal + the visual disc preview arcimg-hint-proposal-1.png stand,
deferred until the truss is settled), the authored fallback table,
picture 8's C64 sky, P4/A8/corpus/goldens. The scratch preview dirs:
beach/{noweave,gd,nb,sup,avg,...} map to the scoreboard rows.

## CHECKPOINT: the arc_image quality round, mid-flight (2026-08-11, compaction)

Self-sufficient resume state, superseding the 2026-08-10 checkpoint above
(read this one; that one's OPEN list is stale). THE WORKING TREE IS THE
ROUND: tools/arcimg.py carries UNCOMMITTED work across four converters.
`git diff tools/arcimg.py` shows it. Nothing commits until Stefan's eye
gates a target; goldens freeze only what he approves.

APPROVED BY STEFAN, DO NOT REOPEN WITHOUT HIM:
- CPC. The dark sanctuary (source luma < 48 renders flat and literal,
  only entries themselves dark may fire, picked luminance-first from the
  SOURCE, no error in or out), the expression clamp, and the BEDPOST FIX
  (pairs collapse by agreement; a disagreeing pair keeps its BRIGHTER
  member, never an average). His verdict: "CPC is flawless now".
- C64. Everything above plus his AUTHORED 14-ROW PALETTE TABLE in
  _CPC_TO_COLODORE (CPC ink -> preferred Colodore homes, in order),
  the COLLAPSE rule (all listed homes taken -> share the first choice,
  never steal a stranger's colour) and the BLUE SHADING ORDER (whoever
  holds the two Colodore blues is re-paired by luminance). His verdict:
  "Major success. C64 is approved."
- PLUS/4. Renders the SAME decision: _inks_to_colodore computes the
  family's colour choice ONCE in Colodore space and the TED reproduces
  it. The bug that cost three attempts: the P4 cell solve judged against
  the raw CPC ink (src_px), so every upgraded cell re-derived its own
  answer and discarded the family choice (green sky came back teal, grey
  fog violet). It now judges against _COLODORE[to_col[i]]. His verdict:
  "finally. approved".

THE DOCTRINE BEHIND ALL OF IT, his words: wherever the pipeline is
uncertain, COLOUR IDENTITY IS RETAINED, never improvised. It has now
fixed four separate defects at four levels: diffusion (the sanctuary),
expression (the clamp), ink mapping (the table), and cell solve (the
P4 fix). Expect the same class of bug wherever a stage re-optimises.

THE A8, STILL OPEN, and the only thing left before bookkeeping:
- Architecture: Stefan RULED (2026-08-11) that it keeps his July
  direct-from-master route. A Colodore-inheritance version was built and
  measured (mean distance to the C64 picture 76.0 -> 50.6 -> 39.2 as
  processing was stripped) and he rejected it: "revert back to the
  original master inheritance we had but apply THIS fix to it".
- In the tree now, on top of the July converter: hue-loyal substitution
  (PROPORTIONAL, d *= 1 + _A8_HUE * dh, _A8_HUE = 6.0; an additive wall
  was tried first and made everything flee to black, since neutrals
  escaped the penalty); the BEDPOST FIX at full strength (_A8_PAIR =
  1.0, a blend weight where 0.5 is the old averaging; a threshold dial
  was tried and did nothing, those pairs sit far beyond any threshold);
  and force_black = False (the forced black canvas made every strip with
  a dark tenth spend one of four colours on pure black: corpus black
  share 37.1% against the masters' 31.2%, now 28.0%).
- HIS STANDING COMPLAINT, unresolved: "still too much black and a lot is
  flattening way too much", shown on pictures 6 and 18. A per-scanline
  palette election was tried and REVERTED the same hour (the format does
  carry four registers per line, and distinct colours rose 11 -> 17, but
  neighbouring lines elected independently and locked into full-width
  stripes; the flat regions stayed flat). Tree is back to per-8-line
  strips, verified 22/22 identical to the pre-experiment build.
- NOT YET TRIED: an election that reasons about the picture rather than
  one strip at a time (global or region-aware), and the segment-analysis
  thresholds (mass >= 120, dmass >= 40, bmass >= 10) which are tuned for
  8-row strips and were only ever validated in July.

WORKING METHOD, restated because it was violated twice today: LOOK AT
THE OUTPUT before reporting. Metrics have misled repeatedly this round
(the truss metric used a 40-unit threshold on a 36-unit contrast and saw
nothing; the P4 mapping measured healthy while the picture was wrong;
the per-scanline change measured better and looked worse). Previews go
to Stefan's Desktop as arcimg-00..21.png, MASTER on top and the target
below, two tiers unless he asks otherwise; the whole corpus, never a
crop, never a subset. His eye gates; mine only locates.

AFTER THE A8: re-freeze the stale goldens (12 failing now: 4 CPC, 4 C64,
4 P4; the A8's 4 will follow), then ONE commit carrying this whole round
into PROGRESS. Note for that commit: the goldens froze three of the
defects found this round as correct, which is worth saying out loud.

## 2026-08-11: the arc_image quality round, closed on Stefan's eye

All four retro targets approved. The two CHECKPOINT sections above are
closed; this entry is the record.

STEFAN'S VERDICTS, in the order they were given. CPC: "CPC is flawless
now". C64: "Major success. C64 is approved and I am genuinely happy with
the results". Plus/4: "finally. approved". A8, after seven rounds:
"Hell yes, that's it. A white canvas stays white cracked it. All images
look perfect now."

HIS RULINGS ALONG THE WAY, each of which overrode a measurement of mine:
- The colour table for the C64 is HIS, fourteen rows authored by hand
  from the two palettes side by side. A generated table was tried first
  and he rejected it: "the older one was genuinely better when all
  colours worked together".
- The A8 keeps its July direct-from-master route. A Colodore-inheritance
  version measured closer to the C64 at every step and he rejected it on
  sight.
- Widening the pixel guard was rejected: "guard 90 is certainly not the
  answer, look how many details and colours are lost in picture 7, the
  iconic picture 8 losing the moon".
- Repairing the diverging diffusion was rejected on its artefacts: "it
  creates dots everywhere, look at the ceiling in the chapel". The
  divergence is real and measured; the picture disagreed, so the picture
  won. It stays in the tree as a dial at zero.
- Continuity 25 is his choice over 15, made against the full corpus.
- Every alternative I built to beat it (two-pass election, near-tie
  tolerance, seam pricing, use-it-or-lose-it floors, short palettes) he
  judged no better, and the measurements agreed once looked at.

THE DOCTRINE, his, and now proved eight times: WHEREVER THE PIPELINE IS
UNCERTAIN, COLOUR IDENTITY IS RETAINED, NEVER IMPROVISED. Every defect
found this round was the same fault in a different place, a decision
taken on an AVERAGE instead of on what is actually there:
- diffusion averaged a dark pair into a tone that quantised away (the
  bedpost fix);
- the strip analysis averaged pure black with a vivid blue into a colour
  present nowhere in the picture, then elected a palette with no blue in
  it, which is why a whole ceiling rendered black;
- the election's error metric averaged brightness over hue, so every
  strip bought a luminance ladder instead of the picture's colours;
- the tint rule ran in one direction only, so a black pixel sat on a
  saturated register for free and a barn's timber vanished into blue;
- the canvas pass averaged a grey majority with a warm minority and
  painted a stone wall skin colour across the full width.

THE LAST ONE, which he found by eye and named exactly: "the mountain
part that would be in this colour is genuinely small and for that it
paints over the whole row, that feels off, disproportional". The canvas
pass has always documented itself as leaving true black AND BRIGHT WHITE
alone, and only black was ever guarded. One strip's white canvas tipped
pink on a 50/50 split while its neighbours stayed white, and a corner of
the picture painted a band across the whole width. Guarding white, as
the code always said it did, closed the round.

THE BEDPOST FIX, RE-OPENED AND REPAIRED at his request once the rest was
right ("that is something I want to look into again now that we are so
close"). It kept the BRIGHTER member of a disagreeing pair, which is
correct on the CPC where it was written and half a rule on the A8: it
bought thin bright lines by destroying thin dark ones, corpus-wide from
83.9 percent of dark lines kept down to 68.6, below what plain averaging
managed. It now keeps whichever member departs further from the ground
either side of it. Bright lines 90.8 percent, dark lines 96.4, and the
mean pixel error fell to its best figure of the round.

THE GOLDENS FROZE THREE OF THESE DEFECTS AS CORRECT, which is worth
saying plainly: a golden test proves a converter has not changed, never
that it was right. Sixteen were re-frozen here against Stefan's eye, the
only gate this work has. Suite 1374 green.

METHOD NOTE, earned twice this round the hard way: LOOK AT THE OUTPUT
BEFORE REPORTING. A metric said the per-scanline palettes were better
while the picture had gained stripes; a metric said the new-colour price
healed three pictures while it put a red band back through one of them.
Numbers locate, they do not judge.

## CHECKPOINT for pickup (2026-08-11): B12 is mid-R4, not near B13

Self-sufficient resume state. It supersedes the two mid-flight
checkpoints above, which are closed: the quality round they describe
landed as 7e8d00c and the entry above it is its record.

WHERE WE ACTUALLY ARE. B12, wave R4. Stefan corrected a claim of mine
that we were at B13 ("Many of the systems are not implemented and don't
have a probe yet. How do you come to the conclusion we are at B13. We
are far away from that?"). He is right and the mistake is worth naming:
four machines passing his eye is not a milestone closing. The ledger in
arc_image/reference/design.md is the authority on the wave order and the
done-tests; read it before planning anything here.

THE COUNT, measured, not remembered:
- Formats defined in arcimg.TARGETS: 15.
- Converters implemented: 9 (AMI, AST, DOS, C64, ZX3, CPC, A8, P4,
  TRSM4), with 9 matching probes under arc_image/probes/.
- SIX TARGETS HAVE A FORMAT AND NOTHING ELSE, no converter, no probe:
  MSX1 and MSX2 (both still inside R4), Apple II, Spectrum Next and
  MEGA65 (R5), and the C128 VDC (an undecided ruling, R5).

WHAT R4 STILL OWES, its own done-test: "corpus conversions approved;
probes green in atari800, openMSX, and xplus4, both modes."
- MSX1 and MSX2 converters do not exist. That is the bulk of it.
- The A8 and Plus/4 conversions are approved as of this round. Whether
  their probes have been through atari800 and xplus4 under Stefan's eye
  in BOTH modes is not recorded here; ASK HIM, do not assume. Emulators
  run on his machine and he gives the path (never launch or install one
  unprompted).
Then R5 (Apple II with the DHGR variant, Spectrum Next, MEGA65, the
C128 ruling executed) and R6 (the public interpreter contract, arcimg
2.0, docs/00 and PROGRESS synced, the size ledger final).

WHAT THE JUST-FINISHED ROUND SETTLED, so it is not reopened by accident:
CPC, C64, Plus/4 and A8 conversions are APPROVED BY STEFAN on the full
22-picture Rabenstein corpus. That closes the R4 amendment's re-gate for
C64, CPC and A8 and takes the Plus/4 with it. It says NOTHING about
probes. The Spectrum keeps its R3 solver and has not been re-gated.

THE TUNING SURFACE now lives in named module constants in tools/arcimg.py
(all _A8_* around lines 2060-2690). Everything Stefan rejected is still
there as a dial at its off value WITH THE REASON IN THE COMMENT, so no
one re-tries it blind: _A8_DRIFT and _A8_ECLAMP (the diffusion divergence
repair, real but it scatters dots on a smooth ceiling), _A8_TWOPASS (the
picture-wide election, measured worse than the chain), _A8_TOL (near-tie
continuity), _A8_SEAM with _A8_HOUSED (per-family join pricing),
_A8_FEWER and _A8_PRICE_NEW (short palettes; they never fire because
taking the neighbour's whole palette is already free). The live settings
are _A8_EXACT 8, _A8_TINT 3 both ways, _A8_ONE_BRIGHT 1, _A8_CONT 25,
_A8_PAIR 1.0 with _A8_PAIR_EXTREME 1, _A8_CANVAS_SHARE 0.5 and
_A8_CANVAS_WHITE 200. Turning the whole set to its off values reproduces
the pre-round build; that was verified at every step and is the way to
check any future change is doing what it claims.

THE DOCTRINE to carry into the remaining targets, because it caught
every defect this round and the same five traps are waiting in MSX and
Apple II code: wherever the pipeline is uncertain, COLOUR IDENTITY IS
RETAINED, NEVER IMPROVISED. In practice, distrust any AVERAGE: of two
pixels, of a colour cluster, of brightness against hue, of a majority
against a minority. Read the entry above for the five places it hid.

WORKING METHOD, unchanged and non-negotiable. Stefan's eye is the only
gate. Previews go to his Desktop as arcimg-00..21.png, the WHOLE corpus,
full pictures, never a crop and never a subset, MASTER on top and the
candidates below, labelled. LOOK AT THE OUTPUT BEFORE REPORTING: metrics
misled four separate times this round and his eye was right every time.
Discuss before implementing; a design question is not authorization.

## AMENDMENT to the pickup checkpoint (2026-08-11): R3 is not closed either

Stefan's correction to the checkpoint above, and it changes the order of
work: "I was very unsatisfied with ZX Spectrum conversion and we wanted
to try to inherit Spectrum from MSX1. So Spectrum was R3, so we are not
completely through with R3 either."

Both halves check out against the design record, which was contradicting
itself: its milestone list called R3 COMPLETE while the same document
carried the ZX3 solver re-gate as an open work item. R3's format, probe
and codec work IS done; the CONVERSION is not. The +3 alone kept its
original R3 solver when the Polizei family was rebuilt around it, and
his verdict on re-view was that the clashes are awful. It was parked
twice: behind the Plus/4 (2026-07-17), then behind the Polizei rebuild.
The Plus/4 has now landed and is approved, so nothing blocks it.

THE ORDER THAT FOLLOWS, and the reason it is not negotiable. The
Spectrum derives FROM MSX1 (section 4, restated by Stefan today): MSX1
is its nearest palette kin with the milder attribute constraint. The
argument is geometric, so no substitute base will do. A C64-class
160-wide base lacks the PIXEL DENSITY a few-colour Spectrum needs; the
machine's strength with a restrained palette is its 256-wide detail, and
only a 256-wide base supplies it. So MSX1 IS A DEPENDENCY OF R3's
CLOSURE, not just another R4 target, and it comes first.

The conversion philosophy for the Spectrum is already ruled and should
not be re-derived: near-monochrome dithered form, one dominant ink per
region, a FEW deliberate colour accents (a sky zone, a moon), plus
dark/bright pairs of one colour for highlighting. Stefan confirmed from
the originals that the historical Rabenstein Spectrum art worked exactly
this way. A full-palette quantize is what makes the current output
clash.

REVISED PICKUP ORDER: MSX1 converter, then the Spectrum re-gate deriving
from it (closing R3), then MSX2, then the R4 probe question, then R5.
arc_image/reference/design.md is updated to match: its R3 bullet no
longer claims completion. docs/00 needed no change, it carries the wave
order only through B12 and never claimed R3 was closed.

## 2026-08-11: the ladder says so (Actaea 1.3.9)

A new adopter running Arcturus on Windows 11, an RPi 5 and Ubuntu
reported that "Win 11 balks at Actaea" while Windows Frotz played the
same z5 fine. Triage found no bug: the standalone must go through the
Python launcher on Windows (py actaea story.z5; Windows reads no
shebang), and his Python likely lacks tkinter, which drops the default
ladder window -> curses -> pipe straight to the bare pipe, since native
Windows has no curses either.

What made it FEEL broken was our own silence. docs/06 has always
promised that Actaea "degrades to the next mode down and says so", and
only --console kept the promise; the default ladder stepped down without
a word. Doc and code disagreed, so per the standing rule the doc won:

- Every step down the ladder now says so on stderr, and the tkinter
  note carries the exact remedy for THAT platform (the python.org
  installer's tcl/tk tickbox on Windows, brew install python-tk on a
  Homebrew Mac, the python3-tk / python3-tkinter package on Linux).
- Stefan asked whether Actaea could prompt to INSTALL tkinter; ruled
  down to the precise hint: tkinter is part of the Python build, not a
  pip package, so the only automated route would be running the system
  package manager under sudo, which an interpreter must not do.
- docs/06 section 1 gains the Windows paragraph: the py launcher, the
  tickbox, the one-line test (py -c "import tkinter"), and why the
  ladder on a tkinter-less native Windows lands in the pipe.
- Three ladder tests hold the promise; suite 1377.

## 2026-08-11: the room lists its things in one sentence (arcc 1.3.63, Cosmos 1.5.0)

An adopter request from the Discord (jens.leugengroot: can more than one
item share a line, "There is a MRE, a lantern and a backpack here",
instead of a sentence per item?), seconded by EdwardianDuck, who had
already mapped the override route and the two-pass shape it needs.
Stefan's ruling in the thread, verbatim: "it should be the standard
behavior of the library. Separate items below the room description only
if they have their own intro line." His calls on the design: the frame
stays "You can see", no approval round needed for the rest, and the
default-behavior change makes this Cosmos 1.5.0.

The build: describe_room now only COUNTS the plain items (appearance
and intro paragraphs unchanged above), and one new language-layer block,
list_room, speaks them all in a single sentence through the run idiom
name_contents already owned. Which items are plain is one shared
predicate, room_plain, asked by both the count and the printing, so the
two passes cannot drift (EdwardianDuck's insight, done once in the
library). The closed qualifier and the contents-in-passing ride along
inline per item. A single item still goes through list_item untouched,
so adopters who overrode list_item keep their wording where it counts
most; the sentence itself is overridable as list_room.

All three languages speak it natively: English "You can see some
scissors and a brass lamp here.", German case-correct through the
existing ${a:acc} machinery ("Du siehst hier eine Laterne, einen
Rucksack und eine Brotzeit."), Spanish "Ves una linterna, una mochila y
una ración." Verified by eye on dfrotz in all three.

Cost, measured and repriced across all 48 example ceilings: +176 bytes
(a handful at +172 to +184), the predicate plus the run. The z8 Cloak
ceiling moves with it. Handbook chapter 5's listing passage rewritten,
WHATSNEW rotated, suite 1377 green.

## 2026-08-11: the stale standalone (arcimg 1.31.0)

Stefan's README check caught a real gap: the arc_image quality round
(7e8d00c, all four retro converters repaired and approved) landed in
tools/arcimg.py without a version bump, so build/arcimg was never
regenerated and the SHIPPED standalone still carried the pre-round
converters. Anyone downloading arcimg got the defective CPC, C64,
Plus/4 and A8 conversions the round had just fixed. Now arcimg 1.31.0,
amalgam regenerated, README table synced (the arcc/Cosmos/Actaea rows
were updated with their own bumps earlier today). The lesson is the
standing habit restated: a behavior change IS a version bump, and the
bump IS the amalgam regeneration; the round's size (seven approval
rounds over two days) made it feel like work-in-progress when each
approval was already a release-worthy change.

## 2026-08-12: the MSX1 conversion, banked on Stefan's eye (arcimg 1.32.0)

The first new converter since the quality round, and R4's third of four.
Stefan's verdict on the banked build: "really good", then "it passes
almost 100%", with the known limits recorded rather than papered over.

HIS RULINGS, which now bind the whole remaining 8-bit family:
- THE HINT SIDECAR IS AN AUTHOR'S LAST RESORT, NEVER THIS TOOL'S CRUTCH
  ("arcimg will bring the best results without any help or fix files").
  Ruled when a moon fix reached for 8.hint; the fix was rebuilt from the
  picture itself (the A8's moon rule plus a contiguity-and-fatness test,
  an opening against tendrils). MEASURED the same hour: the four
  approved converters produce byte-identical output with and without
  the only hint in the corpus, so the quality round's approvals never
  depended on a sidecar.
- GEOMETRY: the MSX1 window is columns 24..279 of the master, ruled by
  eye against pure top-left and against centre; and the Spectrum's
  centre crop was WRONG, part of its problems, to be replaced when the
  Spectrum re-derives from MSX1's window.

THE CONVERTER as banked: exact per-octet pair solve (all 105 pairs
against the source pixels), the tint-loyalty TRIAD (hue against hue;
neutral pays for a chromatic home; and the third leg, found here, a
chromatic pays to fall into a substantially DARKER neutral, which took
picture 2's timber from 6.5 to 95.5 percent red, black had been eating
the lines for free), the dark sanctuary with the saturated-dark
exemption, and the moon rule. Goldens frozen on pictures 2, 8, 10, 12.

THE DAY'S FAILURES, recorded because they cost hours and must not be
re-tried blind (all reverted byte-exact, all documented in the code):
- Ordered halftone in the octet assignment: moth-eaten holes.
- The picture-global ink map (the C64 recolour mechanics computed):
  fixed the dotted timber measurably but flattened the corpus; a
  three-ink octet loses its highlight minority under ANY consistent
  rule, and per-octet freedom turns out to be doing aesthetic work.
- Vertical continuity between octet rows: new issues, no help.
The lesson the day kept teaching: metrics locate, Stefan's eye judges,
and each fix went to his eye BEFORE the next was attempted only in the
second half of the day, which is when progress became real.

OPEN, honestly: row-oscillation stripes in mottled regions (the one-row
color cell itself; needs picture-level reasoning that does not flatten,
nothing octet-local will do), picture 7's curtain two-blues contrast,
picture 10's left wall. The openMSX probe is still owed to R4's
done-test. Next per the standing order: the Spectrum re-derivation from
MSX1, which closes R3.

## 2026-08-13: the Spectrum settles, black and white by ruling (arcimg 1.33.0)

The hardest machine of the family closed on Stefan's design judgment,
not on a converter victory. The ruling, now in docs/07 and the code:
due to the Spectrum's attribute restrictions (two colors per 8x8 cell,
one shared bright), the AUTOMATED conversion path is deliberately a
reasonable-looking black and white artwork; COLOR on this machine
belongs to authors, who can supply their own image for any picture at
any time through the first-class scr/unscr polish loop (a hand file is
stamped and convert never overwrites it).

THE SHIPPED FORM, built across two days under his eye, every step
gated: the C-banded pattern stipple. Tone from the master at the ruled
window, percentile contrast stretch, a gain curve with solid floors
(bright is white, dark is black, HIS sentence become an algorithm),
the hand-artist's five stipple levels with band edges that adapt to
each picture's tonal quartiles ON A LEASH (raw adaptation collapsed
picture 9's edges to 0.11 and ate the bedsheet; the leash holds each
edge inside a window around the classic values), the moon rule with
the yielding glow (the disc solid, its halo dropping one level, after
a rim experiment egged picture 1 and was reverted), all of it in
BRIGHT white ("all WHITE in WHITE, not dark white"), the vibrant tier
that color washes would live on. Goldens frozen on 2, 8, 10, 12.

WHAT DIED ON THE WAY, all of it rendered, corpus-reviewed, and
rejected by his eye, recorded so nobody re-walks it: the MSX1-derived
color route with the sibling table (approved-then-retracted when the
attribute clashes surfaced on re-view; deleted on his order after a
final render), the near-monochrome quiet philosophy (ate thin timber),
an externally authored role-over-hue table (healed one picture, cost
the church its two reds), general fg/bg mixes across chromatic pairs
(no axis preserves identity across hues; twice shredded the church),
the inkline comic route (ugly), the rabenstein-grammar route measured
off his own hand art (right grammar, wrong league), Bayer at native
resolution (crosses), Atkinson (rejected), and an MSX1-sourced tone
field (TMS owns no darks; the mono lost its blacks). The 22-way and
7-way preview rounds that drove the choices were his call and worked:
"I need to make the decision visual and not blind."

HIS ORIGINALS ARE IN THE REPO: the 21 hand-authored Spectrum pictures
of the 2022 +3 release, extracted from the DSK (CPC data format, the
.ZXS band layout decoded: standard interleave rows 0..63, compacted
half-third 64..95, 384 attr bytes) and cross-validated byte-identical
against the loose divMMC files. They live in
arc_image/masters/Spectrum_Masters as the probe test assets and the
permanent reference for what this machine's art should be.

Still owed on B12: the openMSX probe (R4) and the ZX3 probe re-run
against the new art path; the row-oscillation stripes and picture 7's
curtain contrast on MSX1; wave 3's MSX2. R3's conversion question is
CLOSED by the ruling above.

## CHECKPOINT for pickup (2026-08-13, compaction): B12 after the Spectrum ruling

Self-sufficient resume state; supersedes the 2026-08-11/12 checkpoints
above. THE TREE IS CLEAN: everything through the Spectrum ruling is
committed and pushed (7e99034, arcimg 1.33.0).

WHERE B12 STANDS, wave by wave (the ledger in
arc_image/reference/design.md is the authority):
- R2 (16-bit trio): long closed.
- R3 (C64, CPC, Spectrum): the CONVERSION question is now CLOSED. C64
  and CPC approved since July; the Spectrum settled 2026-08-13 by
  Stefan's design ruling: the automated path is deliberately a
  reasonable black-and-white artwork (route "canopus", the C-banded
  pattern stipple, bright white 0x47 on black, leashed adaptive band
  edges, solid tone floors, moon rule with yielding glow; ZX3 goldens
  frozen on 2/8/10/12), and COLOR on this machine belongs to authors
  through the scr/unscr polish loop (docs/07 documents it; hand art is
  stamped, convert never overwrites it). The ZX3 PROBE predates the new
  art path and should be re-run when probes come up.
- R4 (A8, Plus/4, MSX1, MSX2): conversions for A8, Plus/4, MSX1 are
  approved and golden-frozen. The MSX1 round's residual artifacts were
  RULED CLOSED as super minor (Stefan, 2026-08-13): no further
  machinery. STILL OWED: the MSX2 converter, and THE OPENMSX PROBE.
- R5 (Apple II, Next, MEGA65, C128 ruling) and R6 (the public
  contract, arcimg 2.0): untouched.

THE PROBE DEBT IS THE STANDING SHAME AND THE FIRST REMINDER: R4's
done-test needs probes green in atari800, openMSX, xplus4, BOTH modes,
under Stefan's eye. Whether A8 and Plus/4 ever went through their
emulators post-quality-round is NOT recorded; ASK HIM. I failed to
flag the missing MSX1 probe before sailing into the Spectrum and he
called it out ("I am scratching my head why you didn't remind me to
friggin build a probe"); do not repeat that. Emulators run on HIS
machine, he provides paths, never install or launch unprompted.
openMSX is downloaded in ~/Downloads (dmg + system ROMs zip).

TEST ASSETS FOR THE ZX/MSX PROBES: his 21 original hand-authored 2022
Spectrum pictures live in arc_image/masters/Spectrum_Masters (extracted
from the +3 DSK, cross-validated against the divMMC release; the .ZXS
band layout is decoded and documented in the 2026-08-13 entry).

THE SPECTRUM ROUTE DIALS in tools/arcimg.py, all named: _ZX3_ROUTE
("canopus" shipped; "rabenstein" and "inkline" experimental, kept
documented; "derived" DELETED on his order), _ZXC_TEXTURE ("stipple"
shipped; "bayer" selectable; "atkinson" rejected), _ZXC_ADAPT (1, the
leashed C bands), _ZXC_GAIN/_ZXC_WHITE/_ZXC_BLACK (the tone law),
_MS1_* (the MSX1 dials, including every documented rejected
experiment).

THE WORKING RULES, hard-earned and standing: ONE mechanism change per
Stefan review, never stacked (three stacked architectures each cost a
day's trust); his eye gates, metrics only locate; LOOK at the output
before reporting; reverts are verified byte-identical against the last
reviewed build; the hint sidecar is an author's last resort, NEVER the
tool's fix; previews go to his Desktop as arcimg-00..21.png, whole
corpus, full pictures, labeled tiers at 3x, MASTER on top; he decides
visually, so when he must choose between approaches, render ALL
candidates (the 7-dither preview round is the model). His hand-authored
art is the quality bar on machines where he has authored; the converter
does not compete with it, it serves authors without hand art.

NEXT, in the order the record implies: (1) the probe round: MSX1 on
openMSX first (he ruled the probe debt gets discussed), the ZX3 probe
re-run, and the A8/Plus/4 probe question put to him; (2) MSX2 (Screen
5, quantize class, likely quick); (3) R5. The Spectrum color question
is settled; do not reopen it.

## 2026-08-13: the ZX3 probe green on Fuse, and the extraction confesses (arcimg 1.33.1)

THE PROBE VERDICT IS STEFAN'S AND IT IS GREEN: his own picture 8, both
bands, on the +3 under Fuse. The pairs are no longer conversions but
HIS HAND ART carried through the exact author loop the Spectrum ruling
promises: master to .scr, `arcimg unscr` back as a stamped hand-authored
12.ZX3, `slice9` for the 9. One probe pass now proves the ring loader
and the documented color path together.

TWO OF HIS CALLS SHAPED THE SESSION. First, the hand-off emulator is
FUSE (ZEsarUX retired from the human gate for accuracy; it stays for
scripted ZRCP readback only). Fuse crashes on the 128K snapshot and a
.sna forces the machine anyway, so the probe now ships as probe.dsk, a
self-booting +3 disk built with Haumea's mk_plus3.py; its boot sector
opens TRITON.BIN by hardcoded name, and the first disk failed until
the payload wore that name. Second, when the screen showed one
wrong-colour corner cell, he trusted the emulator and pressed; the
emulator was honest and the bug was ours.

THE EXTRACTION CONFESSES: the .ZXS format begins with its band height
in rows (0x60 = 96), bitmap at offset 1, attrs after. The first
extraction read everything one byte early: every bitmap sheared eight
pixels, every attribute shifted one cell, the last bitmap byte posing
as the corner attribute (his cyan cell). Proof came from his
first-Rabenstein UI files: the 48-row and 192-row variants fit the
height formula exactly, and picture 0 decodes byte-perfect against its
.scr ground truth. All 21 masters in Spectrum_Masters are regenerated
from the divMMC release and palette-checked. The lesson is an old one
wearing new clothes: my render matching my own decode proved nothing,
because both sides shared the bug; only his eye on real hardware
truth-tested the chain.

THE MACHINE CHECK ALSO CAUGHT A TOOL BUG BEFORE THE EMULATOR DID:
slice9 only knew the C64 family's planes. It never sliced the
Spectrum's attrs (a mode-9 slice kept all 384 mode-12 attribute bytes,
three rows of colour decoding into the interpreter's text area),
crashed outright on an MSX1 native, and dropped the hand stamp, so a
sliced piece of hand art lost its convert-will-never-overwrite
protection. One patch with a regression test (arcimg 1.33.1, standalone
regenerated); the MSX1 leg is needed for the openMSX probe pairs next.
The full-probe mini-Z80 simulation and the master-to-scr reconstructor
are committed beside the probe (run_probe.py, png_to_scr.py), no
longer session-only harness.

Still owed on B12: the openMSX probe (R4), MSX2, and the A8/Plus/4
post-quality-round probe question. The ZX3 probe debt is PAID.

## 2026-08-13: the openMSX probe, green on the HitBit

R4's standing debt is paid: Stefan's verdict on openMSX 21.0 (his Sony
HB-75P with a disk drive) is green for picture 8's approved MSX1
conversion, the 9/12 cycle. The probe is the reference MSX1 loader for
the format, and the friendliest of the whole family: Screen 2 with the
implicit identity name table, then both sections stream through the
SAME ring decoder the Spectrum and CPC probes use, straight to the VDP
data port; the port's auto-increment does all the walking, so the emit
vector is two instructions and there is no walk state at all.

The method held from the Spectrum round: the mini-Z80 simulation (now
with a TMS9918A write model) proved VRAM and the register file
byte-exact for both pairs BEFORE the emulator, so the hand-off was
about pixels, not loader bugs. The delivery vehicle is a bootable Disk
BASIC .dsk; FictionTools' dsktool segfaults on create, and the
reference repo is never modified from here, so mk_disk.py writes the
720K FAT12 image itself, mk_plus3-manner, and dsktool's still-working
reader cross-validated it (listing and extraction byte-identical, an
INDEPENDENT check, the circularity lesson applied the same day it was
learned).

One self-inflicted scar for the record: macOS's case-insensitive
filesystem let an extracted PROBE.BIN overwrite probe.bin during
validation, and a cleanup deleted it; one reassembly restored it. Copy
foreign-cased twins somewhere else.

R4 now owes only the MSX2 converter, and Stefan's answer on whether
the A8 and Plus/4 probes ever ran after their quality rounds. Then R5.

## 2026-08-13: the probe round pays every debt, and the corpus becomes the shop window

SEVEN MACHINES GREEN UNDER STEFAN'S EYE IN ONE DAY: Atari 8-bit on
Altirra and Plus/4 on xplus4 ("picture perfect": the A8 picture 8 is
the conversion the community suspected could not be automated), C64 on
x64sc and CPC on CPCemu ("just as I expected and remember them"), the
Model 4 on trs80gp, MSX1 on openMSX, and the Spectrum's new
four-picture cycle on Fuse (his hand art 8 and 14, then the automated
black and white of both). Every probe pair had lagged its approved
converter by whole quality rounds; all were regenerated from the
golden-frozen current output, machine-verified where a harness exists,
and judged on the emulator bench Stefan ruled this same day: Fuse,
CPCemu, Altirra under Wine, VICE, openMSX, trs80gp. ZEsarUX is retired
from the human gate ("it let so many bugs pass"); picture 8 is the
benchmark scene on every machine.

THE CORPUS CURRENCY RULE, Stefan's ruling, now standing: the committed
corpora and previews are quality reporting to the outside world; "no
one will give arc_image a test run, they look at the corpus to get a
first idea." Measurement showed every 8-bit corpus directory stale
(the C64 by 40% of pixels, the P4 by an encoding convention so old the
files mis-decoded). All regenerated: c64, cpc, p4, a8, trsm4, the ms1
corpus created, stress-out across all ten converter targets, the cloak
set, and some 200 previews. THE ZX3 CORPUS IS NOW HIS OWN HAND ART,
brought in through the author loop and hand-stamped, exactly what the
Spectrum ruling promises authors; the automated black-and-white route
shows beside it in previews/zx3/auto.

THE BEACH VINDICATION, his story worth keeping: the early days tuned
the beach stress picture one image at a time, then he flipped to
corpus-first optimization and the whole family improved. Today the
freshly regenerated beach conversion appeared on the CPC bench by
accident, and he asked whether it was the new one because it "looked
legit like the best conversion that I ever saw of it." It was the new
one, proven by arithmetic. Get the corpus right and the stress image
follows.

ONE SCAR, RECORDED IN FULL: a resync script assumed the .TR4 suffix
was a retired tag; the truth is the opposite (ARC<id>.TR4 is the Model
4's shipping name, his 1.27.0 ruling from Shawn's report), and three
untracked stress files were deleted and rewritten under wrong names.
Repaired within the hour, correct names, current content, nothing
hand-made lost. His rule, verbatim, now in the working memory: "Make
sure this stuff doesn't happen again. If you are not sure about
something you ask me."

B12 after today: R2 through R4 owe nothing but the MSX2 converter.
Then R5.

## 2026-08-14: MSX2 closes R4 (arcimg 1.34.0)

The last converter of wave 3 was the easy half: MSX2's constraint set
(16 of 512, 3-bit guns) is the Atari ST's exactly, so the approved
quantize recipe carried over whole, through the same window as MSX1
so both machines frame the same scene. The codec was the real
decision, and Stefan's R1 assignment stood for its original reason,
now on the record: LZSA2, because the ZX0 packer's cost explodes on
16-bit-class payloads, and a ~6% size sacrifice buys authors a corpus
that converts in minutes instead of half-hours. A fresh measurement
(ZX0 6.5% smaller on this corpus) did not move the ruling; the tool
serves authors first.

The probe carried the vendored reference LZSA2 decoder (spke &
uniabis), executed against every LZSA2 stream in the repo on a
simulated Z80 before anything trusted it, and then taught two lessons
no RAM-only simulation could: the disk system owns the top of RAM
(HIMEM near $DE79 on a two-drive MSX2; the first build loaded over
the disk ROM's work area and reboot-looped the machine, the resets
Stefan watched live), and the V9938 increments its own bank register
when the VRAM address counter crosses 16K (the second build painted
picture 8 into invisible VRAM). Both were found by MEASUREMENT on
openMSX itself: the emulator is fully scriptable, and the diagnosis
ran breakpoints, VDP watchpoints, HIMEM reads, keystroke injection,
and VRAM censuses headlessly, a new standing capability of the bench.
The fixed probe cycled 9/12/9 under script before his eye saw it;
his verdict: "probe perfect."

R4 IS COMPLETE: every 8-bit target of the current set converts,
probes green, and reports itself honestly in the corpus. Next: R5
(Apple II and DHGR, Spectrum Next, MEGA65, the C128 ruling), then R6.

## 2026-08-14: Shawn's Agon lands (arcimg 1.35.0)

The parked request from Shawn Sijnstra, fulfilled to his own spec:
VDP mode 3, 640x240, the full fixed 64-color RGBA2222 cube, raw rows,
and RLE as his codec ruling ("it reduces the requirement for memory
management, and the code overhead is small"). The interpreter author
is the consumer, so his answers became the chapter.

The target got the full treatment in one day: converter (the fixed
cube needs no palette solving at all; 2x horizontal, the Model 4's
aspect logic), corpus and previews under the shop window, goldens
frozen, and a probe that is the purest loader of the whole family:
the RLE decoder's emit IS the VDU write, so the band streams down the
serial link into a VDP buffer and never exists in eZ80 RAM. Stefan's
verdict on the emulator: "faithful."

The build taught the Z80-mode MOS lessons now in doc 08 C.12: every
MOS call from Z80 mode must ride the .LIS-suffixed RST opcodes (the
first build jp.lil'd into the flash handlers, which discards the
return linkage and painted the band as text glyphs), and the display
is a conversation over the Buffered Commands API, big-endian table in
hand, little-endian wire on the tongue. Bench archaeology along the
way: fab-agon-emulator 1.2.3's macOS build never boots the modern
firmware; 1.2.2 does, and a marker-file autoexec is the programmatic
proof of boot, a trick worth keeping on a machine whose SD card is a
host directory.

The family now stands at FIFTEEN formats, TWELVE probe-proven. R5
still waits: Apple II, Spectrum Next, MEGA65, the C128 ruling.

## 2026-08-14: TAKE ALL speaks every shipped language (Cosmos 1.6.0)

An adopter's German game hit "nimm alles" and the story answered that
it did not know the word: the takeall granule was English-worded, as
several granules deliberately are. Now it speaks all three languages
the compiler ships: its words moved into `when language` groups
(English keeps ALL and EVERYTHING with the FROM filler; German gets
ALLES and ALLE, and needs no filler at all, since AUS is already the
off-particle and phrase matching compares dictionary entries, not
flags; Spanish gets TODO with the bare DE as noise), and its three
messages moved out of the granule into the language packs, the
library-granule rule pathfinding modeled.

One German subtlety earned its guard: "nimm ... aus" compounds to
take_off (ausziehen), so TAKE ALL FROM undressed instead of sweeping.
The compound now stands down when an all-word is typed, and the guard
folds away in a game without the granule. The dictionary taught its
own lesson along the way: one flag per word, so German's AUS could
never have been noise (it is the off-particle), and the fix that
looked obvious would have broken switching things off.

THE COVERAGE TABLE, the second task of the report: the handbook's
shipped-granules section now opens with a measured table of which
granule speaks which language: eight speak all three, three are
language-neutral machinery, and four are English by design
(extendedverbs, nautical, use, verbose_exits, plus the debug tool),
where a fork translates exactly the slice a game summons. The audit
that fed the table also corrected two rows the code had drifted from
the assumption on.

Open, Stefan's call: the German pack has no "lass ... fallen"
separable drop (the canonical German phrasing; WIRF and WEGLEGEN
stand in), and the plurals granule's THEM is English by declaration.

## 2026-08-14: LASS ... FALLEN, the canonical German drop (Cosmos 1.6.1)

Stefan's own catch in the takeall review: the German drop verb line
led with WIRF, which is WERFEN, throwing, not dropping ("I am German
but never play German adventures"). The drop family now leads with
LASS/LASSE and the trailing FALLEN declared as a filler word (the
phrase search simply does not count it), so "lass die Lampe fallen"
and "lass alles fallen" both land as the drop they are. WIRF leaves
the drop line entirely and waits for a German throw family;
FALLENLASSEN, WEGWERFEN, and WEGLEGEN stay as synonyms. One dated
reprice: the German example pays 20 bytes for its new dictionary
words.

## 2026-08-14: the sweep becomes hookable, and actions shed their verbs (arcc 1.4.0, Cosmos 1.7.0)

An adopter wanted to veto DROP ALL in one room and found the sweep
unhookable: it ran beside the pipeline, not on it. Stefan ruled the
fix at the language level, not the granule level: a bare `action`
declaration now names an action with no verb attached ("It is
generally a good thing being able to declare actions without verb
attachment. That could in certain circumstances redirect one verb to
a certain action or the other."). The name joins the ordinary
numbering; handlers, when-clauses, action_id, and dispatch all work;
only the keyboard cannot reach it until code sends the player there.

The takeall granule is the first rider: take_all and drop_all are
declared verbless, run_all dispatches them through the standard
chain, and the sweeps moved into default handlers at the end of it.
The adopter's exact wish is now ordinary Arcturus:

    on drop_all when here is TheHut
        say "Better not."

TAKE ALL FROM binds the source as the noun, so a container defends
itself with its own on take_all; `continue` defers to the sweep; an
intercepted sweep costs its turn and ends a chained line. Priced
honestly: 104 bytes, paid only where the granule is summoned; every
other example byte-identical.

## 2026-08-14: the binary model (arcc 1.5.0, Cosmos 1.8.0)

A field report noticed you could extinguish a dead lamp, in both
shipped examples, since release. The flaw was doctrinal, not local:
`switchable` only marked a thing and left every author to write the
same naive handler pair, while open/shut has always been library-owned
state. STEFAN'S RULING closed the asymmetry and renamed the idea: the
attribute is `binary`, naming what the thing IS (only 0 or 1), not
what you do to it; `toggleable` was considered and rejected, and
`switchable` survives as a compatibility spelling that normalizes to
the canon in one sema pass, so shipped games compile unchanged.

The model: the library owns the state (`active`, christened by
Stefan), flips it with default reports in all three languages, refuses
"is already on/off" honestly in the verb contract BEFORE any handler
(validation is never the handler's job, the pipeline's own doctrine),
and couples light on GLOW things: binary + lit declared makes the
default flip carry the light, so a working lamp is two declaration
lines and no code. Flavor handlers override the default and then own
the flip, the same split as everywhere. The already-on/off messages
had been sitting fully translated and orphaned in all three packs,
Spanish gender agreement included: the voice was ready years before
the behavior.

Priced honestly: games without a binary thing are BYTE-IDENTICAL
(any_binary folds the contract, the defaults, and the messages away;
one darkness-detector subtlety fixed en route, since the glow flip
made every game look dark-capable until the detector learned to skip
library-origin lit-writes). The two lamp examples pay their way and
are repriced, dated. Full battery 1259 green.

## 2026-08-14: the one-noun retry, "Tuer aus Eiche" resolves (arcc 1.5.1, Cosmos 1.8.1)

A field report's second finding, the one our earlier reply had wrongly
claimed fixed: "oeffne tuer aus eiche" asked "Was meinst du" while
"untersuche tuer aus eiche" resolved cleanly. Measured before designed:
the one-noun scorer was healthy all along (2:1 for the door), and the
ask came from the positional TWO-noun split alone. OEFFNE carries a
"mit" grammar, AUS is a phrase boundary (it must be, for "gib X an Y"
and its kin), so the split read "eiche" as an instrument nobody meant,
and the question was about that phantom second slot.

The fix follows the grammar, not the example: when the split leaves a
slot ambiguous or empty and the verb's grammar does not require a
second noun, the German pack retries the whole typed range as ONE noun.
A clean resolve wins and the second slot stays empty; anything less
restores the split's own outcome exactly, the "which do you mean"
question, its answer weave-point, and the unknown-word report included.
A genuine two-noun command never enters the retry, because both its
slots resolve; a required second noun (rq2) disarms it entirely.

Verified on fizmo-console: the door opens without a question, the
Truhe stays shut, "gib muenze an bob" still binds both slots, a
genuine ambiguity still asks and takes its answer, and an unknown word
is still reported, never dissolved. Priced honestly: German-only (the
retry lives in german.granule), the German example pays 152 bytes,
every English and Spanish example byte-identical. Four new tests
(tests/test_split_fallback.py), the two rescue cases red on the old
resolver; full battery 1263 green.

One finding for the record: the checkpoint asked whether the Spanish
resolver shares the split shape. It does, exactly (English too, all
three split on flags 8/136/64/32), so the same seam exists wherever a
name contains a boundary word. Whether the retry generalizes beyond
German is Stefan's call, priced per pack.

## 2026-08-14: reproducible builds, a latent defect caught in passing (arcc 1.5.2)

Preparing a byte-identity proof for the next feature exposed a compiler
defect nobody had seen: compiling the same source twice could produce two
different story files. The react dispatcher's catch-all section iterated
the life-cycle event set raw, and a Python set has no fixed order across
runs, so the three event-skip tests emitted in whichever order the
interpreter's hash seed dealt that day. Any object with an `on other`
handler was affected; the files were equally correct and equally sized,
but not identical, and a project that pins story-file sizes and ships
support against exact binaries wants the stronger property: same source,
same bytes. One word fixes it (the iteration is sorted now), and all
three shipped examples now hash identically across runs, verified under
three different hash seeds.

## 2026-08-14: the trigger marker, #words settle their own ties (arcc 1.6.0, Cosmos 1.9.0)

Generous synonym lists are good declaration practice, and they are where
matching ties come from: a chest that helpfully answers to "kiste" makes
OPEN KISTE ask "which do you mean" about a phrase that already named its
object. The German round surfaced the annoyance; STEFAN'S DESIGN answers
it at the language level: a `words` entry may carry a leading # marker,
`words #kiste, gross, grosse`, and the marked word is ordinary vocabulary
AND the object's trigger, the word that says what the thing IS.

The semantics, ruled precisely: triggers are consulted only when a tie
stands, never before. Among the tied candidates, exactly one whose
trigger was typed wins silently; two or more typed triggers keep the
question (OEFFNE TRUHE TUER is a genuine one, Stefan's rule); zero typed
triggers change nothing. A tiebreaker, never a gag order. Declared intent
outranks the held heuristic, and the marker works in every slot the
matcher resolves, the second noun of PUT COIN IN CRATE included. It is
language-neutral: the machinery lives in the agnostic matcher, so all
three shipped languages speak it with no pack work.

Under the hood the marked words become a per-object vocab array beside
`words`, registered only on first use, so a game without the marker
allocates nothing, folds the matcher code away entirely, and stays
BYTE-IDENTICAL (the shipped examples prove it at their exact pinned
sizes). Verified on fizmo-console: the typed trigger wins over a held
rival, the honest asks all survive. Seven new tests
(tests/test_trigger.py), a worked example
(examples/features/trigger.storyarc, pinned 16944), the handbook's
chapters 3 and 14 carry the feature, syntax first.

## 2026-08-14: Tuere ist auch eine Tuer, and a rescue on the way

The small ruled item of the round: "Türe" is good German beside "Tür",
and a field report typed it. RULED: this is declaration work, not
morphology. Tuere is a spelling, Tische is a plural; no ending rule can
tell them apart, so the compiler will never guess (the crossword-umlaut
automation, a separate depth item, is about spellings of the SAME word,
which is mechanical). The example's Tür now declares tuere, türe,
eichentuere, and eichentüre beside its four existing forms, with the
reasoning as a comment in the file. Priced honestly: +24 bytes of
dictionary, dated.

The size check earned its keep on the way: the build came out SMALLER
after adding words, which is impossible, and measuring instead of
shrugging found the example file had lost its entire Truhe declaration
(six lines, gone from the working tree before the edit, most likely an
IDE buffer accident; the file had been open in an editor all session).
Restored from git, verified back at its exact expected size. Measured
truth, both directions: the deletion predated the session's edits, and
the recovery is byte-exact. One compiler finding fell out for a later
ruling: `thing schluessel in truhe` with no truhe declared compiles
SILENTLY today (the stranded object never errors); a candidate sema
diagnostic.

## 2026-08-14: a dangling `in` is a compile error now (arcc 1.6.1)

The Truhe rescue's open finding, ruled fixed the same day: an object
placed `in` a name that is not declared compiled silently and simply
stranded outside the world, the exact failure that would have caught the
editor accident the moment it happened. Exits learned this lesson from a
field report long ago, spans likewise; the plain location was the last
reference in the language that could dangle. Now it refuses at compile
time, naming the object and the missing location, the handbook says so
in chapter 3, and the legal shapes (a room, a container, the player,
`scope`, backstage-by-omission) all pass untouched. Two tests beside the
exit-validation family; full battery 1273 green.

## 2026-08-14: the fold table, crossword umlauts for free (arcc 1.7.0, Cosmos 1.10.0)

The depth item of the round: German is read with umlauts and typed, on an
8-bit keyboard, without them, and until today every typeable word had to
be declared twice, "oeffne" beside "öffne" through the whole granule and
every game's own words. STEFAN'S RULING: the pack owns its orthography. A
language layer now declares its fold table, one pair per line (fold "ä"
"ae", and ß to ss, Spass for Spaß), and every dictionary word containing
a source, the pack's verbs and directions and the game's words, plural
and trigger vocabulary, grain and topic words alike, gains its crossword
sibling automatically: same meaning, second spelling. One-way by design,
declared to derived, because not every "ue" is a "ü"; the reverse would
guess. English declares no folds and is untouched; Spanish stays
declaration-based on Stefan's line that año to ano is not a spelling.

The granule shed seventeen hand-doubled lines and the example its
doubled words, and the proof came out exact: the pruned-and-folded build
loses NOT ONE typeable spelling against the hand-doubled one and gains
three (möwe, südost, südwest, the proper forms of words that had only
crossword spellings). Collisions follow the ruling: a declared word
always wins; two things sharing a folded spelling become an honest
ambiguity the parser asks about, and a fold that would change a declared
word's role is skipped with a note, never silently. Verified end to end
on fizmo-console: the whole example plays ASCII-only. Seven new tests;
full battery 1280 green; the example holds its exact 23840 bytes.

## 2026-08-15: pronouns done right, a word can reach two slots (arcc 1.8.0, Cosmos 1.11.0)

The pronoun depth item, measured before designed: das Kind filed under
the es slot and "rede mit ihm" refused, or worse, reached a stale Mann
while the Kind was the freshest thing touched; and "ihnen", the dative
plural, was not a word at all. The flaw was structural: the model mapped
every pronoun word to exactly one slot, and German does not work that
way. "ihm" is the dative of masculine AND neuter, "sie" is feminine AND
plural, "ihnen" plural only.

STEFAN'S RULINGS, three: a multi-role word takes the most recently
mentioned live referent SILENTLY (pronouns are recency creatures, no
interrogation); pluribus things file under the them slot, "sie" spans
feminine and plural, "ihnen" is them-only; and recency is strict, so a
freshest referent that left scope refuses honestly rather than an older
one sliding in. The pack now declares `pronoun him, it "ihm"` and the
skeleton resolves the pair by mention stamps; the slot semantics live in
the language layer (the pronoun_pick seam), exactly where the parser
seam principle wants them.

Priced honestly: English and Spanish are byte-identical, PROVEN against
snapshots (three encoding attempts were rejected on that proof: shifted
global numbering twice, and a skeleton reference sema could see; the
seam block was the shape that passed). The plural granule's fold was
re-keyed to its summon on the way, since "ihnen" would have false-armed
the old marker. German pays 84 bytes, repriced dated. Seven new tests
(tests/test_pronoun_sets.py), all nine ruled behaviors probed on
fizmo-console, full battery 1287 green.

ALSO IN THIS COMMIT, Stefan's call of 2026-08-15: the German prose
comments this assistant had written into german.granule were Denglish
calques ("Die Erwaehnungsstempel"), ruled an abomination, and every
German comment in the granule is now idiomatic English (56 blocks
rewritten; German remains only inside quoted player input and message
examples). The lesson is on record: library commentary is English;
German prose appears only where a native pass gates it.

## 2026-08-15: the da-words, damit means what a German means (arcc 1.9.0, Cosmos 1.12.0)

The last built depth item of the round. German fuses preposition and
referent into one word, damit, darauf, darin, daran, and no parser word
existed for any of them: "schliess die truhe damit auf" answered that
the story does not know "damit". Now the pack declares them under the
`da` pronoun role, and a da-word anywhere in a two-noun command fills
the second slot with the freshest remembered THING, satisfies the
requirement ("leg das buch darauf" stops asking wohin), and reads
position-free, exactly like the German.

STEFAN'S RULINGS, three, plus one the first probe forced: the referent
is never a person (damit cannot mean the innkeeper, however fresh her
mention); the v1 word list is damit, darauf/drauf, darin/drin,
daran/dran, with darunter/drunter staying particles that pick
look_under and bind the same referent into an empty noun slot; an empty
referent speaks the honest pronoun refusal. The forced fourth: the
referent is never the object being acted on. The first probe put the
book on itself, because NIMM had just made the book the freshest
mention; "leg das buch darauf" now repicks past the noun and finds the
table it must mean.

The mechanism rides C wholesale: the mention stamps pick the freshest
across all four slots, and the da-word is spliced out of the parse
buffer after binding, so scoring, the split, and every fault range see
a clean command; no skeleton code changed at all. The chain showcase
works on the first try: "nimm den schluessel und schliess damit die
tuer auf", one line, key taken, door unlocked. Priced honestly:
German-only by construction, English and Spanish proven byte-identical;
the German example pays 604 bytes for the referent walk and the two
scans, repriced dated. Nine new tests (tests/test_dawords.py), verified
on fizmo-console, full battery 1296 green.

## 2026-08-15: the adjective marker, the parser learns parts of speech (arcc 1.10.0, Cosmos 1.13.0)

The last depth item of the round, and the one that outgrew it. The forum
asked for German adjective declension; the design talk found the bigger
thing behind it: the parser KNOWING what an adjective is, the concept
Inform 6 and Dialog never had and Infocom's ZIL always did. STEFAN'S
DESIGN, assembled across the discussion: his marker gives the strip its
scope, the strip keeps the dictionary flat, and the class knowledge
serves every language.

The declaration is one sigil: `words #chest, box, trunk, >wooden,
>heavy`. The > points forward, because a word comes after an adjective
(Stefan's sigil, Stefan's reasoning). Matching then scores in ZIL match
classes, RULED 100% Infocom: adjective plus noun above noun alone above
adjective alone, only the highest class survives. EXAMINE RED GUITAR
never asks about the red couch; a UNIQUE adjective still finds its
object (the sausage rule); and two red things in scope produce the
sentence the design started from: "Which do you mean, the red couch or
the red guitar?", asked by the existing machinery the moment the class
model fed it a clean candidate list.

German declension rides the marker: an unknown typed word sheds an
adjective ending (en/er/es/em, then a bare e) and is accepted ONLY when
the stem is a marked adjective, looked up through the interpreter's own
tokenizer. Declare `words truhe, >rot` once and rote, roten, roter,
rotes, rotem all type; the fold table composes, so gruenen reaches
>grün. Nouns never strip: the D ruling stands untouched, and unknown
words keep their honest report. A measurement en route killed a false
positive: an early probe "passed" only because the name-derived word
matched, and the debug print showed the strip had never fired; the real
defect was the tokenise intrinsic's stack operands pushed in the wrong
order.

Priced with the strictest proof of the round: all four shipped examples
BYTE-IDENTICAL with no marker anywhere (three encoding lessons paid on
the way: a let in a statically dead branch still allocates a local, and
hoisting one shifts the whole file). The showcase example
(examples/features/adjectives.storyarc, pinned 17528) carries Stefan's
exact declaration; eleven new tests; handbook chapters 3, 14, and 21;
full battery 1308 green, fizmo-console verified. One open decision
flagged, not built: probe_noun (the reversed-dative probe) still ranks
classlessly; extending the classes there is Stefan's call.

## 2026-08-15: the example rulings, and the adjective sweep

Three rulings closed the round's last open question and reshaped the
example roster. THE GASTHAUS STAYS AS IT IS: a minimal German intro,
never extended, because no extension would satisfy where a real game
will; the big German example becomes HIBERNATED 1 AUF DEUTSCH, ported
first and translated second, in its own gated workspace. THE GHOSTS OF
BLACKWOOD MANOR PORT IS RETIRED: it remains a product of its time. The
English example game becomes a port of Ryan Veeder's CRAVERLY HEIGHTS,
the Inform 7 classic already carried to PunyInform, Dialog, Inform 6,
and ZIL (permission at rcveeder.net/craverly/); a game every major
system has ported is the right common yardstick, and the Puny port's
back-ported Inform 7 behaviors are a reading list of Cosmos improvement
candidates.

And the quality sweep: with the word classes in the language, the
shipped examples now speak them. One hundred and three words across
thirty-nine files gained their > adjective marks, brass and oak and
rusty and roble and eiche, so every example demonstrates the classes a
player will feel. No content changed anywhere, and the full battery
passed UNTOUCHED on the first run after the sweep: one hundred and
three marking decisions, zero behavior regressions, the ceilings
repriced for the armed machinery in one dated stroke.

## 2026-08-15: the forum reply is posted, the round is delivered

The reply went to the German IF forum today, in Stefan's voice after
his native pass: every finding answered in the thread's order, the five
features the discussion produced, one `arcc --update` to get it all,
and an open invitation to report more. Drafting had its own lesson,
now on record: composing English first and translating produces exactly
the calqued German the round existed to keep out of the language;
the good draft was written in German from the facts. With the post,
the German forum round closes: eight landed items, five compiler
versions, two example-roster rulings, and a parser that knows parts of
speech. The reports were right, and answering them properly made the
language better for every author, in every language it speaks.

## 2026-08-15: Arcturus comes to Zed

Stefan moved his daily editing to the Zed editor, and Zed speaks only
Tree-sitter, so the official Arcturus highlighter for it starts a level
deeper than a grammar file: editors/tree-sitter-arcturus/ is a real
Tree-sitter grammar for the language, and editors/zed/ the extension
that wears it (display name Arcturus, Stefan's description line, the
zed-arcturus / tree-sitter-arcturus naming split ruled for the eventual
public repositories, the grammar keeping the ecosystem convention so
other editors can adopt it later).

The grammar is deliberately loose, built for highlighting rather than
parsing: declaration heads are structural so names colour and OUTLINE
(rooms, things, kinds, blocks, and topics appear in Zed's breadcrumbs
and symbol search, a step past what VS Code offers), everything else is
an identifier, and the keyword, attribute, property, and builtin sets
live in highlights.scm queries, one line per future word. The proof of
the shape: ZERO parse errors across the entire corpus, every example,
every granule, every prelude, and the queries validated against the
grammar with real captures. All three file types are covered
(.storyarc, .granule, .prelude), and the word-class markers highlight
distinctly. Zed wants its grammar as a git repository even locally, so
tools/zed_dev.py assembles an untracked installable bundle under
build/zed-dev; Stefan's eye gates the install. Next in this lane, on
his word: an Inform 6 extension for Zed, since the porting work reads
Inform sources daily.

## 2026-08-15: the publishing split, development stays home

Stefan's ruling on the Zed extension's road to the official registry:
development remains in this repository (editors/zed and
editors/tree-sitter-arcturus are the truth), and two sibling
repositories on disk are pure publishing artifacts, refreshed by
tools/zed_publish.py: ../Misc/tree-sitter-arcturus (the grammar Zed
clones by commit) and ../Misc/zed-arcturus (the extension the registry
submodules).
The tool wipes and re-exports both, writes their public READMEs, ships
the MIT LICENSE into each (the registry demands one at the extension
path; a BSD line that had slipped into the grammar metadata was
corrected to the project's MIT), and stamps the extension's grammar
reference with the grammar repo's HEAD, so the pin can never drift from
what is actually published. Both repos stand committed locally;
creating them on GitHub, pushing, and the registry pull request
(fork zed-industries/extensions, submodule, extensions.toml entry) are
Stefan's own acts, documented in editors/zed/README.md.

## CHECKPOINT: the German forum round (updated per item; compaction-proof)

THE PICKUP. This checkpoint is the single source for resuming the
round after a compaction. Read it whole, mirror the NEXT list into the
session todo, and continue top-down. RULES OF THE ROUND: one item at a
time; Stefan's word gates each design and his eye gates behavior;
every landed item gets (1) its own dated PROGRESS entry above, in the
house voice, rulings prominent, and (2) an update to THIS checkpoint
(move the item to DONE with its commit hash, refresh NEXT). The forum
reply is drafted together and posted only when every item verifies.
The thread's temperature and all personal context are deliberately
UNRECORDED anywhere in the repository; Stefan handles the personal
side himself, then posts the professional part and challenges the
thread to contribute rather than hunt. Never name the reporter in any
tracked file for this round.

HOW THE LOG WORKS (the documentation convention of this round): each
landed item's PROGRESS entry states the field finding neutrally ("a
field report noticed..."), the ruling with Stefan's reasoning, the
mechanism built, the price measured (byte-identical or repriced,
dated), and the test count. The checkpoint below carries the WORKING
knowledge (file anchors, designs, measured facts) that the narrative
entries deliberately leave out.

DONE:
- I (RESOLVED BY RULING) + THE EXAMPLE ROSTER: Gasthaus stays minimal
  (never extend); the big German example = HIBERNATED 1 AUF DEUTSCH
  (examples/hibernated1_german/, gitignored, PORTLOG.md inside, parked
  on Stefan's word); Ghosts port RETIRED and deleted; the English
  example game = CRAVERLY HEIGHTS (Ryan Veeder, permission
  rcveeder.net/craverly/; Puny source in examples/craverly/,
  gitignored, PORTLOG.md inside; the Puny port's I7 backports are
  Cosmos improvement candidates to read). THE ADJECTIVE SWEEP: 103
  >marks across 39 example files (no triggers needed beyond the
  showcase; no content changes); suite passed untouched; all ceilings
  repriced dated (incl. CLOAK_Z8_CEILING 20224).
- DEPTH H: THE ADJECTIVE MARKER + ZIL CLASSES (arcc 1.10.0, Cosmos
  1.13.0). `>word` in words lists (parser words branch beside #;
  PropertyDecl.adjectives; sema synthesizes `adjective` vocab prop,
  registered on use, uses_adjectives; objects.py emits with
  fold_words; lower: adjective_addr/count + any_adjectives + the
  tokenise_at intrinsic, STACK OPERANDS PUSHED REVERSED, args[1]
  first, the house pattern). Skeleton: phrase_class/has_adjective
  before phrase_score; match_phrase folds the class INTO the score
  (class * 64 + count, commands never reach 64 words) so ask_score
  carries the composite and NO new locals or globals exist; the
  full-match checks and the three ask re-scans (list_which x2,
  which_tiebreak, trigger_break) are DUAL-BRANCHED on any_adjectives
  is 0 / is 1 with identical bodies, byte-identity proven for all
  four examples. LESSONS BANKED: a `let` in a statically dead branch
  still allocates a local slot (use the same name in both branches);
  hoisting a let shifts every downstream address; an or-chain of four
  comparisons is fine (was not the bug). German strip: strip_endings/
  try_strip in german.granule behind any_adjectives (suffix chars
  checked via text_char ZSCII, e=101 n=110 r=114 s=115 m=109; scratch
  text at ask_addr + one-entry parse at ask_addr+20, idle during
  parsing; per-object has_adjective walk gates acceptance; parse
  entry patched via poke_word(parse_addr, 1+2*i, stem)). RULED: 100%
  ZIL (unique adjective binds, shared asks, noun outranks); sigil >
  (points forward); the ask sentence verified verbatim. Example
  features/adjectives.storyarc (pinned 17528; Stefan's declaration
  verbatim); tests/test_adjectives.py (11). OPEN, flagged not built:
  probe_noun stays classless (reversed-dative probe); name-derived
  words are noun-class (documented ch 14).
- DEPTH G: THE DA-WORDS (arcc 1.9.0, Cosmos 1.12.0). `pronoun da
  "damit", "darauf", "drauf", "darin", "drin", "daran", "dran"` (role
  7, prelude._PRONOUN_ROLES; no new syntax, no skeleton change).
  german.granule: da_referent(excl) walks the four C slots by stamp,
  skipping animate AND excl; bind_daword scans flag-4/role-7, binds
  second, SPLICES the word from the parse buffer (header 2 bytes + 4
  per word; copy_bytes forward-down + count byte) so downstream sees a
  clean command; called in resolve_objects' arity-2 branch before
  resolve_two_nouns, whose pre-bound-second early path resolves the
  rest as ONE noun (repicking via da_referent(noun) when the noun IS
  the referent) and only asks for a missing FIRST noun.
  darunter/drunter: find_under_particle (flag 32 role 5) + compound
  (base,5)==look_under gate in the empty-noun ladder, so "nimm
  darunter" keeps its refusal. Rulings: never animate, never the
  acted-on object, empty referent = fault 5. Tests
  tests/test_dawords.py (9, incl. the chain showcase); beispiel
  repriced 24532 (+604); EN/ES byte-identical proven. Handbook ch 21.
- DEPTH C: PRONOUN SLOT SETS (arcc 1.8.0, Cosmos 1.11.0). Declaration:
  `pronoun him, it "ihm"` (parser roles list; sema maps via
  prelude._PRONOUN_ROLE_SETS {him+it:5, her+them:6} into
  world.pronoun_sets, uses_pronoun_sets; single-role ids untouched so
  existing packs keep bytes). dictionary._pronoun_words merges both.
  any_plurals RE-KEYED to has_summon(world,"plurals") (old marker was
  them-role-pronoun-exists; German ihnen would false-arm it).
  any_pronoun_sets intrinsic folds the skeleton hook: pronoun_slot
  role>=5 calls pronoun_pick(role), a PACK block (english stub returns
  nothing, folded; german implements with fresher() + stamp globals
  pron_seq/pron_at_* declared IN THE GRANULE). Lessons banked: stamps
  as std-globals shift numbering (twice), skeleton refs to pack
  globals fail sema even when folded; the seam block is the shape.
  note_pronouns stamps + files pluribus->them first. German words:
  es/ihn/ihm(5)/ihr/sie(6)/ihnen(4). Tests test_pronoun_sets.py (7);
  beispiel repriced 23928. Handbook ch 21. EN ROUTE: all German prose
  comments in german.granule rewritten to English (Stefan's ruling:
  Denglish, wipe it); example beispiel-deutsch comments NOT touched,
  flagged for Stefan (my recent German blocks there may need the same
  treatment or his native pass).
- DEPTH F: THE FOLD TABLE (arcc 1.7.0, Cosmos 1.10.0). `fold "ä" "ae"`
  pairs declared in the language pack (german.granule ~line 50, four
  folds incl. ß->ss); parse_fold beside parse_noise; world.folds;
  dictionary.build registers folded siblings with copied data bytes
  (verbs/directions/particles/grains work by data), and fold_words
  (objects.py) expands every ADDRESS-compared array: object words,
  plural, trigger, topic word sub-arrays (matching is by dictionary
  address, so data-copy alone was not enough, the first probe proved
  it). Collision policy ruled: declared wins; same-data sibling silent
  (hand-doubles stay quiet), shared thing-spelling becomes a parser
  ambiguity, role-changing fold skipped with an arcc note. Granule
  pruned 17 lines, example pruned (words + grains + comments);
  word-set proof: nothing lost, three gained (möwe/südost/südwest).
  Handbook ch 21 rewritten (fold table + the Spanish contrast).
  Tests: tests/test_fold.py (7). Sizes: beispiel exactly 23840 still.
- D: TUERE VARIANTS (example-only, no version bump). The Tür declares
  tuere/türe/eichentuere/eichentüre beside its four forms
  (examples/beispiel-deutsch.storyarc ~line 190, reasoning in a file
  comment); repriced 23816 -> 23840 (+24 dictionary). RULED: spelling
  variants are declaration work, never morphology (Tuere spelling vs
  Tische plural). NOTE the encoding truth: türe/eichentuere/eichentüre
  collapse onto existing z5 entries (ü costs 4 z-chars, entries
  truncate at 6/9), only tuere is a new distinct entry; all four typed
  forms resolve regardless. EN ROUTE: the working file had LOST its
  whole Truhe block before the edit (IDE buffer accident, predates the
  session's edits, proven by line offsets); restored from HEAD,
  caught because the size DROPPED when it should grow. The silent-strand
  finding was ruled and FIXED same day (arcc 1.6.1, _check_locations
  beside _check_exits): a dangling `in` errors at compile time.
- A2: THE #TRIGGER MARKER (arcc 1.6.0, Cosmos 1.9.0). Syntax: `words
  #truhe, eiche` (parser.py words branch collects triggers; # is a
  lexer op, tokens.py; plural lists reject it). Sema _collect_members
  synthesizes a `trigger` vocab property from PropertyDecl.triggers,
  registered via _unify_property ONLY on use (never seeded in the
  prelude std table: std props are numbered in every game and would
  shift all layouts); world.uses_triggers is the fold truth (an
  adopter's unrelated property named trigger must not arm it).
  objects.py emits it like plural/words; lower.py: trigger_addr/
  trigger_count (0 when absent, plural_addr shape) + any_triggers
  (dynamic + _static_value). Cosmos: trigger_typed/trigger_break in
  parser.prelude before ask_which; tie path consults them AFTER
  plural_tie, BEFORE which_tiebreak, gated on any_triggers. The
  unread-prop lint skips "trigger" (read via intrinsic, not property).
  Tests: tests/test_trigger.py (7: syn-tie win, beats-held, second
  slot, two-triggers-ask, zero-triggers-ask, German, plural-#-error).
  Example: examples/features/trigger.storyarc (pinned 16944).
  Handbook: ch 3 words + ch 14 (tie ladder bullet updated: trigger
  then held; dedicated syntax-first passage + worked-example link).
  EN ROUTE: found and fixed (separate commit, arcc 1.5.2) the
  hash-seed build nondeterminism: _gen_react's catch-all iterated
  frozenset event_names raw; sorted now, examples hash-stable under
  any PYTHONHASHSEED. Byte-identity claims from before that fix were
  luck-prone across processes; in-process comparisons stand.
- A1: THE ONE-NOUN RETRY (arcc 1.5.1, Cosmos 1.8.1). german.granule
  gained one_noun_retry(n) right after is_separator: saves and
  restores parse_fault, ask_lo/ask_hi/ask_score/ask_at, and
  unknown_at, retries match_phrase(1, n, 0), and wins only on a
  clean non-nothing resolve (noun bound, second cleared). Three call
  sites inside resolve_two_nouns, all gated on rq2 is 0: first slot
  fault 3 with b < n; second slot fault 3; second slot nothing with
  b + 1 < n (tried BEFORE noun_fault, and before find_scenery on the
  first-slot-empty path). Fault 4/5 never retries (unknown words and
  dangling pronouns fail the whole range too). Tests:
  tests/test_split_fallback.py, 4 tests, rescue cases red pre-fix;
  fizmo-console verified all four behaviors. German example repriced
  23664 -> 23816 (+152, German-only; banner shows major.minor so
  English/Spanish stay byte-identical). Handbook: chapter 21's
  particle-boundary paragraph documents the retry as German-pack
  behavior. VERIFIED FINDING for a later ruling: Spanish AND English
  resolvers share the exact separator shape (flags 8/136/64/32, not
  flag-8-only), so the seam exists there too; generalizing the retry
  is Stefan's call, priced per pack. Also: no WHATSNEW entry per
  round item (B set the precedent); propose one collected entry when
  the round closes.
- B: THE BINARY MODEL (commit 948637c; arcc 1.5.0, Cosmos 1.8.0).
  `binary`/`active`/`glow`, switchable alias, contract refusals,
  default flips with pack reports x3, glow light coupling, examples
  reworked, tests/test_binary.py (6 tests), handbook rewritten,
  non-binary games byte-identical. Key code anchors: alias
  normalization = sema.py _normalize_aliases (a whole-program AST
  pre-pass, first thing analyze() does); glow derived in sema after
  _collect_members (binary+lit -> glow); the contract =
  check_switch in loop.prelude beside check_requires, called from
  the main contract site AND sweep_one, both behind `if any_binary
  is 1`; the state read: glow things test `lit`, plain binaries
  test `active` (author flavor handlers historically flip lit);
  defaults in actions.prelude fold behind any_binary so foldless
  games keep the classic refusal byte-exactly; any_binary intrinsic
  in lower.py (dynamic + _static_value entry, mirrors any_beyond);
  the darkness detector (sema uses_darkness) skips library-origin
  decls for the lit-clear scan (origin tags exist on
  BlockDecl/Handler/DirectionDecl: "library"/"granule"/"game") or
  every game arms the light watch. Doctrine: a flavor handler owns
  its flip (now self is active, plus lit on glow things); documented
  in the handbook's attribute table and both lamp examples.

NEXT (in order, with the agreed resolutions and pickup data):
- LATER: HIBERNATED 1 AUF DEUTSCH (the big German example; port then
  translation, Stefan's native pass gates; workspace ready) and the
  CRAVERLY HEIGHTS PORT (the English example game; workspace ready;
  read the Puny port for I7-behavior backports as Cosmos candidates).
  Both parked on Stefan's word; the forum reply comes first.
- FINAL (DONE 2026-08-15): the reply is POSTED. The round is closed;
  WHATSNEW carries the collected entry. What remains beyond the round:
  the Craverly Heights port (English example game) and Hibernated 1
  auf Deutsch (both workspaces ready, parked on Stefan's word), then
  B12 R5 (Apple II/DHGR, Next, MEGA65, C128).

MEASURED FACTS the round rests on (do not re-derive): "untersuche
tuer aus eiche" resolves 2:1 today (one-noun path healthy); the ask
comes ONLY from the two-noun particle split; "gehe nord" AND "gehe
norden" both already work (E closed); "tuere" is unknown until
declared; the double-off bug was real in both examples since release
and B killed it; phrase_score compares dictionary entries not flags,
so known-but-foreign words in a noun range are harmless; one
dictionary flag per word (noise would clobber particle - the reason
German "aus" could never be noise and takeall's German group needs no
filler).

SESSION STATE BEYOND THE ROUND: versions arcc 1.10.0 / Cosmos 1.13.0 /
arcimg 1.35.0 / Actaea 1.3.9 / proteus 1.0.0, all standalones
committed and README current; suite 1308 green
(tests/actaea excluded from batch runs: curses needs a TTY). B12
arc_image stands at R2-R4 complete plus Shawn's Agon (fifteen
formats, twelve probe-proven); R5 (Apple II/DHGR, Next, MEGA65, C128
ruling) waits until this adopter round closes. The emulator bench
and its rules live in the memory files, not here.

## CHECKPOINT for pickup (2026-08-16, compaction): the Zed lane shipped, three lanes parked

THE PICKUP. Versions: arcc 1.10.0 / Cosmos 1.13.0 / arcimg 1.35.0 /
Actaea 1.3.9 / proteus 1.0.0; VS Code extension 1.2.1 (one vsix ships);
Zed extension 1.0.0. Suite 1313 green (pytest from a real terminal;
tests/actaea needs a TTY, keep it out of batch runs). Tree clean,
everything pushed.

CLOSED SINCE THE LAST CHECKPOINT: the German forum round is DELIVERED
(reply posted 2026-08-15; the round's eight items B, A1, A2, D,
F, C, G, H plus the example rulings all landed and are recorded above;
WHATSNEW carries the one collected entry; the Discord announcement was
handed over). The adjective sweep marked 103 words in 39 examples with
zero behavior regressions. The example roster RULED: Gasthaus stays the
minimal German intro, Ghosts of Blackwood Manor is retired (its dir
deleted), Craverly Heights becomes the English example game port
(examples/craverly, gitignored, Puny source + PORTLOG.md inside,
permission rcveeder.net/craverly/), Hibernated 1 auf Deutsch the big
German one (examples/hibernated1_german, gitignored, PORTLOG.md).

THE ZED LANE (this checkpoint's main news, all shipped):
- editors/tree-sitter-arcturus: the Tree-sitter grammar (loose,
  highlight-first; declaration heads structural, word sets in queries;
  ZERO parse errors across the whole corpus, examples + cosmos).
  Regenerate after grammar.js edits: cd editors/tree-sitter-arcturus &&
  npx tree-sitter-cli@latest generate (commit src/ too).
- editors/zed: the extension (id arcturus, display "Arcturus", all
  three suffixes storyarc/granule/prelude; highlights + brackets +
  outline). QUERY ORDER LAW: later pattern wins in Zed; calls first,
  then generic sets, then structural captures, strings last (the
  ordering comment in highlights.scm is normative).
- tools/zed_dev.py: assembles the installable dev bundle under
  build/zed-dev (grammar as throwaway git repo, file:// + sha; Zed
  needs git even locally). Stefan: "zed: install dev extension" /
  rebuild after re-running the tool.
- tools/zed_publish.py: exports the publishing artifacts to
  ../Misc/tree-sitter-arcturus and ../Misc/zed-arcturus (Stefan's
  layout: publishing repos live under Fiction/Misc, never in Fiction
  directly). The tool owns their READMEs and LICENSE (MIT, matching
  the project; a stray BSD line was corrected). It stamps the
  extension's grammar rev from the grammar repo's HEAD. Push order:
  GRAMMAR FIRST, then extension.
- PUBLIC STATE: both Misc repos pushed to GitHub (ByteProject).
  tree-sitter-arcturus main = 7170081 (the rev the extension pins),
  zed-arcturus main = 89af9a3. The registry PR is OUT: fork
  ByteProject/extensions (shallow clone at ~/Fiction/Misc/extensions,
  branch add-arcturus), submodule extensions/arcturus + [arcturus]
  entry in extensions.toml (version 1.0.0), sorted with the repo's own
  sorter (node src/sort-extensions.js after npx pnpm install; the
  sorter placed arcturus AFTER arctikai-theme, hand-sorting would have
  missed it). Bot checks PASSED; awaiting human merge.
- UPDATE FLOW for later releases (documented in editors/zed/README.md):
  develop in editors/*, zed_publish.py, commit+push Misc repos
  (grammar first), bump version in extension.toml, then in the fork:
  git submodule update --remote extensions/arcturus, bump
  extensions.toml version, push branch, fresh PR.
- tests/test_editors.py: the parity suite (5 tests) holds the VS Code
  tmLanguage and the Zed queries together mechanically; deliberate
  deviations are listed IN the test with reasons (turns stays builtin,
  clear/capacity resolve as VS Code include order did). The UUID
  lesson: never claim extension parity from memory, the test or a
  file-against-file audit is the proof.

NOT OURS: the "Inform 6 x PunyInform" Zed extension is Stefan's own
project with an Opus instance (his ruling: not part of Arcturus). He
has the ignition prompt (chat, 2026-08-16); foundation copies of the
two Zed dirs were made by him. Do not develop it here; the grammar
convention (tree-sitter-inform6 for the language, extension carries
the pairing name) was advised.

NEXT (the actual todo, in rough order, each on Stefan's word):
1. ZED PR AFTERMATH: when the registry merges, Stefan verifies the
   in-app listing, uninstalls the dev extension; the fork clone at
   ~/Fiction/Misc/extensions stays for future update PRs.
2. CRAVERLY HEIGHTS PORT (the English example game): workspace ready,
   read the Puny port first and note the Inform-7-behavior backports
   as Cosmos improvement candidates (Stefan: "if it serves Inform 7
   well, it might also serve us"). PORTLOG.md discipline like H2.
3. HIBERNATED 1 AUF DEUTSCH: port first (H2 discipline), translation
   second, Stefan's native pass gates line by line. German prose only
   through his pass; code comments English, always.
4. B12 R5 (arc_image): Apple II/DHGR, Spectrum Next, MEGA65, and the
   C128 ruling; then R6. This was the lane paused for the Zed work.
5. SMALL OPEN THREADS: probe_noun stays classless (H's flagged
   decision, Stefan's call if wanted); the Actaea Beyond Zork gap
   stands (do not start unprompted); the roadmap items live in
   WHATSNEW.

STANDING DISCIPLINE (unchanged, the memory files hold the full set):
one item at a time; Stefan's word gates designs, his eye gates
behavior; answers before conditioned work, in the final message;
deviations inside approved designs are proposals surfaced BEFORE
landing; measure, never assume; byte-identity proofs for language work
(snapshot before, compare after, deterministic builds make it real);
per-item PROGRESS entry + checkpoint update in the landing commit.

ADOPTER REPORTS ROUND (2026-08-16): EdwardianDuck brought two. (1) Block
override granule-vs-granule: expected behavior (granules are peers, no
load-order winner, duplicate is the honest report; the chapter-file rank
is the supported route for a house-overrides file). Answered on Discord.
(2) Spanned-object appearance shows only in the home room: triaging the
report surfaced TWO real findings. First, THE -L PRELUDE BUG, fixed in
this commit: chapter 23 promises "extract the library, edit, point -L at
it" and --extract-library prints the same, but combined_program never
consulted -L for preludes (only granule summons did), so a forked
prelude was silently ignored, in every release since B5. Stefan's
ruling: "it's a bug so this needs to be fixed." The loader now shadows
each bundled prelude with a same-named file from the first -L directory
holding one, with the existing fork note riding along; two tests pin the
promise both ways (edited msg_taken speaks with -L, bundled without).
The silence is what let the adopter believe his prelude edit had worked;
his actual report is the spans design issue, ruled and landing
separately (next entry).

THE TWO MULTI-ROOM FORMS: EXISTENCE AND SIGHT (2026-08-17, Stefan's
design, recovered). EdwardianDuck's spans report (a vine `in location1,
location2` whose appearance showed in one room only) opened a design
review, and Stefan's verdict rewrote the feature: the July 1 spans
implementation had flattened TWO different designs into one, and the
handbook's ambiguous passage ("puts the object in hall and spans it into
vault" beside "referable from every room it spans") is exactly why the
adopter had both syntaxes in his code and neither meaning. The record
shows no ruling ever authorized the flattening; it was an earlier
instance's choice, canonized by documentation after the fact.

The recovered design, as ruled: `in room1, room2` is the EXISTENCE form.
One object, whole, in every listed room, "like Agent Smith in the
Matrix": same paragraphs, same listing sentence, contents along
(subtree-follows ruled), one state (a door open on both sides). Fixed
objects only; scenery is redirected to `spans`; a movable or a kind
target is a compile ERROR, never the old silent drop (Stefan: loud, the
silence was the failure mode). The containment test stays tree-truth by
ruling: `if vine in gully` is false, the author declared the rooms and
tests `here` directly; Stefan asked for the byte price of the
alternative first (measured: ~150-260 bytes per game, every in/holds
site swapping jin for a helper call) and ruled it not worth it, since
no realistic author test needs it. Body `spans a, b` stays the SIGHT
form: scenery referable from every spanned room, never presented, kinds
allowed. One object takes one form, never both.

Landed in one pass, arcc 1.11.0 / Cosmos 1.14.0: parser splits
presence from spans (ObjectDecl.presence); sema validates and gates
loudly (_check_presence, after the properties pass so kind-default
fixed is visible: the door kind passes untouched) and synthesizes a
1-byte `presence` marker ONLY when both forms live in one game, so
property numbering never shifts for anyone else; the shared spans
array carries both forms' rooms (scope machinery untouched, one hot
read); is_presence folds to a constant unless both forms are live;
the describer gains presence_next/presence_describe/list_presence_one
in loop.prelude plus a list_presence_tail per language layer, all
behind any_presence (the fold whitelist in _static_value was the
catch: an unlisted any_X compiles as a RUNTIME test and nothing
folds; both new flags are listed). The reserved-name trap struck
again: `after` as a parameter name (the timing keyword); renamed prev.

Proofs: 34 of 38 examples byte-identical to shipped 1.10.0 (the
serial-date decoy en route: a midnight boundary made all 38 "differ"
until the baseline was rebuilt same-day); the four that differ are the
four that must (two existence doors now present on both sides, the two
language examples also paying the 1-byte marker); the spans showcase
byte-identical is the sight-form fold proof. tests/test_presence.py
(13: the vine verbatim, plain listing both sides, subtree+state, sight
never presented, both-forms discrimination, door shut from the far
side, tree-truth containment, all four error gates, the German
accusative tail). Ceilings repriced: door games pay ~264 bytes for
the presence walk; pathfinding's door migrated from its stray
body-spans shape to the comma form. Handbook: the chapter 3 passage
rewritten as the two features (the stale "02 chapter 12" ref died with
it), the door kind passage speaks existence, chapter 7 now actually
documents both forms in scope (the old text pointed at it for spans
and it said nothing). Suite 1328. The -L prelude fix landed separately
the day before (4f6aca1). Both amalgams regenerated; README table and
WHATSNEW updated (pathfinding entry rotated out).

## 2026-08-17: B12 R5 OPENS. The Spectrum Next lands (arcimg 1.36.0)

The round's rulings, all Stefan's: the C128 VDC is PARKED as an
arc_image target (the VDC's graphics limits make it undesirable; his
future C128 interpreter pairs the machine's extended memory with
VIC-IIe graphics, so the C64 asset serves the C128, and 80-column
love is an interpreter question); the Apple II is DHGR-ONLY for the
128K machines (a 48K HGR machine cannot host z5 plus a band; his
reference, deater's DHGR Monkey Island page); the Next verifies on
ZEsarUX, not CSpect (CSpect wants mono and he refuses the bloat; his
old hidden-bugs caveat about ZEsarUX stands, the probe discipline is
the guard); and Canopus's Agon dither-depth request JOINS the round
as its own one-fix item. Emulator logistics: Xemu/MEGA65 installed
and working (his ROM 920422; the setup lessons live in memory and
burned an afternoon: the supported ROM route is Xemu's own UI, and
the SD image is never host-mounted).

NXT, complete per the per-machine discipline: the converter is the
quantize recipe verbatim and turns out to be the IDENTITY for
Stefan's masters: zero differing pixels across all 22, both modes,
because ST-class art sits exactly on the Next's 3-bit guns. The
Rabenstein corpus landed (22 pictures, 126K packed under LZSA2), the
identity is frozen as a test beside four goldens, and the probe is
the friendliest loader of the Z80 family: Layer 2's 320-mode memory
is column-major, the .arc stream order, so a column is one LDIR; the
hardware clip frames the band; the ULA is simply switched off. The
probe pre-proves headless on HAUMEA'S simz80 (Stefan's pointer: use
the capable sim, not a bespoke one) under a TBBlue port model that
checks layer bytes, palette, and register discipline against the
pair files, then ships as a standard .nex (mk_nex.py, banks 0/1/3,
core 3.0 gate). Verified pixel-perfect on ZEsarUX 13.0, his eye.

ONE SCAR, RECORDED IN FULL: the probe pair convention is IMAGE 8 IN
BOTH MODES, files and header ids named for the MODES (9 and 12), one
byte patched. I built the first pair from corpus images 9 and 12,
matching the filenames, and when Stefan said "we used image 8 for
everything" I read the header ids back at him as proof he
misremembered. His screenshots forced the measurement: the pair
files' pixels are image 8, and C.12's ASSETS paragraph even says
"picture 8 of the corpus" in plain words. The convention lives in
the ART, not the labels; measure the content before contradicting
the person who was there. Also en route: the -L prelude fix earlier
in the round, and master 21's missing conversions closed for
ms1/ms2/agn (trsm4 already had it). docs/08 C.13 written
probe-after-probe; design.md ledger and docs/07's what-plays-where
brought current (Haumea PLAYS TODAY had never been recorded there).
NEXT: MEGA65, then Apple II DHGR, then the Agon dither probe.

## 2026-08-17: R5 continues. The MEGA65 lands (arcimg 1.37.0)

The conversion is the family's purest: the VIC-IV has 8-bit guns, so
the quantize recipe with an identity snap IS the converter, and any
master of 255 colors or fewer passes through exactly (0 differing
pixels corpus-wide, frozen as a stronger law than the Next's: no
grid required). Palette index 255 stays out of pixels by format
(the hardware's alpha path) and becomes the loader's own black.

The probe earned its chapter the hard way: five VIC-IV lessons now
in docs/08 C.14, each found by measuring the metal after the sim
said everything was right (the harness pre-proof, a strict 6502 core
under a VIC-IV model, was green from early on; every remaining bug
was a difference between my model and the machine). The knock, then
legacy-before-precise under HOTREG; char numbers ABSOLUTE in
full-colour mode (charset_base/64, CHARPTR plays no part; the first
build showed zero page as art); CHRCOUNT never inherited (the ROM's
80-column boot interleaved every other row); colour RAM reached by
ONE DMAgic fill of $FF80000 (the $D800 window left the boot
screen's stale attributes exactly under the old banner text, the
"two problematic rows" Stefan called out; the fill is the probe's
single non-6510 touch, a ruled exception); blank-first-reveal-whole
(DEN off with boot-black borders before any setup, reveal only when
everything stands: the boot flash died) plus the all-black char
padding every matrix cell past the band (the partial 13th row the
200-line window exposes showed stale entries below the band).
Stefan drove the diagnosis rounds on Xemu; the decisive move was
his normal-quit with -dumpmem armed, which proved charset and
matrix byte-perfect in the machine and pinned every remaining fault
on the display's inputs. Debug lesson kept: when the sim is green
and the screen is wrong, dump the machine and diff, never squint.
Verdict on the final build: "pixel perfect, no artifacts, no
flashing." Probe pre-proof green both modes; suite 183 on the
arcimg side; docs/07 and the design ledger current. NEXT: the Apple
II DHGR converter (the signal class, the round's real test), then
the Agon dither probe.

## 2026-08-17: R5, the Apple II in flight (checkpoint at 98% budget)

Status written mid-machine because the week's budget may force a model
handover before the wave closes; this entry is the pickup state.

STANDING: NXT done (2bf8859), M65 done (840e05f). AP2 = the signal
class. Stefan's ruling on the recipe fork: OPTION B FIRST, the full
NTSC signal model (the ii-pix manner), option A (aligned Polizei-flat
140x16) stays the documented fallback if B's texture fails his eye.

BUILT AND COMMITTED HERE: (1) _convert_ap2, a per-scanline dynamic
program over all 560 dot positions; the NTSC decoder shows at every
dot the colour of the last four dots through the phase table
(_AP2_IDX; the aligned nibble is LSB-leftmost at phase 3), so the DP
picks bits minimising plain-RGB distance to the master column under
them, reaching colours between the sixteen through sequences. The
280-column window is left-weighted (8 off the left, the MSX1
principle). Palette FROZEN: ii-pix's OpenEmulator sRGB sixteen
(_AP2_PAL), ending R1's approximate note. ~2s per picture. (2) The
AP2 format class REDEFINED from the R1 HGR shape to DHGR (the R5
DHGR-only ruling): two sections, aux page then main page (types 1
and 2), 40 bytes per row per page in display row order; render IS
the same window model, with rows DOUBLED so the preview keeps the
master's proportions (AP2-only; Stefan asked for undistorted
previews to judge by; TRSM4/AGN previews stay as approved). The
unwaved-target test now points at the parked VDC, the last
converter-less tag. arcformat/arcconvert suites green (163).

THE GATE IS DELIBERATELY INVERTED FOR THIS CLASS and still OPEN:
corpus previews (/tmp, not committed) read soft in places; the
softness is part physics (chroma cannot change faster than the
four-dot window slides), part optimiser taste (plain RGB distance
rewards blending at every edge; tunable via luma-weighted cost or a
flat-run preference, BEACH ONLY per the iteration rule). Stefan's
key question, answered honestly: the preview is faithful to the
COMPOSITE experience (the palette is measured from OpenEmulator;
real analog reads slightly softer, never sharper) and OPTIMISTIC for
RGB-path displays, which decode aligned nibbles and render the DP's
sequences as different hard colours. THEREFORE: probe first, his eye
on AppleWin in a composite video mode against these previews, THEN
the corpus verdict and any tuning. No corpus, no goldens, no docs/08
chapter yet.

PROBE PLAN (next act, possibly the fresh week's first): plain-6502
loader; the DHGR softswitch dance (80STORE, PAGE2 for the aux/main
$2000 window, GR+HIRES+AN3-off+80COL); codec ZX0 (the 8-bit default;
the 6502 decoders sit in probes/c64/); pairs = IMAGE 8 both modes,
ids stamped 9/12, the standing convention; boot via a DOS-less
boot-sector chain loader on a .dsk written by a pure-Python builder
(FictionTools has no Apple II builder on the R0 list; check, then
write mk_a2probe.py in the BuildTools doctrine); headless pre-proof in
the M65 harness manner (the strict 6502 core plus a softswitch
model); the emulator is AppleWin under wine (~/Fiction/Tools, wine
on PATH), and the video mode MUST be composite for the verdict.

AP2 ADDENDUM, same day: the probe body and its pre-proof are GREEN
both modes (probe.asm: plain 6502, the DHGR softswitch dance, staged
ZX0 decode via the vendored bitfire dzx0_6502, line-table scatter
computed by the assembler; run_probe.py: the strict core under a
main/aux softswitch model; aux and main pages byte-exact, below-band
black, switch end-state asserted). REMAINING for the AppleWin
verdict: the boot disk. Plan: vendor a public-domain minimal
bootloader of the qkumba lineage (the ROM's own $C65C re-entry only
reads within track 0; the probe spans ~2.2 tracks, so the loader
needs arm stepping, which qboot-class loaders solve in one sector) or
write the equivalent with the reference open; mk_a2probe.py then lays
probe.bin behind it in PHYSICAL sector order through the DOS 3.3
logical skew ([0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]), pure Python.
Then AppleWin under wine, COMPOSITE video mode, Stefan's eye against
the /tmp previews; then the corpus verdict, tuning if ruled, goldens,
docs/08 C.15, the ledger, and the arcimg bump close the machine.

AP2 ADDENDUM 2: the bootloader question is settled. Peter Ferrie is
qkumba, known personally to Stefan (he fixed the original Apple II Z5
interpreter for the BuildTools), and his qboot is PUBLIC DOMAIN on
Stefan's word. The path is clear: vendor QBOOT.S, translate
Merlin-syntax to ACME with the adaptation plainly marked, mk_a2probe.py
lays probe.bin behind it, AppleWin composite verdict. Small world:
his LZSA2 decoders already serve the M65 and MS2 probes.

## CHECKPOINT for pickup (2026-08-17 evening, model handover at the
## budget cap): R5 two machines closed, the Apple II mid-stride

Versions: arcc 1.11.0, Cosmos 1.14.0, arcimg 1.37.0, Actaea 1.3.9.
Suites: compiler-side 1328, arc-side 183 (test_arcconvert/arcformat/
arcimg). Tree clean, everything pushed. Read this checkpoint whole,
then the day's entries above it; the memory files carry the standing
discipline. fizmo is DEPRECATED: headless play is build/actaea
--headless (or VM+CaptureIO), the ruling and the reasons are in
memory.

CLOSED TODAY, see the entries: the adopter round (block-override
answer; the spans redesign into the EXISTENCE FORM `in a, b` vs the
SIGHT FORM `spans`, arcc 1.11.0/Cosmos 1.14.0; the -L prelude fix,
broken since B5); R5 opened with Stefan's rulings (VDC parked, AP2
DHGR-only, ZEsarUX for the Next, the Agon dither probe joins); NXT
closed pixel-perfect (2bf8859); M65 closed pixel-perfect (840e05f);
what-plays-where caught up (Eris/Triton/Varuna/Haumea PLAY; Gargoyle
row = next release); Xemu installed and working (memory has the
setup).

THE OPEN LANE: AP2, the signal class, Stefan's ruling = option B
(the full NTSC model) first. DONE so far (commits 018552b, 019e1b3,
e07cc0a, b9f6be8): the converter (_convert_ap2: per-scanline DP over
560 dots, _AP2_IDX phase table, _AP2_PAL = frozen OpenEmulator
sixteen; 280-window left-weighted 8 off the left; ~2s/picture); the
AP2 format class redefined to DHGR (aux+main sections types 1/2, 40
bytes per row per page, display row order; render = the same window
model, rows doubled for aspect-true previews); the probe pre-proven
BOTH MODES (arc_image/probes/ap2/: probe.asm at $6000, softswitch
dance, staged ZX0 via vendored dzx0_6502, assembler-computed line
table; run_probe.py = strict 6502 core + main/aux softswitch model;
pairs 9.AP2/12.AP2 = IMAGE 8 both modes, ids stamped by mode, the
standing convention). The corpus gate is DELIBERATELY OPEN: previews
lived in /tmp (VOLATILE, macOS wiped /tmp once today); regenerate
with:
  python3 tools/arcimg.py convert --target AP2 -o /tmp/etri/ap2 \
      --preview /tmp/etri/ap2-prev arc_image/masters
The preview is faithful to COMPOSITE and optimistic for RGB decodes,
hence probe-first for this class.

PICKUP ORDER FOR AP2:
1. Vendor QBOOT.S from github.com/peterferrie/qboot. PUBLIC DOMAIN
   on Stefan's word: Ferrie IS qkumba, personally known to him (he
   fixed the Apple II Z5 terp for BuildTools; that old path is
   interlz3/interlz5 + Infocom's own 16K terps, nothing reusable).
   Translate Merlin syntax to ACME, adaptation plainly marked,
   credit in the header like the other vendored decoders.
2. Write mk_a2probe.py (the NAME IS RULED: never mk_dsk/mk_disk,
   those collide with the interpreters' real game-disk tools): 140K
   .dsk, 35 tracks x 16 sectors x 256; qboot in T0S0; probe.bin laid
   so qboot's PHYSICAL reads meet consecutive bytes, i.e. chunk for
   physical p at file offset (track*16 + L[p])*256 with the DOS 3.3
   skew L = [0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]; the skew's
   direction is the classic mirror trap, settle it empirically (a
   wrong guess is instant garbage at $6000). Pure Python, stdlib,
   deterministic, in the probe dir (probe furniture by charter; the
   game pipeline lives in BuildTools, later, elsewhere).
3. AppleWin under wine (~/Fiction/Tools/AppleWin, homebrew wine on
   PATH; untested pairing, budget a moment for wine dust). The video
   mode MUST be composite ("Color TV" class) for the verdict; RGB
   modes decode aligned nibbles and misrepresent the DP's sequences.
   Stefan's eye against the /tmp previews.
4. THEN the corpus verdict: if too soft, tune the DP cost
   (luma-weighted distance or a flat-run preference), BEACH ONLY per
   the iteration rule, one knob per round; option A (aligned
   Polizei-flat) stays the ruled fallback. On the pass: corpus +
   previews land (arc_image/ap2, previews/ap2), goldens frozen (the
   NXT/M65 test-block pattern; no identity law here, the signal
   class approximates by nature), the unwaved-target test stays
   pointed at the parked VDC.
5. docs/08 C.15, probe-after-probe: the softswitch dance, the boot
   story (qboot provenance), the composite-vs-RGB warning as a
   loader convention, sections, the conversion recipe, MEMORY notes.
6. design.md ledger + R5 line, docs/07 what-plays-where, arcimg ->
   1.38.0, amalgamate_arcimg, README table, PROGRESS entry, one
   commit, push.

AFTER AP2: the Agon dither probe (Canopus's request, joined R5 by
ruling): one mechanism change (likely the amplitude for
gradient-class masters on AGN), Stefan's eye, corpus re-run per the
shop-window rule, never stacked with other changes. Then R6 (the
public interpreter-contract cut, arcimg 2.0).

STANDING, for whichever model reads this: Stefan drives design; his
word gates builds, his eye gates art; answers before conditioned
work; deviations surfaced before landing; measure before
contradicting (the image-8 pair scar of this very day); one machine
complete before the next; probes become files; FictionTools and the
sibling interpreter repos are NEVER modified from here; emulators
ask-first except the cleared three (ZEsarUX, Xemu, AppleWin paths in
memory); /tmp is scratch and dies, the repo and PROGRESS are the
record.

## 2026-08-17: R5 CLOSES ITS MACHINES. The Apple II lands (arcimg 1.38.0)

The signal class, approved. Stefan's ruling stood (option B, the full
NTSC model, the ii-pix lineage) and the machine confirmed it: the
converter is a per-scanline dynamic program over all 560 DHGR dot
positions, choosing bits so the decoder's four-dot window shows the
master's colour and reaching hues between the sixteen through
sequences. His verdict on the metal, both display paths: "it does the
job", the corpus "rendered perfect". Accepted as it stands, no tuning
round; option A (aligned Polizei-flat) stays documented as the
fallback nobody needed.

THE BOOT WORKED FIRST TRY, which is worth recording because the parts
were all hand-laid: qboot (Peter Ferrie = qkumba, public domain on
Stefan's word) already ships as ACME source, so no Merlin translation
was needed at all; mk_a2probe.py (the ruled name) places its three
pages on track 0 physical 0/2/4 and the probe's 35 sectors from track
1 in physical order, translating to the .dsk file's DOS 3.3 logical
order with Ferrie's OWN xlatsec table, lifted from his DOS33L.S: the
skew question the checkpoint flagged as "the classic mirror trap" was
answered by the source rather than by trial. AppleWin under wine took
the disk without a murmur.

THE DISPLAY FORK, now a documented convention (docs/08 C.15): the
conversion targets the COMPOSITE decode, the machine's own video
output; an RGB card decodes aligned nibbles and shows the sixteen
flat, losing the sequences' in-between hues. Stefan saw both. Neither
falls apart, which is the useful finding: the DP's choices stay
legible even when a card ignores the physics they exploit.

A CORRECTION WORTH KEEPING: mid-close I explained a dim moon by
"the hint sidecar the other converters use" and Stefan stopped it
flat: the salient hint is not used in any conversion. Measured: the
interface lives (_read_hint, _salient_pixels, salient threaded to the
cpc/zx3/c64/p4 routes) but no converter acts on it since the flat-base
rewrite, and the forcing helpers are uncalled. His position, restated
for the record: the FEATURE STAYS for authors; the aim was converters
so good nobody reaches for it. Reconnecting the author-facing path is
its own small round if wanted. My memory carried the R3 text and was
stale; corrected there too. Lesson, again: measure before explaining.

Landed: the AP2 format class redefined to DHGR (aux+main sections),
the corpus (22 pictures) and previews, four goldens plus shape and
render-model tests, docs/08 C.15 written probe-after-probe, the
design ledger and docs/07 current, arcimg 1.38.0 with the amalgam.
Suites: arc-side 189, compiler-side 1346. R5's three machines are
DONE (NXT, M65, AP2); the C128/VDC stays parked by ruling. NEXT: the
Agon dither probe (Canopus's request), then R6.

## 2026-08-17: the Agon dither request, RULED OUT (no code change)

Canopus (Shawn Sijnstra) asked whether the Agon converter could dither
for greater shading depth, suspecting it would help low-contrast
images. Measured first: the Agon's fixed cube steps 85 per channel, so
a nearest-cube map costs mean 13.2 / max 24 on our flat corpus art and
mean 33.9 / max 42 on a GRADIENT master, while the shipped dither
amplitude is 3, which against an 85 step does essentially nothing. A
ladder on the beach (amplitudes 3, 12, 21, 30, 42) halved the blended
error monotonically, 31.8 down to 16.2.

STEFAN'S RULING: DROPPED, no dithering on the Agon. His reasoning,
which reframes the question rather than answering it: dithering should
already come from the MASTERS, where the artist put it deliberately;
the Agon faithfully represents the maximum of the host systems, so it
has nothing to overcome. The reasonable common denominator for masters
is 32 colours, or 16-colour Amiga/ST-class art: that ports well to
DOS, translates well to the retro machines, and lands on the Agon with
no constraint to fight. None of the Rabenstein images need dithering,
and machine-made dither does not do them good. A dither question is a
constraint question; on this machine there is no constraint, so it is
the wrong way of thinking.

Recorded because the reasoning is the durable part: it is the same
doctrine as the 8-bit path's "no machine dither, the author paints
it", extended to say WHY a rich fixed-palette target needs it least.
Nothing was implemented; the comparison ladder lived in scratch only.
R5's machines are done and this closes its last item. NEXT: R6 (the
public interpreter-contract cut, arcimg 2.0).

OPEN, unruled, one line each: the shipped previews for the half-width
machines (AGN, TRSM4) are still rendered squashed, 640x96, while the
Apple II's are now aspect-true; making them consistent is a small
round whenever wanted. And the salient-hint plumbing stays inert until
the author-facing capability is deliberately reconnected.

CORRECTION, same day: "the C128 is parked" was my wording and it was
wrong. Stefan: the C128 is a machine of the family in its own right,
named separately, using the same model as the C64 (VIC-IIe, the C64
assets); only its VDC 80-column picture path is parked, and that
question belongs to the interpreter rather than to arc_image. Both
tables now say exactly that: docs/07 gives the C128 its own row, and
the design ledger's C128 row states the model and the reason (an
interpreter spends the machine's extra memory on the story, not on
the picture).

## 2026-08-18: B12 IS COMPLETE. R6 closes arc_image (arcimg 2.0.0)

The retro graphics milestone is finished: FIFTEEN shipping formats
covering SIXTEEN machines (the C128 rides the C64's; a sixteenth
format, its 80-column VDC path, is specified and parked), every one
carrying a reference loader proven on accurate emulation and reviewed
by Stefan's eye. The counts were wrong in my first writing of this
entry ("sixteen formats across seventeen machines"), and the fix that
followed ("fifteen formats covering sixteen machines") was accurate
but confusing. STEFAN'S RULING on how to say it: arc_image COVERS 16
MACHINES, full stop; the public documents do not split formats from
machines. The engineering ledger in design.md keeps the precision it
needs (the C128 shares the C64's format; the VDC path is specified
and parked). The Agon also had no ledger row despite shipping since
2026-08-14, and now has one. R6's three real items
are done, and one was struck as a phantom.

STRUCK: "the public interpreter-contract document published (the
Vezza-facing cut)". Stefan's observation closed it: the document is
already public in the repository. That line was R0-era wording from
before docs/08 existed in its present form, when the plan imagined
extracting an outsider-facing cut so a third party (Shawn Sijnstra's
Vezza, the first) would never read Arcturus internals. docs/08 IS that
document, implementer-facing throughout, and R6's own text already
defines the handover as documents and content: the chapters, each
target's probe source as reference loader code, the two-mode .arc test
assets, and the arcimg standalone for rendering any .arc back to PNG
as ground truth. All four exist. design.md now says so in place of the
promise.

THE SIZE LEDGER IS MEASURED at last, R1's promise honored: the whole
22-picture corpus, mode 12, packed with each target's own codec, in
design.md ("The size ledger, measured"). What it teaches, and worth
knowing before sizing a disk: the cell machines compress WORST by
ratio (the C64 at 66% of raw) because an attribute solver's output is
already dense, yet they remain the smallest payloads in the family
(the ZX3 median is 2054 bytes); the rich machines compress best (NXT
and M65 near 20%) because band art is mostly flat regions at 8 bits a
pixel; and the Agon is the deliberate outlier (RLE, 29% of a 61K raw
payload) because Shawn ruled simplicity over ratio for a streaming
loader on a FAT32 machine with no reason to count bytes.

Also landed: arcimg 2.0.0 with its amalgam and the README table,
docs/00 marks B12 COMPLETE (and names the adopters implementing the
format: Vezza and Canopus, Ozmoo, Dialog, Gargoyle), docs/07's "never
hand-paint fourteen versions" caught up to sixteen, and WHATSNEW leads
with the finish (the older, now-stale pictures entry rotated out rather
than a fresher one, since the new entry supersedes it). Suites: arc-side
189, compiler-side 1346.

WHAT B12 LEAVES BEHIND, for the record: one master painting per image,
sixteen native formats derived by tool, fifteen probe directories that
double as reference loaders, a container spec and two codecs ported to
6502, Z80, 68000, 8086 and eZ80, and five outside implementations of
the format (Vezza, Canopus, Ozmoo, Dialog, Gargoyle) plus five of our
own interpreters playing bands today. The author's cost stayed one
painting; Stefan's original eight months of hand-porting Rabenstein art
is the number this milestone was measured against.

NEXT: B13, the Rabenstein port from DAAD, which this milestone exists
to serve. Its art is already converted for every target.

OPEN, unruled, small: the AGN and TRSM4 previews still render squashed
(640x96) where the AP2's are aspect-true; the salient-hint plumbing
stays inert until the author-facing capability is deliberately
reconnected.

## CHECKPOINT for pickup (2026-08-18): B12 CLOSED, B13 PARKED, the
## lettered milestones are done for now

B13 IS PARKED, Stefan's ruling of this date: the Rabenstein port waits
until interpreters exist for the arc_image host machines. A graphics
showcase with nothing to show it on proves nothing; the interpreters
are the gate, not the port, and they are Stefan's own work in the
sibling repositories (never touched from here). The art has been
converted for every machine since B12, so the port is unblocked the
day he says so. docs/00 carries the ruling.

WHERE THE PROJECT STANDS. Versions: arcc 1.11.0, Cosmos 1.14.0, arcimg
2.0.0, Actaea 1.3.9, proteus 1.0.0; VS Code extension 1.2.1, Zed
extension 1.0.0. Suites: compiler-side 1346, arc-side 189 (the Actaea
curses test needs a TTY, so never run the whole suite detached).
Everything is committed and pushed; the tree is clean.

MILESTONES: B0 to B12 are complete. B9 was dropped long ago (Ghosts),
B13 is parked as above. There is no lettered milestone in flight for
the first time in the project's life, which means the next work is
chosen rather than queued.

THE PARKED LANES, each on Stefan's word, none started:
1. CRAVERLY HEIGHTS (Ryan Veeder, permission given): the English
   example port. Workspace examples/craverly exists and is gitignored,
   with PORTLOG.md. Read the PunyInform port first and note its
   Inform-7-behaviour backports as Cosmos candidates ("if it serves
   Inform 7 well, it might also serve us").
2. HIBERNATED 1 AUF DEUTSCH: port first under the H2 discipline (no
   game content in tracked files, ever), translation second, Stefan's
   native pass gating line by line. Workspace examples/hibernated1_german,
   gitignored, PORTLOG.md.
3. ZED PR AFTERMATH: when zed-industries/extensions merges the
   submitted PR (bot-approved, human pending), Stefan verifies the
   in-app listing and uninstalls the dev extension. The fork clone at
   ~/Fiction/Misc/extensions stays for future update PRs; the update
   flow is documented in editors/zed/README.md.
4. ADOPTER SUPPORT as it arrives (the pattern of the last two days:
   reproduce against the exact shipped binary from git history, measure
   before concluding, sort defects from misunderstandings, answer in
   Stefan's voice as a pasteable block).

SMALL OPEN ITEMS, unruled, one line each: the AGN and TRSM4 previews
still render squashed (640x96) where the AP2's are now aspect-true;
the salient-hint plumbing is inert (the interface lives, no converter
acts on it) until the author-facing capability is deliberately
reconnected, and Stefan's position is that the FEATURE STAYS while the
converters aim to make it unnecessary; probe_noun stays classless from
the German round; the Actaea Beyond Zork gap stands untriaged and is
never to be started unprompted.

WHAT THE LAST TWO DAYS ADDED, for context when reading the entries
above: the German forum round's aftermath (answers, the Discord
announcement, the VS Code and Zed extensions, the registry PR); two
adopter reports from EdwardianDuck that produced the EXISTENCE FORM
(`in a, b` as true multi-room presence, against `spans` as sight) and
the -L prelude fix that had been broken since B5; then B12's last
round, R5, which closed the Spectrum Next, the MEGA65 and the Apple II
and ruled out the Agon dither request, followed by R6's close of the
whole milestone at arcimg 2.0.0.

STANDING DISCIPLINE (the memory files hold the full set; these are the
ones this stretch exercised hardest): Stefan drives design, his word
gates builds and his eye gates art; answer questions before starting
conditioned work; surface deviations before landing them; MEASURE
before contradicting him (two scars this stretch, the image-8 probe
pairs and the salient hint); one machine or one mechanism at a time,
never stacked; probes and their tooling become durable files; the
sibling interpreter repos and FictionTools are never modified from
here; emulators are ask-first except the cleared three (ZEsarUX, Xemu,
AppleWin, paths and setup in memory); headless play is Actaea, never
fizmo; /tmp is scratch that dies, the repository and this file are the
record.

CHECKPOINT ADDENDUM (2026-08-18, after the docs round): the author
guide got the treatment B12's close deserved, all in docs/07 section 6
("Budgeting your pictures"), and the state above is otherwise
unchanged. What landed, so nobody re-does it:

- BOTH BAND SHAPES have measured tables (band 9 was missing, which
  Stefan called misleading), with a compression column and a legend
  saying what each column answers: unpacked is a RAM question, typical
  is the median to multiply, largest is what to size a disk by, packs
  to is the codec's win. The band-9 numbers were measured by slicing
  the whole corpus with `arcimg slice9`; both sets live only in the
  document (design.md keeps the byte-exact band-12 ledger).
- THE NATIVE-FORMAT BENCHMARK, Stefan's idea and the section's aha:
  each machine's usual full-screen picture beside our band (Koala 9.8K
  against 3.1K, .SCR 6.8K against 2.0K, IFF 39.1K against 7.5K), read
  out in pictures per disk. Two reasons stated separately: we store a
  band, not a screen, and then we compress it. All sizes in KB.
- THE SHOWCASE is per-machine standalone, one picture each, every entry
  naming the constraint that machine fights. No grouping, no image
  shown twice (Stefan: identical-looking machines under one caption
  taught nothing). It survives a change of master picture, which he
  expects when he writes a new illustrated game.
- THE SPECTRUM IS SHOWN TWICE, deliberately: the automatic black-and-
  white conversion FIRST (taken from the converter in memory, because
  the ZX3 corpus entry is intentionally HIS hand-painted art and is
  never to be overwritten), then the hand-painted version beneath it as
  what the polish loop buys. Never "fix" the corpus mismatch there: it
  is the design.
- Rabenstein is no longer named in the author guide except where it is
  the filename of the shipped demo (examples/arc_image/rabenstein.*).
  Stefan's rule: the corpus came from an existing game, and the
  author-facing document is not the place to advertise it.
- Multipaint (Tero Heikkinen, multipaint.kameli.net) is recommended by
  name and link as the tool for masters; the "playable today"
  parenthetical is gone from the modern-path heading, since it read as
  though the retro half were unfinished.
- tools/docs_showcase.py builds every showcase picture from the
  committed corpus (plus that one in-memory Spectrum conversion), so
  the guide cannot drift from the converters. RE-RUN IT whenever a
  converter changes, exactly as the corpus and previews are re-run.

## CHECKPOINT for pickup (2026-08-18, pre-compaction): the adopter
## round opens next

Read the 2026-08-18 checkpoint above this one first; everything in it
still stands (B0-B12 complete, B13 parked until Stefan's interpreters
exist, no lettered milestone in flight, versions arcc 1.11.0 / Cosmos
1.14.0 / arcimg 2.0.0 / Actaea 1.3.9, suites 1346 + 189, tree clean
and pushed). This addendum is the delta since:

- ZED PRS, BOTH STILL OPEN: the Arcturus extension (3 days) and
  Stefan's Inform6 x PunyInform extension (2 days; NOT part of this
  project, built with an Opus instance for the community, based on
  Natrium's but expanded with a tree-sitter grammar and first-class
  PunyInform support; he calls it "super good"). Both bot-approved,
  awaiting the human merge. Nothing to do but wait; on merge, Stefan
  verifies the in-app listings and uninstalls the dev extensions.

- THE NEXT WORK IS THE ADOPTER ROUND, on Stefan's word, reports
  arriving from him one at a time. His framing worth keeping: the
  reports are SHIFTING FROM ISSUES TOWARD FEATURE REQUESTS, which is
  the stable-codebase pattern (Fredrik's lesson in memory), though he
  notes there are still some underlying issues in the queue. The
  discipline, unchanged and battle-tested across the EdwardianDuck
  round: reproduce against the exact shipped binary from git history
  (git show <commit>:build/arcc), MEASURE before concluding or
  contradicting, sort real defects from misunderstandings, treat
  feature requests as design questions for Stefan (discuss first,
  never build on the report alone), and hand him pasteable answers in
  his voice, plain mechanics, no coined jargon.

- Nothing else moved: no code, no docs, no corpus changes this
  session; the only writes were this file and two memory notes (the
  Zed extension state; the docs-showcase rule from the prior round).

## 2026-08-18: the adopter round opens. The selection idea, RULED OUT;
## a loader-error fix lands (arcc 1.11.1)

EdwardianDuck reported back on the override recommendation from the
last round: he moved his personal message overrides from a granule to
.storyarc chapter files, one file per message, because a whole-file
collection cannot be partially overridden in a specific game (chapter
blocks rank as game, and a repeat at the same rank is a genuine
duplicate, by design). He called his own approach over-thinking; it is
in fact the correct shape, and measurement added two comforts he did
not know: name-form chapter summons search the -L path, so his whole
override library can live in one personal directory shared across
games, and a local copy in a game's folder shadows the -L master, so
per-game trimming needs no second mechanism.

From there he floated a feature: generalize the extendedverbs slice
syntax so `summon my.storyarc feature1, feature2` takes named pieces
of any file. Measured: the syntax already parses (the selection list
exists on every summon form since the verbs overhaul); only the
semantics are verb-only, so the question was purely what a selection
means for a file without verbs.

STEFAN'S RULING: NO CHANGE. His reasoning: the author is building
himself the modularity he needs, and the language already provides
it; a single file summoned per game with unwanted overrides commented
out (or the copy-and-trim pattern) does the same job in plain sight.
Files are the selection mechanism. A second way to say something the
language already says is how a small language stops being small.

ONE REAL DEFECT surfaced by the measuring, fixed on Stefan's go as
its own commit: every load-time summon error (missing granule, bad
verb selection, the language gate, the clashing-presentation pair)
escaped as a raw Python traceback, because the combined_program call
in the CLI was the one compile stage outside the ArcError handler.
Now it prints the same one-line file:line error as every other stage
and returns 1. Test added (tests/test_cli_errors.py); full suite 1498
green; arcc 1.11.1, standalone regenerated and the README table
refreshed. Adopters get it with arcc --update, as always.

FIELD CONFIRMATION, same morning: EdwardianDuck updated his WIP port
to the split forms and reports all working as expected, and the new
compile-time gates flagged real mistakes in his door definitions,
which he counts as a bonus. The existence-form redesign is field-
verified by the adopter whose report started it, and the loud-boundary
ruling (a compile error with a pointer, never a silent drop) paid out
on first contact.

## 2026-08-18: STEFAN'S RULING: documentation before the NPC engine.
## Every shipped kind gets its written contract

The fos13 thread (a ParserComp organiser porting a large TADS/Adv3Lite
game) surfaced a real documentation gap: he could not find how to
create an NPC in the handbook. Measured: the word NPC appeared only in
passing, and chapter 3's Standard kinds section gave the character
kind three lines. Stefan's ruling, before any NPC engine work: the
handbook must state, for EVERY kind that ships with the system, what
it means, what it inherits, which attributes it sets, and what the
library already does for it; the NPC engine gets the same treatment
when it exists.

DONE: chapter 3's Standard kinds rewritten from one terse list into
per-kind subsections (thing, room, container, supporter, door,
character), opened by the three governing rules (full inheritance
from thing; universal-only kind defaults, the bowl rule; kinds are
testable and dispatchable). Character's entry says NPC out loud so
search finds it, and carries a worked declaration (innkeeper Aggie,
a fresh scene, never an adopter's) that was compiled and played
before it entered the book. Every behavioral claim was measured
first, compiler and library both: the kind defaults in sema (room
lit, character animate, door openable+fixed, container and supporter
deliberately nothing), the take-refusal ladder, the conversation
seams (one brush-off with no granule; ask/tell and menu in chapter
17), give/show validating on the action, and the holds-and-wears
contract, including the measured fact now stated plainly: a
character's belongings are OUT OF THE PLAYER'S SCOPE until the
author reveals them. A stale cross-reference fell out with the
rewrite (default handlers pointed at chapter 15, the output
chapter; now chapter 12).

## 2026-08-18: the cross-reference sweep, on Stefan's "obviously I
## want it now" (arcc 1.11.2, Cosmos 1.14.1)

The kinds rewrite exposed one stale chapter pointer; Stefan ordered
the full sweep. Every "chapter N" and "Section N" reference was
audited against the real chapter list: 219 in the handbook by hand,
about 120 in the compiler package and 88 in the Cosmos library by two
parallel audit agents whose every finding was re-verified in place
before a byte changed, and the design docs' eight inline. Found and
fixed, thirty-one in all:

- HANDBOOK, sixteen: the attribute table's stale old-arrangement
  numbers (shiftable "Section 10" -> chapter 12, restless "Section
  12" -> 16, arc_image "Section 6b" -> 20); restless's teaching text
  pointing at Scoring (19 -> 5); grains called chapter 22 twice in
  the parser chapter (-> 18); the move-versus-gain warning cited
  three ways, none right ("chapter 3" twice, "Section 5" once, all
  -> 4, where the CAREFUL INFORM HANDS text lives); article words to
  the daemons chapter (16 -> 15); ZSCII to Hacking Cosmos (23 -> 1);
  a mangled "(02 chapter 1)" (-> 2); a doubled "(chapter 2; chapter
  2)"; and two cross-doc pointers into documents that have sections,
  not chapters (docs/00 "chapter 23" -> section 5, docs/04 "chapter
  3" -> section 10).
- CODE COMMENTS, fourteen: the topic machinery cited the granules
  chapter five times where the conversation chapter teaches the
  construct (ast, tokens, objects, prelude -> 17); verbless actions
  and the standard verb set cited the turn loop (-> 12); the turn
  loop itself cited chapter 3 in loop.prelude's header (-> 13); the
  gain warning again (-> 4); the German copula (16 -> 15); the
  multi-role pronoun trio cited chapter 21, which contains no
  pronoun text at all (-> 14, parser.prelude, english.prelude,
  german.granule); and a fossil "docs/01 s6" (-> chapter 5).
- ONE STRUCTURAL FIND, fixed at the root: the author-kinds block
  (kind templates, the inheritance chain, resolution order, the
  mixins non-goal) sat physically inside chapter 4, The player, an
  old-arrangement stranding. It moved home to chapter 3 as "Kinds of
  your own", after the standard kinds; its closing summary paragraph
  was dropped as fully redundant against the new per-kind contracts.
  The compiler's "resolution order (docs/01 chapter 3)" citation
  became correct by the move instead of by editing the comment.

Cosmos comments ship to authors via --extract, so both versions
bumped honestly (arcc 1.11.2, Cosmos 1.14.1), the standalone
regenerated, the README table refreshed. Suite 1498 green; the
sweep touches only comments and the handbook, no behavior.

## 2026-08-18: the NPC engine designed. STEFAN'S RULINGS, no code yet

The design round he promised the adopters, held and closed in one
sitting. The rulings, all his:

- TWO GRANULES, not one. summon.npcengine is the engine;
  summon.maniacswap is multi-player-character switching, its own
  granule from day one, because an author may want to swap player
  characters with no NPCs anywhere (the modularity argument: cramming
  it into the engine would lose what the granule system built).
  Combinable, never entangled. Maniacswap's verb is BECOME, existing
  only when summoned; swapping works from anywhere, and the author
  gates it in fiction when the story demands; the abandoned body
  freezes in place until taken over again.
- V1 SLICE of the engine: movement (patrol routes, wandering in a
  territory, pursuit via the shipped path engine, stay), presence
  prose (arrivals, departures, encounters, overridable per
  character), agenda as when-guards and author-handleable events,
  commanding characters (MARSHAL, GO NORTH; ruled into v1: "now we
  need it"), and a one-shot send for authored beats. Declaration
  surface is plain properties and handlers on the character, no new
  block form.
- THE CONTROLS, Stefan's own design and the round's centerpiece:
  every NPC starts HIBERNATED, inactive at zero per-turn cost, the
  frozen-process model (the name is, of course, his). resume(x) and
  hibernate(x) flip one NPC; resume(npc_engine) and
  hibernate(npc_engine) act on the whole cast through a MASTER GATE
  on the engine itself, ruled over the broadcast reading so a
  cutscene freeze preserves and restores the author's exact per-NPC
  mix; everything testable (if x is hibernated). This dissolved the
  round's one hardware worry, the per-turn path cost of a large cast
  on an 8-bit CPU: activity is opt-in per NPC per scene, so the cost
  class is gone rather than measured.
- HIBERNATED IS A PROCESS STATE, NOT A FICTION STATE, ruled bluntly
  for the handbook: a hibernated character still answers ASK, still
  accepts GIVE, still obeys a command; the word gates only whether
  the engine spends a turn on their agenda. And it gates ONLY
  npcengine activity, never the author's own each_turn, so idle
  flavor keeps breathing on a character whose patrol sleeps.
- POSSESSION, the July requirement, is discharged by composition:
  the frozen state and the inactive state are one shared attribute,
  so taking over an engine-driven character hibernates their agenda
  on entry and restores it on release. A consequence of two granules
  sharing a word, not a feature to build.

No build authorized; the go is Stefan's, and the natural order when
it comes is the engine first (an adopter's large port is waiting on
moving NPCs), maniacswap second.

## 2026-08-19: THE NPC ENGINE LANDS (arcc 1.12.0, Cosmos 1.15.0)

Built in one sitting on Stefan's go, exactly to the round's rulings; an
adopter's large port was the waiting field case. summon.npcengine:

- MOVEMENT declared on the character: patrol (a cycle of adjacent
  rooms, one waypoint pause, pure adjacency), territory (rooms or a
  room kind, wandered one adjacent step at a time), pursue/send (the
  authored errand through way_toward, one searched step per turn; a
  reached room ends the pursuit), opens_doors (closed doors open
  visibly en route; locked still bars; door_bars stays the seam).
- THE CONTROLS, the round's centerpiece, exactly as ruled: hibernated
  by default at zero per-turn cost, resume/hibernate by name, the
  master gate on npc_engine preserving the per-NPC mix, everything
  testable. The gate semantics fell out of one design stroke: the gate
  object carries the same attribute, so one uniform block serves both
  levels with no special case.
- PROSE follows scope deterministically in all three languages
  (departures with direction, arrivals with where-from, the door
  opening seen from either side); German speaks its compass as proper
  nouns via its own direction block, Spanish its own idiom, both
  flagged for Stefan's native pass.
- EVENTS on the ordinary pipeline: npc_arrives (a send completing),
  npc_blocked (each turn a step cannot be made), the character as
  noun, silent unhooked.
- THE ADDRESSED IMPERATIVE, ruled into v1: WATCHMAN, GO NORTH, in all
  three languages through one skeleton-level pre-pass (the comma chain
  split was the natural seam; probe_noun the side-effect-free matcher).
  The character's own on command decides via ordered/ordered_noun/way;
  the default politely refuses; an order reaches a hibernated character
  (process state never gates fiction).

The compiler side mirrors the proven existence-form pattern: sema
collects and validates the roster (loud gates: patrol needs two rooms
and no kinds, engine behavior needs a character, territory expands room
kinds), objects.py emits route arrays in the spans shape and the roster
table, lower.py folds any_npcengine and reads routes through intrinsics,
and the two new globals allocate AFTER every other global including the
game's own, which is what closed the byte gate.

DONE-TEST: tests/test_npcengine.py, 22 tests (controls, the mix through
a gate cycle, all movement modes, doors and locks, events, commanding,
the three languages, the loud compile gates, the unsummoned-name case);
the byte-identity gate proved all 51 examples byte-identical against
the shipped 1.11.2 standalone, file by file; full suite 1518 green.
The worked example is examples/granules/npcengine.storyarc (The Night
Rounds, a fresh scene). Handbook: the npcengine section in chapter 22,
the addressed imperative in chapter 12, chapter 17's deferral line paid
off, chapter 3's character entry points at the engine, and the stale
summonable-features list repaired to the full roster. maniacswap stays
future by ruling, on its own timeline, and took the engine's place on
the public roadmap.

Found and fixed along the way, before they could ship: the search flag
leaking into the step (a warden ghosting through a door it should have
opened), the address pre-pass zeroing its own flag through recursion,
and two false alarms measured down to my own test construction (a
Python operator-precedence slip) and to global renumbering, which the
tail allocation then eliminated entirely.

ADDENDUM, same day (arcc 1.12.1, Cosmos 1.15.1): Stefan's practical
question ("do orders need the summon?") uncovered a gate mismatch: the
addressed imperative folded on the ROSTER, so a game summoning the
engine purely for orders, with no character declaring movement, found
them silently dead, against what chapter 12 said. Ruled and fixed on
his go: commanding now folds on the SUMMON itself (the new
any_commanding), the walk keeps its roster fold, and the engine's
property names unify with the summon rather than the roster, which the
orders-only case needs to compile at all. One new test (orders with an
empty roster), suite 1519 green, the byte gate re-proven clean against
the committed 1.12.0 standalone.

## 2026-08-19: MANIACSWAP LANDS (arcc 1.13.0, Cosmos 1.16.0)

The second granule of the design round, built in the same lovely run,
exactly to the rulings: its OWN granule, never part of the engine.
summon.maniacswap:

- BECOME is the verb (WERDE, ENCARNA), existing only when summoned;
  `playable` marks a body (a character, on pain of an error; the boot
  player is playable by default). The swap works from ANYWHERE, even
  between maps that never connect, through the reach seam; the story
  gates it in fiction with an ordinary `on become` handler on the body
  (stop vetoes, continue allows), exactly as ruled. become(x) is the
  authored-beat call.
- THE LEFT BODY FREEZES where and as it was, holding its own
  inventory, listed in its room, examinable in third person; the mind
  (score, turns, every global) travels with the keyboard. The freeze
  IS the engine's hibernated attribute, so the composition ruling
  discharges itself: a summoned npcengine never drives a frozen PC nor
  the body being ridden, and riding an engine character pauses its
  agenda for exactly the stay.
- ME FOLLOWS THE KEYBOARD, the July analysis's me-words seam, solved
  as the SELF PRONOUN: the language layer's standard self words become
  pronoun role 7 when maniacswap is summoned (sema marks them at the
  player merge, the dictionary re-flags them, pronoun_slot answers
  with the player global). Spanish's clitic machinery composed
  unprompted: EXAMINATE resolves the new self correctly. Game-added
  player words stay ordinary vocabulary, so the abandoned boot body
  keeps its third-person name; the documented pattern names the boot
  body (player.name, player.named, player.words henrik).
- THE REACH SEAM became a DISPATCHER so debug and maniacswap compose
  instead of colliding on one override: all four language layers
  dispatch to per-feature stubs behind summon folds.

THE BYTE GATE EARNED ITS KEEP TWICE. First, +28 bytes in every game:
any_reach judged the seam live because its triviality test wanted a
literal lone `return nothing`; it now judges AFTER static folds, so
the dispatcher counts as dead in games without either granule. Then,
with sizes restored, cmp still failed on TWO bytes, and the second was
one locals-count byte: a `let` in a statically dead branch still
allocates its slot (the dead-branch-let lesson, striking again); the
debug leg moved into its own block. Only then: all 52 examples
byte-identical, proven with cmp, not with sizes. The lesson is now
written into the dispatcher's comment.

DONE-TEST: tests/test_maniacswap.py, 9 tests (the cross-map swap, the
self words and third-person naming, the refusals, the fiction gate,
the engine composition with the frozen PC, the loud playable gate, the
unsummoned case, German and Spanish natively); full suite 1529 green;
the worked example is examples/granules/maniacswap.storyarc (The Two
Shores, a fresh scene, played through headless). Handbook: the
maniacswap section in chapter 22, chapter 4's player chapter points at
it, the granule table and the features list carry it. WHATSNEW leads
with it and its roadmap entry retires, shipped.

## CHECKPOINT for pickup (2026-08-19): the granule pair shipped;
## Stefan builds interpreters next

The standing state: B0 through B12 complete, B13 (the Rabenstein port)
PARKED by ruling until interpreters exist for all the arc_image hosts.
No lettered milestone is in flight. Versions: arcc 1.13.0, Cosmos
1.16.0, arcimg 2.0.0, Actaea 1.3.9. The full suite is 1529 green (one
pytest run covers compiler, library, and Actaea; it needs a real TTY).
Tree clean and pushed.

WHAT LANDED TODAY, all on Stefan's explicit go, entries above with the
full detail: the NPC engine (summon.npcengine; movement, the hibernated
controls with the master gate, presence prose in three languages, the
events, the addressed imperative; then the orders-fold fix at 1.12.1)
and maniacswap (summon.maniacswap; BECOME across any distance, the
frozen left body, the SELF pronoun, the fiction gate; the byte gate
caught the any_reach triviality bug and the dead-branch-let byte, both
fixed). Both announced on Discord by Stefan from the WHATSNEW texts;
fos was pointed at the engine announcement. The German and Spanish
engine prose is Stefan-approved; maniacswap's words (WERDE, ENCARNA,
and its pack lines) still await his native pass, a small open item.

WHAT STEFAN DOES NEXT, in his own words: "until it's time to focus on
new requests I am going to prioritise now the development of the
remaining interpreters", meaning the arc_image host interpreters (his
own projects: the Eris/Varuna/Haumea family, Triton, Canopus's side,
and the rest of the what-plays-where table). That work lives outside
this repo; docs/08-arcimage-interpreters.md is the interpreter-facing
specification he builds against, and its per-machine chapters are the
reference if he asks questions from the metal. When those interpreters
cover the hosts, B13 unparks. The assistant's posture meanwhile:
adopter support in the established discipline (reproduce on the exact
shipped binary, measure before concluding, feature requests are design
questions for Stefan, pasteable answers in his voice), and NOTHING
started unprompted.

Small open items carried, one line each: the AGN and TRSM4 previews
are still rendered squashed while AP2's are aspect-true; the
salient-hint plumbing stays inert until deliberately reconnected;
the Actaea Beyond Zork gap stands (never start unprompted); the Zed
PRs (Arcturus, and Stefan's separate Inform6 x PunyInform extension)
were last seen open and bot-approved, awaiting human merge.

## 2026-08-20: the status bar seats its row once (Cosmos 1.16.1).
## STEFAN'S CORRECTION: the two reports were one issue, not two

FROM HIS OWN INTERPRETER WORK. Stefan brought a report written while
building Triton and Haumea (the CPC host), reproduced on both, and
paired it with Shawn's Discord observation from Canopus on the Agon
Light: the status bar is painted twice on any turn that changes room,
first with the new room and the OLD move count, and the split is
re-issued at every paint instead of establishing the row once.

I answered that these were two separate topics. STEFAN CORRECTED THAT:
he had presented them as one issue on purpose, and the trace proved
him right. The truthful division is one root cause plus one
independent redundancy. The redundancy: draw_status re-issued
split_window on EVERY paint, in every game with a bar, graphics or
not. The root cause, which owns both remaining symptoms (the leftover
split on a movement turn AND the stale-count second paint), is the
single band re-seat call in draw_room_image. HIS ORDER: fix the
redundancy first, discuss the re-seat separately. This entry is the
first half only.

MEASURED BEFORE TOUCHING ANYTHING, since the reports came from other
people's interpreters. A probe traced every split_window, draw_image
and completed bar paint on Actaea, playing the Rabenstein demo. With
Actaea's default (no picture support) the extra paint never appeared;
setting Flags 1 bit 1, the header bit Cosmos's pictures_available
reads, reproduced the reported stream exactly, four boot splits
included. That pinned the trigger: this is the arc_image path, not the
bar as such, which is to say exactly the hosts Stefan is writing
interpreters for.

THE FIX. The split is establishment, not painting. The bar now
remembers its row (bar_seated) and reserves it only after something
took it away, through a new prelude seam, bar_unseated, empty and free
in a game with no bar: the conversations menu's taller window and its
close, the quote box at both ends, screen_ready (which every
full-screen erase already comes back through), and a restore, whose
rewound memory may describe a screen the interpreter reset underneath
it. Wrong in the safe direction costs one spare split; wrong the other
way would put prose in the bar's row, so every doubtful path clears it.

WHAT CANOPUS SEES NOW, per turn: boot 4 splits to 3; a turn that
changes room 2 splits to 1; a turn that does not, 1 to 0. In a
text-only game the bar now splits ONCE for the whole session. The
single remaining split on a movement turn is the band re-seat, the
deferred topic.

COST, stated plainly because size is a charter objective: +24 bytes,
+32 where the quote box or the menu is also summoned, in games WITH a
bar only. Every other example is byte-identical, proven with cmp
across all 53 example builds, 15 unchanged files and 38 changed, every
changed one a statusline game. The bytes buy one fewer opcode per turn
forever, on machines where a split is not free.

DONE-TEST: tests/test_statusline_seat.py, 6 tests reading the story's
OP STREAM rather than the screen, because that is where the defect
lived (the picture was always right; the waste was invisible until
someone counted opcodes): seat-once-repaint-after, the bar-less game
that never splits at all, the menu and the quote box giving the row
back, the restore re-seat, and the quiet turn costing no split on a
picture-claiming interpreter. Full suite 1535 green. Handbook chapter
23 states the rule for anyone writing a granule that takes the upper
window.

## 2026-08-20: the bar paints what changed (Cosmos 1.16.2).
## STEFAN'S RULING: the second paint STAYS, it is the contract

THE SECOND HALF of the interpreter-authors' report, taken up the same
day on Stefan's "I want to take this now", with a piece of information
only he had: on a modern interpreter the band's rows are RELEASED back
to the text view in a pictureless room and built up again in the next
pictured room. That is precisely the case docs/08 section 3a was
written for, and reading it settled the question: the bar paint after
every image change is a PUBLISHED CONTRACT, promised on the wire, with
both demos pinned to the stream in the test suite. Triton, Haumea,
Canopus and Actaea's own window are all written against it. STEFAN
RULED: we keep it, "there is a reason it is part of the contract."

SO THE FLICKER HAD TO COME FROM SOMEWHERE ELSE, and measuring found
it inside the paint, not between paints. Painting the left side meant
blanking the whole row and writing the room name back over the blank:
74 character writes for a 40-cell row, 34 of its cells written twice.
On a memory-mapped screen that IS the name going away and coming back,
and the contract asks for it twice on a scene change.

THE FIX: the left side is painted only when it actually changed, so an
ordinary turn writes the numbers alone, which are the only thing that
moves. Measured on a 40-column screen, Rabenstein, per turn: a turn
that changes room 116 writes down to 68 (and the name painted ONCE,
not twice); a turn that changes nothing 57 down to 9. Identical shape
in all three languages.

WHAT THE ROW SHOWS is remembered as room, nesting, darkness, and the
width it was laid out for (a resize moves the right-hand block, and
the story hears about it only by reading screen_width again). It is
forgotten through bar_unseated, yesterday's seam, which turned out to
be exactly the same list of events: the menu, the quote box, a
full-screen erase, a restore, and the band re-seat. One seam, both
halves.

THE TEST CAUGHT THE ONE THING THAT MATTERED. Written for the contract
case (a picture that changes in the SAME room), it failed: screen_ready
cleared the reservation but not the remembered content, so the paint
after a band change was a cheap one. On an interpreter that had just
handed the bar's row back to the text, that would have left the room
name missing. screen_ready now forgets both, and the test pins it.

A guard space rides in front of the numbers in all three language
packs: with no blank-and-redraw, a counter that SHRINKS (undo rewinds
turns, a penalty rewinds score) would otherwise leave its old leading
digit standing.

COST: +40 to +64, in games with a status bar only; the 15 examples
without one are byte-identical under cmp. DONE-TEST:
tests/test_statusline_seat.py, now 14 tests (the op stream and the
cells written); full suite 1543 green. docs/08 section 3a now states
all three parts of the contract in writing: the post-band paint is
WHOLE, ordinary paints are partial and must not be read as the story
forgetting the room, and the numbers on the post-band paint belong to
the turn in progress, which is the stale count the reporters saw and
correctly flagged as odd. Handbook chapter 22 documents bar_unseated
for authors who paint into the row themselves.

STILL OPEN, Stefan's own observation, ruled unrelated and next: in
Actaea's window, coming from a pictureless room into a pictured one
can leave the view needing a manual scroll. Two candidates in
actaea/gui/app.py, the relayout that shrinks the text widget when the
band returns without re-asserting the tail, and _show_unread's
read-from-the-top jump firing far more often in a shortened area. His
one-second diagnostic decides it: press a key instead of scrolling,
and if the view snaps to the bottom it is _show_unread.

## 2026-08-20: Actaea's window learns [MORE] (Actaea 1.4.0).
## STEFAN'S RULINGS: bottom, appended, reverse video, any key, adaptive

THE QUESTION WAS HIS. Chasing the scroll behaviour he saw entering a
pictured room, the diagnosis came out "not a bug": the window jumps to
the top of a passage that does not fit, deliberately, because there was
no [MORE] to stop it, and a picture band halves the reading area so it
fired on ordinary room descriptions. Stefan then asked the better
question: should Actaea have a [MORE] at all, the way Gargoyle does,
with infinite scrollback afterwards? It resolves the root cause instead
of the symptom, and the curses front end has paged since it was written,
so the window was the odd one out.

HIS RULINGS, all four: the marker goes where every other interpreter
puts it, appended at the bottom in reverse video, never painted over
existing text, curses style. The page adapts rather than assuming a
fixed screen ("this needs to be done since Actaea has a full screen
mode"). Any key continues. And the two implementations stay separate:
"the curses one works brilliantly and I rather don't want to touch it",
with my agreement that the shared part is about five lines of counting
while measuring, drawing and waiting have nothing in common.

BUILT: actaea/gui/pager.py owns the arithmetic (how many display lines
a piece of text takes, where to cut it so exactly the rest of the page
is printed), and app.py owns the widget half. The page is measured from
the reading area's CURRENT height, so a band taking rows, a resize, a
text-size change and fullscreen are all accounted for with no setting.
The read-from-top rule it replaces is gone, as designed: with paging,
nothing scrolls past unread, so returning the view to where the text
began would now undo the reader's own paging.

THE AMALGAM CAUGHT WHAT THE SUITE COULD NOT. The standalone embeds an
explicit module list, so the new gui.pager imported fine in the package
and was missing from build/actaea: the shipped window would have crashed
the moment a player opened it. Found by grepping the built file, not by
1555 green tests. tests/actaea/test_actaea_standalone.py now walks the
package and insists every module is carried, so the next one cannot slip
through.

DONE-TEST: tests/actaea/unit/test_pager.py, 11 tests on the arithmetic
(wrapping, the page boundary, a word longer than a line broken at the
margin, a word that moves whole, blank lines, resuming after the pause).
The wrapping was verified against tkinter itself, six cases, no
mismatch; that comparison lives in test_pager_matches_tk.py but is
OPT-IN (ACTAEA_TK_PARITY=1, run serially), because live Tk measurement
inside the parallel suite fails a different case each run and a flaky
test is worse than none. Full suite 1555 green, 6 skipped (the opt-in
parity cases). docs/06 documents the paging; the design record notes the
two deliberately separate implementations.

THEN THE WIDGET HALF GOT ITS TEST TOO. A background stability run
surfaced tests/actaea/unit/test_gui.py, which drives the real window
programmatically and which I had wrongly believed did not exist: it
failed once, in a run overlapping three other pytest processes (Tk
contention, not the change; it passes five times out of five alone).
But it WOULD have hung on a real pause, since its pump only answers
line reads. It now answers key waits the way a player would, and the
probe game recites forty lines under a picture band on purpose, so the
one GUI test the Tk-9-on-macOS one-root rule allows now covers the
whole path: the pause happens, [MORE] is on screen while it waits, any
key continues, and the marker leaves no trace.

HANDS OFF TO STEFAN, for the look rather than the mechanism: open a game
in the window, walk into a pictured room, and judge whether the [MORE]
sits where it should and reads right. Fullscreen deserves one look, since
that is where the adaptive height earns its keep.

## 2026-08-20: the window's boot, from Stefan's two screenshots
## (Actaea 1.4.1). ONE BUG, TWO SYMPTOMS, AND A METHOD CORRECTION

HIS REPORT, from playing the Rabenstein demo in the window: at boot the
status bar is up but the prompt is nowhere, and no [MORE] appears;
after RESTART everything behaves, except the [MORE] comes one line too
early, with room for two more lines below it.

MY FIRST ANSWER WAS WRONG TWICE OVER, and both are worth recording.
First, I read the status bar as a mode error; it is not. The bar
appears at the first prompt because that is what Cosmos's latch says,
so its presence PROVED the story had reached the prompt and the prompt
itself was off-screen. Second, and worse as method: I launched the
interpreter on his machine to measure it, without the art beside the
story, so there was no picture band and the whole text fit, which is
the one condition under which the bug cannot appear. A probe hung and
left a dead window on his screen for five minutes. He asked what I was
actually doing. NEW RULE, agreed: nothing gets opened on his screen
without asking first.

WHAT IT ACTUALLY WAS. His window is resized well below its saved
thirty rows, so the picture band leaves only a handful of text lines.
Tk applies a widget resize when it next goes idle, and the story
prints its entire boot (intro, banner, opening room, prompt) without
ever returning to the event loop, so at boot the window is measured as
the size it had BEFORE the band arrived. Two consequences, exactly his
two symptoms: the pager reckoned a page that did not exist and never
paused, and Tk keeps the TOP line when a Text widget shrinks, so
everything below the fold, prompt included, went out of sight and
stayed there. RESTART looked right because by then the layout had
settled.

THE FIX, three parts. The reading area's height now comes from the
arithmetic the layout itself does, right when it is computed, not from
the widget's pixel height, which lags a turn behind (measured:
update_idletasks does NOT bring it forward, still 439 pixels for a
widget just told to be six lines). The view is put back at the tail on
the idle pass that applies a resize, and again immediately before the
story waits for input, which is the moment that matters to a player.
And the page keeps ONE spare line below the marker, per his ruling, not
two.

THE TEST EARNED ITS PLACE THE HARD WAY. Written first, it passed
against the broken code twice, because the probe game booted in a few
lines and the harness flushed the layout before looking. It now boots
with an intro longer than the area, in a deliberately small window, and
inspects the view as the STORY left it. It fails against HEAD and
passes with the fix, which is the only version of that test worth
having. Full suite 1555 green.

HANDS TO STEFAN, on the rebuilt standalone: the boot with the picture,
and whether the [MORE] now sits with one spare line rather than two.

## 2026-08-20 (later): the window obeys the re-base rule it was written
## against (Actaea 1.4.2). THE SPEC HAD THE ANSWER ALL ALONG

STEFAN'S THIRD SCREENSHOT: no [MORE] at all, the boot scrolled straight
to the prompt, and the blank line the library deliberately puts under
the status bar was gone with it. Two rounds of my fixes had not touched
the actual cause.

THE CAUSE, found by reading the window's own repaint path rather than
theorising: screen changes are coalesced into ONE repaint per idle
cycle, which is right for painting (a bar paint writes eighty cells,
each signalling a change) and wrong for GEOMETRY. The story prints a
whole boot without ever returning to the event loop, so the picture
band and the status bar claimed their rows only when the story finally
waited, a dozen rows of text after they should have. Everything had
been laid out at the full window size and then shrank under itself.
Furniture that changes the reading area is now applied AT ONCE, and
only when it changes; the pixels stay deferred and coalesced.

AND THEN THE RULE THAT WAS ALREADY WRITTEN. Shrinking the area under
text nobody has read yet is exactly what docs/08 section 3 legislates
for, in Stefan's own words: THE RE-BASE NEVER EATS A LINE. Every line
on the page is unread, so if it no longer fits, it is shown from its
top, a window-full at a time behind honest [MORE]s, until the newest
lines stand bottom-anchored above the prompt; scrollback does not
substitute for that. Actaea's window did not do this. It does now, and
the same treatment covers the status bar taking its row and a window
shrunk mid-turn. The interpreter that ships as the reference now obeys
the contract the other interpreters are being written against.

MEASURED IN THE HARNESS: with a picture band and a boot longer than
what it leaves, the re-base offers the page in four pauses (17 unread
lines, 4 to a page), from the top down, ending bottom-anchored.

THE TEST TOOK FOUR TRIES TO BECOME HONEST, and that is the lesson worth
keeping from this round. Written first, it passed against the broken
code; made stricter, it passed again; given a status bar and a
scroll-off assertion, it passed a third time (the first pause happened
BEFORE the band applied, so nothing had scrolled yet). What finally
caught it was asserting that the furniture on screen matches the MODEL
whenever the story stops: the story had asked for a band before it
printed a word, so a pause with no band is a pause measured against a
screen that does not exist. Fails at the previous commit, passes now.
Full suite 1555 green.

STILL FOR STEFAN'S EYE: the boot with the picture, whether the [MORE]
now leaves one spare line rather than two, and whether the re-base
reads well in motion.

## 2026-08-20 (later still): the orphan strip (Actaea 1.4.3).
## MEASURED IN THE END, AFTER THREE ROUNDS OF GUESSING

STEFAN, after the third failed attempt: "basically NOTHING has changed",
and the fair sting with it, that every 8-bit interpreter and Actaea's
own console get this right. He was right on all counts, including
about the pace: I had been reading his screenshots for pixel counts
instead of asking the window what it believed.

SO THE WINDOW WAS MADE TO SAY. An opt-in geometry log (ACTAEA_GEOM=1,
writes ~/actaea-geom.log) records the layout arithmetic and every
pause; he booted the demo once, and the answer was in the first line:

  band=288 bar=22 margin=10 window=680 -> avail=350 rows=15 leftover=20
  [MORE]: rows=15 page=14 pager_lines=14

The pause fires after 14 lines of a 15-row area, so the app has
EXACTLY the one spare line he asked for. What made it read as two is
that the picture band is 288 pixels against a 22-pixel line: thirteen
rows and change. The remainder sat under the text as an orphan strip,
too small to hold a line, big enough to look like one, and with the
frame's own margin it came to 30 pixels of dead space below the spare
line. The console has no such strip because a terminal IS a grid of
rows, which is exactly why it never showed this.

THE FIX IS GEOMETRIC, NOT ANOTHER OFF-BY-ONE. The band now takes a
WHOLE number of text rows: the picture keeps its exact aspect inside
it and the few spare pixels sit below it in the game's own background,
which is what the band already wears. The reading area is then an
exact number of rows with nothing left over, so what the pager counts
and what the eye sees are the same thing, and one spare line means one
spare line. His question about the font size answers itself: nothing
is stored, the band's scale key already carries the cell height, so a
font change re-rounds through the same path a resize does.

For his window: the band goes 288 to 308, the reading area stays 15
rows, and the dead space below the spare line drops from 30 pixels to
the frame's 10.

DONE-TEST: the GUI test now pins the whole-row band (the picture's own
height unchanged inside it, the difference under one row) and, the
assertion that matters, that the reading area is a whole number of
rows and equals what the pager counts. Full suite 1555 green. docs/06
documents the band rounding and the geometry log.

## 2026-08-21: the Gargoyle shape, measured and made to hold
## (Actaea 1.5.3). THREE ASYNC-GEOMETRY BUGS UNDER ONE SYMPTOM

STEFAN, out of patience after the ratio rounds, brought the reference
back and two hard symptoms: switching shape filled the screen from
menu bar to dock, and a reopened window kept losing height. The shape
he wants is Gargoyle's page, which MEASURES 880 by 810: height 92
percent of width. Not 4:5, not square; a named thing, so the menu now
says Modern (Gargoyle) and the code carries the measured number.

WHAT MADE EVERY EARLIER ATTEMPT WRONG was one wrong rule and two
async-geometry bugs. The rule: the shape pinned its width at eighty
columns and clamped only the height, so on a short desktop it filled
top-to-bottom and squatted; a true aspect ratio scales BOTH sides
(floor at seventy columns, the sixty-column floor of an earlier try is
what made the picture small). The bugs, both the same trap: (1)
_reshape persisted its geometry in the same breath as requesting it,
but the window manager applies geometry asynchronously, so the
settings recorded the OLD size and every reopen came up short; persist
is debounced now, closing writes at once, and Cmd-Q on the Mac routes
through the close handler it used to bypass. (2) The fit-to-contents
snap read winfo_width() mid-boot, before the manager had applied the
aspect width, and re-asserted the stale one: the window flapped
between two widths while the pager was counting wrapped lines. The
app now remembers the width it ASKED for and never asks the widget.

AND THE ONE UNDERNEATH: the window could never be narrower than
eighty columns at all, whatever anyone requested, because a Tk Text's
DEFAULT requested width is eighty characters and a mapping toplevel
grows back to its children's natural size, overriding wm geometry
(measured: asked 894 wide, mapped at 971). The Text now requests
next to nothing and the window's geometry is the only authority.

The GUI test hunted all three down (its own two stale assertions fell
along the way: the boot no longer paginates in the taller opening
window, and the column count now FOLLOWS the width rather than
dictating it). Full suite 1555 green. docs/06 names the shape and the
rule. Versions ran 1.4.4 to 1.5.3 through the evening; none of it
pushed yet, Stefan looks first.

ADDENDUM, same night: STEFAN WAS RIGHT ABOUT THE DOCK, and about the
shape. Measured from his two fresh screenshots, the window really was
wider than tall (0.91 with the dock, 0.99 without): my "measured
Gargoyle" ratio of 0.92 had encoded a CLAMPED reference crop, not the
portrait he meant. The truth underneath is an impossible triangle:
portrait at eighty columns needs some 1250 points of height and his
laptop has about 900 usable, so portrait + eighty columns + that
screen cannot coexist. Modern is now what he asked for on day one,
PORTRAIT 4:5, scaling down to the seventy-column floor, where the
width holds and the height takes everything the desktop offers, with
the room asked from wm_maxsize so the dock is part of the arithmetic
instead of a surprise. On his laptop that opens 860x887, seventy
columns, taller than wide at last; on a tall display it is the true
4:5 page. (Actaea 1.5.4)

## 2026-08-21 (night): ACTAEA 2.0 CHARTERED, and the fonts settled.
## All rulings Stefan's, no code yet

WHAT 2.0 IS, in his framing: a new modern look, a better typeface,
selectable stored aspect ratios, and native dressing so Actaea presents
as a real app on Mac, Linux and Windows, icon and all, never again as
"Python" in the menu bar. He made the icon himself while watching the
window rounds: a golden star. The build order is chartered in the task
list (A2.0-1 to A2.0-6): measured pager first (paging by Tk
measurement, the prerequisite for everything), then proportional
prose with the fixed-pitch obligations, the embedded fonts with
first-run registration, the dressing with a polished About dialog
linking the bundled font licenses.

THE FONT ROUND, settled tonight from staged specimen cards: NO free
font choices; three coherent LOOKS. "Novel", the default: Noto Serif
prose over Roboto Mono. "Clean": Roboto over Roboto Mono. "Retro":
monogram (datagoblin), ONE face for everything the way a real 8-bit
machine was, unsmoothed, on its pixel grid of eights, default size
step 24 (matches Novel's 14, his eye, the metrics agreed). Both
non-retro looks share Roboto Mono, so the machine voice is constant
and only the story voice changes. Rejected on the way: Pixeloid (the
lowercase i reads as a capital), Geist Pixel (and any split-face
retro). Licenses verified at source, every one: OFL for the Noto and
Roboto faces, CC0 for monogram. Attribution goes in the licenses
document regardless.

A method lesson paid for twice tonight: specimens must be judged
INSIDE one image, never across Preview windows (fit-to-window zoom
lies), and never through a resampler; the mushy first cards and the
false size alarm both came from my pipeline, not the fonts.

STATE AT LIGHTS OUT: the whole 1.4.x-1.5.x window evening plus this
charter is committed but UNPUSHED, waiting on Stefan's eye for the
portrait window and dock behavior. The 2.0 build starts on his
explicit go, at the measured pager.

## CHECKPOINT for pickup (2026-08-21 evening): Actaea 2.0 in flight,
## dressing next, NOTHING pushed until 2.0 ships whole

STANDING STATE. Branch main, everything from Actaea 1.7.0 onward is
LOCAL ONLY by Stefan's ruling: no push to origin until version 2.0 is
complete, it ships as one release, never bits and pieces. Origin stands
at 323387d (Actaea 1.6.0, the measured pager). Local versions: arcc
1.13.0, Cosmos 1.16.3, Actaea 1.9.4, arcimg 2.0.0. Full suite 1544
green (one pytest run, needs a real TTY). The 2.0 work is chartered in
the harness task list as A2.0-1 to A2.0-6; done: typeface rulings,
measured pager, proportional looks, font embed; open: A2.0-5 the native
dressing (Stefan has thoughts to give FIRST, ask before building) and
A2.0-6 the release round.

WHAT 2.0 HOLDS SO FAR, all rulings Stefan's. THREE LOOKS, no free font
choices: Novel (default) = Noto Serif prose + Roboto Mono machine
voice; Clean = Roboto + Roboto Mono; Retro = monogram for EVERYTHING,
one face like a real 8-bit machine, sizes snapped to its grid of
eights, default step 24 for base 14 (he verified 24 matches Noto 14 by
eye and by x-height both), plus a DRAWN bold cut we generated ourselves
(tools/monogram_bold.py, pixel-domain: rasterize on the 64-unit grid,
OR with a one-pixel shift, trace back; counter-preserving so the m
keeps its daylight; own family "monogram bold" because the CoreText
matcher mis-serves cuts sharing a family). Optical factors: NONE for
the Robotos (neutral 1.00, his ruling after the geometry hunt), ratio
only for Retro. The prompt and [MORE] speak the PROSE face (one voice
on the page); the status bar is the deliberate mono exception; FIXED
style and the Flags 2 bit stay mono per the Standard. Fonts: 14 TTFs,
all OFL except monogram (CC0, verified at the itch page), licenses in
actaea/gui/fonts/LICENSES.md, embedded in build/actaea (4.0MB) via a
generated gui.fontdata module, unpacked once to XDG data on first run.

THE APP SHAPE: File > Open (Cmd+O) switches stories mid-session in the
same window; menus restructured to File / Visuals (Typeface, Text
Size, Window Shape, Screen Height, Game Colours) / Settings (On
Launch: ask for a story, or reopen the last). A bare launch resolves
its own story (dialog or last-played); every terminal-facing mode
still requires the story argument. Window shapes: Modern 4:5 portrait
scaling to a 70-column floor with the room asked from wm_maxsize
(dock included), Classic 4:3.

THE BUG WAR, because the record matters. The boot-race family is dead
in three doors: the fit-to-contents snap never trusts an unmapped
window (Stefan's ACTAEA_GEOM log convicted it: window=200 at first
layout, snapped to 181, locked); persist and restore both refuse
absurd geometries (his settings had been poisoned with 200x195 and
every launch restored the accident); and run() now waits for the map
so the first screen is stamped with the real column count (the H2 bar
adrift of the prose edge). The amalgam loader never set __file__, so
every STANDALONE window launch since the looks had died on a NameError
in fonts.py, which was Stefan's "it doesn't let me test". And the
day-one status bar squeeze fell to the SPACE-COLLAPSE DISCOVERY: the
compiler collapses interior space runs in string literals, so Cosmos's
three-space gap never survived compilation; all three packs now place
the bar's right block by cursor arithmetic, flush to the last column
(Cosmos 1.16.3). DESIGN FLAG for Stefan, unruled: whether single-line
literals should preserve space runs is a real language question now.

METHOD RULINGS EARNED THE HARD WAY, binding: never open a window on
Stefan's screen without asking; specimens and comparisons live in ONE
image (Preview zoom lies across windows); his launches share the tree
I edit, so tell him "tree is quiet" when handing over; a fix that
cannot show a failing-then-passing test has proven nothing; edits
must assert their own match (two replaces no-opped silently and
printed success this session).

NEXT: Stefan speaks first on the dressing (A2.0-5: his golden star
icon, Actaea.app bundle so the menu bar stops saying Python, .desktop
and ico, file associations, the polished About linking the font
licenses). Then the release round (A2.0-6): PROGRESS charter entry,
docs/06 full pass, version 2.0.0, amalgams, and the one push that
ships everything.

## The star goes on (2026-08-21): Actaea presents as itself, not as
## Python (Actaea 1.10.0, toward 2.0, still unpushed)

STEFAN'S RULINGS, given before a line was written. The installer is
explicit, never automatic: `actaea --install-app`, his approval of the
flag name. The stub goes among the applications while THE CORE STAYS
WHERE IT WAS DOWNLOADED, kept together with arcc and the other Arcturus
files so that `arcc --update` keeps every tool current; the install
prints exactly that sentence. Linux and Windows are considered, not
promised and forgotten. The star is his own artwork (artworks/
actaea.jpeg).

THE PROBE CAME FIRST. The whole design stood on an undocumented
technique, so before building, probes/macdress_probe.py rewrote
CFBundleName in the hosting bundle's in-memory dictionary via pure
ctypes/objc and opened a window: Stefan read "Actaea" in his menu bar.
Only then was the strategy locked: the amalgam DRESSES ITS OWN PROCESS
at every window launch (menu bar name and Dock star on macOS, taskbar
identity on Windows, window icon everywhere), so the terminal life
developers actually live looks native with no bundle involved; the
.app stub is optional dressing holding ZERO logic, three shell lines
that exec the real interpreter, so it can never go stale against
updates. If the download directory moves, the next hand launch heals
the stub; a stub pointing at a LIVE core is never touched (a second
copy must not hijack the installed one), and the shim falls back to
the PATH's python3 when a Homebrew upgrade retires the recorded
interpreter's path.

WHAT LANDED: actaea/gui/dress.py (identity, icons, installers, all of
it unable to raise: an undressed session still plays); the icon set
cut from the star by tools/actaea_icon.py (macOS icns masked into the
native rounded rectangle on Apple's own grid, PROPOSED convention
awaiting Stefan's Dock verdict; Windows ico and Linux png keep the
full square); double-clicked and Dock-dropped stories arriving through
Tk's ::tk::mac::OpenDocument into the same mid-session switch File >
Open uses, with a short grace at bundle launches so the Apple Event
beats the open dialog; the About panel wearing the star with the
bundled typefaces' license record one click away; the icons embedded
in the standalone beside the fonts (build/actaea now 7.6MB, the
full-resolution icns is most of the growth, flagged for Stefan). The
GUI test now walks the Apple Event door; six new dressing tests cover
the icons by magic number, the logic-free bundle, the
heal-only-dead-cores rule, and the Linux entry. Actaea unit suite 133
green; the standalone's install path smoke-tested end to end against
a temp directory.

NEXT: Stefan's live verdict (menu bar, Dock star, a real
--install-app, a double-clicked story), then the release round
(A2.0-6).

## The revert (2026-08-21, late): the status line belongs to Stefan's
## design, and the library was never mine to change (Cosmos 1.16.4)

STEFAN'S RULING, in anger and in the right. The status bar's right
block ending two to three columns short of the screen edge is THE
DESIGN, proven by every shipped interpreter rendering the same build:
Gargoyle, Canopus, Proteus, Haumea, and Actaea's own console all show
that breathing gap, and he provided the screenshots. Yesterday's
"flush to the edge" change (Cosmos 1.16.3) replaced his design with my
theory, in the library, against evidence he had explicitly given: the
console painted the bar right, so the fault could only be Actaea's
window, and the ask was to fix ACTAEA. Cosmos 1.16.4 restores all
three language packs and the size ceilings exactly to their 1.16.2
state; the arcc amalgam, the arc_image example builds, and the local
H2 build are regenerated with it. Probed after the revert: the
Rabenstein demo ends at column 123 of 125, H2 at 122 of 125, the gap
back at every window width, GUI included.

WHAT THE ORIGINAL SYMPTOM ACTUALLY WAS, best supported reading: the
"far off from the right side" screenshot came from a window whose
boot had stamped 80 columns into a wider window (the boot race), a
bug already killed in Actaea 1.9.4; his amalgam only received that
fix at the 18:10 regeneration, after the screenshot. The library was
innocent all along.

THE LESSON, binding and written to memory: when the evidence
localizes a fault to one front-end, the fix lives in that front-end;
the library is shared truth across every interpreter and changing its
behavior requires Stefan's explicit consent, every time. Reproduce on
the exact artifact before theorizing (the stale hibernated2.z5 and
the pre-fix screenshots cost this evening two false convictions).

ALSO THIS ROUND: the About star at 320 (Stefan's pick from the size
sheet); the Dock hover name probed to the end of the road: the
LaunchServices setter resolves, gets a valid ASN, and returns
accepted, yet the tile keeps the old label, so one post-map repeat
was added as the last arrow and beyond that it is what it is (the
.app stub always names it right); barflush_probe.py records what the
edge fill hides.

## Round three finds it (2026-08-21, night): the bar was adrift in
## PIXELS, not in cells, and it was Actaea's alone all along

Stefan: "Nothing has changed. You are simply incapable of doing it,
right?" The model probes kept swearing the bar was placed right, and
his screen kept showing it adrift, and both were true: the upper
window drew each style run as ONE canvas text item, which advances by
the font's true FRACTIONAL glyph widths, while every cell computation
uses the integer cell_w. Measured in his own settings' window: cell_w
11, true advance about 10.21, drift 55px over 70 columns, exactly
five cells, the right block landing five cells left of where the
model has it, on top of the design's own gap of three. The console
never shows it because a terminal has hard cells. This is the
Actaea-only fault the console-vs-GUI evidence pointed at from the
first screenshot; every earlier theory (space collapse, stale builds,
boot races) was either a side-story or a false conviction.

THE FIX, in the window and nowhere else: every glyph is pinned to its
own cell's x (per-character create_text in _redraw_grid). Probed
after: the last glyph's item ends within bbox padding of the model's
last inked column. The GUI test now asserts every row-1 text item
anchors on a cell boundary and the rightmost sits exactly at the
model's last inked cell.

VERIFIED BY STEFAN'S EYE (2026-08-21, night): "Yes, that's it.
finally." The bar stands with its design gap in the window, matching
every other interpreter. The stub launches from Applications, the Dock
shows the star and, from the bundle, the name; the terminal launch
keeping "Python" on hover is accepted as the platform's own boundary.
A2.0-5 closes; the release round (A2.0-6) is what remains of 2.0.

## RELEASE: Actaea 2.0.0 (2026-08-22), the reference interpreter
## becomes a native application, shipped whole

Stefan's ship ruling, held to the letter: nothing since Actaea 1.6.0
was pushed until 2.0 stood complete; this release is that one push,
everything at once, no bits and pieces along the way.

WHAT 2.0 IS, every visual ruling his. Three typographic looks and no
free font choices: Novel (Noto Serif over Roboto Mono, the default),
Clean (Roboto over the same mono), Retro (monogram for everything,
one face like a real 8-bit machine, with the bold cut we drew
ourselves in the pixel domain because no true cut exists). One Text
Size drives all looks. The measured [MORE] pager; whole text rows
always; Modern (4:5) portrait and Classic (4:3) shapes, his call on
both the ratio and the names. His golden star artwork became the icns
(the native rounded rectangle), the ico, and the window icon; the
process presents as Actaea, not Python, at every launch. The
--install-app strategy is his design: the stub goes among the
applications on explicit request only, holds zero logic, and prints
that the core stays where it was downloaded, kept together with the
other Arcturus tools for arcc --update. The About wears the star at
320 points, his pick from the size sheet. On Launch (ask or last),
File > Open mid-session, double-clicked stories through the Apple
Event door, dialogs centered where a person looks.

THE HARD LESSON OF THE ROUND, in the record because it matters: his
console-versus-window evidence said from the first screenshot that
the status bar fault was Actaea's alone, and I overrode that evidence
and changed the library without consent. The library was right; it
was reverted whole (Cosmos 1.16.4 restores the 1.16.2 placement, the
breathing gap that is the design), and the true fault was found by
measurement where he pointed: the canvas drew rows by the font's
fractional advances while the grid reckons integer cells, five cells
of drift across seventy columns. Every glyph is pinned to its cell
now. His verdict: "Yes, that's it. finally."

Versions shipped: Actaea 2.0.0, Cosmos 1.16.4, arcc 1.13.0 (both
standalones regenerated and committed; README table refreshed;
docs/06 carries the full 2.0 surface and his window screenshot).

## Pour is not a synonym of fill, and the grammar learns to say so
## (Cosmos 1.16.5, `reverse` on prepositional lines)

Found by Stefan's own quality pass: checking the Hibernated 2
invisiclues against the game showed POUR CONTAINER INTO TANK refused
where the hint promised it, and he pushed past every shallow answer
(the Inform original refused it too; the granule declared pour a plain
synonym) to the real defect: "fill X with Y" fills X but "pour X into
Y" fills Y, and a shared verb declaration hands every game the wrong
roles for the pour phrasing, so the object written to accept the pair
is never asked.

HIS RULING SHAPED THE FIX, after my false start (a pour_into
dispatcher verb, implemented without his go, guard-less, and breaking
the selective summon: reverted whole, and the lesson recorded). The
design he confirmed: `reverse`, the grammar's existing word for
swapped roles, extended from the adjacent dative (give noun noun
reverse) to prepositional lines. The granule now declares pour and
spill as their own verb whose lines name the SAME fill action, the
prepositional one marked reverse: same family, so a selective summon
naming fill keeps them; same guarded default; an object's ordinary on
fill serves both phrasings unaware.

The mechanics: summary-byte bit 5, decoded behind the any_swap fold;
the two_swap slot rides the tail globals so no number moves; the
packs swap the bound slots reusing a spent local, because a let costs
its slot even inside a folded branch. Byte-identity held the hard
way: the first build differed by ONE byte (a routine's local count),
and the reuse closed it, proven by compiling Cloak of Darkness on
both compilers and comparing bytes. Hibernated 2 needed zero changes:
POUR CANISTER INTO TANK now answers "You pour the viscous blue
fluid..." through the reservoir's own handler, and the invisiclues
sentence stands as written. Suite 1554 green; the extended-verbs
example repriced +44, the only games that pay.
