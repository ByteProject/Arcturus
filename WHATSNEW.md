# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Darkness done right.** Arcturus now follows the modern darkness model:
  in the dark you can still feel what you carry, so INVENTORY lists your
  possessions, but seeing detail needs light, so EXAMINE and READ refuse
  with the too-dark message, and the two can never disagree because read
  maps onto examine. Coming from Inform 6, PunyInform, or Dialog this is
  a behavior change worth reading up on (docs/02, section 6); Inform 7
  behaves the same way, and its darkness rules translate almost 1:1 into
  a single Arcturus handler header: `on inventory when is_lit is false`.
- **Directions are values everywhere.** A catalog holds a fixed route
  (`catalog escape_route` with `north / east / up` lines), a matrix `of
  direction` holds a mutable one (a patrol path that grows), and saying
  any direction value speaks its word: `say "${entry(route, 1)}"` prints
  north, exactly as an object entry prints its name. Comparisons
  (`is north`), switch cases, iteration, and `exit_dest` all work on
  them, and a global can alias a whole catalog or matrix by name.
- **The dispatch chain, hardened.** An object's `on other` catch-all now
  outranks its kind's specific handlers, exactly as both reference
  documents always specified: the react dispatcher runs owner by owner,
  each owner's specific handlers before its own catch-all, the instance
  before its kinds. And blocks may now have EMPTY bodies: a named seam
  another layer overrides, free until claimed, which is how the status
  bar learned to rise before `on start` prints its first word.
- **The ring decode architecture.** Every retro picture stream now
  carries a hard guarantee: no compression back-reference reaches beyond
  2048 bytes, at zero measured cost on the corpus. In exchange, a
  loader needs only a 2K ring in main RAM and can decode straight to the
  screen, byte by byte, with no staging buffer at all: the memory
  posture a 64K machine running a Z-machine interpreter actually has.
  The Commodore 64, ZX Spectrum +3, and Amstrad CPC reference loaders
  are rebuilt on it and verified byte-exact against emulator memory,
  and the two reference decoders (Z80 and 6502) are executed against
  the whole corpus in the test suite on every run.
- **A fifteenth target: TRS-80 Model 4.** The first arc_image target
  whose interpreter lives outside our family, requested and built for by
  the community. The hi-res board is 640x240 monochrome, so the
  converter buys quality with resolution: the master doubles
  horizontally, a contrast stretch anchors the tonal range, and ordered
  dithering runs at the full 640 grid. One bitmap section, ring-decoded
  through three ports; the whole 21-picture corpus ships converted, and
  the reference probe is verified against emulated video memory.

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
  today lists work in single-noun actions only), DROP ALL as the one
  all-form worth having (taking all stays a deliberate granule, putting
  all has no case), and maybe CONSULT <object> ABOUT <topic>, which
  ties into the topic machinery we already have.
- **Question preservation.** A disambiguation question survives an
  interposed command: asked "which coin?", the player may take inventory
  first and then answer. In the same breath: likelihood hints, letting a
  verb or object mark an interpretation as unlikely so disambiguation
  picks well before it has to ask at all.
