<p align="center">
  <img src="artworks/arcturus_artwork.png" alt="Arcturus" width="860">
</p>

# Arcturus

**Arcturus is a programming language and compiler for the Infocom Z-machine.**

It is a high-level, readable language for writing interactive fiction: text
adventures in the tradition of *Zork* and the modern works that still run on the
Z-machine. You describe a world (rooms, things, verbs, and the behavior that
hangs off them) and the compiler produces a standard Z-machine story file that
plays on Frotz, Ozmoo, Eris, Vezza and other interpreters, old and new.

Arcturus is designed and written by **Stefan Vogt**. The compiler is written in
Python and depends only on the standard library, so it runs anywhere Python
does, with nothing to install. The standard library, **Cosmos**, is written in
Arcturus itself and ships as editable source rather than a black box.

The name is a star, Arcturus, and the narrative arc every story is built on.

## Philosophy

Arcturus is built for one thing and built for it well: writing modern adventure
games for the Z-machine. It gives authors the constructs they actually reach for
(rooms and things and kinds, containers and doors, scope and light, an NPC
conversation model, daemons and timers, computed descriptions, multi-room
scenery), each as clean syntactic sugar, so the common cases are short, readable,
and hard to get wrong. This is a complete, powerful core, and Arcturus is its own
language, not a dialect of any other.

Cosmos, the standard library, is editable Arcturus source you own outright: read
it, override any behavior, and reshape it to your game rather than work around a
black box. Optional and specialized features are granules you summon, present only
where a game wants them and costing nothing where it does not. And because
Arcturus owns its whole pipeline (the compiler, the library, and the interpreter),
it can be this expressive and still compile small, with whole-program optimization
trimming every build to exactly what the game uses.

## Project status

Arcturus is in **active development**. It is not at a 1.0 release yet, but it
already compiles complete, playable games. The two worked examples - **The Brass
Lantern** and the classic **Cloak of Darkness** - compile with the standalone
`arcc` and are winnable start to finish on Frotz, with the entire Cosmos runtime
(turn loop, movement, verbs, scope and light, the parser, and scenery) written in
Arcturus itself.

The road from here, milestone by milestone:

- **Done:** the language spec; the compiler (lexer, parser, semantic analysis,
  Z-machine code generation); and a feature-complete Cosmos written in Arcturus
  itself - the full standard verb set, the meta verbs (score, save, restore,
  undo, again, oops), an original standard message set, kinds and inheritance,
  the container knowledge model, computed properties, daemons and timers, doors
  (including two-sided doors) and multi-room scenery, the `topic` conversation
  model, and the summonable granules: extended verbs, an opt-in status line,
  verbose exits, a menu-driven conversation system, and debug verbs. The size
  pass is complete: whole-program dead-code elimination, abbreviation-based text
  compression (a baked-in default plus an opt-in per-game pass), and dense code
  generation, all built into the compiler so every build is trimmed with nothing
  to configure, and optional features cost nothing when a game does not use them.
  Both example games play end to end, and Cloak of Darkness compiles to about
  12K with the whole modern Cosmos library linked in and nothing stripped out.
- **Also done: language packs.** Spanish and German are full members of
  Arcturus: the verbs, direction words, articles, and every message translated,
  with correct accents (and a plain-ASCII form for every word the player must
  type, since an 8-bit keyboard cannot enter them). Spanish
  (`summon.language "spanish"`) derives grammatical gender automatically
  (`una lámpara`, `el libro`, agreement like `la caja está abierta`). German
  (`summon.language "german"`) has three genders and no spelling rule, so the
  author declares the article (`der`, `die`, `das`) on the object, and the
  article then inflects for case in the messages (`du nimmst den Schlüssel`, `in
  der Truhe`) with no further work; separable verbs parse naturally (`schalt
  die Lampe an`, `schliess die Tür auf`). Worked examples:
  [examples/ejemplo-espanol.storyarc](examples/ejemplo-espanol.storyarc) and
  [examples/beispiel-deutsch.storyarc](examples/beispiel-deutsch.storyarc).
- **In progress:** porting Hibernated 2, the first full-length game and the
  maturity milestone. The port's first fruits are already in the toolchain:
  Z-machine colours as first-class syntax (`zcolor`, `say.yellow "..."`), the
  Trinity-style quote box (`summon.quotes`), banner control for pregame
  preludes, and a compile-statistics ledger after every build, watching the
  story's use of each Z-machine ceiling.
- **After that:** Ghosts of Blackwood Manor; then a modern reference
  interpreter, the `arc_image` graphics path (modern systems first, then the
  8-bit and 16-bit retro machines), and porting The Curse of Rabenstein.
  Reaching 1.0 is tied to those ports.

Follow this section and `PROGRESS.md` for where things stand.

## The language

The authoritative language definition is the syntax reference, which is enough
to start writing Arcturus today:

- [docs/01-syntax-reference.md](docs/01-syntax-reference.md): the language.
  Grammar, every construct, and two complete worked example games.
- [docs/02-cosmos-and-parser.md](docs/02-cosmos-and-parser.md): the runtime.
  The Cosmos library, the parser, the action pipeline, scope, light, and the
  turn loop.
- [docs/05-granules.md](docs/05-granules.md): the summonable granules. How to
  summon them, how to fork one, and how to write your own.

For the curious who want to see under the hood, two further documents cover how
the compiler itself works:

- [docs/03-compiler-pipeline.md](docs/03-compiler-pipeline.md): the compiler.
  The pass pipeline, the command-line interface, how Cosmos is bundled and
  overridden, the single-file distribution, and the version model.
- [docs/04-codegen-mapping.md](docs/04-codegen-mapping.md): the backend. How
  Arcturus constructs map to Z-machine opcodes and the story-file image, plus the
  size levers (dead-code elimination and abbreviation text compression).
