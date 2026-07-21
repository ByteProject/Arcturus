# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **The screen the game is actually on.** Actaea told every game it was
  running on an 80-column screen, whatever screen it was really running on,
  so a status bar in a wider terminal stopped at column 80 and left a notch
  beyond it. The terminal front-end now reports its true width and height,
  a resize reaches the game with the next thing it draws, and the bar
  reaches the edge at any size. This matters beyond one interpreter: a
  status bar is written once and has to fit a 40-column home computer and a
  132-column terminal alike, so what it spans has to be the truth.
- **Conversations, rebuilt.** The five ways to address a character are now
  five different things. ASK ABOUT and TELL ABOUT reach a character's
  topics, and one topic can answer each differently; ASK FOR is its own
  act at last, a request rather than a question; GIVE and SHOW stay
  ordinary actions on the thing in your hand. Characters that discuss the
  same matter share one `subject` declaration, so the words a player might
  type live in one place for the whole cast instead of being copied per
  character, and an `idle` topic gives a character its own default answer
  when nothing else fits. Underneath all this sits a new `text` grammar
  slot, which absorbs the words of a subject without trying to resolve
  them into an object, because what you ask about is usually not a thing
  you can point at. That slot is the first real piece of the grammar work
  to come.
- **Pictures travel as Blorb.** Blorb is the container the interpreter
  world already knows, so supporting it removes a step for anyone adding
  arc_image to an existing interpreter. Beside the `.arcres` pack, which
  stays exactly as it is, `arcimg` now writes plain Blorb for the pictures
  and `.zblorb` with the story embedded, one file holding a whole
  illustrated game. The mapping cost nothing, because a picture id and a
  Blorb resource number are the same idea. Actaea reads both, and every
  Blorb declares up front whether a game wants a picture band, so an
  interpreter can decide before it runs a single instruction.
- **Knowing what was tried.** `action` reads the action a turn is running,
  and compares against a plain action name: `if action is touch`. It earns
  its keep in the two places that answer many verbs at once, an object's
  `on other` catch-all, which could never say what you had attempted, and
  a grain that answers several verbs and wants a different line for each.
- **Search that actually searches.** SEARCH used to shrug at everything.
  Now it tells you what is there and makes findable what was not: living
  people still rebuff you, sealed containers still refuse, open ones list
  what they hold, and a knocked-out guard's pockets give up their contents
  onto the floor where you can pick them up. The whole recipe for a
  lootable body is to clear `animate` and put the loot inside.

## Feature roadmap

Considered and coming, in no particular order; each lands the Arcturus
way, designed on its own terms, pay-for-use as always.

- **Inference (implicit actions).** Open a closed container before
  looking inside it, open the door before walking through: the game
  infers the obvious preparatory action instead of refusing and making
  the player type it. The exact Arcturus shape is decided when we reach
  it.
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
  DARKNESS answers), EXITS refusing without light, and the status bar
  showing darkness instead of the room name, because naming an unseen
  room is a spoiler.
- **LOOK \<direction\>.** "look north" describes what lies that way.
- **The verbs overhaul.** Retire the all-or-nothing extended verbset:
  opt into individual documented verbs with a one-liner, each with its
  grammar documented; let authors ADD to a verb's grammar or REPLACE it
  wholesale. In its scope besides the breadth (taste, tie, throw at,
  push things between rooms, and friends): declarative per-verb
  requirements (whether a verb needs its noun reachable or merely
  visible), noun lists in two-noun actions ("put coin and nail in box";
  today lists work in single-noun actions only), and maybe CONSULT
  \<object\> ABOUT \<topic\>, which ties into the topic machinery we
  already have.
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
