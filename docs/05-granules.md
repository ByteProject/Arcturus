# Arcturus Granules

The summonable features of Cosmos: the optional modules a story pulls in with
`summon`. This document is the author-facing reference for the granules that ship
with Arcturus, how to summon and fork them, and how to write your own. The
`summon` syntax is defined in 01 (section 13); the runtime each granule sits on
is in 02.

## 1. Granules and preludes

Cosmos comes in two kinds of file, both ordinary Arcturus that lex identically;
the extension marks the role (01, section 2):

- A `.prelude` is part of the core library, loaded before every story. The
  prelude is the **overridable base**: redefine a prelude block of the same name
  in your story (or in a granule) and yours wins.
- A `.granule` is a **summoned module**, loaded only when a story summons it, and
  left out entirely otherwise. A granule is **forked, not overridden**: if you
  want to change one, you take a copy of the whole file and edit it.

That boundary is the point of having two kinds. A granule's own blocks are *not*
overridable from a story (the compiler reports a duplicate definition). If they
were, a granule would be nothing more than a renamed prelude. So:

> **Prelude blocks: overridable, per block. Granule blocks: forked, whole file.**

A granule *can* override a **prelude** block, though. That is how the statusline
granule replaces the core `prompt`, and it is exactly what a language pack needs:
a translation is a granule whose blocks override the English prelude's. The
asymmetry only forbids a *story* from reaching into a *granule*.

## 2. Summoning a granule

There are three forms (01, section 13), and they differ in where the granule is
found:

```
summon.statusline             // the bundled copy, always
summon statusline.granule     // your copy if present, else the bundled copy
summon "/path/to/fork.granule"  // exactly this file
```

- **`summon.statusline`** (dotted) always uses the copy baked into `arcc`. It
  never looks at your directories. This is the form to use for the official
  feature, and the one the shipped examples use. The dotted form also covers the
  non-granule feature `summon.language "<name>"`, a compiler feature rather than a
  runtime module (section 6). The tuned abbreviation set is not a dotted feature;
  it is summoned by name (section 7).
- **`summon statusline.granule`** (a bare filename) searches the story's own
  directory, then each `-L` directory, and only then falls back to the bundled
  copy - printing a note when it does, so you know your fork was not picked up.
  A custom name found nowhere and not bundled is an error. This is the
  fork-friendly form.
- **`summon "..."`** (a quoted string) is an explicit file: an absolute path as
  written, or for a bare quoted name the story directory and then the working
  directory. There is no bundled fallback; a missing file is an error.

`-L` directories must be absolute paths, so the library a story compiles against
is deliberate and unambiguous.

## 3. The shipped granules

### extendedverbs

```
summon.extendedverbs
```

The verbs beyond the always-in standard set. The full verb-to-action table
with every synonym is docs/verb-set.md (the E column) and each default line
is in docs/message-set.md; the roster:

- RUMMAGING: `search`/`frisk` (lists what a container or supporter holds;
  a closed container keeps its secrets).
- ACTING ON THINGS, futile by default until an object overrides:
  `throw ... at`, `rub` (polish, clean, wipe...), `squeeze`, `tie ... to`,
  `cut`, `fill`, `burn`, `blow`, `set ... to`, `empty`, `buy`, `consult
  ... about`.
- BODY AND IDLE: `dig`, `wave`, `sit`, `stand`, `sleep`, `swim`, `swing`,
  `think`, `pray`, `shout`.

(Conversation is not this granule's business: ask/tell/answer are STANDARD
verbs, and the two topic presentations are their own granules, conversations
and infocom_talking, below. There is no fullscore verb anywhere: SCORE is
the one score verb and reports score, turns, and rank itself.)

Every default is an ordinary free handler, so the override story is the
usual one: an object's own `on rub` wins ("on rub / say ..."), a top-level
`on rub` rule reskins the verb game-wide, and `continue` defers back to the
granule's default. The granule's own message blocks (msg_throw, msg_dig,
...) are granule-owned wording: to rewrite them, fork the granule (section
4) rather than overriding from the story.

### infocom_talking

```
summon.infocom_talking
```

