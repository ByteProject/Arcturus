# Arcturus Code Generation Mapping

Status: in progress, produced as the backend is built (roadmap document 04).
This document records how Arcturus constructs lower to Z-machine version 5. It
grows milestone by milestone; this revision covers the B3 minimum viable
backend (banner, print, quit).

The authoritative language and runtime definitions are Parts I and II of the
Arcturus Handbook (docs/01); this document is the construct-to-opcode
reference the backend implements.

## 1. Text

Text is encoded as Z-strings: 5-bit Z-characters packed three to a 16-bit word,
the top bit of the final word marking the end (standard 1.1, section 3). Three
alphabets carry the characters (A0 lowercase, A1 uppercase, A2 punctuation);
in version 5 the shift characters 4 and 5 shift the next single character into
A1 and A2. A character in no alphabet is written with the A2 escape (Z-char 6)
and its 10-bit ZSCII value. Implemented in `arcturus/zstring.py`. Abbreviation
compression (Z-chars 1 to 3) is a size-pass lever (B5) and is not yet emitted.

## 2. Story-file layout

A version 5 story file is a 64-byte header followed by three regions, built by
`arcturus/storyfile.py`:

- dynamic memory (writable): the global variables table and the object table;
- static memory (read-only): the abbreviations table and the dictionary;
- high memory: the code, run from the initial program counter.

Header fields the backend sets (standard 1.1, section 11):

| Offset | Field | B3 value |
|--------|-------|----------|
| 0x00 | version | 5 |
| 0x02 | release number | from `game release`, default 1 |
| 0x04 | high memory base | start of code |
| 0x06 | initial program counter | start of code (a byte address in v5) |
| 0x08 | dictionary | an empty dictionary |
| 0x0A | object table | property defaults table (no objects yet) |
| 0x0C | global variables | 240-entry table |
| 0x0E | static memory base | end of the object table |
| 0x12 | serial number | from `game serial`, else the build date (YYMMDD) |
| 0x18 | abbreviations table | empty |
| 0x1A | file length | real length / 4 (the v5 scale) |
| 0x1C | checksum | sum of bytes 0x40 to end, modulo 65536 |

The MVP touches no objects, so the object table is only the 63-word property
defaults table; objects and a populated dictionary arrive with Cosmos (B4).

## 3. The MVP main routine

The smallest program has no routine calls and no expressions, so the code is a
single straight-line instruction stream at the initial program counter. In
version 5 the initial PC is a byte address pointing at the first opcode, with no
routine header, so no packed addresses or alignment are involved.

0OP opcodes used (standard 1.1, section 14):

| Opcode | Byte | Use |
|--------|------|-----|
| print | 0xB2 | print the inline literal Z-string that follows |
| new_line | 0xBB | print a newline |
| quit | 0xBA | end the program |

## 4. Construct mapping (B3 subset)

| Construct | Lowering |
|-----------|----------|
| the startup banner | `print` of title, headline-by-author, and the release / serial / `Arcturus <version>` line; provisional, moves into Cosmos at B4 |
| `say "literal text"` (in `on start`) | `print` of the encoded string, then `new_line` |
| end of `on start` | `quit` |

The banner is emitted by the compiler as a stand-in. From B4 the banner is
Cosmos's responsibility (docs/01 chapter 2), where the library contributes its
own name and version; the compiler continues to hardcode nothing about Cosmos.

## 5. Routines and the value model (B4.1, B4.2)

Routines have a v5 header (one byte of local count, no initial values) and are
reached by packed address (byte address / 4), so each is 4-aligned. The entry
stub at the initial PC calls the main routine and quits. The assembler
(`arcturus/assembler.py`) encodes all instruction forms and the linker
backpatches call targets, branches, and jumps.

Expression lowering (`arcturus/lower.py`) is stack-based and right-first: an
expression evaluates onto the stack and a computing opcode stores its result
where asked. Binary operands are pushed right-first so the opcode reads them in
source order; a temporary preserves source order only when an operand contains
a block call. Conditions branch directly, with short-circuit `and`/`or` and
`not` folded into branch targets, never materializing a boolean.

| Construct | Lowering |
|-----------|----------|
| `+ - * / mod` | `add` / `sub` / `mul` / `div` / `mod` |
| `< > <= >=` | `jl` / `jg` (with negation for `<=` / `>=`) |
| `is` / `is not` (equality) | `je` |
| `let`, `change` to local/global | `store` / `push` into the variable |
| number `say` | `print_num` |
| `if` / `else`, `while`, number `switch` | labels, `jz`/`je`/`jl`/`jg`, `jump` |
| `return`, `finish` | `ret` / `rfalse`, `quit` |
| block call | `call_vs` / `call_vn` |

## 6. The object table (B4.3)

The object table (`arcturus/objects.py`) carries the property defaults, the
object entries (48 attribute bits, the parent/sibling/child tree, a
property-table pointer), and each object's property table (the Z-encoded short
name from `name`, then slot properties in descending number). Boolean
properties become attributes; `desc` holds a packed string address backpatched
once high memory is laid out.

| Construct | Lowering |
|-----------|----------|
| an object name as a value | its object-number constant |
| `now x is attr` / `is not` | `set_attr` / `clear_attr` |
| `x is attr` (property test) | `test_attr` |
| `x.prop` read | `get_prop` |
| `change x.prop to v` | `put_prop` |
| `move x to y` / `to nothing` | `insert_obj` / `remove_obj` |
| `x holds y`, `y in x` | `jin` |
| `say` an object, `${the obj}` | `print_obj` (article printed literally for now) |
| `say` a text property | `print_paddr` |

### 6a. Kinds and the attribute budget

A kind is compile-time sugar; the Z-machine has no class concept. The only
place a kind needs a run-time identity is `obj is <kind>`, which reads a
per-object attribute bit (an instance carries the attribute of every kind in
its chain). Spanning, handler-sharing, property inheritance, and `of <kind>`
declaration are all resolved in the compiler and need no attribute. So the 48
attribute bits are allocated in strict priority, in `objects.build_layout`:

