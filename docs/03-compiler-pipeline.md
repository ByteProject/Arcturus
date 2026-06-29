# Arcturus Compiler Pipeline and Behavior

How `arcc` is built and how it behaves: the compilation pipeline, the module
boundaries, the command-line interface and its options, the way Cosmos is
included and overridden, the single-file distribution, and the version model.
The code-generation detail (constructs to opcodes, the story-file image) is its
own document, docs/04-codegen-mapping.md; the runtime the compiler targets is
docs/02-cosmos-and-parser.md.

## 1. What the compiler is

`arcc` reads Arcturus source (a `.storyarc` story, compiled together with the
Cosmos library) and writes a conformant Z-machine version 5 story file. It is
written in Python and uses only the standard library, so it runs on a bare
interpreter with nothing to install. Tests use pytest, a development-only
dependency; the compiler itself never imports anything outside the standard
library.

## 2. The pipeline

Source becomes a story file in a fixed sequence of passes, each a module with a
clear boundary. Source flows forward only: a later pass never reaches back into
an earlier pass's representation.

1. Lex (`lexer`). The indentation-significant tokenizer. It tracks indent and
   dedent, reads multi-line strings (collapsing a real line break to a single
   space, with `\n` for a forced break and `${ }` for interpolation), and emits
   a token stream. Newlines inside a string do not produce layout tokens.
2. Parse (`parser`, into `ast`). Recursive descent with precedence climbing,
   producing the abstract syntax tree. One statement or declaration per logical
   line.
3. Combine (`cosmos`). The Cosmos library sources are parsed and their
   declarations are prepended to the game's, yielding one program. Cosmos blocks
   are tagged `library` so a game (or granule) block of the same name overrides
   them (section 5).
4. Analyze (`sema`, into `worldmodel`). Semantic analysis turns the AST into the
   checked world-model intermediate representation: objects and their kind
   chains, the program-wide property table (one type per property, attribute or
   slot storage), the verbs and actions, the handlers with their dispatch
   specificity, and the grains. It resolves names, disambiguates `is` (property
   test, kind test, or equality), checks that conditions are boolean, enforces
   declare-before-change, and validates handler events and operands.
5. Lower (`lower`). Each block and handler body is lowered to Z-machine
   instructions: the expression and statement set, control flow, the value model
   (stack-first, temps for call operands), and the intrinsic bridge (section 6).
6. Code-generate and assemble (`codegen`, `objects`, `dictionary`, `zstring`,
   `assembler`, `storyfile`). The world model becomes a complete z5 image: the
   object table, the dictionary, Z-string text, the routines linked into high
   memory, and the header. The construct-to-opcode mapping is docs/04.

`astdump` and `irdump` expose the intermediate forms for inspection (the
`--dump-ast` and `--dump-ir` options).

## 3. Module map

Under `arcturus/`:

```
errors      diagnostics and the ArcError type
tokens      token kinds
lexer       the indentation-significant tokenizer
ast         the abstract syntax tree
parser      recursive descent plus precedence climbing
prelude     the provisional standard environment (kinds, properties, actions)
worldmodel  the checked intermediate representation
sema        the analysis passes
zstring     the ZSCII / Z-string encoder
storyfile   the header and memory-region assembler (checksum, length)
assembler   the instruction encoder and the routine linker
objects     the object table (attributes, properties, tree, short names)
dictionary  the version 5 dictionary (verbs, vocabulary, parser data bytes)
lower       lowering of expressions, statements, and the intrinsic bridge
codegen     the top-level lowering to a z5 image, the banner, the react routines
cosmos      loading and bundling the Cosmos library
astdump     --dump-ast
irdump      --dump-ir
cli         the arcc command-line front end
```

## 4. The command-line interface

Invocation:

```
arcc [options] <file.storyarc>
```

With no arguments, `arcc` prints its banner to standard error and exits with
status 2. The banner reports the compiler version, the bundled Cosmos version,
the runtime tags, and the host operating system, for example:

```
Arcturus 0.1.0 -- [ arcc 0.1.0 | Cosmos 0.1.0 | python3 | stdlib | MacOS ARM ]
```

