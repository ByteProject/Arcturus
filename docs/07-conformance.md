# Arcturus Conformance

What "conformant" means for this project, the evidence that the compiler meets
it, and the size record that evidence protects. The charter is docs/00 (sections
2 and 5); the backend mapping the claims below rest on is docs/04. This document
records the state as of arcc 0.8.0 / Cosmos 0.11.0 (2026-07-03) and is updated
whenever the conformance evidence changes.

## 1. The conformance claim

Arcturus emits standard Z-machine story files, version 5 by default and version
8 with `--zversion 8`, as specified by the Z-Machine Standards Document 1.1. The
compiler uses no custom opcodes, no interpreter extensions, and no nonstandard
header fields; a generated story runs on any conformant interpreter. (The
`arc_image` graphics path, milestones B11 to B12, will be introduced behind an
EXT capability check so that the same story file still runs unchanged on
interpreters without it; nothing in the current compiler emits it.)

The two image-level differences between the z5 and z8 targets are exactly the
ones the standard defines: the header version byte, the file-length scale (a z8
length is stored divided by 8 rather than 4), and the packed-address unit (8
rather than 4). Codegen is otherwise identical (docs/03, the `--zversion` flag).

## 2. The golden games

The two worked games from the syntax reference (docs/01 sections 18 and 19) are
the conformance anchors:

- The Brass Lantern (`examples/brass-lantern.storyarc`)
- Cloak of Darkness (`examples/cloak-of-darkness.storyarc`)

Both must compile, be winnable start to finish on a reference interpreter, and
stay under their PunyInform-equivalent size. All three requirements are enforced
by the test suite on every run, not checked by hand.

## 3. The evidence

The suite (355 tests at this writing; `python3 -m pytest`) drives generated
stories end to end on Frotz (dfrotz). What runs on a real interpreter, per run:

- Full winning walkthroughs of both golden games, z5; Cloak of Darkness also as
  z8 (`tests/test_examples.py`).
- The meta layer: a Quetzal save and restore round trip, undo (including
  nothing-to-undo), restart with confirmation, again/g, and oops for both noun
  and verb typos (`tests/test_meta.py`). Save, restore, and undo use the
  standard opcodes (`save`, `restore`, `save_undo`, `restore_undo`); the file
  format is the interpreter's own Quetzal.
- The upper window and styles: the status line granule's cell-addressed bar
  (`tests/test_statusline.py`), and the conversations menu pinned in the upper
  window (`tests/test_conversations.py`).
- The language packs: Spanish and German games with accented output and both
  accented and ASCII-fallback typed input (`tests/test_language.py`); accents
  encode to the ZSCII default extra character set (Standard 1.1 section 3.8.5,
  codes 155 to 223, `arcturus/zstring.py`), never to raw Unicode, so they render
  on 8-bit interpreters as well.
- Scope, containers, doors, spans, grains, daemons, topics, and the rest of the
  library behavior, each with its own interpreter-driven test file.

Interpreters beyond Frotz are out of the repository's scope by design: releases
are additionally hand-verified by the author on his own Standard 1.1
interpreters for retro targets (C64, Amiga, Atari ST, and others), and milestone
B10 adds Actaea, an in-repo reference interpreter with CZECH, Praxix, and
TerpEtude as its own gates (docs/06).

## 4. The size record

Smallest possible z-code is a charter objective, judged alongside correctness
(docs/00 section 5). The current golden-game numbers (2026-07-03):

| Story | Bytes | Benchmark |
|-------|-------|-----------|
| Cloak of Darkness, z5 | 14520 | PunyInform-equivalent build: ~27K |
| Cloak of Darkness, z8 | 14944 | same game, version 8 |
| The Brass Lantern, z5 | 14000 | no published equivalent |

The 11792-byte Cloak built at the close of the size pass (B6) is, to our
knowledge, the smallest runnable Cloak of Darkness for the Z-machine
registered to date. The current build is larger because the parser has since
gained command chaining, full disambiguation (scored noun matching and the
"Which do you mean" ask), and noun lists with the noise words they need, as
core features every game carries; it still comes
in at roughly half the PunyInform benchmark. Features beyond the must-have
core stay out of that fixed cost: they ship as summonable granules
(docs/05), the pay-for-use rule. These numbers, and a ceiling for
every shipped example, are enforced by `tests/test_sizes.py`: a build that grows
past its ceiling fails the suite, and a ceiling may only be raised in the same
commit as the change that grew it, with the growth explained. When an
improvement shrinks a story, the ceiling is lowered to lock the win in.

## 5. Known boundaries

Stated plainly, so nobody reads more into the claim than it says:

- Attributes are capped at 48 per the v5 object format; the standard boolean
  properties and the kind bits use 28, and attribute spill (packing overflow
  attributes elsewhere) is not implemented. A game that declares more than the
  remaining 20 booleans and kinds fails with a clear compile error. Revisited
  when a real game needs it (B8).
- The dictionary truncates words to nine Z-characters (six bytes), as the
  standard prescribes; words sharing a nine-character prefix collapse to one
  entry, which is standard behavior and has not yet mattered in practice.
- Characters outside ZSCII and the default extra character set are not
  supported, by design; the extra set covers the shipped languages (English,
  Spanish, German) and most of Western Europe.
- Sound, mouse input, and the version 6 screen model are out of scope; the
  compiler targets versions 5 and 8 only.
