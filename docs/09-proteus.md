# Proteus: the Arcturus web interpreter

Proteus puts an Arcturus game on the web as one self-contained HTML
file: the interpreter, the styles, the font, the story, and its
arc_image pictures, all inside a single page. Upload that file anywhere
(itch.io, your own webspace) and the game plays in any browser. There
is no server component and nothing else to deploy.

This document covers the author tool (`proteus`, the fourth standalone), what the web page does and does not support, and the fork that powers it. The name follows the Solar System object naming of the project's arc_image capable Z-machine interpreters, alongside Actaea.

## 1. The proteus tool

You bring the finished artifacts you already have from `arcc` and
`arcimg`; `proteus` never touches masters or sources.

```
proteus mygame.zblorb -o mygame.html
    The single-file shape: a zblorb made with `arcimg pack --zblorb`
    already carries the story and its pictures together.

proteus mygame.z5 mygame.blorb -o mygame.html
    The pair shape: a bare story plus the pictures-only Blorb made
    with `arcimg pack`. The tool splices them into a zblorb first.

proteus mygame.z5 -o mygame.html
    A text-only game; no pictures, no Blorb, still one page.
```

The output is one `.html` file, typically under a megabyte for a full
game with pictures. The browser tab shows `Proteus - <filename>`, the
Actaea manner. Like the other standalones, `proteus` is a single
self-contained Python file (`build/proteus`) with no dependencies
beyond a bare interpreter; the whole web runtime rides inside it.

A pictures-only Blorb alone is refused (it holds no story), and a
`.zblorb` output from `arcimg pack` without its story is refused there
too: to create a zblorb you provide the story file, always.

## 2. What the page supports

- Z-machine versions 5 and 8, the Arcturus targets. Versions 3 and 4
  ride along (the engine plays them; a PunyInform-compiled version 3
  game is part of the verification), so stories from other toolchains
  are welcome too.
- The arc_image picture band (docs/08): drawn above the text, scaled
  crisply to the window (the masters are pixel art), pictures swapped
  by the game, cleared on id 0, and absent entirely for a game without
  them. The band follows the browser window through resizes and zoom.
- Z-machine colours: text colours flow through, and the game's
  background paints the window and the page (the Gargoyle manner), so
  a black-screen game is black to the page edges. The statusline's
  reverse video paints its full row.
- Save, restore, undo, transcripts: saves live in the browser's local
  storage, per site.
- Graceful degradation both ways: the page is still an ordinary
  Z-machine interpreter, and the embedded story is still an ordinary
  story file.

What it does not do: sound, version 6, and timed input (the engine
does not claim the timed-input header bit). Proteus is built and
verified for Arcturus games; the engine inside is ZVM, which has
played standard z-code for years, but Arcturus output is what the
project tests.

## 3. The fork (proteus/ in this repository)

Proteus is a trimmed, Z-machine-only fork of Dannii Willis' Parchment, vendored under `proteus/` with its provenance and upstream commits recorded in `proteus/PROVENANCE.md`. There is no separate fork repository. What was trimmed, what was added:

- Trimmed: every non-Z engine (Glulx, TADS, Hugo, SCARE, AGT), the
  iplayif.com application, the Inform 7 packaging, test harnesses, and
  all fonts but the one the page embeds. The single file went from
  upstream's 3.6 MB to about 0.8 MB.
- Revived: ZVM, Dannii's TypeScript Z-machine, as the one engine (it
  was dormant in upstream), wired to the modern shell.
- Added: the arc_image band (an `ARCI`-declaring Blorb lights the
  capability bit and the band appears; see docs/08), window and page
  background painting from the game's colours, and the single-file
  template the `proteus` tool fills.

## 4. Rebuilding after changes

The JS toolchain (node) is needed only to rebuild the web runtime
itself, never by authors. After changing anything under `proteus/`:

```
cd proteus
npm install                     # once per machine
node build.js                   # build the runtime
node tools/make-single-file.js --out dist/single-file   # the template
cd ..
python3 tools/amalgamate_proteus.py                     # -> build/proteus
```

Regenerate `build/proteus` in the same breath as the other standalones
whenever the web interpreter changes; the tool's `--version` prints the
build fingerprint that proves which template rides inside.
