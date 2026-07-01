# Arcturus Code Generation Mapping

Status: in progress, produced as the backend is built (roadmap document 04).
This document records how Arcturus constructs lower to Z-machine version 5. It
grows milestone by milestone; this revision covers the B3 minimum viable
backend (banner, print, quit).

The authoritative language and runtime definitions are docs/01 and docs/02;
this document is the construct-to-opcode reference the backend implements.

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
Cosmos's responsibility (docs/02 section 3), where the library contributes its
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
statusline and menu seams (`status_bar`, `status_lines`, `menu_owns_talk`) when
neither granule is summoned. Dropping it is sound because a kept routine's call
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

## 12. Not yet lowered

Deferred to later milestones: the `a`/`an` choice by sound, kind-level grains and
topics (they need per-instance scope), and computed (`block`-valued) exits and
`on go other`.
