# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

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
- **The picture follows the scene, and darkness is a scene too.** A
  room's picture is no longer fixed at compile time: `arc_image` is an
  ordinary property, so opening the door can swap the gatehouse picture
  for the open one, and the band repaints the same turn, no LOOK needed.
  And a game with both pictures and darkness now declares `arc_image_dark`,
  the picture the band shows in the dark; the compiler refuses to build
  without it, because the alternative was the previous room's picture
  hanging over a room you cannot see. The band also repaints honestly
  after UNDO, RESTORE, and RESTART, which used to be able to strand a
  picture the rewound world never drew. In the same spirit the status bar
  stops naming an unseen room, saying "In the dark" instead (the German
  and Spanish packs carry their own idiomatic lines). None of this costs
  a byte in a game without pictures, or an always-lit game its bar bytes.
- **A terminal that keeps its screen.** Two things went wrong when you
  resized Actaea's terminal window. The game was never told the screen had
  changed, so a status bar stayed at whatever width it started with, and
  everything already printed vanished, trickling back only as you kept
  playing. Both are fixed: the game is told the terminal's real size, at
  startup and after every resize, and the console now keeps its own record
  of what the story printed and repaints from it, re-wrapped to the new
  width. A screen the story cleared on purpose stays cleared. This matters
  more than it sounds, because a status bar is written once and has to fit
  a 40-column home computer and a 132-column terminal alike.
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
- **The verbs overhaul** (underway; the `text` grammar slot and the verb
  contract have landed). Still to come: foresight, the summonable
  implicit-action granule ("(taking the pebble first)") built on the
  contract, with a probe that never promises what it cannot deliver
  (doors and containers join the repairs when travel meets it);
  pay-per-verb selection on the extended verbset (`summon.extendedverbs
  squeeze, burn, search`); `enhance verb` and `redefine verb` for adding
  to or replacing a verb's grammar out loud; noun lists in two-noun
  actions ("put coin and nail in box"; today lists work in single-noun
  actions only); maybe CONSULT \<object\> ABOUT \<topic\>, which ties
  into the topic machinery we already have; and the breadth (taste, tie,
  throw at, push things between rooms, and friends).
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
