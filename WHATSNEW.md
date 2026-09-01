# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

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
- **Carrying, three ways.** Declare nothing and the player carries
  everything, as before. `constant item_cap = N` is the classic item
  limit, now counted honestly: what is inside a carried sack counts,
  a loaded box is priced as it is lifted, and rearranging what you
  already carry is never refused; `global carry_limit = N` is the same
  limit movable at run time, and containers can carry their own
  ceiling (`item_cap 3` on a box, bottomless without it). And
  `summon.carryweight` prices mass instead, the tradition of the PAW
  school: things weigh (`weight 2.1`, half a unit if unsaid), the
  player carries a budget (10.0 unless you set one), a count and a
  budget enforce side by side, and the unit is a label an author can
  turn into pounds with one overridden block. `box.item_count` and
  `box.totalweight` read like properties and are computed on demand
  (arcc 1.14.0, Cosmos 1.17.0).
- **Actaea 2.0: a massive overhaul of the reference interpreter.**
  Three selectable looks, set in a selected serif, a clean, and a
  retro typeface. Long passages page with [MORE] instead of scrolling
  past unread. Two window shapes, the portrait Modern (4:5) and the
  classic 4:3, and the window remembers its size, position, and
  settings between sessions. `actaea --install-app` installs it as a
  native application on the host system, macOS, Linux, or Windows,
  while it stays fully accessible from the command line, and
  `arcc --update` continues to update everything in place when the
  tools are kept together (Actaea 2.0.0, Cosmos 1.16.4).
- **Multiple player characters: maniacswap.** `summon.maniacswap`, mark
  each body `playable`, and BECOME swaps the keyboard between them,
  Maniac Mansion style, from anywhere, even between maps that never
  connect. The body you leave freezes exactly where and as it was,
  holding its own inventory, listed in its room like anyone standing
  there; the mind (score, turns, every global) travels. ME and MYSELF
  follow the keyboard in all three shipped languages (WERDE and ENCARNA
  come along), and the story gates every swap in fiction with an
  ordinary handler on the body ("Not without the signal."). Beside the
  NPC engine it composes on one shared word: the engine never drives a
  frozen PC nor the body you are riding. Games that never summon it
  compile byte-identical, and the proof of that hunted down a one-byte
  compiler subtlety along the way (arcc 1.13.0, Cosmos 1.16.0).
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
