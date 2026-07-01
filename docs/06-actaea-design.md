# Actaea: Design Document

Status: design phase. Actaea is a Standard 1.1 conformant Z-machine
interpreter for versions 5 and 8, written in Python with a tkinter GUI. It
plays any well-formed story file, not only Arcturus output. The name continues
the trans-Neptunian line of the family (Ceres, Varuna, Eris, Haumea), and is
the first written for the desktop rather than the metal.

Actaea is not a separate project. It is built inside the existing Arcturus
repository, by the same project and the same Claude Code context that is
building the compiler and Cosmos. It is the work of Arcturus milestone B7, the
reference interpreter. This document joins the Arcturus docs as 06, and the
Arcturus CLAUDE.md points to it. The milestones below (M1 to M11) are the
breakdown of that single roadmap milestone.

arc_image is explicitly not part of Actaea. You build it later, yourself, in
this same project, as Arcturus milestones B11 and B12. Actaea is the plain,
conformant interpreter; bringing it to life never touches graphics. The only
thing Actaea does for the later work is leave the cell model decoupled so B11
and B12 are an extension rather than a rewrite (sections 6 and 14).

## 1. What Actaea is

A correct, portable, plain z5 and z8 interpreter with a windowed front-end. It
implements the Standard 1.1 screen model, full text styles and colours,
Quetzal save and restore, in-memory undo, and restart. It has no Arcturus-
specific behavior of any kind: a story file built by Inform, ZILF, Dialog, or
Arcturus all play identically.

## 2. Locked decisions

- Versions 5 and 8 only. No z1 to z4, no z6, no z7. The packed-address
  multiplier is the only version-dependent arithmetic that matters here: 4 for
  v5, 8 for v8. Everything else in the two versions is shared.
- Python with a tkinter GUI. Standard library only; no third-party runtime
  dependencies. Tests may use pytest as a dev-only dependency.
- The upper window is a true monospace cell grid, modeled as a rows-by-columns
  cell buffer that is decoupled from its renderer, not a loose approximation.
- Full text styles (roman, bold, italic, reverse, fixed-pitch) and full colour
  including Standard 1.1 true colour.
- Quetzal for save and restore, standard IFF files that interoperate with
  other interpreters. Undo via in-memory snapshots. Restart reloads the
  initial state.
- Standard 1.1 is the conformance target, proven against CZECH, Praxix, and
  TerpEtude.
- Headless core first. The VM runs and passes opcode conformance through a
  console harness before the GUI exists, the same discipline as the headless
  CPU simulator that preceded each assembly interpreter.
- git first, before any code.

## 3. Non-goals

- No sound effects. The relevant opcodes degrade to no-ops and are marked out
  of scope rather than half-built.
- No arc_image. Actaea is the plain interpreter. The graphics extension is
  later work that you do yourself in this same project, as Arcturus milestones
  B8 and B9, never as part of bringing Actaea to life. Actaea only leaves the
  door open for it: the cell-grid screen model is built decoupled from its
  renderer so images can later be drawn into cell regions without
  rearchitecting (section 6).
- No v6 graphics window model, no mouse, no menus.

## 4. Architecture

Two layers with a hard boundary between them.

The core is a headless virtual machine: it loads a story file, decodes and
executes instructions, and talks to the outside world only through a small I/O
interface (print text, read line, read char, draw to a window cell, set style,
select stream, save, restore). The core has no knowledge of tkinter and can be
driven entirely from a console.

The front-end is the tkinter GUI: it implements the I/O interface against real
widgets, owns the event loop, and translates keystrokes into the input the
core asks for.

This boundary is the single most important design choice. It is what lets
CZECH and Praxix run headless in the test harness, what keeps the screen model
testable apart from rendering, and what will later let you add image rendering
(Arcturus B8 and B9) by extending the front-end and the cell model, not the
VM.

Module map (within the actaea package):

```
loader.py      story file load, header parsing, version and addressing
memory.py      dynamic, static, and high memory; byte and word access;
               packed-address resolution (x4 for v5, x8 for v8)
decode.py      instruction decoder: long, short, variable, extended forms;
               operand types; store, branch, and inline-text decoding
vm.py          the executor: evaluation stack, call frames, locals, the
               full opcode set, the run loop
objects.py     the v4+ object tree: 48 attributes, properties, parent,
               sibling, child, property defaults
text.py        ZSCII, the three alphabets and the custom alphabet table,
               abbreviations, encode and decode, the Unicode translation
               table
dictionary.py  dictionary parsing and lookup, word separators
iostreams.py   output streams 1 to 4, including stream 3 to a memory table
screen.py      the window model and the cell-grid buffer, renderer-agnostic
quetzal.py     Quetzal save and restore, undo snapshots, restart
io.py          the I/O interface the core calls and the GUI implements
gui/           tkinter front-end: app, lower window, upper grid, input
cli.py         the headless console runner used for conformance
```

