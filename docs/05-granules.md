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

The verbs beyond the always-in standard set: search, throw, rub, squeeze, tie,
cut, fill, burn, blow, set, empty, buy, consult, dig, wave, sit, stand, sleep,
swim, swing, think, pray, shout, ask, tell, answer, and fullscore, each with
their synonyms. Most speak a sensible default that an object overrides through
ordinary handler resolution (an object's `on rub` wins over the granule's
default), exactly like the standard sensory verbs; `search` lists what a
container or supporter holds.

It also carries the Infocom-style conversation dispatch: `ask`/`tell <person>
about <subject>` runs the person's matching `topic` (01, section 15) if one is in
view, else the verb's flat default. When the conversations granule is also
summoned, the menu owns talking and ask/tell defer to it (see below).

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

The menu presentation of the `topic` model. `talk to <person>` paints their
topics in view as a numbered menu, held static in the upper window while the
conversation scrolls beneath it; press the number to ask one, and the menu
repaints as topics reveal, retire, or unlock. It is built on the same `topic`
construct the ask/tell path uses (01, section 15), shown as a list instead of
typed by subject. The two are mutually exclusive views of one model: when
conversations is summoned, the menu wins, and the extendedverbs ask/tell topic
dispatch steps aside and points the player at TALK TO.

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