1. Genuine object attributes (boolean properties) first: these are mutable
   per-object state and have no other home, so they own the budget.
2. Membership-tested kinds next, busiest first. `sema` counts every `obj is
   <kind>` site into `world.kind_tests`; only kinds that appear there are given
   a slot, and only while slots remain. An untested kind costs nothing.
3. The overflow tested kinds SPILL. Each spilled kind gets a synthesized extent
   catalog in the catalog region (`layout.kind_catalog[name]`): the object
   numbers of its transitive instances, in the same `[count, widest=0, e1..eN]`
   shape as an author catalog. `obj is <spilled_kind>` then lowers to a
   `blk_position` membership scan of that catalog (`_kind_test` in `lower.py`),
   identical in result to `test_attr`, paid only on the cold tail. Because the
   catalog region lives in dynamic memory it is resident on paging interpreters
   (Ozmoo), so the scan never triggers a disk read.

The only hard ceiling is therefore 48 genuine attributes; the error names them,
never kinds. `arcc -s` reports `attributes N/48, kinds M (K spilled to
catalogs)` from `stats["attributes"]` (real attributes only), `kinds_backed`,
and `kinds_spilled`, so an author reads the true budget at a glance.

## 7. The dictionary and input (B4.4)

The dictionary (`arcturus/dictionary.py`) holds every matchable word - verb
words (multi-word phrases split into tokens), object `words`, and grain words -
as 6-byte Z-encoded entries truncated to nine Z-characters, sorted so the
interpreter's tokenizer can binary-search, with three data bytes per entry
reserved for the parser. The compiler provides the low-level intrinsics the
parser sits on: `aread` reads a line into the text buffer and tokenizes it into
the parse buffer against the dictionary, and `loadb`/`storeb`/`loadw`/`storew`
read and write memory. The text and parse buffers sit at fixed dynamic-memory
addresses just after the globals (`TEXT_BUFFER_ADDR`, `PARSE_BUFFER_ADDR`).

A verb whose grammar needs the positional matcher (docs/01 chapter 14;
`worldmodel.needs_table`) is flagged as a TABLED verb, and its data bytes hold
the address of its grammar table instead of an action and an arity. The tables
sit in static memory with the grain chains, right before the dictionary: per
line an action byte, one byte per token (a literal word token carries its
dictionary address, backpatched after the dictionary is placed, the same
word-fixup recipe the object table uses), a zero closing each line and a zero
in action position closing the table. Lines are emitted in matcher order
(`worldmodel.table_line_order`). A game with no tabled verb emits no table,
and the matcher folds away behind `any_tables`.

## 8. Conversation topics (B5)

A person with `topic` declarations carries a `topics` property holding the
address of a runtime topic table (`arcturus/objects.py`). The table is a count
word followed by one fixed `TOPIC_REC`-byte record per topic, then the
per-topic match-word sub-arrays. Each record holds the packed address of the
topic's body routine and (if any) its `when`-guard routine, the packed address
of its menu label string, a pointer to its match-word sub-array, a static flags
byte (`once`, initial `hidden`), and a mutable live-state byte (`retired`,
`hidden` now). The table lives in dynamic memory, so `reveal`/`hide` can flip a
topic's visibility at run time. All four address kinds are filled by the same
backpatch machinery the rest of the object table uses (routine, string, word,
and object-relative pointer fixups).

| Construct | Lowering |
|-----------|----------|
| a `topic` body | a `topic_<obj>_<i>` routine, `self` = the person |
| a topic `when <cond>` | a `topicwhen_<obj>_<i>` guard returning 1/0 |
| `you "..."` | `call` `line_you`, the text, then `line_end` |
| `reply "..."` | `call` `line_reply(self)`, the text, then `line_end` |
| `reveal <id>` / `hide <id>` | clear / set the `hidden` bit in sibling `<id>`'s state byte (the index is resolved at compile time) |

The compiler owns only the line's structure: open framing, the text (with
interpolation), close framing. The wording - the speaker label, the separator,
and the quotation marks - lives in the Cosmos blocks `line_you`, `line_reply`,
and `line_end`, so a story can restyle it and a language pack can translate it.
It deliberately is not in the conversations granule, because the ask/tell path
uses these lines and runs with that granule absent.

The conversation granules never touch this byte layout: they call the
`cosmos_topic_*` backing routines (`arcturus/codegen.py`) through the
`topics_count` / `topic_visible` / `topic_label` / `topic_matches` /
`topic_run` intrinsics. The menu granule also uses `read_key` (the `read_char`
VAR opcode, first operand 1) to read a single keypress for press-a-number
selection. Those helpers ship only when one is referenced, so a
game with topics but no conversation granule carries the table and bodies but
none of the walking machinery; the body and guard routines are always emitted
when topics exist, because the table references them.

## 9. Dead-code elimination (B6)

The library is compiled in full, but a given game reaches only a fraction of it,
so codegen runs a whole-program reachability sweep over the routine call graph
and drops every routine the running story can never enter (`codegen.
_prune_unreachable`, the first size lever of docs/00 section 5).

The sweep marks from a set of roots, following only `call` fixups (the static
"this routine calls that one" edges left by `RoutineRef` operands). The catch is
that not every live routine is reached by a call: the dispatcher invokes a
handler INDIRECTLY, reading a react or topic routine's packed address out of the
object table (objects.py `routine_fixups`) and calling it by address with the
`call_handler` intrinsic, an edge no scan of the code can see. So the roots are
the entry stub PLUS every routine the data names: each `react_<obj>`, every topic
body `topic_<obj>_<i>`, and every `when`-guard `topicwhen_<obj>_<i>`. From there
the mark is transitive, so `react_free`, `grain_dispatch`, the `grain<i>`
routines, and the `cosmos_*` helpers stay live exactly when something on a
reachable path calls them (through the `run_free` / `run_grain` / topic
intrinsics, which lower to ordinary `RoutineRef` calls).

