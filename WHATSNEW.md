# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Light that travels: summon.lighttopology.** Light becomes a level
  (0 dark, 1 dim, 2 lit, 3 bright) and moves through the map: a lit room
  spills light one level less through an open doorway, a closed door
  seals it off, and a thing can declare `needs_light 2` to stay unseen
  (not listed, not referable) until the light is good enough. Levels
  combine by maximum, so two candles are candlelight; `light N` sets a
  room's or a lamp's strength and the existing `lit` stays the switch,
  so a game that summons the granule and declares nothing plays exactly
  as before. One granule, three languages, and a game that never summons
  it compiles byte for byte as before (arcc 2.21.0, Cosmos 1.39.0).
- **The clock's second hand: the `first` placement.** Daemons and
  timers can now fire at the TOP of the turn: `on each_turn first`
  runs before your command is even parsed, so a rule there refreshes
  derived state (a hidden flag computed from the room's light) in
  time for the parser itself to see it, the pipeline position
  PunyInform authors abused InScope for. `after`/`every N turns first
  do X` fires a timer before the action dispatches; out-of-world
  commands burn no fuse. Alongside it, a computed block on an
  attribute (`hidden block`) is now refused with a clear cure instead
  of being silently ignored. Games using neither compile byte for
  byte as before (arcc 2.20.0, Cosmos 1.38.0).
- **Italic and bold, one dot.** `say.italic "..."` and `say.bold "..."`
  print one passage in that style and restore roman by themselves,
  exactly like the color dots, with `show.italic` / `show.bold` as the
  inline siblings and free composition with colors and paragraph
  modifiers (`say.yellow.italic.par`). No guard needed, on any
  interpreter: the Standard substitutes a style a machine cannot draw.
  A game that never styles compiles byte for byte as before
  (arcc 2.19.0).
- **The whole machine park, one command.** `arcimg convert art/ --all
  -o out/ --preview previews/` converts every master for every retro
  machine at once: one folder per target (out/c64/, out/ami/,
  out/zx3/, ...), a pixel-exact preview folder beside each, per-class
  master selection (masters-broad/) and the Spectrum colour path
  applying per target as ever, and machines whose converter is still
  to come reported once and skipped. Preparing sources got simpler
  too: a file named 1.png IS picture 1, and art already at a band
  size keeps its shape (arcimg 2.3.1).
- **Say I: first-person narration.** One constant in your game,
  `constant first_person = 1`, and the whole English library narrates
  as I: "I take the lamp with me.", "I'm carrying:", every listing,
  report, and refusal, the extended verbs included. The system voice
  deliberately stays second person (the parser's clarifying questions
  and the quit and death prompts talk to the player at the keyboard,
  not the narrator), any single line is still yours to override by
  declaring its block, and a second-person game compiles byte for
  byte as before (arcc 2.16.0, Cosmos 1.36.0).

## Feature roadmap

Considered and coming, in no particular order; each lands the Arcturus
way, designed on its own terms, pay-for-use as always.

- **Darkness furniture.** Darkness as a referable thing (EXAMINE
  DARKNESS answers) and EXITS refusing without light. (The status bar
  already shows darkness instead of the room name; the rest of the
  furniture is still to come.)
- **Question preservation.** A disambiguation question survives an
  interposed command: asked "which coin?", the player may take inventory
  first and then answer. In the same breath: likelihood hints, letting a
  verb or object mark an interpretation as unlikely so disambiguation
  picks well before it has to ask at all.
- **Local spill.** A Z-machine routine holds at most 15 locals, parameters
  and `let`s together; today the compiler refuses an over-full block with a
  clear error and the cure (move part of the work into a helper block).
  Spilling the excess to the stack automatically would lift the ceiling
  without the author ever noticing. Fifteen is a lot, but someone will hit
  it sooner or later.
