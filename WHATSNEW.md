# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

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
- **Foresight.** `summon.foresight` and the game does the obvious step
  for you: GIVE APPLE TO STACY with the apple at your feet prints
  "(taking the apple first)" and gets on with it. The parenthetical is a
  promise, and it only prints when the promise is certain: the repair
  asks the take's own guard chain first, so an unreachable thing refuses
  plainly instead of promising and then failing, the little embarrassment
  every Inform player knows. Off unless summoned, because implicit
  actions are a matter of taste; the whole exchange is one UNDO; and each
  language pack speaks its own parenthetical.
- **Verbs got a contract.** A verb now states what it requires of its
  operands, `requires noun carried`, `requires second animate`, and the
  library enforces it before any handler runs. The field report behind it
  was an `on give,show` override that answered for gibberish and for gifts
  the player did not hold, because overriding the response used to mean
  accidentally overriding the validation too. No longer: GIVE and SHOW
  declare a carried gift and an animate recipient, your handler fires only
  on turns that make sense, and your code does not change. Requirements
  live on the action, so German and Spanish games inherit them without a
  word, and requirement kinds no verb in the game uses are not
  even compiled. This is the
  foundation the coming foresight granule repairs failures on, "(taking
  the pebble first)", instead of refusing.

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
  landed, and shiftable now pushes things between rooms; doors and
  containers join foresight's repairs when travel meets them). Still
  open: the last word-roster rulings (notify, version, profanity).
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
