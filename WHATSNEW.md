# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Arcturus games play on the web.** Proteus, the fourth standalone:
  one command turns a finished game into a single self-contained HTML
  page that runs in any browser, nothing to install and nothing to
  deploy. `proteus mygame.zblorb -o mygame.html`, or the story and its
  pictures Blorb as a pair, or a bare `.z5` or `.z8` for a text-only game.
  The resulting webpage carries the whole interpreter, the arc_image picture band scaled
  crisply to the window, the game's Z-machine colours painted to the page edges,
  and saves in the browser's local storage, typically in under a
  megabyte. Inside it is a Z-machine-only fork of Dannii Willis'
  Parchment, trimmed to a quarter of
  upstream's size and taught the arc_image contract; the fork lives in
  the repository under `proteus/`, and docs/09 is its book.
- **Blorb is the new standard.** `arcimg pack` now writes the IF world's
  standard resource container by default, and the short-lived `.arcres`
  zip is retired. Picture id N is Blorb resource `Pict N`, nothing
  translated; `--zblorb STORY` still embeds the story so the whole
  game travels as one file that the Arcturus reference interpreter `Actaea` opens directly, and `proteus` turns it into
  a web page.
- **Restless things, and timers that stop.** Stefan's design, one
  sentence long: work follows the performer's nature, prose follows
  scope. Mark a character `restless` (or arm it mid-story: `now guard is
  restless`) and its `on each_turn` fires every turn wherever it is; the
  thief keeps moving, taking, and scheming offstage, and the system, not
  the author, decides what you hear: what happens in front of you is
  spoken, arrivals and departures included, and what happens rooms away
  is silently discarded. No new concepts, no daemon taxonomy, one
  attribute. And the schedule became author-managed: a timer stops by
  the exact statement that armed it (`stop every 5 turns do
  water_dripping`; the kind and interval must match, so you always stop
  the timer you mean) and `stop all timers` clears the stage for the
  next act. Games without any of it stay byte-identical.
- **Exits are checked at compile time.** A field report from Ichiro
  Ota: a typo'd room name in an exit (`north attic`, no attic declared)
  compiled silently into a runtime "There's no exit in that direction.",
  and an exit naming a plain thing quietly walked the player inside it,
  a pitch-black soft-lock. Both are compile errors now, with the honest
  sentence naming the room, the direction, and the offender. The legal
  targets are what they always were: a declared room, a door, or a
  computed block, with `nothing` as the explicit no-exit.
- **The one honest ask, and verb_trigger.** The verbs overhaul is
  whole: a command whose grammar wanted a noun that was never typed is
  answered by the library, one central line for every verb alike, "The
  verb dance requires you to be more specific." It echoes the verb as
  the player typed it (bare ROLL says "roll", never "push") and no
  longer guesses the missing role the way "Dance what?" did, when the
  grammar may have wanted WITH WHOM. Custom verbs ask exactly like
  standard ones now (a bare WIBBLE used to answer with silence), a
  declared bare grammar line hands the bare command to your handler
  instead, and every game got smaller: forty-odd per-verb ask stanzas
  left the library for the one seam. And the seam is yours too:
  `if verb_trigger is "roll"` inside an `on push` answers each synonym
  in its own voice.

## Feature roadmap

Considered and coming, in no particular order; each lands the Arcturus
way, designed on its own terms, pay-for-use as always.

- **Pathfinding.** One shortest-path engine over the room graph with two
  consumers: player travel (`GO TO <a visited room>`, `FIND <object>`)
  and actor movement, an NPC walking toward a goal one step per turn.
- **An NPC engine.** A summoned granule for living characters: define an
  NPC's movement (patrol routes, pathfinding toward goals), what they
  do and say as they go, where they operate, whether they can open
  doors, and a measure of intelligence in how they act. Builds on the
  pathfinding engine above.
- **Light topology.** Doors and openings that block or pass light, so a
  lit room can spill light through an open doorway and a closed door can
  seal it off.
- **Darkness furniture.** Darkness as a referable thing (EXAMINE
  DARKNESS answers) and EXITS refusing without light. (The status bar
  already shows darkness instead of the room name; the rest of the
  furniture is still to come.)
- **LOOK \<direction\>.** "look north" describes what lies that way.
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
