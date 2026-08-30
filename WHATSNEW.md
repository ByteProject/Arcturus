# What's new in Arcturus, and the feature roadmap

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log. The feature roadmap follows below.

## What's new

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
- **The NPC engine: living characters, declared instead of hand-wired.**
  `summon.npcengine` and a character can `patrol` a route of rooms
  (opening doors on its way with `opens_doors`), wander a `territory`
  (rooms, or a whole room kind), or be sent on an errand
  (`send(verger, chapel)`) that walks the real room graph one honest
  step per turn, doors and all. The player watches it happen: "The
  watchman heads east.", "The watchman arrives from the west.", in all
  three shipped languages. The controls make a large cast cheap on real
  8-bit hardware: every character starts `hibernated`, inactive at zero
  per-turn cost, until `resume(watchman)` wakes them; the same calls on
  `npc_engine` itself are a master gate that freezes the whole town for
  a cutscene and restores the exact mix after. Two events ride the
  ordinary pipeline (`npc_arrives`, `npc_blocked`), and the classic
  addressed imperative arrives with it: WATCHMAN, GO NORTH reaches the
  character's own `on command`, which decides; the default politely
  refuses. Games that never summon it compile byte-identical, proven
  file by file (arcc 1.12.0, Cosmos 1.15.0).
- **arc_image is finished: sixteen machines, every one proven on the
  metal.** The retro graphics path is complete. One band-shaped master
  painting converts to the native format of sixteen machines, from
  the Amiga and the ST down to the C64 and C128, Spectrum, CPC,
  Plus/4, MSX1 and 2, Atari 8-bit, TRS-80 Model 4, Apple II, Agon
  Light, Spectrum Next and MEGA65, and every one of them carries a
  reference loader verified pixel-perfect on accurate emulation. The
  last round closed the hardest three: the Spectrum Next and the
  MEGA65, where the conversion turns out to be the
  IDENTITY (their palettes reach the master exactly, so the art
  arrives untouched), and the Apple II, where color is not a palette
  at all but an artifact of the NTSC signal, solved by a dynamic
  program that chooses each of the 560 dots per scanline so the
  decoder's own four-dot window shows the painting, reaching hues
  between the machine's sixteen. Authors paint once; arcimg derives
  the rest (arcimg 2.0.0).
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
