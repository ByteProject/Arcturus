# Actaea: The Reference Interpreter

Status: official documentation. Actaea is complete (Arcturus milestone B10);
this document describes what it is and how to use it. The design record,
with the architecture and the build milestones, is actaea/actaea-design.md.

Actaea is a Standard 1.1 conformant Z-machine interpreter for story-file
versions 5 and 8, written in Python with zero dependencies beyond the
standard library. It plays any well-formed z5 or z8 story file, not only
Arcturus output, and it is also a debugging tool: a header inspector, a
disassembler, and a scriptable harness. The name continues the
trans-Neptunian line of the family (Ceres, Varuna, Eris, Haumea), and is the
first written for the desktop rather than the metal.

```
Actaea vx.x.x - Z-machine v5/8 interpreter, debugger and disassembler
Standard 1.1 conformant | Part of Arcturus (programming language & compiler)
Copyright (c) 2026, Stefan Vogt | https://github.com/ByteProject/Arcturus
```

## 1. Getting it and running it

Actaea ships two ways, identical in behavior:

- The package: `python3 -m actaea story.z5` from the repository root.
- The standalone: one self-contained file, `build/actaea`, produced by
  `python3 tools/amalgamate_actaea.py`. Copy it anywhere and run
  `python3 actaea story.z5` (or `./actaea story.z5`); no installation, no
  package directory, no dependencies. This is the distribution form, the
  same arrangement as the `arcc` compiler.

Python 3.11 or later. The GUI needs tkinter and the terminal mode needs
curses; both ship inside CPython itself. On a Python without one of them,
Actaea degrades to the next mode down and says so.

## 2. The three ways to play

One headless virtual-machine core sits behind three front-ends. The core
cannot tell them apart; they differ only in where the screen and keyboard
live.

### The window (default)

`actaea story.z5` on a desktop opens the tkinter window: the game-drawn
status area rendered as a true character-cell grid, text styles and the
full Z-machine colour set, inline input at the story's own prompt wearing
the game's input colour, and native save/restore/transcript file dialogs.

Actaea is a light interpreter: its own screen is black on white paper, and
a game that wants a dark screen sets its colours (which the window then
honours completely, repainting the paper when the game erases).

The menu bar:

- About Actaea: the version and identity panel.
- View -> Font: every fixed-pitch family installed on the system (the list
  is scanned once, the first time the menu opens).
- View -> Text Size, Screen Height: point sizes and window lines.
- View -> Game Colours: off shows black-on-white with styles kept; on
  restores the game's palette, including text already on screen.

Settings persist in `~/.config/actaea/settings.json` (XDG_CONFIG_HOME is
honoured) and return at the next launch. They save when changed in the
menu, never behind your back.

A long passage returns the view to where unread text begins rather than
racing to the bottom, "press any key" accepts any key including Return,
and the window is exactly 80 cells wide, as the Z-machine screen model
declares.

Pictures (arc_image): the window is the one front-end that shows a room's
`arc_image` picture (01 section 6b). It draws a band across the top, above
the status bar, integer-scaled to the 80-cell width so pixel art stays
crisp; the status bar and text sit flush beneath it, and the band clears in
a room with no picture. The console and pipe modes report no picture
support, so the same story plays there as pure text. Actaea finds the
pictures next to the story: `--images DIR` points at a directory of numbered
PNGs (`8.png` is picture id 8, the debug path), and with no flag it reads a
sibling `.arcres` pack (the zip `arcimg` builds), then the story's own
directory. There is no name manifest; the id is the file. This is the modern
half; retro rendering is B12.

On macOS, the application menu shows the hosting Python's name unless
pyobjc is installed (then it reads Actaea); a proper .app wrapper is a
packaging concern outside this repository.

### The terminal: --console

`actaea --console story.z5` plays in the terminal, in the manner of
fizmo-ncursesw, on the standard library's curses: the status bar live from
the cell grid, Z-machine colours mapped to the terminal's, bold, italic,
and reverse, word wrap at the terminal width, [MORE] paging, inline input
in the game's input colour, and timed input on the terminal clock. The
screen fills from the top after a clear and scrolls once it reaches the
bottom; erasing paints the whole screen in the game's background. The
terminal tab is titled after the story.

Native Windows has no stdlib curses; there, --console degrades to the
headless pipe with a note (WSL plays fine).

### The pipe: --headless

