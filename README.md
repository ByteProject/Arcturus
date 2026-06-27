# Arcturus

**Arcturus is a programming language and compiler for the Infocom Z-machine.**

It is a high-level, readable language for writing interactive fiction: text
adventures in the tradition of *Zork* and the modern works that still run on the
Z-machine. You describe a world (rooms, things, verbs, and the behavior that
hangs off them) and the compiler produces a standard Z-machine story file that
plays on Frotz, Bocfel, and other interpreters, old and new.

Arcturus is designed and written by **Stefan Vogt**. The compiler is written in
Python and depends only on the standard library, so it runs anywhere Python
does, with nothing to install. The standard library, **Cosmos**, is written in
Arcturus itself and ships as editable source rather than a black box.

The name is a star, Arcturus, and the narrative arc every story is built on.

## Project status

Arcturus is in **active development and is not yet ready for production**. It
cannot compile a playable game today. The compiler is being built milestone by
milestone:

- **Done:** project scaffold, the language specification, and the compiler front
  end (lexer and parser) for the full language, with the two reference games
  parsing cleanly.
- **In progress:** semantic analysis and the world-model representation.
- **Next:** the Z-machine code generator, then the Cosmos library, then a size
  pass, graphics, and beyond.

Follow this README's status section and `PROGRESS.md` for where things stand.

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
- **`.prelude`** — a *Cosmos library file*. The library is the prelude loaded
  before your story; the standard library is editable Arcturus source you can
  read and override.
- **`.granule`** — an *extension*: a reusable add-on. Granules are the
  convection cells that tile the Sun's photosphere; since Arcturus is a star,
  an extension is a granule on its surface.

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

This produces `build/arcc`, the standalone compiler. Run it on an example:

```
python3 build/arcc examples/brass-lantern.storyarc
```

(While Arcturus is still in development the compiler parses and reports; code
generation is a coming milestone.) Useful options:

```
python3 build/arcc game.storyarc --dump-ast   # show the parsed syntax tree
python3 build/arcc -L path/to/cosmos game.storyarc   # add a library search path
python3 build/arcc --version
```

The `-L` option points the compiler at a shared Cosmos library so a project does
not have to carry its own copy of the prelude files.

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
