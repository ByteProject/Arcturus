# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **The game's own say in a tie: `prefer`.** Three coins answer to
  "coin", and PAY COIN asked which although the story knew the fare
  was the florin. A game now overrides the `prefer` seam, a block the
  matcher asks once per tied candidate with `action` already set:
  answer true for the one the story means and it is bound silently,
  after a typed trigger and before the held tiebreak. None or several
  preferred leave the question as it was. Games that leave the seam
  alone compile byte for byte as before (arcc 2.28.0, Cosmos 1.47.0).
- **The body you begin in has a name: `body`.** In a maniacswap game
  the player was always a pointer and the bodies characters, except the
  one you started in, seeded under the name `player` and nameless the
  moment you left it. Now the game block says `body henrik` (or `body
  demon`), the boot body is a character you declared, and everything a
  story needs follows: `if player is henrik`, `move henrik to nothing`,
  `become(henrik)`, starting as any body by declaration. The old form
  keeps compiling (arcc 2.27.0, Cosmos 1.45.0).
- **Which Smith? Topics that share a word.** ASK ABOUT SMITH with a John
  and a Mary no longer runs whichever was declared first. The words
  decide where they can (JOHN SMITH is John), an umbrella topic for the
  bare word answers in the character's own voice (the author's tool),
  and a cold tie is asked as dialogue, `The troll: "John Smith, or Mary
  Smith?"`, offering only the topics the player has been told about; the
  next line answers it or simply runs as the next command (arcc 2.26.0,
  Cosmos 1.44.0).
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
