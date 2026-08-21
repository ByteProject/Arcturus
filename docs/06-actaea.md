# Actaea: The Reference Interpreter

Status: official documentation. Actaea is complete (Arcturus milestone B10);
this document describes what it is and how to use it. The design record,
with the architecture and the build milestones, is actaea/actaea-design.md.

Actaea is a Standard 1.1 conformant Z-machine interpreter for story-file
versions 5 and 8, written in Python with zero dependencies beyond the
standard library. It plays any well-formed z5 or z8 story file, not only
Arcturus output, and it is also a debugging tool: a header inspector, a
disassembler, and a scriptable harness. Beyond the Z-machine itself, it
brings Arcturus's `arc_image` graphics to the modern desktop: the window
draws a story's pictures, straight from loose PNGs while you are still
working on them or from the finished pack when you ship, which makes
Actaea the tool to develop an arc_image game with. The name continues
the trans-Neptunian line of the family (Ceres, Varuna, Eris, Haumea),
and is the first written for the desktop rather than the metal.

```
Actaea vx.x.x - Z-machine v5/8 interpreter, debugger and disassembler
Standard 1.1 conformant | Part of Arcturus (programming language & compiler)
Copyright (c) 2026, Stefan Vogt | https://github.com/ByteProject/Arcturus
```

## 1. Getting it and running it

Actaea ships two ways, identical in behavior:

- The package: `python3 -m actaea story.z5` from the repository root. The
  story argument is optional for the window: a bare `actaea` asks for one
  with a native open dialog, or reopens the last story you played,
  whichever Settings -> On Launch says (asking is the default). Every
  terminal-facing mode (--console, --headless, --header, --disasm,
  --record, --replay, --check) still requires the story on the command
  line: those are developer's tools at a prompt. The
  story argument may also be a `.zblorb` (a Blorb with the story embedded,
  the pack `arcimg pack --zblorb` writes): Actaea plays the story out of
  it and serves its pictures from the same file.
- The standalone: one self-contained file, `build/actaea`, produced by
  `python3 tools/amalgamate_actaea.py`. Copy it anywhere and run
  `python3 actaea story.z5` (or `./actaea story.z5`); no installation, no
  package directory, no dependencies. This is the distribution form, the
  same arrangement as the `arcc` compiler.

Python 3.11 or later. The GUI needs tkinter and the terminal mode needs
curses; both ship inside CPython itself. On a Python without one of them,
Actaea degrades to the next mode down and says so, naming the exact way
to get tkinter on that platform.

On Windows, two things differ. First, the standalone must be started
through the Python launcher: `py actaea story.z5` (the file's first line
is a Unix shebang, which Windows does not read, so the file cannot be
started by name alone; this is the whole reason a plain `actaea story.z5`
is "not recognized" there). Second, the window needs a Python that
includes tkinter: the python.org installer ships it when the "tcl/tk and
IDLE" box stays ticked, and an installation missing it can be repaired by
re-running the installer and choosing Modify. A quick test is
`py -c "import tkinter"`. Native Windows has no curses at all, so without
tkinter the ladder goes straight down to the plain pipe; the console mode
plays fine under WSL.

On macOS, recent systems (Tahoe and later) deprecate the Tk that ships
with the OS, and a Python still linked against it can open the Actaea
window as a BLANK FORM, with "The system version of Tk is deprecated"
in the terminal. The window is not broken, its toolkit is: give Python
a current Tcl/Tk and the form fills in. With Homebrew:

    brew install tcl-tk

then put its bin directory on the PATH ahead of the system one, in
`~/.zshenv` or your shell profile (check the installed version; the
path carries it):

    export PATH=/opt/homebrew/Cellar/tcl-tk/9.0.4/bin:$PATH

and restart the terminal (and your editor, if it launched Actaea).
Until then, `actaea --console story.z5` plays fine: the terminal mode
does not use Tk at all.

## 2. The three ways to play

