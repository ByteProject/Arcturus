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

Arcturus compiles to highly optimized Z-code that performs well on classic
8-bit hardware, and at the same time modernizes the platform's authoring.
Some of its comforts the platform otherwise knows only from modern systems
such as Dialog and Inform 7.

Arcturus games can carry **images** in z5 and z8 story files while staying
fully standard-compliant; how that works, and what plays them, is in the
comparison below.

The parser is language agnostic: grammar and wording live in a language
granule (English, German, and Spanish ship with the compiler), and authors
can eject that granule and adapt it to their own tone and needs, or their
own language, without touching the parser's machinery.

The name is a star, Arcturus, and the narrative arc every story is built on.

## Quickstart

The whole toolchain is two self-contained files (a third if your game uses
pictures). Download them and you are ready: no installation, no packages,
nothing to build. All you need is Python 3.11 or later, which you almost
certainly already have.

| Component | Version | Download |
|-----------|---------|----------|
| **arcc**, the compiler (the Cosmos library is embedded inside it) | 1.3.3 | [build/arcc](build/arcc) |
| **Cosmos**, the standard library | 1.2.2 | shipped inside `arcc` |
| **Actaea**, the reference interpreter | 1.1.0 | [build/actaea](build/actaea) |
| **arcimg**, the arc_image tool (optional, for graphics) | 1.13.0 | [build/arcimg](build/arcimg) |

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

The documentation above is the complete reference; everything the language
does is specified there. For a taste, the two worked games live under
[examples/](examples/) - the Brass Lantern and the classic
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

## What's new, and where Arcturus is heading

Arcturus is in active, healthy development, and the core is solid enough to
build real games on today. The three pieces of the toolchain - the **compiler**,
the **Cosmos** standard library, and the **Actaea** reference interpreter - are
all in stable shape and work together as a real pipeline: write a game, compile
it, and play it, start to finish. You will still meet the occasional bug (please
report it), but this is no longer use-at-your-own-risk territory. If you write
interactive fiction, this is a good time to pick it up.

The most significant recent additions and achievements, together with the
feature roadmap, are kept in [WHATSNEW.md](WHATSNEW.md).

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
it can be this expressive and still compile small.

## Comparison with other Z-machine languages and compilers

**The syntax finds the sweet spot.** Inform 7 reads like English, and
therefore does not read like a programming language: beautiful on the page,
but the author has to discover which sentences the compiler will accept,
and a large program hides its structure inside prose. Dialog is the
opposite pole: elegant, minimal, and deeply abstract, a rule-based language
closer to logic programming than to storytelling, and many authors find
that abstraction a wall. Inform 6 and ZIL are honest programming languages
of their decades, C-shaped and Lisp-shaped, with the world model largely
built by hand. Arcturus sits deliberately between the poles, and it never
pretends to be English: it is unmistakably a programming language, kept so
lean that it reads. Every construct is one keyword-led line shape on an
indent skeleton: `thing lantern in hallway` declares, `on take lantern`
handles, `north cellar` connects, `vary loop` varies. Because each thing
has exactly one way to be written, you always know what to type next and
the compiler never surprises you, which is the predictability Inform 7's
prose trades away; and because the shapes name the world directly (rooms,
things, kinds, verbs), there is nothing to translate through, which is the
abstraction Dialog charges for. A stranger can open a game's source and
follow the story, and what they are reading is a program that is plain
about being one.

**One mechanism where others need many.** Behavior is handlers: an action
walks from the acted-on object to the recipient, the room, the free rules,
and last the library default, most specific first. Ending a handler
consumes the action, `continue` passes it on, and `on after` runs once it
has really happened. That single chain expresses what elsewhere takes
instead-rules, before- and after-rulebooks, daemons, and life routines.

**Much of it exists in no other system.** The container knowledge model:
the game tracks what the player has actually SEEN and words itself
accordingly. Grains: scenery words and quips with no objects behind them,
whole regions of set dressing at zero object cost. Auto-scoring: mark a
thing `scored` and the library pays its points exactly once, while the
compiler sums `max_score` for you at compile time. Catalogs: ordered tables
with list power and not a byte of heap behind them. Self-varying prose
(`vary`) and reach modeling (`beyond`) round it out, the first shared with
Inform 7 and Dialog, the second otherwise Dialog's alone. And where the
classic libraries are monoliths you subtract from, Arcturus features arrive
only when summoned: no status line unless you ask for one, and what you do
not summon is simply not in the file.

**The compiler is a structural advantage over the whole ZIL and Inform
lineage.** arcc is a whole-program, multi-pass compiler: it sees game and
library at once, folds unused features away at compile time, and applies
strict dead-code elimination, so a build carries only what the game
actually uses, provably, byte for byte. ZILCH, Inform 6, and ZILF compile
what they are given, and Inform 7 emits through the Inform 6 compiler,
inheriting the same shape. Dialog's compiler optimizes globally, but the
language rides a runtime engine inside every story file; arcc emits direct
Z-machine operations with no runtime layer at all.

**Images, fully standard.** Arcturus pictures ride an extension opcode in
the range a conformant interpreter must simply ignore, and a story only
draws after an interpreter raises a capability flag that picture-aware
interpreters alone set. So the same z5 or z8 file plays as pure text on
Frotz or any classic interpreter, and shows its art where art is
understood: no Blorb, no separate build. **Actaea**, the project's own
interpreter, plays version 5 and 8 games with images today, and a dedicated
set of interpreters for retro systems with arc_image support is in the
making.

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
  the `arcturus-<version>.vsix` in [editors/vscode/](editors/vscode/) (exactly
  one ships there, always the current one); or
- from a terminal: `code --install-extension editors/vscode/arcturus-*.vsix`

This works on macOS, Windows, and Linux. The extension source is under
[editors/vscode/](editors/vscode/); rebuild the `.vsix` with
`python3 tools/build_vsix.py`.

## How Arcturus is built

I want to be very open about how this project. Many of you know me: you played my games, like the *Hibernated* series, *Ghosts of Blackwood Manor*, or *The Curse of Rabenstein*, or maybe used one of my tools for your own interactive fiction games. The language design, the syntax, Cosmos, and the compiler are my work, and Arcturus is a human-driven project. I use Anthropic's Claude Code as a coding assistant. It doesn't do anything I couldn't do myself. Python is my language of choice, and I use it daily in my role as regional head of a department at a global software company. Arcturus is a serious effort and I build it the way any engineer would build a project of this scope today. I know some of you have mixed feelings or objections about AI, and I take that seriously. For me, a coding assistant buys the time and the efficiency that make a project of this scope possible for the community, and what it enables in the end are new opportunities for interactive fiction and new, wonderful human-made stories. That is what matters most to me. The repository keeps a full log of my design decisions and the code I made along the way. This is not another Sunday-afternoon-vibe-coding-experiment but a thoughtfully crafted product with a full-featured roadmap and quality assessment through regression tests, where the human factor in the loop makes the difference.

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