What stays unmarked is compiled in but never run, and in a typical game that is
most of Cosmos: the message and verb-default blocks the story never triggers, the
`you`/`reply`/`line_end` conversation framing when no topic runs, and the
statusline and conversation seams (`status_bar`, `status_lines`, `ask_to`,
`tell_to`) when neither granule is summoned. Dropping it is sound because a kept routine's call
targets are themselves kept (they were followed) and its data references are roots
(always kept), so the linker never dangles. The standard verb set is deliberately
NOT reclaimed: each standard verb default is a free rule reached through
`react_free`, so JUMP or LISTEN works in every game whether or not the author
wrote a handler, and that is the always-present baseline the PunyInform size
comparison is measured against.

## 10. Abbreviation text compression (B6)

Most of a story file is text, so the encoder packs strings against the Z-machine's
96-entry abbreviation table (the second size lever, docs/00 section 5). An
abbreviation reference is two Z-characters, a bank shift (1, 2, or 3) then an index
0..31, so the three banks address abbreviations 0..95, matching the table the
header points at (storyfile.H_ABBREV). At encode time `zstring.encode` walks each
string left to right and, where the longest installed abbreviation is a prefix of
what remains, emits the reference instead of the literal Z-chars; otherwise it
emits the literal. The abbreviation strings themselves, and dictionary words, are
encoded literally (the standard forbids a reference inside an abbreviation).

The active set is module state, installed once per compile (`zstring.
set_abbreviations`), because text is encoded from several places: the assembler
packs inline `print` text as routines are built, and `build_story` packs the
object descriptions and the pooled strings. `generate` installs the set before any
of that and resets it afterward, so the driven backend tests, which never install
one, encode literally exactly as before. `build_story` then lays the table out at
the start of static memory: the 96 words first, each abbreviation string just after
(encoded literally), and each table word pointing at its string's word address
(byte address / 2); unused entries share one empty string.

Which substrings to abbreviate is chosen two ways (`arcturus/abbrev.py`). The
baked-in DEFAULT_ABBREVS is a fixed set used on every build with no extra step; it
is regenerated by `tools/arcabbr.py`, which compiles a representative standard-only
corpus (`tools/corpus.storyarc`), harvests the text the compiler would encode, and
runs the optimizer. Because every standard verb handler is always live, the
library's whole message set is harvested from any game, and that always-present
text is what the default compresses; it tops out near fifty abbreviations, which is
about as many profitable substrings as the library text contains. Filling more of
the 96 slots only pays for a specific game's own prose, which is the job of the
slow, opt-in `--make-abbreviations` pass: it pools the story's and its summoned
granules' strings, runs the same optimizer to the full 96, and writes an
`abbreviations.granule` beside the story (Arcturus-lexable string data, not runtime
code). A story summons that file by name, and `cosmos.combined_program` intercepts
it, extracts its strings, and hands them to codegen as the encoder's set in place
of the default (`world.abbreviations`). The optimizer itself is a greedy heuristic:
it repeatedly takes the substring whose references would save the most bytes and
blanks its occurrences so the next round re-scores against what is left, until the
table is full or nothing else pays.

The baked default is tuned to the English library, so it applies only to an
English game. A game that selects another language (`summon.language "spanish"`)
gets no default set: English abbreviations barely match Spanish text, so applying
them would just cost the abbreviation strings for almost no compression, a small
net loss (`codegen._abbreviations_for` returns an empty set for a non-default
language). Cosmos deliberately does not bake a standard set per language; a
foreign-language game runs `--make-abbreviations`, which harvests through
`combined_program` and so sees the selected language's translated text, producing
a set tuned to that language (on the Spanish example, about 700 bytes below the
no-abbreviation size). Small games gain little from abbreviations either way;
large ones want their own tuned set regardless of language.

## 11. Dense code generation (B6)

The third size lever (docs/00 section 5) tightens the emitted code, through one
emit-point peephole, the relaxation pass, and a lowering-level dead-code pass.

At the emit point, a `ret 0` / `ret 1` (the two-byte 1OP form) is written as the
one-byte `rfalse` / `rtrue`. Every handler, react routine, and helper ends on a
"return 0/1", so this alone is the single largest saving.

The relaxation pass (`assembler.Routine.relax`) settles each routine's intra-
routine control flow. Branch and jump offsets are PC-relative within a routine, so
the pass runs per routine before the linker places it: it sizes every branch and
jump, resolves their offsets, rewrites the code to its final length, and hands the
linker only the inter-routine call and string-reference fixups, repositioned. It
applies three peepholes:

- Short-form branches: a forward branch whose offset fits 2 to 63 takes the one-
  byte form instead of the two-byte wide form.
- Branch-to-return: a branch whose target is a bare `rfalse` / `rtrue` returns
  directly through the short-form offset 0 / 1, never reaching the label.
- One-byte jumps: a forward jump whose offset fits 2 to 255 uses the one-byte
  small-constant operand (opcode 0x9C) instead of the two-byte form (0x8C).

Sizing is a fixpoint: shortening one element pulls every element that spans it one
byte closer to its target, which can bring another into range, so the pass shrinks
what fits and repeats until nothing changes. Shrinking only ever shortens
distances, and a forward offset bottoms out at its short-form minimum of 2, so it
never drops into the 0/1 range the machine reads as "return", and it converges.

The dead-code pass is in the lowering. `compile_block` reports whether a statement
list unconditionally terminates (every path returns, stops, finishes, or
continues, including an if/else all of whose clauses do); it stops emitting at the
first terminator, since the rest is unreachable, `_if` skips the jump-to-end after
a clause that already returned, and codegen omits the default return it would
otherwise append to a body that already returns.

