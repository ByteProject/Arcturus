# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Verbs that reach beyond the room: `anywhere`.** A verb whose object
  has just left (FOLLOW, SHOUT) declares `anywhere` beside its grammar,
  and the parser binds the thing the player named wherever it is; the
  handler decides what reachable means. The declarative face of the
  reach_unscoped seam, Inform's scope token in one word; games without
  it compile byte for byte as before (arcc 2.24.0, Cosmos 1.41.0).
- **A name that changes: `name block`.** An object's short name can
  now be computed at print time, Inform's short_name in Arcturus's own
  block idiom: "a dull coin" until it is polished, "a gleaming relic"
  after, in the room listing, the inventory, every report and your own
  `${the noun}`. The spelling always existed on paper and printed
  garbage; now it works, and `change obj.name` explains itself. With
  it, `first_in(obj)` and `next_in(obj)` read the object tree's links
  directly, so "is the box empty" is one test. Games with literal
  names compile byte for byte as before (arcc 2.23.0).
- **Put says what it did, and a line back for retro screens.** PUT and
  INSERT now report like every other success: "You put the coin in the
  box.", "You put the candle on the altar." (German and Spanish in their
  own words), in place of the flat "Done.". And a game on a 25-row
  screen can reclaim the blank line above every room title with
  `constant compact_rooms = 1`; off by default, byte-identical without
  it (arcc 2.22.0, Cosmos 1.40.0).
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
