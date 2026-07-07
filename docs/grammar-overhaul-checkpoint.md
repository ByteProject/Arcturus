# Checkpoint: a positional grammar layer for Arcturus

Status: DESIGN NOTE, not yet built. Written 2026-07-07 as a handoff for a
dedicated grammar-parser overhaul. The goal is a real, positional grammar system
that is a genuine alternative to Inform's, while keeping every simple statement
that works today working unchanged, and without sacrificing Arcturus's small
z-code. Falling behind Inform on grammar expressiveness is treated as a real
minus for the language, so this is worth doing properly rather than patching.

This note is deliberately concrete: it names the files, blocks, and encodings,
states the verified current behaviour (not guesses), and lists what must not
regress.

## 1. The trigger

An author declared:

```
verb "dig"
    dig
    dig noun
    dig noun with held
    dig in noun with held

on dig
    ...
```

Everything works except the last line. `DIG IN SAND WITH SHOVEL` does not run
the verb; it answers "Which do you mean, the sand or the shovel?" And `DIG IN
SAND` binds `noun = nothing` (sand lands in `second`). The leading `in` breaks
it.

## 2. Why: the current parser is flag-driven, not grammar-driven

The runtime parser does NOT walk grammar lines. At compile time each verb's
grammar lines are reduced to exactly two things:

- the verb's **arity**: how many `noun`/`held` slots its richest line has,
  capped at 2 (0 = intransitive, 1 = one noun, 2 = two nouns); and
- the **literal words** it mentions (`with`, `to`, `in`, ...), each registered
  in the dictionary as a **preposition** (a separator).

At run time (the per-language resolvers), a two-noun command is split at the
FIRST separator it finds: everything before is `noun`, everything after is
`second`. The grammar line's SHAPE, and where a literal sits in it, is never
consulted. Consequences, all verified by test:

- `dig noun noun` and `dig noun with noun` behave IDENTICALLY: both just mean
  "dig takes two nouns", and the split happens at any registered preposition.
- ANY leading literal breaks, standard or invented: `dig in noun with held` and
  `dig around noun with noun` both fail the same way (the leading word is grabbed
  as the split point, first noun empty, the rest is one ambiguous phrase).
- The action is the VERB WORD only. Prepositions do not select an action, so
  `look under noun` and `look behind noun` cannot be distinguished; both would be
  plain `look` with `noun = bed`. (`put X in Y` vs `put X on Y` are one action
  `put`, disambiguated at run time by whether the second noun is a container or a
  supporter, NOT by the preposition.)
- `second` is NOT a slot keyword. A two-noun line is written with `noun` twice
  (or `noun ... held`); the compiler assigns the first occurrence to `noun`, the
  second to `second`. Writing `dig noun second` silently collapses to `dig noun`.
- Quoted literals in a grammar line do NOT compile today: `dig "in" noun` crashes
  the compiler (`'list' object has no attribute 'lower'`), because a STRING token
  in `_parse_grammar_item` becomes an `ast.Word` whose value is a StringLit
  (a list of parts), which the vocabulary/preposition collection then `.lower()`s.

The virtue of this model is that it is tiny and fast, and it is why Arcturus
compiles small. That virtue must survive the overhaul for the simple cases.

## 3. Exact current mechanics (so the rewrite is grounded)

### Compiler
- `arcturus/parser.py`: `_parse_grammar_line` / `_parse_grammar_item`. Slots are
  `noun` (a keyword), and `held`/`multi`/`text`/`direction` (in
  `_GRAMMAR_SLOTS`). Anything else becomes `ast.Word(value)`. A trailing
  `reverse` sets `GrammarLine.reverse` (requires exactly two noun slots).
- `arcturus/ast.py` / `arcturus/worldmodel.py`: `GrammarLine(action, items,
  reverse)`, `items` a list of `Slot`/`Word`. The grammar lines ARE already
  parsed and available on `world.verbs[*].grammar`; they are just under-used.