Together these reclaim around 1.2K from each example game.

A fourth, whole-feature lever is static-`if` folding. `_if` decides a clause whose
condition is a compile-time constant at compile time: a statically-false clause
emits nothing, a statically-true one is taken unconditionally and later clauses
are dropped. Cosmos uses this to make optional features pay-for-use. A feature's
code is guarded on a compile-time flag intrinsic, `any_spans()` (1 when any object
declares `spans`) or `any_doors()` (1 when any object is a door), which folds to a
constant; in a game that does not use the feature, the guard folds to false, the
feature's calls vanish, and whole-program dead-code elimination reclaims the now-
uncalled blocks. So the multi-room scope walk and the two-sided-door movement
detour cost nothing in a game without spans or doors.

## 12. Not yet lowered

Deferred to later milestones: the `a`/`an` choice by sound, kind-level grains and
topics (they need per-instance scope), and `on go other`.

Computed (`block`-valued) properties are lowered for text: the property slot holds
the block routine's packed address, and a read lowers to "print or run": compare
the stored address against the first string's packed address (the `__strings__`
global), print it as a string when at or above that line, else call it as the
block routine, which says its own text.

A general computed value property (a number decided at run time) stays a compile
error, since that read cannot tell an arbitrary value from a routine address. The
one exception is a **computed exit** (docs/01 chapter 8): a direction property
that is a block. Its value is a room OBJECT NUMBER, always small, so it never
collides with the block routine's large packed address. The exit read is
`exit_dest`, which mirrors "print or run" as "read or run": it compares the stored
value against the LOWEST routine packed address (the `__routines__` global,
pre-biased +0x8000 like `__strings__`) and calls it as a block when at or above
that line, else uses it as the destination. `exit_dest` folds to a plain
`get_prop` when the program has no computed exit, so a static-exit game is
byte-identical, and `__routines__` claims a fixed global slot only. Cosmos reads
every exit through `exit_dest`, in the go handler and the `verbose_exits` scan.

## The word-to-owners index

Noun resolution is the hottest code an 8-bit interpreter runs, and the
compiler knows at build time which objects own which words. The story file
therefore carries an index, emitted after the dictionary's side tables:

- For every distinct DICTIONARY ENTRY that any object's vocabulary reaches
  (its `words`, its `plural` group words, its `>`-marked adjectives), a
  chain of the owning objects' numbers, two bytes each, zero-terminated.
  The key is the entry's address, never the spelling: words sharing a
  nine-z-char prefix collapse to one entry (extinguish / extinguisher),
  and their owners union into one chain, because the matcher looks up by
  the address the tokenizer produced.
- Then the index proper: a count, then (word dictionary address, chain
  address) pairs, sorted by address for the matcher's binary search. The
  `__owners__` global holds the index address.

The pairs are harvested at the property emitter itself, the same loop that
writes each object's vocabulary properties, so the index can never drift
from what the live `has_word` family can answer. The invariant that keeps
it safe: THE INDEX ONLY PROPOSES CANDIDATES; `phrase_score` still decides.
Over-proposal costs a few instructions; only a missing candidate would be
a bug, and the emitter's coverage equals the emitted properties by
construction. Dynamic vocabulary does not exist in the language (add and
remove on word-list properties are refused at compile time); if that door
ever opens, a loose-object side list must ship in the same change, holding
every object whose vocabulary a running game can extend, swept classically
per phrase.

At run time the matcher walks each typed word's chain instead of the
object table, visiting every candidate exactly once (an object in two
chains is skipped on the later word when any earlier typed word already
owns it, the `owns_word` mirror of the index), and one shared block
(`consider_obj`, writing the m_* globals) holds the scoring and tie rules
for both this and the classic sweep, which stays in the source as the
readable spec. The internal ARCC_CLASSIC_MATCH environment escape compiles
the classic sweep instead, and the conformance tests play the two matchers
against each other on identical seeded scripts.

Measured on Hibernated 2's opening ten commands (the Varuna cycle
evaluation's session, probes/zi_count.py): the session fell from 53,385
executed z-instructions to 20,110, the worst verb turn from 10,272 to
1,733, with verb turns landing below the movement turns. The price is the
index itself: a few hundred bytes on an example-sized game, 2.9K on
Hibernated 2.

<!-- intrinsics:begin -->

## Appendix: the intrinsic reference

Every intrinsic the compiler exposes, with the line its own dispatch
branch carries. Generated by `tools/intrinsic_ref.py` from the compiler,
never edited by hand; a test keeps it level with the code. These are
the library's vocabulary (docs/01 chapter 23): an author reaches for
the author-facing ones (output, the parser buffer, memory, the tree,
movement), and `arcc --extract` shows every use of the rest.

### Compile-time folds (any_*)

