# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **The parser learns parts of speech, and German gets its depth round.**
  A field-report round on the German IF forum ended as the biggest parser
  upgrade since the verbs overhaul, and the fundamentals serve every
  language: a `words` entry marked `>red` is an ADJECTIVE, and matching
  ranks in Infocom's ZIL classes (adjective plus noun over noun over
  adjective alone), so EXAMINE RED with two red things asks the honest
  "Which do you mean, the red couch or the red guitar?" while a lone
  adjective still finds its object; a `#trigger` word settles
  synonym-overlap ties silently; switch state is library-owned now
  (`binary`, with honest already-on/off refusals and light coupling);
  and language packs declare their own orthography folds and multi-role
  pronouns. German cashes all of it in: declare `words tür` once and
  "tuer" types (the fold table), one adjective stem carries every
  declension (`>rot` matches rote, roten, roter, rotes, rotem), "ihm"
  reaches masculine and neuter, "sie" feminine and plural, "ihnen"
  exists, and the pronominal adverbs damit, darauf, darin, daran bind
  the last thing mentioned. Games using none of it compile
  byte-identical (arcc 1.5.0 to 1.10.0, Cosmos 1.8.0 to 1.13.0).
- **Actions without verbs, and a sweep you can hook.** A bare
  declaration, `action take_all, drop_all`, names an action with no
  verb attached: it joins the ordinary action numbering, so handlers
  at every level, `when` clauses, `action_id`, and `dispatch` all
  work; only the keyboard cannot reach it until your code routes the
  player there. The takeall granule is the first rider: TAKE ALL and
  DROP ALL now dispatch through the standard pipeline before
  sweeping, so `on drop_all when here is shrine` vetoes the sweep in
  one room, a container answers TAKE ALL FROM with its own handler,
  and `continue` defers to the sweep. An adopter's question, answered
  at the language level (arcc 1.4.0, Cosmos 1.7.0).
- **Pictures reach every 8-bit screen, probe-proven.** The retro side
  of arc_image is complete through the MSX family and the Agon Light:
  one master painting converts to fifteen native formats, and twelve
  of them (Amiga, Atari ST, DOS, C64, Spectrum +3, CPC, Plus/4, Atari
  8-bit, TRS-80 Model 4, MSX1, MSX2's sixteen colors from 512, and
  the Agon's sixty-four) carry reference loaders verified
  pixel-perfect on accurate emulation. The
  committed corpus under arc_image/ is the shop window: what you see
  in the previews is exactly what the current converter produces, on
  every machine, including the Spectrum's deliberate black-and-white
  art beside Stefan's own hand-painted originals.
- **The room lists its things in one sentence.** "You can see a MRE, a
  lantern and a backpack here.", the classic idiom, instead of a line
  per item: every plain item joins one combined sentence, with the
  closed qualifier and a holder's contents riding along inline ("a pine
  box (closed)"). Things with their own `appearance` or unexpired
  `intro` keep their own paragraphs above it, exactly as before. All
  three shipped languages speak it natively, German with its accusative
  intact ("Du siehst hier eine Laterne, einen Rucksack und eine
  Brotzeit."), and a game that overrode `list_item` keeps its wording
  for the single-item case. An adopter request, and the standard
  behavior now (Cosmos 1.5.0).
- **Pathfinding: GO TO, FIND, LOOK <direction>, and the way family.**
  `summon.pathfinding` and the player can GO TO any room they have
  visited, by name and with no declarations (a room's name words become
  its vocabulary; `words` on a room overrides). FIND walks to a thing
  you know of; LOOK NORTH answers what lies that way, leading with the
  direction as typed, so it composes with the nautical granule ("Aft
  lies your cabin."). Knowledge is the visited set: unvisited places
  are as unknown as places that do not exist, and no route leads
  through rooms you have not seen or doors that stand closed. Every
  step of a walk is a real turn (daemons and clocks run; one breadcrumb
  line per room passed), one UNDO takes back the whole walk, and the
  walk yields the moment the world pushes back. Beneath the granule,
  the engine is core library, callable with no summon from any handler:
  `way_between(a, b)` for adjacency, `way_toward(a, b)` for the first
  step of a shortest path (an NPC walking toward a goal is one call per
  turn), the `door_bars` and `path_admits` seams for doors and rooms
  that play by their own rules, and the `no_way` constant, so 0 stays
  honest north forever. Unused, all of it folds away to the byte.
## Feature roadmap

Considered and coming, in no particular order; each lands the Arcturus
way, designed on its own terms, pay-for-use as always.

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