- [docs/07-conformance.md](docs/07-conformance.md): conformance. What the
  compiler guarantees, the interpreter-driven evidence behind it, and the size
  record the test suite protects.

A fuller wiki will follow as the project matures. For a taste, the two worked
games live under [examples/](examples/) - the Brass Lantern and the classic
Cloak of Darkness. Small teaching showcases sit alongside them:
[examples/features/](examples/features/) isolates core-language features (the
container knowledge model, computed properties, kinds and inheritance, doors
and locks, multi-room scenery with `spans`, the `intro` first-look property,
grains, the object catch-all, daemons and timers, Z-machine colours with
the self-restoring coloured say, and the player object with its standard
self-words, pronouns, and Spanish clitic forms), and
[examples/granules/](examples/granules/) shows the summonable granules (the
Infocom-style and menu-driven conversation systems, the status line, verbose
exits, the extended verbs, and the quote box).

## File extensions

Arcturus uses three source extensions, named after the star:

- **`.storyarc`** is a *story*: an author's game, the program you compile.
- **`.prelude`** is a *core Cosmos library file*. The library is the prelude
  loaded before your story; the standard library is editable Arcturus source you
  can read and override.
- **`.granule`** is a *summoned module*: anything brought in with `summon`,
  whether a third-party extension or an optional Cosmos feature or language pack
  (it loads only when summoned). Granules are the convection cells that tile the
  Sun's photosphere; since Arcturus is a star, a summoned module is a granule on
  its surface.

## Output

Arcturus emits conformant Z-machine **version 5** story files by default. Pass
**`--zversion 8`** for a version 8 target for large, modern-only releases (the
same code generation, a larger 512KB story-file ceiling).

## Getting started

You need **Python 3.11 or newer**. Nothing else.

### Build the compiler

The compiler ships as a single self-contained script with no dependencies and
no installation. Build it from the package:

```
python3 tools/amalgamate.py build/arcc
```

This produces `build/arcc`, the standalone compiler, with the whole Cosmos
library embedded inside it - nothing else to install or locate. Compile an
example to a story file and play it:

```
python3 build/arcc examples/brass-lantern.storyarc -o brass-lantern.z5
frotz brass-lantern.z5
```

Useful options:

```
python3 build/arcc game.storyarc -o game.z5    # compile to a z5 story file
python3 build/arcc game.storyarc --zversion 8 -o game.z8   # target z8 (larger games)
python3 build/arcc game.storyarc -o game.z5 -q # script mode: no banner, no statistics
python3 build/arcc game.storyarc --dump-ast    # show the parsed syntax tree
python3 build/arcc -L /abs/path/cosmos game.storyarc   # use a forked library
python3 build/arcc --make-abbreviations game.storyarc  # tune text compression (below)
python3 build/arcc --version
```

Every compile prints a statistics ledger: what the story uses of each Z-machine
ceiling (attributes, properties, globals, memory, story size), so you can watch
the headroom as a game grows; `-q` silences it for scripts.

Text compression is automatic: every build packs its text against a standard
abbreviation set with nothing to configure. To squeeze a large story further,
`--make-abbreviations` computes a set tuned to its own text and writes an
`abbreviations.granule` beside it; add `summon abbreviations.granule` to the story
to use it in place of the default.

Cosmos travels inside `arcc`, so the compiler works wherever you put it, but it
is never locked away. To hack the library:

```
python3 build/arcc --eject-granule statusline  # write one granule here, to fork it
python3 build/arcc --eject-language .           # write english.prelude (the messages)
python3 build/arcc --extract-library /abs/cosmos   # write the whole library out to edit
python3 build/arcc -L /abs/cosmos game.storyarc    # compile against your edited copy
```

`--eject-granule` pulls a single granule out to fork one feature; summon your
copy by name (`summon statusline.granule`) and it wins over the bundled one.
`--eject-language` drops the English language file (where the standard messages
live) beside your story for message customization or a translation.
`--extract-library` writes every bundled `.prelude` and `.granule` for wholesale
forking; then `-L` (an absolute path) points the compiler at your copy. For a
single standard message you need not extract anything: redefine its block (for
example `block msg_jump()`) in your own story and it overrides the library's. A
granule's own blocks are not overridable that way - you fork the granule;
[docs/05](docs/05-granules.md) covers the model.

### Run from the package (for development)

```
python3 -m arcturus examples/brass-lantern.storyarc
python3 -m pytest
```

## Editor support

A Visual Studio Code extension provides syntax highlighting for `.storyarc`,
`.prelude`, and `.granule` files. Install the packaged extension:

- In VS Code: Extensions view, `...` menu, **Install from VSIX...**, then choose
  [editors/vscode/arcturus-0.4.0.vsix](editors/vscode/arcturus-0.4.0.vsix); or
- from a terminal: `code --install-extension editors/vscode/arcturus-0.4.0.vsix`

This works on macOS, Windows, and Linux. The extension source is under
[editors/vscode/](editors/vscode/); rebuild the `.vsix` with
`python3 tools/build_vsix.py`.

## How Arcturus is built

The language design, syntax, and the Cosmos library are the work of Stefan
Vogt. This is a human-driven project: the design decisions are his, and Claude
(Anthropic) is used as an AI coding assistant under his direction to implement
the toolchain.

The compiler is developed as a clean, modular Python package under
[arcturus/](arcturus/) (lexer, parser, AST, and the later semantic and code
generation stages). For distribution it is amalgamated into the single `arcc`
script, so the shipped artifact stays identical to the source.

## License

MIT. See the headers in each source file.

## Credits

Thanks to **Pablo Martínez** for the translation of the Spanish language
granule.