`actaea --headless story.z5` is the dumb-terminal mode, in the manner of
dumb frotz: plain stdin/stdout, no screen control, suitable for debuggers,
walkthrough scripts, and build tools. Piped input is echoed into the
transcript so a scripted run reads like play. A walkthrough file follows
the dfrotz conventions: one command per line, a blank line for "press any
key". When input is piped, headless mode is chosen automatically.

Save, restore, and transcript prompts read their filenames from the same
input stream, so a scripted session can save and restore mid-walkthrough.

## 3. The tools

- `actaea --header story.z5` validates the file and prints the parsed
  header: version, release and serial, length and checksum (verified
  against the file), memory map, and table addresses.
- `actaea --disasm story.z5` disassembles every routine reachable from the
  entry point.
- `actaea --version` prints the banner; `--help` the usage. Every
  tool-facing output leads with the banner and ends with a blank line;
  play output carries neither, so piped transcripts stay pure game text.

The pictures a story shows are prepared by a separate tool, `arcimg`, the
third standalone alongside `arcc` and `actaea` (01 section 6b). It packs
numbered PNGs into the `.arcres` file Actaea reads (`arcimg pack`), sizes a
source to a picture mode (`arcimg prep`), and reports a PNG or a pack
(`arcimg info`); like the others it leads with its banner.

## 4. Saves, undo, transcripts

Saves are Quetzal 1.4, the portable standard: a save written by Actaea
restores in Frotz and every other Quetzal interpreter, and the reverse.
Actaea writes the compact form (dynamic memory XORed against the original
story file and run-length coded) and reads both the compact and
uncompressed forms. A save from a different story is refused by name.
Undo is in memory (multiple undo, as deep as the game asks) and restart
restores the pristine story.

The transcript (stream 2) is a real file, one per session, opened through
a file dialog, a console prompt, or the script, whichever front-end is
playing. It records the story text and the player's commands, lower
window only, and obeys both ways of switching (the output_stream opcode
and the game flipping the Flags 2 bit directly).

## 5. Input, in full

Everything Standard 1.1 asks of a v5/v8 interpreter's keyboard:

- Line input with editing, echoed by the front-end that shows it.
- Preloaded input: a part-typed line the game hands back (Beyond Zork
  style, after an interrupted command) appears at the prompt, editable,
  never printed twice.
- The terminating-characters table: reads can end on function keys the
  story names, which are reported as the terminator.
- read_char with the full key set: printables (accents included, decoded
  through the story's own alphabet tables), cursor keys, F1 to F12, the
  keypad.
- Timed input: the interrupt routine runs mid-read at the story's
  interval, its printing lifts the typed line and puts it back, and it
  can end the read (the typed text survives as the next read's preload).
  Front-ends without an event loop simply never time out, and honestly
  leave the header's timed-input capability bit unset.

## 6. Conformance

The gate Actaea passed to call itself conformant, all headless and all in
the test suite:

- CZECH 406/406, output matched byte for byte against the reference
  transcript (the interpreter-identity block aside).
- Praxix: all tests passed, every group verdict counted.
- TerpEtude: the text portions asserted headless (signed arithmetic,
  multiple undo, input preloading, lower-casing, closing text before
  quit); the styled, coloured, and timed portions verified by eye in the
  window and the terminal.
- Real games, z5 and z8, played headless as integration checks; the suite
  drives them where the (third-party) story files are present locally.
- Cross-interpreter saves proven in both directions against dfrotz inside
  the test suite, on a compiled Arcturus game.

Two leniencies exist because real games demand them, and are deliberate:
the table opcodes compute addresses in wrapping 16-bit arithmetic, and
asking for the relatives of object 0 answers "nothing" rather than
faulting (mutating object 0 remains an error). Sound is a designed no-op,
forever; there is no v6. Graphics are the one Arcturus extension: the
`arc_image` picture band renders in the window (B11, section 2), with retro
rendering to follow (B12). It extends the cell grid Actaea already keeps
decoupled for it, and never touches conformance: a story's pictures are
separate files, and a picture-less interpreter plays the same z5 as text.

## 7. For Arcturus authors

`arcc game.storyarc -o game.z5 && actaea game.z5` is the whole loop. The
compiler and the interpreter are independent implementations of the same
standard, built in the same repository, and each is the other's check: the
text Actaea decodes is the text arcc encoded, the saves interoperate with
third-party interpreters, and Hibernated 2 plays start to finish on all
three front-ends. Verify releases on a second interpreter (Frotz or
Bocfel) as a matter of craft; that is what reference implementations are
for.
