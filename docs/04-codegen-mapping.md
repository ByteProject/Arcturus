# Arcturus Code Generation Mapping

Status: in progress, produced as the backend is built (roadmap document 04).
This document records how Arcturus constructs lower to Z-machine version 5. It
grows milestone by milestone; this revision covers the B3 minimum viable
backend (banner, print, quit).

The authoritative language and runtime definitions are docs/01 and docs/02;
this document is the construct-to-opcode reference the backend implements.

## 1. Text

Text is encoded as Z-strings: 5-bit Z-characters packed three to a 16-bit word,
the top bit of the final word marking the end (standard 1.1, section 3). Three
alphabets carry the characters (A0 lowercase, A1 uppercase, A2 punctuation);
in version 5 the shift characters 4 and 5 shift the next single character into
A1 and A2. A character in no alphabet is written with the A2 escape (Z-char 6)
and its 10-bit ZSCII value. Implemented in `arcturus/zstring.py`. Abbreviation
compression (Z-chars 1 to 3) is a size-pass lever (B5) and is not yet emitted.

## 2. Story-file layout

A version 5 story file is a 64-byte header followed by three regions, built by
`arcturus/storyfile.py`:

- dynamic memory (writable): the global variables table and the object table;
- static memory (read-only): the abbreviations table and the dictionary;
- high memory: the code, run from the initial program counter.

Header fields the backend sets (standard 1.1, section 11):

| Offset | Field | B3 value |
|--------|-------|----------|
| 0x00 | version | 5 |
| 0x02 | release number | from `game release`, default 1 |
| 0x04 | high memory base | start of code |
| 0x06 | initial program counter | start of code (a byte address in v5) |
| 0x08 | dictionary | an empty dictionary |
| 0x0A | object table | property defaults table (no objects yet) |
| 0x0C | global variables | 240-entry table |
| 0x0E | static memory base | end of the object table |
| 0x12 | serial number | from `game serial`, else the build date (YYMMDD) |
| 0x18 | abbreviations table | empty |
| 0x1A | file length | real length / 4 (the v5 scale) |
| 0x1C | checksum | sum of bytes 0x40 to end, modulo 65536 |

The MVP touches no objects, so the object table is only the 63-word property
defaults table; objects and a populated dictionary arrive with Cosmos (B4).

## 3. The MVP main routine

The smallest program has no routine calls and no expressions, so the code is a
single straight-line instruction stream at the initial program counter. In
version 5 the initial PC is a byte address pointing at the first opcode, with no
routine header, so no packed addresses or alignment are involved.

0OP opcodes used (standard 1.1, section 14):

| Opcode | Byte | Use |
|--------|------|-----|
| print | 0xB2 | print the inline literal Z-string that follows |
| new_line | 0xBB | print a newline |
| quit | 0xBA | end the program |

## 4. Construct mapping (B3 subset)

| Construct | Lowering |
|-----------|----------|
| the startup banner | `print` of title, headline-by-author, and the release / serial / `Arcturus <version>` line; provisional, moves into Cosmos at B4 |
| `say "literal text"` (in `on start`) | `print` of the encoded string, then `new_line` |
| end of `on start` | `quit` |

The banner is emitted by the compiler as a stand-in. From B4 the banner is
Cosmos's responsibility (docs/02 section 3), where the library contributes its
own name and version; the compiler continues to hardcode nothing about Cosmos.

## 5. Routines and the value model (B4.1, B4.2)

Routines have a v5 header (one byte of local count, no initial values) and are
reached by packed address (byte address / 4), so each is 4-aligned. The entry
stub at the initial PC calls the main routine and quits. The assembler
(`arcturus/assembler.py`) encodes all instruction forms and the linker
backpatches call targets, branches, and jumps.

Expression lowering (`arcturus/lower.py`) is stack-based and right-first: an
expression evaluates onto the stack and a computing opcode stores its result
where asked. Binary operands are pushed right-first so the opcode reads them in
source order; a temporary preserves source order only when an operand contains
a block call. Conditions branch directly, with short-circuit `and`/`or` and
`not` folded into branch targets, never materializing a boolean.

| Construct | Lowering |
|-----------|----------|
| `+ - * / mod` | `add` / `sub` / `mul` / `div` / `mod` |
| `< > <= >=` | `jl` / `jg` (with negation for `<=` / `>=`) |
| `is` / `is not` (equality) | `je` |
| `let`, `change` to local/global | `store` / `push` into the variable |
| number `say` | `print_num` |
| `if` / `else`, `while`, number `switch` | labels, `jz`/`je`/`jl`/`jg`, `jump` |
| `return`, `finish` | `ret` / `rfalse`, `quit` |
| block call | `call_vs` / `call_vn` |

## 6. The object table (B4.3)

The object table (`arcturus/objects.py`) carries the property defaults, the
object entries (48 attribute bits, the parent/sibling/child tree, a
property-table pointer), and each object's property table (the Z-encoded short
name from `name`, then slot properties in descending number). Boolean
properties become attributes; `desc` holds a packed string address backpatched
once high memory is laid out.

| Construct | Lowering |
|-----------|----------|
| an object name as a value | its object-number constant |
| `now x is attr` / `is not` | `set_attr` / `clear_attr` |
| `x is attr` (property test) | `test_attr` |
| `x.prop` read | `get_prop` |
| `change x.prop to v` | `put_prop` |
| `move x to y` / `to nothing` | `insert_obj` / `remove_obj` |
| `x holds y`, `y in x` | `jin` |
| `say` an object, `${the obj}` | `print_obj` (article printed literally for now) |
| `say` a text property | `print_paddr` |

## 7. The dictionary and input (B4.4)

The dictionary (`arcturus/dictionary.py`) holds every matchable word - verb
words (multi-word phrases split into tokens), object `words`, and grain words -
as 6-byte Z-encoded entries truncated to nine Z-characters, sorted so the
interpreter's tokenizer can binary-search, with three data bytes per entry
reserved for the parser. The compiler provides the low-level intrinsics the
parser sits on: `aread` reads a line into the text buffer and tokenizes it into
the parse buffer against the dictionary, and `loadb`/`storeb`/`loadw`/`storew`
read and write memory. The text and parse buffers sit at fixed dynamic-memory
addresses just after the globals (`TEXT_BUFFER_ADDR`, `PARSE_BUFFER_ADDR`).

## 8. Not yet lowered

Deferred to later milestones: wiring each object's `words` to dictionary
addresses and noun resolution, `for each`, string switches, list properties
(`add`/`remove`), computed (`block`) properties and text-property writes, the
`a`/`an` choice by sound, dynamic property access (`here.(dir)`), the parser,
scope, and the turn loop (B4.5), and abbreviation-based text compression and
dense-codegen tightening (B5).
