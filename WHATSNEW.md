# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

- **The whole machine park, one command.** `arcimg convert art/ --all
  -o out/ --preview previews/` converts every master for every retro
  machine at once: one folder per target (out/c64/, out/ami/,
  out/zx3/, ...), a pixel-exact preview folder beside each, per-class
  master selection (masters-broad/) and the Spectrum colour path
  applying per target as ever, and machines whose converter is still
  to come reported once and skipped. Preparing sources got simpler
  too: a file named 1.png IS picture 1, and art already at a band
  size keeps its shape (arcimg 2.3.1).
- **Say I: first-person narration.** One constant in your game,
  `constant first_person = 1`, and the whole English library narrates
  as I: "I take the lamp with me.", "I'm carrying:", every listing,
  report, and refusal, the extended verbs included. The system voice
  deliberately stays second person (the parser's clarifying questions
  and the quit and death prompts talk to the player at the keyboard,
  not the narrator), any single line is still yours to override by
  declaring its block, and a second-person game compiles byte for
  byte as before (arcc 2.16.0, Cosmos 1.36.0).
- **Touch is the default: the reach gate moves into the house.** Every
  action now honors `beyond` centrally, before any handler runs: a new
  verb refuses what is out of reach with zero gate code, an object's
  own overrides never explain a thing the player could not have
  reached, and the audit's forgotten holes (SET, TIE, KISS, CLIMB,
  DRINK, DIG, SEARCH on unreachable things) are closed for good. A
  verb whose meaning works at any distance declares it beside its
  grammar: `reachagnostic`, bare or per slot (SHOW's far person,
  THROW's target). With `success` speaking the report through the
  alter gate, a complete verb with full library manners is now three
  lines. Games that never set `beyond` compile byte-identical
  (arcc 2.2.0, Cosmos 1.20.0).
- **Arcturus 2.0: the parser stops searching and starts knowing.** The
  compiler now ships a word-to-owners index in every story file: each
  vocabulary word points at the few objects that own it, so the noun
  matcher scores a handful of candidates instead of sweeping the whole
  object table. Measured cycle-exact on 8-bit hardware profiles, verb
  turns run 3 to 6 times fewer instructions (TAKE in Hibernated 2:
  10,272 down to 1,733), landing below PunyInform's counts on the same
  commands, with movement and printing already faster. Nothing changes
  in your source and nothing is declared; games grow by a few hundred
  bytes and answer like they mean it on a C64 (arcc 2.0.0,
  Cosmos 1.18.0).
- **Machines you can type at: typed input slots.** A verb's own
  grammar line now declares what a machine accepts: `speak letters to
  noun` matches letter words only (SPEAK FRIEND TO DOOR, the
  Hibernated 1 codeword shape), `set noun to number` one all-digit
  word (SET DIAL TO 3), `type anychar into noun` anything at all, and
  the matcher enforces the class, so one verb can route by input kind,
  and wrong-kind input is refused in the machine's own name ("The dial
  only accepts numbers.", overridable).
  No vocabulary is declared anywhere, and the input reads back under
  the slot's own name: `if letters is "xanadu"`, `${letters}` echoed
  verbatim in your refusals, `number` as a plain value. A dial is one
  handler and an if. Works in all three languages out of the box
  (arcc 1.14.4, Cosmos 1.17.4).
## Feature roadmap

Considered and coming, in no particular order; each lands the Arcturus
way, designed on its own terms, pay-for-use as always.

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
