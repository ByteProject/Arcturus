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

## Project status

Arcturus is in **active development**. It is not at a 1.0 release yet, but it
already compiles complete, playable games. The two worked examples - **The Brass
Lantern** and the classic **Cloak of Darkness** - compile with the standalone
`arcc` and are winnable start to finish on Frotz, with the entire Cosmos runtime
(turn loop, movement, verbs, scope and light, the parser, and scenery) written in
Arcturus itself. Early days for size, too: Cloak builds to under 6 KB before any
dedicated size pass.

The road from here, milestone by milestone:

- **Done:** the language spec, the compiler (lexer, parser, semantic analysis,
  Z-machine code generation), and Cosmos far enough that both example games play
  end to end.
- **Next:** a feature-complete library (the full standard verb set, the meta
  verbs, a fresh standard message set, and the summonable granules - extended
  verbs, an opt-in status line, verbose exits, a menu-driven conversation system,
  and debug verbs), then a size pass benchmarked against PunyInform.
- **After that:** Spanish and German language packs, a modern reference
  interpreter, the `arc_image` graphics path (modern systems first, then the
  8-bit and 16-bit retro machines), and porting two existing games - Ghosts of
  Blackwood Manor and The Curse of Rabenstein - as the proving ground. Reaching
  1.0 is tied to those ports.

Follow this section and `PROGRESS.md` for where things stand.

## The language

The authoritative language definition is the syntax reference, which is enough
to start writing Arcturus today:

- [docs/01-syntax-reference.md](docs/01-syntax-reference.md) — the language:
  grammar, every construct, and two complete worked example games.
- [docs/02-cosmos-and-parser.md](docs/02-cosmos-and-parser.md) — the runtime:
  the Cosmos library, the parser, the action pipeline, scope, light, and the
  turn loop.

A fuller wiki will follow as the project matures. For a taste, the two worked
games live under [examples/](examples/): the Brass Lantern and the classic
Cloak of Darkness.

## File extensions

Arcturus uses three source extensions, named after the star:

- **`.storyarc`** — a *story*: an author's game, the program you compile.
- **`.prelude`** — a *core Cosmos library file*. The library is the prelude
  loaded before your story; the standard library is editable Arcturus source you
  can read and override.
- **`.granule`** — a *summoned module*: anything brought in with `summon`,
  whether a third-party extension or an optional Cosmos feature or language pack
  (it loads only when summoned). Granules are the convection cells that tile the
  Sun's photosphere; since Arcturus is a star, a summoned module is a granule on
  its surface.

## Output

Arcturus emits conformant Z-machine **version 5** story files, with **version
8** planned for large, modern-only releases (the same code generation, a couple
of header values apart).

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
python3 build/arcc game.storyarc --dump-ast    # show the parsed syntax tree
python3 build/arcc -L path/to/cosmos game.storyarc   # use a forked library
python3 build/arcc --version
```

Cosmos travels inside `arcc`, so the compiler works wherever you put it, but it
is never locked away. To hack the library:

```
python3 build/arcc --extract-library cosmos/   # write the whole library out to edit
python3 build/arcc --eject-language .          # write just english.prelude (the messages)
python3 build/arcc -L cosmos/ game.storyarc    # compile against your edited copy
```

`--extract-library` writes every bundled `.prelude` and `.granule` file into a
directory for wholesale forking; `--eject-language` drops just the English
language file (where the standard messages live) beside your story for quick
message customization. Then `-L` points the compiler at your copy. For a single
message, you do not even need to extract: redefine its block (for example
`block msg_jump()`) in your own story and it overrides the library's.

### Run from the package (for development)

```
python3 -m arcturus examples/brass-lantern.storyarc
python3 -m pytest
```

## Editor support

A Visual Studio Code extension provides syntax highlighting for `.storyarc`,
`.prelude`, and `.granule` files. Install the packaged extension:

- In VS Code: Extensions view, `...` menu, **Install from VSIX...**, then choose
  [editors/vscode/arcturus-0.1.0.vsix](editors/vscode/arcturus-0.1.0.vsix); or
- from a terminal: `code --install-extension editors/vscode/arcturus-0.1.0.vsix`

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
