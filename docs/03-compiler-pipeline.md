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
   memory, and the header. Before the routines are laid out, a whole-program
   reachability sweep (`codegen._prune_unreachable`) drops every routine the
   running story can never enter, the first size lever (docs/04 section 9). The
   construct-to-opcode mapping is docs/04.

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
Arcturus 0.5.0 -- [ arcc 0.5.0 | Cosmos 0.8.1 | python3 | stdlib | MacOS ARM ]
```

Options:

- `-o FILE`, `--output FILE`: write the story file to FILE. Without it the
  compiler parses and reports only.
- `--zversion {5,8}`: the Z-machine version to target. The default is 5, the
  standard: a plain compile with no version flag produces a z5 story file. Pass
  `--zversion 8` for a version 8 target, which raises the story-file ceiling to
  512KB (from the z5 256KB) for a large, modern-only release. The story source is
  identical for both.
- `-L DIR`, `--lib DIR`: add an absolute directory to the search path for granule
  (`.granule`) files a story summons by name; repeatable. Used to compile against
  a forked library (section 5, docs/05). A relative `-L` is rejected.
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
- `--eject-granule NAME`: write a single bundled granule (for example
  `statusline`) into the current directory for forking, then exit (section 5).
- `--make-abbreviations`: compute a tuned abbreviation set for the story (and the
  granules it summons) and write `abbreviations.granule` beside it, then exit. The
  standard set is always applied without this; summon the written file by name
  (`summon abbreviations.granule`) to use the tuned set instead (docs/04 section
  10, docs/05 section 7).
- `--version`: print the version and exit.

Exit status: 0 on success, 1 on a source error (parse or analysis, with a
formatted diagnostic), 2 on a usage or I/O error.

z5 and z8 share their instruction set and story image; only the header version
byte, the file-length scale, and the packed-address unit (4 for z5, 8 for z8)
differ, so `--zversion` changes those three things and nothing about code
generation.

## 5. Cosmos, overriding, and the library search

By default the game is compiled together with the bundled Cosmos library
(docs/02): `cosmos.combined_program` prepends the library declarations to the
game's. `--no-cosmos` opts out.

Overriding works against the prelude. A block defined in the game (or in a
summoned granule) overrides a Cosmos *prelude* block of the same name: redefine
`msg_jump()` in the story and it replaces the library's, with no unpacking. A
granule's own blocks, by contrast, are not overridable from a story; to change a
granule you fork it. That boundary is what keeps a granule distinct from a
prelude (otherwise a granule would just be a renamed prelude), and a granule
overriding a prelude is exactly what a language pack relies on. The full model -
the override boundary, the summon forms, and the fork workflow - is docs/05.

The library travels inside `arcc` (section 7), so the compiler never has to find
it on disk. When an author wants to change the library, four paths, lightest
first:

- Redefine a single prelude block in the story (the override above).
- `arcc --eject-granule <name>` writes one granule beside the story to fork it,
  summoned by filename.
- `arcc --eject-language` writes `english.prelude` to edit the messages or start
  a translation.
- `arcc --extract-library DIR` writes the whole library (preludes and granules)
  to fork wholesale, compiled with `-L DIR` (absolute).

A story summons a granule in one of three forms (docs/05, section 2):
`summon.statusline` always uses the bundled copy; `summon statusline.granule`
prefers a copy in the story directory or a `-L` directory and otherwise falls
back to the bundled one with a notice; `summon "path"` is an explicit file with
no fallback.

## 6. The intrinsic bridge

Cosmos is ordinary Arcturus, but a small set of reserved built-in functions lower
directly to opcodes rather than to a call, so the library can reach the machine:
input and parse-buffer access (`read_line`, `word_count`, `word_dict`, and the
rest), memory peek and poke, object-tree and property primitives (`parent_of`,
`words_addr`, `get_prop` via the computed `here.(dir)` form), the dispatch
helpers (`handler_of`, `call_handler`, `run_free`, `run_grain`), the life-cycle
event numbers, the output and turn-loop helpers (`show`, `print_name`, `par`,
`tick`, `set_here`, `do_quit`), the v5 screen model the statusline and
conversations granules draw with (`split_window`, `set_window`, `set_cursor`,
`erase_window`, `screen_width`, `read_key`), and the topic-table accessors the
conversation granules walk (`topics_count`, `topic_visible`, `topic_label`,
`topic_run`). Everything else in Cosmos is normal Arcturus.

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