One headless virtual-machine core sits behind three front-ends. The core
cannot tell them apart; they differ only in where the screen and keyboard
live.

### The window (default)

`actaea story.z5` on a desktop opens the window: the game-drawn status
bar, text styles and the full Z-machine colour set, inline input at the
story's own prompt wearing the game's input colour, and native file
dialogs for saves and transcripts.

![The Actaea window on macOS: an arc_image story with its picture band
and status bar, the About panel, and the star on the Dock](../artworks/docs/actaea-window.png)

Actaea is a light interpreter: its own screen is black on white paper, and
a game that wants a dark screen sets its colours (which the window then
honours completely, repainting the paper when the game erases).

The menu bar:

- About Actaea: the version panel.
- File -> Open (Cmd+O): open another story in the same window,
  mid-session, without quitting.
- Visuals -> Typeface: three looks, set in a selected serif (Novel, the
  default), a clean typeface (Clean), or a genuine pixel font (Retro,
  the whole screen in one face the way a real 8-bit machine was). The
  fonts ship with Actaea; there is nothing to install.
- Visuals -> Text Size: one size, driving every look.
- Visuals -> Screen Height: how many lines tall the story plays.
- Visuals -> Window Shape: Modern (4:5), a portrait page like the
  modern desktop interpreters open, or Classic (4:3), the squat screen
  of the machines the format came from. On a display too small for the
  full portrait the shape scales down to fit what the desktop really
  offers. Everything is relative to the font: a larger font gives a
  larger window of the same shape.
- Visuals -> Game Colours: off plays black-on-white with styles kept;
  on restores the game's palette, including text already on screen.
- Settings -> On Launch: what starting Actaea without a story does,
  ask for one or reopen the last one played.

Settings persist in `~/.config/actaea/settings.json` (XDG_CONFIG_HOME
is honoured) and return at the next launch, the window's size and
position included: Actaea opens where you last left it. Delete the file
to start fresh.

A passage taller than the screen stops at a reverse-video `[MORE]`, and
any key turns the page: nothing scrolls past unread. The scrollback
stays yours, and the wheel, the trackpad, and Page Up walk back through
everything printed so far. "Press any key" accepts any key, Return
included. The story sets in the chosen look's own typeface; the status
bar and anything a game prints as fixed-pitch stay monospaced, as
Z-machine games expect. In Retro, emphasis comes as colour and reverse
video, the way the real machines did it.

Pictures: the window draws a story's `arc_image` picture (01 section
6b) in a band across the top, pixel-crisp at every window size, and the
window keeps the text below it at a whole number of lines; text the
band displaces is re-shown behind [MORE]s rather than scrolled away
(the re-base rule of 08 section 3, which every arc_image interpreter
follows). This is arc_image on the modern desktop, and it is the loop
an arc_image game is developed in: point `--images DIR` at a directory
of numbered PNGs (`8.png` is picture id 8) and play while the art is
still loose; when you ship, Actaea reads the same pictures from the
sibling `.blorb` pack, or from a `.zblorb` carrying story and pictures
in one file. The terminal and pipe modes report no picture support, so
the same story plays there as pure text.

The window is a native application, with Actaea's own name and icon
rather than Python's. For a place among your applications,
`actaea --install-app` installs a thin launcher on macOS, Linux, or
Windows, with file associations for .z5, .z8, and .zblorb: double-click
a story and it opens in the window. The interpreter itself stays the
single file beside arcc and the other Arcturus tools, fully accessible
from the command line, and `arcc --update` continues to update
everything in place when the tools are kept together; the launcher
holds no logic of its own, so it never goes stale. (If the tools'
directory later moves, launch the relocated `actaea` once by hand and
the launcher follows.)

### The terminal: --console