- `arcturus/dictionary.py`: `_verb_arity` (arity per verb word; a verb with a
  `reverse` line is encoded as arity 6 = 2 | bit2), `_verb_actions`,
  `_preposition_words` (every grammar `Word` becomes a preposition entry),
  `collect_vocab`. Per-entry data bytes are `[flags, b1, b2]`: a verb is
  flags bit7 (128), b1 = action number, b2 = arity; a preposition is flag bit3
  (8); a direction bit6 (64); a particle bit5 (32); a pronoun, a grain, `all`,
  noise, each their own flag. THREE data bytes only, and a verb's are full.

### Runtime (Cosmos), per language
Language packs each own their resolvers (the language seam): `english.prelude`,
`german.granule`, `spanish.granule`. The agnostic matcher primitives live in
`parser.prelude`.
- `resolve_verb`: verb dict entry -> action (reads the data bytes; handles
  compound verbs via `find_particle` + `compound`).
- `resolve_objects`: arity 0 -> intransitive (`has_extra_words` guard); arity 1
  -> `match_noun`; arity 2 (or 6) -> `resolve_two_nouns`. Decodes arity 6 into
  `two_reverse`.
- `resolve_two_nouns`: scan for the first separator (`is_separator`: a
  preposition/direction/particle), split, `match_phrase(1,b)` and
  `match_phrase(b+1,n)`. If `two_reverse` and no separator, `reverse_split`
  (the adjacent-noun dative, `give bob coin`), which probes boundaries with
  `probe_noun`. A named-but-unresolved slot faults (`b > 1` / `b + 1 < n`).
- `match_phrase(lo, hi, plural_ok)` (parser.prelude): the reusable scoring noun
  matcher (word-membership scoring, ties -> disambiguation fault 3, pronouns,
  shut-container knowledge). `probe_noun` is its side-effect-free sibling.
- `dispatch` (dispatch.prelude): noun -> second (only when there IS a first
  noun) -> here -> free rules.

## 4. What MUST NOT regress

- Every current grammar shape: `verb`, `verb noun`, `verb noun <prep> noun`,
  `verb noun <prep> held`, `multi`/`text`/`direction` slots, multi-word verbs
  (particles: `take off`, `switch on/off`, `turn on/off`), verb synonyms.
- The reversed dative (`give noun noun reverse`, and German `gib noun noun
  reverse`); Spanish deliberately has none (its dative uses the personal "a").
- The recent parser fixes (do not undo them): the reversed dative and its
  `EXT:0x80` cousin are separate; second-noun pronoun binding
  (`note_referent(second)` in the shared `parse_line`); the missing-noun fault
  (a named-but-unresolved two-noun slot is rejected, and dispatch withholds the
  recipient handler when there is no first noun); `self` in a kind handler is the
  dispatched instance (an owned handler takes its self object as its first arg).
- The disambiguation / pronoun / chaining (`take x and y`) / oops / `all` /
  plurals / grains machinery. These operate on the RESOLVED noun/second and
  should be reusable above whatever matcher replaces the split.
- The three example conformance games and Hibernated 2, byte-for-byte behaviour.
- The size ceilings (`tests/test_sizes.py`) — smallest z-code is a charter
  objective. A `verb noun`-only game must not pay for a grammar table it does
  not need beyond the minimum; richer grammar is what should cost bytes.
- Zero runtime dependency; the language seam (agnostic matcher in
  parser.prelude, per-pack grammar + prepositions).

## 5. The goal

A positional grammar matcher that walks each grammar line token by token and
matches the typed command against it, Inform-style, so all of these become
expressible (none are today):

- leading prepositions: `dig in noun`, `search in noun`, `climb up noun`;
- fixed keywords anywhere: `fill noun from noun`, `tie noun to noun`;
- a preposition that SELECTS the action, so `look under noun` and `look behind
  noun` can be different actions with different responses (today impossible —
  action is the verb word);
- custom literal words that are not standard prepositions.

...while the simple lines keep working unchanged and stay as small as now.

## 6. Design direction (a sketch, not a mandate)