Options:

- `-o FILE`, `--output FILE`: write the story file to FILE. Without it the
  compiler parses and reports only.
- `-L DIR`, `--lib DIR`: add a directory to the search path for Cosmos `.prelude`
  and `.granule` files; repeatable. Used to compile against a forked library
  (section 5).
- `--check`: parse and analyze only, no code generation.
- `--dump-ast`: print the parsed syntax tree and stop.
- `--dump-ir`: print the analyzed world-model IR and stop.
- `--no-cosmos`: compile the game alone, without the bundled Cosmos library
  (used by the compiler's own unit tests).
- `--extract-library DIR`: write the whole bundled library (`.prelude` and
  `.granule`) into DIR for wholesale forking, then exit (section 5).
- `--eject-language [DIR]`: write just `english.prelude`, the language layer that
  holds the standard messages, into DIR (default: the current directory), then
  exit (section 5).
- `--version`: print the version and exit.

Exit status: 0 on success, 1 on a source error (parse or analysis, with a
formatted diagnostic), 2 on a usage or I/O error.

The `--v8` build flag (a version 8 target for large modern-only releases, the
same code generation with two header values changed) is a later option, not yet
implemented.

## 5. Cosmos, overriding, and the library search

By default the game is compiled together with the bundled Cosmos library
(docs/02): `cosmos.combined_program` prepends the library declarations to the
game's. `--no-cosmos` opts out.

Overriding is most-specific-wins, the same rule used for handlers, extended to
blocks. A block defined in the game (or in a summoned granule) overrides a Cosmos
library block of the same name. This is how an author reskins a standard message
without unpacking anything: redefine `msg_jump()` in the story and it replaces
the library's. A duplicate that is not a game-over-library override is still an
error.

The library travels inside `arcc` (section 7), so the compiler never has to find
it on disk. When an author wants to edit the library, three paths, lightest
first:

- Redefine a single block in the story (the override above).
- `arcc --eject-language` writes `english.prelude` beside the story, to edit the
  messages or start a translation, then compile with `-L`.
- `arcc --extract-library DIR` writes the whole library out to fork wholesale,
  then compile with `-L DIR`.

When the compiler does read library files from disk (the development tree, or a
`-L` directory), a summoned granule resolves relative to the story file's
directory and then the `-L` path.

## 6. The intrinsic bridge

Cosmos is ordinary Arcturus, but a small set of reserved built-in functions lower
directly to opcodes rather than to a call, so the library can reach the machine:
input and parse-buffer access (`read_line`, `word_count`, `word_dict`, and the
rest), memory peek and poke, object-tree and property primitives (`parent_of`,
`words_addr`, `get_prop` via the computed `here.(dir)` form), the dispatch
helpers (`handler_of`, `call_handler`, `run_free`, `run_grain`), the life-cycle
event numbers, and the output and turn-loop helpers (`show`, `print_name`, `par`,
`tick`, `set_here`, `do_quit`). Everything else in Cosmos is normal Arcturus.

## 7. Distribution: the single-file arcc

The compiler is developed as a modular package but shipped as one self-contained
script. `tools/amalgamate.py` embeds every module verbatim behind an in-memory
loader, in dependency order, and embeds the Cosmos `.prelude` and `.granule`
sources as data (it sets `cosmos._EMBEDDED`). The result, `build/arcc`, carries
the compiler and the whole standard library in a single file with zero runtime
dependencies, so it runs wherever Python does and works no matter where the user
puts it. `tests/test_standalone.py` runs the generated script with no package on
the path, to prevent drift between the package and the shipped artifact.

## 8. The version model

Two versions are tracked independently. The compiler version is
`arcturus.__version__`; the library version is `cosmos.COSMOS_VERSION`. They can
diverge, because the bundled library can move ahead of or behind the compiler and
is not visible on disk. Both appear in the command-line banner (section 4) and in
the in-game banner Cosmos prints at the start of a story ("Release N / Serial
number ... / Arcturus X.Y / Cosmos X.Y"). Nothing in the compiler hardcodes the
library's version; Cosmos declares its own.