## 5. The Z-machine core

Loader and addressing. Parse the header at story start: version, initial PC,
the dictionary, object table, global table, static memory base, abbreviations
table, the file length and checksum, the alphabet and terminating-characters
and header-extension pointers (v5 and Standard 1.1). Reject anything that is
not version 5 or 8 with a clear message.

Memory. Dynamic memory below the static base is writable; static and high
memory are read-only. Word and byte accessors with bounds checks. Packed
addresses for routines and strings resolve with the version multiplier.

Decoder. Decode all four instruction forms and the four operand types,
including the 0xBE extended opcodes used in v5 and v8. Carry per-opcode flags
for whether an instruction stores a result, branches, or carries inline text.
A disassembler mode is built alongside the decoder and earns its own tests; it
also makes later debugging tractable.

Executor. The evaluation stack, call frames with their locals and return
addresses, and the run loop. The full v5 and v8 opcode set: arithmetic and
logic, comparison and branch, load and store, call and return in their several
forms, object and property and attribute operations, the print family,
read and read_char, output_stream and input_stream, random, and the extended
opcodes that matter here (save and restore in table form, save_undo and
restore_undo, log_shift, art_shift, set_font, print_unicode, check_unicode,
set_true_colour). Sound and the v6 picture opcodes are no-ops.

Objects. The v4+ object format: 48 attribute bits, the parent, sibling, and
child words, and the property table with one- and two-byte size forms, over a
63-entry property defaults table. All the tree and property opcodes.

Text. ZSCII encode and decode, the A0, A1, A2 alphabets and the custom
alphabet table, the abbreviation mechanism, the 10-bit ZSCII escape, and the
Standard 1.1 Unicode translation table for input and output beyond ZSCII.

Dictionary. Parse the separators and entries, encode a typed word to its
dictionary form, and look it up; expose the result to the read opcode.

## 6. The screen model

Standard 1.1 in v5 and v8 has two windows and no automatic status line. The
game itself draws whatever status display it wants into the upper window, so
Actaea provides the windows and the positioning opcodes and lets the game,
including Cosmos's summon.statusline, render into them.

Lower window (window 0): a scrolling, word-wrapped, buffered text area. The
core performs word wrap and buffering; the front-end renders the resulting
text with styles and colours.

Upper window (window 1): a fixed grid of character cells, non-buffered,
overwriting, addressed by set_cursor. split_window sizes it, erase_window and
erase_line clear it, and printing places characters at the cursor. This is the
piece most easily faked into something that merely looks right, so it is
modeled honestly: a rows-by-columns buffer of cells, each cell holding a
character plus its style and colour, owned by screen.py and independent of any
widget. The front-end renders that buffer; it never holds the truth itself.

That decoupling is deliberate and forward-looking. When you later add
arc_image, as Arcturus milestones B8 and B9, you extend this cell model and its
renderer to draw a picture into a region of cells, with the pure-text path
unchanged. Actaea does not build that, but it is built so that adding it is an
extension rather than a rewrite.

## 7. Text styles and colours

The set_text_style opcode drives roman, reverse video, bold, and italic, and
fixed-pitch, combinable as the standard allows. set_colour drives the standard
colour numbers, with the current and default foreground and background, and
Standard 1.1 set_true_colour drives 15-bit RGB. The upper window is always
fixed-pitch. In the front-end these map cleanly onto tkinter text tags and
canvas cell attributes.

## 8. Input and output

Input. read assembles a line with editing and the terminating-characters
table, returning the terminator; read_char returns a single key. Timed input,
where a routine fires after an interval, is supported through the front-end
event loop. Input is echoed and editable in the lower window.

Output streams. Stream 1 is the screen. Stream 2 is a transcript to a file,
toggled by the game. Stream 3 redirects output into a table in dynamic memory
and nests correctly, which games rely on for measuring and capturing text.
Stream 4 logs commands. The core multiplexes these; only stream 1 reaches the
GUI.

## 9. Save, undo, restart

Save and restore use Quetzal, the standard IFF container (IFhd identification,
compressed or uncompressed memory, the stack chunk), so Actaea saves
interoperate with other interpreters and the reverse. Undo is handled in
memory through save_undo and restore_undo, snapshotting dynamic memory and the
stack. Restart restores the initial machine state. These are conformance
requirements, not extras.

## 10. The tkinter front-end

The lower window is a Text widget with word wrap and tags for styles and
colours. The upper window is a fixed character grid rendered from the cell
buffer, drawn on a Canvas so cell geometry is exact and so the later image
work has pixel control; a measured monospace font fixes the cell size. The
front-end owns the tkinter event loop, feeds keystrokes to the core's read and
read_char, schedules timed input with after, and renders the lower buffer and
the upper grid whenever the core signals a change. It implements the I/O
interface and nothing more; no game logic lives here.