The Infocom-style conversation surface, the menu-less presentation of the
`topic` model: `ask innkeeper about lighthouse` scans the person's inline
`topic` declarations (01 section 15; they live in the person's body) for one
whose `words` match a typed subject word and is in view, runs it, and falls
back to the standard flat "stays mum" default when nothing matches. `tell`
shares the same path. There is no topic list anywhere: discovery is play,
the Infocom way, and TALK TO stays the flat brush-off a person can override
to nudge the player toward the two verbs that matter.

The granule holds ONLY logic, and is as translatable as the menu: the
ask/tell/answer verb words, their grammar, and every message live in the
language layer (the packs carry them), and the granule overrides the
standard `ask_to`/`tell_to` seams with the dispatch. It is mutually
exclusive with the conversations menu BY THE COMPILER: summoning both is an
error, an author settles on one presentation. The topics themselves are
identical either way, so switching later is a one-line change.

### statusline

```
summon.statusline
```

A one-line status bar across the top of the screen, painted before every prompt:
the room on the left, the score and move count on the right, in reverse video.
The right side adapts to the screen width the way PunyInform does - the full
`Score: n   Moves: n` on a wide screen, the compact `Score: s/t` on a narrow
retro one. It coexists with the conversations menu: when both are summoned the
bar sits pinned above the topic list.

### quotes

```
summon.quotes
```

A centered, reverse-video quote box in the upper window, in the tradition of
Infocom's Trinity: the classic way to open a game with an epigraph. The box is
centered from the interpreter-reported screen width, so it sits right on a
40-column 8-bit machine and a wide terminal alike, and it sits in the upper
third of the screen, where the eye expects it.

Three blocks, called in order:

- `quote(lines, width)` opens the box: `lines` is the number of text lines,
  `width` the length of the LONGEST line, counted by hand the way one counts a
  fixed-width layout. The box adds one space of padding on each side and a
  blank reverse row above and below. Opening the box clears the screen.
- `quote_line()` advances to the next line and leaves the cursor inside it;
  the author's own `show("...")` then prints that line's text. One
  `quote_line()` / `show(...)` pair per line, top to bottom. Lines print
  left-aligned inside the box; pad with leading spaces by hand for a
  right-aligned attribution, exactly as on paper. An empty line is
  `quote_line()` followed by `show("")`.
- `quote_done()` draws the bottom row, waits for a single keypress, and clears
  the screen for whatever follows. The status line, if summoned, redraws at
  the next prompt.

```
on start
    quote(3, 37)
    quote_line()
    show("In order to make an apple pie from")
    quote_line()
    show("scratch, you must first create the")
    quote_line()
    show("universe.        -- Carl Sagan")
    quote_done()
```

The text goes through `show(...)` directly because a string cannot travel
through a block parameter (01, section 3); the box manages the geometry, the
author supplies the words. Keep `width` under the narrowest screen you target
minus four (36 is safe on a 40-column Commodore 64); on a screen too narrow to
center, the box clamps to the left edge rather than wrapping.

An opening quote usually comes BEFORE the banner. Pair the granule with
`banner false` in the game block and a `print_banner()` call after
`quote_done()` (01, section 4; 02, section 3), and the game opens in the
classic order: quote, keypress, banner, story. The box prints no words of its
own, so it works identically in every language, and it draws with the same
colours the game set with `zcolor` (01, section 16a).

### verbose_exits

```
summon.verbose_exits
```

Replaces the blunt "there's no exit in that direction" with a list of the room's
actual exits ("You can only go north or east from here."), read from the
compiler's own direction data, so it always matches the map.

### conversations

```
summon.conversations
```

The menu presentation of the `topic` model: TALK TO <person> opens a numbered
list of what there is to talk about, pinned in the upper window while the
conversation scrolls beneath it.

WHERE TOPICS LIVE. Topics are not declared in the granule or in any separate
registry: they live INLINE in the person's body, like properties and
handlers, and the same declarations serve both conversation systems (this
menu, and extendedverbs' ask/tell). The full header grammar is 01 section
15; the shape:

```
thing wirtin of character in inn
    name "innkeeper"
    named

    topic lighthouse "the lighthouse" words lighthouse, tower
        you "What about that lighthouse out there?"
        reply "Dark since that night. Nobody has gone back up."
        reveal key_talk

    topic key_talk "the key" hidden
        you "Is there a key somewhere?"
        reply "In the chest, by the hearth."

    topic debt "the old debt" when player holds ledger once
        reply "So you found it. Then you know what I owe."
```

- The MENU LABEL is the quoted string after the subject id ("the
  lighthouse"): that is the line the player sees, numbered, in the list.
- `words` are only for ask/tell (`ask innkeeper about tower`); the menu does
  not need them, players pick by number.
- VISIBILITY is live, three ways (01 section 15 explains when to use which):
  a `when` guard follows the story state by itself; `hidden` topics enter
  view when another topic's body (or any handler) runs `reveal <subject>`;
  `once` retires a topic permanently after one telling.
- The BODY is an ordinary statement block: `you`/`reply` print attributed,
  auto-quoted dialogue (framing overridable via line_you/line_reply/
  line_end), `say` is narration, and any statement works: set flags, move
  objects, change the score. The person is `self`.

THE MENU FLOW. TALK TO paints the list (the statusline, if summoned, stays
pinned above it); a digit runs that topic's exchange in the lower window and
the list repaints, reflecting anything the topic revealed, hid, or retired;
0, or running out of topics, closes it ("You let the conversation rest
there."). A person with nothing to raise answers msg_no_topics ("You can't
think of anything worth raising right now."). Every framing line is in the
language layer, so packs translate it (docs/message-set.md).

ASK AND TELL. The standard ask lands in the menu (asking IS talking:
`ask vlad`, and even `ask vlad about the vines`, opens Vlad's menu, the
subject words riding along), and the standard tell answers with the
use-TALK hint (msg_use_talk, a language-layer line): the granule overrides
the `ask_to`/`tell_to` seams and holds no words and no strings itself.
The infocom_talking granule is the other presentation of the same topic
declarations, and the two are mutually exclusive BY THE COMPILER: summoning
both is an error. The topics are identical either way, so switching
presentations is a one-line change. A person can still override `on talk`
for a one-off custom exchange that bypasses the menu.

### ambience

```
summon.ambience
```

Rooms and things murmur over time. An `ambience` block is a list of lines; on
a room it plays while the player is there, on a thing while the thing is in
scope, which is what makes a companion or a muttering radio work. At most one
ambient line plays per turn, so a busy room never floods the transcript.

```
room monorail
    ambience
        "Vlad steps over the skeletal remains without adjusting his gait."
        "Vlad runs a rapid scan of the chamber, then dismisses it as redundant."
        "Somewhere far down the tunnel, metal settles."

    ambience about 12 turns when door_open
        "A draught moves through the open blast door."
```

The header, modifiers in any order (`when` reads to the end of the line, so
it comes last):

- bare `ambience`: ABOUT the `ambience_rate` dial (default 8), random order,
  never the same line twice running.
- `about N turns`: living odds. Each silent turn shortens them, a fired line
  resets them, so the room breathes instead of ticking.
- `every N turns`: the strict metronome.
- `in order`: the lines play as written, then cycle; `in order once` falls
  silent after the last, for scene-setting that quietly exhausts itself.
- `when <cond>`: gates the whole block live, like a topic guard.

A line is a string, or `do <block>` for a computed one, and each line may
carry its own trailing `when`. The dial: `ambience_rate` is the default
cadence, and `change ambience_rate to 0` mutes every block (bring it back
after the tense scene); blocks with their own cadence keep it otherwise.

KNOW WHEN NOT TO USE IT. One line that fires until a condition flips is a
plain daemon, two lines of code and no granule (`every 3 turns do drip`);
the ruby-gem style room pulse in the daemons example is exactly that.
Ambience earns its summon for shuffled, breathing texture: NPC behavior and
layered room mood.

### takeall

```
summon.takeall
```

TAKE ALL, DROP ALL, and TAKE ALL FROM <container>. The core deliberately
omits ALL (it flattens scenes into transactional loot runs), so it is a
granule: a game that wants the convenience summons it, and a game that does
not pays nothing (the parser's hand-off folds away without the summon).

The sweep tries what a plain take would not refuse on sight: nothing fixed,
scenery, animate, hidden, or already carried, including what sits on
supporters and in open containers; DROP ALL keeps what is worn; a shut
source refuses honestly ("The chest is shut."). Each attempt still runs the
object's own handlers, so a custom `on take` refusal simply prints after the
item's name:

```
>take all
brass lamp: Got it.
wooden box: Got it.
idol: The idol is welded to its pedestal.
```

Every swept item is a FULL TURN: daemons fire and the clock moves per item,
exactly as if the takes had been typed one by one. This is a deliberate
departure from Inform, where ALL costs one turn; in Arcturus doing three
things costs three turns, the same rule a chained line follows (02, section
8b). UNDO takes back the whole sweep, because the sweep is one typed command
and undo peels typed commands. An empty sweep, and ALL with any other verb
("eat all"), refuse, so a chained line stops there honestly.

The granule declares the words (`all "all", "everything"`) and its messages
in English; a translation forks it and redeclares both (section 4), the same
rule as every granule.

### plurals

```
summon.plurals
```

The group model, two parts that arrive together (noun lists, "take lamp
and box", are a CORE chaining feature, not part of this granule; 02, section
8b):

- GROUP WORDS. Each member of a group declares the words that name it as a
  group: `plural coins` on the gold coin and the silver coin. "take coins"
  then runs the take on every coin in scope, one line and one full turn per
  coin, exactly like TAKE ALL's sweep; with only one coin left, the same word
  binds it singularly with no ceremony. The ordinary singular vocabulary
  still disambiguates: "take coin" (a `words` entry on both) asks which.
- THEM. The pronoun for the last group: "take coins" then "drop them". THEM
  re-runs the group word, so it honestly covers whatever of the group is
  still in scope.

English-worded like every granule; a translation forks it. A Spanish fork
should keep the THEM declaration out: the clitic plurals (-los, -las) in the
core Spanish pack already fill that role, and bare "los"/"las" are the
articles. The granule's `pronoun them "them"` declaration doubles as its
compile-time marker: every hook in the core parser folds away without it.

### debug

```
summon.debug
```

Developer verbs, opt-in by the summon alone (there is no separate release build
to strip them from; not summoning them leaves them out). Arcturus-named with the
familiar Inform synonyms:

- `tree` / `objects` - the whole object tree.
- `scope` - what is reachable from here.
- `fetch` / `purloin` - pull any object into your hands.
- `warp` / `gonear` - teleport to an object's room.
- `inspect` / `showobj` - an object's location and the attributes it has set.

`fetch`, `warp`, and `inspect` reach objects that are out of scope, which the
parser would normally refuse; the granule teaches the parser to reach them
through the `reach_unscoped` seam (section 5).

## 4. Forking a granule

To change a granule, take a copy and edit it.

- One granule next to a story:

  ```
  arcc --eject-granule statusline      // writes statusline.granule here
  // edit statusline.granule, then in the story:
  summon statusline.granule            // your copy wins over the bundled one
  ```

- The whole library, to fork several files or a prelude:

  ```
  arcc --extract-library /abs/cosmos   // every prelude and granule
  // edit files in /abs/cosmos, then:
  arcc game.storyarc -L /abs/cosmos    // -L must be absolute
  ```

  With `-L /abs/cosmos`, a `summon statusline.granule` in the story finds your
  edited `/abs/cosmos/statusline.granule` before the bundled one. A prelude can
  only be forked this way: there is no single-prelude eject (except
  `--eject-language` for translation, section 6) - to hack a prelude you extract
  the whole library and point `-L` at it.

## 5. Writing your own granule

A granule is plain Arcturus in a `.granule` file. It may declare verbs, kinds,
objects, and blocks, and it may **override prelude blocks** by defining a block
of the same name. Summon it by filename (`summon mygranule.granule`) or path.

A few patterns the shipped granules use:

- **Override a message or behavior.** Define a block named like a prelude block
  (a `msg_*`, or `prompt`, `describe_room`, the parser blocks) and yours replaces
  it. This is how statusline overrides `prompt` and verbose_exits overrides
  `msg_cant_go`.
- **Add a verb with an overridable default.** Declare the `verb`, write a free
  `on <verb>` handler that speaks a default, and let an object override it with
  its own `on <verb>` (most-specific-wins).
- **Integrate optionally with another feature through a seam.** When two granules
  may or may not both be present, neither can override the other's blocks. Put a
  default block in the *prelude* and have each granule override or call it. The
  statusline/conversations coexistence works this way (`status_bar`, a prelude
  no-op the statusline overrides and the menu calls), and so does the debug
  granule reaching out of scope (`reach_unscoped`, a prelude hook the parser
  calls and debug overrides). A seam is the only way to compose two optional
  granules, and it is what lets a language pack and the debug granule both extend
  the parser at once.
- **Depend on another granule.** A granule may itself `summon` another; the
  loader resolves summons transitively, each granule loaded once.

Keep a granule self-contained and summon-gated: anything it ships is left out of
a story that does not summon it.

## 6. Not a granule: the language pack

`summon.language "<name>"` is a compiler feature rather than a runtime granule: it
selects a localization (milestone B7). A language pack is a translation of
english.prelude, saved as a granule whose blocks override the English ones (a
granule overriding the prelude, section 1). Start from `arcc --eject-language`,
translate, and ship the result. The pack may replace the parser's grammar logic
too, not only its wording, since an inflected language parses differently (02,
section 8).

## 7. The tuned abbreviation set

Most of a story file is text, so the compiler compresses it against the
Z-machine's abbreviation table (docs/00 section 5). This asks nothing of you:
every build already applies a standard abbreviation set, computed once from the
Cosmos library text and baked into `arcc`.

A particular story can do better than the standard set by curating one over its
own text. Run:

```
arcc --make-abbreviations mystory.storyarc
```

which pools the strings of the story and every granule it summons, computes an
optimized set up to the Z-machine's ceiling of 96 entries, and writes an
`abbreviations.granule` beside the story. Summon it by name to use it in place of
the default:

```
summon abbreviations.granule
```

It is neither a dotted feature nor runtime code. The file is compile-time data the
text encoder reads, so it holds only string literals (and therefore lexes and
highlights like any Arcturus source). A story that never summons it simply keeps
the standard set, and summoning it costs nothing at run time; it only changes how
the text is packed. Regenerate it after large text edits. The optimizer is the
same one that computes the built-in default (tools/arcabbr.py), so a
`--make-abbreviations` run is slower than a plain build, but it runs only when you
ask, which is why the two-pass split exists: the fast default on every build, the
slow tuned set on request.
