# Actaea: The Reference Interpreter

Status: official documentation.

Actaea is Arcturus's own interpreter: Standard 1.1 conformant, for
story files in versions 5 and 8, running natively on macOS, Linux, and
Windows. It plays any well-formed z5 or z8 file, not only Arcturus
output, and it doubles as a development tool: a header inspector, a
disassembler, and a scriptable harness for recorded walkthroughs.
Beyond the Z-machine itself it brings Arcturus's `arc_image` graphics
to the desktop: the window shows a story's pictures, straight from
loose PNGs during development or from the finished Blorb, which makes
Actaea the tool to build an arc_image game with.

```
Actaea vx.x.x - Z-machine v5/8 interpreter, debugger and disassembler
Standard 1.1 conformant | Part of Arcturus (programming language & compiler)
Copyright (c) 2026, Stefan Vogt | https://github.com/ByteProject/Arcturus
```

## 1. Getting it and running it

All Actaea needs is Python 3.11 or later. It ships two ways, identical
in behavior:

- The standalone: one self-contained file, `actaea`, beside `arcc` and
  the other Arcturus tools. Keep them together, and `arcc --update`
  keeps them all current. `actaea story.z5` plays. This is the form to
  use.
- The package: `python3 -m actaea story.z5` from a checkout of the
  repository, for working on the interpreter itself.

The story argument is optional for the window: a bare `actaea` asks
for a story, or reopens the last one you played, whichever Settings ->
On Launch says. Every terminal-facing mode (--console, --headless,
--header, --disasm, --record, --replay, --check) requires the story on
the command line. The story may also be a `.zblorb`, story and
pictures in one file, written by `arcimg pack --zblorb`.

The window needs Python's tkinter and the terminal mode its curses;
both come with Python on most systems. Where one is missing, Actaea
falls back to the next mode down and says so, naming the exact way to
get tkinter on that platform.

### Notes for macOS users

Two different Tk problems look alike on a Mac; the message Actaea
prints tells you which one you have.

If Actaea says **this Python has no tkinter**, install the Tk bindings
for your Python. On a Homebrew Python that is

    brew install python-tk

(match your Python's version if Homebrew asks, e.g. `python-tk@3.14`).
Homebrew's plain `tcl-tk` package is not enough: it installs Tcl/Tk
itself, not Python's bindings to it.

If the window opens as a **blank form** with "The system version of Tk
is deprecated" in the terminal: recent systems (Tahoe and later)
deprecate the Tk that ships with the OS, and a Python still linked
against it draws nothing. Give Python a current Tcl/Tk:

    brew install tcl-tk

then put its bin directory on the PATH ahead of the system one, in
`~/.zshenv` or your shell profile (check the installed version; the
path carries it):

    export PATH=/opt/homebrew/Cellar/tcl-tk/9.0.4/bin:$PATH

and restart the terminal (and your editor, if it launched Actaea).
Either way, `actaea --console story.z5` plays meanwhile: the terminal
mode does not use Tk at all.

### Notes for Windows users

Start the standalone through the Python launcher: `py actaea story.z5`.
The file's first line is a Unix shebang, which Windows does not read,
so the file cannot be started by name alone; that is the whole reason
a plain `actaea story.z5` is "not recognized" there.

The window needs a Python that includes tkinter: the python.org
installer ships it when the "tcl/tk and IDLE" box stays ticked, and an
installation missing it can be repaired by re-running the installer
and choosing Modify. A quick test is `py -c "import tkinter"`. Native
Windows has no curses, so without tkinter Actaea goes straight down to
the plain pipe; the console mode plays fine under WSL.

## 2. The three ways to play

Actaea plays in a window, in the terminal, or as a plain text pipe.

### The window (default)

`actaea story.z5` opens the window, the way Actaea is normally played.
It supports the full Z-machine screen model: colors, text styles, the
game-drawn status bar, and timed input. Long passages page with
`[MORE]`, and you can scroll back through everything printed. The Up
and Down arrows recall your earlier commands at the prompt, and one
step past the newest brings back whatever you had half-typed.

![The Actaea window on macOS: an arc_image story with its picture band
and status bar, and the About panel](../artworks/docs/actaea-window.png)

The menu bar:

- About Actaea: the version panel.
- File -> Open (Cmd+O): open another story in the same window,
  mid-session.
- Visuals -> Typeface: three looks, set in a selected serif (Novel,
  the default), a clean typeface (Clean), or a pixel font (Retro). The
  fonts ship with Actaea.
- Visuals -> Text Size: one size, driving every look.
- Visuals -> Screen Height: how many lines tall the story plays.
- Visuals -> Window Shape: Modern (4:5), a portrait page, or Classic
  (4:3), the squat screen of the old machines. A larger font gives a
  larger window of the same shape.
- Visuals -> Z-machine Colors: turns Z-machine colors on and off.
- Settings -> On Launch: what starting Actaea without a story does,
  ask for one or reopen the last one played.

Settings persist in `~/.config/actaea/settings.json` and return at the
next launch, the window's size and position included. Delete the file
to start fresh.

Pictures: the window draws a story's `arc_image` picture (01 section
6b) in a band across the top, pixel-crisp at every window size. This
is the loop an arc_image game is developed in: point `--images DIR` at
a directory of numbered PNGs (`8.png` is picture id 8) and play while
the art is still loose; a shipped game's pictures are read from the
sibling `.blorb`, or from a `.zblorb` with story and pictures in one
file. The terminal and pipe modes play the same story as pure text.

`actaea --install-app` installs Actaea among your applications, on
macOS, Linux, or Windows, with file associations for .z5, .z8, and
.zblorb. The interpreter itself stays the single file beside the other
Arcturus tools, still fully usable from the command line, and
`arcc --update` continues to update everything in place; the installed
launcher never needs a reinstall.

### The terminal: --console

`actaea --console story.z5` plays in the terminal, in the manner of
fizmo-ncursesw: the game-drawn status bar, Z-machine colors mapped to
the terminal's, bold, italic, and reverse, `[MORE]` paging, and timed
input. The terminal tab is titled after the story while it plays.

The status bar spans the terminal's full width, whatever it is. Resize
the terminal and the text re-wraps to the new width; the game itself
hears about the new size with its next command (a v5 game cannot be
interrupted mid-turn to be told).

Native Windows has no curses; there, --console degrades to the
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
  terminal (status bar, colors, paging), the way you would normally play;
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

- Line input with editing, echoed by the front-end that shows it. The
  window and the terminal both recall earlier commands on the arrow
  keys; a story that claims the cursor keys as terminating characters
  wins them, and the recall steps aside.
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
  quit); the styled, colored, and timed portions verified by eye in the
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
`arc_image` picture band renders in the window (section 2), and it never
touches conformance: a story's pictures are separate files, and any
interpreter without them plays the same z5 as pure text.

## 7. For Arcturus authors

`arcc game.storyarc -o game.z5 && actaea game.z5` is the whole loop. The
compiler and the interpreter are independent implementations of the same
standard, built in the same repository, and each is the other's check: the
text Actaea decodes is the text arcc encoded, the saves interoperate with
third-party interpreters, and Hibernated 2 plays start to finish on all
three front-ends. Verify releases on a second interpreter (Frotz or
Bocfel) as a matter of craft; that is what reference implementations are
for.