## 11. Conformance

The bar is Standard 1.1, proven by the community suites:

- CZECH: the opcode checker. Run headless through cli.py, its output compared
  against the known-good transcript.
- Praxix: a second opcode and arithmetic suite, run the same way.
- TerpEtude: Andrew Plotkin's interpreter feature tests, covering the screen
  model, styles, Unicode, and timed input. The text portions run headless; the
  screen and timing portions are verified in the GUI.

The two Arcturus example games (the Brass Lantern and Cloak of Darkness) and a
handful of third-party z5 and z8 games are played end to end as integration
checks. The headless harness is the primary gate; the GUI checks cover what
only a real screen can show.

## 12. Repository layout

Actaea lives inside the existing Arcturus repository as the `actaea/` subtree,
added to the project Claude Code is already working in. There is no separate
repo and no separate CLAUDE.md; the existing Arcturus CLAUDE.md gains a short
Actaea entry pointing here, and this design joins the docs as `docs/06-actaea-
design.md`.

```
(arcturus repo root)
  CLAUDE.md                with an Actaea section added
  docs/
    06-actaea-design.md    (this document)
  arcturus/                the compiler package
  cosmos/                  the Cosmos library
  actaea/                  the interpreter (module map in section 4)
    gui/                   tkinter front-end
  tests/
    actaea/
      conformance/         czech and praxix runners, terpetude assets
      unit/
```

Keeping Actaea in the same repo and context is deliberate: the same project
builds the compiler, the library, and the interpreter, and B8 and B9 will add
graphics across the Arcturus and Actaea code together. Splitting it out would
sever exactly the shared context that later work depends on.

## 13. Milestones

Each lands with tests and a concrete done-test, and none advances until the
prior is green. M1 through M6 are headless; the GUI begins at M7.

- M1: scaffold and git, the story loader, the memory model, and header
  parsing. Done when it loads both example files and CZECH, reports the header
  fields correctly, and rejects non-v5/v8 files cleanly.
- M2: the instruction decoder and disassembler, all forms and operand types
  including extended. Done when it disassembles a real story file without error
  and the decode unit tests pass.
- M3: the execution core: stack, call frames, locals, arithmetic and logic,
  branches, load and store, call and return, jump. Done when computational test
  routines produce correct results headless.
- M4: the object tree, attributes, and properties, with all their opcodes.
  Done when the object and property tests pass.
- M5: the text engine and dictionary: ZSCII, alphabets, abbreviations, encode
  and decode, Unicode translation, dictionary lookup. Done when text prints
  correctly and word lookup resolves.
- M6: conformance gate. CZECH and Praxix pass clean, headless, output matched
  against the reference transcripts. This is the correctness milestone the
  whole build hangs on.
- M7: the tkinter shell: the lower window with scrolling and word wrap, line
  and character input, and output stream 1. Done when both example games are
  playable start to finish in the window in plain text.
- M8: the upper-window cell grid. The rows-by-columns cell model,
  split_window, set_cursor, erase_window, erase_line, and a game-drawn status
  line. Its done-test is visible and specific: the status line is correct, the
  upper window stays stable under splits and cursor moves, and a boxed quote
  renders cleanly, checked on a game that exercises the upper window hard. This
  is the foundation the later graphics work extends, so it is built as a real
  grid, not an approximation.
- M9: text styles and colours: set_text_style, set_colour, set_true_colour,
  fixed-pitch and reverse, rendered through tkinter tags and cell attributes.
  Done when styled and coloured text shows correctly in both windows.
- M10: save, undo, and restart: Quetzal save and restore interoperating with a
  reference interpreter both ways, save_undo and restore_undo, and restart.
  Done when a save made in Actaea loads in Frotz and the reverse, and undo and
  restart behave correctly.
- M11: the conformance sweep and polish: TerpEtude, output streams 2 and 3,
  terminating characters and timed input, v8 large-file checks, and a set of
  real z5 and z8 games played through. Done when CZECH, Praxix, and the
  applicable TerpEtude tests are green and the games run correctly.

After M11 Actaea is a finished Standard 1.1 interpreter in the Arcturus repo,
completing milestone B7. arc_image then proceeds as Arcturus milestones B8 and
B9, in this same project, extending the cell model M8 established.

## 14. Deferred and future hooks

Sound is out of scope and stays out. arc_image is out of scope for Actaea and
is built later by you, in this same Arcturus project, as milestones B8 and B9;
the only preparation here is the decoupled cell model in M8. z3 is permanently
out: Arcturus will never target it, and the version-3 status line and header
quirks are not worth carrying.
