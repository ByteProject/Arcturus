# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Scoring, one half at a time.** Auto-scoring stays what it is (five
  points on a room's first visit, five on a thing's first take, once
  each, the maximum and the ranks summed by the compiler), and now
  either half switches off game-wide: `constant score_rooms = false`
  or `constant score_things = false`, with `reward` and `scored false`
  working on top as ever (arcc 2.25.0).
- **What a character shows: `exposed`.** A character's belongings are
  private on purpose (not Inform's everything-in-scope), and now the
  visible ones are declared per item: `exposed` on the hat someone
  wears or the passport they wave puts it in scope, EXAMINE on the
  character says "Testy is wearing a felt hat and carrying a
  passport.", and TAKE refuses in the holder's name. Games that expose
  nothing compile byte for byte as before (arcc 2.24.1, Cosmos 1.42.0).
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
  `constant compact_rooms = true`; off by default, byte-identical without
  it (arcc 2.22.0, Cosmos 1.40.0).

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
