# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Foresight's second act.** Doors and containers join the repairs: a
  closed, unlocked door opens itself on the walk, and naming a thing you
  know is inside a closed container opens the container and carries on,
  chaining when it must: "(opening the clear jar first)", "(taking the
  pearl first)", then the give you actually typed. The same promise rule
  holds at every step, locked things stay honest refusals, and contents
  you have never seen cannot even be named. In the same release the
  input buffers doubled (long chained commands stopped dying mid-word)
  and Actaea's caret learned to stay on the input line.
- **The session verbs, and a wink.** VERSION prints the banner mid-game,
  the bug-report command, always in. NOTIFY brings the classic
  "[Your score has just gone up by 5.]" bracket line: off by default, the
  author enables it in `on start`, the player toggles it, and the two are
  coupled, enabling the feature anywhere brings the verb along, while a
  game that never touches it has no lines, no verb, and not even the
  dictionary word. And the oldest Easter egg in the medium finally
  answers: a player who curses gets a dry line back, selectable as the
  `swear` family.
- **Push the crate north.** A thing marked `shiftable` (Stefan's word)
  rolls through the exit with you: doors respected, the same arrival a
  walk gets, and the crate is there when the room is described. Anything
  unmarked answers that it will not shift; games with nothing shiftable
  pay nothing. PICK UP THE LAMP arrived in the same pass, the everyday
  take phrasing in all three languages, and it never mistakes itself for
  boarding something.
- **Noun lists reach the two-noun verbs.** "put coin and nail in box"
  now does what it says: the box is bound once, each item runs as its
  own full turn reported by name ("gold coin: Done."), the list stops at
  the first refusal like any chained line, and the verb contract guards
  every item. The "and" still chains when a verb follows it, and
  single-noun lists ride the chain's verb borrow untouched.
- **Grammar surgery, said out loud.** `enhance verb "look"` grows the
  standard LOOK with your new lines and keeps everything it had;
  `redefine verb "read"` replaces a family whole, words included. The old
  way, redeclaring the verb, shadowed it word by word and quietly left
  the other synonyms on the old grammar; it still compiles, but the
  compiler now tells you what it is doing and names the two forms that
  say what they mean. The shipped examples now use them, and two relic
  declarations from before their verbs joined the standard set simply
  went away.

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
- **The verbs overhaul** (underway; the `text` grammar slot, the verb
  contract, foresight, verbs by the slice, enhance/redefine, noun lists
  in two-noun actions, CONSULT ABOUT, typed YES/NO, and LIGHT have
  landed, shiftable pushes things between rooms, the session verbs
  (VERSION, the coupled NOTIFY, the swear family) closed the roster,
  and doors and containers joined foresight's repairs). The overhaul
  is complete.
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