The core change is to stop throwing the line shape away. Emit a compact
**grammar table** per verb (each line = a sequence of tokens: slot-kind, or a
literal word reference, plus the line's action and a reverse bit), and give the
runtime a matcher that, for the typed words, tries the verb's lines in order and
takes the first that matches positionally:

- a literal token must equal the typed word (skipping noise/articles);
- a slot token (`noun`/`held`/`multi`/`text`) consumes a noun phrase via the
  existing `match_phrase` up to the next literal token or end;
- a full match sets `noun`/`second`/`action` and wins.

This SUBSUMES the flag model: arity, prepositions, leading prepositions,
positional keywords, and per-line actions all fall out of positional matching.
`match_phrase`/`probe_noun` stay as the noun-matching primitive. The `reverse`
marker becomes one line flag. Particles/compounds may fold into literal tokens.

Key tensions to solve, eyes open:
- SIZE. A grammar table costs bytes. Inform's is dense (~1 byte per token +
  action). Keep it pay-for-use (a game with only `verb noun` lines should encode
  next to nothing, or the matcher should special-case the trivial shapes). This
  is the make-or-break constraint; measure against `tests/test_sizes.py`.
- LANGUAGE SEAM. The matcher itself should be agnostic (parser.prelude); each
  pack supplies its grammar lines and its noise/article words, the way resolvers
  are split today. Do not duplicate the matcher three times.
- BACKWARD COMPAT. `dig noun noun` and `dig noun with noun` must still both work;
  the missing-noun fault, reversed dative, pronoun binding, and dispatch order
  must be preserved on top of the new matcher.
- The quoted-literal question resolves itself: with a positional matcher, a bare
  literal in a line is already a positional keyword, so quoting may be
  unnecessary. If a literal must double as a word that is elsewhere a real
  preposition (`in` for `dig` vs `in` for `put`), positional matching per verb
  handles it for free — no per-verb keyword table needed.

## 7. The concrete anchor case (the acceptance test)

```
verb "dig"
    dig
    dig noun
    dig noun with held
    dig in noun with held
```

- `DIG` -> intransitive.
- `DIG SAND` -> noun = sand.
- `DIG SAND WITH SHOVEL` -> noun = sand, second = shovel.
- `DIG IN SAND` -> noun = sand (today: noun = nothing).
- `DIG IN SAND WITH SHOVEL` -> noun = sand, second = shovel (today:
  disambiguation).

Plus a per-line-action case to prove the capability gain, e.g.

```
verb "look", "l"
    look
    look noun            -> examine
    look under noun      -> look_under
    look behind noun     -> look_behind
```

with `LOOK UNDER BED` and `LOOK BEHIND BED` reaching different actions.

## 8. Files to touch

- Compiler: `arcturus/parser.py` (accept quoted literals cleanly; the `.lower()`
  crash is the StringLit-as-Word path), `arcturus/dictionary.py` (emit the
  grammar table; today it only extracts arity + prepositions), `arcturus/ast.py`
  / `arcturus/worldmodel.py` (`GrammarLine` already carries the items),
  `arcturus/codegen.py`, maybe new intrinsics in `arcturus/lower.py` to read the
  grammar table at run time.
- Runtime: `cosmos/parser.prelude` (the agnostic matcher, keeping `match_phrase`
  / `probe_noun`), `cosmos/english.prelude` + `cosmos/german.granule` +
  `cosmos/spanish.granule` (their `resolve_verb` / `resolve_objects` /
  `resolve_two_nouns` / `is_separator` get replaced or thinned by the matcher).

## 9. Recommendation for the interim

Until this lands, document the current boundary in docs/01 section 10 (a grammar
line is `verb`, `verb noun`, or `verb noun <prep> noun`; the preposition
separates the two nouns and cannot precede the first; a preposition that carries
meaning should be a separate verb). Do NOT ship the quoted-literal band-aid: it
patches one symptom (leading words), adds per-verb machinery, and does not
generalise. The positional matcher is the real answer, and it makes the
quoted-literal idea moot.