| intrinsic | what it does |
|---|---|
| `any_action_read` | any_action_read(): 1 if any code reads `action`, so the dispatcher's one-store bookkeeping folds away in a game that never asks. |
| `any_adjectives` | any_adjectives(): 1 when any words list carries the > adjective marker, so the ZIL match classes fold away without one. |
| `any_after` | any_after(): 1 when any `on after` handler exists (compile-time; the static fold usually decides it before this is reached). |
| `any_allwords` | any_allwords(): 1 when the takeall granule declared all-words, else 0, so the parser's TAKE ALL hand-off folds away without the granule. |
| `any_alter` | any_alter(): 1 if any `alter` statement exists; the report guards fold away in a game that never alters. |
| `any_ambience_once` | any_ambience_once(): 1 if any ambience block is the shuffled deal (bare `once`), so the granule's deal path folds away otherwise. |
| `any_anywhere` | any_anywhere(): 1 when a verb declares `anywhere`. |
| `any_appearance` | any_appearance(): 1 when anything declares `appearance`, so the room describer's check folds away otherwise. |
| `any_articles` | any_articles(): 1 when anything hand-sets `article`, so the packs' override branch (and its capitalized twin) folds away otherwise. |
| `any_awards` | any_awards(): 1 when the game scores at all (any award site, pool, or auto-scored object), so score plumbing folds away otherwise. |
| `any_beyond` | any_beyond(): 1 if any object is beyond; the touch guards fold. |
| `any_binary` | any_binary(): 1 if any object is binary (or its alias switchable), so the switch contract folds away in a game with nothing to flip. |
| `any_binds` | any_binds(): 1 when any grammar line binds an object into a slot (the spell-verb idiom), so the matcher's bound bookkeeping folds. |
| `any_carry_limit` | any_carry_limit(): 1 when the game has a limit, fixed constant or declared carry_limit global (_any_carry). |
| `any_carryweight` | any_carryweight(): 1 when the carryweight granule is summoned. |
| `any_commanding` | any_commanding(): 1 when the NPC engine is summoned at all. |
| `any_compactrooms` | any_compactrooms(): 1 when `constant compact_rooms = 1` drops the blank line above a room title. |
| `any_components` | any_components(): 1 when anything declares `component` (object or kind default), so the part-of hooks fold away otherwise. |
| `any_concealed` | any_concealed(): 1 when anything is ever concealed (declared or set in play), so gain's noticed-now clear folds away otherwise. |
| `any_container_caps` | any_container_caps(): 1 when any object or kind declares the item_cap property, so the insertion ceiling folds away unused. |
| `any_dark` | any_dark(): 1 when darkness can happen in this game (a room without `lit`, or a statement that clears `lit` at run time), else 0, so the darkness branch of the draw path folds away in an always-lit game. |
| `any_death` | any_death(): 1 if any `death` statement exists; the post-mortem's UNDO machinery folds away in a game whose endings all `finish`. |
| `any_debug` | any_debug(): 1 when the debug granule is summoned (its reach fold). |
| `any_doors` | any_doors(): the compile-time door flag (1 or 0), consumed by the go handler's static `if any_doors() is 1`; a plain constant otherwise. |
| `any_duals` | any_duals(): 1 when a verb word doubles as a noun. |
| `any_edible` | any_edible(): 1 when any object or kind declares edible, so the eat handler's consume branch folds away in a game with no food. |
| `any_enterable` | any_enterable(): 1 when any object is a supporter or container by kind, so the nested-location suffix folds away otherwise. |
| `any_exposed` | any_exposed(): 1 when a thing is `exposed`. |
| `any_exposed_line` | any_exposed_line(): 1 unless the game writes constant exposed_line = false (the automatic belongings sentence after EXAMINE on a character). |
| `any_firstperson` | any_firstperson(): 1 when the game narrates in the first person (constant first_person = 1); the language layer's person branches fold on it. |
| `any_grains` | any_grains(): the compile-time grains flag (1 or 0), so find_scenery folds its chain walker away in a game with no grains. |
| `any_images` | any_images(): the compile-time image flag (1 or 0), so describe_room folds its whole picture path away in a game with no arc_image. |
| `any_indefinites` | any_indefinites(): 1 when an object sets `indefinite`. |
| `any_lighttopology` | any_lighttopology(): 1 when the light-level granule is summoned; the core's visibility seams (light_dims) fold away otherwise. |
| `any_maniacswap` | any_maniacswap(): 1 when maniacswap is summoned (the SELF pronoun and the swap's reach fold on it). |
| `any_named` | any_named(): the compile-time named flag (1 or 0), so the article blocks fold their `named` check away in a game with no proper-named objects. |
| `any_named_lower` | any_named_lower(): 1 when some named object carries a capitalized name twin (a lowercase literal name). |
| `any_noiseprep` | any_noiseprep(): 1 when a noise word doubles as a grammar preposition or particle (the du class), so the packs' combined flag arms fold away otherwise. |
| `any_notify` | any_notify(): 1 when the game writes the notify global anywhere, so the loop's score-watch folds away otherwise (the coupled rule). |
| `any_npcengine` | any_npcengine(): 1 only when a roster exists. |
| `any_owner_index` | any_owner_index(): 1 when the word-to-owners index is built. |
| `any_pathfinding` | any_pathfinding(): 1 when the pathfinding granule is summoned. |
| `any_plurals` | any_plurals(): 1 when the plurals granule is summoned, so the plural hooks fold away without it. |
| `any_pluribus` | any_pluribus(): the compile-time grammatical-plural flag (1 or 0); the number-agreement machinery folds away in an unmarked game. |
| `any_presence` | any_presence(): 1 if any object uses the existence form (`in a, b`); the describer's presence pass folds on it (docs/01 chapter 3). |
| `any_pronoun_sets` | any_pronoun_sets(): 1 when the pack declares a multi-role pronoun word (German "ihm", "sie"), so the recency walk folds away in every other language. |
| `any_ranks` | any_ranks(): 1 when the game declares a rank ladder, so msg_score's rank clause folds away otherwise. |
| `any_reach` | any_reach(): 1 when something reaches beyond scope (the reach_unscoped seam or `anywhere`). |
| `any_requires` | any_requires(): 1 when a verb declares `requires`. |
| `any_restless` | any_restless(): 1 if any object is (or can become) restless. |
| `any_scenery_contents` | any_scenery_contents(): 1 when the game opts in with `constant scenery_contents = 1` (the arc_mode manner: the constant folds by name where declared; this default covers its absence). |
| `any_scoperoom` | any_scoperoom(): 1 when the backstage scope room was seeded (some object is placed `in scope`), so the scope hook folds away otherwise. |
| `any_scored` | any_scored(): 1 when anything declares `scored`, so the award hooks in take and go fold away in a scoreless game. |
| `any_shiftable` | any_shiftable(): 1 if anything can be pushed between rooms, so the push-travel path folds away otherwise. |
| `any_sight` | any_sight(): 1 if any non-movable object uses the sight form (`spans`); with it 0, is_presence needs no marker read. |
| `any_spans` | any_spans(): the compile-time spans flag (1 or 0). |
| `any_swap` | any_swap(): 1 when the maniacswap granule is summoned. |
| `any_tables` | any_tables(): the compile-time positional-grammar flag (1 or 0), so the grammar-table matcher and the packs' tabled-verb branches fold away in a game whose verbs all fit the flag model. |
| `any_tagged` | any_tagged(): 1 when any object declares a `tag` qualifier, so the listing hook folds away otherwise. |
| `any_thing_duals` | any_thing_duals(): 1 when a thing word doubles as a verb. |
| `any_timerfirst` | any_timerfirst(): 1 if any timer is armed `. |
| `any_topic_idle` | any_topic_idle(): 1 if any topic is `idle`, so the granules' idle handling folds away otherwise (and cosmos_topic_idle is then DCE'd). |
| `any_topics` | any_topics(): 1 if any object or kind declares a topic. |
| `any_triggers` | any_triggers(): 1 when any words list carries the # trigger marker (docs/01 chapter 14), so the matcher's trigger tiebreak folds away without one. |
| `any_turnfirst` | any_turnfirst(): 1 if any handler is `on each_turn first`. |
| `any_typed_slots` | any_typed_slots(): 1 when any verb grammar line carries a typed input slot (letters, number, anychar), so the matcher's class branch and slot_class_ok fold away in every other game and the story file does not grow by a byte. |
| `any_unruled` | any_unruled(): 1 when some action has no free-standing rule, so an unclaimed command could otherwise end the turn in silence. |
| `any_verb_read` | any_verb_read(): 1 if any author code reads verb_trigger, so the parser's store and the AGAIN/perform plumbing fold away otherwise. |
| `any_wearable` | any_wearable(): 1 when anything declares wearable or worn, so the movers' worn gate folds away where nothing can be on the body. |

### Output and the screen

| intrinsic | what it does |
|---|---|
| `buffer_mode` | buffer_mode(n): 0 suspends the lower window's word-wrap buffering, 1 resumes it. |
| `clear_screen` | clear_screen(): wipe the whole screen (erase_window -1, which also unsplits) and drop any pending paragraph break with it. |
| `erase_line` | erase_line(): the standard's operand 1 means "to the end of the current line"; other values are undefined, so it is not exposed. |
| `erase_window` | erase_window(n): clear window n (1 = upper) so the menu repaints clean; -1 unsplits and clears the whole screen. |
| `mute_begin` | mute_begin(): select z-machine output stream 3 into the mute buffer (seeded in __mutebuf__), so everything a background performer prints while out of scope lands there instead of the screen. |
| `mute_buf` | mute_buf(): the mute buffer's byte address (the __mutebuf__ global), for replay_muted to read the captured text back. |
| `mute_end` | mute_end(): deselect stream 3 (the -3 as its 16-bit two's complement); the buffered text is simply discarded. |
| `new_line` | new_line(): a bare newline (the raw opcode), for the library's own line control. |
| `par` | par(): mark a pending paragraph break; the print layer flushes it as a single blank line before the next text, collapsing repeats. |
| `print_banner` | print_banner(): print the game's banner (title, author, release line) on demand (`banner false` in the game block stops the automatic one). |
| `print_name` | print_name(obj): the object's short name, no newline. |
| `print_packed` | print_packed(a): print the packed string at a (the rank titles). |
| `read_key` | read_key(): read one keypress, returning its ZSCII code. |
| `screen_height` | screen_height(): the screen height in lines (header byte 0x20), so the menu can cap the upper window to what fits. |
| `screen_width` | screen_width(): the screen width in characters (header byte 0x21). |
| `set_colour` | set_colour(fg, bg): the raw colour opcode (0 keeps a side); author code uses zcolor and say.<colour>. |
| `set_cursor` | set_cursor(line, column): move the upper-window cursor (1-based). |
| `set_style` | set_style(s): text style bits (0 normal, 1 reverse, 2 bold, 4 italic). |
| `set_window` | set_window(n): select window 0 (main) or 1 (upper). |
| `show` | show(text): print without a trailing newline (for prompts and for building a sentence around a named object). |
| `show_char` | show_char(c): print one ZSCII character. |
| `split_window` | split_window(n): reserve n lines for the upper window. |
| `zc_font` | zc_font(): the base font colour zcolor.font stored. |
| `zc_input` | zc_input(): the input colour zcolor.input stored. |
| `zc_status` | zc_status(): the status-bar colour zcolor.statusline stored. |

### The parser buffer

| intrinsic | what it does |
|---|---|
| `ask_addr` | ask_addr(): the address of the text-buffer backup the disambiguation ask uses to keep the command while the answer claims the live buffer. |
| `dict_entry` | dict_entry("se"): the word's DICTIONARY address, a compile-time literal (the Inform 'se' idiom, auraes's ask, 2026-09-15): what word_dict() returns for the typed spelling, so parse-buffer words compare and scan against vocabulary directly. |
| `oops_addr` | oops_addr(): the address of the parse-buffer backup kept for oops. |
| `parse_addr` | parse_addr(): the address of the live parse buffer. |
| `read_line` | read_line(): read a line from the player into the text buffer; returns the terminating character. |
| `retokenize` | retokenize(): re-run the interpreter's tokenizer over the (possibly patched) text buffer, refilling the parse buffer. |
| `text_addr` | text_addr(): the typed-text buffer's address (its first character is at text_addr() + 2, and word_pos offsets are relative to the buffer). |
| `text_char` | text_char(i): the i-th character typed on the last input line. |
| `tokenise_at` | tokenise_at(text, parse): the interpreter's tokenizer over explicit buffers (S 15, tokenise). |
| `word_count` | word_count(): how many words the last input line tokenized to. |
| `word_dict` | parse buffer word i: dict-address word at word index 1 + 2*i. |
| `word_len` | word_len(i): the length of the i-th typed word. |
| `word_pos` | word_pos(i): the position of the i-th typed word in the text buffer. |

### Memory

| intrinsic | what it does |
|---|---|
| `band` | band(a, b) / bor(a, b): bitwise and/or, the Z-machine's own opcodes, one instruction; games that never call them pay nothing. |
| `bor` | band(a, b) / bor(a, b): bitwise and/or, the Z-machine's own opcodes, one instruction; games that never call them pay nothing. |
| `catalogs_base` | catalogs_base(): the base address of the catalog region in dynamic memory. |
| `peek_byte` | peek_byte(addr): the byte at addr. |
| `peek_word` | peek_word(addr, i): the i-th word at addr (word-indexed). |
| `poke_byte` | storeb(addr, 0, v): push v then addr so addr is read first. |
| `poke_word` | poke_word(addr, i, value): store value as the i-th word at addr. |
| `scan_table` | scan_table(value, addr, count): the interpreter's table search (VAR:23) over count words from addr, storing the address of the first entry equal to value, 0 when there is none. |
| `words_addr` | words_addr(obj): the address of the object's words array (0 if none). |
| `words_count` | words_count(obj): how many words the object has (the array length / 2). |

### The object tree and properties

| intrinsic | what it does |
|---|---|
| `adjective_addr` | adjective_addr(obj): the address of the object's adjective word array. |
| `adjective_count` | adjective_count(obj): how many adjective words the object lists. |
| `appearance_addr` | appearance_addr(obj): the address of the object's appearance property, 0 if none. |
| `article_addr` | article_addr(obj): the address of the object's hand-set article, 0 if none. |
| `beyond_why_addr` | beyond_why_addr(obj): the address of the object's beyond_why text, 0 if none. |
| `carry_limit` | carry_limit(): the game's `constant item_cap`, or 0 for none. |
| `carry_weight` | The budget in tenths: constant weight_cap (sema scaled it), or 100 (10.0 units, twenty average things) when undeclared. |
| `container_cap` | container_cap(obj): the object's item_cap property (0 uncapped). |
| `desc_addr` | desc_addr(obj): the address of the object's desc property, 0 if none. |
| `exits_count` | exits_count(): how many directions are properties in this program. |
| `first_in` | first_in(obj): the first object inside obj (get_child), nothing when empty: "is the box empty" without a loop (auraes's ask, 2026-09-23). |
| `indefinite_addr` | indefinite_addr(obj): the address of the object's hand-set indefinite article, 0 if none. |
| `intro_addr` | intro_addr(obj): the address of the object's intro property, 0 if none. |
| `is_presence` | is_presence(obj): does this object's spans array mean EXISTENCE (present in each room) rather than sight (referable only)? Folds to a constant unless both forms are live in one game: no existence anywhere is 0; existence only is 1 (spans_here filters the rest); both live reads the sema-synthesized 1-byte presence marker. |
| `name_cap_addr` | name_cap_addr(obj): the address of a lowercase named thing's capitalized name twin, 0 if none. |
| `next_in` | next_in(obj): the next object beside obj in its holder (get_sibling), nothing at the end. |
| `object_count` | object_count(): how many objects the program declares (1..N), so the debug granule can scan them all by number (the parser reaches only those in scope). |
| `parent_of` | parent_of(obj): the object's parent in the tree (0 if detached). |
| `patrol_addr` | The address of the character's route array (0 if it has none): patrol and territory are arrays of room object numbers, emitted in the spans shape (objects.py). |
| `patrol_count` | How many rooms the route names (array length / 2). |
| `plural_addr` | plural_addr(obj): the address of the object's plural word array. |
| `plural_count` | plural_count(obj): how many plural words the object lists. |
| `spans_addr` | spans_addr(obj): the address of the object's spans array (0 if none). |
| `spans_count` | spans_count(obj): how many rooms the object spans (array length / 2). |
| `tag_addr` | tag_addr(obj): the address of the object's tag property, 0 if none. |
| `territory_addr` | The address of the character's route array (0 if it has none): patrol and territory are arrays of room object numbers, emitted in the spans shape (objects.py). |
| `territory_count` | How many rooms the route names (array length / 2). |
| `topics_count` | topics_count(person): how many topics the person has (0 if none). |
| `trigger_addr` | trigger_addr(obj): the address of the object's trigger word array. |
| `trigger_count` | trigger_count(obj): how many trigger words the object lists. |
| `weight_of` | weight_of(obj): the thing's own weight in tenths. |

### Dispatch and the turn

| intrinsic | what it does |
|---|---|
| `action_id` | action_id("take_off"): the action number for a named action, so the parser can remap a particle verb (switch + off -> switch_off). |
| `after_floor` | after_floor(): the first synthetic after action number (a compile-time constant); dispatch's refusal tail stays quiet at or past it, because an after pass that nothing answers is normal. |
| `after_of` | after_of(action): the action's synthetic after number, 0 when it has no after handlers (after_map, emitted by codegen). |
| `anywhere_of` | anywhere_of(action): 1 when the action's verb declared `anywhere` (anywhere_map); with no such verb, a constant 0. |
| `call_handler` | call_handler(addr, action): call the routine at addr with one argument. |
| `ev_each_turn` | The event's action number, so the loop can fire it through react. |
| `ev_each_turn_first` | The event's action number, so the loop can fire it through react. |
| `ev_enter` | The event's action number, so the loop can fire it through react. |
| `ev_start` | The event's action number, so the loop can fire it through react. |
| `handler_of` | handler_of(obj): the object's react routine address, or 0 (the property default) if it has none. |
| `meta_floor` | meta_floor(): the first out-of-world action number (a compile-time constant); dispatch skips the object and room stages at or past it. |
| `perform` | perform("take", book) / perform("go", west) / perform("give", coin, bob): the action name resolves at compile time like action_id; the optional operands default to nothing. |
| `reach_of` | reach_of(action): the reachagnostic exemption bits (reach_map). |
| `req_noun_animate` | req_noun_animate(): the requirement bit for `requires noun animate`. |
| `req_noun_carried` | req_noun_carried(): the requirement bit for `requires noun carried`. |
| `req_second_animate` | req_second_animate(): the requirement bit for `requires second animate`. |
| `req_second_carried` | req_second_carried(): the requirement bit for `requires second carried`. |
| `requires_of` | requires_of(action): the packed requirement bits the action declares (requires_map, emitted by codegen). |
| `run_alter` | run_alter(): speak the report an `alter` registered for this action, then clear it (the library's success paths call it). |
| `run_free` | run_free(action): run the free rules for an action (react_free). |
| `run_grain` | run_grain(id, action): route a matched scenery grain to its routine. |
| `tick` | tick(): advance the turn counter (the loop owns turns). |
| `tick_timers` | tick_timers(): count down the after/every schedule once, firing what is due (schedule_tick, emitted by codegen; empty when nothing is scheduled). |
| `tick_timers_first` | tick_timers_first(): the same countdown for the first-marked slots (armed `after/every N turns first do X`), called at the top of the turn before the action dispatches. |

### Conversation

| intrinsic | what it does |
|---|---|
| `topic_idle` | topic_idle(person, i): 1 if topic i is the ask/tell fallback (`idle`). |
| `topic_label` | topic_label(person, i): print topic i's menu label (no newline). |
| `topic_matches` | topic_matches(person, i, word): 1 if topic i lists the dictionary word. |
| `topic_retire` | topic_retire(person, i): retire topic i now, so the menu drops it once it has been picked (the ask/tell path does not call this, so typed topics stay re-askable unless `once`). |
| `topic_run` | topic_run(person, i): run topic i's exchange (retires it if `once`). |
| `topic_visible` | topic_visible(person, i): 1 if topic i is in view (not hidden/retired, `when` satisfied). |
| `topic_word` | topic_word(person, i, k): topic i's k-th match-word (1-based). |
| `topic_words` | topic_words(person, i): the count of topic i's match-words (0 if none). |

### Movement and the map

| intrinsic | what it does |
|---|---|
| `dir_name` | dir_name(d): speak the direction's word at runtime, wherever the value came from (the answer to static typing ending at a block parameter). |
| `exit_dest` | exit_dest(room, dirprop): the destination of a direction. |
| `exit_name` | exit_name(i): print the i-th direction's name (no newline). |
| `exit_prop` | exit_prop(i): the property number of the i-th direction (0 out of range). |
| `no_way` | no_way(): the way family's absence value, -1 as a 16-bit word. |
| `npc_table` | npc_table(): the NPC roster's base address (0 without a roster), from the __npcs__ global build_story seeds. |
| `path_buf` | path_buf(): the path scratch's byte address (crumbs, then fringe; codegen sizes and seeds it only when way_toward is called). |
| `scope_room` | scope_room(): the backstage room's object number (0 unseeded). |

### Pictures

| intrinsic | what it does |
|---|---|
| `arc_image_dark` | arc_image_dark(): the darkness picture's id as a folded constant. |
| `arc_mode` | arc_mode(): the game's picture mode as a folded constant (the default when no `constant arc_mode` is set). |
| `draw_image` | draw_image(id, mode): draw the room picture (id 0 clears the band); mode selects the layout. |
| `image_of` | image_of(room): the room's picture id (the arc_image slot), or 0 (the property default) when the room has no picture. |
| `pictures_available` | pictures_available(): 1 when the interpreter can show pictures, else 0. |

### Session

| intrinsic | what it does |
|---|---|
| `auto_banner` | auto_banner(): 1 unless `banner false`, so the turn loop prints the banner itself after `on start` (a folded constant, like any_X). |
| `do_quit` | do_quit(): end the session. |
| `do_restart` | do_restart(): restart the story from the beginning (never returns). |
| `do_restore` | do_restore(): restore a save. |
| `do_restore_undo` | do_restore_undo(): undo to the last checkpoint. |
| `do_save` | do_save(): save the game. |
| `do_save_undo` | do_save_undo(): checkpoint for undo. |
| `transcript_close` | transcript_close(): deselect stream 2 (-2 as the unsigned 16-bit word; the interpreter reads the operand as signed) and close the transcript. |
| `transcript_open` | transcript_open(): select output stream 2. |

### Scoring

| intrinsic | what it does |
|---|---|
| `award_earned` | award_earned(i): the earned byte for award site or pool i. |
| `pools_table` | pools_table(): always 0. |
| `ranks_table` | ranks_table(): the rank ladder's base address (0 without a ladder). |

### Library tables and the rest

| intrinsic | what it does |
|---|---|
| `action` | action: the action being dispatched this turn, read from the global the dispatcher sets. |
| `ambience_table` | ambience_table(): the ambience table's base address (0 when no block exists), from the __ambience__ global build_story seeds. |
| `calculate` | calculate(cat): the entry count. |
| `columns` | rows(m) / columns(m): a 2D matrix's dimensions, compile-time constants. |
| `dice` | dice(cat): one entry at random (1..count rides random's contract). |
| `duals_table` | duals_table(): the table of verb words that double as nouns. |
| `entry` | entry(cat, i): the i-th entry, 1-based. |
| `last` | last(cat): the index of the last live entry of a catalog or matrix. |
| `owners_table` | owners_table(): the word-to-owners index the noun matcher consults. |
| `random` | random(n): a uniform number from 1 to n (the interpreter's own generator, @random). |
| `rows` | rows(m) / columns(m): a 2D matrix's dimensions, compile-time constants. |
| `set_here` | set_here(room): the loop owns the here global (read-only to authors). |
| `thing_duals_table` | thing_duals_table(): the table of thing words that double as verbs. |

<!-- intrinsics:end -->
