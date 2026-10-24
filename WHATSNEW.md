# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **Each body its own ways: `as player`.** In a maniacswap game, a
  handler on a character answers for what is done to it; what a body
  does while you drive it is now written on the body: `on jump as
  player`, `on take as player`. It runs only while that character is
  you, so BECOME switches the behavior with the body, and it runs
  first, so a body's limits ("you won't lift anything that heavy") gate
  everything after them. Games without it compile byte for byte as
  before (arcc 2.36.0, Cosmos 1.51.0).
- **Computed values: a number or an object can be a block.** A property
  that was text-only when computed now takes a block returning a number
  or an object, decided when it is read: `reading block` with `return 3`
  in a storm, `return 9` otherwise, while every other gauge keeps its
  plain `reading 7`. Once any object declares a property as a block, that
  property is computed everywhere, at about 3 bytes per read site; every
  other property costs nothing. A property declared only as a block takes
  its type from its returns (arcc 2.35.0).
- **Lists for every verb, and the lid stops the hand.** TAKE APPLE AND
  KEY is now one command with two items, swept and labeled exactly like
  PUT KEY AND APPLE IN VITRINE ("apple: You take the apple with you."),
  no paragraph break between them, stopping at the first refusal; a
  verb after "and" still chains. And a shut lid now stops every touching
  action, not only TAKE: a closed clear vitrine shows its lantern and
  SWITCH ON answers "You'll have to open the vitrine first."; EXAMINE
  still looks. Container games reprice; games without an openable
  container are byte-identical on the gate (arcc 2.30.0, Cosmos 1.49.0).
- **A performed direction rides `way` for any action.** The vehicle
  redirect, "while aboard, a bare direction means driving", is one
  handler: `on go` with `perform("drive", cart, way)`. The direction
  used to ride `way` only for go and was cleared for every other
  action; now a direction-typed argument reaches `way` whatever the
  action, the object staying the noun, so a verb with a `direction`
  grammar line receives a performed direction exactly as a typed one.
  Games without such a perform compile byte for byte as before (arcc
  2.29.0, Cosmos 1.48.0).
- **The game's own say in a tie: `prefer`.** Three coins answer to
  "coin", and PAY COIN asked which although the story knew the fare
  was the florin. A game now overrides the `prefer` seam, a block the
  matcher asks once per tied candidate with `action` already set:
  answer true for the one the story means and it is bound silently,
  after a typed trigger and before the held tiebreak. None or several
  preferred leave the question as it was. Games that leave the seam
  alone compile byte for byte as before (arcc 2.28.0, Cosmos 1.47.0).
## Feature roadmap

Considered and coming, in no particular order; each lands the Arcturus
way, designed on its own terms, pay-for-use as always.

- **Darkness furniture.** Darkness as a referable thing (EXAMINE
  DARKNESS answers) and EXITS refusing without light. (The status bar
  already shows darkness instead of the room name; the rest of the
  furniture is still to come.)
- **Question preservation.** A disambiguation question survives an
  interposed command: asked "which coin?", the player may take inventory
  first and then answer.
- **Local spill.** A Z-machine routine holds at most 15 locals, parameters
  and `let`s together; today the compiler refuses an over-full block with a
  clear error and the cure (move part of the work into a helper block).
  Spilling the excess to the stack automatically would lift the ceiling
  without the author ever noticing. Fifteen is a lot, but someone will hit
  it sooner or later.