`actaea --console story.z5` plays in the terminal, in the manner of
fizmo-ncursesw, on the standard library's curses: the status bar live from
the cell grid, Z-machine colours mapped to the terminal's, bold, italic,
and reverse, word wrap at the terminal width, [MORE] paging, inline input
in the game's input colour, and timed input on the terminal clock. The
screen fills from the top after a clear and scrolls once it reaches the
bottom; erasing paints the whole screen in the game's background. The
terminal tab is titled after the story for the session and gets its old
name back on exit (the terminal's title stack; terminals without one
keep the story title, as before).

The game is told the terminal's real size, so anything it draws across the
screen crosses the whole screen: a status bar in a 103-column window is 103
columns wide, and in a 40-column one it is 40. Resize the window and the new
size reaches the game with the next thing it draws, which for a status bar
means the next command; version 5 has no way for an interpreter to interrupt
a game mid-turn to announce a resize, so one turn's delay is how every v5
interpreter behaves.

Resizing keeps what is on screen. The terminal itself holds no history, so
the console keeps its own record of what the story has printed and repaints
from it, re-wrapped to the new width. A screen the story deliberately
cleared stays cleared.

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
numbered PNGs into the Blorb pack Actaea reads (`arcimg pack`), sizes a
source to a picture mode (`arcimg prep`), and reports a PNG or a pack
(`arcimg info`); like the others it leads with its banner.

### Record, replay, and check

If you have met Inform's RECORDING and REPLAY, this is the same idea, done in
the interpreter instead of the game: it costs the story nothing, works on any
file, and produces a plain playthrough you can edit and re-run. Three flags
over one file:

```
actaea --record walk.txt story.z5    # play, saving the session to walk.txt
actaea --replay walk.txt story.z5    # replay it, then keep playing
actaea --check  walk.txt story.z5    # did anything change? (in plain words)
```

- **`--record FILE`** plays normally and saves the session, your commands AND
  the game's replies, to FILE. Add `--console` to record from the full
  terminal (status bar, colours, paging), the way you would normally play;
  without it, recording runs on the plain console (interactive in a terminal,
  piped otherwise). `--replay` works the same way, in either. Only `--check`
  is always headless, since it is a batch comparison with nothing to show.
- **`--replay FILE`** runs the file's commands and then hands you the keyboard
  to keep playing, the fast "skip ahead to where I was". With `--headless` it
  runs the commands and stops, for build tools.
- **`--check FILE`** re-runs the recorded commands against the current game and
  tells you whether it still plays the same. If nothing changed it says so; if
  something did, it names the command, shows the reply before and now, and
  **stops at the first difference**, because once the world's state has moved,
  every later reply is noise. It exits 0 when everything matched and 1 when it
  diverged, so a build script can gate on it.

The file is the readable playthrough. Command lines start with `> `; the game's
reply to each sits under it. The commands are the editable spine, so you can
add commands by hand: a command you typed in with no recorded reply is run and
counted as new, never a failure, so the check never scolds you for extending a
walkthrough. When you are happy with the new tail, record again to save its
replies. Appending commands at the end is clean; inserting one in the middle
legitimately changes every reply after it (the game is in a different state),
so `--check` will flag the insertion point, and you re-record from there.

Games with random flavor (dice, shuffled ambience, `vary mutate`) are the
one thing record and check cannot pin down on their own: the commands
replay identically, the dice do not. **`--seed N`** closes that gap. It
seeds the interpreter's random generator with N at boot, so a session is
reproducible end to end, and RESTART rewinds the generator with the
machine, so even a restarted run replays the same. It works in every mode
(window, console, headless) and pairs naturally with the three flags
above: `--record --seed 7` today, `--check --seed 7` after every change,
and the walkthrough of a random game becomes as deterministic as a quiet
one. The seed is never implied: without the flag, every session rolls
fresh, `--check` included.

The typical loop: record a full playthrough once, change your code, run
`arcc` and then `actaea --check walk.txt story.z5`. In a few seconds it tells
you, in plain language, whether your change broke the walkthrough. Combine
`--replay IN --record OUT` to replay an existing walkthrough and record where
you take it next, extending it without replaying by hand.

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
