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

## Quickstart

The whole toolchain is two self-contained files (a third if your game uses
pictures). Download them and you are ready: no installation, no packages,
nothing to build. All you need is Python 3.11 or later, which you almost
certainly already have.

| Component | Version | Download |
|-----------|---------|----------|
| **arcc**, the compiler (the Cosmos library is embedded inside it) | 0.11.34 | [build/arcc](build/arcc) |
| **Cosmos**, the standard library | 0.32.0 | shipped inside `arcc` |
| **Actaea**, the reference interpreter | 1.0.4 | [build/actaea](build/actaea) |
| **arcimg**, the arc_image tool (optional, for graphics) | 1.7.0 | [build/arcimg](build/arcimg) |

Each is one self-contained file: download, `chmod +x`, done. Keeping them
current is one command: `arcc --update` refreshes all three in place (the
only time arcc ever touches the network; there is no passive check).

Write a game, compile it, play it:

```
python3 arcc mygame.storyarc -o mygame.z5    # compile to a Z-machine story
python3 actaea mygame.z5                      # play it in a window,
python3 actaea --console mygame.z5            # or in the terminal
```

The story file `mygame.z5` is a standard Z-machine v5 file: it also plays on
Frotz, Ozmoo, and any other interpreter, old or new. Then read the docs and
go: start with the [syntax reference](docs/01-syntax-reference.md) (the
language, with two complete worked games) and, when you want to play or debug,
the [Actaea guide](docs/06-actaea.md). The full documentation index is
[below](#the-language).

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

## What's new

Arcturus is in active, healthy development, and the core is solid enough to
build real games on today. The three pieces of the toolchain - the **compiler**,
the **Cosmos** standard library, and the **Actaea** reference interpreter - are
all in stable shape and work together as a real pipeline: write a game, compile
it, and play it, start to finish. You will still meet the occasional bug (please
report it), but this is no longer use-at-your-own-risk territory. If you write
interactive fiction, this is a good time to pick it up.

The most significant recent additions and achievements:

- **Catalogs: list power without the list tax.** `catalog` declares a
  fixed, ordered collection, one value per line (the lines of a letter, a
  roster of suspects, a table of numbers), and the operations read like
  prose: `calculate` for how many, `entry(x, 3)` for the third, `last`,
  `dice` for one at random, `position` for where something sits, plain
  `in` for membership, `for each` to iterate, and `change entry(...) to`
  rewriting one entry in place. Underneath there is no heap and no
  runtime library, only static tables and single opcodes, so it runs
  fast on a C64; a game that declares no catalog pays zero bytes. The
  quote box draws a whole letter from one with one call
  ([worked example](examples/features/catalogs.storyarc)).
- **SWIM SOUTH parses, and TRANSCRIPT records.** A grammar line can end in a
  `direction` slot (`push noun direction`, `swim direction`), so PUSH CRATE
  WEST and SWIM SOUTH reach their handlers with the direction riding `way`,
  the same slot GO uses; hand the move to the walking machinery whole with
  `perform("go", way)`. And every game now answers the classic TRANSCRIPT /
  SCRIPT and TRANSCRIPT OFF / UNSCRIPT, honestly: the library reads the
  interpreter's own flag back, so a cancelled file prompt never claims a
  recording. Worded natively in all three languages (MITSCHRIFT AN,
  TRANSCRIPCION), and the English meta words (SAVE, UNDO, SCORE, TRANSCRIPT
  and their kin) answer in every pack, so the session is never hostage to a
  guessed translation. See
  [examples/features/direction-grammar.storyarc](examples/features/direction-grammar.storyarc).
- **arc_image reaches the retro machines.** The same numbered pictures a
  modern build shows now convert to the 8-bit and 16-bit machines' own
  formats: paint ONE master per scene, and `arcimg convert` derives the
  native version for the Commodore 64, ZX Spectrum +3, Amstrad CPC, Amiga,
  Atari ST, and DOS, resolving each machine's palette and color-cell
  constraints, with PNG previews to judge without an emulator, an author
  hint that keeps a moon or sun visible on the narrowest palettes, and a
  polish loop that round-trips Spectrum art through any .scr editor.
  Reference loaders are proven on real emulators for four machines so far,
  and the interpreter blueprints ship with the toolkit
  ([docs/07-arc-image.md](docs/07-arc-image.md) for authors).
- **`perform` and `appearance`: the classic bridges, grown from the field.**
  `perform("take", book)` runs any action as part of the current turn,
  refusals, messages, and after-phase included, with the action name checked
  at compile time (Inform's `<<take book>>`, Dialog's `(try ...)`); the
  `appearance` property is the paragraph an object always owns in a room
  description ("The keeper is trimming the wick."), worded by state when
  computed, beside `intro`'s until-first-taken rule. Both came from early
  adopters porting real games, and both cost nothing in a game that never
  uses them; component objects (a lever that is `component` of its machine)
  arrived the same way. Worked examples:
  [perform](examples/features/perform.storyarc),
  [appearance](examples/features/appearance.storyarc),
  [components](examples/features/components.storyarc).
- **A parser that names your typo.** A noun phrase that resolves to nothing
  no longer runs the action with an empty noun: a real thing that is not
  here keeps the classic refusal, and a word the story does not know at all
  is spelled back ("This story doesn't know the word \"sdlfjh\".", worded
  by each language pack), with OOPS correcting it on the next line. Handlers
  can finally trust that `noun is nothing` means a bare verb, and the bare
  verb asks its own question ("Take what?", "Nimm was?", "¿Coge qué?"), while
  a pronoun with nothing to refer to gets its own answer too. Three
  situations, three responses, in every language.


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
- [docs/06-actaea.md](docs/06-actaea.md): Actaea, the reference interpreter.
  The three ways to play, the tools, saves and transcripts, and conformance.
- [docs/07-arc-image.md](docs/07-arc-image.md): pictures in your story. The
  master art, the `arcimg` workflow from PNG to every machine, and what plays
  where today.

For the curious who want to see under the hood, two further documents cover how
the compiler itself works:

- [docs/03-compiler-pipeline.md](docs/03-compiler-pipeline.md): the compiler.
  The pass pipeline, the command-line interface, how Cosmos is bundled and
  overridden, the single-file distribution, and the version model.
- [docs/04-codegen-mapping.md](docs/04-codegen-mapping.md): the backend. How
  Arcturus constructs map to Z-machine opcodes and the story-file image, plus the
  size levers (dead-code elimination and abbreviation text compression).

A fuller wiki will follow as the project matures. For a taste, the two worked
games live under [examples/](examples/) - the Brass Lantern and the classic
Cloak of Darkness. Small teaching showcases sit alongside them:
[examples/features/](examples/features/) isolates core-language features (the
container knowledge model, computed properties, kinds and inheritance, doors
and locks, multi-room scenery with `spans`, the `intro` first-look property,
grains, positional grammar, the object catch-all, daemons and timers,
Z-machine colours with the self-restoring coloured say, and the player object
with its standard self-words, pronouns, and Spanish clitic forms), and
[examples/granules/](examples/granules/) shows the summonable granules (the
Infocom-style and menu-driven conversation systems, the status line, verbose
exits, the extended verbs, the nautical directions, and the quote box).

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

You need **Python 3.11 or newer**. Nothing else. If you only want to write
games, the [Quickstart](#quickstart) above is the whole story: download
`build/arcc` and `build/actaea` and go. This section is for working from a
clone of the repository, and for rebuilding the standalones from source.

### The compiler

The prebuilt standalone is tracked at [build/arcc](build/arcc), so a fresh
clone can compile immediately:

```
python3 build/arcc examples/brass-lantern.storyarc -o brass-lantern.z5
python3 build/actaea brass-lantern.z5     # or frotz brass-lantern.z5
```

To rebuild it from the package after changing the compiler or Cosmos (a single
self-contained script, the whole Cosmos library embedded inside it, no
dependencies):

```
python3 tools/amalgamate.py            # writes build/arcc
python3 tools/amalgamate_actaea.py     # writes build/actaea
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
  [editors/vscode/arcturus-0.11.0.vsix](editors/vscode/arcturus-0.11.0.vsix); or
- from a terminal: `code --install-extension editors/vscode/arcturus-0.11.0.vsix`

This works on macOS, Windows, and Linux. The extension source is under
[editors/vscode/](editors/vscode/); rebuild the `.vsix` with
`python3 tools/build_vsix.py`.

## How Arcturus is built

The language design, the syntax, the Cosmos library, and the compiler are my
work, and Arcturus is a human-driven project. Many of you know me: you played
my games, like the *Hibernated* series, *Ghosts of Blackwood Manor*, or *The
Curse of Rabenstein*, or maybe used one of my tools for your own interactive
fiction games. For Arcturus, I work with Anthropic's Claude Code as a coding
assistant, and it implements and debugs the toolchain under my direction.
Python is my language of choice and I work with it on a daily basis as
regional head for one of the departments of a global software company. With
that being said, Claude does not do what I couldn't do myself. I know that
some of you out there have mixed feelings or even objections against the use
of AI. Please consider this: a coding assistant buys me the time and the
efficiency to create and maintain a project of this scope and quality for the
community. The result is a language full of syntactic sugar, contemporary and
easy to use, inspiring and motivating authors to write faster and better, and
the outcome is new opportunities for the interactive fiction community and
new, wonderful human-made stories. And that is what matters the most to me.

The compiler is developed as a clean, modular Python package under
[arcturus/](arcturus/) (lexer, parser, AST, and the later semantic and code
generation stages). For distribution it is amalgamated into the single `arcc`
script, so the shipped artifact stays identical to the source.

## Join the community on Discord

https://discord.gg/JF6YNUTPfT

## License

MIT. See the headers in each source file.

## Credits

Thanks to **Pablo Martínez** for the translation of the Spanish language
granule.

Special thanks to **Charles Moore Jr.** for early adoption and bug hunting.
